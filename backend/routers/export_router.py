"""
API endpoints pour exporter les données
"""
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
import csv
import io
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
import os

router = APIRouter(prefix="/api/export", tags=["export"])

# MongoDB connection - will be initialized from main app
_db = None


def init_db(db):
    """Initialize database connection"""
    global _db
    _db = db


def get_db():
    """Get database instance"""
    if _db is None:
        # Fallback: create connection if not initialized
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
        client = AsyncIOMotorClient(mongo_url)
        return client[os.environ.get('DB_NAME', 'afcfta')]
    return _db


@router.get("/tariffs/csv")
async def export_tariffs_csv(
    country: str = Query(..., description="Country code"),
    latest: bool = Query(True, description="Latest only")
):
    """Export tariffs as CSV"""
    try:
        db = get_db()
        query = {"country_code": country}

        if latest:
            data = await db["customs_data"].find_one(query, sort=[("imported_at", -1)])
            if not data:
                raise HTTPException(404, f"No data for {country}")
            data_list = [data]
        else:
            cursor = db["customs_data"].find(query).sort("imported_at", -1)
            data_list = await cursor.to_list(length=None)

        rows = []
        for data in data_list:
            for line in data.get("tariffs", {}).get("tariff_lines", []):
                rows.append({
                    "country": data.get("country_code"),
                    "hs_code": line.get("hs_code", ""),
                    "description": line.get("description", ""),
                    "unit": line.get("unit", ""),
                    "customs_duty": line.get("customs_duty", ""),
                    "vat": line.get("vat", ""),
                    "source": line.get("source", ""),
                    "date": data.get("imported_at", "")
                })

        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        filename = f"tariffs_{country}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/tariffs/excel")
async def export_tariffs_excel(
    countries: str = Query(..., description="Comma-separated country codes"),
    latest: bool = Query(True)
):
    """Export tariffs as Excel (multi-sheet)"""
    try:
        db = get_db()
        country_list = [c.strip() for c in countries.split(",")]
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for country in country_list:
                query = {"country_code": country}
                data = await db["customs_data"].find_one(query, sort=[("imported_at", -1)])

                if not data:
                    continue

                rows = []
                for line in data.get("tariffs", {}).get("tariff_lines", []):
                    rows.append({
                        "HS Code": line.get("hs_code"),
                        "Description": line.get("description"),
                        "Unit": line.get("unit"),
                        "Customs Duty": line.get("customs_duty"),
                        "VAT": line.get("vat")
                    })

                if rows:
                    df = pd.DataFrame(rows)
                    df.to_excel(writer, sheet_name=country[:31], index=False)  # Excel sheet name limit is 31 chars

        output.seek(0)
        filename = f"tariffs_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"

        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/validation-report/json")
async def export_validation_report_json(
    country: str = Query(None, description="Optional country code filter"),
    min_score: float = Query(0.0, description="Minimum validation score")
):
    """Export validation report as JSON"""
    try:
        db = get_db()
        query = {}

        if country:
            query["country_code"] = country

        # Get all customs data with validation info
        cursor = db["customs_data"].find(query).sort("imported_at", -1)
        data_list = await cursor.to_list(length=None)

        validation_report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "country": country,
                "min_score": min_score
            },
            "summary": {
                "total_records": 0,
                "validated_records": 0,
                "failed_validations": 0,
                "average_score": 0.0
            },
            "records": []
        }

        total_score = 0.0
        for data in data_list:
            validation_info = data.get("validation", {})
            score = validation_info.get("score", 0.0)

            if score < min_score:
                continue

            validation_report["summary"]["total_records"] += 1
            total_score += score

            if validation_info.get("is_valid", False):
                validation_report["summary"]["validated_records"] += 1
            else:
                validation_report["summary"]["failed_validations"] += 1

            validation_report["records"].append({
                "country_code": data.get("country_code"),
                "imported_at": data.get("imported_at"),
                "validation": {
                    "is_valid": validation_info.get("is_valid", False),
                    "score": score,
                    "issues": validation_info.get("issues", []),
                    "warnings": validation_info.get("warnings", [])
                },
                "tariff_count": len(data.get("tariffs", {}).get("tariff_lines", [])),
                "regulation_count": len(data.get("regulations", []))
            })

        # Calculate average score
        if validation_report["summary"]["total_records"] > 0:
            validation_report["summary"]["average_score"] = round(
                total_score / validation_report["summary"]["total_records"], 2
            )

        return validation_report

    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/comparison/csv")
async def export_comparison_csv(
    countries: str = Query(..., description="Comma-separated country codes (2+ required)"),
    hs_codes: str = Query(None, description="Optional: Comma-separated HS codes to compare")
):
    """Compare tariffs between countries as CSV"""
    try:
        db = get_db()
        country_list = [c.strip() for c in countries.split(",")]

        if len(country_list) < 2:
            raise HTTPException(400, "At least 2 countries required for comparison")

        # Parse optional HS code filter
        hs_code_filter = None
        if hs_codes:
            hs_code_filter = [code.strip() for code in hs_codes.split(",")]

        # Collect data for all countries
        country_data = {}
        for country in country_list:
            data = await db["customs_data"].find_one(
                {"country_code": country},
                sort=[("imported_at", -1)]
            )
            if data:
                country_data[country] = data

        if not country_data:
            raise HTTPException(404, "No data found for specified countries")

        # Build comparison rows
        # Use the first country's HS codes as the base
        base_country = country_list[0]
        if base_country not in country_data:
            raise HTTPException(404, f"No data for base country {base_country}")

        base_tariffs = country_data[base_country].get("tariffs", {}).get("tariff_lines", [])

        rows = []
        for tariff in base_tariffs:
            hs_code = tariff.get("hs_code", "")

            # Apply HS code filter if specified
            if hs_code_filter and hs_code not in hs_code_filter:
                continue

            row = {
                "hs_code": hs_code,
                "description": tariff.get("description", "")
            }

            # Add data for each country
            for country in country_list:
                if country not in country_data:
                    row[f"{country}_duty"] = "N/A"
                    row[f"{country}_vat"] = "N/A"
                    continue

                # Find matching HS code in this country's data
                country_tariffs = country_data[country].get("tariffs", {}).get("tariff_lines", [])
                matching_tariff = next(
                    (t for t in country_tariffs if t.get("hs_code") == hs_code),
                    None
                )

                if matching_tariff:
                    row[f"{country}_duty"] = matching_tariff.get("customs_duty", "N/A")
                    row[f"{country}_vat"] = matching_tariff.get("vat", "N/A")
                else:
                    row[f"{country}_duty"] = "N/A"
                    row[f"{country}_vat"] = "N/A"

            rows.append(row)

        if not rows:
            raise HTTPException(404, "No matching tariff data found")

        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

        filename = f"comparison_{'_'.join(country_list)}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

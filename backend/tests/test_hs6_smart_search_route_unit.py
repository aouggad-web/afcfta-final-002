import pytest
from fastapi import HTTPException
from routes import hs6_database


class _DummyEngine:
    def search(self, query, country=None, limit=20):
        return [
            {
                "hs_code": "700100",
                "description": "Verre brut",
                "country": "SEN",
                "duty_rate_pct": 20.0,
            },
            # Sub-position row should not be returned as top-level result when
            # include_sub_positions=True
            {
                "hs_code": "7001001000",
                "description": "Verre brut - sous-position",
                "country": "SEN",
                "duty_rate_pct": 5.0,
            },
        ]


@pytest.mark.asyncio
async def test_smart_search_supports_query_alias_and_sub_positions(monkeypatch):
    monkeypatch.setattr(hs6_database, "get_search_engine", lambda: _DummyEngine())
    monkeypatch.setattr(hs6_database, "get_tariff_line", lambda country, hs6: {"hs6": hs6})
    monkeypatch.setattr(
        hs6_database,
        "get_sub_positions",
        lambda country, hs6: [
            {
                "code": "7001001000",
                "digits": 10,
                "dd_rate": 5.0,
                "description_fr": "Verre brut - sous-position",
                "description_en": "Raw glass - sub-position",
                "source": "mock",
            }
        ],
    )

    response = await hs6_database.smart_search_hs6(
        q=None,
        query="70",
        language="fr",
        country_code="sen",
        include_sub_positions=True,
        limit=20,
    )

    assert response["query"] == "70"
    assert response["count"] == 1
    assert response["total"] == 1
    assert isinstance(response["results"], list)

    first = response["results"][0]
    assert first["code"] == "700100"
    assert first["chapter"] == "70"
    assert "chapter_name" in first
    assert "full_position" in first
    assert first["from_authentic"] is True
    assert len(first["sub_positions"]) == 1
    assert first["sub_positions"][0]["dd"] == 5.0


@pytest.mark.asyncio
async def test_smart_search_rejects_short_query():
    with pytest.raises(HTTPException) as exc:
        await hs6_database.smart_search_hs6(q="1")
    assert exc.value.status_code == 422

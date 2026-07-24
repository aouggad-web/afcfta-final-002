import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CalculationMethodStatus from "./CalculationMethodStatus";

describe("CalculationMethodStatus", () => {
  it("shows the country-specific method and legal source", () => {
    render(
      <CalculationMethodStatus
        status="country_specific"
        legalSource="Zambia Revenue Authority — VAT on imports"
        language="fr"
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Méthode nationale appliquée",
    );
    expect(screen.getByText(/Zambia Revenue Authority/)).toBeInTheDocument();
  });

  it("warns clearly when the backend used its default method", () => {
    render(
      <CalculationMethodStatus
        status="default"
        legalSource="Profil par défaut (TVA base = CIF+DD)"
        language="fr"
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Méthode générique à confirmer",
    );
    expect(screen.getByRole("alert")).toHaveTextContent("TVA = CIF + DD");
  });
});

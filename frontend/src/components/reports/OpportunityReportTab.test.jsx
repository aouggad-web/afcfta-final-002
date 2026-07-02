import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import OpportunityReportTab from "./OpportunityReportTab";

vi.mock("../opportunities/OpportunitiesTab", () => ({
  default: ({ language }) => (
    <div data-testid="opportunities-preview">preview-{language}</div>
  ),
}));

describe("OpportunityReportTab", () => {
  it("affiche par défaut le preview du module opportunities et permet de basculer", async () => {
    const user = userEvent.setup();

    render(<OpportunityReportTab countries={[]} language="fr" />);

    expect(screen.getByTestId("opportunities-preview")).toHaveTextContent("preview-fr");

    await user.click(screen.getByTestId("mode-market"));
    expect(screen.queryByTestId("opportunities-preview")).not.toBeInTheDocument();
    expect(screen.getByTestId("ms-run")).toBeInTheDocument();

    await user.click(screen.getByTestId("mode-preview"));
    expect(screen.getByTestId("opportunities-preview")).toBeInTheDocument();
  });
});

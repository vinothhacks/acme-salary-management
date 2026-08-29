import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import FilterBar, { EMPTY_FILTERS, Filters } from "./FilterBar";

function Harness() {
  const [value, setValue] = useState<Filters>(EMPTY_FILTERS);
  return (
    <>
      <FilterBar value={value} onChange={setValue} />
      <p data-testid="q">{value.q}</p>
      <p data-testid="country">{value.country}</p>
    </>
  );
}

describe("FilterBar", () => {
  it("keeps search and country in sync", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.type(screen.getByPlaceholderText("Name, code, or email"), "Ada");
    await user.selectOptions(screen.getByLabelText("Country"), "US");
    expect(screen.getByTestId("q")).toHaveTextContent("Ada");
    expect(screen.getByTestId("country")).toHaveTextContent("US");
  });
});

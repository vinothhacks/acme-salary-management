import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Ask from "./Ask";

const ask = vi.fn();

vi.mock("../lib/api", () => ({
  api: { ask: (...args: unknown[]) => ask(...args) },
}));

vi.mock("../lib/chartRegistry", () => ({
  renderAction: () => <div>chart</div>,
}));

function renderAsk() {
  return render(
    <MemoryRouter initialEntries={["/ask"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/ask" element={<Ask />} />
        <Route path="/" element={<p>Dashboard page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Ask composer", () => {
  beforeEach(() => {
    ask.mockReset();
    ask.mockResolvedValue({
      say: "Pay distribution from current compensation rows.",
      actions: [
        {
          fn: "barChart",
          title: "Pay distribution",
          x_key: "name",
          y_key: "value",
          columns: [],
          rows: [{ name: "$0", value: 2 }],
        },
      ],
      model: null,
    });
  });

  it("sends on Enter from the bottom input", async () => {
    const user = userEvent.setup();
    renderAsk();
    await user.type(screen.getByRole("textbox", { name: "Question" }), "pay distribution{Enter}");
    expect(ask).toHaveBeenCalledWith("pay distribution", []);
    expect(await screen.findByText("Pay distribution from current compensation rows.")).toBeInTheDocument();
  });

  it("goes to the dashboard without waiting on the API", async () => {
    const user = userEvent.setup();
    renderAsk();
    await user.type(screen.getByRole("textbox", { name: "Question" }), "go to dashboard{Enter}");
    expect(ask).not.toHaveBeenCalled();
    expect(screen.getByText("Dashboard page")).toBeInTheDocument();
  });
});

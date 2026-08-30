import { describe, expect, it } from "vitest";
import { renderAction, UI_FNS, type UiAction } from "./chartRegistry";

const sample: UiAction = {
  fn: "barChart",
  title: "Mean",
  x_key: "name",
  y_key: "value",
  columns: [],
  rows: [{ name: "IN", value: 1 }],
};

describe("chart registry", () => {
  it("exposes bar, line, pie, and table functions", () => {
    expect(Object.keys(UI_FNS).sort()).toEqual(["barChart", "lineChart", "pieChart", "table"]);
  });

  it("ignores navigateTo in the renderer", () => {
    expect(renderAction({ ...sample, fn: "navigateTo", path: "/" })).toBeNull();
  });
});

import { describe, expect, it } from "vitest";
import { validateRevise } from "./revise";

describe("validateRevise", () => {
  const valid = {
    base_amount: "120000",
    bonus_amount: "0",
    allowances_amount: "0",
    currency: "USD",
    effective_from: "2026-01-01",
    revision_reason: "Annual review",
  };

  it("accepts a complete revision", () => {
    expect(validateRevise(valid)).toEqual({});
  });

  it("rejects a negative base and a short reason", () => {
    const errors = validateRevise({ ...valid, base_amount: "-1", revision_reason: "no" });
    expect(errors.base_amount).toBeTruthy();
    expect(errors.revision_reason).toBeTruthy();
  });
});

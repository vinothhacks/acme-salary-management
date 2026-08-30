import { describe, expect, it } from "vitest";
import { navPathFromMessage } from "./askNav";

describe("navPathFromMessage", () => {
  it("opens dashboard, employees, and import from go-to phrases", () => {
    expect(navPathFromMessage("go to dashboard")).toBe("/");
    expect(navPathFromMessage("Go to the dashboard")).toBe("/");
    expect(navPathFromMessage("take me to employees")).toBe("/employees");
    expect(navPathFromMessage("open import")).toBe("/import");
  });

  it("does not treat chart questions as navigation", () => {
    expect(navPathFromMessage("pay distribution")).toBeNull();
    expect(navPathFromMessage("mean pay IN vs US")).toBeNull();
    expect(navPathFromMessage("dashboard numbers")).toBeNull();
  });
});

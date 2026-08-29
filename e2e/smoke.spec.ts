import { expect, test } from "@playwright/test";

const MIXED_CSV = [
  "employee_code,full_name,email,country_code,department,job_title,band,employment_type,hire_date,base_amount,bonus_amount,allowances_amount,currency,effective_from,revision_reason,status",
  "ACME-E2E01,E2E Hire,e2e.hire@acme.example,US,Engineering,Analyst,IC2,full_time,2024-03-01,80000,4000,0,USD,2024-03-01,,active",
  "ACME-BAD,Nope,nope-e2e@acme.example,US,NotADept,Analyst,IC2,full_time,2024-03-01,-5,0,0,USD,2024-03-01,,active",
  "",
].join("\n");

test("hr can search, revise, see the dashboard, and import mixed CSV", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Enter" }).click();
  await expect(page.getByText("Headcount")).toBeVisible({ timeout: 30_000 });

  await page.getByRole("link", { name: "Employees" }).click();
  await page.getByLabel("Search").fill("ACME-00001");
  await expect(page.getByRole("link", { name: "ACME-00001" })).toBeVisible({ timeout: 15_000 });
  await page.getByRole("link", { name: "ACME-00001" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  await page.getByRole("button", { name: "Revise salary" }).click();
  await page.getByLabel("Base").fill("91000");
  await page.getByLabel("Effective from").fill("2026-12-01");
  await page.getByLabel("Reason").fill("E2E market check");
  await page.getByRole("button", { name: "Record revision" }).click();
  await expect(page.getByText("E2E market check")).toBeVisible();

  await page.getByRole("link", { name: "Dashboard" }).click();
  await expect(page.getByText("Headcount")).toBeVisible();

  await page.getByRole("link", { name: "Import" }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "mixed.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(MIXED_CSV),
  });
  await page.getByRole("button", { name: "Import" }).click();
  await expect(page.getByText(/Created 1/)).toBeVisible();
  await expect(page.getByText(/failed 1/)).toBeVisible();
});

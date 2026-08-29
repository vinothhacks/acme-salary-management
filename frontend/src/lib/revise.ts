export type ReviseValues = {
  base_amount: string;
  bonus_amount: string;
  allowances_amount: string;
  currency: string;
  effective_from: string;
  revision_reason: string;
};

export type ReviseErrors = Partial<Record<keyof ReviseValues, string>>;

export function validateRevise(values: ReviseValues): ReviseErrors {
  const errors: ReviseErrors = {};
  for (const field of ["base_amount", "bonus_amount", "allowances_amount"] as const) {
    const n = Number(values[field]);
    if (values[field] === "" || Number.isNaN(n) || n < 0) {
      errors[field] = "Must be zero or a positive number";
    }
  }
  if (!/^[A-Z]{3}$/.test(values.currency)) {
    errors.currency = "Use a 3-letter currency code";
  }
  if (!values.effective_from) {
    errors.effective_from = "Effective date is required";
  }
  if (values.revision_reason.trim().length < 3) {
    errors.revision_reason = "Give a short reason (at least 3 characters)";
  }
  return errors;
}

import { FormEvent, useState } from "react";
import { ReviseValues, validateRevise } from "../lib/revise";

const INITIAL: ReviseValues = {
  base_amount: "",
  bonus_amount: "0",
  allowances_amount: "0",
  currency: "USD",
  effective_from: "",
  revision_reason: "",
};

type Props = {
  onSubmit: (values: ReviseValues) => Promise<void>;
  busy?: boolean;
};

export default function ReviseForm({ onSubmit, busy }: Props) {
  const [values, setValues] = useState<ReviseValues>(INITIAL);
  const [errors, setErrors] = useState<ReturnType<typeof validateRevise>>({});
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const next = validateRevise(values);
    setErrors(next);
    if (Object.keys(next).length) return;
    try {
      setFormError(null);
      await onSubmit(values);
      setValues(INITIAL);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not save revision");
    }
  }

  function field(name: keyof ReviseValues, label: string, type = "text") {
    return (
      <label>
        {label}
        <input
          name={name}
          type={type}
          value={values[name]}
          onChange={(e) => setValues({ ...values, [name]: e.target.value })}
        />
        {errors[name] ? <span className="field-error">{errors[name]}</span> : null}
      </label>
    );
  }

  return (
    <form className="revise-form" onSubmit={handleSubmit} noValidate>
      <div className="form-grid">
        {field("base_amount", "Base")}
        {field("bonus_amount", "Bonus")}
        {field("allowances_amount", "Allowances")}
        {field("currency", "Currency")}
        {field("effective_from", "Effective from", "date")}
      </div>
      <label>
        Reason
        <textarea
          name="revision_reason"
          value={values.revision_reason}
          onChange={(e) => setValues({ ...values, revision_reason: e.target.value })}
        />
        {errors.revision_reason ? <span className="field-error">{errors.revision_reason}</span> : null}
      </label>
      {formError ? <p className="banner error">{formError}</p> : null}
      <button type="submit" disabled={busy}>
        {busy ? "Saving…" : "Record revision"}
      </button>
    </form>
  );
}

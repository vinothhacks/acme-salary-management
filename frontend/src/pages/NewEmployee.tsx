import { FormEvent, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import type { Department, EmployeeDetail } from "../lib/types";

export default function NewEmployee() {
  const navigate = useNavigate();
  const depts = useQuery({ queryKey: ["departments"], queryFn: () => api.departments() as Promise<Department[]> });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      const created = (await api.createEmployee({
        employee_code: form.get("employee_code"),
        full_name: form.get("full_name"),
        email: form.get("email"),
        country_code: form.get("country_code"),
        department_id: Number(form.get("department_id")),
        job_title: form.get("job_title"),
        band: form.get("band"),
        employment_type: form.get("employment_type"),
        hire_date: form.get("hire_date"),
        salary: {
          base_amount: form.get("base_amount"),
          bonus_amount: form.get("bonus_amount") || "0",
          allowances_amount: form.get("allowances_amount") || "0",
          currency: form.get("currency"),
          effective_from: form.get("hire_date"),
        },
      })) as EmployeeDetail;
      navigate(`/employees/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create employee");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>Add employee</h1>
      {depts.isError ? <p className="banner error">Departments unavailable.</p> : null}
      <form className="stack-form" onSubmit={onSubmit}>
        <label>
          Code <input name="employee_code" required />
        </label>
        <label>
          Full name <input name="full_name" required />
        </label>
        <label>
          Email <input name="email" type="email" required />
        </label>
        <label>
          Country <input name="country_code" defaultValue="US" maxLength={2} required />
        </label>
        <label>
          Department
          <select name="department_id" required>
            {(depts.data ?? []).map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Title <input name="job_title" required />
        </label>
        <label>
          Band <input name="band" defaultValue="IC3" required />
        </label>
        <label>
          Type
          <select name="employment_type" defaultValue="full_time">
            <option value="full_time">Full time</option>
            <option value="part_time">Part time</option>
            <option value="contract">Contract</option>
          </select>
        </label>
        <label>
          Hire date <input name="hire_date" type="date" required />
        </label>
        <label>
          Base <input name="base_amount" required />
        </label>
        <label>
          Bonus <input name="bonus_amount" defaultValue="0" />
        </label>
        <label>
          Allowances <input name="allowances_amount" defaultValue="0" />
        </label>
        <label>
          Currency <input name="currency" defaultValue="USD" maxLength={3} required />
        </label>
        {error ? <p className="banner error">{error}</p> : null}
        <button type="submit" disabled={busy}>
          {busy ? "Saving…" : "Create"}
        </button>
      </form>
    </section>
  );
}

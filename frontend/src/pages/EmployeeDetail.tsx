import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReviseForm from "../components/ReviseForm";
import { api } from "../lib/api";
import { dateLabel, money } from "../lib/format";
import type { ReviseValues } from "../lib/revise";
import type { EmployeeDetail as Detail } from "../lib/types";

export default function EmployeeDetail() {
  const { id } = useParams();
  const employeeId = Number(id);
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const detail = useQuery({
    queryKey: ["employee", employeeId],
    queryFn: () => api.employee(employeeId) as Promise<Detail>,
    enabled: Number.isFinite(employeeId),
  });
  const revise = useMutation({
    mutationFn: (values: ReviseValues) => api.reviseSalary(employeeId, values),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["employee", employeeId] });
      client.invalidateQueries({ queryKey: ["summary"] });
      setOpen(false);
    },
  });
  const deactivate = useMutation({
    mutationFn: () => api.patchEmployee(employeeId, { status: "inactive" }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["employee", employeeId] }),
  });

  if (detail.isLoading) return <p className="muted">Loading profile…</p>;
  if (detail.isError) return <p className="banner error">That employee could not be found.</p>;
  if (!detail.data) return <p className="muted">No profile.</p>;
  const person = detail.data;

  return (
    <section>
      <p className="crumb">
        <Link to="/employees">Employees</Link> / {person.employee_code}
      </p>
      <header className="page-head">
        <div>
          <p className="eyebrow">{person.band} · {person.country_code}</p>
          <h1>{person.full_name}</h1>
          <p className="lede">
            {person.job_title} · {person.department_name} · {person.status}
          </p>
        </div>
        <div className="actions">
          <button type="button" onClick={() => setOpen(true)}>
            Revise salary
          </button>
          {person.status === "active" ? (
            <button className="ghost" type="button" onClick={() => deactivate.mutate()}>
              Mark inactive
            </button>
          ) : null}
        </div>
      </header>

      <article className="comp-card">
        <p>Current compensation</p>
        <strong className="money">
          {money(person.current_base, person.current_currency ?? "USD")}
        </strong>
        <span>{person.current_currency}</span>
      </article>

      <article className="panel">
        <h2>Salary history</h2>
        {person.salary_history.length === 0 ? <p className="muted">No salary rows.</p> : null}
        <ol className="timeline">
          {person.salary_history.map((row) => (
            <li key={row.id}>
              <div>
                <strong className="money">{money(row.base_amount, row.currency)}</strong>
                <span>
                  {dateLabel(row.effective_from)} — {dateLabel(row.effective_to)}
                </span>
              </div>
              <p>{row.revision_reason || "Opening record"}</p>
            </li>
          ))}
        </ol>
      </article>

      {open ? (
        <div className="modal" role="dialog" aria-labelledby="revise-title">
          <div className="modal-card">
            <h2 id="revise-title">Revise salary</h2>
            <ReviseForm
              busy={revise.isPending}
              onSubmit={async (values) => {
                await revise.mutateAsync(values);
              }}
            />
            <button className="ghost" type="button" onClick={() => setOpen(false)}>
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

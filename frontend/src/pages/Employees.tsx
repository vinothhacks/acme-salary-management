import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import FilterBar, { EMPTY_FILTERS, Filters } from "../components/FilterBar";
import { api } from "../lib/api";
import { money } from "../lib/format";
import type { EmployeePage } from "../lib/types";

export default function Employees() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);
  const params = useMemo(() => {
    const search = new URLSearchParams({ page: String(page), page_size: "25", sort: "employee_code" });
    if (filters.q) search.set("q", filters.q);
    if (filters.country) search.set("country", filters.country);
    if (filters.band) search.set("band", filters.band);
    if (filters.status) search.set("status", filters.status);
    return search;
  }, [filters, page]);

  const list = useQuery({
    queryKey: ["employees", params.toString()],
    queryFn: () => api.employees(params) as Promise<EmployeePage>,
  });

  function changeFilters(next: Filters) {
    setFilters(next);
    setPage(1);
  }

  return (
    <section>
      <header className="page-head">
        <div>
          <p className="eyebrow">Directory</p>
          <h1>Employees</h1>
        </div>
        <div className="actions">
          <Link className="button" to="/employees/new">
            Add employee
          </Link>
          <a className="button ghost" href={api.exportUrl(params)}>
            Export CSV
          </a>
        </div>
      </header>
      <FilterBar value={filters} onChange={changeFilters} />
      {list.isLoading ? <p className="muted">Loading people…</p> : null}
      {list.isError ? <p className="banner error">The directory could not be loaded.</p> : null}
      {list.data && list.data.items.length === 0 ? <p className="muted">No one matches those filters.</p> : null}
      {list.data && list.data.items.length > 0 ? (
        <>
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Country</th>
                <th>Dept</th>
                <th>Band</th>
                <th>Base</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {list.data.items.map((row) => (
                <tr key={row.id}>
                  <td>
                    <Link to={`/employees/${row.id}`}>{row.employee_code}</Link>
                  </td>
                  <td>{row.full_name}</td>
                  <td>{row.country_code}</td>
                  <td>{row.department_name}</td>
                  <td>{row.band}</td>
                  <td className="money">{money(row.current_base, row.current_currency ?? "USD")}</td>
                  <td>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pager">
            <button type="button" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {list.data.meta.page} of {Math.max(1, Math.ceil(list.data.meta.total / list.data.meta.page_size))} ·{" "}
              {list.data.meta.total.toLocaleString()} people
            </span>
            <button
              type="button"
              disabled={page * list.data.meta.page_size >= list.data.meta.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      ) : null}
    </section>
  );
}

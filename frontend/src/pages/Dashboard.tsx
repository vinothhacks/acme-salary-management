import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../lib/api";
import { compact, money } from "../lib/format";
import type { CostTrend, Distribution, Percentiles, Summary } from "../lib/types";

export default function Dashboard() {
  const summary = useQuery({ queryKey: ["summary"], queryFn: () => api.summary() as Promise<Summary> });
  const dist = useQuery({ queryKey: ["dist"], queryFn: () => api.distribution() as Promise<Distribution> });
  const pct = useQuery({ queryKey: ["pct"], queryFn: () => api.percentiles() as Promise<Percentiles> });
  const trend = useQuery({ queryKey: ["trend"], queryFn: () => api.costTrend() as Promise<CostTrend> });

  if (summary.isLoading) return <p className="muted">Loading the ledger…</p>;
  if (summary.isError) return <p className="banner error">Could not load analytics.</p>;
  if (!summary.data) return <p className="muted">No compensation data yet.</p>;

  const s = summary.data;
  return (
    <section>
      <header className="page-head">
        <div>
          <p className="eyebrow">Ask the data</p>
          <h1>How the organisation pays</h1>
        </div>
      </header>
      <div className="stat-row">
        <article className="stat">
          <p>Headcount</p>
          <strong>{s.headcount.toLocaleString()}</strong>
        </article>
        <article className="stat">
          <p>Annual cost (USD)</p>
          <strong className="money">{money(s.total_annual_usd)}</strong>
        </article>
        <article className="stat">
          <p>Mean</p>
          <strong className="money">{money(s.mean_usd)}</strong>
        </article>
        <article className="stat">
          <p>Median</p>
          <strong className="money">{money(s.median_usd)}</strong>
        </article>
      </div>

      <div className="grid-2">
        <article className="panel">
          <h2>Distribution</h2>
          {dist.isLoading ? <p className="muted">Loading…</p> : null}
          {dist.data ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={dist.data.buckets.map((b) => ({ name: compact(b.bucket_usd), count: b.count }))}>
                <CartesianGrid stroke="#d4cbb8" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#b45309" />
              </BarChart>
            </ResponsiveContainer>
          ) : null}
        </article>
        <article className="panel">
          <h2>Cost over time</h2>
          {trend.isLoading ? <p className="muted">Loading…</p> : null}
          {trend.data ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={trend.data.points}>
                <CartesianGrid stroke="#d4cbb8" vertical={false} />
                <XAxis dataKey="as_of" tick={{ fontSize: 10 }} />
                <YAxis tickFormatter={(v: number) => compact(String(v))} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => money(String(v))} />
                <Line type="monotone" dataKey="total_usd" stroke="#1a1916" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : null}
        </article>
      </div>

      <article className="panel">
        <h2>Percentiles by band</h2>
        {pct.isError ? <p className="banner error">Percentiles unavailable.</p> : null}
        {!pct.data?.by_band.length ? <p className="muted">No rows for this filter.</p> : null}
        {pct.data ? (
          <table>
            <thead>
              <tr>
                <th>Band</th>
                <th>p10</th>
                <th>p25</th>
                <th>p50</th>
                <th>p75</th>
                <th>p90</th>
              </tr>
            </thead>
            <tbody>
              {pct.data.by_band.map((row) => (
                <tr key={row.key}>
                  <td>{row.key}</td>
                  <td className="money">{money(row.p10)}</td>
                  <td className="money">{money(row.p25)}</td>
                  <td className="money">{money(row.p50)}</td>
                  <td className="money">{money(row.p75)}</td>
                  <td className="money">{money(row.p90)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </article>

      <article className="panel">
        <h2>By country</h2>
        <table>
          <thead>
            <tr>
              <th>Country</th>
              <th>People</th>
              <th>Total USD</th>
              <th>Mean</th>
            </tr>
          </thead>
          <tbody>
            {s.by_country.map((row) => (
              <tr key={row.key}>
                <td>{row.key}</td>
                <td>{row.headcount}</td>
                <td className="money">{money(row.total_usd)}</td>
                <td className="money">{money(row.mean_usd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
}

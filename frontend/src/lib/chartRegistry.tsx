import type { ReactElement, ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { compact, money } from "./format";

export type UiFn = "barChart" | "lineChart" | "pieChart" | "table" | "navigateTo";

export type UiAction = {
  fn: UiFn;
  title: string;
  path?: string | null;
  x_key: string;
  y_key: string;
  columns: string[];
  rows: Record<string, string | number>[];
};

const INK = ["#b45309", "#1a1916", "#5c574e", "#8c2f2f", "#7c6a46", "#3f3a32"];

function ChartFrame({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="panel">
      {title ? <h2>{title}</h2> : null}
      {children}
    </article>
  );
}

function barChart(action: UiAction) {
  return (
    <ChartFrame title={action.title}>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart accessibilityLayer={false} data={action.rows}>
          <CartesianGrid stroke="#d4cbb8" vertical={false} />
          <XAxis dataKey={action.x_key} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey={action.y_key} fill="#b45309" />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function lineChart(action: UiAction) {
  return (
    <ChartFrame title={action.title}>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart accessibilityLayer={false} data={action.rows}>
          <CartesianGrid stroke="#d4cbb8" vertical={false} />
          <XAxis dataKey={action.x_key} tick={{ fontSize: 10 }} />
          <YAxis tickFormatter={(v: number) => compact(String(v))} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v: number) => money(String(v))} />
          <Line type="monotone" dataKey={action.y_key} stroke="#1a1916" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function pieChart(action: UiAction) {
  return (
    <ChartFrame title={action.title}>
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie data={action.rows} dataKey={action.y_key} nameKey={action.x_key} cx="50%" cy="50%" outerRadius={80}>
            {action.rows.map((_, i) => (
              <Cell key={String(i)} fill={INK[i % INK.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function table(action: UiAction) {
  const cols = action.columns.length ? action.columns : Object.keys(action.rows[0] ?? {});
  return (
    <ChartFrame title={action.title}>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {cols.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {action.rows.map((row, i) => (
              <tr key={String(row.name ?? i)}>
                {cols.map((col) => (
                  <td key={col} className={col.includes("p") || col === "base" ? "money" : undefined}>
                    {String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ChartFrame>
  );
}

export const UI_FNS: Record<Exclude<UiFn, "navigateTo">, (action: UiAction) => ReactElement> = {
  barChart,
  lineChart,
  pieChart,
  table,
};

export function renderAction(action: UiAction) {
  if (action.fn === "navigateTo") return null;
  const draw = UI_FNS[action.fn];
  return draw(action);
}

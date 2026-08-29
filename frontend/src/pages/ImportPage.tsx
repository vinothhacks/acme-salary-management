import { FormEvent, useState } from "react";
import { api } from "../lib/api";
import type { ImportResult } from "../lib/types";

export default function ImportPage() {
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = (event.currentTarget.elements.namedItem("file") as HTMLInputElement).files?.[0];
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setResult((await api.importCsv(file)) as ImportResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <header className="page-head">
        <div>
          <p className="eyebrow">Migration</p>
          <h1>CSV import</h1>
          <p className="lede">HR still lives in Excel. Bad rows should not sink the good ones.</p>
        </div>
      </header>
      <form className="stack-form" onSubmit={onSubmit}>
        <label>
          File
          <input name="file" type="file" accept=".csv,text/csv" />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Reading…" : "Import"}
        </button>
      </form>
      {error ? <p className="banner error">{error}</p> : null}
      {result ? (
        <article className="panel">
          <p>
            Created {result.created}, revised {result.revised}, failed {result.failed}.
          </p>
          {result.errors.length === 0 ? <p className="muted">No row errors.</p> : null}
          {result.errors.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {result.errors.map((row) => (
                  <tr key={`${row.row}-${row.message}`}>
                    <td>{row.row}</td>
                    <td>{row.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}

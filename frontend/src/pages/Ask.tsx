import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { renderAction, type UiAction } from "../lib/chartRegistry";

type Turn = {
  role: "user" | "assistant";
  say: string;
  actions: UiAction[];
};

export default function Ask() {
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, busy]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const message = text.trim();
    if (!message || busy) return;
    setText("");
    setBusy(true);
    setError(null);
    setTurns((prev) => [...prev, { role: "user", say: message, actions: [] }]);
    try {
      const history = turns
        .filter((turn) => turn.role === "user" || turn.role === "assistant")
        .slice(-6)
        .map((turn) => ({ role: turn.role, content: turn.say }));
      const result = await api.ask(message, history);
      const go = result.actions.find((action) => action.fn === "navigateTo");
      setTurns((prev) => [
        ...prev,
        { role: "assistant", say: result.say, actions: result.actions.filter((a) => a.fn !== "navigateTo") },
      ]);
      if (go?.path) {
        navigate(go.path);
      }
    } catch {
      setError("Ask could not reach the ledger. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ask-page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Ask</p>
          <h1>Ask the ledger</h1>
          <p className="lede">Charts switch by function: bar, line, pie, table. “Go to dashboard” opens that page.</p>
        </div>
      </header>
      <div className="ask-log">
        {turns.length === 0 ? (
          <p className="muted">
            Try “mean pay IN vs US”, “pay distribution”, “cost over time”, “percentiles by band”, or “go to
            dashboard”.
          </p>
        ) : null}
        {turns.map((turn, i) => (
          <article key={`${turn.role}-${i}`} className={turn.role === "user" ? "ask-bubble user" : "ask-bubble"}>
            <p>{turn.say}</p>
            {turn.actions.map((action, j) => (
              <div key={`${action.fn}-${j}`}>{renderAction(action)}</div>
            ))}
          </article>
        ))}
        {busy ? <p className="muted">Reading the ledger…</p> : null}
        <div ref={end} />
      </div>
      {error ? <p className="banner error">{error}</p> : null}
      <form className="ask-form" onSubmit={onSubmit}>
        <label>
          Question
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={2}
            placeholder="Show mean pay by country"
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Asking…" : "Ask"}
        </button>
      </form>
    </section>
  );
}

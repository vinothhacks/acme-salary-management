import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { navPathFromMessage } from "../lib/askNav";
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
  const box = useRef<HTMLInputElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [turns, busy]);

  async function send(message: string) {
    if (!message || busy) return;
    setText("");
    setBusy(true);
    setError(null);
    setTurns((prev) => [...prev, { role: "user", say: message, actions: [] }]);
    const path = navPathFromMessage(message);
    if (path) {
      setTurns((prev) => [...prev, { role: "assistant", say: "Opening that page.", actions: [] }]);
      setBusy(false);
      navigate(path);
      return;
    }
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
      box.current?.focus();
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(text.trim());
  }

  return (
    <section className="ask-page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Ask</p>
          <h1>Ask the ledger</h1>
          <p className="lede">Type a question and press Enter. “Go to dashboard” opens that page.</p>
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
        <input
          ref={box}
          aria-label="Question"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask the ledger…"
          autoComplete="off"
          disabled={busy}
        />
        <button type="submit" disabled={busy}>
          {busy ? "…" : "Send"}
        </button>
      </form>
    </section>
  );
}

"use client"; // Runs in the browser: needs state (useState) and click/submit events

import { useState, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import { stripCitations } from "@/lib/citations";
import type { AskResponse, ErrorResponse } from "@/lib/types";
import styles from "./Search.module.css";

const EXAMPLES = [
  "Comment redimensionner une VM ?",
  "Comment créer un point de restauration ?",
  "Ma VM Linux ne démarre pas, comment la dépanner ?",
];

export default function Search() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function search(text: string) {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      // Our own route: it adds the API key on the server side
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });
      if (res.ok) {
        setResult((await res.json()) as AskResponse);
      } else {
        setError(((await res.json()) as ErrorResponse).error);
      }
    } catch {
      setError("Impossible de joindre le serveur.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); // Stay on the page instead of reloading it
    search(question);
  }

  function handleExample(example: string) {
    setQuestion(example);
    search(example);
  }

  return (
    <>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.srOnly} htmlFor="question">
          Votre question
        </label>
        <div className={styles.searchBar}>
          <svg
            className={styles.searchIcon}
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle cx="10.5" cy="10.5" r="6.5" />
            <path d="M15.5 15.5 21 21" />
          </svg>
          <input
            id="question"
            className={styles.input}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Posez votre question"
            minLength={3}
            maxLength={500}
            required
          />
          <button className={styles.button} type="submit" disabled={loading}>
            {loading ? "Recherche…" : "Rechercher"}
          </button>
        </div>
      </form>

      <div className={styles.examples}>
        <span className={styles.examplesLabel}>Exemples</span>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            className={styles.example}
            type="button"
            disabled={loading}
            onClick={() => handleExample(example)}
          >
            {example}
          </button>
        ))}
      </div>

      <div aria-live="polite">
        {loading && (
          <section className={styles.card}>
            <div className={styles.skeleton} aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <p className={styles.status}>
              Recherche en cours. Si l&apos;API dormait, comptez une trentaine
              de secondes.
            </p>
          </section>
        )}

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        {result && (
          <>
            <section className={styles.card}>
              <h2 className={styles.heading}>Réponse</h2>
              <div className={styles.answer}>
                <ReactMarkdown>{stripCitations(result.answer)}</ReactMarkdown>
              </div>
            </section>

            {result.sources.length > 0 && (
              <section className={styles.sourcesSection}>
                <h2 className={styles.heading}>Sources</h2>
                <ul className={styles.sources}>
                  {result.sources.map((source) => (
                    <li key={source.source}>
                      <a
                        className={styles.source}
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <span className={styles.sourceTitle}>
                          {source.title}
                        </span>
                        <span className={styles.path}>{source.source}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>
    </>
  );
}

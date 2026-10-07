"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

export default function WhatsAppPage() {
  const [adapter, setAdapter] = useState<Record<string, string> | null>(null);
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [text, setText] = useState(
    "Nike Air Max 95 noire a 45000 FCFA, j'en ai 4 en taille 42 et 2 en taille 43.",
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Record<string, string>>("/whatsapp/adapter", {}, true)
      .then(setAdapter)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function runExtract() {
    setError(null);
    try {
      const result = await apiFetch<Record<string, unknown>>(
        "/whatsapp/ai/extract-product",
        {
          method: "POST",
          body: JSON.stringify({ text, language: "fr" }),
        },
        true,
      );
      setPreview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Extraction failed");
    }
  }

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">WhatsApp</h1>
      <p className="mt-2 text-ink-soft">
        Meta Cloud API wiring is ready. Phase 2 will connect the full conversation engine.
      </p>

      <div className="mt-8 rounded-2xl border border-line bg-foam p-5">
        <h2 className="font-display text-xl font-semibold">Adapter</h2>
        <pre className="mt-3 overflow-x-auto text-sm text-ink-soft">
          {adapter ? JSON.stringify(adapter, null, 2) : "Loading…"}
        </pre>
      </div>

      <div className="mt-6 max-w-2xl rounded-2xl border border-line bg-foam p-5">
        <h2 className="font-display text-xl font-semibold">AI product extract preview</h2>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          className="mt-3 w-full rounded-xl border border-line px-3 py-3"
        />
        <button
          type="button"
          onClick={() => void runExtract()}
          className="mt-3 rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white"
        >
          Extract structured product
        </button>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
        {preview ? (
          <pre className="mt-4 overflow-x-auto rounded-xl bg-ink p-4 text-sm text-citron">
            {JSON.stringify(preview, null, 2)}
          </pre>
        ) : null}
      </div>
    </div>
  );
}

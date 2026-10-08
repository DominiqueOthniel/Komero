"use client";

import { useEffect, useState } from "react";
import { apiFetch, Store } from "@/lib/api";

type Outbound = {
  type?: string;
  body?: string;
  buttons?: { id: string; title: string }[];
  filename?: string;
  caption?: string;
};

export default function WhatsAppPage() {
  const [store, setStore] = useState<Store | null>(null);
  const [adapter, setAdapter] = useState<Record<string, string> | null>(null);
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [simLog, setSimLog] = useState<Outbound[]>([]);
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);
  const [text, setText] = useState(
    "Nike Air Max 95 noire a 45000 FCFA, j'en ai 4 en taille 42 et 2 en taille 43.",
  );
  const [saleText, setSaleText] = useState("vente BBC 9000");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Record<string, string>>("/whatsapp/adapter", {}, true)
      .then(setAdapter)
      .catch((err: Error) => setError(err.message));
    apiFetch<Store[]>("/stores", {}, true)
      .then((stores) => setStore(stores[0] ?? null))
      .catch(() => undefined);
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

  async function simulate(message: string, buttonId?: string) {
    if (!store) return;
    setError(null);
    try {
      const result = await apiFetch<{
        outbound: Outbound[];
        result: Record<string, unknown>;
      }>(
        `/whatsapp/stores/${store.id}/simulate`,
        {
          method: "POST",
          body: JSON.stringify({
            from_number: "237670000111",
            text: message,
            button_id: buttonId,
          }),
        },
        true,
      );
      setSimLog(result.outbound || []);
      setLastResult(result.result || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    }
  }

  function lastButtons() {
    return [...simLog].reverse().find((m) => m.type === "buttons");
  }

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">WhatsApp</h1>
      <p className="mt-2 text-ink-soft">
        Sales, receipts, and AI product creation work in the simulator. Point Meta webhooks here for live WhatsApp.
      </p>

      <div className="mt-8 rounded-2xl border border-line bg-foam p-5">
        <h2 className="font-display text-xl font-semibold">Adapter</h2>
        <pre className="mt-3 overflow-x-auto text-sm text-ink-soft">
          {adapter ? JSON.stringify(adapter, null, 2) : "Loading…"}
        </pre>
      </div>

      <div className="mt-6 max-w-2xl rounded-2xl border border-line bg-foam p-5">
        <h2 className="font-display text-xl font-semibold">Sale + receipt simulator</h2>
        <p className="mt-2 text-sm text-ink-soft">
          Flow: record sale → Receipt button → No name → PDF receipt.
        </p>
        <input
          value={saleText}
          onChange={(e) => setSaleText(e.target.value)}
          className="mt-3 w-full rounded-xl border border-line px-3 py-3"
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void simulate(saleText)}
            className="rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white"
          >
            Send sale message
          </button>
          <button
            type="button"
            onClick={() => {
              const receiptBtn = lastButtons()?.buttons?.find((b) =>
                b.id.startsWith("receipt:"),
              );
              if (receiptBtn) void simulate(receiptBtn.title, receiptBtn.id);
            }}
            className="rounded-xl border border-line px-4 py-3 text-sm font-semibold"
          >
            Tap Receipt
          </button>
          <button
            type="button"
            onClick={() => {
              const noName = lastButtons()?.buttons?.find((b) =>
                b.id.startsWith("receipt_noname:"),
              );
              void simulate("No name", noName?.id || "receipt_noname:pending");
            }}
            className="rounded-xl border border-line px-4 py-3 text-sm font-semibold"
          >
            Tap No name
          </button>
        </div>
      </div>

      <div className="mt-6 max-w-2xl rounded-2xl border border-line bg-foam p-5">
        <h2 className="font-display text-xl font-semibold">AI product flow</h2>
        <p className="mt-2 text-sm text-ink-soft">
          Flow: describe product → Confirm / Edit / Cancel → published in catalog.
        </p>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          className="mt-3 w-full rounded-xl border border-line px-3 py-3"
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void simulate("", "add_product")}
            className="rounded-xl border border-line px-4 py-3 text-sm font-semibold"
          >
            Start add product
          </button>
          <button
            type="button"
            onClick={() => void simulate(text)}
            className="rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white"
          >
            Send product text
          </button>
          <button
            type="button"
            onClick={() => void simulate("Confirm", "product_confirm")}
            className="rounded-xl border border-line px-4 py-3 text-sm font-semibold"
          >
            Tap Confirm
          </button>
          <button
            type="button"
            onClick={() => void simulate("Edit", "product_edit")}
            className="rounded-xl border border-line px-4 py-3 text-sm font-semibold"
          >
            Tap Edit
          </button>
          <button
            type="button"
            onClick={() => void runExtract()}
            className="rounded-xl border border-line px-4 py-3 text-sm font-semibold"
          >
            Extract only
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
        {lastResult ? (
          <pre className="mt-4 overflow-x-auto rounded-xl bg-ink p-4 text-sm text-citron">
            {JSON.stringify({ result: lastResult, outbound: simLog }, null, 2)}
          </pre>
        ) : null}
        {preview ? (
          <pre className="mt-4 overflow-x-auto rounded-xl bg-ink p-4 text-sm text-citron">
            {JSON.stringify(preview, null, 2)}
          </pre>
        ) : null}
      </div>
    </div>
  );
}

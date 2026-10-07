"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch, Store } from "@/lib/api";

export default function StorePage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const list = await apiFetch<Store[]>("/stores", {}, true);
    setStores(list);
  }

  useEffect(() => {
    void refresh().catch((err: Error) => setError(err.message));
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await apiFetch<Store>(
        "/stores",
        {
          method: "POST",
          body: JSON.stringify({
            name,
            description,
            whatsapp_number: whatsapp || undefined,
            currency: "XAF",
          }),
        },
        true,
      );
      setName("");
      setDescription("");
      setWhatsapp("");
      setMessage("Store created.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create store");
    }
  }

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Store</h1>
      <p className="mt-2 text-ink-soft">Tenant store settings for your public shopfront.</p>

      <div className="mt-8 space-y-4">
        {stores.map((store) => (
          <div key={store.id} className="rounded-2xl border border-line bg-foam p-5">
            <h2 className="font-display text-xl font-semibold">{store.name}</h2>
            <p className="mt-1 text-sm text-ink-soft">/{store.slug}</p>
            <p className="mt-2 text-sm">{store.description || "No description"}</p>
            <p className="mt-2 text-sm text-ink-soft">
              WhatsApp: {store.whatsapp_number || "Not set"} · {store.currency} · {store.status}
            </p>
          </div>
        ))}
      </div>

      <form onSubmit={onCreate} className="mt-10 max-w-lg space-y-4 rounded-2xl border border-line bg-foam p-5">
        <h2 className="font-display text-xl font-semibold">Create store</h2>
        <label className="block text-sm font-medium">
          Name
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line px-3 py-3"
          />
        </label>
        <label className="block text-sm font-medium">
          Description
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line px-3 py-3"
            rows={3}
          />
        </label>
        <label className="block text-sm font-medium">
          WhatsApp number
          <input
            value={whatsapp}
            onChange={(e) => setWhatsapp(e.target.value)}
            placeholder="2376XXXXXXXX"
            className="mt-1 w-full rounded-xl border border-line px-3 py-3"
          />
        </label>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {message ? <p className="text-sm text-leaf">{message}</p> : null}
        <button type="submit" className="rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white">
          Create store
        </button>
      </form>
    </div>
  );
}

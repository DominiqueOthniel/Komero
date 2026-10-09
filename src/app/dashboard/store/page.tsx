"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch, Store } from "@/lib/api";

export default function StorePage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const list = await apiFetch<Store[]>("/stores", {}, true);
    setStores(list);
    const current = list[0];
    if (current) {
      setEditName(current.name);
      setEditDescription(current.description || "");
    }
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

  async function onRename(event: FormEvent) {
    event.preventDefault();
    const store = stores[0];
    if (!store) return;
    setError(null);
    setMessage(null);
    try {
      await apiFetch<Store>(
        `/stores/${store.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            name: editName.trim(),
            description: editDescription.trim() || null,
          }),
        },
        true,
      );
      setMessage("Boutique mise a jour.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mise a jour impossible");
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
            <p className="mt-2 text-sm">
              <a className="font-semibold text-leaf" href={`/shop/${store.slug}`}>
                Ouvrir le catalogue
              </a>
            </p>
          </div>
        ))}
      </div>

      {stores[0] ? (
        <form onSubmit={onRename} className="mt-10 max-w-lg space-y-4 rounded-2xl border border-line bg-foam p-5">
          <h2 className="font-display text-xl font-semibold">Modifier la boutique</h2>
          <label className="block text-sm font-medium">
            Nom
            <input
              required
              minLength={2}
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line px-3 py-3"
            />
          </label>
          <label className="block text-sm font-medium">
            Description
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line px-3 py-3"
              rows={3}
            />
          </label>
          <button type="submit" className="rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white">
            Enregistrer
          </button>
        </form>
      ) : null}

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

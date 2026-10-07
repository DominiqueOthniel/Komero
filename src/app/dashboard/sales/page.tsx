"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch, formatXafShort, Sale, Store } from "@/lib/api";

export default function SalesPage() {
  const [store, setStore] = useState<Store | null>(null);
  const [sales, setSales] = useState<Sale[]>([]);
  const [name, setName] = useState("BBC");
  const [price, setPrice] = useState("9000");
  const [quantity, setQuantity] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function load() {
    const stores = await apiFetch<Store[]>("/stores", {}, true);
    const current = stores[0] ?? null;
    setStore(current);
    if (!current) {
      setSales([]);
      return;
    }
    const list = await apiFetch<Sale[]>(`/stores/${current.id}/sales`, {}, true);
    setSales(list);
  }

  useEffect(() => {
    void load().catch((err: Error) => setError(err.message));
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!store) return;
    setError(null);
    try {
      await apiFetch(
        `/stores/${store.id}/sales`,
        {
          method: "POST",
          body: JSON.stringify({
            items: [
              {
                name,
                quantity: Number(quantity),
                unit_price: Number(price),
              },
            ],
          }),
        },
        true,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not record sale");
    }
  }

  async function makeReceipt(sale: Sale) {
    if (!store) return;
    setBusyId(sale.id);
    setError(null);
    try {
      await apiFetch(
        `/stores/${store.id}/sales/${sale.id}/receipt`,
        {
          method: "POST",
          body: JSON.stringify({ customer_name: null }),
        },
        true,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create receipt");
    } finally {
      setBusyId(null);
    }
  }

  if (!store) {
    return (
      <div>
        <h1 className="font-display text-3xl font-bold">Sales</h1>
        <p className="mt-2 text-ink-soft">Create a store first, then record sales.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Sales</h1>
      <p className="mt-2 text-ink-soft">
        POS sales recorded from WhatsApp or the dashboard, with PDF receipts.
      </p>

      <div className="mt-8 overflow-x-auto rounded-2xl border border-line bg-foam">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-line text-ink-soft">
            <tr>
              <th className="px-4 py-3 font-medium">Sale</th>
              <th className="px-4 py-3 font-medium">Items</th>
              <th className="px-4 py-3 font-medium">Total</th>
              <th className="px-4 py-3 font-medium">Receipt</th>
              <th className="px-4 py-3 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {sales.map((sale) => (
              <tr key={sale.id} className="border-b border-line last:border-0">
                <td className="px-4 py-3 font-semibold text-ink">{sale.public_code}</td>
                <td className="px-4 py-3">
                  {sale.items.map((item) => item.name).join(", ")}
                </td>
                <td className="px-4 py-3">{formatXafShort(sale.total_amount)}</td>
                <td className="px-4 py-3">
                  {sale.receipt ? (
                    <a
                      href={sale.receipt.verification_url || "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="font-semibold text-leaf"
                    >
                      {sale.receipt.number}
                    </a>
                  ) : (
                    <span className="text-ink-soft">None</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {!sale.receipt ? (
                    <button
                      type="button"
                      disabled={busyId === sale.id}
                      onClick={() => void makeReceipt(sale)}
                      className="rounded-lg bg-leaf px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
                    >
                      {busyId === sale.id ? "…" : "Receipt"}
                    </button>
                  ) : (
                    <a
                      href={sale.receipt.verification_url || "#"}
                      className="text-xs font-semibold text-leaf"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open
                    </a>
                  )}
                </td>
              </tr>
            ))}
            {sales.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-ink-soft">
                  No sales yet. Record one below or via WhatsApp: vente BBC 9000
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <form
        onSubmit={onCreate}
        className="mt-10 max-w-lg space-y-4 rounded-2xl border border-line bg-foam p-5"
      >
        <h2 className="font-display text-xl font-semibold">Record a sale</h2>
        <label className="block text-sm font-medium">
          Item
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line px-3 py-3"
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm font-medium">
            Price (XAF)
            <input
              required
              type="number"
              min={1}
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line px-3 py-3"
            />
          </label>
          <label className="block text-sm font-medium">
            Qty
            <input
              required
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line px-3 py-3"
            />
          </label>
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button type="submit" className="rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white">
          Save sale
        </button>
      </form>
    </div>
  );
}

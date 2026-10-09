"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch, formatXaf, Product, Store } from "@/lib/api";

export default function ProductsPage() {
  const [store, setStore] = useState<Store | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("1000");
  const [stock, setStock] = useState("1");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function load() {
    const stores = await apiFetch<Store[]>("/stores", {}, true);
    const current = stores[0] ?? null;
    setStore(current);
    if (!current) {
      setProducts([]);
      return;
    }
    const list = await apiFetch<Product[]>(`/stores/${current.id}/products`, {}, true);
    setProducts(list);
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
        `/stores/${store.id}/products`,
        {
          method: "POST",
          body: JSON.stringify({
            name,
            description,
            price: Number(price),
            stock_quantity: Number(stock),
            status: "published",
            images: [{ image_url: "/images/product-wax.jpg", position: 0 }],
          }),
        },
        true,
      );
      setName("");
      setDescription("");
      setPrice("1000");
      setStock("1");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create product");
    }
  }

  async function onDelete(product: Product) {
    if (!store) return;
    const ok = window.confirm(`Supprimer « ${product.name} » du catalogue ?`);
    if (!ok) return;
    setBusyId(product.id);
    setError(null);
    try {
      await apiFetch(`/stores/${store.id}/products/${product.id}`, { method: "DELETE" }, true);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Suppression impossible");
    } finally {
      setBusyId(null);
    }
  }

  if (!store) {
    return (
      <div>
        <h1 className="font-display text-3xl font-bold">Products</h1>
        <p className="mt-2 text-ink-soft">Create a store first, then add products.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Products</h1>
      <p className="mt-2 text-ink-soft">Catalog for {store.name}</p>

      <div className="mt-8 overflow-x-auto rounded-2xl border border-line bg-foam">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-line text-ink-soft">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Price</th>
              <th className="px-4 py-3 font-medium">Stock</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id} className="border-b border-line last:border-0">
                <td className="px-4 py-3 font-semibold text-ink">{product.name}</td>
                <td className="px-4 py-3">{formatXaf(product.price)}</td>
                <td className="px-4 py-3">{product.stock_quantity}</td>
                <td className="px-4 py-3 capitalize">{product.status}</td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    disabled={busyId === product.id}
                    onClick={() => void onDelete(product)}
                    className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-red-700"
                  >
                    {busyId === product.id ? "…" : "Supprimer"}
                  </button>
                </td>
              </tr>
            ))}
            {products.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-ink-soft">
                  No products yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <form onSubmit={onCreate} className="mt-10 max-w-lg space-y-4 rounded-2xl border border-line bg-foam p-5">
        <h2 className="font-display text-xl font-semibold">Add product</h2>
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
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm font-medium">
            Price (XAF)
            <input
              required
              type="number"
              min={0}
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line px-3 py-3"
            />
          </label>
          <label className="block text-sm font-medium">
            Stock
            <input
              required
              type="number"
              min={0}
              value={stock}
              onChange={(e) => setStock(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line px-3 py-3"
            />
          </label>
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button type="submit" className="rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white">
          Publish product
        </button>
      </form>
    </div>
  );
}

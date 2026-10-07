"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, formatXaf, Product, Store } from "@/lib/api";

export default function PublicShopPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const [store, setStore] = useState<Store | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const shop = await apiFetch<Store>(`/public/shops/${slug}`);
        const catalog = await apiFetch<Product[]>(`/public/shops/${slug}/products`);
        setStore(shop);
        setProducts(catalog);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Shop unavailable");
      }
    }
    if (slug) void load();
  }, [slug]);

  if (error) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold">Shop not found</h1>
        <p className="mt-2 text-ink-soft">{error}</p>
        <Link href="/en" className="mt-6 inline-block text-leaf">
          Back to Komero
        </Link>
      </main>
    );
  }

  if (!store) {
    return (
      <main className="flex min-h-screen items-center justify-center text-ink-soft">
        Loading shop…
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-foam">
      <header
        className="border-b border-line px-4 py-8"
        style={{ backgroundColor: `${store.primary_color}14` }}
      >
        <div className="mx-auto max-w-5xl">
          <p className="text-sm font-semibold text-leaf">Komero shop</p>
          <h1 className="mt-2 font-display text-4xl font-bold text-ink">{store.name}</h1>
          <p className="mt-2 max-w-2xl text-ink-soft">
            {store.description || "Browse products and order on WhatsApp."}
          </p>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-4 py-10">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => {
            const image = product.images[0]?.image_url || "/images/product-wax.jpg";
            return (
              <Link
                key={product.id}
                href={`/shop/${store.slug}/product/${product.id}`}
                className="overflow-hidden rounded-2xl border border-line bg-white no-underline transition-transform hover:-translate-y-0.5"
              >
                <div className="relative aspect-[4/3] bg-mist">
                  <Image src={image} alt={product.name} fill className="object-cover" />
                </div>
                <div className="p-4">
                  <h2 className="font-display text-lg font-semibold text-ink">{product.name}</h2>
                  <p className="mt-1 font-semibold text-leaf">{formatXaf(product.price)}</p>
                  <p className="mt-1 text-sm text-ink-soft">
                    {product.stock_quantity > 0 ? `${product.stock_quantity} in stock` : "Sold out"}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
        {products.length === 0 ? (
          <p className="text-ink-soft">No published products yet.</p>
        ) : null}
      </section>
    </main>
  );
}

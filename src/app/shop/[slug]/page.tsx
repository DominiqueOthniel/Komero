"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ShopCatalog } from "@/components/shop/ShopCatalog";
import { apiFetch, Category, Product, Store } from "@/lib/api";

export default function PublicShopPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const [store, setStore] = useState<Store | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [shop, catalog, cats] = await Promise.all([
          apiFetch<Store>(`/public/shops/${slug}`),
          apiFetch<Product[]>(`/public/shops/${slug}/products`),
          apiFetch<Category[]>(`/public/shops/${slug}/categories`),
        ]);
        setStore(shop);
        setProducts(catalog);
        setCategories(cats);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Boutique indisponible");
      }
    }
    if (slug) void load();
  }, [slug]);

  if (error) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold">Boutique introuvable</h1>
        <p className="mt-2 text-ink-soft">{error}</p>
        <Link href="/fr" className="mt-6 inline-block text-leaf">
          Retour a Komero
        </Link>
      </main>
    );
  }

  if (!store) {
    return (
      <main className="flex min-h-screen items-center justify-center text-ink-soft">
        Chargement de la boutique…
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <ShopCatalog store={store} products={products} categories={categories} />
    </main>
  );
}

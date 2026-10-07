"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { apiFetch, formatXaf, Product, Store } from "@/lib/api";

export default function PublicProductPage() {
  const params = useParams<{ slug: string; productId: string }>();
  const [store, setStore] = useState<Store | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [selectedVariant, setSelectedVariant] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const shop = await apiFetch<Store>(`/public/shops/${params.slug}`);
        const item = await apiFetch<Product>(
          `/public/shops/${params.slug}/products/${params.productId}`,
        );
        setStore(shop);
        setProduct(item);
        if (item.variants[0]) {
          setSelectedVariant(`${item.variants[0].name}:${item.variants[0].value}`);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Product unavailable");
      }
    }
    if (params.slug && params.productId) void load();
  }, [params.slug, params.productId]);

  const waLink = useMemo(() => {
    if (!store || !product) return "#";
    const lines = [
      "Hello, I would like to order:",
      "",
      product.name,
      selectedVariant ? `Variant: ${selectedVariant}` : null,
      `Quantity: ${quantity}`,
      "",
      `Store: ${store.name}`,
    ].filter(Boolean);
    const number = store.whatsapp_number || "";
    const text = encodeURIComponent(lines.join("\n"));
    return number ? `https://wa.me/${number}?text=${text}` : `https://wa.me/?text=${text}`;
  }, [store, product, quantity, selectedVariant]);

  if (error) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold">Product not found</h1>
        <p className="mt-2 text-ink-soft">{error}</p>
      </main>
    );
  }

  if (!store || !product) {
    return (
      <main className="flex min-h-screen items-center justify-center text-ink-soft">
        Loading product…
      </main>
    );
  }

  const image = product.images[0]?.image_url || "/images/product-wax.jpg";

  return (
    <main className="mx-auto grid min-h-screen max-w-5xl gap-8 px-4 py-10 md:grid-cols-2">
      <div className="relative aspect-square overflow-hidden rounded-2xl bg-mist">
        <Image src={image} alt={product.name} fill className="object-cover" priority />
      </div>
      <div>
        <Link href={`/shop/${store.slug}`} className="text-sm font-semibold text-leaf">
          Back to {store.name}
        </Link>
        <h1 className="mt-3 font-display text-4xl font-bold text-ink">{product.name}</h1>
        <p className="mt-3 text-2xl font-semibold text-leaf">{formatXaf(product.price)}</p>
        <p className="mt-4 leading-relaxed text-ink-soft">
          {product.description || "No description yet."}
        </p>

        {product.variants.length > 0 ? (
          <label className="mt-6 block text-sm font-medium">
            Variant
            <select
              value={selectedVariant}
              onChange={(e) => setSelectedVariant(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line px-3 py-3"
            >
              {product.variants.map((variant) => (
                <option
                  key={variant.id}
                  value={`${variant.name}:${variant.value}`}
                >
                  {variant.name}: {variant.value}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        <label className="mt-4 block text-sm font-medium">
          Quantity
          <input
            type="number"
            min={1}
            max={Math.max(product.stock_quantity, 1)}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            className="mt-1 w-32 rounded-xl border border-line px-3 py-3"
          />
        </label>

        <a
          href={waLink}
          className="mt-8 inline-flex min-h-14 items-center justify-center rounded-xl bg-[#0F6B5C] px-6 text-base font-bold text-white no-underline"
        >
          Order on WhatsApp
        </a>
      </div>
    </main>
  );
}

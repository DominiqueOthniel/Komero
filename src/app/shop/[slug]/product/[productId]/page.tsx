"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ProductMedia } from "@/components/shop/ProductMedia";
import { apiFetch, formatXafShort, Product, Store } from "@/lib/api";
import { startCatalogOrder } from "@/lib/catalogOrder";

export default function PublicProductPage() {
  const params = useParams<{ slug: string; productId: string }>();
  const [store, setStore] = useState<Store | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [selectedVariant, setSelectedVariant] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [ordering, setOrdering] = useState(false);

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
        setError(err instanceof Error ? err.message : "Article indisponible");
      }
    }
    if (params.slug && params.productId) void load();
  }, [params.slug, params.productId]);

  if (error) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold">Article introuvable</h1>
        <p className="mt-2 text-ink-soft">{error}</p>
      </main>
    );
  }

  if (!store || !product) {
    return (
      <main className="flex min-h-screen items-center justify-center text-ink-soft">
        Chargement de l&apos;article…
      </main>
    );
  }

  const image = product.images[0]?.image_url || "/images/product-wax.jpg";
  const accent = store.primary_color || "#0F6B5C";
  const inStock = product.stock_quantity > 0;

  return (
    <main className="shop-product-page">
      <div className="shop-product-shell">
        <Link href={`/shop/${store.slug}`} className="shop-back">
          ← {store.name}
        </Link>

        <div className="shop-product-grid">
          <div className="shop-product-media">
            <ProductMedia
              src={image}
              alt={product.name}
              sizes="(max-width: 720px) 100vw, 50vw"
              priority
            />
          </div>

          <div className="shop-product-copy">
            <p className="shop-kicker">{store.name}</p>
            <h1>{product.name}</h1>
            <p className="shop-product-price" style={{ color: accent }}>
              {formatXafShort(product.price)}
            </p>
            <p className={`shop-stock-line ${inStock ? "ok" : "out"}`}>
              {inStock
                ? `${product.stock_quantity} disponible${product.stock_quantity > 1 ? "s" : ""}`
                : "Epuise pour le moment"}
            </p>
            <p className="shop-product-desc">
              {product.description || "Demandez plus de details sur WhatsApp."}
            </p>

            {product.variants.length > 0 ? (
              <label className="shop-field">
                Variante
                <select
                  value={selectedVariant}
                  onChange={(e) => setSelectedVariant(e.target.value)}
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

            <label className="shop-field">
              Quantite
              <input
                type="number"
                min={1}
                max={Math.max(product.stock_quantity, 1)}
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
              />
            </label>

            <button
              type="button"
              className="shop-order-btn"
              style={{ backgroundColor: accent }}
              disabled={ordering}
              onClick={() => {
                setOrdering(true);
                void startCatalogOrder(store, {
                  product,
                  quantity,
                  variant: selectedVariant || null,
                }).finally(() => setOrdering(false));
              }}
            >
              {ordering ? "Ouverture…" : "Commander sur WhatsApp"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  apiFetch,
  DashboardStats,
  formatXaf,
  Store,
} from "@/lib/api";

export default function DashboardHomePage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const storeList = await apiFetch<Store[]>("/stores", {}, true);
        setStores(storeList);
        if (storeList[0]) {
          const dashboard = await apiFetch<DashboardStats>(
            `/stores/${storeList[0].id}/dashboard`,
            {},
            true,
          );
          setStats(dashboard);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      }
    }
    void load();
  }, []);

  const store = stores[0];

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Dashboard</h1>
      <p className="mt-2 text-ink-soft">
        Sales, products and store health for your WhatsApp shop.
      </p>

      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}

      {!store ? (
        <div className="mt-8 rounded-2xl border border-line bg-foam p-6">
          <h2 className="font-display text-xl font-semibold">Create your first store</h2>
          <p className="mt-2 text-ink-soft">
            Phase 1 dashboard store setup lives under Store.
          </p>
          <Link
            href="/dashboard/store"
            className="mt-4 inline-flex rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white no-underline"
          >
            Set up store
          </Link>
        </div>
      ) : (
        <>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <p className="font-semibold text-ink">{store.name}</p>
            <Link
              href={`/shop/${store.slug}`}
              className="text-sm font-semibold text-leaf"
              target="_blank"
            >
              Open public shop
            </Link>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: "Total sales", value: formatXaf(stats?.total_sales ?? 0) },
              { label: "Orders", value: String(stats?.orders_count ?? 0) },
              { label: "Products", value: String(stats?.products_count ?? 0) },
              { label: "Customers", value: String(stats?.customers_count ?? 0) },
            ].map((card) => (
              <div key={card.label} className="rounded-2xl border border-line bg-foam p-5">
                <p className="text-sm text-ink-soft">{card.label}</p>
                <p className="mt-2 font-display text-2xl font-bold text-ink">{card.value}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

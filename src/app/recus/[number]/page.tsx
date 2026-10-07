"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, formatXafShort, PublicReceipt } from "@/lib/api";

export default function PublicReceiptPage() {
  const params = useParams<{ number: string }>();
  const search = useSearchParams();
  const cle = search.get("cle") || "";
  const [receipt, setReceipt] = useState<PublicReceipt | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!params.number || !cle) {
        setError("Missing receipt key.");
        return;
      }
      try {
        const data = await apiFetch<PublicReceipt>(
          `/public/receipts/${params.number}?cle=${encodeURIComponent(cle)}`,
        );
        setReceipt(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Receipt unavailable");
      }
    }
    void load();
  }, [params.number, cle]);

  if (error) {
    return (
      <main className="mx-auto max-w-lg px-4 py-20">
        <h1 className="font-display text-3xl font-bold">Receipt not found</h1>
        <p className="mt-2 text-ink-soft">{error}</p>
      </main>
    );
  }

  if (!receipt) {
    return (
      <main className="flex min-h-screen items-center justify-center text-ink-soft">
        Loading receipt…
      </main>
    );
  }

  const saleDate = new Date(receipt.sale_date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const phone = receipt.store_phone
    ? receipt.store_phone.startsWith("+")
      ? receipt.store_phone
      : `+${receipt.store_phone}`
    : null;

  return (
    <main className="min-h-screen bg-[#f3efe8] px-4 py-8">
      <article className="mx-auto max-w-md rounded-sm bg-white px-6 py-8 shadow-sm">
        <header className="flex items-start justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-bold text-ink">{receipt.store_name}</h1>
            {phone ? <p className="mt-1 text-sm text-ink-soft">Tel.: {phone}</p> : null}
          </div>
          <div className="text-right">
            <p className="font-semibold text-ink">Receipt</p>
            <p className="text-sm text-ink-soft">{receipt.number}</p>
          </div>
        </header>

        <dl className="mt-8 space-y-3 text-sm">
          {[
            ["Date", saleDate],
            ["Date of sale", saleDate],
            ["Sale ID", receipt.sale_code],
            ["Customer", receipt.customer_name || "Sans nom"],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-[#8B5A2B]">{label}</dt>
              <dd className="font-medium text-ink">{value}</dd>
            </div>
          ))}
        </dl>

        <div className="mt-8 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#D9D2C5]">
                <th className="py-2 font-semibold">Item</th>
                <th className="py-2 text-right font-semibold">Qty</th>
                <th className="py-2 text-right font-semibold">Unit price</th>
                <th className="py-2 text-right font-semibold">Amount</th>
              </tr>
            </thead>
            <tbody>
              {receipt.items.map((item) => (
                <tr key={item.id} className="border-b border-[#eee7db]">
                  <td className="py-2">{item.name}</td>
                  <td className="py-2 text-right">{item.quantity}</td>
                  <td className="py-2 text-right">{formatXafShort(item.unit_price)}</td>
                  <td className="py-2 text-right">{formatXafShort(item.total_price)}</td>
                </tr>
              ))}
              <tr>
                <td colSpan={3} className="py-3 text-right font-semibold">
                  Total
                </td>
                <td className="py-3 text-right text-lg font-bold">
                  {formatXafShort(receipt.total_amount)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-10 space-y-3 text-sm">
          <p className="text-ink-soft">
            To check this document, open the address below.
          </p>
          <a
            href={receipt.verification_url}
            className="break-all text-[#8B5A2B] underline"
          >
            {receipt.verification_url}
          </a>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL}/public/receipts/${receipt.number}/pdf?cle=${encodeURIComponent(cle)}`}
            className="mt-4 inline-flex rounded-xl bg-leaf px-4 py-3 text-sm font-semibold text-white no-underline"
          >
            Download PDF
          </a>
        </div>

        <p className="mt-12 text-center text-xs text-[#8B5A2B]">
          Receipt generated with Komero · komero.app
        </p>
      </article>
    </main>
  );
}

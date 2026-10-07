import { ReactNode, Suspense } from "react";

export default function ReceiptLayout({ children }: { children: ReactNode }) {
  return <Suspense fallback={<main className="p-8 text-ink-soft">Loading…</main>}>{children}</Suspense>;
}

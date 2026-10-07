"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { apiFetch, setToken } from "@/lib/api";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/products", label: "Products" },
  { href: "/dashboard/orders", label: "Orders" },
  { href: "/dashboard/customers", label: "Customers" },
  { href: "/dashboard/conversations", label: "Conversations" },
  { href: "/dashboard/store", label: "Store" },
  { href: "/dashboard/whatsapp", label: "WhatsApp" },
  { href: "/dashboard/settings", label: "Settings" },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [userName, setUserName] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("komero_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    apiFetch<{ name: string }>("/auth/me", {}, true)
      .then((user) => {
        setUserName(user.name);
        setReady(true);
      })
      .catch(() => {
        setToken(null);
        router.replace("/login");
      });
  }, [router]);

  if (!ready) {
    return (
      <main className="flex min-h-screen items-center justify-center text-ink-soft">
        Loading dashboard…
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-mist md:grid md:grid-cols-[240px_1fr]">
      <aside className="border-b border-line bg-foam px-4 py-6 md:min-h-screen md:border-b-0 md:border-r">
        <Link href="/en" className="font-display text-xl font-bold text-leaf no-underline">
          Komero
        </Link>
        <p className="mt-1 text-sm text-ink-soft">{userName}</p>
        <nav className="mt-8 flex flex-wrap gap-2 md:flex-col md:gap-1">
          {links.map((link) => {
            const active =
              link.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-xl px-3 py-2 text-sm font-semibold no-underline ${
                  active ? "bg-leaf text-white" : "text-ink-soft hover:bg-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <button
          type="button"
          className="mt-8 text-sm font-semibold text-ink-soft"
          onClick={() => {
            setToken(null);
            router.push("/login");
          }}
        >
          Sign out
        </button>
      </aside>
      <main className="px-4 py-8 sm:px-8">{children}</main>
    </div>
  );
}

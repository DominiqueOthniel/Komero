"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ApiClientError, login, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("merchant@komero.test");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await login(email, password);
      setToken(result.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-16">
      <Link href="/en" className="mb-8 font-display text-2xl font-bold text-leaf no-underline">
        Komero
      </Link>
      <h1 className="font-display text-3xl font-bold text-ink">Merchant login</h1>
      <p className="mt-2 text-ink-soft">Manage your WhatsApp store from the dashboard.</p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block text-sm font-medium text-ink">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-white px-3 py-3 outline-none focus:border-leaf"
          />
        </label>
        <label className="block text-sm font-medium text-ink">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-white px-3 py-3 outline-none focus:border-leaf"
          />
        </label>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-leaf px-4 py-3 font-semibold text-white disabled:opacity-60"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="mt-6 text-sm text-ink-soft">
        No account?{" "}
        <Link href="/register" className="font-semibold text-leaf">
          Create one
        </Link>
      </p>
    </main>
  );
}

"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Me = {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  role: string;
};

export default function SettingsPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Me>("/auth/me", {}, true)
      .then(setMe)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Settings</h1>
      <p className="mt-2 text-ink-soft">Account details for your merchant workspace.</p>

      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}

      {me ? (
        <div className="mt-8 max-w-lg space-y-3 rounded-2xl border border-line bg-foam p-5 text-sm">
          <p>
            <span className="text-ink-soft">Name</span>
            <br />
            <span className="font-semibold text-ink">{me.name}</span>
          </p>
          <p>
            <span className="text-ink-soft">Email</span>
            <br />
            <span className="font-semibold text-ink">{me.email}</span>
          </p>
          <p>
            <span className="text-ink-soft">Phone</span>
            <br />
            <span className="font-semibold text-ink">{me.phone || "Not set"}</span>
          </p>
          <p>
            <span className="text-ink-soft">Role</span>
            <br />
            <span className="font-semibold capitalize text-ink">{me.role}</span>
          </p>
        </div>
      ) : (
        <p className="mt-8 text-ink-soft">Loading account…</p>
      )}
    </div>
  );
}

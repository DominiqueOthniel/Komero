"use client";

import { useEffect, useState } from "react";
import { apiFetch, Store } from "@/lib/api";

type Message = {
  id: string;
  direction: string;
  message_type: string;
  content: string | null;
  created_at: string;
};

type Conversation = {
  id: string;
  whatsapp_number: string;
  status: string;
  state: string;
  updated_at: string;
  messages: Message[];
};

export default function ConversationsPage() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const stores = await apiFetch<Store[]>("/stores", {}, true);
        const store = stores[0];
        if (!store) {
          setItems([]);
          return;
        }
        const conversations = await apiFetch<Conversation[]>(
          `/whatsapp/stores/${store.id}/conversations`,
          {},
          true,
        );
        setItems(conversations);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load conversations");
      }
    }
    void load();
  }, []);

  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Conversations</h1>
      <p className="mt-2 text-ink-soft">
        WhatsApp threads for onboarding, product creation, sales, and receipts.
      </p>
      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
      {items.length === 0 && !error ? (
        <div className="mt-8 rounded-2xl border border-dashed border-line bg-foam p-8 text-ink-soft">
          No conversations yet. Use the WhatsApp simulator to start one.
        </div>
      ) : (
        <div className="mt-8 space-y-4">
          {items.map((conversation) => {
            const latest = [...conversation.messages].sort((a, b) =>
              a.created_at.localeCompare(b.created_at),
            );
            return (
              <article
                key={conversation.id}
                className="rounded-2xl border border-line bg-foam p-5"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h2 className="font-display text-xl font-semibold text-ink">
                    {conversation.whatsapp_number}
                  </h2>
                  <p className="text-sm text-ink-soft">
                    {conversation.state} · {conversation.status}
                  </p>
                </div>
                <ul className="mt-4 space-y-2 text-sm">
                  {latest.slice(-6).map((message) => (
                    <li key={message.id} className="text-ink-soft">
                      <span className="font-semibold text-ink">
                        {message.direction === "inbound" ? "In" : "Out"}
                      </span>
                      {": "}
                      {message.content || `(${message.message_type})`}
                    </li>
                  ))}
                </ul>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function ConversationsPage() {
  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Conversations</h1>
      <p className="mt-2 text-ink-soft">
        State-based WhatsApp threads (onboarding, product creation, orders) land in Phase 2.
      </p>
      <div className="mt-8 rounded-2xl border border-dashed border-line bg-foam p-8 text-ink-soft">
        No conversations yet. Webhook stubs are live under the WhatsApp section.
      </div>
    </div>
  );
}

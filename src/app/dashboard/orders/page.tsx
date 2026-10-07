export default function OrdersPage() {
  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Orders</h1>
      <p className="mt-2 text-ink-soft">
        Order intake from WhatsApp arrives in Phase 4. Schema and statuses are already in the API.
      </p>
      <div className="mt-8 rounded-2xl border border-dashed border-line bg-foam p-8 text-ink-soft">
        No orders yet. When customers click Order on WhatsApp, merchants will manage PENDING through
        DELIVERED here.
      </div>
    </div>
  );
}

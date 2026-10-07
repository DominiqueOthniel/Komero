export default function CustomersPage() {
  return (
    <div>
      <h1 className="font-display text-3xl font-bold text-ink">Customers</h1>
      <p className="mt-2 text-ink-soft">
        Customer profiles are stored per store. This list fills when WhatsApp orders start flowing.
      </p>
      <div className="mt-8 rounded-2xl border border-dashed border-line bg-foam p-8 text-ink-soft">
        No customers yet.
      </div>
    </div>
  );
}

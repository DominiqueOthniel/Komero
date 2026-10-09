import { apiFetch, formatXafShort, Product, Store } from "@/lib/api";

export type CatalogOrderPayload = {
  product: Product;
  quantity?: number;
  variant?: string | null;
};

export function buildCatalogOrderMessage(
  store: Store,
  { product, quantity = 1, variant }: CatalogOrderPayload,
) {
  const lines = [
    "Bonjour, je voudrais commander :",
    "",
    product.name,
    variant ? `Variante : ${variant}` : null,
    `Quantite : ${quantity}`,
    `Prix : ${formatXafShort(product.price)}`,
    "",
    `Boutique : ${store.name}`,
    "",
    "KOMERO_ORDER",
    `store:${store.slug}`,
    `product:${product.id}`,
    `qty:${quantity}`,
    `price:${product.price}`,
  ];
  if (variant) lines.push(`variant:${variant}`);
  return lines.filter((line) => line !== null).join("\n");
}

export function catalogOrderWhatsAppUrl(
  store: Store,
  payload: CatalogOrderPayload,
) {
  const number = (store.whatsapp_number || store.phone || "").replace(/[^\d]/g, "");
  const text = encodeURIComponent(buildCatalogOrderMessage(store, payload));
  return number ? `https://wa.me/${number}?text=${text}` : `https://wa.me/?text=${text}`;
}

export async function notifyCatalogOrder(
  store: Store,
  payload: CatalogOrderPayload,
) {
  try {
    await apiFetch<{ order_id: string; order_ref: string }>(
      `/public/shops/${store.slug}/orders`,
      {
        method: "POST",
        body: JSON.stringify({
          product_id: payload.product.id,
          quantity: payload.quantity ?? 1,
          variant: payload.variant || undefined,
          unit_price: Number(payload.product.price),
        }),
      },
    );
  } catch {
    // WhatsApp deep link remains the fallback if notify fails.
  }
}

export async function startCatalogOrder(
  store: Store,
  payload: CatalogOrderPayload,
) {
  await notifyCatalogOrder(store, payload);
  const url = catalogOrderWhatsAppUrl(store, payload);
  window.open(url, "_blank", "noopener,noreferrer");
}

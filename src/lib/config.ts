const DEFAULT_WHATSAPP_NUMBER = "237653711921";
const DEFAULT_WHATSAPP_TEXT =
  "Bonjour Komero, je veux creer ma boutique";

export const siteConfig = {
  name: "Komero",
  whatsappNumber:
    process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? DEFAULT_WHATSAPP_NUMBER,
  whatsappUrl:
    process.env.NEXT_PUBLIC_WHATSAPP_URL ??
    `https://wa.me/${DEFAULT_WHATSAPP_NUMBER}?text=${encodeURIComponent(DEFAULT_WHATSAPP_TEXT)}`,
} as const;

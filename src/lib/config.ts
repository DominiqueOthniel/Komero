export const siteConfig = {
  name: "Komero",
  whatsappUrl:
    process.env.NEXT_PUBLIC_WHATSAPP_URL ??
    "https://wa.me/?text=Hello%20Komero%2C%20I%20want%20to%20create%20my%20shop",
} as const;

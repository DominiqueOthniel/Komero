# Komero

WhatsApp-first shop for sellers. This repo is the marketing site: a sharper take on the Klinbot landing experience, with stronger brand presence, less chat clutter in the first viewport, and a cooler teal–citron visual system.

## Develop

```bash
npm install
npm run dev
```

Open [http://localhost:3000/en](http://localhost:3000/en). French lives at `/fr`.

Set `NEXT_PUBLIC_WHATSAPP_URL` to your WhatsApp deep link for the primary CTA.

## Deploy on Netlify

1. Connect this GitHub repo in the Netlify dashboard.
2. Build settings come from `netlify.toml` (`npm run build`, Node 22).
3. Add site env `NEXT_PUBLIC_WHATSAPP_URL` with your WhatsApp deep link.
4. Deploy. Netlify’s OpenNext adapter handles App Router, caching, and `next/image` via the Image CDN.

Skew protection is enabled via `NETLIFY_NEXT_SKEW_PROTECTION` in `netlify.toml`.

## Stack

Next.js App Router, Tailwind CSS v4, Google fonts (Bricolage Grotesque + Manrope), Netlify OpenNext.

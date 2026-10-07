# Komero

WhatsApp-powered e-commerce SaaS for small merchants in Cameroon and Francophone Africa.

Merchants create and manage a store through WhatsApp, publish a mobile storefront, and track sales from a web dashboard. Currency defaults to FCFA (XAF). French-first, English-ready.

## Architecture

```
WhatsApp Customer
      |
Meta WhatsApp Cloud API
      |
FastAPI webhook + conversation engine + AI service
      |
PostgreSQL (multi-tenant by store_id)
      |
Next.js marketing + dashboard + public /shop/[slug]
```

Adapters keep WhatsApp and AI swappable (`mock` for local, Meta / future AI providers in production).

## Monorepo layout

- `src/` Next.js frontend (marketing, dashboard, public shop)
- `backend/` FastAPI API, SQLAlchemy models, Alembic migrations
- Phase 1 includes auth, stores, products, public shop, dashboard stats
- WhatsApp webhook endpoints and AI extract preview are scaffolded for Phase 2

## Prerequisites

- Node.js 22+
- Python 3.12+
- PostgreSQL 16+

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
PYTHONPATH=. python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Seed login:

- Email: `merchant@komero.cm`
- Password: `password123`
- Demo shop: `/shop/chez-awa`

## Frontend setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open:

- Marketing: [http://localhost:3000/en](http://localhost:3000/en)
- Login: [http://localhost:3000/login](http://localhost:3000/login)
- Dashboard: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- Public shop: [http://localhost:3000/shop/chez-awa](http://localhost:3000/shop/chez-awa)

Set `NEXT_PUBLIC_API_URL` to your FastAPI base (`http://localhost:8000/api/v1`).

## Deployment

- Frontend: Netlify (Next.js App Router via `@netlify/plugin-nextjs`). `netlify.toml` sets `publish = ".next"`. In the Netlify UI, clear any old Publish directory override such as `out` (that causes the classic Netlify 404 for `/login`, `/shop/...`, `/dashboard`).
- Backend: Render/Koyeb with `uvicorn app.main:app`
- Database: Supabase/Neon PostgreSQL via `DATABASE_URL`

## Security notes

- WhatsApp access tokens stay on the backend only
- JWT protects merchant APIs
- Every store/product query is scoped by owner/store_id
- AI never executes SQL; it returns structured JSON for backend services

## WhatsApp sales and receipts

Merchants can record a sale from WhatsApp:

```text
vente BBC 9000
```

Bot reply:

```text
Sale recorded: C-19H6.
[Receipt C-19H6] [Add a product] [More actions]
```

Then:

```text
Receipt for sale C-19H6: 1 item, 9 000 F. In whose name?
[No name] [Cancel]
```

Komero generates a PDF receipt (`Receipt-R-2026-0001.pdf`), sends it on WhatsApp, and publishes a verification page at `/recus/R-2026-0001?cle=...`.

Local simulator: Dashboard → WhatsApp (no Meta credentials required when `WHATSAPP_ADAPTER=mock`).

## Phase roadmap

1. Foundation: schema, auth, store/product APIs, dashboard, public shop
2. WhatsApp sales + PDF receipts + conversation engine (this branch)
3. AI product confirmation flow + images + full onboarding
4. Orders + customers + analytics
5. Voice, Mobile Money, delivery, subscriptions

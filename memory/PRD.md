# KhetSetu Product Requirements

## Original problem statement
Build a complete production-ready full-stack web application called KhetSetu for Smart India Hackathon 2026, connecting farmers directly with verified buyers and logistics partners to improve price transparency and reduce intermediary layers.

## Architecture decisions
- React frontend with responsive route-based application shell.
- FastAPI backend with MongoDB persistence using the preconfigured `MONGO_URL` and `DB_NAME`.
- Secure JWT access/refresh cookies, bcrypt passwords, role-aware protected routes.
- Seeded farmer, buyer, admin, produce, orders and notifications for an immediate SIH presentation flow.
- Prototype market prices and matching are explicitly labeled as simulated data.

## User personas
- Farmer: Arjun Das, small/marginal farmer in Nadia, West Bengal.
- Buyer: FreshMart Retail and verified produce buyers.
- Admin: KhetSetu operations manager overseeing network health.
- Presenter: SIH jury demonstrator using the guided demo mode.

## Core requirements
- Farmer-first Indian agricultural identity and plain-language UX.
- Working authentication, produce publishing, marketplace, order status workflow, logistics context, notifications, price transparency, admin metrics and guided demo.
- Responsive desktop, tablet and mobile layouts with accessible interaction states.

## Implemented — 2026-03-31
- Replaced starter template with KhetSetu public site, auth flows, dashboard, produce management, marketplace, orders, market prices, notifications, admin view and ten-step demo.
- Added MongoDB seed data and CRUD/status APIs for the core journey.
- Added test credentials and auth testing playbook.

## Prioritized backlog
- P0: connect real transporter assignment records and buyer-side order creation UX.
- P1: add full profile editing, forgot-password email delivery, admin farmer/buyer tables and demo reset UI.
- P2: add Hindi/Bengali translations, verified market API adapters, image uploads and richer analytics charts.
## Update (June 2026): Dark Landing Theme
- Landing page (Public component only) restyled to dark farming aesthetic: near-black soil background (#14100c), full-width generated wheat-field hero image with gradient overlay, forest green buttons, golden wheat headings/accents, warm off-white text.
- Scoped via `.dark-landing` class in index.css; app shell, auth, marketplace pages unchanged.

## Update (June 2026): App-wide Dark Theme
- Extended the dark farming theme globally via CSS variable overrides + targeted rules in index.css (bottom block): soil-black backgrounds, dark panels (#1f1812), golden wheat accents/eyebrows/tags, forest green primary buttons, warm off-white text, dark status pills, dark form inputs.
- Applies to dashboard, login/signup, produce, marketplace, orders, prices, notifications, admin, demo. Verified via screenshots (login, dashboard, marketplace, prices).

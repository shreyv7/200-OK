# Trellis

**Agentic AI growth curator — IABTM Hackathon**

Trellis is an agentic AI system that measures the gap between who you say you want to become and who your behavior shows you are — then continuously curates media, knowledge, experiences, and micro-missions to close it.

Built for the **Agentic AI for Human Potential** challenge: optimize for human potential, not attention.

## What it does

- **Identity Gap Engine** — live model of Declared Self vs Revealed Self with an explainable alignment score
- **Continuous Curation** — re-evaluates and refreshes your growth stack as behavior, capacity, and outcomes change
- **In-feed interception** — meets you in the scroll moment and morphs passive drift into purposeful growth
- **Guardian layer** — protects capacity; every intervention is explainable and dismissible
- **Trust Ledger** — logs what worked, what failed, and how the system adapts

## Tech stack

- **Frontend:** Next.js, React, Tailwind, shadcn/ui
- **Backend:** Next.js API routes
- **Database:** Supabase
- **LLM:** Google Gemini (AWS Bedrock fallback)
- **Search:** Tavily API

## Getting started

```bash
npm install
cp .env.example .env.local   # add your keys
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment variables

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `TAVILY_API_KEY` | Tavily search API key |

## Team

Built for [I Am Better Than Me](https://iambetterthanme.com/) hackathon — Pune, 2026.

## License

MIT

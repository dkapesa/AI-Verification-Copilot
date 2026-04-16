# Frontend

This frontend powers the analyst dashboard for AI Verification Copilot.

It is built with Next.js, TypeScript, and Tailwind CSS, and provides the user-facing interface for reviewing verification cases and inspecting persisted workflow state.

Current functionality includes:
- case queue view
- case detail view
- deterministic tool results panel
- AI review panel
- audit timeline
- persisted state loading on refresh

The frontend connects to the FastAPI backend and is designed to simulate an internal review console rather than a public-facing application.

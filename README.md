# A.M.E. - Autonomous Merchant Engine --- DORI 

AI agents can discover products, but traditional merchant checkout is not agent-native. A.M.E. turns the merchant into an AI-transactable endpoint.

It demonstrates a working end-to-end architecture where a human delegates intent to an AI Buyer, which then programmatically discovers a merchant, checks policy guardrails, negotiates autonomously with the Merchant Agent, and completes a strictly gated Razorpay test-mode transaction.

## How to Run

Terminal 1 (Backend):
```bash
uvicorn main:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm install
npm run dev
```

*Note: The previous Streamlit frontend (`app.py`) is preserved as a fallback during the migration testing phase. It can be run with `streamlit run app.py`.*

## Core Flow
- **Intent**: Natural language shopping queries parsed into structured JSON requests.
- **Discovery**: Real-time evaluation against an agent-readable product catalog.
- **Policy Engine**: Strict deterministic bounds (e.g. inventory limits, max discounts) that an LLM cannot override.
- **Negotiation**: Agent-to-agent counter-offers within safe financial limits.
- **Razorpay Checkout**: Seamless test-mode payment capturing.
- **Verification**: Zero-trust payment verification (paid state is derived ONLY from the Razorpay API, never the frontend).

## Setup
Please refer to `SETUP.md` for exact Windows installation instructions.

## Known Limitations
- Data persistence uses local `.json` instead of a full Postgres/Redis cluster to keep the demo lightweight.
- OpenAI is used for intent extraction, but a deterministic heuristic fallback is included if the key is missing.

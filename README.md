# Propra

**AI-native property regulation guidance for German homeowners.**

---

## What is Propra?

Propra helps homeowners in Germany understand what they are legally allowed to do with their property — building a fence, adding a window, extending a garden structure — without paying for a professional consultation.

It returns jurisdiction-specific, plain-language regulatory assessments with cited sources, so you can walk into any conversation with an architect or building authority already informed.

**Who is it for?**
- Renate (67, retired) — wants to know if she can build a taller hedge before calling anyone
- Tobias (41, self-employed) — wants to understand the rules before committing to an extension project
- Anyone in Germany who has a property question and doesn't know where to start

---

## Core User Journey

```
1. Goal Input
   └─ "What do you want to do with your property?"
      The user describes their intent in plain language.

2. Situation Funnel
   └─ A short, guided intake form collects the key facts:
      federal state, municipality, property type, and project details.

3. Regulatory Assessment
   └─ Propra queries its knowledge graph and document corpus,
      synthesises jurisdiction-specific rules, and returns a
      plain-German assessment with cited paragraphs.

4. Results + Living Assessment (teaser)
   └─ The user sees a clear verdict (Allowed / Conditional / Not Allowed),
      the relevant regulations cited, and a personalised next action.
      The Living Assessment updates as regulations change.
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Knowledge Graph | NetworkX |
| Vector Search | FAISS |
| LLM | Claude (Anthropic) via direct SDK |
| Orchestration | LangChain (optional) |
| Frontend | React, Tailwind CSS (mobile-first) |
| Validation | Pydantic v2 |

---

## Repo Structure

```
propra/
├── api/              # FastAPI route handlers
├── retrieval/        # RAG (FAISS) and knowledge graph query logic
├── graph/            # Knowledge graph: build, explore, visualize, audit (see graph/README.md)
├── prompts/          # LLM prompt files (.txt / .md)
├── schemas/          # Pydantic models for request/response validation
├── data/             # data/node inventory/*.md (LBO inventories), data/txt/*.txt (source text), data/raw/ (PDFs); graph.pkl by build
├── eval/             # Benchmark evaluation scripts
├── frontend/         # React frontend application
├── analytics/        # Event logging
├── tests/            # Pytest test suite
├── .env.example      # Required environment variables template
├── CLAUDE.md         # Agent conventions and code rules
└── README.md         # This file
```

---

## Running Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key

### Backend

```bash
# Clone the repo
git clone https://github.com/your-org/propra.git
cd propra

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the API server
uvicorn api.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and the API at `http://localhost:8000`.

---

## Knowledge graph (build, explore, audit)

From the repo root, with dependencies installed:

```bash
# Build graph (MBO + BW nodes, structural + domain + reference edges)
python -m propra.graph.build_graph

# Interactive node explorer
python -m propra.graph.explore

# Export to HTML (optional: --filter §5 §6 A1-07 §74 for a subgraph)
python -m propra.graph.visualize_html

# Audit relations (sample or export edges for review)
python -m propra.graph.audit_relations --sample 15
```

Full details and data pipeline: [propra/graph/README.md](propra/graph/README.md).

---

## Running Tests

```bash
pytest tests/
```

---

## Contributing

1. Fork the repository and create a feature branch (`git checkout -b feature/your-feature`)
2. Follow the conventions in [CLAUDE.md](./CLAUDE.md)
3. Ensure all new API endpoints have happy-path and error-path tests
4. Open a pull request with a clear description of what you changed and why
5. Enable the pre-commit hooks, setup (run once):

```
pip install pre-commit
pre-commit install
```

After installation, the hooks will automatically run before every commit.


---

## License

MIT © 2024 Propra Contributors

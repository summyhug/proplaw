# CLAUDE.md — Agent Conventions for Propra

This file defines the rules and conventions the Claude Code agent must follow throughout this project. Read it before making any change to this codebase.

---

## Product Context

- Propra is a **consumer product for German homeowners**. It is not a developer tool and not a B2B product.
- The end user is someone like **Renate** (67, retired, low technical confidence) or **Tobias** (41, wants to be informed before talking to an architect).
- Every output the product generates must be:
  - Written in **plain German**
  - Include a **cited source** (paragraph, regulation name, jurisdiction)
  - End with a **concrete next action** for the user
- Never generate UI copy that sounds like a legal disclaimer. It should sound like a **knowledgeable friend explaining the rules**.

---

## Code Conventions

### Python

- All Python files must include a **module-level docstring** explaining what the file does.
- All functions over 20 lines must include a **docstring**.
- Use **snake_case** for all Python identifiers.
- No hardcoded API keys — use environment variables loaded from `.env`. The `.env` file must never be committed.
- All API endpoints must include **input validation** (Pydantic) and return structured error messages:
  - **English** for developers (in the `detail` field)
  - **German** for end users (in the `user_message` field)
- Never push directly to main, always open a PR.

### JavaScript / React

- Use **camelCase** for all JavaScript/React identifiers.
- Components go in `frontend/src/components/`.

---

## Frontend Rules

- Every page and component must be **mobile-first** — design for 375px minimum width before considering desktop.
- Use **Tailwind CSS utility classes only**. Do not create custom CSS files unless there is no Tailwind equivalent.
- **Primary colour:** deep navy `#1A3355`
- **Accent colour:** warm amber `#C9952A`
- **Typography:**
  - Headlines: DM Serif Display (serif)
  - Body: DM Sans (sans-serif)
- **No dark mode** in MVP.
- Every form field must have a visible **German-language label and placeholder**.
- All buttons must have a **loading state**.
- No page should require **horizontal scrolling on mobile**.

---

## AI / Data Conventions

### Prompts

- Every LLM prompt must be stored as a `.txt` or `.md` file in `prompts/`. **Never inline prompts in code.**
- Every prompt file must begin with a comment block containing:
  ```
  # WHAT: What this prompt does
  # INPUTS: What variables it expects
  # OUTPUT FORMAT: What structure it returns
  ```

### LLM Outputs

- All LLM outputs must be **validated against a Pydantic schema** before being passed to the frontend.
- **Confidence must never be set to `HIGH`** when B-Plan data is absent from the corpus.

### Knowledge Graph

- Every **node** must include: `type`, `jurisdiction`, `source_paragraph`, `text`
- Every **edge** must include: `relation`, `sourced_from`

---

## Testing Conventions

- Every API endpoint must have at least **one happy-path test** and **one error-path test** in `tests/`.
- Every prompt must be tested against at least **5 sample inputs** before being used in the pipeline.
- KG queries must be tested against the **10 benchmark questions** defined in `eval/benchmark.py`.

---

## What This Agent Must Never Do

- Never generate **legal advice** — always regulatory information with cited sources.
- Never return a **`HIGH` confidence verdict** when corpus coverage is incomplete.
- Never add **features outside the current epic scope** without flagging it first with a comment and asking.
- Never skip **mobile optimisation** on any UI component.
- Never **inline secrets or API keys** in code, prompts, or config files.
- Never commit the `.env` file.

## Pull Request Summary
Provide a clear description of the changes. What specific part of the lead generation pipeline does this improve?

**Fixes # (issue number)**

---

## Scope of Change
- [ ] **Scraper Engine**: Playwright selectors, stealth-evasion, or site-specific logic.
- [ ] **AI Intent Engine**: GPT-4o prompt engineering or context-parsing logic.
- [ ] **Frontend**: Next.js 14 UI, Shadcn/ui, or Tailwind CSS.
- [ ] **Backend/Infra**: FastAPI endpoints, Redis Queue, or PostgreSQL schema.

---

## Critical Verification Checklist
For any logic affecting data extraction or AI parsing:

- [ ] **Stealth Verification**: I have verified the scraper passes bot-detection on target sites (e.g., using `playwright-extra-plugin-stealth`).
- [ ] **LLM Consistency**: I have confirmed the LLM output format (JSON/Search params) remains consistent with the existing parser.
- [ ] **Performance**: I have checked that the asynchronous Redis workers handle the new logic without memory leaks.
- [ ] **Deduplication**: If adding new sources, I have verified the deduplication logic prevents duplicate leads.

---

## Quality Standards
- [ ] **Linting**: I have run `npm run lint` (Frontend) or `black/flake8` (Python).
- [ ] **Environment**: No API keys or secrets are committed in this PR.
- [ ] **Apertre 3.0**: This contribution follows the competition's open-source guidelines.

---

## Visual Proof
*Mandatory for UI changes or terminal logs showing a successful "Stealth" scrape session.*

> [Paste Image/GIF Here]

---
*Created for the Lead Gen Tool*

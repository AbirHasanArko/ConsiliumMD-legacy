# ConsiliumMD · CARMA Supervisor Deck (HTML)

Browser-based slide deck for the supervisor briefing.

## How to view

Easiest: open `index.html` directly in any modern browser
(`file:///D:/Documents/HelloMed_X_CARMA/ConsiliumMD/supervisor_deck/index.html`).

Navigation:
- **Arrow keys** / **Space** — next/previous slide
- **Esc** — overview of all slides
- **F** — fullscreen
- **S** — speaker notes (plain text; `notes.js` plugin only opens if you're serving over HTTP)

If you also want presenter notes, run a tiny static server in this folder:

```powershell
cd D:\Documents\HelloMed_X_CARMA\ConsiliumMD\supervisor_deck
python -m http.server 8000
```

then visit <http://localhost:8000>.

## Files

- `index.html` — the deck itself (13 slides, inline SVG figures, 10 verified arXiv links)
- `theme.css` — custom navy/teal/amber palette and component styles
- `README.md` — this file

## Slides

1. Title
2. The problem with today's clinical LLMs
3. The core insight (epistemic vs. normative, with figure)
4. What CARMA is — and isn't
5. What's genuinely novel (4 cards: RPD, identifiability, gated routing, CECB-T)
6. Why this differs from prior work (comparison table)
7. System architecture (6-stage pipeline figure)
8. ConsiliumMD surface (Doctor / Reviewer / Admin)
9. Data model (ER-style SVG of the schema)
10. The paper's central claim (H2 quote + 4 hypotheses)
11. How we evaluate it (baselines / ablations / metrics + bar chart)
12. 10 related papers (each linked)
13. Takeaways

## Links

All 10 paper URLs are real arXiv abstracts (verified). Each paper card has both a
title link and an explicit URL with the ↗ arrow.

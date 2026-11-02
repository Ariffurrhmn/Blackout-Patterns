# Design brief: "Report Workbench" (from `index.html`)

A reusable description of the design used for the Bangladesh data-mining project report. Everything below is taken from the real CSS and JS in `index.html`, so you can recreate or adapt it.

---

## 1. What it is

A single-file, offline-capable, tabbed **report workbench**: dense research content (tables, cards, plans, source lists) made scannable by a left navigation rail, expandable cards, sortable tables and score visuals. It reads like a calm lab notebook, not a marketing page.

**Best for:** reports, research summaries, comparison/decision documents, project plans, dataset catalogues, audit write-ups. Anything with many items to compare and a lot of reference detail.

**Not for:** landing pages, storytelling pages, apps with heavy interaction.

---

## 2. Personality in three lines

- Quiet, analytical, trustworthy. Lots of whitespace, thin borders, almost no shadows.
- One strong colour (deep bottle green) used for meaning (selection, links, scores), plus one rare red used for warnings and the signature dot.
- Monospace for small labels and numbers; a characterful grotesque for headings; a humanist sans for reading.

---

## 3. Colour tokens

Define every colour as a token on `:root`, then redefine in dark mode. Components never use literal colours.

| Token | Light | Dark | Used for |
|---|---|---|---|
| `--bg` | `#f3f6f4` | `#0e1613` | Page background (green-tinted grey, not pure grey) |
| `--surface` | `#ffffff` | `#15201b` | Cards, tables, inputs |
| `--surface-2` | `#e8efeb` | `#1c2a24` | Table headers, chips, hover, notes |
| `--fg` | `#13201b` | `#e3ece7` | Body text (green-black, not pure black) |
| `--muted` | `#56675f` | `#93a69d` | Secondary text, labels |
| `--line` | `#d3ded8` | `#2a3a33` | Borders and dividers |
| `--accent` | `#0a6b4f` | `#55c99d` | Links, selected state, primary buttons, big numbers |
| `--accent-fg` | `#ffffff` | `#0c1a14` | Text on accent |
| `--accent-soft` | `#d6ebe2` | `#1b3a2e` | Selected tab, soft chips, highlighted week |
| `--flag` | `#c92a3a` | `#ff6f7a` | Warnings, "bad" callout, signature dot |
| `--flag-soft` | `#f8dfe1` | `#3a1e22` | Warning chip background |
| `--warn` | `#9a6a12` | `#e2b45e` | Caution callout, "unverified" tag |
| `--warn-soft` | `#f6ead2` | `#3a2f1a` | Caution chip background |

**Score ramp (1 to 5), a single-hue sequential scale used for heat cells:**

| | s1 | s2 | s3 | s4 | s5 | text on s4/s5 |
|---|---|---|---|---|---|---|
| Light | `#e3ece7` | `#c6ddd2` | `#97c6b1` | `#4fa283` | `#0a6b4f` | `#ffffff` |
| Dark | `#1c2a24` | `#24443a` | `#2f6b55` | `#3d9a77` | `#55c99d` | `#0c1a14` |

**Rules:** neutrals are tinted toward the accent hue. Semantic colours (flag, warn) are separate from the accent. Dark mode is designed, not inverted: lighter accent, deeper surfaces, same contrast roles.

**Theme plumbing (copy this pattern exactly):**
```css
:root { /* all light tokens */ color-scheme: light; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { /* dark tokens */ color-scheme: dark; } }
:root[data-theme="dark"] { /* same dark tokens */ color-scheme: dark; }
body { background: var(--bg); color: var(--fg); }
```

---

## 4. Typography

| Role | Font | Weights | Use |
|---|---|---|---|
| Display | **Bricolage Grotesque** (opsz 12..96) | 500, 700 | Headings, big rank numbers, totals |
| Body | **IBM Plex Sans** | 400, 500, 600 (+400 italic) | All reading text, buttons, tables |
| Utility | **IBM Plex Mono** | 400, 500 | Eyebrows, chips, table headers, numbers, URLs, code |

Fallbacks: display and body → `"Segoe UI", system-ui, sans-serif`; mono → `ui-monospace, "Cascadia Mono", Consolas, monospace`.

Google Fonts link:
`https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap`

**Scale**
- Base: 15px / 1.55.
- H1: `clamp(28px, 4.2vw, 44px)`, 700, tight line-height 1.15, letter-spacing −0.01em.
- H2 (view title): `clamp(22px, 2.6vw, 30px)`, 700.
- H3 (card title): 18–20px, 700. Sub-section H3: 18px.
- Small text: 12.5–14px. Mono labels: 11–12px.
- Headings use `text-wrap: balance`. Reading text capped around 68–80 characters wide.
- **Mono eyebrow/label style:** 11–12px, uppercase, letter-spacing 0.06–0.08em, muted colour. Used above the title, on table headers, on card section labels ("PITCH", "DATASETS", "RISKS").
- Numbers in columns use `font-variant-numeric: tabular-nums`.

---

## 5. Shape, spacing, elevation

- **Radius:** 10px for cards, tables and callouts; 8px for buttons, tabs and small boxes; 999px for pills and chips; 4–5px for tiny marks.
- **Borders over shadows:** 1px `--line` borders define objects. There are no box shadows anywhere.
- **Spacing:** flex/grid `gap` only (no margin stacking). Gaps of 6, 8, 12, 16, 24, 32px. Card padding 16–20px.
- **Page gutter:** `padding-inline: clamp(16px, 3vw, 32px)`, content max-width **84rem**, centred.

---

## 6. Layout

**App shell:** two columns on desktop: a **200px left rail** (sticky, `top: 16px`) and a fluid content column, 32px gap.

**Under 860px:** the rail becomes a **horizontal scrolling tab strip**, sticky at the top with the page background and a bottom border; the "legend note" under the rail is hidden.

**Header:** mono eyebrow line (what, where, date) → large H1 with a **small red dot** after the title (the one signature mark) → a facts strip on the right/below with bold mono numbers ("~50 candidates logged · 12 shortlisted · …"), separated from the content by a 1px border.

**Responsive breakpoints used:** 1100px (three-up cards → single column), 1000px (callouts → single column), 900px (two-column splits → single), 860px (shell → rail strip), 640px (card summary → stacked), 520px (week timeline → single column).

**Everything wide scrolls inside its own container** (`.tscroll`, `overflow-x: auto`), so the page never scrolls sideways. Flex/grid children that hold text get `min-width: 0`.

---

## 7. Components

**Navigation rail (tabs).** Vertical list of buttons; label left, mono count right. Default muted; hover → `--surface-2`; selected → `--accent-soft` background, count turns accent. ARIA `tablist`/`tab`; arrow keys move between tabs.

**Top-pick cards.** White surface, 1px border, 20px padding. Big **display number** (40px, accent) top-left, family chip top-right, title, short paragraph, mono chips for key facts, five score rows, then a filled button + ghost button pinned to the bottom (`margin-top: auto`).

**Score "pips".** Five 9px rounded squares, filled with accent up to the score, empty ones `--s1` with a hairline. Label (muted), pips, mono value in a 3-column grid. Total score uses the display font at 28px with "/ 25" in small mono.

**Chips.** Mono 12px pill, `--surface-2` background. Variants: `acc` (accent-soft), `flag` (flag-soft + flag text), `warn` (warn-soft + warn text). They wrap and break long words.

**Expandable idea cards (`<details>`).** Closed: number + "Top n" badge (accent fill, tiny uppercase) | title + one-line summary + chips | total score + chevron. Open: border turns accent-tinted, body splits into a main column and a 260px side column (scores, effort, key question). Section labels inside use the mono-uppercase style.

**Tables.** White surface, 1px outer border, 10px radius. Header row on `--surface-2` with mono uppercase labels; 9×12px cell padding; hairline row dividers; no zebra. Sortable headers are borderless buttons with an arrow that turns accent when active.

**Heat cells.** 28×24px rounded squares showing the score on the 1–5 ramp. **Total bars:** 8px track with an accent fill plus a mono number.

**Callouts.** Surface background, 3px **left border** in `--warn` (caution) or `--flag` (problem), square left corners, rounded right corners. Bold short title + one or two sentences.

**Note box.** `--surface-2` background, 8px radius, small mono bold label ("MY DATA CHECK") followed by text.

**Week timeline.** Grid of small cards (7 columns on wide screens, 2 or 1 on narrow). Each shows a mono "Week n" label and one line of text. Milestone weeks get an accent border, `--accent-soft` fill and a mono tag ("Mid-term demo").

**Buttons.** Primary: accent fill, white text, 8px radius, 600 weight, hover brightens. Ghost: transparent, accent text, inset 1px `--line`. Segmented filters: pill buttons with inset border; the active one inverts (foreground colour as background).

**Inputs.** Search and select: 14px, 8px radius, 1px `--line`, `--surface` background. Search max width 320px.

**Source lists.** One card per group; each entry is a muted description line over a mono URL link (`word-break: break-all`).

---

## 8. Behaviour

- Single page; sections are `hidden` panels switched by tab. The URL hash holds the current view (`#round2`), and the last view is remembered in `localStorage` inside `try/catch`.
- Buttons inside content deep-link to other views and open a specific card ("Open 14-week plan", "Full details").
- Search, filter and sort re-render the list instantly (no page reload).
- Cards open and close natively with `<details>`.
- Accessibility: visible `:focus-visible` outline (2px accent, 2px offset), semantic roles, text never clipped, real `<a href>` links opening in a new tab with `rel="noopener"`.
- Motion: only a 0.15s chevron rotation, and only if `prefers-reduced-motion` allows it.
- Content is complete on load; nothing waits on a scroll observer.

---

## 9. Writing style

Plain sentences, specific numbers, no marketing language. Short labels in the mono style. Anything unconfirmed is tagged "unverified" in a small warn chip. Pilots and negative results are stated as plainly as positive ones.

---

## 10. How to adapt it to another project

1. **Re-skin by changing one hue.** Replace the green family (`--accent`, `--accent-soft`, the `--s1…s5` ramp, and the tint of the neutrals) with another hue; keep `--flag` red and `--warn` amber as the semantic colours. Check the accent has at least 4.5:1 contrast against `--surface` and against `--bg`.
2. **Keep the signature small.** The red dot after the H1 is the only decoration. Swap it for a mark that fits the new subject, or drop it.
3. **Keep the fonts unless the subject calls for a different personality.** If you change them, keep the three roles (characterful display, readable body, mono for labels and data).
4. **Reuse the data-driven structure.** In `index.html` the content lives in JS arrays (`IDEAS`, `R2`, `PLANS`, `REJECTED`, `SOURCES`) and the views render from them. New project = new arrays, same renderers.
5. **Remove what you do not need.** The score pips, heat cells and week timeline are specific to ranking and planning; the shell, tabs, cards, tables, chips, callouts and notes are generic.

---

## 11. Paste-ready prompt

> Build a single-file, offline HTML report with a left-rail tabbed layout (200px sticky rail on desktop, horizontal scrolling tab strip under 860px). Visual style: calm lab-notebook. Page background `#f3f6f4`, white cards with 1px `#d3ded8` borders and 10px radius, no shadows, deep bottle-green accent `#0a6b4f` (dark mode `#55c99d`), red `#c92a3a` only for warnings and one small dot after the H1, amber for cautions. Define all colours as tokens on `:root` with a designed dark mode (`prefers-color-scheme` plus `data-theme`), and set `color-scheme`. Fonts from Google Fonts: Bricolage Grotesque (700) for headings, IBM Plex Sans for text, IBM Plex Mono for small uppercase labels, chips, table headers and numbers. Base 15px/1.55, fluid headings with `clamp`, `text-wrap: balance`. Components: mono-eyebrow header with a facts strip; top-pick cards with a large display number; mono pill chips; five-pip score rows and 1–5 heat cells from one green ramp; expandable `<details>` cards with a main column and a 260px side column; sortable tables inside `overflow-x: auto` wrappers with mono uppercase headers on a tinted row; callouts with a 3px left border; a note box; a week-by-week timeline grid with highlighted milestones; segmented filter pills and a search box. Behaviour: view held in the URL hash and remembered in `localStorage` (try/catch), keyboard arrows between tabs, visible focus outline, no horizontal page scroll at 375px, content fully visible on load, motion only if reduced-motion is not requested. Plain, specific writing; mark unconfirmed facts with a small "unverified" chip.

---
name: revision-site-brief
description: Turns the documents of a Claude project (lectures, tutorials, past exams, notes) into a compact zip of .md design files for an interactive revision site, built by Claude Code. Create or update.
---

# Design folder for a revision website

## Workflow

1. The user gathers course documents in a Claude project (lectures, handouts, tutorials, solutions, past exams, notes, code, meeting notes). Past conversations in the project count as context.
2. **This skill** produces a zip of `.md` design files.
3. The user drops the zip into Claude Code, opened on a GitHub repo, with the `revision-site-builder` skill. Claude Code builds, tests and pushes to `main`; Netlify redeploys on every push.
4. When new documents arrive, run this skill again in **update mode** (section 7): it produces a small delta zip.

**Division of labour.** Everything that is the same for every site (stack, technical constraints, search, workshop, interactive-diagram reliability, testing, working method) lives in the `revision-site-builder` skill. **Do not restate it in the folder.** The folder holds only what is specific to this course: content, exercises, diagnosis, widgets, decisions, and any deliberate deviation from the defaults.

**Self-sufficiency.** Claude Code will not see the documents, this conversation, or the user. Every course-specific fact it needs must be in the folder, and every ambiguity must be resolved here.

## Token budget (read first)

The folder is read in full by Claude Code, and every token you write is paid twice: once here as output, once there as input. Aim for **dense, non-redundant files**:

- **Each fact lives in one place.** Content in `02`, exercises in `03`, widgets in `04`. Elsewhere, refer to it by ID (`see Q3.2`, `F4`, `W3.1`), never copy it.
- **Structured data in YAML blocks** (formats in `references/file-formats.md`). Claude Code imports them with a script instead of retyping them, and `scripts/check_folder.py` validates them.
- **No boilerplate**: no generic teaching advice, no restated tech stack, no filler sentences. Bullet points over prose.
- **Write files with code** (create them directly in the sandbox). Never echo file contents in the chat; the final reply is one line per file.
- **Ask all open questions in one message**, not one by one.
- Work in a **fresh conversation** in the project rather than at the end of a long one: the whole conversation is re-read on every turn.
- Copy `templates/00_BRIEF.md` and fill it; don't rewrite it from scratch.

## Language

- Design files: English, unless the user asks otherwise.
- Site content and UI: the user's language (French users: French, informal "tu", direct and kind tone, unless told otherwise). Write `prompt`, `solution`, content text directly in that language. State the site language in `00_BRIEF.md`.

## 1. Inventory and questions

1. Read every project document; list what exists (lectures, handouts, tutorials, solutions, past exams, lab work, code, meeting notes, existing diagnosis).
2. Collect the **essentials**. If one is missing, ask (all at once); never invent:
   - **scope**: chapters in and out;
   - **assessment**: type, date, duration, allowed documents, marking scheme (MCQ penalty included), recurring exercises;
   - **diagnosis**: what the user knows. If none exists, offer a short test (≈10 questions) answered off the top of their head in the chat. Otherwise a self-description. Never inferred;
   - **project** (if any): what was really done, who asks questions at the oral;
   - **publication**: the site is public. What must not appear (full names, IPs, private code, photos, copyrighted material).
3. List **inconsistencies** between documents (notation, values, definitions). Get the user's decision or propose a precedence rule. Record each one.

## 2. Ground rules

- **Invent nothing.** Teaching content only from the documents; project facts only from project sources. If data doesn't exist, say so.
- **Origin tags** on every section, shown as badges. Course set: [Lecture] [Handout] [Tutorial] [Past exam] [Prerequisite] [Inferred]. Project set: [Project] [Theory] [Background] [To verify] [Inferred]. Translate labels into the site language.
- **Verify every number by code** before writing it. Flag values read from hard-to-read handwriting, with the recomputed value.
- **Confidentiality**: clean sources (IPs, credentials, infrastructure, private code, names) before copying.
- **Stable IDs**: chapter slugs (`ch03-routing`), items (`Q3.2`), generators (`GEN-3A`), widgets (`W3.1`), misconceptions (`F4`). They are the site's progress keys and never change across updates.

## 3. Folder contents

Zip `<CODE>_for_Claude_Code.zip`, one root folder `<CODE>_for_Claude_Code/`. Exact formats: **read `references/file-formats.md` before writing files 01–07.**

| File | Content | Required |
|---|---|---|
| `00_BRIEF.md` | from `templates/00_BRIEF.md`: context, scope, assessment, site specifics, visual direction, decisions, deviations, acceptance criteria | yes |
| `01_DIAGNOSIS.md` | misconceptions (F#), strengths, gaps, priority order | yes |
| `02_COURSE_CONTENT.md` | source of truth: one section per chapter, tagged, all exact formulas, keywords | yes |
| `03_EXERCISES.md` | YAML items (quiz, workshop, exam, oral), generators, exam structure | yes |
| `04_INTERACTIVE_MODULES.md` | YAML widget specs, search reference queries, training-mode specifics | yes |
| `05_PROJECT_SOURCES.md` | project timeline, real cleaned code excerpts, commands | project only |
| `06_GLOSSARY.md` | table: acronym, meaning, definition, synonyms, chapter | if > ~15 terms (else end of `02`) |
| `07_UPDATE.md` | change table | update mode only |

Visual direction: write a short one per site (concept, signature motif, meaningful colours with hex values, fonts). Guidance: `references/visual-direction.md`.

## 4. What the folder must guarantee

- Every misconception F# has a "Watch out" location in `02`, at least one quiz item and one workshop item (`misconception: F#`), and where possible a widget that demonstrates it.
- Every chapter has workshop material: at least one generator, or 10–15 items of varied kinds.
- Every P1 widget has inputs with ranges and defaults, numbered steps with a "why", edge cases, and 2–4 reference states computed by code.
- 5–10 search reference queries (including one without accents, one with a typo, one acronym).
- The assessment is described precisely enough to reproduce (duration, parts, marks, penalty).
- No "ask the user", TODO or placeholder left.

## 5. Check and zip

Run `python3 scripts/check_folder.py <folder>`. It validates the YAML blocks, IDs, cross-references, workshop coverage, widget specs and leftovers, flags IP-like strings, and writes the zip next to the folder. Fix every error; review warnings. Then deliver the zip with one line per file and the list of points the user still needs to confirm, if any.

## 6. Final reply

Short: the zip, one line per file, open points, and a one-line reminder to add this zip to the project's files (the next update needs it). No summary of the contents (the user can open the files).

## 7. Update mode

Use when a site built from an earlier folder is online and the project has grown.

1. Get the previous folder (project or conversation). If unavailable, ask for it, or at least the list of slugs and IDs: without them, user progress can't be preserved.
2. Produce a **delta folder** `<CODE>_for_Claude_Code_v2.zip` containing only:
   - `00_BRIEF.md`: a short update brief (what changed in scope or assessment; everything else "unchanged");
   - `07_UPDATE.md`: the change table (format in `references/file-formats.md`);
   - the **new or changed** parts only: new chapters in `02`, new or modified YAML blocks in `03`/`04`, updated `01`/`06` if they changed. The site repo already holds the rest.
3. **Never renumber.** Existing slugs and IDs stay identical; new elements get new IDs; removed IDs are listed in `07` and never reused.
4. Include widgets the user reported as buggy, with the symptom and steps to reproduce.
5. Run `scripts/check_folder.py --delta`.

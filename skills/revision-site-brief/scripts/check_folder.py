#!/usr/bin/env python3
"""Validate a revision-site design folder, then zip it.

Usage:
  python3 check_folder.py <folder> [--delta] [--no-zip]

Errors block the zip; warnings are printed for review.
Formats: see ../references/file-formats.md
"""
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is missing: pip install pyyaml (add --break-system-packages if needed)")

REQUIRED = ["00_BRIEF.md", "01_DIAGNOSIS.md", "02_COURSE_CONTENT.md",
            "03_EXERCISES.md", "04_INTERACTIVE_MODULES.md"]
ITEM_KINDS = {
    "mcq": ["choices", "correct"],
    "number": ["answer"],
    "short": ["accepted"],
    "cloze": ["text", "blanks"],
    "match": ["pairs"],
    "order": ["sequence"],
    "card": ["back"],
    "open": ["criteria", "solution"],
    "oral": ["short_answer", "key_points"],
}
YAML_BLOCK = re.compile(r"```yaml[^\n]*\n(.*?)```", re.S)
CHAPTER = re.compile(r"^## Chapter .*\{#([a-z0-9][a-z0-9-]*)\}\s*$", re.M)
SUBSECTION = re.compile(r"^### (\d+\.\d+) ", re.M)
MISCONCEPTION_ROW = re.compile(r"^\|\s*(F\d+)\s*\|", re.M)
LEFTOVER = re.compile(r"\b(TODO|TBD|FIXME)\b|ask the user|demander à l'utilisateur", re.I)
PLACEHOLDER = re.compile(r"<(?:[A-Z][A-Za-z /,.'-]{1,60}|[a-z][a-z ,./'()-]{2,60})>")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def load_blocks(path: Path, rep: Report):
    objs = []
    for n, raw in enumerate(YAML_BLOCK.findall(path.read_text(encoding="utf-8")), 1):
        try:
            obj = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            rep.err(f"{path.name}: YAML block #{n} does not parse: {str(e).splitlines()[0]}")
            continue
        if not isinstance(obj, dict):
            rep.err(f"{path.name}: YAML block #{n} is not a single object")
            continue
        obj["_file"] = path.name
        objs.append(obj)
    return objs


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    delta, no_zip = "--delta" in argv, "--no-zip" in argv
    if len(args) != 1:
        sys.exit(__doc__)
    folder = Path(args[0]).resolve()
    rep = Report()

    # 1. files
    present = {p.name for p in folder.iterdir() if p.is_file()}
    needed = ["00_BRIEF.md", "07_UPDATE.md"] if delta else REQUIRED
    for f in needed:
        if f not in present:
            rep.err(f"missing file {f}")

    def read(name):
        p = folder / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    # 2. chapters and misconceptions
    content = read("02_COURSE_CONTENT.md")
    slugs = CHAPTER.findall(content)
    for slug, c in Counter(slugs).items():
        if c > 1:
            rep.err(f"02: chapter slug {slug} used {c} times")
    for part in re.split(r"(?=^### \d+\.\d+ )", content, flags=re.M)[1:]:
        head = part.splitlines()[0]
        if "Keywords:" not in part:
            rep.warn(f"02: no 'Keywords:' line in '{head[:60]}'")
        if not re.search(r"\[[^\]]+\]", head):
            rep.warn(f"02: no origin tag in '{head[:60]}'")
    if not delta and not slugs:
        rep.err("02: no '## Chapter N — Title {#slug}' heading found")
    fids = set(MISCONCEPTION_ROW.findall(read("01_DIAGNOSIS.md")))

    # 3. YAML objects
    objs = []
    for name in sorted(present):
        if name.endswith(".md"):
            objs += load_blocks(folder / name, rep)
    ids = Counter(o["id"] for o in objs if "id" in o)
    for i, c in ids.items():
        if c > 1:
            rep.err(f"ID {i} defined {c} times")
    by_id = {o["id"]: o for o in objs if "id" in o}

    def unknown_chapter(o):
        ch = o.get("chapter")
        if ch and ch not in slugs:
            (rep.warn if delta else rep.err)(f"{o.get('id', '?')}: unknown chapter '{ch}'")

    def check_misconception(o):
        m = o.get("misconception")
        if m and m not in fids:
            (rep.warn if delta else rep.err)(f"{o.get('id', '?')}: misconception {m} not in 01")

    items = [o for o in objs if o.get("kind") in ITEM_KINDS]
    gens = [o for o in objs if o.get("kind") == "generator"]
    widgets = [o for o in objs if o.get("kind") == "widget"]
    queries = [q for o in objs if o.get("kind") == "search-queries" for q in o.get("queries", [])]

    for o in objs:
        k = o.get("kind")
        if k is None:
            rep.err(f"{o['_file']}: YAML block without 'kind' ({o.get('id', 'no id')})")
        elif k not in ITEM_KINDS and k not in {"generator", "widget", "search-queries", "exam", "training"}:
            rep.err(f"{o.get('id', o['_file'])}: unknown kind '{k}'")

    for o in items:
        for f in ["id", "chapter", "prompt", *ITEM_KINDS[o["kind"]]]:
            if f not in o and not (o["kind"] == "cloze" and f == "prompt"):
                rep.err(f"{o.get('id', '?')}: missing field '{f}' for kind {o['kind']}")
        if o["kind"] == "mcq" and isinstance(o.get("choices"), dict):
            bad = [c for c in o.get("correct", []) if c not in o["choices"]]
            if bad:
                rep.err(f"{o['id']}: correct {bad} not among choices")
        if o["kind"] == "number" and not isinstance(o.get("answer"), (int, float)):
            rep.err(f"{o.get('id')}: 'answer' must be a number")
        if not o.get("use"):
            rep.warn(f"{o.get('id')}: no 'use' field (quiz/workshop/exam/oral)")
        unknown_chapter(o)
        check_misconception(o)

    for g in gens:
        for f in ["id", "chapter", "params", "answer_format", "method", "reference"]:
            if f not in g:
                rep.err(f"{g.get('id', '?')}: generator missing '{f}'")
        unknown_chapter(g)
        check_misconception(g)

    for w in widgets:
        for f in ["id", "chapter", "priority", "inputs", "steps"]:
            if f not in w:
                rep.err(f"{w.get('id', '?')}: widget missing '{f}'")
        if w.get("priority") == "P1":
            for f in ["edge_cases", "reference"]:
                if not w.get(f):
                    rep.err(f"{w.get('id')}: P1 widget needs '{f}'")
        for q in w.get("quiz", []) or []:
            if q not in by_id and not delta:
                rep.err(f"{w.get('id')}: quiz item {q} not found")
        for s in w.get("steps", []) or []:
            if isinstance(s, dict) and not s.get("why"):
                rep.warn(f"{w.get('id')}: step '{s.get('id')}' has no 'why'")
        unknown_chapter(w)
        check_misconception(w)

    for e in (o for o in objs if o.get("kind") == "exam"):
        for part in e.get("parts", []) or []:
            for i in part.get("items", []) or []:
                if i not in by_id and not delta:
                    rep.err(f"{e.get('id')}: item {i} not found")

    # 4. coverage (full folder only)
    if not delta:
        workshop = defaultdict(int)
        for o in items:
            if "workshop" in (o.get("use") or []):
                workshop[o.get("chapter")] += 1
        gen_ch = {g.get("chapter") for g in gens}
        for s in slugs:
            if s not in gen_ch and workshop[s] == 0:
                rep.err(f"{s}: no workshop material (no generator, no item with use: workshop)")
            elif s not in gen_ch and workshop[s] < 10:
                rep.warn(f"{s}: only {workshop[s]} workshop items and no generator (aim for 10-15)")
        for f in sorted(fids):
            uses = [u for o in items if o.get("misconception") == f for u in (o.get("use") or [])]
            if "quiz" not in uses:
                rep.err(f"{f}: no quiz item targets it")
            if "workshop" not in uses and f not in {g.get("misconception") for g in gens}:
                rep.err(f"{f}: no workshop item or generator targets it")
            if f"Watch out ({f})" not in content:
                rep.warn(f"{f}: no '> Watch out ({f}):' box in 02")
        if len(queries) < 5:
            rep.err(f"04: {len(queries)} search reference queries (need 5-10)")
        if not any(w.get("priority") == "P1" for w in widgets):
            rep.warn("04: no P1 widget")

    # 5. leftovers and confidentiality hints
    for name in sorted(present):
        if not name.endswith(".md"):
            continue
        text = read(name)
        for m in LEFTOVER.finditer(text):
            rep.err(f"{name}: leftover '{m.group(0)}'")
        ph = sorted(set(PLACEHOLDER.findall(text)))
        if ph:
            msg = f"{name}: possible unfilled placeholders: {', '.join(ph[:5])}"
            rep.err(msg) if name == "00_BRIEF.md" else rep.warn(msg)
        ips = IPV4.findall(text)
        if ips:
            rep.warn(f"{name}: {len(ips)} IP-like strings (fine for course examples; check none are real infrastructure)")

    # report
    for w in rep.warnings:
        print("WARN ", w)
    for e in rep.errors:
        print("ERROR", e)
    print(f"\n{len(objs)} YAML objects, {len(slugs)} chapters, {len(fids)} misconceptions, "
          f"{len(items)} items, {len(gens)} generators, {len(widgets)} widgets, {len(queries)} search queries")
    if rep.errors:
        print(f"{len(rep.errors)} error(s): fix them, zip not written.")
        return 1
    if not no_zip:
        out = folder.parent / f"{folder.name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(folder.rglob("*")):
                if p.is_file() and not p.name.startswith("."):
                    z.write(p, Path(folder.name) / p.relative_to(folder))
        print(f"OK, zip written: {out}")
    else:
        print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

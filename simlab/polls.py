"""Poll table (docs/stats-groundwork.md §2.2, §5.1): Senate, generic-ballot and approval polls from the snapshots of
VoteHub (CC BY 4.0) and the Wikipedia race pages (CC BY-SA 4.0; the parsed table must carry the same licence).

    python -m simlab.polls                      # latest snapshot -> data/polls/<date>_<time>/
    python -m simlab.polls --snapshot DIR --out DIR
"""
from __future__ import annotations

import argparse
import calendar
import gzip
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

SNAPSHOTS = Path(__file__).parents[2] / "simlab-data" / "snapshots"
OUT = Path(__file__).parents[1] / "data" / "polls"
OVERVIEW_PAGE = "2026 United States Senate elections"
LICENCE = ("Polls from VoteHub (CC BY 4.0) and Wikipedia (CC BY-SA 4.0); this table is CC BY-SA 4.0 "
           "(docs/stats-groundwork.md, D8)")

STATE_CODES = dict(s.split(" ", 1)[::-1] for s in (
    "AL Alabama|AK Alaska|AZ Arizona|AR Arkansas|CA California|CO Colorado|CT Connecticut|DE Delaware|FL Florida|"
    "GA Georgia|HI Hawaii|ID Idaho|IL Illinois|IN Indiana|IA Iowa|KS Kansas|KY Kentucky|LA Louisiana|ME Maine|"
    "MD Maryland|MA Massachusetts|MI Michigan|MN Minnesota|MS Mississippi|MO Missouri|MT Montana|NE Nebraska|"
    "NV Nevada|NH New Hampshire|NJ New Jersey|NM New Mexico|NY New York|NC North Carolina|ND North Dakota|OH Ohio|"
    "OK Oklahoma|OR Oregon|PA Pennsylvania|RI Rhode Island|SC South Carolina|SD South Dakota|TN Tennessee|TX Texas|"
    "UT Utah|VT Vermont|VA Virginia|WA Washington|WV West Virginia|WI Wisconsin|WY Wyoming").split("|"))
STATE_NAMES = {code: name for name, code in STATE_CODES.items()}
PARTY = {"Republican": "R", "Democratic": "D", "DFL": "D", "Democratic–Farmer–Labor": "D", "Independent": "I"}
POP_RANK = {"lv": 0, "rv": 1, "v": 2, "a": 3}
POLLSTER_STOP = {"university", "college", "the", "poll", "polls", "polling", "research", "group", "insights", "inc",
                 "llc", "associates", "strategies", "reports", "and", "of", "center", "school", "law", "survey",
                 "institute", "company", "co", "partners", "analytics"}
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}
VERSION_COLUMNS = ["pollster", "tag", "start", "end", "n", "population", "left", "right", "other", "undecided"]
TEMPLATE_TEXT = {"nbsp": " ", "sdash": "–", "ndash": "–", "snd": "–", "mdash": "—"}
TEMPLATE_FIRST_ARG = {"small", "nowrap", "abbr"}
DASH = r"\s*[–—-]\s*"


def _templates(text: str) -> str:
    """Replace {{...}} (nested) with plain text: known spacing and dash templates, the first argument of formatting
    templates, nothing for the rest (notes, citations, party shading)."""
    out, i, start, depth = [], 0, 0, 0
    while i < len(text):
        if text.startswith("{{", i):
            if depth == 0:
                out.append(text[start:i])
                start = i
            depth += 1
            i += 2
        elif text.startswith("}}", i) and depth:
            depth -= 1
            i += 2
            if depth == 0:
                parts = text[start + 2:i - 2].split("|")
                name = parts[0].strip().lower()
                out.append(TEMPLATE_TEXT.get(name, parts[1] if name in TEMPLATE_FIRST_ARG and len(parts) > 1 else ""))
                start = i
        else:
            i += 1
    out.append(text[start:] if depth == 0 else "")
    return "".join(out)


def clean(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = _templates(text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)
    text = re.sub(r"<br\s*/?>|<wbr\s*/?>", " ", text)
    text = re.sub(r"</?[a-z]+[^>]*>", "", text)
    text = text.replace("'''", "").replace("''", "").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def _split(text: str, sep: str) -> list[str]:
    """Split on `sep` outside {{...}} and [[...]]."""
    parts, depth, i, start = [], 0, 0, 0
    while i < len(text):
        two = text[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            i += 2
        elif two in ("}}", "]]") and depth:
            depth -= 1
            i += 2
        elif depth == 0 and text.startswith(sep, i):
            parts.append(text[start:i])
            i += len(sep)
            start = i
        else:
            i += 1
    parts.append(text[start:])
    return parts


def _cell(raw: str) -> tuple[str, int, int]:
    """Cell text -> (clean content, rowspan, colspan). Attributes sit before the first bare pipe; a prefix that is only
    templates (party shading) counts as attributes too."""
    pieces = _split(raw, "|")
    attrs, content = ("", raw) if len(pieces) == 1 else (pieces[0], "|".join(pieces[1:]))
    if attrs and "=" not in attrs and _templates(attrs).strip():
        attrs, content = "", raw
    rs = re.search(r'rowspan\s*=\s*"?(\d+)', attrs)
    cs = re.search(r'colspan\s*=\s*"?(\d+)', attrs)
    return clean(content), int(rs.group(1)) if rs else 1, int(cs.group(1)) if cs else 1


def parse_table(table: str) -> tuple[list[str], list[list[str]]]:
    """Wikitext table -> (header names, data rows) with rowspan and colspan expanded."""
    raw_rows, cur = [], []
    for line in table.split("\n"):
        s = line.strip()
        if s.startswith("{|") or s.startswith("|+"):
            continue
        if s.startswith("|-") or s.startswith("|}"):
            if cur:
                raw_rows.append(cur)
            cur = []
        elif s.startswith("!"):
            cur += [("!", c) for c in _split(s[1:], "!!")]
        elif s.startswith("|"):
            cur += [("|", c) for c in _split(s[1:], "||")]
        elif cur and s:
            kind, c = cur[-1]
            cur[-1] = (kind, c + " " + s)
    if cur:
        raw_rows.append(cur)
    header, rows, pending = [], [], {}
    for raw in raw_rows:
        if all(kind == "!" for kind, _ in raw) and not header:
            header = [_cell(c)[0] for _, c in raw]
            continue
        cells, out, col = iter(raw), [], 0
        while True:
            if col in pending:
                value, left = pending.pop(col)
                out.append(value)
                if left > 1:
                    pending[col] = (value, left - 1)
                col += 1
                continue
            nxt = next(cells, None)
            if nxt is None:
                break
            text, rs, cs = _cell(nxt[1])
            for _ in range(cs):
                out.append(text)
                if rs > 1:
                    pending[col] = (text, rs - 1)
                col += 1
        rows.append(out)
    return header, rows


def sample(text: str) -> tuple[int | None, str | None]:
    m = re.search(r"([\d,]+)\s*\((LV|RV|A|V)\)", text)
    return (int(m.group(1).replace(",", "")), m.group(2).lower()) if m else (None, None)


def _date(text: str) -> date:
    return datetime.strptime(re.sub(r"\s+", " ", text.strip()), "%B %d, %Y").date()


def dates(text: str) -> tuple[date, date]:
    """Field dates as written on Wikipedia; a month alone ("July 2026") covers the whole month."""
    if m := re.fullmatch(r"([A-Za-z]+) (\d{4})", text.strip()):
        first = datetime.strptime(f"{m.group(1)} 1, {m.group(2)}", "%B %d, %Y").date()
        return first, first.replace(day=calendar.monthrange(first.year, first.month)[1])
    parts = re.split(DASH, text.strip())
    if len(parts) == 1:
        d = _date(parts[0])
        return d, d
    left, right = parts[0], parts[1]
    if not re.match(r"[A-Za-z]", right):
        right = left.split()[0] + " " + right
    end = _date(right)
    if re.search(r"\d{4}", left):
        return _date(left), end
    start = _date(f"{left}, {end.year}")
    return (start.replace(year=end.year - 1) if start > end else start), end


def pollster_tag(text: str) -> tuple[str, str]:
    m = re.match(r"^(.*?)\s*\((R|D)\)\s*$", text)
    return (m.group(1), m.group(2)) if m else (text, "")


def pct(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    return float(m.group(1)) if m else None


def surname(name: str) -> str:
    toks = [t for t in re.sub(r"[()\"']", " ", name).split() if t.lower() not in SUFFIXES]
    return toks[-1] if toks else ""


@dataclass(frozen=True)
class Race:
    """A 2026 Senate race: `right` is the Republican nominee, `left` the main challenger (Democrat, or the notable
    independent where there is one instead)."""
    state: str
    special: bool
    right: str
    left: str
    left_party: str
    title: str
    incumbent: str = ""
    status: str = ""

    @property
    def race_id(self) -> str:
        return self.state + ("-S" if self.special else "")


def _section(text: str, name: str, level: int, start: int = 0, end: int | None = None) -> tuple[int, int] | None:
    """Span of the first heading `name` at `level` (== is 2) inside text[start:end], up to the next heading of the same
    or a higher level."""
    end = len(text) if end is None else end
    heads = [(m.start(), len(m.group(1)), m.group(2).strip())
             for m in re.finditer(r"^(=+)\s*(.*?)\s*=+\s*$", text[start:end], re.M)]
    for i, (pos, lvl, title) in enumerate(heads):
        if lvl == level and title.lower().startswith(name.lower()):
            stop = next((p for p, l, _ in heads[i + 1:] if l <= level), end - start)
            return start + pos, start + stop
    return None


def _tables(text: str) -> list[str]:
    out, i = [], 0
    while (a := text.find("{|", i)) >= 0:
        depth, j = 0, a
        while j < len(text):
            if text.startswith("{|", j):
                depth, j = depth + 1, j + 2
            elif text.startswith("|}", j):
                depth, j = depth - 1, j + 2
                if depth == 0:
                    break
            else:
                j += 1
        out.append(text[a:j])
        i = j
    return out


def poll_tables(page: str, level: int = 2) -> list[tuple[list[str], list[list[str]]]]:
    """Poll tables of the "General election" > "Polling" section (headings at `level` and one below; 3 in a House
    page's district sections); aggregator tables are skipped."""
    ge = _section(page, "General election", level)
    span = _section(page, "Polling", level + 1, *ge) if ge else None
    if not span:
        return []
    parsed = [parse_table(t) for t in _tables(page[span[0]:span[1]])]
    return [(h, r) for h, r in parsed if any(x.startswith("Poll source") for x in h)]


def _has(header: list[str], name: str) -> int | None:
    return next((i for i, h in enumerate(header) if re.search(rf"\b{re.escape(name)}\b", h, re.I)), None)


def nominee_table(tables, right: str, left: str):
    """The table with a column for each nominee (by surname); the largest if several (a full-ballot table beats a
    head-to-head subset)."""
    hits = [t for t in tables if _has(t[0], right) is not None and _has(t[0], left) is not None]
    return max(hits, key=lambda t: len(t[1])) if hits else None


def wiki_polls(page: str, race: Race, level: int = 2) -> pd.DataFrame:
    """One row per poll version in the nominee table."""
    found = nominee_table(poll_tables(page, level), surname(race.right), surname(race.left))
    if not found:
        return pd.DataFrame(columns=VERSION_COLUMNS)
    header, rows = found
    col = {k: next(i for i, h in enumerate(header) if h.startswith(k)) for k in ("Poll source", "Date", "Sample")}
    li, ri = _has(header, surname(race.left)), _has(header, surname(race.right))
    und = next((i for i, h in enumerate(header) if h.lower().startswith("undecided")), None)
    rest = [i for i, h in enumerate(header) if i not in (li, ri, und, *col.values()) and not h.startswith("Margin")]
    out = []
    for row in rows:
        row = row + [""] * (len(header) - len(row))
        try:
            start, end = dates(row[col["Date"]])
        except ValueError:
            continue
        if pct(row[li]) is None or pct(row[ri]) is None:
            continue
        pollster, tag = pollster_tag(row[col["Poll source"]])
        n, population = sample(row[col["Sample"]])
        others = [p for p in (pct(row[i]) for i in rest) if p is not None]
        out.append({"pollster": pollster, "tag": tag, "start": start, "end": end, "n": n, "population": population,
                    "left": pct(row[li]), "right": pct(row[ri]), "other": sum(others) if others else np.nan,
                    "undecided": pct(row[und]) if und is not None else np.nan})
    return pd.DataFrame(out, columns=VERSION_COLUMNS)


def pollster_key(name: str) -> frozenset:
    toks = re.findall(r"[a-z0-9]+", re.sub(r"\(.*?\)", " ", name.lower()).replace("&", " "))
    return frozenset(t for t in toks if t not in POLLSTER_STOP) or frozenset(toks)


def same_pollster(a: str, b: str) -> bool:
    ka, kb = pollster_key(a), pollster_key(b)
    return bool(ka and kb) and (len(ka & kb) / len(ka | kb) >= 0.5 or ka <= kb or kb <= ka)


def two_party(left, right):
    return 100 * (left - right) / (left + right)


def _vh_date(text: str | None) -> date | None:
    return datetime.strptime(text[:10], "%Y-%m-%d").date() if text else None


def _vh_meta(e: dict) -> dict:
    return {"votehub_id": e["id"], "pollster": e["pollster"], "sponsors": ", ".join(e.get("sponsors") or []),
            "partisan": e.get("partisan") or "", "internal": bool(e.get("internal")),
            "population": e.get("population") or "v", "n": e.get("sample_size"), "start": _vh_date(e["start_date"]),
            "end": _vh_date(e["end_date"]), "created": _vh_date(e.get("created_at")), "url": e.get("url") or ""}


def _answer(answers: list[dict], name: str) -> float | None:
    hits = [a for a in answers if surname(a["choice"]).lower() == surname(name).lower()]
    exact = [a for a in hits if a["choice"].strip().lower() == name.strip().lower()]
    pick = exact or hits
    return max(a["pct"] for a in pick) if pick else None


def votehub_polls(entries: list[dict], race_list: list[Race]) -> pd.DataFrame:
    """VoteHub Senate general-election polls of each race's nominee pair (primaries and other matchups dropped)."""
    out = []
    for race in race_list:
        subject = f"2026 {STATE_NAMES[race.state]}"
        for e in entries:
            if e.get("poll_type") != "us-senator" or e.get("subject") != subject:
                continue
            left, right = _answer(e["answers"], race.left), _answer(e["answers"], race.right)
            if left is None or right is None or (left == right == 50 and len(e["answers"]) == 2):
                continue  # an exact 50-50 two-way is a placeholder in VoteHub's data, not a result
            rest = sum(a["pct"] for a in e["answers"]) - left - right
            out.append({"race_id": race.race_id, **_vh_meta(e), "left": left, "right": right,
                        "other": rest if rest > 0 else np.nan, "undecided": np.nan})
    return pd.DataFrame(out)


def _best_population(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Group rows that are the same poll (same race, matching pollster name, end dates a day apart at most) and keep
    the best population in each: likely voters, then registered voters, then unspecified, then adults."""
    df = df.sort_values(keys + ["end"]).reset_index(drop=True)
    poll, last = np.zeros(len(df), dtype=int), None
    for i, r in enumerate(df.itertuples()):
        same = last is not None and all(getattr(r, k) == getattr(last, k) for k in keys if k != "pollster") and \
            same_pollster(r.pollster, last.pollster) and abs((r.end - last.end).days) <= 1
        poll[i] = poll[i - 1] + (0 if same else 1) if i else 0
        last = r
    df["poll"] = poll
    rank = df.population.map(POP_RANK).fillna(4)
    return df[rank == rank.groupby(df.poll).transform("min")].drop(columns="poll")


def merge(wiki: pd.DataFrame, vh: pd.DataFrame) -> pd.DataFrame:
    """One row per poll: Wikipedia versions averaged within a population (D7); VoteHub supplies sponsor, partisan and
    internal flags when it has the poll, and fills in polls Wikipedia lacks; the best population is kept."""
    keys = ["race_id", "pollster", "start", "end", "population"]
    groups = (wiki.assign(population=wiki.population.fillna("v"))
              .groupby(keys, as_index=False, dropna=False)
              .agg(left=("left", "mean"), right=("right", "mean"), other=("other", "mean"),
                   undecided=("undecided", "mean"), n=("n", "max"), tag=("tag", "first"), versions=("left", "size")))
    used, rows = set(), []
    for g in groups.itertuples(index=False):
        cand = vh[(vh.race_id == g.race_id) & (vh.population == g.population)] if len(vh) else vh
        best = None
        for c in cand.itertuples(index=False):
            if c.votehub_id in used or not same_pollster(g.pollster, c.pollster):
                continue
            if abs((c.end - g.end).days) > 1 or abs((c.start - g.start).days) > 2:
                continue
            if g.n and c.n and abs(g.n - c.n) > 0.05 * max(g.n, c.n):
                continue
            if best is None or abs((c.end - g.end).days) < abs((best.end - g.end).days):
                best = c
        row = {**g._asdict(), "source": "wikipedia", "votehub_id": "", "sponsors": "", "partisan": "",
               "internal": False, "url": "", "vh_margin": np.nan}
        if best is not None:
            used.add(best.votehub_id)
            row.update(source="both", votehub_id=best.votehub_id, sponsors=best.sponsors, partisan=best.partisan,
                       internal=best.internal, url=best.url, vh_margin=two_party(best.left, best.right))
        rows.append(row)
    for c in (vh[~vh.votehub_id.isin(used)] if len(vh) else vh).itertuples(index=False):
        rows.append({"race_id": c.race_id, "pollster": c.pollster, "start": c.start, "end": c.end,
                     "population": c.population, "left": c.left, "right": c.right, "other": c.other,
                     "undecided": c.undecided, "n": c.n, "tag": "", "versions": 1, "source": "votehub",
                     "votehub_id": c.votehub_id, "sponsors": c.sponsors, "partisan": c.partisan,
                     "internal": c.internal, "url": c.url, "vh_margin": np.nan})
    if not rows:
        return pd.DataFrame(columns=keys + ["left", "right", "margin", "source"])
    out = pd.DataFrame(rows)
    out["margin"] = two_party(out.left, out.right)
    out["decided"] = out.left + out.right
    out["disagree"] = (out.vh_margin - out.margin).abs() > 1
    out["mid"] = [s + (e - s) / 2 for s, e in zip(out.start, out.end)]
    return _best_population(out, ["race_id", "pollster"]).sort_values(["race_id", "end"], ascending=[True, False]) \
        .reset_index(drop=True)


def _national(entries: list[dict], poll_type: str, subject: str, first: str, second: str) -> pd.DataFrame:
    rows = []
    for e in entries:
        if e.get("poll_type") != poll_type or e.get("subject") != subject:
            continue
        a = {x["choice"]: x["pct"] for x in e["answers"]}
        if first in a and second in a:
            rows.append({**_vh_meta(e), first.lower(): a[first], second.lower(): a[second]})
    df = pd.DataFrame(rows)
    return _best_population(df, ["pollster"]).reset_index(drop=True) if len(df) else df


def generic_ballot(entries: list[dict], cycle: str = "2026") -> pd.DataFrame:
    df = _national(entries, "generic-ballot", cycle, "Dem", "Rep")
    return df.assign(margin=two_party(df.dem, df.rep)) if len(df) else df


def approval(entries: list[dict], president: str = "Donald Trump") -> pd.DataFrame:
    df = _national(entries, "approval", president, "Approve", "Disapprove")
    return df.assign(net=df.approve - df.disapprove) if len(df) else df


def slug(title: str) -> str:
    """File name the snapshotter uses for a page (simlab.snap.slug)."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _load(path: Path):
    return json.loads(gzip.decompress(path.read_bytes()))


def build(snapshot: Path) -> dict:
    """All poll tables from one snapshot folder (snapshots/YYYY-MM-DD/HHMM)."""
    snapshot = Path(snapshot)
    page = lambda p: p["revisions"][0]["slots"]["main"]["content"]
    race_list = races(page(_load(snapshot / "wikipedia" / f"{slug(OVERVIEW_PAGE)}.gz")))
    frames, revisions, missing = [], {}, []
    for race in race_list:
        path = snapshot / "wikipedia" / f"{slug(race.title)}.gz"
        if not path.exists():
            missing.append(race.race_id)
            continue
        p = _load(path)
        revisions[race.race_id] = p["revisions"][0]["revid"]
        frames.append(wiki_polls(page(p), race).assign(race_id=race.race_id))
    entries = _load(snapshot / "polls" / "votehub.gz")
    wiki = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=VERSION_COLUMNS + ["race_id"])
    return {"snapshot": f"{snapshot.parent.name} {snapshot.name[:2]}:{snapshot.name[2:]}", "race_list": race_list,
            "entries": entries, "races": pd.DataFrame([{**asdict(r), "race_id": r.race_id} for r in race_list]),
            "senate": merge(wiki, votehub_polls(entries, race_list)), "generic_ballot": generic_ballot(entries),
            "approval": approval(entries), "revisions": revisions, "missing_pages": missing}


def latest_snapshot(root: Path = SNAPSHOTS) -> Path:
    return sorted(p for p in root.glob("*/*") if p.is_dir())[-1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    snap = args.snapshot or latest_snapshot()
    t = build(snap)
    out = args.out or OUT / f"{snap.parent.name}_{snap.name}"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("races", "senate", "generic_ballot", "approval"):
        t[name].to_csv(out / f"{name}.csv", index=False)
    s = t["senate"]
    meta = {"snapshot": t["snapshot"], "licence": LICENCE, "revisions": t["revisions"],
            "missing_pages": t["missing_pages"], "polls": int(len(s)),
            "by_source": s.source.value_counts().to_dict(), "disagreements": int(s.disagree.sum())}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"snapshot {t['snapshot']}: {len(t['races'])} races, {len(s)} Senate polls {meta['by_source']}, "
          f"{meta['disagreements']} source disagreements over 1 point, generic ballot {len(t['generic_ballot'])}, "
          f"approval {len(t['approval'])}; missing pages {t['missing_pages']} -> {out}")


def _candidates(row: str) -> list[tuple[str, str, bool]]:
    """(name, party code, has a Wikipedia article) for each bullet in a race-summary row."""
    out = []
    for bullet in re.finditer(r"\*([^\n]*)", row):
        s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", bullet.group(1), flags=re.S)
        s = re.sub(r"\{\{Party stripe\|[^{}]*\}\}", "", s).strip()
        m = re.match(r"(.*)\(([^()]*)\)\s*$", s)
        if m:
            out.append((clean(m.group(1)), PARTY.get(m.group(2).strip(), "O"), "[[" in m.group(1)))
    return out


def races(overview: str) -> list[Race]:
    """The 2026 Senate races from the overview page's race-summary tables."""
    out = []
    for name in ("Special elections during the preceding Congress", "Elections leading to the next Congress"):
        span = _section(overview, name, 3)
        if not span:
            continue
        for row in re.split(r"\n\|-", overview[span[0]:span[1]]):
            m = re.search(r"^!\s*\[\[(2026 United States Senate (special )?election in ([^|\]]+))\|", row, re.M)
            if not m:
                continue
            cands = _candidates(row)
            reps = sorted((c for c in cands if c[1] == "R"), key=lambda c: not c[2])
            challengers = [c for c in cands if c[1] in ("D", "I")]
            if not reps or not challengers:
                continue
            left = max(challengers, key=lambda c: (c[2], c[1] == "D"))
            inc = re.search(r"\{\{Party shading/[^}]*\}\}\s*\|\s*(Republican|Democratic|Independent|DFL|"
                            r"Democratic–Farmer–Labor)\s*$", row, re.M)
            status = [s for s in re.findall(r"data-sort-value=-?\d+\s*\|\s*([^\n]+)", row) if re.match(r"[A-Z]", s)]
            out.append(Race(STATE_CODES[m.group(3).strip()], bool(m.group(2)), reps[0][0], left[0], left[1], m.group(1),
                            PARTY.get(inc.group(1), "") if inc else "", clean(status[-1].split("<br")[0]) if status else ""))
    return out


if __name__ == "__main__":
    main()

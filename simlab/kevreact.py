"""Kev reaction fine-tune (react-v1): how a person's party and Senate support change after news, trained on real
measured shifts and design rules, never on GLM answers (Matteo's rule), so Kev can be an independent second opinion.

Training records (personas = real CES 2024 respondents from every state, the 28 party-ID x race x degree strata sampled
evenly, never the test archetypes):
- events2.json: 11 events with a clear shift (|z| >= 1, raw and detrended agree in sign, no confounders) and 15 with
  none (|z| < 0.5); the rest are noise or unattributable. Party-support and Senate-support questions, same target.
- 60 politically irrelevant news items (new; the null test's stay out): no change on every question.
- 20 mirror templates (new; the mirror test's stay out), asked with the actor's party swapped: minimal pairs whose
  direction follows the event (a scandal hurts the actor's party, good news helps it).
Targets (assumption register): 4% of any group move at random, 2% "slightly" each way. On top, a share
m = min(0.04 * s * g, 0.5) moves toward the side the event helps, 80% slightly and 20% strongly. s = the shift in
points of people: approval change, or half the D-R margin change (a 1% switch moves the margin 2 points), mean of raw
and detrended; 2 for a mirror template. g = responsiveness by party ID, a Field Guide prior (firm partisans barely
switch): strong 0.2, not very strong 0.6, lean 1.0, independent 1.6, normalised to a weighted mean of 1 over the test
archetypes. Every score question also appears reversed, as the test bench asks it.

Development = the test bench itself: the null, mirror and events tests' exact states and questions for the 28
archetypes, so a run's rows.json answers them offline (`score`). Its targets only feed Kev's own report (null test:
no change; events: the same mapping from the measured shift; mirror: no-change placeholder).

    python -m simlab.kevreact                 # data/kev/react-v1/
    python -m simlab.kevreact score react-v1  # null, mirror and events tests from the run, vs GLM and Jev
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
from scipy.special import softmax
from scipy.stats import pearsonr, spearmanr

from . import probes, tests
from .askers import order_avg
from .ces import DATA, PID7, STATE_NAMES, _fields, load
from .core import RUNS as BENCH
from .personas import render

HERE = Path(__file__).parent
OUT = DATA / "kev" / "react-v1"
KIT_RUNS = HERE.parent / "kev-finetune" / "runs"
EVENTS2 = json.loads((HERE / "events2.json").read_text(encoding="utf-8"))
ARCH = json.loads((HERE / "archetypes.json").read_text(encoding="utf-8"))
G_RAW = {1: 0.2, 2: 0.6, 3: 1.0, 4: 1.6, 5: 1.0, 6: 0.6, 7: 0.2, 8: 1.6}   # 7-point party ID; 8 = not sure
K, BACKGROUND, STRONG, CAP, MIRROR_S = 0.04, 0.04, 0.2, 0.5, 2.0
QUESTIONS = {"event": tests.EVENT_Q, "support": probes.REACTION_QUESTIONS["support"],
             "turnout": probes.REACTION_QUESTIONS["turnout"]}

TRAIN_NULL_NEWS = [
    "A minor-league baseball team unveiled new uniforms inspired by the city's old streetcars.",
    "Researchers found that honeybees can learn to recognize simple shapes after a few hours of training.",
    "A regional airline added a nonstop route between two mid-sized cities starting in the spring.",
    "The county library's summer reading challenge drew a record 12,000 young readers.",
    "A local hospital welcomed quadruplets, the first born there in 30 years.",
    "A video game studio released a remastered version of a classic 1990s racing game.",
    "An amateur fossil hunter found a well-preserved mammoth tooth in a riverbank.",
    "A city aquarium opened a new exhibit featuring glowing jellyfish from the deep Pacific.",
    "The heaviest watermelon at this year's county fair weighed in at 350 pounds.",
    "A high school robotics team qualified for the world championship for the first time.",
    "Scientists identified a new species of frog in a remote cloud forest in Peru.",
    "A popular sitcom from the 2000s is getting a reunion special next year.",
    "An ice cream shop set a record by stacking 125 scoops on a single cone.",
    "A professional soccer club signed a young midfielder from Brazil to a four-year contract.",
    "The annual hot air balloon festival launched more than 500 balloons at sunrise on Saturday.",
    "A new study suggests that cats recognize their owners' voices but often choose to ignore them.",
    "A community garden donated 3,000 pounds of fresh vegetables to local food pantries this summer.",
    "The city zoo's elderly tortoise celebrated its 100th birthday with a strawberry cake.",
    "A children's author released the final book in a best-selling fantasy series.",
    "A kite shaped like a blue whale flew over the beach during a weekend festival.",
    "A tech company recalled a line of wireless earbuds because the charging case can overheat.",
    "A minor earthquake gently shook a rural area overnight; no damage or injuries were reported.",
    "Birdwatchers reported an unusually large migration of sandhill cranes along the river this week.",
    "A famous rock band announced that its drummer is retiring after 40 years on tour.",
    "A local bakery won a national award for its sourdough bread.",
    "A university choir won first prize at an international competition in Vienna.",
    "A cyclist rode across the country in 16 days, beating the time of their previous attempt.",
    "A new roller coaster, the tallest in the region, will open at an amusement park next summer.",
    "Hikers photographed a rare white moose in a northern forest.",
    "A camera maker released a compact model aimed at wildlife photographers.",
    "A golf tournament ended in a three-way playoff decided on the fifth extra hole.",
    "A 94-year-old woman completed her college degree, graduating alongside her great-grandson.",
    "Volunteer divers located the wreck of an 1880s steamship at the bottom of Lake Superior.",
    "A movie about a talking dog topped the weekend box office with $48 million in ticket sales.",
    "A horse named Midnight Clover won the state's biggest harness race by half a length.",
    "Food scientists developed a strawberry variety that stays fresh for two weeks longer.",
    "The regional orchestra announced a free outdoor concert series in city parks.",
    "A college basketball game was won by a half-court shot at the buzzer in double overtime.",
    "A new trail connecting two state parks opened to hikers and mountain bikers.",
    "A museum received a donation of 200 antique toys from a private collector.",
    "Firefighters rescued a kitten that had climbed 40 feet up a telephone pole.",
    "A beagle named Biscuit won best in show at a national dog show.",
    "Leaf-peeping guides expect peak fall colors in the northern hills around mid-October.",
    "A pro football team's star quarterback will miss two games with a sprained ankle.",
    "A pizza chain introduced a limited-edition pizza topped with pickles.",
    "A teenage skateboarder won a gold medal at an international competition in Rome.",
    "A local couple celebrated their 75th wedding anniversary with a dance at the community center.",
    "A charter boat captain photographed a rare pink dolphin in the Gulf.",
    "A board game cafe opened downtown with more than 800 games on its shelves.",
    "An annual chili cook-off raised money for the county animal shelter.",
    "The city's minor-league hockey team retired the jersey of its all-time leading scorer.",
    "A photograph of a lightning storm over a canyon won an international photo prize.",
    "A popular streaming drama was renewed for a fifth and final season.",
    "A science museum unveiled a full-size replica of a Tyrannosaurus rex skeleton.",
    "A carpenter built a working violin out of wood reclaimed from an old barn.",
    "A 12-year-old won the county fair's pie-baking contest with a peach pie.",
    "A new ferry began service across the bay, cutting the trip to 25 minutes.",
    "A 71-year-old local runner qualified for the Boston Marathon.",
    "A wildlife camera captured a family of bobcats playing in a suburban backyard.",
    "A startup released an app that identifies bird songs from a phone recording.",
]
TRAIN_MIRROR = [  # (template, +1 if the news helps the actor's party, -1 if it hurts)
    ("Records show the {P} Senate candidate claimed a military medal they never received.", -1),
    ("A former aide accused the {P} Senate candidate of routinely berating and threatening staff.", -1),
    ("The {P} Senate candidate's family company was fined for dumping chemicals into a local river.", -1),
    ("The {P} Senate candidate was arrested for drunk driving over the weekend.", -1),
    ("The {P} Senate candidate admitted that large parts of a major policy speech were copied from a think tank report.", -1),
    ("Reporters found that the {P} Senate candidate has lived out of state for most of the past decade.", -1),
    ("The {P} Senate candidate joked about a deadly flood at a fundraiser, and the video spread quickly.", -1),
    ("Former tenants sued the {P} Senate candidate over unsafe conditions in apartments the candidate owns.", -1),
    ("The {P} Senate candidate's charity was found to have spent most of its donations on salaries and travel.", -1),
    ("In a leaked recording, the {P} Senate candidate called the state's teachers lazy and overpaid.", -1),
    ("The {P} Senate candidate helped pull a family out of a burning car on the interstate.", 1),
    ("The state farm bureau endorsed the {P} Senate candidate, its first Senate endorsement in 20 years.", 1),
    ("The {P} Senate candidate pledged to give their Senate salary to veterans' charities if elected.", 1),
    ("The {P} Senate candidate brokered a deal that kept a major auto plant open, saving 3,000 local jobs.", 1),
    ("An independent fact-checker rated the {P} Senate candidate the most truthful candidate in the race.", 1),
    ("The {P} Senate candidate released 20 years of tax returns showing large charitable giving.", 1),
    ("The {P} Senate candidate unveiled a rural hospital plan praised by mayors from both parties.", 1),
    ("A heartfelt ad about the {P} Senate candidate's late mother went viral and drew wide praise.", 1),
    ("The state's largest veterans' organization endorsed the {P} Senate candidate.", 1),
    ("The {P} Senate candidate spent a week rebuilding homes after a tornado, without press or cameras.", 1),
]


def people_points(ev: dict) -> float:
    """Shift toward D in points of people: approve-% change, or half the D-R margin change."""
    raw, det = ev.get("shift_toward_D"), ev.get("shift_detrended")
    s = (raw + det) / 2 if det is not None and raw is not None and raw * det > 0 else raw
    return s / 2 if "margin" in ev["measure"] or ev["measure"].startswith("generic") else s


def select_events() -> tuple[list[dict], list[dict]]:
    measured = [e for e in EVENTS2 if e.get("z") is not None]
    directional = [e for e in measured if abs(e["z"]) >= 1 and e["shift_detrended"] is not None
                   and e["shift_toward_D"] * e["shift_detrended"] > 0 and not e["confounded_with"]]
    return directional, [e for e in measured if abs(e["z"]) < 0.5]


def g_scale() -> float:
    """Weighted mean of G_RAW over the test archetypes (national adult shares), so normalised g averages 1."""
    code = {v: k for k, v in PID7.items() if k != 8}
    return sum(a["weight"] * G_RAW[code[a["id"].split(" / ")[0]]] for a in ARCH) / sum(a["weight"] for a in ARCH)


def reaction(sign: int, s: float, g: float) -> list[float]:
    """Probabilities of the 5 levels, low to high (strongly R ... strongly D; much less ... much more likely)."""
    p = [0.0, BACKGROUND / 2, 1 - BACKGROUND, BACKGROUND / 2, 0.0]
    m = min(K * abs(s) * g, CAP) if sign else 0.0
    up, strong = (3, 4) if sign > 0 else (1, 0)
    p[2] -= m
    p[up] += (1 - STRONG) * m
    p[strong] += STRONG * m
    return p


def ask_both(qs: dict, name: str, probs: list[float]):
    """The question as written and reversed, each with its soft target (keys are level indices as shown)."""
    q = QUESTIONS[name]
    for i, (criteria, p) in enumerate(((q["criteria"], probs), (q["criteria"][::-1], probs[::-1]))):
        target = {str(j): round(v, 4) for j, v in enumerate(p)}
        qs[f"{name}_{i}"] = {**q, "criteria": list(criteria), "label": int(np.argmax(p)), "target": target}


def persona_pool() -> tuple[list[dict], dict]:
    """CES respondents by stratum (party ID x white/non-white x degree), with texts as the test bench renders them."""
    df = load(next(DATA.glob("CCES24_*.csv")))
    df = df[df.pid7.isin(list(G_RAW)) & df.inputstate.isin(list(STATE_NAMES))]
    test = {a["text"] for a in ARCH} | {a["text_events"] for a in ARCH}
    pool, strata = [], {}
    for r in df.itertuples():
        f = {**_fields(r), "state": STATE_NAMES[r.inputstate]}
        text, text_events = render(f), render(f, drop=("vote_2020",))
        if text in test or text_events in test:
            continue
        pid = int(r.pid7)
        pool.append({"text": text, "text_events": text_events, "pid": pid, "weight": r.commonweight})
        strata.setdefault((4 if pid == 8 else pid, r.race5 == "White", r.degree), []).append(len(pool) - 1)
    return pool, strata


def sample(pool: list[dict], strata: dict, n: int, rng: random.Random) -> list[dict]:
    keys, out = sorted(strata), set()
    while len(out) < n:
        idx = strata[rng.choice(keys)]
        out.add(rng.choices(idx, weights=[pool[i]["weight"] for i in idx])[0])
    return [pool[i] for i in sorted(out)]


def build(per_event: int = 40, per_null: int = 8, per_mirror: int = 10, calibration: float = 0.15,
          seed: int = 0) -> None:
    rng = random.Random(seed)
    pool, strata = persona_pool()
    z = g_scale()
    g = lambda pid: G_RAW[pid] / z
    directional, flat = select_events()
    train = []
    for ev in directional + flat:
        s = people_points(ev) if ev in directional else 0.0
        news = f"({ev['date']}) {ev['description']}"
        for p in sample(pool, strata, per_event, rng):
            qs = {}
            for name in ("event", "support"):
                ask_both(qs, name, reaction(int(np.sign(s)), s, g(p["pid"])))
            train.append({"state": probes.reaction_state(p["text_events"], news), "questions": qs,
                          "_meta": {"kind": "events2", "id": ev["id"], "s": round(s, 3)}})
    for news in TRAIN_NULL_NEWS:
        for p in sample(pool, strata, per_null, rng):
            qs = {}
            for name in ("event", "support", "turnout"):
                ask_both(qs, name, reaction(0, 0, 1))
            train.append({"state": probes.reaction_state(p["text"], news), "questions": qs,
                          "_meta": {"kind": "null"}})
    for i, (template, valence) in enumerate(TRAIN_MIRROR):
        for p in sample(pool, strata, per_mirror, rng):
            for party, side in (("Democratic", 1), ("Republican", -1)):
                qs = {}
                ask_both(qs, "support", reaction(valence * side, MIRROR_S, g(p["pid"])))
                train.append({"state": probes.reaction_state(p["text"], template.format(P=party)), "questions": qs,
                              "_meta": {"kind": "mirror", "template": i, "party": party}})
    rng.shuffle(train)
    k = round(calibration * len(train))
    parts = {"calibration": train[:k], "train": train[k:], "development": development(g)}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, recs in parts.items():
        (OUT / f"{name}.jsonl").write_text("\n".join(json.dumps({"state": r["state"], "questions": r["questions"]})
                                                     for r in recs) + "\n", encoding="utf-8")
    kinds = lambda recs: {k: sum(1 for r in recs if r["_meta"]["kind"] == k) for k in ("events2", "null", "mirror")}
    manifest = {"seed": seed, "k_per_point": K, "background": BACKGROUND, "strong_share": STRONG, "cap": CAP,
                "mirror_points": MIRROR_S, "g_raw": G_RAW, "g_scale": round(z, 4),
                "directional": {e["id"]: round(people_points(e), 3) for e in directional},
                "no_change": [e["id"] for e in flat],
                "sources": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                            for f in (HERE / "events2.json", HERE / "archetypes.json", HERE / "events.json")},
                "records": {n: len(r) for n, r in parts.items()},
                "train_kinds": kinds(parts["train"]), "calibration_kinds": kinds(parts["calibration"]),
                "questions": {n: sum(len(r["questions"]) for r in recs) for n, recs in parts.items()}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("g_scale", "directional", "records", "train_kinds", "questions")},
                     indent=1))


def development(g) -> list[dict]:
    """The test bench's exact items (tests.null_test, mirror_test, events_test on the 28 archetypes)."""
    code = {v: k for k, v in PID7.items() if k != 8}
    null, out = reaction(0, 0, 1), []
    for a in ARCH:
        for news in probes.NULL_NEWS:
            qs = {}
            for name in ("support", "turnout"):
                ask_both(qs, name, null)
            out.append({"state": probes.reaction_state(a["text"], news), "questions": qs, "_meta": {"kind": "null"}})
        for i in range(len(probes.MIRROR_TEMPLATES)):
            for news in probes.mirror_pair(i):
                qs = {}
                ask_both(qs, "support", null)
                out.append({"state": probes.reaction_state(a["text"], news), "questions": qs,
                            "_meta": {"kind": "mirror"}})
        for ev in tests.EVENTS:
            s = people_points(ev)
            qs = {}
            ask_both(qs, "event", reaction(int(np.sign(s)), s, g(code[a["id"].split(" / ")[0]])))
            out.append({"state": probes.reaction_state(a["text_events"], f"({ev['date']}) {ev['description']}"),
                        "questions": qs, "_meta": {"kind": "events"}})
    return out


class Lookup:
    """A fine-tuned run's answers on the development file as an asker, so the test bench runs unchanged."""

    def __init__(self, run: str, temperature: float = 1.0):
        self.name = f"kev-{run}"
        dev = [json.loads(line) for line in (OUT / "development.jsonl").read_text(encoding="utf-8").splitlines()
               if line.strip()]
        self.p = {}
        for r in json.loads((KIT_RUNS / run / "development" / "rows.json").read_text(encoding="utf-8")):
            rec = dev[int(r["id"].split("/")[1])]
            q = rec["questions"][r["question"]]
            probs = softmax(np.array(r["logits"]) / temperature)
            self.p[(rec["state"], q["instructions"], json.dumps(q["criteria"]))] = dict(zip(r["keys"], map(float, probs)))

    def ask(self, state: str, question: dict, tag: str = "") -> dict:
        return order_avg(lambda q: self.p[(state, q["instructions"], json.dumps(list(q["criteria"])))], question, 2)


def size_tracking(model: str) -> dict:
    rows = [json.loads(line) for line in (BENCH / f"events__{model}.jsonl").read_text().splitlines() if line.strip()]
    x = np.array([r["pred"]["all"] for r in rows])
    y = np.array([r["measured"] for r in rows], float)
    w = np.array([r["weight"] for r in rows])
    k = float(np.sum(w * x * y) / np.sum(w * x * x))
    return {"ids": [r["id"] for r in rows], "x": x, "y": y, "w": w, "k": k, "err": k * x - y,
            "size_spearman": float(spearmanr(np.abs(x), np.abs(y))[0]),
            "rmse_after_scaling": float(np.sqrt(np.average((k * x - y) ** 2, weights=w)))}


def score(run: str, temperature: float = 1.0) -> dict:
    asker = Lookup(run, temperature)
    texts = [a["text"] for a in ARCH]
    res = {"null": tests.null_test(asker, texts), "mirror": tests.mirror_test(asker, texts),
           "events": tests.events_test(asker, [dict(a, text=a["text_events"]) for a in ARCH])}
    ref = {m: size_tracking(m) for m in ("glm", "jev", asker.name)}
    kev, glm = ref[asker.name], ref["glm"]
    assert kev["ids"] == glm["ids"]
    both = (kev["k"] * kev["x"] + glm["k"] * glm["x"]) / 2
    res["second_opinion"] = {
        **{f"size_spearman_{m}": round(v["size_spearman"], 3) for m, v in ref.items()},
        **{f"rmse_after_scaling_{m}": round(v["rmse_after_scaling"], 3) for m, v in ref.items()},
        "error_corr_with_glm": round(float(pearsonr(kev["err"], glm["err"])[0]), 3),
        "rmse_kev_glm_average": round(float(np.sqrt(np.average((both - kev["y"]) ** 2, weights=kev["w"]))), 3)}
    (KIT_RUNS / run / f"react_scores_T{temperature:g}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for name, r in res.items():
        print(name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k not in ("test", "model")})
    return res


if __name__ == "__main__":
    score(sys.argv[2]) if sys.argv[1:2] == ["score"] else build()

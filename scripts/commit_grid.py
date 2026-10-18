"""Lager et animert commit-kart (lys og mørk SVG).

Henter det ekte commit-kartet fra GitHub og fyller i tillegg minst
EXTRA tomme ruter med grønt i ulike nyanser, rent for utseendets skyld.

Bruk:  python scripts/commit_grid.py <brukernavn> <ut-mappe>
Krever miljøvariabelen GITHUB_TOKEN. Uten token (eller med --demo)
brukes tilfeldige testdata.
"""
import json
import os
import random
import sys
import urllib.request

EXTRA = 160            # minst 150 ekstra grønne ruter
CELL, GAP, PAD = 11, 3, 4
CYCLE = 10             # sekunder per runde
PALETTES = {
    "light": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    "dark":  ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
}
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch(user, token):
    query = ('{user(login:"%s"){contributionsCollection{contributionCalendar'
             '{weeks{contributionDays{weekday contributionLevel}}}}}}' % user)
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "commit-grid"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[(d["weekday"], LEVELS[d["contributionLevel"]]) for d in w["contributionDays"]]
            for w in weeks]


def demo():
    rnd = random.Random(1)
    weeks = [[(d, rnd.choice([0, 0, 0, 0, 1, 2])) for d in range(7)] for _ in range(52)]
    weeks.append([(d, 0) for d in range(3)])  # inneværende uke er ikke ferdig
    return weeks


def add_green(weeks, user):
    """Fyll minst EXTRA ruter ekstra, flest i lyse nyanser."""
    rnd = random.Random(user)
    cells = [(w, i) for w, week in enumerate(weeks) for i in range(len(week))]
    empty = [c for c in cells if weeks[c[0]][c[1]][1] == 0]
    rnd.shuffle(empty)
    picks = empty[:EXTRA]
    if len(picks) < EXTRA:  # for få tomme ruter: løft svake ruter i stedet
        weak = [c for c in cells if weeks[c[0]][c[1]][1] in (1, 2)]
        rnd.shuffle(weak)
        picks += weak[:EXTRA - len(picks)]
    for w, i in picks:
        day, level = weeks[w][i]
        bump = rnd.choices([1, 2, 3, 4], weights=[45, 30, 17, 8])[0]
        weeks[w][i] = (day, min(4, max(level + 1, bump)))
    return len(picks)


def render(weeks, colors):
    width = PAD * 2 + len(weeks) * (CELL + GAP) - GAP
    height = PAD * 2 + 7 * (CELL + GAP) - GAP
    css = [
        "rect{shape-rendering:geometricPrecision}",
        f"rect.c{{transform-box:fill-box;transform-origin:center;"
        f"animation:pop {CYCLE}s ease-in-out infinite both}}",
    ]
    for lvl in range(1, 5):
        css.append(f".l{lvl}{{--c:{colors[lvl]}}}")
    css.append(
        "@keyframes pop{"
        f"0%{{fill:{colors[0]};transform:scale(.3)}}"
        "6%{fill:var(--c);transform:scale(1.25)}"
        "10%{fill:var(--c);transform:scale(1)}"
        "80%{fill:var(--c);transform:scale(1)}"
        f"92%,100%{{fill:{colors[0]};transform:scale(.3)}}}}"
    )
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}"><style>{"".join(css)}</style>']
    for w, week in enumerate(weeks):
        for day, lvl in week:
            x = PAD + w * (CELL + GAP)
            y = PAD + day * (CELL + GAP)
            if lvl == 0:
                out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                           f'rx="2" fill="{colors[0]}"/>')
            else:
                delay = w * 0.07 + day * 0.03
                out.append(f'<rect class="c l{lvl}" x="{x}" y="{y}" width="{CELL}" '
                           f'height="{CELL}" rx="2" fill="{colors[lvl]}" '
                           f'style="animation-delay:{delay:.2f}s"/>')
    out.append("</svg>")
    return "".join(out)


def main():
    user, outdir = sys.argv[1], sys.argv[2]
    token = os.environ.get("GITHUB_TOKEN")
    weeks = demo() if "--demo" in sys.argv or not token else fetch(user, token)
    added = add_green(weeks, user)
    os.makedirs(outdir, exist_ok=True)
    for name, colors in PALETTES.items():
        suffix = "" if name == "light" else "-dark"
        with open(os.path.join(outdir, f"commit-grid{suffix}.svg"), "w") as f:
            f.write(render(weeks, colors))
    print(f"Ferdig: {added} ekstra grønne ruter")


if __name__ == "__main__":
    main()

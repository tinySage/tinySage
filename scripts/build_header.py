"""Draws the profile header in two readouts of the same signal.

    header-light.svg  printed ECG strip (GitHub light theme)
    header-dark.svg   bedside monitor   (GitHub dark theme)

The lead II trace runs a few beats, then the last beat lifts into a
handwritten "Muktanan" drawn as one continuous pen line.

All text is converted to outlines, because an SVG shown as an <img>
cannot load fonts. Run:  python3 scripts/build_header.py
"""

import math
import pathlib
import xml.etree.ElementTree as ET

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
OUT = ROOT.parent / "assets"

NAME = "Muktanan"
PATIENT = "MOHAPATRA, MUKTANAN"
HANDLE = "tinySage"
WARD = "CSE, ITER (SOA), Bhubaneswar"
SINCE = "Oct 2026"
FINDING = "Sinus rhythm"
NOTE = "Unconfirmed. Awaiting review by Maranello."
RATE = 72  # bpm; the drawn beats are spaced to match
MASCOT_ROOM = 0  # space kept after the name for the mascot to sit


# ---------------------------------------------------------------- text

class Face:
    def __init__(self, file):
        self.tt = TTFont(FONTS / file)
        self.upm = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.gs = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]

    def width(self, s, size):
        return sum(self.hmtx[self.cmap[ord(c)]][0] for c in s) * size / self.upm

    def path(self, s, size, x, y, fill, anchor="start", extra=""):
        if anchor == "end":
            x -= self.width(s, size)
        k = size / self.upm
        pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        cx = 0.0
        for c in s:
            g = self.cmap[ord(c)]
            self.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x + cx, y)))
            cx += self.hmtx[g][0] * k
        return f'<path fill="{fill}" d="{pen.getCommands()}"{extra}/>'


REG = Face("IBMPlexSansCondensed-Regular.ttf")
MED = Face("IBMPlexSansCondensed-Medium.ttf")
SEMI = Face("IBMPlexSansCondensed-SemiBold.ttf")


# ---------------------------------------------------------------- signal

# One beat as a sum of Gaussians (P, Q, R, S, T): (mV, centre s, width s)
WAVES = [(0.15, -0.20, 0.026), (-0.12, -0.034, 0.010), (1.15, 0.0, 0.011),
         (-0.28, 0.029, 0.011), (0.32, 0.26, 0.046)]


def beat_mv(t):
    return sum(a * math.exp(-((t - m) ** 2) / (2 * s * s)) for a, m, s in WAVES)


def simplify(pts, eps):
    """Ramer-Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-9
    worst, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / norm
        if d > worst:
            worst, idx = d, i
    if worst <= eps:
        return [pts[0], pts[-1]]
    return simplify(pts[: idx + 1], eps)[:-1] + simplify(pts[idx:], eps)


def ecg_points(x0, x1, y0, r_xs, px_s=150.0, px_mv=60.0, step=0.5):
    pts = []
    x = x0
    while x <= x1 + 1e-6:
        v = sum(beat_mv((x - r) / px_s) for r in r_xs)
        pts.append((x, y0 - v * px_mv))
        x += step
    return simplify(pts, 0.12)


# ---------------------------------------------------------------- handwriting

def load_allure():
    ns = {"s": "http://www.w3.org/2000/svg"}
    font = ET.parse(FONTS / "EMSAllure.svg").getroot().find(".//s:font", ns)
    dflt = float(font.get("horiz-adv-x"))
    glyphs = {}
    for g in font.findall("s:glyph", ns):
        if g.get("unicode"):
            glyphs[g.get("unicode")] = (g.get("d") or "", float(g.get("horiz-adv-x") or dflt))
    return glyphs


ALLURE = load_allure()


def name_strokes(text, x, y0, em):
    """Polylines for the handwritten name, baseline on y0."""
    s = em / 1000.0
    strokes, cursor = [], 0.0
    for ch in text:
        d, adv = ALLURE[ch]
        toks = d.replace(",", " ").split()
        i, cur = 0, None
        while i < len(toks):
            if toks[i] in ("M", "L"):
                cmd = toks[i]
                i += 1
            px, py = float(toks[i]), float(toks[i + 1])
            i += 2
            pt = (x + (cursor + px) * s, y0 - py * s)
            if cmd == "M":
                cur = [pt]
                strokes.append(cur)
                cmd = "L"
            else:
                cur.append(pt)
        cursor += adv
    return strokes, cursor * s


def name_width(text, em):
    return sum(ALLURE[c][1] for c in text) * em / 1000.0


def catmull(pts, tension=0.5):
    """Polyline -> list of cubic segments (p0, c1, c2, p3)."""
    segs = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        t = tension / 3.0 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 2, p1[1] + (p2[1] - p0[1]) * t / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 2, p2[1] - (p3[1] - p1[1]) * t / 2)
        segs.append((p1, c1, c2, p2))
    return segs


def cubic_len(seg, n=24):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = seg
    total, px, py = 0.0, x0, y0
    for k in range(1, n + 1):
        t = k / n
        u = 1 - t
        x = u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3
        y = u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3
        total += math.hypot(x - px, y - py)
        px, py = x, y
    return total


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def trace_paths(x_start, y0, r_xs, x_ecg_end, name_x, em, calibrate):
    """Returns [(d, length), ...]: the ECG run first, then each pen stroke of the name."""
    d, length = [], 0.0
    cx = x_start
    d.append(f"M{f(cx)},{f(y0)}")
    if calibrate:  # 1 mV x 0.2 s square pulse, as printed at the start of a strip
        for nx, ny in [(cx + 12, y0), (cx + 12, y0 - 60), (cx + 42, y0 - 60), (cx + 42, y0)]:
            d.append(f"L{f(nx)},{f(ny)}")
        length += 12 + 60 + 30 + 60
        cx += 42
    pts = ecg_points(cx, x_ecg_end, y0, r_xs)
    prev = (cx, y0)
    for p in pts:
        d.append(f"L{f(p[0])},{f(p[1])}")
        length += math.hypot(p[0] - prev[0], p[1] - prev[1])
        prev = p

    strokes, _ = name_strokes(NAME, name_x, y0, em)
    first = strokes[0]
    n0, n1 = first[0], first[1]
    ux, uy = n1[0] - n0[0], n1[1] - n0[1]
    un = math.hypot(ux, uy)
    ux, uy = ux / un, uy / un
    reach = math.hypot(n0[0] - prev[0], n0[1] - prev[1])
    conn = (prev, (prev[0] + reach * 0.55, prev[1]),
            (n0[0] - ux * reach * 0.45, n0[1] - uy * reach * 0.45), n0)
    d.append("C" + " ".join(f"{f(p[0])},{f(p[1])}" for p in conn[1:]))
    length += cubic_len(conn)

    # Each pen stroke of the name is its own path: browsers restart the dash
    # pattern at every subpath, so one multi-stroke path would draw all at once.
    parts = [("".join(d), length)]
    for st in strokes:
        ds, ls = [f"M{f(st[0][0])},{f(st[0][1])}"], 0.0
        for seg in catmull(st):
            ds.append("C" + " ".join(f"{f(p[0])},{f(p[1])}" for p in seg[1:]))
            ls += cubic_len(seg)
        parts.append(("".join(ds), ls))
    return parts


def trace_markup(parts, colour, t_ecg=2.3, t_name=2.9, delay=0.35, lift=0.05):
    """Paths plus the CSS that draws them one after another, like a pen.

    Without animation support the paths simply show fully drawn. Gaps in
    the dash pattern are longer than the path so nothing peeks out early.
    """
    css, paths = [], []
    name_len = sum(l for _, l in parts[1:])
    t = delay
    for i, (d, l) in enumerate(parts):
        dur = t_ecg if i == 0 else max(0.08, t_name * l / name_len)
        ease = "linear" if i == 0 else "cubic-bezier(.3,0,.6,1)"
        on, off = l + 4, l + 8
        css.append(f".p{i}{{stroke-dasharray:{on:.0f} {off:.0f};"
                   f"animation:k{i} {dur:.2f}s {ease} {t:.2f}s both}}"
                   f"@keyframes k{i}{{from{{stroke-dashoffset:{off:.0f}}}to{{stroke-dashoffset:0}}}}")
        paths.append(f'<path class="p{i}" d="{d}"/>')
        t += dur + (lift if i else 0)
    sel = ",".join(f".p{i}" for i in range(len(parts)))
    style = ("<style>" + "".join(css)
             + f"@media (prefers-reduced-motion:reduce){{{sel}{{animation:none}}}}</style>")
    group = (f'<g fill="none" stroke="{colour}" stroke-width="2.3" stroke-linecap="round" '
             f'stroke-linejoin="round">{"".join(paths)}</g>')
    return style, group


def layout_beats(x_min_r, x_name, rr):
    """R-wave positions placed back from the name, so the last T wave
    hands straight into the handwriting with no flat run before it."""
    rs = [x_name - 0.38 * 150 - 18]
    while rs[0] - rr >= x_min_r:
        rs.insert(0, rs[0] - rr)
    return rs


# ---------------------------------------------------------------- light: printed strip

def light():
    W, H, mm = 1200, 404, 6
    paper, minor, major = "#FFFBFB", "#FADFE4", "#F2AFBB"
    ink, muted = "#221A1F", "#76646C"
    y0 = 306
    em = 112
    name_x = W - 40 - MASCOT_ROOM - name_width(NAME, em)
    rr = 60 / RATE * 150
    rs = layout_beats(130, name_x, rr)
    ecg_end = rs[-1] + 0.36 * 150
    style, trace = trace_markup(trace_paths(36, y0, rs, ecg_end, name_x, em, calibrate=True), ink)

    grid = []
    for x in range(0, W + 1, mm):
        grid.append(f'<path d="M{x},0V{H}" stroke="{major if x % 30 == 0 else minor}" '
                    f'stroke-width="{1.1 if x % 30 == 0 else 0.6}"/>')
    for y in range(0, H + 1, mm):
        grid.append(f'<path d="M0,{y}H{W}" stroke="{major if y % 30 == 0 else minor}" '
                    f'stroke-width="{1.1 if y % 30 == 0 else 0.6}"/>')
    # minor lines first, major on top
    grid.sort(key=lambda s: major in s)

    t = []
    t.append(SEMI.path(PATIENT, 31, 36, 62, ink))
    x = 36
    for label, value in [("ID", HANDLE), ("Ward", WARD)]:
        t.append(REG.path(label, 19, x, 96, muted))
        x += REG.width(label, 19) + 9
        t.append(MED.path(value, 19, x, 96, ink))
        x += MED.width(value, 19) + 30
    t.append(REG.path("Monitoring since", 19, 36, 124, muted))
    t.append(MED.path(SINCE, 19, 36 + REG.width("Monitoring since", 19) + 9, 124, ink))
    rx = 724
    t.append(MED.path(FINDING, 22, rx, 62, ink))
    t.append(REG.path(NOTE, 19, rx, 96, ink))
    t.append(MED.path("II", 21, 36, 204, ink))
    t.append(REG.path("25 mm/s", 16, 36, 384, muted))
    t.append(REG.path("10 mm/mV", 16, 112, 384, muted))
    t.append(REG.path("0.05–150 Hz", 16, 196, 384, muted))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Muktanan Mohapatra, tinySage</title>
<desc id="d">A printed ECG strip on pink grid paper. Header: {PATIENT}; ID {HANDLE}; {WARD}; monitoring since {SINCE}. Interpretation: {FINDING}. {NOTE} The lead II trace runs a few beats, then lifts into the handwritten name {NAME}.</desc>
{style}
<rect width="{W}" height="{H}" fill="{paper}"/>
<g>{''.join(grid)}</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{major}"/>
<g>{''.join(t)}</g>
{trace}
</svg>
"""


# ---------------------------------------------------------------- dark: bedside monitor

def dark():
    W, H = 1200, 404
    # one accent only: everything that is not the signal is warm grey on black
    screen, bar, rule = "#000000", "#151214", "#2B2629"
    text, muted = "#EEE8EB", "#9C9196"
    rose = "#F4A6C2"
    y0 = 306
    em = 100
    wave_right = 892 - MASCOT_ROOM
    name_x = wave_right - name_width(NAME, em)
    rr = 60 / RATE * 150
    rs = layout_beats(80, name_x, rr)
    ecg_end = rs[-1] + 0.36 * 150
    style, trace = trace_markup(trace_paths(28, y0, rs, ecg_end, name_x, em, calibrate=False), rose)

    t = []
    t.append(SEMI.path(PATIENT, 22, 28, 37, text))
    t.append(REG.path(HANDLE, 18, 28 + SEMI.width(PATIENT, 22) + 16, 37, muted))
    t.append(REG.path(WARD, 18, W - 28, 37, muted, anchor="end"))

    note = (f'<rect x="28" y="76" width="3" height="23" fill="{rose}"/>'
            + REG.path(NOTE, 18, 42, 94, text))
    t.append(REG.path(f"Monitoring since {SINCE}", 17, W - 28, 94, muted, anchor="end"))

    t.append(MED.path("II", 20, 28, 148, rose))
    t.append(REG.path("25 mm/s", 15, 28, 384, muted))

    px = 944
    t.append(MED.path("HR", 22, px, 148, rose))
    t.append(REG.path("bpm", 16, W - 28, 148, muted, anchor="end"))
    t.append(MED.path(str(RATE), 118, W - 28, 286, rose, anchor="end"))
    t.append(MED.path(FINDING, 18, px, 340, text))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Muktanan Mohapatra, tinySage</title>
<desc id="d">A bedside monitor. Patient {PATIENT}, {HANDLE}, {WARD}. Message: {NOTE} Lead II shows a few beats that lift into the handwritten name {NAME}. HR {RATE} bpm, {FINDING.lower()}.</desc>
{style}
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{screen}" stroke="{rule}"/>
<path d="M10,0H{W - 10}A10,10 0 0 1 {W},10V56H0V10A10,10 0 0 1 10,0Z" fill="{bar}"/>
{note}
<path d="M920,124V372" stroke="{rule}"/>
<g>{''.join(t)}</g>
{trace}
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in [("header-light.svg", light), ("header-dark.svg", dark)]:
        svg = fn()
        (OUT / name).write_text(svg)
        print(f"{name}: {len(svg) / 1024:.1f} KB")

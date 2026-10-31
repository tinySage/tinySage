"""tinySage, the strip's mascot: a small black cat with blue eyes and a green
sprout growing from its head.

draw(pose, theme, ...) returns an SVG <g> for one pose. The cat is drawn in a
100 x 100 box with its feet resting on y = 90, then scaled to `size` and
placed so its feet sit on `baseline` at horizontal centre `x`.
"""

import math

POSES = ("stand", "hop", "land", "sit")  # also "walk" and "perch", used by the route

# printed strip: an ink-black cat on paper
LIGHT = dict(outline="#221A1F", fill="#221A1F", eye="#5DA9E9", pupil="#0E1A2B",
             shine="#FFFFFF", face="#F4A9B8", blush="#F4A9B8", ear="#F2AFBB",
             leaf="#8DBB75", vein="#4F7A3E")
# monitor: the same cat, outlined in the trace's rose so it reads on black
DARK = dict(outline="#F4A6C2", fill="#1A1618", eye="#6CB6F0", pupil="#0E1A2B",
            shine="#FFFFFF", face="#F4A6C2", blush="#F4A6C2", ear="#F4A6C2",
            leaf="#86B86E", vein="#A9D493")


def _f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _leaf(bx, by, length, width, angle_deg):
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)

    def p(u, v):
        return bx + u * ca - v * sa, by + u * sa + v * ca

    L, W = length, width
    pts = [p(0, 0), p(L * .25, -W), p(L * .72, -W * .95), p(L, 0),
           p(L * .72, W * .95), p(L * .25, W), p(0, 0)]
    q = [f"{_f(x)},{_f(y)}" for x, y in pts]
    outline = f"M{q[0]}C{q[1]} {q[2]} {q[3]}C{q[4]} {q[5]} {q[6]}Z"
    m0, m1 = p(L * .15, 0), p(L * .75, 0)
    return outline, f"M{_f(m0[0])},{_f(m0[1])}L{_f(m1[0])},{_f(m1[1])}"


SILHOUETTE = ("M22,65C22,54 24,46 28,40"
              "L30.5,24.5Q31.5,20.5 34.5,23"
              "L43.5,32.5C47.5,31.4 52.5,31.4 56.5,32.5"
              "L65.5,23Q68.5,20.5 69.5,24.5"
              "L72,40C76,46 78,54 78,65"
              "C78,81 66,88 50,88C34,88 22,81 22,65Z")

LIMBS = {
    "stand": ["M25,58C20,54 17,49 17,43"],                              # one paw waving, away from the tail
    "hop":   ["M26,58C22,53 20,48 20,43", "M74,58C78,53 80,48 80,43"],   # both paws up
    "land":  ["M23,68C19,70 15,73 13,77", "M77,68C81,70 85,73 87,77"],   # arms out for balance
    "sit":   [],
    "walk":  [],
    "perch": [],
}
TAILS = {
    "stand": "M73,80C86,82 93,72 90,61C89,56 85,55 84,59",
    "hop":   "M70,82C80,90 92,86 94,74",
    "land":  "M73,82C86,84 94,78 95,70",
    "sit":   "M68,86C78,92 91,89 93,79",
    "walk":  "M73,78C84,76 90,66 88,55C87,51 84,51 84,54",   # tail up, trotting
    "perch": "M72,84C81,88 83,99 80,110C79,114 75,115 74,111",  # hangs over the edge it sits on
}


def draw(pose, theme, x=0.0, baseline=0.0, size=46.0, stroke=2.3, extra=""):
    t = theme
    s = size / 90.0
    sx, sy = {"stand": (1, 1), "walk": (1, 1), "hop": (.9, 1.1), "land": (1.14, .84),
              "sit": (1.05, .92), "perch": (1.05, .92)}[pose]
    sw = stroke / s
    same = t["outline"] == t["fill"]

    def thick(d, w):
        """An outlined limb: outline-coloured wide stroke, fill-coloured core."""
        out = f'<path d="{d}" fill="none" stroke="{t["outline"]}" stroke-width="{_f(w + (0 if same else 2 * sw))}"/>'
        core = "" if same else f'<path d="{d}" fill="none" stroke="{t["fill"]}" stroke-width="{_f(w)}"/>'
        return out + core

    g = []
    g.append(thick(TAILS[pose], 6.5))
    feet = [(42, 86, 5, 3.4), (58, 86, 5, 3.4)] if pose == "hop" else \
           [] if pose in ("sit", "perch") else [(39, 88, 7, 3.8), (61, 88, 7, 3.8)]
    for cx, cy, rx, ry in feet:
        g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{t["fill"]}"/>')
    for d in LIMBS[pose]:
        g.append(thick(d, 6))

    # sprout, rooted behind the head
    g.append(f'<path d="M50,33C50,28 51,24 50.5,18.5" fill="none" stroke="{t["vein"]}"/>')
    for outline, vein in (_leaf(50.6, 21.5, 14, 5.6, -156), _leaf(50.6, 19.5, 15.5, 6.2, -27)):
        g.append(f'<path d="{outline}" fill="{t["leaf"]}" stroke="{t["vein"]}"/>')
        g.append(f'<path d="{vein}" fill="none" stroke="{t["vein"]}" stroke-width="{_f(sw * .5)}"/>')

    g.append(f'<path d="{SILHOUETTE}" fill="{t["fill"]}"/>')
    g.append(f'<path d="M31.6,35.5L32.7,27L39.3,33.2Z M68.4,35.5L67.3,27L60.7,33.2Z" '
             f'fill="{t["ear"]}" opacity=".75" stroke="none"/>')

    # whiskers
    g.append(f'<path d="M22.5,63.5L13,61.5M22.5,67L13,69M77.5,63.5L87,61.5M77.5,67L87,69" '
             f'fill="none" stroke-width="{_f(sw * .6)}"/>')

    # cheeks and nose
    g.append(f'<ellipse cx="31.5" cy="65" rx="4" ry="2.3" fill="{t["blush"]}" opacity=".62" stroke="none"/>'
             f'<ellipse cx="68.5" cy="65" rx="4" ry="2.3" fill="{t["blush"]}" opacity=".62" stroke="none"/>'
             f'<path d="M48.6,62.6L51.4,62.6L50,64.2Z" fill="{t["face"]}" stroke="{t["face"]}" stroke-width="{_f(sw * .3)}"/>')

    lid = f'fill="none" stroke="{t["eye"]}" stroke-width="{_f(sw * .95)}"'
    mouth_w = (f'<path d="M46.5,65.4Q48.2,67.6 50,65.6Q51.8,67.6 53.5,65.4" fill="none" '
               f'stroke="{t["face"]}" stroke-width="{_f(sw * .65)}"/>')
    if pose in ("stand", "walk", "land"):
        for cx in (40, 60):
            g.append(f'<ellipse cx="{cx}" cy="57" rx="5" ry="5.6" fill="{t["eye"]}" stroke="none"/>'
                     f'<ellipse cx="{cx}" cy="57.3" rx="2" ry="3.6" fill="{t["pupil"]}" stroke="none"/>'
                     f'<circle cx="{cx + 1.9}" cy="54.9" r="1.4" fill="{t["shine"]}" stroke="none"/>'
                     f'<circle cx="{cx - 1.5}" cy="59.3" r=".7" fill="{t["shine"]}" stroke="none"/>')
        g.append(mouth_w if pose in ("stand", "walk") else
                 f'<ellipse cx="50" cy="66.8" rx="1.6" ry="2" fill="{t["face"]}" stroke="none"/>')
    elif pose == "hop":
        g.append(f'<path d="M35.5,58Q40,52.5 44.5,58M55.5,58Q60,52.5 64.5,58" {lid}/>')
        g.append(f'<path d="M47,65.2Q50,70.5 53,65.2Z" fill="{t["face"]}" stroke="none"/>')
    else:  # sit / perch: content, eyes closed, paws tucked in front
        g.append(f'<path d="M35.5,57Q40,61 44.5,57M55.5,57Q60,61 64.5,57" {lid}/>')
        g.append(mouth_w)
        for cx in (41, 59):
            g.append(f'<ellipse cx="{cx}" cy="85.5" rx="6.5" ry="3.6" fill="{t["fill"]}"/>')

    tx, ty = x - 50 * s, baseline - 90 * s
    squash = f"translate(50 90) scale({sx} {sy}) translate(-50 -90)"
    return (f'<g transform="translate({_f(tx)} {_f(ty)}) scale({_f(s)})"{extra}>'
            f'<g transform="{squash}" stroke="{t["outline"]}" stroke-width="{_f(sw)}" '
            f'stroke-linecap="round" stroke-linejoin="round">{"".join(g)}</g></g>')


# ---------------------------------------------------------------- the route

def _quad(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def route(theme, box_w, box_h, left, top, size=58.0, start=0.6, speed=260.0):
    """The cat's walk around a framed panel.

    The panel occupies (left, top, box_w, box_h) inside a larger canvas.
    The cat trots in along the panel's bottom edge, crouches near the
    bottom-right corner, swings up round the right side, lands on the top
    edge and settles there with its tail hanging over the front.

    Returns (css, markup, canvas_height). With animation off or unsupported
    the cat simply shows in its final perch, so the still image is complete.
    """
    floor = top + box_h                      # walks on the bottom edge itself
    x_in = -size                             # starts just off the left edge
    x_corner = left + box_w - 46             # near the bottom-right corner
    perch = (left + box_w - 96, top)         # top edge, near the right corner

    t_walk0 = start
    t_walk1 = t_walk0 + (x_corner - x_in) / speed
    t_crouch = t_walk1 + 0.3
    t_air = t_crouch + 0.8
    t_land = t_air + 0.26
    total = t_land + 0.05

    # jump: swing out past the right edge and over onto the top edge,
    # keeping the whole cat inside the canvas at the top of the arc
    p0, p2 = (x_corner, floor), perch
    cx = left + box_w + 46
    ctrl_y = top - 80
    while True:
        apex = min(_quad(p0, (cx, ctrl_y), p2, i / 80)[1] for i in range(81))
        if apex >= size * 0.98 or ctrl_y >= top:
            break
        ctrl_y += 3
    p1 = (cx, ctrl_y)

    def pct(t):
        return f"{100 * t / total:.3f}%"

    def pos(x, y):
        return f"transform:translate({x:.1f}px,{y:.1f}px)"

    move = [f"0%{{{pos(x_in, floor)}}}", f"{pct(t_walk0)}{{{pos(x_in, floor)}}}",
            f"{pct(t_walk1)}{{{pos(x_corner, floor)}}}", f"{pct(t_crouch)}{{{pos(x_corner, floor)}}}"]
    for i in range(1, 16):
        x, y = _quad(p0, p1, p2, i / 15)
        move.append(f"{pct(t_crouch + (t_air - t_crouch) * i / 15)}{{{pos(x, y)}}}")
    move.append(f"100%{{{pos(*perch)}}}")

    # which pose is showing when: (class, start, end)
    windows = [("walk", 0, t_walk1), ("land", t_walk1, t_crouch), ("hop", t_crouch, t_air),
               ("land2", t_air, t_land), ("perch", t_land, total)]
    css = [f".cat{{animation:catmove {total:.2f}s linear both}}"
           f"@keyframes catmove{{{''.join(move)}}}"]
    for name, a, b in windows:
        frames = [] if a == 0 else ["0%{opacity:0}"]
        frames.append(f"{pct(a)}{{opacity:1}}")
        frames.append(f"{pct(b)}{{opacity:0}}100%{{opacity:0}}" if b < total else "100%{opacity:1}")
        css.append(f".c-{name}{{animation:o-{name} {total:.2f}s step-end both}}"
                   f"@keyframes o-{name}{{{''.join(frames)}}}")
    bob_n = max(1, int((t_walk1 - t_walk0) / 0.3))
    css.append(f".bob{{animation:bob .3s ease-in-out {t_walk0:.2f}s {bob_n}}}"
               "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}")
    css.append("@media (prefers-reduced-motion:reduce){.cat,.bob,"
               + ",".join(f".c-{n}" for n, *_ in windows) + "{animation:none}}")

    poses = {"walk": "walk", "land": "land", "hop": "hop", "land2": "land", "perch": "perch"}
    groups = []
    for name, pose in poses.items():
        shown = "1" if name == "perch" else "0"
        body = draw(pose, theme, x=0, baseline=0, size=size)
        if name == "walk":
            body = f'<g class="bob">{body}</g>'
        groups.append(f'<g class="c-{name}" opacity="{shown}">{body}</g>')
    markup = (f'<g class="cat" transform="translate({perch[0]:.1f} {perch[1]:.1f})">'
              + "".join(groups) + "</g>")
    return "".join(css), markup, floor + 6

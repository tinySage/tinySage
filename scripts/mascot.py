"""tinySage, the strip's mascot: a small round sage with a sprig on its head.

draw(pose, ...) returns an SVG <g> for one pose. The character is drawn in a
100 x 100 box with its feet resting on y = 90, so placing it on a baseline is
a matter of translating (x - 50*s, baseline - 90*s).
"""

import math

POSES = ("stand", "hop", "land", "sit")


def _f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _leaf(bx, by, length, width, angle_deg):
    """A soft lance-shaped sage leaf from (bx, by), tip pointing at angle."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)

    def p(u, v):  # leaf-local (along, across) -> canvas
        return bx + u * ca - v * sa, by + u * sa + v * ca

    L, W = length, width
    pts = [p(0, 0), p(L * .28, -W), p(L * .72, -W * .9), p(L, 0),
           p(L * .72, W * .9), p(L * .28, W), p(0, 0)]
    q = [f"{_f(x)},{_f(y)}" for x, y in pts]
    outline = f"M{q[0]}C{q[1]} {q[2]} {q[3]}C{q[4]} {q[5]} {q[6]}Z"
    m0, m1 = p(L * .12, 0), p(L * .78, 0)
    vein = f"M{_f(m0[0])},{_f(m0[1])}L{_f(m1[0])},{_f(m1[1])}"
    return outline, vein


def draw(pose, ink, fill, blush, leaf_fill=None, x=0.0, baseline=0.0, size=46.0,
         stroke=2.3, extra=""):
    """One pose of the mascot. `size` is its height in canvas units."""
    s = size / 90.0
    sx, sy = {"stand": (1, 1), "hop": (.9, 1.1), "land": (1.14, .84), "sit": (1.05, .92)}[pose]
    sw = stroke / s  # keep the line weight constant whatever the scale

    parts = []
    # feet behind the body (standing / hopping / landing)
    if pose == "hop":
        feet = [(42, 86, 5, 3.4), (58, 86, 5, 3.4)]
    elif pose == "sit":
        feet = []
    else:
        feet = [(39, 88, 7, 3.8), (61, 88, 7, 3.8)]
    for cx, cy, rx, ry in feet:
        parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"/>')

    # arms
    if pose == "hop":
        arms = ["M25,58c-5,-4 -7,-10 -6,-15", "M75,58c5,-4 7,-10 6,-15"]
    elif pose == "land":
        arms = ["M23,66c-5,1 -9,4 -10,8", "M77,66c5,1 9,4 10,8"]
    elif pose == "sit":
        arms = ["M30,70c3,3 8,4 12,3", "M70,70c-3,3 -8,4 -12,3"]
    else:
        arms = ["M23,64c-5,2 -7,6 -7,10", "M77,64c5,-3 8,-10 8,-16"]  # a small wave

    body = ("M22,63C22,42 35,31 50,31C65,31 78,42 78,63"
            "C78,80 66,88 50,88C34,88 22,80 22,63Z")

    # sprig: stem plus three leaves
    stem = "M50,31C50,26 51,21 50,15"
    leaves = [_leaf(50, 25, 17, 5.2, -152), _leaf(50.5, 21, 16, 5, -30), _leaf(50, 15.5, 9.5, 3.4, -96)]

    if pose in ("hop",):
        eyes = (f'<path d="M37,59Q40.5,54 44,59M56,59Q59.5,54 63,59" fill="none"/>')
        mouth = f'<path d="M46,65Q50,71 54,65Z" fill="{ink}" stroke-linejoin="round"/>'
    elif pose == "sit":
        eyes = (f'<path d="M37,58Q40.5,62 44,58M56,58Q59.5,62 63,58" fill="none"/>')
        mouth = '<path d="M47.5,66Q50,68.5 52.5,66" fill="none"/>'
    else:
        eyes = (f'<ellipse cx="40.5" cy="58" rx="2.7" ry="3.6" fill="{ink}" stroke="none"/>'
                f'<ellipse cx="59.5" cy="58" rx="2.7" ry="3.6" fill="{ink}" stroke="none"/>'
                f'<circle cx="41.4" cy="56.6" r=".9" fill="{fill}" stroke="none"/>'
                f'<circle cx="60.4" cy="56.6" r=".9" fill="{fill}" stroke="none"/>')
        mouth = ('<path d="M47,65.5Q50,69 53,65.5" fill="none"/>' if pose == "stand"
                 else f'<ellipse cx="50" cy="66.5" rx="1.9" ry="2.3" fill="{ink}" stroke="none"/>')

    cheeks = (f'<ellipse cx="33" cy="65" rx="4.6" ry="2.6" fill="{blush}" stroke="none"/>'
              f'<ellipse cx="67" cy="65" rx="4.6" ry="2.6" fill="{blush}" stroke="none"/>')

    sprig = [f'<path d="{stem}" fill="none"/>']
    for outline, vein in leaves:
        sprig.append(f'<path d="{outline}" fill="{leaf_fill or fill}"/>')
        sprig.append(f'<path d="{vein}" fill="none" stroke-width="{_f(sw * .55)}"/>')

    seat = []
    if pose == "sit":
        seat = [f'<ellipse cx="35" cy="88" rx="8" ry="4" fill="{fill}"/>',
                f'<ellipse cx="65" cy="88" rx="8" ry="4" fill="{fill}"/>']

    inner = "".join(
        parts
        + [f'<path d="{a}" fill="none"/>' for a in arms]
        + sprig
        + [f'<path d="{body}" fill="{fill}"/>', cheeks, eyes, mouth]
        + seat
    )
    tx = x - 50 * s
    ty = baseline - 90 * s
    squash = f"translate(50 90) scale({sx} {sy}) translate(-50 -90)"
    return (f'<g transform="translate({_f(tx)} {_f(ty)}) scale({_f(s)})"{extra}>'
            f'<g transform="{squash}" stroke="{ink}" stroke-width="{_f(sw)}" '
            f'stroke-linecap="round" stroke-linejoin="round">{inner}</g></g>')

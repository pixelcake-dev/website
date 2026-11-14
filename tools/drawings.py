"""The drawings of the site: small networks seen from above and from the side
(isometric), thin lines, the orange of the logo for what moves.

There are five: the one that opens the home page, one for each of the three
things PixelCake does (design, ask, present), and the one that opens the page
on why it is being built (a whiteboard, and the network it becomes). Each tells a short story
in a loop, with the animation elements of SVG; assets/site.js starts a story
when its drawing comes into view and stills it for who asked for less motion.

Colours come from the style sheet (assets/site.css), so one drawing serves
the light and the dark theme.

    python tools/drawings.py

writes every drawing into the pages, between the comments that name it:

    <!-- drawing:hero --> ... <!-- /drawing:hero -->
"""

import math
import os
import re
import sys

S = 52.0  # pixels for one unit of the plan
COS, SIN = math.cos(math.radians(30)), math.sin(math.radians(30))
SHADOW = 1.0  # how far under the board its dashed shadow lies
BOARD_H = 0.3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ("index.html", "why.html")


# --- geometry ----------------------------------------------------------------


def iso(x, y, z=0.0):
    """Plan coordinates (x to the right and down, y to the left and down, z up) to the screen."""
    return ((x - y) * COS * S, (x + y) * SIN * S - z * S)


def pts(points):
    return " ".join(f"{px:.1f},{py:.1f}" for px, py in points)


def polygon(points, cls, inner=""):
    return f'<polygon class="{cls}" points="{pts(points)}">{inner}</polygon>' if inner else (
        f'<polygon class="{cls}" points="{pts(points)}"/>'
    )


def polyline(points, cls, inner="", attrs=""):
    head = f'<polyline class="{cls}" points="{pts(points)}"{attrs}'
    return f"{head}>{inner}</polyline>" if inner else f"{head}/>"


def on_board(plan_points, z=0.02):
    return [iso(x, y, z) for x, y in plan_points]


def length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def fractions(points):
    """How far along a line each of its points is, from 0 to 1."""
    total, run, out = length(points), 0.0, [0.0]
    for a, b in zip(points, points[1:]):
        run += math.dist(a, b)
        out.append(run / total)
    return out


def centre(item):
    x, y, w, d, _ = item
    return (x + w / 2, y + d / 2)


def top_of(item):
    x, y, w, d, h = item
    return iso(x + w / 2, y + d / 2, h)


# --- boxes and what is drawn on them -----------------------------------------


def box(x, y, w, d, h, z=0.0, top="iso-top", extra=None):
    """A box standing at (x, y): the three faces one sees."""
    left = [iso(x, y + d, z), iso(x + w, y + d, z), iso(x + w, y + d, z + h), iso(x, y + d, z + h)]
    right = [iso(x + w, y, z), iso(x + w, y + d, z), iso(x + w, y + d, z + h), iso(x + w, y, z + h)]
    roof = [iso(x, y, z + h), iso(x + w, y, z + h), iso(x + w, y + d, z + h), iso(x, y + d, z + h)]
    out = [polygon(left, "iso-left"), polygon(right, "iso-right"), polygon(roof, top)]
    if extra:
        out.extend(extra(x, y, w, d, h, z))
    return out


def footprint(item, grow=0.14):
    """The dashed outline a box leaves on the board."""
    x, y, w, d, _ = item
    a, b, c, e = x - grow, y - grow, x + w + grow, y + d + grow
    return polygon([iso(a, b), iso(c, b), iso(c, e), iso(a, e)], "iso-foot")


def slots(count):
    """Horizontal lines on the right face: the units of a server."""

    def draw(x, y, w, d, h, z):
        return [
            polyline([iso(x + w, y + 0.14, z + h * i / (count + 1)), iso(x + w, y + d - 0.14, z + h * i / (count + 1))], "iso-detail")
            for i in range(1, count + 1)
        ]

    return draw


def bricks(x, y, w, d, h, z):
    """Courses of bricks on the right face of a firewall."""
    lines, rows = [], 5
    for i in range(1, rows):
        level = z + h * i / rows
        lines.append(polyline([iso(x + w, y, level), iso(x + w, y + d, level)], "iso-detail"))
    for i in range(rows):
        low, high = z + h * i / rows, z + h * (i + 1) / rows
        for offset in (0.4, 0.95, 1.5) if i % 2 == 0 else (0.13, 0.68, 1.23):
            if offset < d:
                lines.append(polyline([iso(x + w, y + offset, low), iso(x + w, y + offset, high)], "iso-detail"))
    return lines


def bricks_left(x, y, w, d, h, z):
    """The same on the left face, for a firewall that lies along x."""
    lines, rows = [], 5
    for i in range(1, rows):
        level = z + h * i / rows
        lines.append(polyline([iso(x, y + d, level), iso(x + w, y + d, level)], "iso-detail"))
    for i in range(rows):
        low, high = z + h * i / rows, z + h * (i + 1) / rows
        for offset in (0.4, 0.95, 1.5) if i % 2 == 0 else (0.13, 0.68, 1.23):
            if offset < w:
                lines.append(polyline([iso(x + offset, y + d, low), iso(x + offset, y + d, high)], "iso-detail"))
    return lines


def ports_left(count):
    """Small openings on the left face of a switch that lies along x."""

    def draw(x, y, w, d, h, z):
        step = w / (count + 1)
        return [
            polygon(
                [
                    iso(x + step * i - 0.08, y + d, z + h * 0.3),
                    iso(x + step * i + 0.08, y + d, z + h * 0.3),
                    iso(x + step * i + 0.08, y + d, z + h * 0.7),
                    iso(x + step * i - 0.08, y + d, z + h * 0.7),
                ],
                "iso-port",
            )
            for i in range(1, count + 1)
        ]

    return draw


def ports_right(count):
    """The same on the right face, for a switch that lies along y."""

    def draw(x, y, w, d, h, z):
        step = d / (count + 1)
        return [
            polygon(
                [
                    iso(x + w, y + step * i - 0.08, z + h * 0.3),
                    iso(x + w, y + step * i + 0.08, z + h * 0.3),
                    iso(x + w, y + step * i + 0.08, z + h * 0.7),
                    iso(x + w, y + step * i - 0.08, z + h * 0.7),
                ],
                "iso-port",
            )
            for i in range(1, count + 1)
        ]

    return draw


def screen(x, y, w, d, h, z):
    """The screen of a PC, on its left face."""
    m = 0.14
    return [
        polygon(
            [iso(x + m, y + d, z + m), iso(x + w - m, y + d, z + m), iso(x + w - m, y + d, z + h - m), iso(x + m, y + d, z + h - m)],
            "iso-screen",
        )
    ]


def lamps(x, y, w, d, h, z):
    """Three lamps on the left face of a router."""
    return [
        polygon(
            [
                iso(x + 0.22 + 0.22 * i, y + d, z + h * 0.36),
                iso(x + 0.34 + 0.22 * i, y + d, z + h * 0.36),
                iso(x + 0.34 + 0.22 * i, y + d, z + h * 0.64),
                iso(x + 0.22 + 0.22 * i, y + d, z + h * 0.64),
            ],
            "iso-port",
        )
        for i in range(3)
    ]


# The devices, by their size: (width along x, depth along y, height)
def pc(x, y):
    return (x, y, 0.9, 0.8, 0.75)


def router(x, y):
    return (x, y, 1.2, 1.2, 0.5)


def server(x, y):
    return (x, y, 1.0, 1.0, 1.6)


def switch_x(x, y):
    return (x, y, 2.0, 0.85, 0.3)


def switch_y(x, y):
    return (x, y, 0.85, 2.0, 0.3)


def firewall(x, y):
    return (x, y, 0.34, 1.7, 1.5)


def firewall_x(x, y):
    return (x, y, 1.7, 0.34, 1.5)


def internet(x, y):
    return (x, y, 1.4, 1.1, 0.24)


def stand(things):
    """What stands on the board, the far things first. A thing: (item, class of its top, details, before, after)."""
    out = []
    for thing in sorted(things, key=lambda t: (t[0][0] + t[0][2]) + (t[0][1] + t[0][3])):
        item, top, extra = thing[0], thing[1], thing[2]
        before = thing[3] if len(thing) > 3 else ""
        after = thing[4] if len(thing) > 4 else ""
        x, y, w, d, h = item
        out.append(before + "".join(box(x, y, w, d, h, top=top, extra=extra)) + after)
    return out


def board(width, depth):
    """The board: its shadow, its two sides, its top with the dots of the canvas."""
    out = [
        polygon(
            [iso(0, 0, -SHADOW), iso(width, 0, -SHADOW), iso(width, depth, -SHADOW), iso(0, depth, -SHADOW)],
            "iso-foot",
        )
    ]
    out.extend(box(0, 0, width, depth, BOARD_H, z=-BOARD_H, top="iso-board"))
    dots, gx = [], 0.6
    while gx < width - 0.2:
        gy = 0.6
        while gy < depth - 0.2:
            px, py = iso(gx, gy)
            dots.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1"/>')
            gy += 0.6
        gx += 0.6
    out.append('<g class="iso-dots">' + "".join(dots) + "</g>")
    return out


# --- what moves --------------------------------------------------------------


def num(value):
    return f"{value:.3f}".rstrip("0").rstrip(".") or "0"


def animate(attribute, frames, dur):
    """`frames`: (moment from 0 to 1, value), the first at 0 and the last at 1."""
    assert frames[0][0] == 0 and frames[-1][0] == 1, frames
    times = ";".join(num(t) for t, _ in frames)
    values = ";".join(v if isinstance(v, str) else num(v) for _, v in frames)
    return f'<animate attributeName="{attribute}" dur="{dur}s" repeatCount="indefinite" keyTimes="{times}" values="{values}"/>'


def shown(start, end, dur, ramp=0.02):
    """Opacity of something that is there from `start` to `end` of the story."""
    frames = [(0, 1 if start <= 0 else 0)]
    if start > 0:
        frames += [(start, 0), (min(start + ramp, 1), 1)]
    if end < 1:
        frames += [(end, 1), (min(end + ramp, 1), 0)]
    if frames[-1][0] != 1:
        frames.append((1, frames[-1][1]))
    return animate("opacity", frames, dur)


def travel(points, frames, dur):
    """Along a line of the screen: (moment, how far along) pairs."""
    path = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in points)
    times = ";".join(num(t) for t, _ in frames)
    where = ";".join(num(p) for _, p in frames)
    return (
        f'<animateMotion dur="{dur}s" repeatCount="indefinite" calcMode="linear" '
        f'keyTimes="{times}" keyPoints="{where}" path="{path}"/>'
    )


def flash(item, moments, dur):
    """The top of a device lights up for an instant at each of `moments`."""
    x, y, w, d, h = item
    frames = [(0, 0)]
    for at in moments:
        frames += [(at, 0), (at + 0.015, 0.75), (at + 0.07, 0)]
    frames.append((1, 0))
    roof = [iso(x, y, h), iso(x + w, y, h), iso(x + w, y + d, h), iso(x, y + d, h)]
    return polygon(roof, "iso-flash", inner=animate("opacity", frames, dur))


def packet(inner, size=0.26):
    """An orange pixel at the origin, moved by what is put inside it."""
    half = size / 2
    return '<g class="iso-px">' + inner + "".join(box(-half, -half, size, size, size, z=0.02)) + "</g>"


# --- flat things over the drawing --------------------------------------------


def plus(px, py, arm=7):
    return f'<path class="iso-mark" d="M{px - arm:.1f} {py:.1f} H{px + arm:.1f} M{px:.1f} {py - arm:.1f} V{py + arm:.1f}"/>'


def cross(px, py, arm=5, inner=""):
    d = f"M{px - arm:.1f} {py - arm:.1f} L{px + arm:.1f} {py + arm:.1f} M{px + arm:.1f} {py - arm:.1f} L{px - arm:.1f} {py + arm:.1f}"
    return f'<path class="iso-cross" d="{d}">{inner}</path>' if inner else f'<path class="iso-cross" d="{d}"/>'


LINE, PAD = 21, 13


def note_height(count):
    return PAD * 2 + LINE * count - 7


def note(lines, px, py, width, leader=None, inner="", dur=0):
    """A boxed note. A line: (text, class) or (text, class, the moment it appears)."""
    out = []
    if leader:
        (sx, sy), (tx, ty) = leader
        out.append(f'<path class="iso-leader" d="M{sx:.1f} {sy:.1f} L{tx:.1f} {ty:.1f}"/>')
    out.append(f'<rect class="iso-note" x="{px:.1f}" y="{py:.1f}" width="{width}" height="{note_height(len(lines))}"/>')
    for i, line in enumerate(lines):
        text, cls = line[0], line[1]
        appear = animate("opacity", line[2], dur) if len(line) > 2 else ""
        start = ' opacity="0"' if len(line) > 2 and line[2][0][1] == 0 else ""
        out.append(
            f'<text class="{cls}" x="{px + PAD:.1f}" y="{py + PAD + 12 + i * LINE:.1f}" xml:space="preserve"{start}>{appear}{text}</text>'
        )
    return "<g>" + inner + "".join(out) + "</g>"


def tag(text, px, py, inner="", start_hidden=False):
    """A small label on a cable, as the app writes them."""
    width = 9 + 7.4 * len(text)
    hidden = ' opacity="0"' if start_hidden else ""
    return (
        f"<g{hidden}>{inner}"
        f'<rect class="iso-tag" x="{px - width / 2:.1f}" y="{py - 10:.1f}" width="{width:.1f}" height="20"/>'
        f'<text class="iso-tag-text" x="{px:.1f}" y="{py + 4:.1f}" text-anchor="middle">{text}</text></g>'
    )


def badge(px, py, text, lit, dur):
    """A numbered mark; `lit`: the frames of the opacity of its orange state."""
    return (
        f'<circle class="iso-badge" cx="{px:.1f}" cy="{py:.1f}" r="12"/>'
        f'<text class="iso-badge-text" x="{px:.1f}" y="{py + 4.5:.1f}" text-anchor="middle">{text}</text>'
        f'<g opacity="0">{animate("opacity", lit, dur)}'
        f'<circle class="iso-badge on" cx="{px:.1f}" cy="{py:.1f}" r="12"/>'
        f'<text class="iso-badge-text on" x="{px:.1f}" y="{py + 4.5:.1f}" text-anchor="middle">{text}</text></g>'
    )


def sheet(parts, width, depth, label, still, top=70, bottom=82, side=26):
    """The whole drawing, with the four marks of its corners."""
    left, right = iso(0, depth), iso(width, 0)
    min_x, max_x = left[0] - side, right[0] + side
    min_y, max_y = iso(0, 0)[1] - top, iso(width, depth, -SHADOW)[1] + bottom
    marks = [plus(px, py) for px in (min_x + 8, max_x - 8) for py in (min_y + 8, max_y - 8)]
    return (
        f'<svg class="iso" viewBox="{min_x:.0f} {min_y:.0f} {max_x - min_x:.0f} {max_y - min_y:.0f}" '
        f'data-still="{still}" role="img" aria-label="{label}">\n' + "\n".join(parts + marks) + "\n</svg>"
    )


def corners(width, depth, top=70, bottom=82, side=26):
    """(left, top, right, bottom) of the sheet, to place the notes in its empty corners."""
    left, right = iso(0, depth), iso(width, 0)
    return (left[0] - side, iso(0, 0)[1] - top, right[0] + side, iso(width, depth, -SHADOW)[1] + bottom)


# A note on where things stand. One sees the faces of a box that look towards
# larger x and larger y, and a tall box hides what is right behind it. So a
# packet always arrives at a tall device from the front (moving towards
# smaller x or smaller y), and no cable that matters runs behind one.


# --- the hero: a question that gets its answer, and one that is stopped ------


def hero():
    width, depth, dur = 8.4, 6.6, 10
    srv, rtr, wall = server(0.6, 0.6), router(3.6, 0.5), firewall(5.5, 0.25)
    net = (7.0, 0.55, 1.2, 1.1, 0.24)
    sw, pcs = switch_x(3.2, 2.8), [pc(2.9, 5.3), pc(4.6, 5.3), pc(6.3, 5.3)]
    r, a, s = centre(rtr), centre(sw), centre(srv)
    bus = 4.15

    cables = [
        [centre(net), centre(wall), r],
        [r, a],
        [r, s],
        [(centre(pcs[0])[0], bus), (centre(pcs[2])[0], bus)],
        [a, (a[0], bus)],
    ] + [[(centre(p)[0], bus), centre(p)] for p in pcs]
    ask_from = centre(pcs[0])
    way = [ask_from, (ask_from[0], bus), (a[0], bus), a, r, s]
    halt = (wall[0] + wall[2] + 0.3, centre(net)[1])
    stopped = [centre(net), halt]

    out = board(width, depth)
    out += [polyline(on_board(c, 0.01), "iso-cable") for c in cables]
    out += [footprint(item) for item in [net, wall, rtr, sw, srv] + pcs]
    out.append(polyline(on_board(stopped), "iso-way stopped"))
    out.append(polyline(on_board(way), "iso-way"))

    # The question goes, waits for its answer, and the answer comes back
    out.append(packet(travel(on_board(way), [(0, 0), (0.36, 1), (0.48, 1), (0.84, 0), (1, 0)], dur)))
    # The one from outside goes as far as the wall
    out.append(
        packet(
            travel(on_board(stopped), [(0, 0), (0.14, 1), (1, 1)], dur)
            + animate("opacity", [(0, 1), (0.66, 1), (0.72, 0), (1, 0)], dur)
        )
    )

    out += stand(
        [
            (net, "iso-top", None),
            (wall, "iso-top", bricks),
            (rtr, "iso-top", lamps),
            (sw, "iso-top", ports_left(6)),
            (pcs[0], "iso-top end", screen),
            (pcs[1], "iso-top", screen),
            (pcs[2], "iso-top", screen),
            (srv, "iso-top end", slots(5)),
        ]
    )

    out.append(flash(srv, [0.36], dur))
    out.append(flash(pcs[0], [0.84], dur))

    cx, cy = iso(halt[0], halt[1], 0.78)
    out.append(cross(cx, cy, inner=animate("opacity", [(0, 0), (0.14, 0), (0.16, 1), (0.66, 1), (0.72, 0), (1, 0)], dur)))

    left, top, right, bottom = corners(width, depth, top=104, bottom=30)
    sx, sy = top_of(srv)
    nx, ny, nw = left + 14, top + 14, 258
    out.append(
        note(
            [("ping &#8594; reply", "iso-note-text strong"), ("there and back, hop by hop", "iso-note-text")],
            nx,
            ny,
            nw,
            leader=((nx + nw, ny + 40), (sx - 40, sy + 2)),
        )
    )
    hx, hy = iso(halt[0], halt[1], 0.4)
    nw = 232
    nx, ny = right - nw - 26, bottom - note_height(2) - 26
    out.append(
        note(
            [("ping &#8594; stopped here", "iso-note-text strong"), ("the answer says why", "iso-note-text")],
            nx,
            ny,
            nw,
            leader=((nx + nw * 0.5, ny), (hx + 2, hy + 12)),
        )
    )
    return sheet(
        out,
        width,
        depth,
        "A small network drawn in perspective: a server, a router, a firewall and the Internet in a row, "
        "a switch and three PCs in front. A packet goes from a PC to the server and back along a line marked "
        "in orange; a second packet, from the Internet, is stopped at the firewall.",
        still=4.2,
        top=104,
        bottom=30,
    )


# --- design: a device is put down, its cable is drawn, its numbers written ----


def design():
    width, depth, dur = 7.0, 6.4, 9
    rtr, srv, sw = router(3.0, 0.7), server(5.3, 0.8), switch_x(2.6, 2.9)
    old, new = pc(1.85, 5.2), pc(4.45, 5.2)
    r, a, bus = centre(rtr), centre(sw), 4.2
    cables = [
        [r, a],
        [r, centre(srv)],
        [a, (a[0], bus)],
        [(centre(old)[0], bus), (a[0], bus)],
        [(centre(old)[0], bus), centre(old)],
    ]
    fresh = on_board([(a[0], bus), (centre(new)[0], bus), centre(new)], 0.01)
    drawn = length(fresh)

    out = board(width, depth)
    out += [polyline(on_board(c, 0.01), "iso-cable") for c in cables]
    # The new cable is drawn from the switch to the new device
    out.append(
        polyline(
            fresh,
            "iso-cable drawn",
            inner=animate("stroke-dashoffset", [(0, drawn), (0.22, drawn), (0.4, 0), (0.94, 0), (0.98, drawn), (1, drawn)], dur),
            attrs=f' stroke-dasharray="{drawn:.1f}" stroke-dashoffset="{drawn:.1f}"',
        )
    )
    out += [footprint(item) for item in (rtr, srv, sw, old, new)]

    # The new device comes down on its place
    drop = (
        '<g opacity="0">'
        + animate("opacity", [(0, 0), (0.03, 0), (0.08, 1), (0.94, 1), (0.98, 0), (1, 0)], dur)
        + f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" repeatCount="indefinite" '
        'keyTimes="0;0.04;0.2;1" values="0 -86;0 -86;0 0;0 0" calcMode="spline" '
        'keySplines="0 0 1 1;0.3 0 0.2 1;0 0 1 1"/>'
    )
    out += stand(
        [
            (rtr, "iso-top", lamps),
            (srv, "iso-top", slots(5)),
            (sw, "iso-top", ports_left(6)),
            (old, "iso-top", screen),
            (new, "iso-top end", screen, drop, "</g>"),
        ]
    )

    mx, my = iso(r[0], r[1] + (a[1] - r[1]) * 0.47, 0.02)
    out.append(tag("VLAN 10", mx, my))
    fx, fy = iso((a[0] + centre(new)[0]) / 2 - 0.1, bus, 0.02)
    out.append(tag("1 Gbps", fx, fy - 4, inner=shown(0.4, 0.94, dur), start_hidden=True))

    left, top, right, bottom = corners(width, depth)
    px, py = top_of(new)
    nx, ny, nw = left + 22, top + 18, 232
    lines = [("PC-2", "iso-note-text strong")]
    for i, text in enumerate(["ip       192.168.10.12", "gateway  192.168.10.1", "vlan     10"]):
        at = 0.48 + 0.08 * i
        lines.append((text, "iso-note-text", [(0, 0), (at, 0), (at + 0.02, 1), (0.94, 1), (0.98, 0), (1, 0)]))
    out.append(
        '<g opacity="0">'
        + shown(0.42, 0.94, dur)
        + note(lines, nx, ny, nw, leader=((nx + nw * 0.5, ny + note_height(4)), (px - 6, py + 4)), dur=dur)
        + "</g>"
    )
    return sheet(
        out,
        width,
        depth,
        "A network being drawn: a router, a server, a switch and a PC are on the board. "
        "A second PC is put down, its cable to the switch is drawn, and its address, gateway and VLAN are written next to it.",
        still=7.4,
    )


# --- ask: the packet goes hop by hop, and each hop is written down -----------


def ask():
    width, depth, dur = 4.8, 8.6, 10
    col = 2.4
    start, sw, rtr = pc(col - 0.45, 7.1), switch_x(col - 1.0, 5.47), router(col - 0.6, 3.8)
    wall, srv = firewall_x(col - 0.85, 2.9), server(col - 0.5, 0.6)
    chain = [start, sw, rtr, wall, srv]
    way = on_board([centre(start), centre(srv)])
    y0, y1 = centre(start)[1], centre(srv)[1]
    reach = 0.6  # the moment the packet is at the server
    when = [reach * (y0 - centre(item)[1]) / (y0 - y1) for item in chain]

    out = board(width, depth)
    out.append(polyline(way, "iso-cable"))
    out += [footprint(item) for item in chain]
    out.append(polyline(way, "iso-way"))
    out.append(
        packet(
            travel(way, [(0, 0), (reach, 1), (1, 1)], dur)
            + animate("opacity", [(0, 1), (reach, 1), (reach + 0.03, 0), (1, 0)], dur)
        )
    )
    out += stand(
        [
            (start, "iso-top end", screen),
            (sw, "iso-top", ports_left(6)),
            (rtr, "iso-top", lamps),
            (wall, "iso-top", bricks_left),
            (srv, "iso-top end", slots(5)),
        ]
    )

    def appears(at):
        if at <= 0.02:
            return [(0, 1), (0.94, 1), (0.98, 0), (0.999, 0), (1, 1)]
        return [(0, 0), (at, 0), (at + 0.02, 1), (0.94, 1), (0.98, 0), (1, 0)]

    for i, item in enumerate(chain):
        level = 0.3
        bx, by = iso(0.62, centre(item)[1], level)
        ex, ey = iso(item[0] - 0.12, centre(item)[1], level)
        out.append(f'<line class="iso-stem" x1="{bx + 10.4:.1f}" y1="{by + 6:.1f}" x2="{ex:.1f}" y2="{ey:.1f}"/>')
        out.append(badge(bx, by, str(i + 1), appears(when[i]), dur))
        out.append(flash(item, [when[i]] if when[i] > 0.02 else [], dur))

    left, top, right, bottom = corners(width, depth)
    words = ["1  PC", "2  Switch", "3  Router    routed, port 2", "4  Firewall  allowed, rule 1", "5  Server    reached"]
    lines = [("trace Server from PC", "iso-note-text strong")]
    lines += [(text, "iso-note-text", appears(when[i])) for i, text in enumerate(words)]
    nw = 282
    out.append(note(lines, right - nw - 22, bottom - note_height(6) - 22, nw, dur=dur))
    return sheet(
        out,
        width,
        depth,
        "A packet goes from a PC to a server through a switch, a router and a firewall. "
        "Each device it passes gets its number, and a note lists the five hops with what each device did.",
        still=8.6,
    )


# --- present: the line is cut, and the packet goes the other way -------------


def present():
    width, depth, dur = 8.6, 4.8, 12
    row, back = 3.3, 1.1
    srv, b, a = server(0.5, row - 0.5), router(2.4, row - 0.6), router(5.6, row - 0.6)
    start, spare = pc(7.25, row - 0.4), router(4.0, back - 0.6)
    ca, cb, cs = centre(a), centre(b), centre(spare)
    gap = (4.15, 5.05)

    direct = [centre(start), centre(srv)]
    around = [centre(start), ca, (ca[0], back), cs, (cb[0], back), cb, centre(srv)]

    out = board(width, depth)
    out.append(polyline(on_board([centre(start), (gap[1], row)], 0.01), "iso-cable"))
    out.append(polyline(on_board([(gap[0], row), centre(srv)], 0.01), "iso-cable"))
    # The piece of the main line that gets cut
    out.append(
        polyline(
            on_board([(gap[0], row), (gap[1], row)], 0.01),
            "iso-cable",
            inner=animate("opacity", [(0, 1), (0.32, 1), (0.35, 0), (0.95, 0), (0.99, 1), (1, 1)], dur),
        )
    )
    out.append(polyline(on_board([ca, (ca[0], back), cs, (cb[0], back), cb], 0.01), "iso-cable"))
    out += [footprint(item) for item in (start, a, b, spare, srv)]

    out.append(polyline(on_board(direct), "iso-way", inner=animate("opacity", [(0, 1), (0.3, 1), (0.34, 0), (0.98, 0), (1, 1)], dur)))
    out.append(
        polyline(
            on_board(around),
            "iso-way",
            inner=animate("opacity", [(0, 0), (0.42, 0), (0.46, 1), (0.94, 1), (0.98, 0), (1, 0)], dur),
            attrs=' opacity="0"',
        )
    )
    out.append(
        packet(
            travel(on_board(direct), [(0, 0), (0.26, 1), (1, 1)], dur)
            + animate("opacity", [(0, 1), (0.26, 1), (0.29, 0), (1, 0)], dur)
        )
    )
    out.append(
        '<g opacity="0">'
        + animate("opacity", [(0, 0), (0.46, 0), (0.47, 1), (0.86, 1), (0.89, 0), (1, 0)], dur)
        + packet(travel(on_board(around), [(0, 0), (0.46, 0), (0.86, 1), (1, 1)], dur))
        + "</g>"
    )

    out += stand(
        [
            (start, "iso-top end", screen),
            (a, "iso-top", lamps),
            (b, "iso-top", lamps),
            (spare, "iso-top", lamps),
            (srv, "iso-top end", slots(5)),
        ]
    )

    out.append(flash(srv, [0.26, 0.86], dur))

    kx, ky = iso((gap[0] + gap[1]) / 2, row, 0.02)
    out.append(
        '<g opacity="0">'
        + animate("opacity", [(0, 0), (0.33, 0), (0.36, 1), (0.94, 1), (0.98, 0), (1, 0)], dur)
        + f'<circle class="iso-badge" cx="{kx:.1f}" cy="{ky:.1f}" r="11"/>'
        + cross(kx, ky, arm=4.5)
        + "</g>"
    )

    left, top, right, bottom = corners(width, depth)
    nw = 282
    nx, ny = left + 22, bottom - note_height(2) - 22
    lines = [
        ("main line cut", "iso-note-text strong"),
        ("still arrives, by the backup", "iso-note-text", [(0, 0), (0.86, 0), (0.88, 1), (0.94, 1), (0.98, 0), (1, 0)]),
    ]
    out.append(
        '<g opacity="0">'
        + shown(0.36, 0.94, dur)
        + note(lines, nx, ny, nw, leader=((nx + nw * 0.72, ny), (kx - 2, ky + 14)), dur=dur)
        + "</g>"
    )
    return sheet(
        out,
        width,
        depth,
        "Two sites joined by a main line, with a third router as a backup. A packet goes along the main line; "
        "the line is cut, and the next packet goes round through the backup router and still arrives.",
        still=10.6,
    )


# --- why: the network is on a whiteboard first, and the board keeps it alive --


def why():
    width, depth, dur = 7.4, 6.6, 11
    srv, rtr, sw = server(0.8, 2.3), router(3.3, 2.2), switch_x(2.9, 4.0)
    pcs = [pc(2.6, 5.5), pc(4.7, 5.5)]
    r, a, s = centre(rtr), centre(sw), centre(srv)
    bus = 5.15
    cables = [
        [r, a],
        [a, (a[0], bus)],
        [(centre(pcs[0])[0], bus), (centre(pcs[1])[0], bus)],
    ] + [[(centre(p)[0], bus), centre(p)] for p in pcs]
    new = [r, s]  # the cable that is drawn in the story
    way = [centre(pcs[0]), (centre(pcs[0])[0], bus), (a[0], bus), a, r, s]

    # The whiteboard stands along the back of the board, on two legs
    wx, wy, ww, wd, low, high = 1.4, 0.45, 4.6, 0.1, 0.55, 3.25
    face = wy + wd

    def wall(x, z):
        return iso(x, face + 0.01, z)

    def sketched(point):
        """Where a point of the plan is on the whiteboard: the network seen from above."""
        x, y = point
        k = 0.54  # one scale for both ways, so that a square stays a square
        return wall(wx + ww / 2 + (x - 3.2) * k, (low + high) / 2 - (y - 4.25) * k)

    out = board(width, depth)
    out += [polyline(on_board(c, 0.01), "iso-cable") for c in cables]
    on_floor = on_board(new, 0.01)
    drawn = length(on_floor)
    out.append(
        polyline(
            on_floor,
            "iso-cable drawn",
            inner=animate("stroke-dashoffset", [(0, drawn), (0.24, drawn), (0.38, 0), (0.94, 0), (0.98, drawn), (1, drawn)], dur),
            attrs=f' stroke-dasharray="{drawn:.1f}" stroke-dashoffset="{drawn:.1f}"',
        )
    )
    out += [footprint(item) for item in [srv, rtr, sw] + pcs]

    # The whiteboard: two legs, its frame, the surface one writes on
    for leg in (wx + 0.55, wx + ww - 0.63):
        out += box(leg, wy, 0.08, wd, low)
    out += box(wx, wy, ww, wd, high - low, z=low)
    m = 0.12
    out.append(polygon([wall(wx + m, low + m), wall(wx + ww - m, low + m), wall(wx + ww - m, high - m), wall(wx + m, high - m)], "iso-top"))

    # On it, the network as one draws it: a square for a device, a line for a cable
    out += [polyline([sketched(p) for p in c], "iso-sketch") for c in cables]
    on_wall = [sketched(p) for p in new]
    marked = length(on_wall)
    out.append(
        polyline(
            on_wall,
            "iso-cable drawn",
            inner=animate("stroke-dashoffset", [(0, marked), (0.05, marked), (0.2, 0), (0.94, 0), (0.98, marked), (1, marked)], dur),
            attrs=f' stroke-dasharray="{marked:.1f}" stroke-dashoffset="{marked:.1f}"',
        )
    )
    for item, asks in [(srv, True), (rtr, False), (sw, False), (pcs[0], True), (pcs[1], False)]:
        x, y, w, d, _ = item
        square = [sketched((x, y)), sketched((x + w, y)), sketched((x + w, y + d)), sketched((x, y + d))]
        out.append(polygon(square, "iso-sketch box end" if asks else "iso-sketch box"))

    # The question goes on the board, and on the whiteboard a dot follows the same way
    start, reach = 0.44, 0.8
    floor_way, wall_way = on_board(way), [sketched(p) for p in way]
    moments = [start + (reach - start) * f for f in fractions(floor_way)]
    out.append(
        packet(
            travel(floor_way, [(0, 0), (start, 0), (reach, 1), (1, 1)], dur)
            + animate("opacity", [(0, 0), (start - 0.02, 0), (start, 1), (reach, 1), (reach + 0.03, 0), (1, 0)], dur)
        )
    )

    out += stand(
        [
            (srv, "iso-top end", slots(5)),
            (rtr, "iso-top", lamps),
            (sw, "iso-top", ports_left(6)),
            (pcs[0], "iso-top end", screen),
            (pcs[1], "iso-top", screen),
        ]
    )
    out.append(flash(srv, [reach], dur))

    along = [(0, 0)] + list(zip(moments, fractions(wall_way)))[1:] + [(1, 1)]
    along[1:1] = [(start, 0)]
    out.append(
        '<g opacity="0">'
        + animate("opacity", [(0, 0), (start - 0.02, 0), (start, 1), (reach, 1), (reach + 0.03, 0), (1, 0)], dur)
        + '<circle class="iso-dot" r="4.5">'
        + travel(wall_way, along, dur)
        + "</circle></g>"
    )

    left, top, right, bottom = corners(width, depth, top=176, bottom=30)
    bx, by = wall(wx + 0.2, (low + high) / 2)
    nx, ny, nw = left + 14, top + 22, 250
    out.append(
        note(
            [("on the whiteboard", "iso-note-text strong"), ("where a network starts", "iso-note-text")],
            nx,
            ny,
            nw,
            leader=((nx + nw * 0.62, ny + note_height(2)), (bx - 4, by)),
        )
    )
    fx, fy = iso(centre(pcs[1])[0] + 0.75, centre(pcs[1])[1] + 0.2, 0.3)
    nw = 268
    nx, ny = right - nw - 20, bottom - note_height(2) - 22
    out.append(
        note(
            [("on the board", "iso-note-text strong"), ("the same network, answering", "iso-note-text")],
            nx,
            ny,
            nw,
            leader=((nx + nw * 0.3, ny), (fx, fy)),
        )
    )
    return sheet(
        out,
        width,
        depth,
        "A whiteboard stands behind a small network, and the same network is sketched on it as squares and lines. "
        "A line is drawn on the whiteboard, the matching cable appears between the router and the server, "
        "and a packet goes from a PC to the server while a dot follows the same way on the sketch.",
        still=8,
        top=176,
        bottom=30,
    )


DRAWINGS = {"hero": hero, "design": design, "ask": ask, "present": present, "why": why}


def main():
    made = {name: draw() for name, draw in DRAWINGS.items()}
    for page in PAGES:
        path = os.path.join(ROOT, page)
        text = open(path, encoding="utf-8", newline="").read()
        newline = "\r\n" if "\r\n" in text else "\n"
        text = text.replace("\r\n", "\n")
        used = []
        for name, svg in made.items():
            pattern = re.compile(
                r"(?P<indent>[ \t]*)<!-- drawing:" + name + r" -->\n.*?<!-- /drawing:" + name + r" -->", re.S
            )

            def put(match, svg=svg, name=name):
                pad = match.group("indent")
                body = "\n".join(pad + line for line in svg.splitlines())
                return f"{pad}<!-- drawing:{name} -->\n{body}\n{pad}<!-- /drawing:{name} -->"

            text, count = pattern.subn(put, text)
            if count:
                used.append(name)
        open(path, "w", encoding="utf-8", newline="").write(text.replace("\n", newline))
        print(page, "drawings:", ", ".join(used) or "none")


if __name__ == "__main__":
    sys.exit(main())

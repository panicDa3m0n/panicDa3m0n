#!/usr/bin/env python3
"""Build the animated SVG assets of the PanicDa3m0n GitHub profile (HoneyLabs identity).

    python3 tools/build_assets.py      ->  writes assets/*.svg

Standard library only. Animations use CSS keyframes and SMIL, both of which GitHub
renders inside <img>. No external fonts or resources: SVGs loaded as images cannot
fetch them, so every font falls back to a system stack.
"""
from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

# ---------------------------------------------------------------- identity
BG0, BG1, BG2 = "#0c0b10", "#17151d", "#1d1b23"
INK, INK2, INK3 = "#fff4d6", "#d9cfb8", "#9c937f"
AMBER, HONEY, GOLD = "#ffb020", "#ff8a1f", "#ffe08a"
SANS = ("'Bricolage Grotesque','Segoe UI Variable Display','Segoe UI',system-ui,"
        "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif")
MONO = ("'Geist Mono',ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,"
        "'Liberation Mono','DejaVu Sans Mono',monospace")
CW = 0.6  # advance of a monospace glyph, in em (text uses textLength to enforce it)
SQ3 = math.sqrt(3)

BASE_CSS = f"""
.s{{font-family:{SANS}}}
.m{{font-family:{MONO}}}
.lit{{opacity:0;animation:pulse 6s ease-in-out infinite}}
.cur{{animation:blink 1.05s step-end infinite}}
.comet{{animation:comet 5s linear infinite}}
.breathe{{animation:breathe 5s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:0}}50%{{opacity:1}}}}
@keyframes wave{{0%{{opacity:0}}4%{{opacity:1}}12%,100%{{opacity:0}}}}
@keyframes blink{{0%,50%{{opacity:1}}50.01%,100%{{opacity:0}}}}
@keyframes comet{{from{{stroke-dashoffset:0}}to{{stroke-dashoffset:-100}}}}
@keyframes breathe{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes spinr{{to{{transform:rotate(-360deg)}}}}
@keyframes d1{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(70px,26px)}}}}
@keyframes d2{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-80px,18px)}}}}
@keyframes d3{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(36px,-34px)}}}}
@keyframes scan{{from{{transform:translateX(-260px)}}to{{transform:translateX(1460px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def e(text: str) -> str:
    return escape(text)


def svg(w: int, h: int, title: str, body: str, defs: str = "", css: str = "", desc: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d">\n'
        f'<title id="t">{e(title)}</title>\n<desc id="d">{e(desc or title)}</desc>\n'
        f"<style>{BASE_CSS}{css}</style>\n<defs>{defs}</defs>\n{body}\n</svg>\n"
    )


def card(uid: str, w: float, h: float, rx: float = 28, x: float = 0, y: float = 0,
         c0: str = BG1, c1: str = BG0, stroke_op: float = .10):
    """Returns (defs, background, border, clip-id) for a rounded dark panel."""
    defs = (
        f'<linearGradient id="{uid}-bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/></linearGradient>'
        f'<clipPath id="{uid}-clip"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath>'
    )
    bg = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{uid}-bg)"/>'
    border = (f'<rect x="{x + .75}" y="{y + .75}" width="{w - 1.5}" height="{h - 1.5}" rx="{rx - .75}" '
              f'fill="none" stroke="{INK}" stroke-opacity="{stroke_op}" stroke-width="1.5"/>')
    return defs, bg, border, f"{uid}-clip"


def hex_pts(cx: float, cy: float, r: float) -> str:
    return " ".join(
        f"{cx + r * math.cos(math.radians(a)):.2f},{cy + r * math.sin(math.radians(a)):.2f}"
        for a in (-90, -30, 30, 90, 150, 210)
    )


def honeycomb(uid: str, w: float, h: float, r: float, fx: float, fy: float, fr: float,
              op: float = .09) -> tuple[str, str]:
    """Pointy-top honeycomb pattern, faded by a radial mask centred on (fx, fy)."""
    hw = SQ3 * r
    cells = [(0, 0), (hw, 0), (hw / 2, 1.5 * r), (0, 3 * r), (hw, 3 * r)]
    polys = "".join(f'<polygon points="{hex_pts(x, y, r * .92)}"/>' for x, y in cells)
    defs = (
        f'<pattern id="{uid}-hex" width="{hw:.3f}" height="{3 * r:.3f}" patternUnits="userSpaceOnUse">'
        f'<g fill="none" stroke="{INK}" stroke-opacity="{op}" stroke-width="1.2">{polys}</g></pattern>'
        f'<radialGradient id="{uid}-fade" cx="{fx}" cy="{fy}" r="{fr}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="{uid}-mask"><rect width="{w}" height="{h}" fill="url(#{uid}-fade)"/></mask>'
    )
    layer = f'<rect width="{w}" height="{h}" fill="url(#{uid}-hex)" mask="url(#{uid}-mask)"/>'
    return defs, layer


def lit_cells(r: float, cells: list[tuple[int, int, float, float, float]]) -> str:
    """Amber cells of the same lattice that pulse: (col, row, delay, duration, opacity)."""
    hw = SQ3 * r
    out = []
    for i, j, delay, dur, op in cells:
        cx, cy = i * hw + (j % 2) * hw / 2, j * 1.5 * r
        out.append(
            f'<polygon class="lit" points="{hex_pts(cx, cy, r * .92)}" fill="{AMBER}" fill-opacity="{op}" '
            f'style="animation-delay:-{delay}s;animation-duration:{dur}s"/>'
        )
    return "".join(out)


def blob(uid: str, cx: float, cy: float, r: float, color: str, op: float, anim: str, dur: float) -> tuple[str, str]:
    defs = (f'<radialGradient id="{uid}"><stop offset="0" stop-color="{color}" stop-opacity="{op}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
    el = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{uid})" '
          f'style="animation:{anim} {dur}s ease-in-out infinite"/>')
    return defs, el


def glyph(x: float, y: float, size: float, sw: float = 9, bar_cls: str = "") -> str:
    """The HoneyLabs mark <—> in a size x size box."""
    s = size / 100
    cls = f' class="{bar_cls}"' if bar_cls else ""
    return (
        f'<g transform="translate({x} {y}) scale({s:.4f})" fill="none" stroke-linecap="round" stroke-linejoin="round">'
        f'<polyline points="30,12 8,50 30,88" stroke="{INK}" stroke-width="{sw}"/>'
        f'<polyline points="70,12 92,50 70,88" stroke="{INK}" stroke-width="{sw}"/>'
        f'<line x1="32" y1="50" x2="68" y2="50" stroke="{AMBER}" stroke-width="{sw + 2}"{cls}/></g>'
    )


def hex_badge(cx: float, cy: float, r: float, delay: float = 0) -> str:
    """Hexagon outline with an amber light running around it."""
    pts = hex_pts(cx, cy, r)
    return (
        f'<polygon points="{pts}" fill="{BG0}" fill-opacity=".6" stroke="{INK}" stroke-opacity=".16" stroke-width="1.5"/>'
        f'<polygon points="{pts}" pathLength="100" fill="none" stroke="{AMBER}" stroke-width="2.5" '
        f'stroke-linecap="round" stroke-dasharray="14 86" class="comet" style="animation-delay:-{delay}s"/>'
    )


def mono_text(x: float, y: float, text: str, fs: float, fill: str, extra: str = "", ls: float = 0) -> str:
    """Monospace text whose width is pinned to len * CW * fs, so layout never depends on the font."""
    width = len(text) * (CW * fs + ls)
    ls_attr = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text class="m" x="{x}" y="{y}" font-size="{fs}" fill="{fill}"{ls_attr} '
            f'textLength="{width:.1f}" lengthAdjust="spacingAndGlyphs"{extra}>{e(text)}</text>')


def chip(x: float, y: float, text: str, fs: float = 14, fill: str = INK2, stroke: str = INK,
         stroke_op: float = .16, bg: str = BG0, bg_op: float = .55, pad: float = 14, h: float = 32,
         ls: float = 0, cls: str = "", style: str = "") -> tuple[str, float]:
    tw = len(text) * (CW * fs + ls)
    w = tw + 2 * pad
    c = f' class="{cls}"' if cls else ""
    st = f' style="{style}"' if style else ""
    el = (
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{bg}" fill-opacity="{bg_op}" '
        f'stroke="{stroke}" stroke-opacity="{stroke_op}" stroke-width="1.2"{c}{st}/>'
        + mono_text(x + pad, y + h / 2 + fs * .36, text, fs, fill, ls=ls)
    )
    return el, w


def discrete(attr: str, timeline: list[tuple[float, float]], T: float) -> str:
    """SMIL discrete animation over one cycle of T seconds. timeline: [(t, value)], t from 0."""
    merged: dict[float, float] = {}
    for t, v in timeline:
        merged[round(t / T, 4)] = v
    keys = sorted(merged)
    assert keys[0] == 0.0, "timeline must start at t=0"
    kt = ";".join(f"{k:.4f}" for k in keys)
    vals = ";".join(f"{merged[k]:.2f}" for k in keys)
    return (f'<animate attributeName="{attr}" dur="{T:.2f}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{kt}" values="{vals}"/>')


def write(name: str, content: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(content, encoding="utf-8")
    print(f"  {name:<24} {len(content.encode()) / 1024:5.1f} KB")


# ---------------------------------------------------------------- hero
def hero() -> str:
    W, H = 1200, 460
    defs, bg, border, clip = card("h", W, H, rx=30)
    ex, ey = 985, 228  # emblem centre
    hc_defs, hc = honeycomb("h", W, H, 26, ex, ey, 640, op=.10)
    defs += hc_defs
    blobs = ""
    for uid, cx, cy, r, col, op, anim, dur in (
        ("hb1", 930, 120, 330, AMBER, .30, "d1", 19),
        ("hb2", 1120, 400, 280, HONEY, .22, "d2", 23),
        ("hb3", 260, 470, 300, GOLD, .10, "d3", 27),
    ):
        d, el = blob(uid, cx, cy, r, col, op, anim, dur)
        defs += d
        blobs += el
    lit = lit_cells(26, [
        (21, 2, 0, 7, .35), (24, 4, 2.2, 6, .3), (27, 3, 4.1, 8, .28), (22, 9, 1.3, 6.5, .3),
        (26, 11, 3.3, 7.5, .25), (19, 6, 5.0, 9, .2), (28, 7, .8, 6, .3), (17, 12, 2.7, 8, .15),
        (25, 0, 3.8, 7, .25), (23, 13, 4.6, 6.5, .2), (14, 3, 6.0, 10, .12),
    ])

    # --- emblem: rings, orbiting sparks, hexagon with running light, the mark
    emblem = (
        f'<circle cx="{ex}" cy="{ey}" r="150" fill="url(#h-glow)" class="breathe"/>'
        f'<g style="transform-origin:{ex}px {ey}px;animation:spin 48s linear infinite">'
        f'<circle cx="{ex}" cy="{ey}" r="172" fill="none" stroke="{AMBER}" stroke-opacity=".28" stroke-width="1.5" stroke-dasharray="2 9"/>'
        f'<circle cx="{ex + 172}" cy="{ey}" r="4.5" fill="{AMBER}"/>'
        f'<circle cx="{ex - 172}" cy="{ey}" r="3" fill="{GOLD}" fill-opacity=".8"/></g>'
        f'<g style="transform-origin:{ex}px {ey}px;animation:spinr 30s linear infinite">'
        f'<circle cx="{ex}" cy="{ey}" r="132" fill="none" stroke="{INK}" stroke-opacity=".14" stroke-width="1.2" stroke-dasharray="46 22"/>'
        f'<circle cx="{ex}" cy="{ey - 132}" r="3.5" fill="{INK}" fill-opacity=".9"/></g>'
        + hex_badge(ex, ey, 98)
        + f'<polygon points="{hex_pts(ex, ey, 98)}" pathLength="100" fill="none" stroke="{GOLD}" stroke-width="2" '
          f'stroke-linecap="round" stroke-dasharray="6 94" class="comet" style="animation-delay:-2.5s;animation-duration:7s"/>'
        + glyph(ex - 58, ey - 58, 116, sw=10, bar_cls="breathe")
    )
    defs += (f'<radialGradient id="h-glow"><stop offset="0" stop-color="{AMBER}" stop-opacity=".34"/>'
             f'<stop offset=".55" stop-color="{HONEY}" stop-opacity=".10"/><stop offset="1" stop-color="{HONEY}" stop-opacity="0"/></radialGradient>')

    # --- name with a moving sheen on "Da3m0n"
    defs += (
        f'<linearGradient id="h-sheen" gradientUnits="userSpaceOnUse" x1="-420" y1="0" x2="-60" y2="0">'
        f'<stop offset="0" stop-color="{AMBER}"/><stop offset=".46" stop-color="{AMBER}"/>'
        f'<stop offset=".5" stop-color="#fff1c4"/><stop offset=".54" stop-color="{AMBER}"/>'
        f'<stop offset="1" stop-color="{AMBER}"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;1500 0;1500 0" '
        f'keyTimes="0;.55;1" dur="7s" repeatCount="indefinite"/></linearGradient>'
    )
    head = (
        glyph(78, 56, 40, sw=10)
        + mono_text(134, 83, "HONEYLABS / INDEPENDENT AI LAB", 15, AMBER, ls=2.4)
        + f'<text class="s" x="76" y="214" font-size="100" font-weight="800" letter-spacing="-3" fill="{INK}">'
          f'Panic<tspan fill="url(#h-sheen)">Da3m0n</tspan></text>'
        + f'<text class="s" x="80" y="266" font-size="27" font-weight="500" fill="{INK2}">'
          f'Reverse engineer <tspan fill="{AMBER}">·</tspan> Cracker <tspan fill="{AMBER}">·</tspan> AI researcher</text>'
    )

    # --- rotating typed phrases
    phrases = [
        "building digital living beings",
        "opening closed systems, binary by binary",
        "porting console games to the open PC",
        "hunting bugs for Sony, Microsoft & Samsung",
        "designing agent-first operating systems",
    ]
    fs, ty = 24, 334
    cw = fs * CW
    x0 = 80
    px = x0 + 2 * cw
    t, type_dt, erase_dt, hold, gap = .5, .055, .022, 2.3, .35
    cursor_tl: list[tuple[float, float]] = [(0, px)]
    timelines: list[tuple[str, list[tuple[float, float]]]] = []
    for p in phrases:
        n = len(p)
        tl: list[tuple[float, float]] = [(0, 0)]
        for k in range(1, n + 1):
            tl.append((t + k * type_dt, k * cw))
            cursor_tl.append((t + k * type_dt, px + k * cw))
        te = t + n * type_dt + hold
        for k in range(n - 1, -1, -1):
            tt = te + (n - k) * erase_dt
            tl.append((tt, k * cw))
            cursor_tl.append((tt, px + k * cw))
        t = te + n * erase_dt + gap
        timelines.append((p, tl))
    T = t
    clips, texts = "", ""
    for idx, (p, tl) in enumerate(timelines):
        clips += (f'<clipPath id="tp{idx}"><rect x="{px:.1f}" y="{ty - fs}" height="{fs * 1.4:.1f}" width="0">'
                  + discrete("width", tl, T) + "</rect></clipPath>")
        texts += f'<g clip-path="url(#tp{idx})">' + mono_text(px, ty, p, fs, INK) + "</g>"
    defs += clips
    typing = (
        mono_text(x0, ty, ">", fs, AMBER)
        + texts
        + f'<rect class="cur" x="{px:.1f}" y="{ty - fs * .82:.1f}" width="{cw * .62:.1f}" height="{fs * 1.02:.1f}" fill="{AMBER}">'
        + discrete("x", cursor_tl, T) + "</rect>"
    )

    # --- status chips
    c1, w1 = chip(80, 380, "OPEN TO COLLABORATION", fs=13, ls=1.6, fill=INK, pad=34, h=34,
                  stroke=AMBER, stroke_op=.45, bg=AMBER, bg_op=.08)
    dot = (f'<circle cx="98" cy="397" r="5" fill="{AMBER}"/>'
           f'<circle cx="98" cy="397" r="5" fill="none" stroke="{AMBER}" stroke-width="2">'
           f'<animate attributeName="r" values="5;13" dur="1.8s" repeatCount="indefinite"/>'
           f'<animate attributeName="stroke-opacity" values=".8;0" dur="1.8s" repeatCount="indefinite"/></circle>')
    c2, w2 = chip(80 + w1 + 12, 380, "OPEN SOURCE, ALWAYS", fs=13, ls=1.6, fill=INK2, pad=18, h=34)
    c3, _ = chip(80 + w1 + w2 + 24, 380, "BUG BOUNTY HUNTER", fs=13, ls=1.6, fill=INK2, pad=18, h=34)

    body = (
        bg + f'<g clip-path="url(#{clip})">{blobs}{hc}{lit}{emblem}</g>'
        + head + typing + c1 + dot + c2 + c3 + border
    )
    return svg(W, H, "PanicDa3m0n · HoneyLabs",
               body, defs,
               desc="PanicDa3m0n: reverse engineer, cracker and AI researcher. HoneyLabs, independent AI lab. "
                    "Building digital living beings, opening closed systems, porting console games to the open PC, "
                    "hunting bugs for Sony, Microsoft and Samsung, designing agent-first operating systems.")


# ---------------------------------------------------------------- terminal
def whoami() -> str:
    W, H = 1200, 452
    defs, bg, border, clip = card("w", W, H, rx=22, c0="#141218", c1=BG0)
    fs, lh, x0, y0 = 20, 36, 48, 110
    cw = fs * CW
    prompt_w = len("~/lab $ ") * cw
    script: list[tuple[str, object]] = [
        ("p", "whoami"),
        ("o", [("PanicDa3m0n", AMBER, True), (" — reverse engineer · cracker · AI researcher · bug hunter", INK2, False)]),
        ("p", "cat manifesto.md"),
        ("o", [("> ", AMBER, False), ("Every closed system is an open question.", INK, False)]),
        ("o", [("> ", AMBER, False), ("If it can be understood, it should be free: code, hardware, minds.", INK, False)]),
        ("o", [("> ", AMBER, False), ("Next: digital individuals that live, remember and grow.", INK, False)]),
        ("p", "ls ./focus"),
        ("o", [("digital-individuals/", AMBER, False), ("   ", INK, False), ("agentic-os/", AMBER, False),
               ("   ", INK, False), ("reverse-engineering/", AMBER, False), ("   ", INK, False),
               ("bug-bounty/", AMBER, False)]),
        ("p", ""),
    ]
    events = []  # (line index, start time)
    t = .6
    cursor: list[tuple[float, float, float]] = [(0, x0 + prompt_w, y0)]
    lines_out = []
    for i, (kind, payload) in enumerate(script):
        y = y0 + i * lh
        if kind == "p":
            t += .55 if i else 0
            start = t
            cx0 = x0 + prompt_w
            cursor.append((start, cx0, y))
            cmd = str(payload)
            tl = [(0, 0)]
            for k in range(1, len(cmd) + 1):
                tt = start + .35 + k * .075
                tl.append((tt, k * cw))
                cursor.append((tt, cx0 + k * cw, y))
            t = start + .35 + len(cmd) * .075 + .4
            lines_out.append(("p", i, y, start, cmd, tl))
        else:
            start = t
            t += .22
            lines_out.append(("o", i, y, start, payload, None))
    T = round(t + 7.5, 2)
    end = T * .975
    body_lines = ""
    for kind, i, y, start, payload, tl in lines_out:
        vis = discrete("opacity", [(0, 0), (start, 1), (end, 0)], T)
        if kind == "p":
            cmd = str(payload)
            clip_el = (f'<clipPath id="wc{i}"><rect x="{x0 + prompt_w:.1f}" y="{y - fs}" height="{fs * 1.5}" width="0">'
                       + discrete("width", tl, T) + "</rect></clipPath>")
            defs += clip_el
            cmd_el = (f'<g clip-path="url(#wc{i})">' + mono_text(x0 + prompt_w, y, cmd, fs, INK) + "</g>") if cmd else ""
            body_lines += (
                f'<g opacity="0">{vis}'
                + mono_text(x0, y, "~/lab", fs, AMBER) + mono_text(x0 + 6 * cw, y, "$", fs, INK3)
                + "</g>" + cmd_el
            )
        else:
            spans = "".join(
                f'<tspan fill="{c}"{" font-weight=" + chr(34) + "700" + chr(34) if b else ""}>{e(txt)}</tspan>'
                for txt, c, b in payload  # type: ignore[union-attr]
            )
            n = sum(len(txt) for txt, _, _ in payload)  # type: ignore[union-attr]
            body_lines += (
                f'<g opacity="0">{vis}<text class="m" x="{x0}" y="{y}" font-size="{fs}" '
                f'textLength="{n * cw:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{spans}</text></g>'
            )
    ctl_x = [(tt, cx) for tt, cx, _ in cursor] + [(end, x0 + prompt_w)]
    ctl_y = [(tt, cy) for tt, _, cy in cursor] + [(end, y0)]
    cur = (f'<rect class="cur" x="{x0 + prompt_w}" y="{y0 - fs * .82:.1f}" width="{cw * .62:.1f}" '
           f'height="{fs * 1.05:.1f}" fill="{AMBER}">'
           + discrete("x", ctl_x, T)
           + discrete("y", [(tt, cy - fs * .82) for tt, cy in ctl_y], T) + "</rect>")
    chrome = (
        f'<rect width="{W}" height="54" fill="{INK}" fill-opacity=".035"/>'
        f'<line x1="0" y1="54" x2="{W}" y2="54" stroke="{INK}" stroke-opacity=".08"/>'
        f'<circle cx="34" cy="27" r="7" fill="{AMBER}"/><circle cx="58" cy="27" r="7" fill="{HONEY}" fill-opacity=".75"/>'
        f'<circle cx="82" cy="27" r="7" fill="{INK3}" fill-opacity=".5"/>'
        + mono_text(W / 2 - len("panicda3m0n@honeylabs: ~/lab") * 14 * CW / 2, 32,
                    "panicda3m0n@honeylabs: ~/lab", 14, INK3)
    )
    defs += f'<linearGradient id="w-scan" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/><stop offset=".5" stop-color="{AMBER}" stop-opacity=".05"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>'
    scan = f'<rect x="0" y="54" width="260" height="{H - 54}" fill="url(#w-scan)" style="animation:scan 9s linear infinite"/>'
    body = bg + f'<g clip-path="url(#{clip})">{chrome}{scan}</g>' + body_lines + cur + border
    return svg(W, H, "whoami: PanicDa3m0n", body, defs,
               desc="Terminal. whoami: PanicDa3m0n, reverse engineer, cracker, AI researcher, bug hunter. "
                    "Manifesto: every closed system is an open question. If it can be understood, it should be free: "
                    "code, hardware, minds. Next: digital individuals that live, remember and grow. "
                    "Focus: digital individuals, agentic OS, reverse engineering, bug bounty.")


# ---------------------------------------------------------------- icons
def icon(kind: str, cx: float, cy: float) -> str:
    a = f'fill="none" stroke="{AMBER}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "mind":
        return (f'<circle cx="{cx}" cy="{cy}" r="6" fill="{AMBER}"/>'
                f'<g style="transform-origin:{cx}px {cy}px;animation:spin 6s linear infinite">'
                f'<ellipse cx="{cx}" cy="{cy}" rx="19" ry="8" {a}/>'
                f'<circle cx="{cx + 19}" cy="{cy}" r="3" fill="{GOLD}"/></g>'
                f'<g style="transform-origin:{cx}px {cy}px;animation:spinr 9s linear infinite">'
                f'<ellipse cx="{cx}" cy="{cy}" rx="8" ry="19" {a} stroke-opacity=".55"/></g>')
    if kind == "os":
        return (f'<rect x="{cx - 17}" y="{cy - 14}" width="34" height="28" rx="5" {a}/>'
                f'<line x1="{cx - 17}" y1="{cy - 6}" x2="{cx + 17}" y2="{cy - 6}" {a}/>'
                f'<rect x="{cx - 10}" y="{cy - 1}" width="8" height="8" rx="1.5" fill="{AMBER}" class="breathe"/>'
                f'<rect x="{cx + 2}" y="{cy - 1}" width="8" height="8" rx="1.5" fill="{GOLD}" fill-opacity=".7" '
                f'class="breathe" style="animation-delay:-2.5s"/>')
    if kind == "re":
        return (f'<polyline points="{cx - 8},{cy - 13} {cx - 18},{cy} {cx - 8},{cy + 13}" {a}/>'
                f'<polyline points="{cx + 8},{cy - 13} {cx + 18},{cy} {cx + 8},{cy + 13}" {a}/>'
                f'<line x1="{cx + 4}" y1="{cy - 15}" x2="{cx - 4}" y2="{cy + 15}" {a} class="breathe"/>')
    if kind == "bug":
        return (f'<circle cx="{cx}" cy="{cy}" r="14" {a}/>'
                f'<g style="transform-origin:{cx}px {cy}px;animation:spin 8s linear infinite">'
                f'<line x1="{cx}" y1="{cy - 22}" x2="{cx}" y2="{cy - 16}" {a}/><line x1="{cx}" y1="{cy + 16}" x2="{cx}" y2="{cy + 22}" {a}/>'
                f'<line x1="{cx - 22}" y1="{cy}" x2="{cx - 16}" y2="{cy}" {a}/><line x1="{cx + 16}" y1="{cy}" x2="{cx + 22}" y2="{cy}" {a}/></g>'
                f'<circle cx="{cx}" cy="{cy}" r="4" fill="{AMBER}" class="breathe"/>')
    raise ValueError(kind)


# ---------------------------------------------------------------- pillars
def pillars() -> str:
    W, H = 1200, 836
    defs, bg, border, clip = card("p", W, H, rx=30)
    hc_defs, hc = honeycomb("p", W, H, 24, 1100, 40, 520, op=.08)
    defs += hc_defs
    d, b1 = blob("pb1", 1050, 40, 380, AMBER, .16, "d2", 24)
    defs += d
    head = (mono_text(48, 66, "WHAT I DO", 15, AMBER, ls=3)
            + f'<text class="s" x="46" y="118" font-size="44" font-weight="800" letter-spacing="-1" fill="{INK}">'
              f'Open systems. <tspan fill="{AMBER}">Living minds.</tspan></text>')
    tiles = [
        ("mind", "Digital individuals",
         ["Studying how humans remember, sleep, feel and",
          "pay attention, to grow persistent AI minds that",
          "can honestly call themselves digital living beings."],
         "LLM AGENTS · COGNITIVE ARCHITECTURES · LOCAL AI"),
        ("os", "New-concept operating systems",
         ["Agent-first OS design: machines that are run,",
          "maintained and evolved by AI agents. Agentic IDEs",
          "and multi-agent workflows are my daily driver."],
         "AGENT-FIRST OS · AGENTIC IDES · MULTI-AGENT"),
        ("re", "Reverse engineering & cracking",
         ["Binaries, firmware, consoles: static recompilation,",
          "native ports and closed formats cracked open,",
          "because locked knowledge is lost knowledge."],
         "RE · CRACKING · NATIVE PORTS · VULKAN"),
        ("bug", "Bug bounty",
         ["Active hunter in the bug bounty programs of Sony,",
          "Microsoft, Samsung and more. Responsible",
          "disclosure: break it, report it, make it safer."],
         "SECURITY RESEARCH · RESPONSIBLE DISCLOSURE"),
    ]
    tw, th, gap, ox, oy = 556, 316, 24, 32, 156
    out = ""
    for n, (kind, title, lines, tags) in enumerate(tiles):
        tx = ox + (n % 2) * (tw + gap)
        ty = oy + (n // 2) * (th + gap)
        td, tbg, tborder, _ = card(f"pt{n}", tw, th, rx=22, x=tx, y=ty, c0="#1b1920", c1="#111015", stroke_op=.09)
        defs += td
        text = "".join(
            f'<text class="s" x="{tx + 40}" y="{ty + 196 + k * 28}" font-size="19" fill="{INK2}">{e(line)}</text>'
            for k, line in enumerate(lines)
        )
        out += (
            tbg + tborder
            + hex_badge(tx + 76, ty + 76, 38, delay=n * 1.25)
            + icon(kind, tx + 76, ty + 76)
            + mono_text(tx + tw - 36 - 2 * 15 * CW, ty + 62, f"0{n + 1}", 15, INK3)
            + f'<text class="s" x="{tx + 40}" y="{ty + 158}" font-size="29" font-weight="750" fill="{INK}">{e(title)}</text>'
            + text
            + mono_text(tx + 40, ty + 284, tags, 12.5, AMBER, ls=1.2)
        )
    body = bg + f'<g clip-path="url(#{clip})">{b1}{hc}</g>' + head + out + border
    return svg(W, H, "What I do: open systems, living minds", body, defs,
               desc="Four fronts. Digital individuals: studying human memory, sleep, affect and attention to grow "
                    "persistent AI minds. New-concept operating systems: agent-first OS design, agentic IDEs, "
                    "multi-agent workflows. Reverse engineering and cracking: binaries, firmware, consoles, static "
                    "recompilation, native ports. Bug bounty: Sony, Microsoft, Samsung and more, responsible disclosure.")


# ---------------------------------------------------------------- HoneyLabs lab banner
def lab() -> str:
    W, H = 1200, 436
    defs, bg, border, clip = card("l", W, H, rx=30)
    hc_defs, hc = honeycomb("l", W, H, 22, 1060, 90, 560, op=.10)
    defs += hc_defs
    blobs = ""
    for uid, cx, cy, r, col, op, anim, dur in (
        ("lb1", 1040, 60, 360, AMBER, .22, "d2", 21),
        ("lb2", 120, 420, 300, HONEY, .12, "d1", 25),
    ):
        d, el = blob(uid, cx, cy, r, col, op, anim, dur)
        defs += d
        blobs += el
    lit = lit_cells(22, [(40, 1, 0, 6, .3), (43, 3, 2, 7, .25), (37, 2, 3.5, 8, .2), (45, 0, 1.2, 6.5, .3),
                         (41, 5, 4.4, 7, .2), (34, 0, 5.3, 9, .14)])
    big = f'<g opacity=".07">{glyph(890, 60, 250, sw=8)}</g>'
    head = (
        glyph(48, 46, 52, sw=10)
        + f'<text class="s" x="116" y="90" font-size="50" font-weight="800" letter-spacing="-1.5" fill="{INK}">'
          f'Honey<tspan fill="{AMBER}">Labs</tspan></text>'
        + mono_text(1152 - 22 * 13 * CW - 22 * 1.8, 80, "MY INDEPENDENT R&D LAB", 13, INK3, ls=1.8)
        + f'<text class="s" x="46" y="168" font-size="42" font-weight="800" letter-spacing="-1" fill="{INK}">'
          f'We create digital living beings.</text>'
        + f'<text class="s" x="48" y="208" font-size="20" fill="{INK2}">'
          f'Local, persistent AI minds that remember, reason and sleep. '
          f'<tspan fill="{AMBER}" font-weight="600">HLLM</tspan> is the flagship.</text>'
    )
    # metric tiles
    tiles = ""
    tw, th, ty = 352, 150, 250
    bar_w = tw - 48
    specs = [
        ("38", " words/s", "HLLM-1 27B on a single RTX 4070 Ti SUPER", "v0.45: 24  →  v0.48: 38  ·  target 60",
         ("grow", 24 / 60, 38 / 60)),
        ("7", " s", "to the first word over a 256k-token context", "was ~3 min  →  now 7 s",
         ("shrink", 1.0, 7 / 180)),
        ("100%", " local", "a mind that lives in your home, not a cloud", "private by design: your data stays home",
         ("flow", 1.0, 1.0)),
    ]
    for n, (big_v, unit, label, cap, (mode, a, b)) in enumerate(specs):
        x = 48 + n * (tw + 24)
        td, tbg, tborder, _ = card(f"lt{n}", tw, th, rx=20, x=x, y=ty, c0="#1c1a21", c1="#121116", stroke_op=.10)
        defs += td
        bx, by = x + 24, ty + 106
        track = f'<rect x="{bx}" y="{by}" width="{bar_w}" height="6" rx="3" fill="{INK}" fill-opacity=".08"/>'
        if mode == "flow":
            defs += (f'<linearGradient id="lt-flow" gradientUnits="userSpaceOnUse" x1="{bx}" y1="0" x2="{bx + bar_w}" y2="0" spreadMethod="repeat">'
                     f'<stop offset="0" stop-color="{AMBER}"/><stop offset=".5" stop-color="{GOLD}"/><stop offset="1" stop-color="{AMBER}"/>'
                     f'<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="{bar_w} 0" dur="3s" repeatCount="indefinite"/>'
                     f'</linearGradient>')
            fill = f'<rect x="{bx}" y="{by}" width="{bar_w}" height="6" rx="3" fill="url(#lt-flow)"/>'
        else:
            wa, wb = bar_w * a, bar_w * b
            fill = (f'<rect x="{bx}" y="{by}" width="{wa:.1f}" height="6" rx="3" fill="{AMBER}">'
                    f'<animate attributeName="width" values="{wa:.1f};{wa:.1f};{wb:.1f};{wb:.1f}" keyTimes="0;.25;.55;1" '
                    f'dur="6s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.3 .8 .2 1;0 0 1 1"/></rect>')
            if mode == "grow":
                fill += f'<line x1="{bx + bar_w - 1}" y1="{by - 5}" x2="{bx + bar_w - 1}" y2="{by + 11}" stroke="{GOLD}" stroke-width="2"/>'
        tiles += (
            tbg + tborder
            + f'<text class="s" x="{x + 24}" y="{ty + 58}" font-size="44" font-weight="800" letter-spacing="-1" fill="{AMBER}">'
              f'{e(big_v)}<tspan font-size="22" font-weight="600" fill="{INK}" letter-spacing="0">{e(unit)}</tspan></text>'
            + f'<text class="s" x="{x + 24}" y="{ty + 86}" font-size="15.5" fill="{INK2}">{e(label)}</text>'
            + track + fill
            + mono_text(x + 24, ty + 134, cap, 11.5, INK3)
        )
    body = bg + f'<g clip-path="url(#{clip})">{blobs}{hc}{lit}{big}</g>' + head + tiles + border
    return svg(W, H, "HoneyLabs: we create digital living beings", body, defs,
               desc="HoneyLabs, my independent R&D lab. Local, persistent AI minds that remember, reason and sleep; "
                    "HLLM is the flagship. HLLM-1 27B runs at 38 words per second on a single RTX 4070 Ti SUPER "
                    "(up from 24, target 60). First word over a 256k-token context in 7 seconds, down from about "
                    "3 minutes. 100% local: a mind that lives in your home.")


# ---------------------------------------------------------------- section header
def header(name: str, kicker: str, title: str, accent: str = "") -> None:
    W, H = 1200, 132
    defs, bg, border, clip = card(name, W, H, rx=24)
    hc_defs, hc = honeycomb(name, W, H, 20, 1150, 66, 380, op=.10)
    defs += hc_defs
    defs += (f'<linearGradient id="{name}-ln" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="{AMBER}"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>')
    title_svg = e(title) + (f' <tspan fill="{AMBER}">{e(accent)}</tspan>' if accent else "")
    body = (
        bg + f'<g clip-path="url(#{clip})">{hc}'
        f'<rect x="0" y="{H - 2}" width="260" height="2" fill="url(#{name}-ln)" style="animation:scan 6s linear infinite"/></g>'
        + mono_text(48, 50, kicker, 14, AMBER, ls=3)
        + f'<text class="s" x="46" y="98" font-size="38" font-weight="800" letter-spacing="-1" fill="{INK}">{title_svg}</text>'
        + border
    )
    write(f"{name}.svg", svg(W, H, f"{title} {accent}".strip(), body, defs))


# ---------------------------------------------------------------- project cards
def project_card(name: str, label: str, badge: str, title: str, lines: list[str], tags: list[str], cta: str,
                 side: str = "left") -> None:
    """A 600x312 card on a 612-wide canvas: the extra 12px sit on the inner side, so two cards
    placed at width=50% with no whitespace line up with the full-width banners and keep a gap."""
    W, H = 600, 312
    ox = 0 if side == "left" else 12
    defs, bg, border, clip = card(name, W, H, rx=24)
    hc_defs, hc = honeycomb(name, W, H, 18, 560, 20, 260, op=.11)
    defs += hc_defs
    d, glow = blob(f"{name}-g", 560, 10, 230, AMBER, .17, "d2", 18)
    defs += d
    bfs = 14
    bw = len(badge) * bfs * CW + 28
    badge_el, _ = chip(W - 32 - bw, 30, badge, fs=bfs, fill=AMBER, stroke=AMBER, stroke_op=.4, bg=AMBER, bg_op=.08, pad=14, h=32)
    text = "".join(
        f'<text class="s" x="36" y="{158 + k * 28}" font-size="18" fill="{INK2}">{e(line)}</text>'
        for k, line in enumerate(lines)
    )
    x = 36.0
    tag_el = ""
    for k, tg in enumerate(tags):
        el, w = chip(x, 248, tg, fs=12.5, fill=INK2, pad=12, h=30, cls="", style="")
        tag_el += el
        x += w + 8
    cta_w = len(cta) * 13 * CW
    body = (
        bg + f'<g clip-path="url(#{clip})">{glow}{hc}</g>'
        + mono_text(36, 52, label, 12.5, AMBER, ls=2)
        + badge_el
        + f'<text class="s" x="34" y="114" font-size="42" font-weight="800" letter-spacing="-1.2" fill="{INK}">{e(title)}</text>'
        + text + tag_el
        + mono_text(W - 32 - cta_w, 268, cta, 13, INK3)
        + f'<polygon points="{hex_pts(W - 32 - cta_w - 14, 263, 6)}" fill="{AMBER}" class="breathe"/>'
        + border
    )
    body = f'<g transform="translate({ox} 0)">{body}</g>'
    write(f"{name}.svg", svg(W + 12, H, f"{title}: {label.title()}", body, defs, desc=f"{title}. " + " ".join(lines)))


# ---------------------------------------------------------------- bug bounty strip
def bounty() -> str:
    W, H = 1200, 236
    defs, bg, border, clip = card("b", W, H, rx=28)
    hc_defs, hc = honeycomb("b", W, H, 20, 120, 118, 300, op=.10)
    defs += hc_defs
    defs += (f'<linearGradient id="b-beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/>'
             f'<stop offset=".75" stop-color="{AMBER}" stop-opacity=".05"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".16"/></linearGradient>')
    beam = (f'<g style="animation:scan 7s cubic-bezier(.5,0,.5,1) infinite">'
            f'<rect x="0" y="0" width="240" height="{H}" fill="url(#b-beam)"/>'
            f'<rect x="239" y="0" width="1.2" height="{H}" fill="{GOLD}" fill-opacity=".35"/></g>')
    cx, cy = 128, 118
    target = (
        f'<circle cx="{cx}" cy="{cy}" r="74" fill="url(#b-glow)" class="breathe"/>'
        f'<g style="transform-origin:{cx}px {cy}px;animation:spin 14s linear infinite">'
        f'<circle cx="{cx}" cy="{cy}" r="62" fill="none" stroke="{AMBER}" stroke-opacity=".5" stroke-width="1.5" stroke-dasharray="3 7"/></g>'
        f'<g style="transform-origin:{cx}px {cy}px;animation:spinr 9s linear infinite">'
        f'<circle cx="{cx}" cy="{cy}" r="46" fill="none" stroke="{INK}" stroke-opacity=".18" stroke-width="1.5" stroke-dasharray="40 32"/></g>'
        + icon("bug", cx, cy)
    )
    defs += (f'<radialGradient id="b-glow"><stop offset="0" stop-color="{AMBER}" stop-opacity=".28"/>'
             f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>')
    vendors = ""
    x = 248.0
    for k, v in enumerate(["SONY", "MICROSOFT", "SAMSUNG", "AND MORE"]):
        col = INK if k < 3 else INK3
        vendors += mono_text(x, 186, v, 22, col, ls=3)
        x += len(v) * (22 * CW + 3)
        if k < 3:
            vendors += f'<polygon points="{hex_pts(x + 20, 179, 5)}" fill="{AMBER}"/>'
            x += 40
    body = (
        bg + f'<g clip-path="url(#{clip})">{hc}{beam}</g>' + target
        + mono_text(250, 66, "BUG BOUNTY · RESPONSIBLE DISCLOSURE", 14, AMBER, ls=2.6)
        + f'<text class="s" x="248" y="124" font-size="38" font-weight="800" letter-spacing="-1" fill="{INK}">'
          f'I break things <tspan fill="{AMBER}">so they can be fixed.</tspan></text>'
        + vendors + border
    )
    return svg(W, H, "Bug bounty: Sony, Microsoft, Samsung and more", body, defs,
               desc="Bug bounty hunter, responsible disclosure. I break things so they can be fixed. "
                    "Programs: Sony, Microsoft, Samsung and more.")


# ---------------------------------------------------------------- stack
def stack() -> str:
    rows = [
        ("SYSTEMS", ["C++20", "Vulkan", "SPIR-V", "CMake + Ninja", "x86-64", "static recompilation"]),
        ("AI / LLM", ["Python", "FastAPI", "SQLite", "local LLM inference", "cognitive architectures"]),
        ("AGENTIC", ["Claude Code", "MCP", "agentic IDEs", "multi-agent orchestration"]),
        ("WEB & APPS", ["TypeScript", "Node.js", "WebGPU", "Capacitor"]),
    ]
    W = 1200
    y0, rh = 158, 58
    H = y0 + len(rows) * rh + 22
    defs, bg, border, clip = card("s", W, H, rx=28)
    hc_defs, hc = honeycomb("s", W, H, 20, 1150, 40, 420, op=.09)
    defs += hc_defs
    head = (mono_text(48, 66, "TOOLBOX", 15, AMBER, ls=3)
            + f'<text class="s" x="46" y="116" font-size="40" font-weight="800" letter-spacing="-1" fill="{INK}">'
              f'The stack behind <tspan fill="{AMBER}">the lab.</tspan></text>')
    out = ""
    idx = 0
    total = sum(len(r[1]) for r in rows)
    for r, (label, items) in enumerate(rows):
        y = y0 + r * rh
        out += mono_text(48, y + 25, label, 13, INK3, ls=2)
        x = 236.0
        for it in items:
            delay = idx * 0.35
            el, w = chip(x, y, it, fs=16, fill=INK, pad=16, h=38)
            hl = (f'<rect x="{x}" y="{y}" width="{w:.1f}" height="38" rx="19" fill="{AMBER}" fill-opacity=".10" '
                  f'stroke="{AMBER}" stroke-width="1.5" opacity="0" '
                  f'style="animation:wave {total * .35:.2f}s linear {delay:.2f}s infinite"/>')
            out += el + hl
            x += w + 10
            idx += 1
    body = bg + f'<g clip-path="url(#{clip})">{hc}</g>' + head + out + border
    return svg(W, H, "Toolbox: the stack behind the lab", body, defs,
               desc="; ".join(f"{label}: {', '.join(items)}" for label, items in rows))


# ---------------------------------------------------------------- collaborate
def collab() -> str:
    W, H = 1200, 380
    defs, bg, border, clip = card("c", W, H, rx=30)
    hc_defs, hc = honeycomb("c", W, H, 24, W / 2, H, 640, op=.10)
    defs += hc_defs
    blobs = ""
    for uid, cx, cy, r, col, op, anim, dur in (
        ("cb1", 600, 420, 420, AMBER, .22, "d1", 20),
        ("cb2", 150, 0, 260, HONEY, .12, "d3", 24),
        ("cb3", 1080, 40, 260, GOLD, .10, "d2", 26),
    ):
        d, el = blob(uid, cx, cy, r, col, op, anim, dur)
        defs += d
        blobs += el
    lit = lit_cells(24, [(12, 14, 0, 6, .3), (14, 13, 2, 7, .25), (10, 13, 3.5, 8, .2), (16, 14, 1, 6.5, .2),
                         (8, 14, 4.2, 7, .15), (13, 12, 5.1, 9, .15)])
    kicker = "OPEN TO COLLABORATION"
    kw = len(kicker) * (14 * CW + 3)
    kx = W / 2 - kw / 2 + 12
    cta = "Open an issue to say hi  →"
    cfs = 17
    cw_ = len(cta) * cfs * CW + 56
    body = (
        bg + f'<g clip-path="url(#{clip})">{blobs}{hc}{lit}</g>'
        + f'<circle cx="{kx - 20}" cy="61" r="5" fill="{AMBER}"/>'
          f'<circle cx="{kx - 20}" cy="61" r="5" fill="none" stroke="{AMBER}" stroke-width="2">'
          f'<animate attributeName="r" values="5;13" dur="1.8s" repeatCount="indefinite"/>'
          f'<animate attributeName="stroke-opacity" values=".8;0" dur="1.8s" repeatCount="indefinite"/></circle>'
        + mono_text(kx, 66, kicker, 14, AMBER, ls=3)
        + f'<text class="s" x="{W / 2}" y="136" text-anchor="middle" font-size="52" font-weight="800" letter-spacing="-1.5" fill="{INK}">'
          f'Let\'s build <tspan fill="{AMBER}">what comes next.</tspan></text>'
        + f'<text class="s" x="{W / 2}" y="186" text-anchor="middle" font-size="21" fill="{INK2}">'
          f'Projects of general interest, experimental research and futuristic ideas:</text>'
        + f'<text class="s" x="{W / 2}" y="218" text-anchor="middle" font-size="21" fill="{INK2}">'
          f'digital individuals, agentic systems, open ports of closed platforms.</text>'
        + f'<rect x="{W / 2 - cw_ / 2}" y="254" width="{cw_:.1f}" height="54" rx="27" fill="{AMBER}"/>'
        + f'<rect x="{W / 2 - cw_ / 2}" y="254" width="{cw_:.1f}" height="54" rx="27" fill="none" stroke="{GOLD}" stroke-width="2" class="breathe"/>'
        + mono_text(W / 2 - (cw_ - 56) / 2, 287, cta, cfs, "#1a1205", extra=' font-weight="700"')
        + glyph(W / 2 - 13, 330, 26, sw=11)
        + border
    )
    return svg(W, H, "Let's build what comes next", body, defs,
               desc="Open to collaboration on projects of general interest, experimental research and futuristic "
                    "ideas: digital individuals, agentic systems, open ports of closed platforms. "
                    "Open an issue to say hi.")


def nav_pill(name: str, text: str, primary: bool = False) -> None:
    fs, h, pad = 15, 44, 22
    tw = len(text) * fs * CW
    hexw = 18
    W = round(tw + 2 * pad + hexw)
    if primary:
        fill, fop, stroke, sop, ink = AMBER, 1, GOLD, .9, "#1a1205"
    else:
        fill, fop, stroke, sop, ink = BG1, 1, INK, .16, INK
    body = (
        f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="{(h - 2) / 2}" fill="{fill}" fill-opacity="{fop}" '
        f'stroke="{stroke}" stroke-opacity="{sop}" stroke-width="1.5"/>'
        f'<polygon points="{hex_pts(pad + 4, h / 2, 6)}" fill="{"#1a1205" if primary else AMBER}" class="breathe"/>'
        + mono_text(pad + hexw, h / 2 + fs * .36, text, fs, ink, extra=' font-weight="600"')
    )
    write(f"{name}.svg", svg(W, h, text, body))


def main() -> None:
    print("Building assets ->", OUT)
    write("hero.svg", hero())
    write("whoami.svg", whoami())
    write("what-i-do.svg", pillars())
    write("honeylabs.svg", lab())
    header("work", "SELECTED WORK", "Open source, reverse engineering", "& research.")
    project_card(
        "card-anyps5", "OPEN SOURCE · CONTRIBUTOR", "★ 60k+", "AnyPS5",
        ["Automatic porting of PS5 executables to Linux",
         "and Windows. I work on GPU / AGC performance,",
         "like keeping draw snapshots in resizable BAR."],
        ["C++", "Vulkan", "GPU", "porting"], "boykopovar/AnyPS5",
    )
    project_card(
        "card-nativeframe", "OPEN SOURCE · MAINTAINER", "GPL-2.0", "NativeFrame",
        ["Native PC ports of console games. My performance",
         "fork of AnyPS5: static conversion, rebuilt system",
         "libraries, Vulkan rendering. Target: 60 FPS."],
        ["C++20", "Vulkan", "SPIR-V", "CMake"], "NativeFrame", side="right",
    )
    project_card(
        "card-hllm", "HONEYLABS · FLAGSHIP", "38 words/s", "HLLM Vision",
        ["Human LLM: a digital mind that lives on a machine",
         "in your home. It remembers for years, reasons",
         "before answering and sleeps to consolidate."],
        ["local AI", "memory", "privacy"], "hllm-honeylabs",
    )
    project_card(
        "card-apimind", "RESEARCH · SCARLET", "cognition", "LLM API Mind",
        ["External cognitive architecture for Scarlet, a",
         "digital individual in development. Motto:",
         "“Build the microscope before the mind.”"],
        ["Python", "FastAPI", "SQLite", "traces"], "llm-api-mind", side="right",
    )
    write("bug-bounty.svg", bounty())
    write("stack.svg", stack())
    write("collaborate.svg", collab())
    nav_pill("nav-hllm", "HLLM Vision")
    nav_pill("nav-nativeframe", "NativeFrame")
    nav_pill("nav-anyps5", "AnyPS5")
    nav_pill("nav-apimind", "LLM API Mind")
    nav_pill("nav-hi", "Say hi", primary=True)


if __name__ == "__main__":
    main()

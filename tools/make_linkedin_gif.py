"""Generate a 16:9 LinkedIn showcase GIF for dynacode.

One 1280x720 terminal-style scene with all four animation zones running at
once. Animation math is imported from make_gifs.py, which is a 1:1 port of
the functions tui.tsx runs in the OpenCode TUI.

Loop: 90 frames @ 90ms = 8.1s. The phrase cycle is shortened to 30 frames
here (the TUI uses 45) so all three phrases fit one loop.
"""

import os
from PIL import Image, ImageDraw, ImageFont

from make_gifs import (
    PHRASES,
    PULSE_GLYPH,
    SPIN_GLYPH,
    clock_line,
    eq_line,
    font_for,
    scramble,
)

W, H = 1280, 720
FRAMES = 90
DURATION = 90

BG = (18, 18, 18)
PANEL = (26, 26, 26)
BORDER = (51, 51, 51)
TITLE = (240, 240, 240)
SUB = (150, 150, 150)
CAPTION = (138, 138, 138)
CAPTION_SUB = (90, 90, 90)
ORANGE = (255, 158, 94)
YELLOW = (232, 194, 106)
GREEN = (100, 195, 100)
RED = (227, 93, 93)
GREY = (156, 156, 156)

TTF = r"C:\Users\dcuyl\AppData\Local\Programs\Python\Python313\Lib\site-packages\matplotlib\mpl-data\fonts\ttf"
SANS = os.path.join(TTF, "DejaVuSans.ttf")
SANS_BOLD = os.path.join(TTF, "DejaVuSans-Bold.ttf")
MONO_SIZE = 24

# --- zone lines (reuse the plugin's math) -----------------------------------


def ribbon_line(f: int) -> str:
    stages = [(0, "starting"), (16, "⚙ bash"), (38, "reasoning"), (58, "streaming")]
    start, text = max((s for s in stages if s[0] <= f), key=lambda s: s[0])
    progress = min(1.0, (f - start) / 6.67)
    glyph = PULSE_GLYPH[(f // 5) % len(PULSE_GLYPH)]
    return glyph + " " + scramble(text, progress, f)


def prompt_line(f: int):
    """Returns (text, color): permission -> done -> fail -> gap, looping."""
    if f < 24:
        return SPIN_GLYPH[(f // 4) % len(SPIN_GLYPH)] + " waiting for you", YELLOW
    if f < 52:
        p = f - 24
        return scramble("✓ done in 3.4s", min(1.0, (p * 90) / 700), p), GREEN
    if f < 80:
        p = f - 52
        return scramble("✕ failed", min(1.0, (p * 90) / 700), p), RED
    return "", GREY


def vitals_line(f: int) -> str:
    seconds = 4 + f // 11
    cost = 0.10 if f < 45 else 0.11
    return f"⏱ {clock_line(seconds)} · ${cost:.2f}"


def home_line(f: int) -> str:
    cycle = 30  # 45 in the TUI; shortened so all three phrases fit one loop
    phrase = PHRASES[(f // cycle) % len(PHRASES)]
    return eq_line(f // 2) + " " + scramble(phrase, min(1.0, (f % cycle) / 8), f)


# --- rendering --------------------------------------------------------------


def draw_mono_line(draw, x, y, text, color, size=MONO_SIZE):
    for ch in text:
        font = font_for(ch, size)
        draw.text((x, y), ch, font=font, fill=color, anchor="lm")
        x += font.getlength(ch)


def build_frame(f: int) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(SANS_BOLD, 42)
    sub_font = ImageFont.truetype(SANS, 19)
    cap_font = ImageFont.truetype(SANS, 17)
    slot_font = ImageFont.truetype(SANS, 13)

    draw.text((70, 52), "dynacode", font=title_font, fill=TITLE, anchor="lm")
    title_w = title_font.getlength("dynacode")
    draw.text((70 + title_w + 18, 58), "an OpenCode animation pack", font=sub_font, fill=ORANGE, anchor="lm")
    draw.text((70, 96), "Six subtle animations that make the terminal TUI lively. One line each, driven by real session events.",
              font=sub_font, fill=SUB, anchor="lm")

    draw.rounded_rectangle((70, 130, 1210, 618), radius=14, fill=PANEL, outline=BORDER, width=2)

    rows = [
        (205, "activity ribbon", "session.composer.top"),
        (325, "permission pulse / run result", "prompt.footer.status"),
        (445, "sidebar vitals", "sidebar.footer"),
        (565, "home footer", "home.footer.status"),
    ]
    for y, name, slot in rows:
        draw.text((110, y - 12), name, font=cap_font, fill=CAPTION, anchor="lm")
        draw.text((110, y + 12), slot, font=slot_font, fill=CAPTION_SUB, anchor="lm")

    draw_mono_line(draw, 470, 205, ribbon_line(f), ORANGE)
    text, color = prompt_line(f)
    draw_mono_line(draw, 470, 325, text, color)
    draw_mono_line(draw, 470, 445, vitals_line(f), GREY)
    draw_mono_line(draw, 470, 565, home_line(f), GREY)

    draw.text((70, 665), "github.com/SkorpioX22/dynacode", font=sub_font, fill=SUB, anchor="lm")
    toggle = "/anim on  |  /anim off"
    draw.text((1210, 665), toggle, font=sub_font, fill=CAPTION_SUB, anchor="rm")
    return img


def main():
    out = os.path.join(os.path.dirname(__file__), "..", "docs", "linkedin-showcase.gif")
    frames = [build_frame(f).convert("P", palette=Image.ADAPTIVE, colors=64) for f in range(FRAMES)]
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION,
        loop=0,
        optimize=True,
        disposal=2,
    )
    size = os.path.getsize(out)
    print(f"linkedin-showcase.gif: {FRAMES} frames {W}x{H} {size/1024:.0f}KB")


if __name__ == "__main__":
    main()

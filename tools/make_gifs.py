"""Generate README GIFs for the dynacode animation pack.

Frames are computed with the same functions (ported 1:1) that tui.tsx runs
in the OpenCode TUI, so the GIFs show exactly what the plugin renders:
same glyphs, same timings (90ms per frame), same reveal math.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

# --- constants copied from tui.tsx -----------------------------------------

NOISE = "▓▒░#*+~"
EQ_H = ["▁", "▂", "▃", "▄", "▅", "▆", "▇"]
PHRASES = ["animation pack", "/anim to toggle", "vibrant edition"]
SPIN_GLYPH = ["◐", "◓", "◑", "◒"]
PULSE_GLYPH = ["·", "•", "●", "•"]

# --- ports of the tui.tsx animation functions ------------------------------


def scramble(target: str, progress: float, seed: int) -> str:
    out = ""
    n = len(target)
    for i, ch in enumerate(target):
        at = (i + 1) / n
        if progress >= at:
            out += ch
        elif progress >= at - 0.5:
            out += NOISE[(seed + i * 5) % len(NOISE)]
        else:
            out += " "
    return out


def eq_line(frame: int) -> str:
    out = ""
    for i in range(6):
        value = math.sin((frame + i * 11) * 0.22) * 3.4 + 3.4
        idx = max(0, min(6, int(math.floor(value + 0.5))))
        out += EQ_H[idx]
    return out


def clock_line(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# --- demo timelines ---------------------------------------------------------

def demo_ribbon():
    """Activity ribbon: stages decode in, exactly like session events drive it."""
    stages = [(0, "starting"), (14, "⚙ bash"), (40, "reasoning"), (66, "streaming")]
    frames = []
    for f in range(100):
        start, text = max((s for s in stages if s[0] <= f), key=lambda s: s[0])
        progress = min(1.0, (f - start) / 6.67)  # 600ms decode
        glyph = PULSE_GLYPH[(f // 5) % len(PULSE_GLYPH)]
        frames.append(glyph + " " + scramble(text, progress, f))
    return frames


def demo_permission():
    frames = []
    for f in range(32):
        glyph = SPIN_GLYPH[(f // 4) % len(SPIN_GLYPH)]
        frames.append(glyph + " waiting for you")
    return frames


def demo_flash(text: str, total: int = 34, hold: int = 27):
    """Scramble-in over 700ms, hold ~2.4s, blank tail for a clean loop."""
    frames = []
    for f in range(total):
        if f >= hold:
            frames.append("")
            continue
        progress = min(1.0, (f * 90) / 700)
        frames.append(scramble(text, progress, f))
    return frames


def demo_vitals():
    frames = []
    for f in range(44):
        seconds = 4 + f // 11  # clock ticks once per second
        cost = 0.10 if f < 33 else 0.11
        frames.append(f"⏱ {clock_line(seconds)} · ${cost:.2f}")
    return frames


def demo_home():
    frames = []
    for f in range(135):  # 3 phrases x 45 frames
        cycle = 45
        phrase = PHRASES[(f // cycle) % len(PHRASES)]
        progress = min(1.0, (f % cycle) / 8)
        frames.append(eq_line(f // 2) + " " + scramble(phrase, progress, f))
    return frames


# --- rendering --------------------------------------------------------------

BG = (23, 23, 23)
PRIMARY = r"C:\Users\dcuyl\AppData\Local\Programs\Python\Python313\Lib\site-packages\matplotlib\mpl-data\fonts\ttf\DejaVuSansMono.ttf"
FALLBACKS = [
    r"C:\Windows\Fonts\seguisym.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\consola.ttf",
]

_font_cache = {}


def font_for(ch: str, size: int):
    key = (ch, size)
    if key in _font_cache:
        return _font_cache[key]
    path = PRIMARY
    try:
        from fontTools.ttLib import TTFont  # noqa: F401

        for candidate in [PRIMARY] + FALLBACKS:
            try:
                if ord(ch) in _cmap(candidate):
                    path = candidate
                    break
            except Exception:
                continue
    except ImportError:
        pass
    font = ImageFont.truetype(path, size)
    _font_cache[key] = font
    return font


def _cmap(path: str):
    if path not in _font_cache:
        from fontTools.ttLib import TTFont

        with TTFont(path, fontNumber=0) as tt:
            _font_cache[path] = set(tt.getBestCmap().keys())
    return _font_cache[path]


def measure(text: str, size: int) -> int:
    return sum(font_for(ch, size).getlength(ch) for ch in text)


def render(frames, color, out_path: str, size: int = 18, pad: int = 14, duration: int = 90):
    width = int(max(measure(f, size) for f in frames)) + pad * 2
    height = size + pad * 2 + 6
    images = []
    for text in frames:
        img = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(img)
        x = pad
        baseline = height // 2
        for ch in text:
            font = font_for(ch, size)
            draw.text((x, baseline), ch, font=font, fill=color, anchor="lm")
            x += font.getlength(ch)
        images.append(img.convert("P", palette=Image.ADAPTIVE, colors=64))
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"{os.path.basename(out_path)}: {len(images)} frames, {width}x{height}")


def main():
    out = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(out, exist_ok=True)
    render(demo_ribbon(), (255, 158, 94), os.path.join(out, "activity-ribbon.gif"))
    render(demo_permission(), (232, 194, 106), os.path.join(out, "permission-pulse.gif"))
    render(demo_flash("✓ done in 3.4s"), (100, 195, 100), os.path.join(out, "done-flash.gif"))
    render(demo_flash("✕ failed"), (227, 93, 93), os.path.join(out, "fail-flash.gif"))
    render(demo_vitals(), (156, 156, 156), os.path.join(out, "sidebar-vitals.gif"))
    render(demo_home(), (156, 156, 156), os.path.join(out, "home-footer.gif"))


if __name__ == "__main__":
    main()

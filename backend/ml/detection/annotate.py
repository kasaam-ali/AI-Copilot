"""Draw detection boxes + labels onto an image (returns PNG bytes)."""

from __future__ import annotations

import hashlib
import io

from PIL import Image, ImageDraw, ImageFont

# Distinct, high-contrast colors; a label maps to a stable color by hash.
_PALETTE = [
    "#ef4444", "#f5a623", "#10b981", "#3b82f6",
    "#a855f7", "#ec4899", "#14b8a6", "#f97316",
]


def color_for(label: str) -> str:
    index = int(hashlib.md5(label.encode()).hexdigest(), 16) % len(_PALETTE)
    return _PALETTE[index]


def _font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # older Pillow
        return ImageFont.load_default()


def annotate(image: Image.Image, detections) -> bytes:
    img = image.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    line_width = max(2, img.width // 300)
    font = _font(max(14, img.width // 45))

    for det in detections:
        x1, y1, x2, y2 = det.box
        color = color_for(det.label)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        text = f"{det.label} {det.confidence:.0%}"
        tb = draw.textbbox((0, 0), text, font=font)
        text_h = tb[3] - tb[1]
        text_w = tb[2] - tb[0]
        label_top = max(0, y1 - text_h - 6)
        draw.rectangle([x1, label_top, x1 + text_w + 8, label_top + text_h + 6], fill=color)
        draw.text((x1 + 4, label_top + 3), text, fill="#0b0f14", font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

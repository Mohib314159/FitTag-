"""Generate the printable FitTag calibration kit -> print/

Four A4 corner sheets (tape into a 1000x1400 mm rectangle), a single-marker quick sheet,
and a placement guide. Everything is computed from core.calibrate's layout constants, so
the printed kit can never drift from what the engine expects.

    python make_mat.py
"""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.calibrate import (DEFAULT_MAT_LAYOUT, MAT_MM, MAT_MARKER_MM,
                            calibrate, make_marker)

DPI = 300
MM = DPI / 25.4                       # px per mm
A4_MM = (210.0, 297.0)
A4_PX = (round(A4_MM[0] * MM), round(A4_MM[1] * MM))
W, H = MAT_MM
DIAG = math.hypot(W, H)

INK, PAPER, TAPE, SOFT = (26, 23, 20), (255, 255, 255), (232, 181, 0), (110, 102, 90)
CORNER = {0: "TOP-LEFT", 1: "TOP-RIGHT", 2: "BOTTOM-RIGHT", 3: "BOTTOM-LEFT"}
ORIGIN = {0: (0.0, 0.0), 1: (W - A4_MM[0], 0.0),
          2: (W - A4_MM[0], H - A4_MM[1]), 3: (0.0, H - A4_MM[1])}

OUT = Path(__file__).resolve().parent / "print"


def _font(size, bold=True, mono=False):
    cands = (["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"] if mono else
             ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    if not bold:
        cands = cands[1:] + cands[:1]
    for p in cands:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def mm2px(v):
    return round(v * MM)


def _check_bar(d: ImageDraw.ImageDraw, x_mm, y_mm):
    """A 100 mm bar with 10 mm ticks — the print-scale verification instrument."""
    x0, y = mm2px(x_mm), mm2px(y_mm)
    x1 = x0 + mm2px(100)
    d.line([(x0, y), (x1, y)], fill=INK, width=6)
    for k in range(11):
        xk = x0 + mm2px(10 * k)
        tall = 5 if k % 5 == 0 else 3
        d.line([(xk, y - mm2px(tall)), (xk, y)], fill=INK, width=4)
    d.text((x0, y + mm2px(2)),
           "THIS BAR MUST MEASURE EXACTLY 100 mm  —  print at 100% / \"Actual size\"",
           font=_font(40), fill=INK)


def _arrow_up(d, cx_mm, y_mm):
    cx, y0 = mm2px(cx_mm), mm2px(y_mm)
    d.line([(cx, y0 + mm2px(16)), (cx, y0)], fill=INK, width=10)
    d.polygon([(cx - mm2px(5), y0 + mm2px(5)), (cx + mm2px(5), y0 + mm2px(5)), (cx, y0 - mm2px(2))], fill=INK)
    d.text((cx + mm2px(8), y0), "THIS WAY UP", font=_font(52), fill=INK)


def _corner_mark(d, corner_id):
    """L-shaped registration mark at the sheet corner that becomes a mat corner."""
    L, t = mm2px(12), 6
    Wp, Hp = A4_PX
    pts = {0: [(0, L), (0, 0), (L, 0)], 1: [(Wp - L, 0), (Wp - 1, 0), (Wp - 1, L)],
           2: [(Wp - 1, Hp - L), (Wp - 1, Hp - 1), (Wp - L, Hp - 1)],
           3: [(L, Hp - 1), (0, Hp - 1), (0, Hp - L)]}[corner_id]
    d.line(pts, fill=(197, 69, 62), width=t)


def corner_sheet(mid: int) -> Image.Image:
    img = Image.new("RGB", A4_PX, PAPER)
    d = ImageDraw.Draw(img)
    ox, oy = ORIGIN[mid]
    mx, my = DEFAULT_MAT_LAYOUT[mid][0] - ox, DEFAULT_MAT_LAYOUT[mid][1] - oy
    side = mm2px(MAT_MARKER_MM)
    marker = make_marker(mid, side_px=side)
    img.paste(Image.fromarray(marker).convert("RGB"), (mm2px(mx), mm2px(my)))

    # info band in the marker-free middle of the sheet
    ty = 128 if my < 148 else 18
    d.text((mm2px(14), mm2px(ty)), f"FITTAG CALIBRATION  ·  {CORNER[mid]}  ·  ID {mid}",
           font=_font(66), fill=INK)
    d.rectangle([mm2px(14), mm2px(ty + 9.5), mm2px(14 + 42), mm2px(ty + 11)], fill=TAPE)
    _arrow_up(d, 20, ty + 22)
    _check_bar(d, 14, ty + 42)
    d.text((mm2px(14), mm2px(ty + 52)),
           f"Tape all four sheets flat so their OUTER corners form a {W:.0f} x {H:.0f} mm rectangle.\n"
           f"Check BOTH diagonals with a tape: each should be = {DIAG:.0f} mm. Equal diagonals = square.\n"
           f"Red corner mark = the mat corner. Keep every sheet upright (arrows up). Avoid glare.",
           font=_font(38, bold=False), fill=SOFT, spacing=14)
    _corner_mark(d, mid)
    d.text((mm2px(14), A4_PX[1] - mm2px(10)),
           f"fittag calibration kit · sheet for corner {CORNER[mid].lower()} · 4x4 ArUco · marker {MAT_MARKER_MM:.0f} mm",
           font=_font(30, bold=False, mono=True), fill=SOFT)
    return img


def single_sheet(mid: int = 10, size_mm: float = 50.0) -> Image.Image:
    img = Image.new("RGB", A4_PX, PAPER)
    d = ImageDraw.Draw(img)
    side = mm2px(size_mm)
    img.paste(Image.fromarray(make_marker(mid, side_px=side)).convert("RGB"),
              (mm2px((A4_MM[0] - size_mm) / 2), mm2px(40)))
    d.text((mm2px(14), mm2px(110)), "FITTAG QUICK MARKER  ·  SINGLE MODE", font=_font(66), fill=INK)
    d.rectangle([mm2px(14), mm2px(119.5), mm2px(56), mm2px(121)], fill=TAPE)
    d.text((mm2px(14), mm2px(126)),
           f"No mat needed: place this {size_mm:.0f} mm marker flat beside the garment, same surface,\n"
           "and shoot from above. Faster — but ~4x wider tolerance than the four-corner mat.\n"
           "For listing-grade numbers, use the full kit.",
           font=_font(38, bold=False), fill=SOFT, spacing=14)
    _arrow_up(d, 20, 152)
    _check_bar(d, 14, 172)
    d.text((mm2px(14), A4_PX[1] - mm2px(10)),
           f"fittag calibration kit · quick single marker · 4x4 ArUco · id {mid} · {size_mm:.0f} mm",
           font=_font(30, bold=False, mono=True), fill=SOFT)
    return img


def guide_sheet() -> Image.Image:
    img = Image.new("RGB", A4_PX, PAPER)
    d = ImageDraw.Draw(img)
    d.text((mm2px(14), mm2px(14)), "FITTAG MAT — PLACEMENT GUIDE", font=_font(72), fill=INK)
    d.rectangle([mm2px(14), mm2px(24.5), mm2px(70), mm2px(26)], fill=TAPE)
    steps = [
        f"1  Print the four corner sheets at 100% (\"Actual size\"). Verify each 100 mm bar with a ruler.",
        f"2  Tape them flat on the floor so the OUTER sheet corners (red marks) form {W:.0f} x {H:.0f} mm.",
        f"3  Measure BOTH diagonals: each must read = {DIAG:.0f} mm. Equal diagonals = right angles.",
        "4  Every sheet upright — all arrows point the same way. No folds, no glare, even light.",
        "5  Lay the garment flat inside the rectangle. Smooth it; don't stretch it.",
        "6  Shoot from roughly above with ALL FOUR markers in frame. One photo is enough.",
    ]
    d.text((mm2px(14), mm2px(32)), "\n".join(steps), font=_font(40, bold=False), fill=INK, spacing=26)

    # diagram: mat rectangle + corner markers + garment silhouette
    gx, gy = mm2px(30), mm2px(120)
    gw, gh = mm2px(150), mm2px(150 * H / W)  # keep aspect
    d.rectangle([gx, gy, gx + gw, gy + gh], outline=INK, width=6)
    s = mm2px(14)
    for mid, (lx, ly) in DEFAULT_MAT_LAYOUT.items():
        px = gx + int(lx / W * gw); py = gy + int(ly / H * gh)
        d.rectangle([px, py, px + s, py + s], fill=INK)
        d.text((px + s + 8, py), f"ID {mid}", font=_font(34, mono=True), fill=SOFT)
    # simple tee silhouette
    cx, cy = gx + gw // 2, gy + gh // 2
    bw, bl, sw = mm2px(42), mm2px(56), mm2px(16)
    d.polygon([(cx - bw//2 - sw, cy - bl//2), (cx + bw//2 + sw, cy - bl//2),
               (cx + bw//2 + sw, cy - bl//2 + mm2px(12)), (cx + bw//2, cy - bl//2 + mm2px(12)),
               (cx + bw//2, cy + bl//2), (cx - bw//2, cy + bl//2),
               (cx - bw//2, cy - bl//2 + mm2px(12)), (cx - bw//2 - sw, cy - bl//2 + mm2px(12))],
              outline=(63, 78, 112), width=6)
    d.text((gx, gy + gh + mm2px(6)),
           f"diagonal check: corner-to-corner = {DIAG:.0f} mm (both ways)",
           font=_font(36, mono=True), fill=SOFT)
    return img


def self_test():
    """End-to-end proof the printed kit works: composite the actual sheet PNGs at their
    mat positions, tilt the scene like a handheld photo, and run the real calibrate()."""
    scale = 0.6  # px per mm for the virtual floor
    floor = np.full((int(H * scale), int(W * scale), 3), 246, np.uint8)
    for mid in DEFAULT_MAT_LAYOUT:
        sheet = cv2.imread(str(OUT / f"mat_corner_{mid}_{CORNER[mid].lower().replace('-','_')}.png"))
        sheet = cv2.resize(sheet, (int(A4_MM[0] * scale), int(A4_MM[1] * scale)),
                           interpolation=cv2.INTER_AREA)
        ox, oy = ORIGIN[mid]
        x, y = int(ox * scale), int(oy * scale)
        floor[y:y + sheet.shape[0], x:x + sheet.shape[1]] = sheet
    h, w = floor.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[w*0.06, h*0.03], [w*0.96, 0], [w, h], [w*0.02, h*0.97]])
    photo = cv2.warpPerspective(floor, cv2.getPerspectiveTransform(src, dst), (w, h),
                                borderValue=(200, 200, 200))
    cal = calibrate(photo, mm_per_px_out=0.5)
    assert cal.ok and cal.mode == "mat" and cal.n_markers == 4, \
        f"kit self-test FAILED: ok={cal.ok} mode={cal.mode} n={cal.n_markers}"
    print(f"kit self-test: PASS — mode={cal.mode}, markers={cal.n_markers}, tol x{cal.tol_scale}")


def main():
    OUT.mkdir(exist_ok=True)
    for mid in DEFAULT_MAT_LAYOUT:
        corner_sheet(mid).save(
            OUT / f"mat_corner_{mid}_{CORNER[mid].lower().replace('-','_')}.png", dpi=(DPI, DPI))
    single_sheet().save(OUT / "quick_single_marker.png", dpi=(DPI, DPI))
    guide_sheet().save(OUT / "placement_guide.png", dpi=(DPI, DPI))
    print(f"wrote {len(list(OUT.glob('*.png')))} sheets -> {OUT}")
    self_test()


if __name__ == "__main__":
    main()

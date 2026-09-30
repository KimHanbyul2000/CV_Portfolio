"""곡면 수식. 이미지·영상(render.py)이 import 한다.

같은 수식이 web/surface.js 에도 있다. 한쪽을 고치면 다른 쪽도 고친다.
매개변수는 data/surface.json 에서만 읽는다.

각 기둥이 자기 곡면을 만들고, 최종 곡면 S 는 그 중첩(합)이다. 상호작용(시너지) 항은 없다.

  f_i(x, y) = h_i · exp(-d_i² / 2σ_i²) · m_i(θ_i, d_i)        기둥 i 의 곡면, 꼭짓점 = h_i
  m_i       = 1 - depth · (1 - cos(k(θ_i - φ))) / 2 · (1 - exp(-d_i² / 2c²))
              방향별 특화·부족 (L2 만). 기둥 바로 위(d→0)에서는 1 이라 꼭짓점 높이가 유지된다
  f_now     = H · exp(-r² / 2σ_now²)                           L_now 의 곡면, H 는 시점에 따라 변한다
  S(x, y)   = z_scale · ( g · Σ_i f_i + f_now )

  u (이야기 진행도, 0~4): 0~1 기둥 셋 · 1~2 각 곡면과 중첩 · 2~3 현재의 L_now · 3~4 미래 기대값
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "data" / "surface.json").read_text(encoding="utf-8"))
SURF = CFG["surface"]
CENTER = CFG["center"]
ZS = CFG["z_scale"]
U_MAX = 4.0

PILLARS = CFG["pillars"]
PILLAR_XY = np.array([
    [p["radius"] * np.cos(np.radians(p["angle_deg"])),
     p["radius"] * np.sin(np.radians(p["angle_deg"]))]
    for p in PILLARS
])


def own_surface(i, x, y):
    """기둥 i 의 곡면 f_i (상징 단위, z_scale 적용 전)."""
    p = PILLARS[i]
    px, py = PILLAR_XY[i]
    dx, dy = x - px, y - py
    d2 = dx ** 2 + dy ** 2
    f = p["height"] * np.exp(-d2 / (2 * p["sigma"] ** 2))
    lb = p.get("lobes")
    if lb:
        th = np.arctan2(dy, dx) - np.radians(lb["phase_deg"])
        dip = lb["depth"] * (1 - np.cos(lb["count"] * th)) / 2
        f = f * (1 - dip * (1 - np.exp(-d2 / (2 * lb["core"] ** 2))))
    return f


def now_surface(x, y, H):
    return H * np.exp(-(x ** 2 + y ** 2) / (2 * CENTER["sigma"] ** 2))


def z(x, y, g, H):
    """최종 곡면 S (장면 높이)."""
    total = sum(own_surface(i, x, y) for i in range(len(PILLARS)))
    return ZS * (g * total + now_surface(x, y, H))


def polar_grid():
    r = np.linspace(0, SURF["r_max"], SURF["n_r"])
    t = np.linspace(0, 2 * np.pi, SURF["n_theta"] + 1)
    R, T = np.meshgrid(r, t)
    return R * np.cos(T), R * np.sin(T)


def roots(i):
    """기둥 i 의 뿌리 가닥: 바닥 점 [(x, y)], 합류 높이 비율. 없으면 ([], 0)."""
    r = PILLARS[i].get("roots")
    if not r:
        return [], 0.0
    cx, cy = r["center"]
    n = r["count"]
    pts = [(cx + r["radius"] * np.cos(2 * np.pi * k / n + 0.13),
            cy + r["radius"] * np.sin(2 * np.pi * k / n + 0.13)) for k in range(n)]
    return pts, r["join"]


def _ease(v):
    v = np.clip(v, 0.0, 1.0)
    return v * v * (3 - 2 * v)


def story_state(u):
    """→ (기둥 셋 비율, g, L_now 높이 H(상징 단위))."""
    frac = np.array([_ease((u - 0.25 * i) / 0.5) for i in range(3)])
    g = float(_ease(u - 1))
    H = (CENTER["h_now"] * float(_ease(u - 2))
         + (CENTER["h_future"] - CENTER["h_now"]) * float(_ease(u - 3)))
    return frac, g, H

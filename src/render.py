"""이미지·영상 생성.

  python3 src/render.py            # 이미지 6장 (assets/img/)
  python3 src/render.py --video    # 이미지 + 영상 (assets/video/convergence.mp4)

영상 인코딩에 imageio-ffmpeg 에 번들된 ffmpeg 를 쓴다(requirements.txt).
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np

import surface as sf

ROOT = sf.ROOT
IMG = ROOT / "assets" / "img"
VID = ROOT / "assets" / "video"

BG = sf.CFG["background"]
ORANGE = sf.SURF["color"]
C = sf.CENTER
PLANE = "#2a3350"
INK = "#e8ecf5"
MUTED = "#8b93a8"
AZIM = -75   # 기둥 셋+중심 사이 모든 연결선(30° 간격)과 15° 떨어진 방향 — 화면에서 서로 가장 덜 겹친다

plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "NanumGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

STAGES = {
    1: ("STAGE 1 · Foundations", "학문적 기초 — 세 기둥. 바이오메디컬공학은 낮지만 가장 넓은 바닥을 딛는다"),
    2: ("STAGE 2 · Integration", "융합 — 각 기둥이 자기 곡면을 만들고, 그 중첩이 전체 곡면 S"),
    3: ("STAGE 3 · Now (2026)", "현재 — 뉴로모픽 반도체 L_now 는 아직 가장 낮다. 그 곡면이 더해져 전체가 약간 오른다"),
    4: ("STAGE 4 · Future (expected)", "미래 기대값 — L_now 가 가장 높아지며 전체 곡면을 끌어올린다"),
}
ZMAX = 5.0
L1_LABEL_Z = 2.7  # L1 라벨 최소 높이 — L2 라벨과 겹치지 않게
OWN_CUT = 0.3   # 개별 곡면은 자기 꼭짓점의 30% 이상인 영역만 그린다

X, Y = sf.polar_grid()
LABEL_BOX = dict(facecolor=BG, alpha=0.78, edgecolor="none", boxstyle="round,pad=0.3")


def zs(x, y, g, H):
    return float(sf.z(np.array(x), np.array(y), g, H))


def draw(ax, u, labels=True, label_size=13, own=False):
    frac, g, H = sf.story_state(u)
    ZS = sf.ZS
    ax.set_facecolor(BG)
    ax.set_axis_off()
    r = sf.SURF["r_max"]
    ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(0, ZMAX)
    ax.set_box_aspect((1, 1, 0.9))
    ax.computed_zorder = False

    # 3D 평면 (z=0)
    ax.plot_wireframe(X, Y, np.zeros_like(X), rstride=3, cstride=2,
                      color=PLANE, linewidth=0.5, zorder=1)

    # z축 = 깊이 · 전문성 (정성적, 눈금 없음)
    if sf.CFG.get("depth_axis") and labels:
        ax.quiver(1.9, 1.6, 0, 0, 0, ZMAX * 0.92, color=MUTED, linewidth=1.2,
                  arrow_length_ratio=0.04, zorder=1)
        if labels:
            ax.text(1.9, 1.6, ZMAX * 0.97, "깊이 · 전문성\nDepth", color=MUTED,
                    fontsize=label_size - 3, ha="center", va="bottom", zorder=6)

    # 각 기둥의 곡면 (옅게) → 중첩 = 전체 곡면 S (주황)
    if g > 0.001:
        if own:
            # 각자의 영역만 보이도록 꼭짓점의 OWN_CUT 미만은 지운다
            for i, p in enumerate(sf.PILLARS):
                f = sf.own_surface(i, X, Y)
                ax.plot_wireframe(X, Y, np.where(f >= OWN_CUT * p["height"], ZS * g * f, np.nan),
                                  rstride=2, cstride=2, color=p["color"], linewidth=0.8,
                                  alpha=0.7 * g, zorder=2)
            if H > 0.01:
                f = sf.now_surface(X, Y, H)
                ax.plot_wireframe(X, Y, np.where(f >= OWN_CUT * H, ZS * f, np.nan),
                                  rstride=2, cstride=2, color=C["color"], linewidth=0.8,
                                  alpha=0.7, zorder=2)
        ax.plot_wireframe(X, Y, sf.z(X, Y, g, H), rstride=1, cstride=1, color=ORANGE,
                          linewidth=0.5, alpha=0.15 + 0.4 * g, zorder=2)

    # 세 기둥 L1~L3
    for i, ((px, py), f, p) in enumerate(zip(sf.PILLAR_XY, frac, sf.PILLARS)):
        if f <= 0.001:
            continue
        top = ZS * p["height"] * f
        pts, join = sf.roots(i)
        if pts:
            rt = p["roots"]
            t = np.linspace(0, 2 * np.pi, 120)
            ax.plot(rt["center"][0] + rt["radius"] * np.cos(t),
                    rt["center"][1] + rt["radius"] * np.sin(t), 0 * t,
                    color=p["color"], linewidth=1.0, alpha=0.55 * f, zorder=3)
            for rx, ry in pts:
                ax.plot([rx, px], [ry, py], [0, top * join], color=p["color"],
                        linewidth=0.9, alpha=0.55 * f, zorder=3)
                ax.scatter([rx], [ry], [0], s=10, color=p["color"], alpha=f,
                           zorder=3, depthshade=False)
        ax.plot([px, px], [py, py], [0, top], color=p["color"], linewidth=5,
                solid_capstyle="round", zorder=4)
        ax.scatter([px], [py], [top], s=70, color=p["color"], edgecolor="white",
                   linewidth=0.8, zorder=5, depthshade=False)
        if labels and f > 0.6:
            # 라벨 위치: 기둥 방향 바깥. L1 은 뒤쪽 가운데라 L_now 를 가리므로 왼쪽 뒤·더 높이 비킨다
            a = np.arctan2(py, px) + (np.radians(38) if i == 0 else 0)
            ox, oy = 1.7 * np.cos(a), 1.7 * np.sin(a)
            zl = max(top, zs(ox, oy, g, H)) + 0.2
            if i == 0:
                zl = max(zl, L1_LABEL_Z)
            sub = ("\n" + " · ".join(p["roots"]["fields"])) if pts else ""
            ax.text(ox, oy, zl, f"$L_{p['id'][1]}$  {p['en']}\n{p['ko']}{sub}",
                    color=p["color"], fontsize=label_size, ha="right" if i == 0 else "center",
                    va="bottom", zorder=6, fontweight="bold", bbox=LABEL_BOX)

    # 중심 기둥 L_now: 현재 높이까지 실선, 그 위(미래 기대값)는 반투명
    if H > 0.01:
        hn, ht = ZS * C["h_now"], ZS * H
        ax.plot([0, 0], [0, 0], [0, min(ht, hn)], color=C["color"], linewidth=7,
                solid_capstyle="round", zorder=4)
        future = ht > hn + 0.01
        if future:
            ax.plot([0, 0], [0, 0], [hn, ht], color=C["color"], linewidth=7,
                    alpha=0.42, solid_capstyle="round", zorder=4)
            ax.scatter([0], [0], [hn], s=60, marker="D", color=C["color"],
                       edgecolor="white", linewidth=0.8, zorder=5, depthshade=False)
            if labels:
                ax.text(0.18, -0.18, hn, "현재 2026", color=C["color"],
                        fontsize=label_size - 2, ha="left", va="center", zorder=6, bbox=LABEL_BOX)
        ax.scatter([0], [0], [ht], s=140, color=C["color"], edgecolor="white",
                   linewidth=1.0, alpha=0.7 if future else 1.0, zorder=5, depthshade=False)
        ax.scatter([0], [0], [0], s=40, color=C["color"], zorder=5, depthshade=False)
        if labels and H > C["h_now"] * 0.5:
            name = f"$L_{{now}}$  {C['en']}\n{C['ko']}"
            if H > (C["h_now"] + C["h_future"]) / 2:
                ax.text(0, 0, zs(0, 0, g, H) + 0.2, name + "\n미래 기대값", color=C["color"],
                        fontsize=label_size + 1, ha="center", va="bottom", zorder=6,
                        fontweight="bold", bbox=LABEL_BOX)
            else:
                # 곡면 아래(현재): 앞쪽 바닥에 두고 지시선으로 잇는다
                lx, ly = 0.0, -1.75
                ax.plot([lx, 0], [ly, 0], [0.05, ht], color=C["color"], linewidth=0.9,
                        alpha=0.8, zorder=5)
                ax.text(lx, ly, 0.0, name + "\n현재 2026 — 가장 얕다", color=C["color"],
                        fontsize=label_size, ha="center", va="top", zorder=6,
                        fontweight="bold", bbox=LABEL_BOX)
            ax.text(0.12, -0.12, -0.05, "$P_{now}$", color=C["color"],
                    fontsize=label_size - 1, zorder=6)

    if labels and g > 0.6:
        ex, ey = sf.PILLAR_XY[1] * 1.95
        ax.text(ex, ey, zs(ex, ey, g, H) + 0.1, "$S$", color=ORANGE,
                fontsize=label_size + 3, zorder=6, fontstyle="italic")


def draw_own(ax, which, label_size=12):
    """분해도 한 칸: 기둥 하나와 그 자기 곡면. which = 0..2 (L1~L3) 또는 "now"."""
    ax.set_facecolor(BG); ax.set_axis_off()
    r = sf.SURF["r_max"]
    ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(0, 3.2)
    ax.set_box_aspect((1, 1, 0.8))
    ax.computed_zorder = False
    ax.plot_wireframe(X, Y, np.zeros_like(X), rstride=3, cstride=2, color=PLANE,
                      linewidth=0.5, zorder=1)
    if which == "now":
        f, color, (px, py) = sf.now_surface(X, Y, C["h_now"]), C["color"], (0.0, 0.0)
        top, name = sf.ZS * C["h_now"], f"$L_{{now}}$  {C['ko']} (현재)"
    else:
        p = sf.PILLARS[which]
        f, color, (px, py) = sf.own_surface(which, X, Y), p["color"], sf.PILLAR_XY[which]
        top, name = sf.ZS * p["height"], f"$L_{p['id'][1]}$  {p['ko']}"
    ax.plot_wireframe(X, Y, sf.ZS * f, rstride=1, cstride=1, color=color, linewidth=0.45,
                      alpha=0.75, zorder=2)
    ax.plot([px, px], [py, py], [0, top], color=color, linewidth=4, zorder=4)
    ax.scatter([px], [py], [top], s=50, color=color, edgecolor="white", linewidth=0.8,
               zorder=5, depthshade=False)
    return name, color


def decomposition():
    """개별 곡면 4개 + 그 합(3단계 현재)을 한 줄로."""
    fig = new_fig(30, 7.2, 160)
    items = [0, 1, 2, "now"]
    notes = {0: "낮지만 넓다 — L2·L3 자리까지 덮는다",
             1: "방향마다 특화(돌출)와 부족(골)",
             2: "가장 높지만 일부에만 특화",
             "now": "현재는 가장 낮다"}
    for k, w in enumerate(items):
        ax = fig.add_axes([k / 5, -0.02, 1 / 5, 0.82], projection="3d")
        ax.view_init(elev=26, azim=AZIM)
        name, color = draw_own(ax, w)
        fig.text(k / 5 + 0.1, 0.9, name, color=color, fontsize=17, fontweight="bold",
                 ha="center", va="top")
        fig.text(k / 5 + 0.1, 0.83, notes[w], color=MUTED, fontsize=12, ha="center", va="top")
        fig.text((k + 1) / 5, 0.45, "=" if k == 3 else "+", color=INK, fontsize=34,
                 ha="center", va="center")
    ax = fig.add_axes([4 / 5, -0.02, 1 / 5, 0.82], projection="3d")
    ax.view_init(elev=26, azim=AZIM)
    draw(ax, 3.0, labels=False)
    ax.set_zlim(0, 3.2); ax.set_box_aspect((1, 1, 0.8))
    fig.text(0.9, 0.9, "중첩 = 전체 곡면 S", color=ORANGE, fontsize=17, fontweight="bold",
             ha="center", va="top")
    fig.text(0.9, 0.83, "상호작용(시너지) 항 없이 단순 합", color=MUTED, fontsize=12,
             ha="center", va="top")
    fig.savefig(IMG / "decomposition.png", facecolor=BG)
    plt.close(fig)


def new_fig(w, h, dpi):
    return plt.figure(figsize=(w, h), dpi=dpi, facecolor=BG)


def title(fig, stage, x=0.05, y=0.93, size=26):
    head, sub = STAGES[stage]
    fig.text(x, y, head, color=INK, fontsize=size, fontweight="bold", va="top")
    fig.text(x, y - 0.055, sub, color=MUTED, fontsize=size * 0.58, va="top")


def stills():
    IMG.mkdir(parents=True, exist_ok=True)
    for stage in (1, 2, 3, 4):
        fig = new_fig(12, 9, 250)
        ax = fig.add_axes([0, -0.04, 1, 1.02], projection="3d")
        ax.view_init(elev=26, azim=AZIM)
        draw(ax, float(stage), label_size=15)
        title(fig, stage)
        fig.savefig(IMG / f"stage{stage}.png", facecolor=BG)
        plt.close(fig)

    # 네 단계 나란히
    fig = new_fig(32, 8.4, 160)
    for i, stage in enumerate((1, 2, 3, 4)):
        ax = fig.add_axes([i / 4, -0.02, 1 / 4, 0.86], projection="3d")
        ax.view_init(elev=26, azim=AZIM)
        draw(ax, float(stage), label_size=10)
        head, sub = STAGES[stage]
        fig.text(i / 4 + 0.015, 0.95, head, color=INK, fontsize=20, fontweight="bold", va="top")
        fig.text(i / 4 + 0.015, 0.895, sub, color=MUTED, fontsize=10.5, va="top", wrap=True)
    fig.savefig(IMG / "overview.png", facecolor=BG)
    plt.close(fig)

    # 대표 이미지 (4단계, 와이드)
    fig = new_fig(16, 9, 250)
    ax = fig.add_axes([0.08, -0.08, 0.92, 1.12], projection="3d")
    ax.view_init(elev=20, azim=AZIM + 5)
    draw(ax, sf.U_MAX, label_size=15)
    fig.text(0.05, 0.9, "Kim Hanbyul", color=INK, fontsize=30, fontweight="bold", va="top")
    fig.text(0.05, 0.835, "Biomedical × Semiconductor × Medical AI", color=MUTED,
             fontsize=17, va="top")
    fig.text(0.05, 0.795, "→ Neuromorphic Semiconductor", color=C["color"],
             fontsize=17, va="top", fontweight="bold")
    fig.savefig(IMG / "hero.png", facecolor=BG)
    plt.close(fig)

    decomposition()


# 영상 시간표: (구간 길이 초, u 시작, u 끝)
SEGMENTS = [(3.5, 0, 1), (1.2, 1, 1), (3.5, 1, 2), (1.2, 2, 2),
            (2.5, 2, 3), (1.6, 3, 3), (4.5, 3, 4), (3.5, 4, 4)]
FPS = 30


def at(t):
    t0 = 0.0
    for d, u0, u1 in SEGMENTS:
        if t <= t0 + d:
            return u0 + (u1 - u0) * (t - t0) / d
        t0 += d
    return SEGMENTS[-1][2]


def video():
    import imageio_ffmpeg
    plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    VID.mkdir(parents=True, exist_ok=True)
    T = sum(d for d, _, _ in SEGMENTS)
    frames = int(T * FPS)

    fig = new_fig(19.2, 10.8, 100)
    ax = fig.add_axes([0.1, -0.08, 0.9, 1.14], projection="3d")

    def update(i):
        t = i / FPS
        u = at(t)
        ax.cla()
        for txt in list(fig.texts):
            txt.remove()
        ax.view_init(elev=18 + 8 * t / T, azim=AZIM - 20 + 30 * t / T)
        draw(ax, u, label_size=14)
        title(fig, min(4, max(1, int(np.ceil(u - 1e-3)))), x=0.04, y=0.92, size=28)
        return []

    anim = animation.FuncAnimation(fig, update, frames=frames, blit=False)
    anim.save(VID / "convergence.mp4",
              writer=animation.FFMpegWriter(fps=FPS, bitrate=3500,
                                            extra_args=["-pix_fmt", "yuv420p"]),
              savefig_kwargs={"facecolor": BG})
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", action="store_true")
    a = ap.parse_args()
    stills()
    if a.video:
        video()

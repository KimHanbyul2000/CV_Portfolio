// 홈페이지의 인터랙티브 3D 곡면.
// 수식은 src/surface.py 와 같다. 한쪽을 고치면 다른 쪽도 고친다.
// 매개변수는 data/surface.json 에서만 읽는다.
//
// 각 기둥이 자기 곡면을 만들고, 전체 곡면 S 는 그 중첩(합)이다. 상호작용(시너지) 항은 없다.
// 좌표: 수식의 (x, y, z) → three.js 의 (x, z, -y)  (three.js 는 y 가 위)
// u (0~4): 0~1 기둥 셋 · 1~2 각 곡면과 중첩 · 2~3 현재의 L_now · 3~4 미래 기대값

export const U_MAX = 4;

export async function mountSurface(container, overlay, cfg) {
  const S = cfg.surface, C = cfg.center, ZS = cfg.z_scale;
  const P = cfg.pillars.map(p => {
    const a = p.angle_deg * Math.PI / 180;
    return { ...p, x: p.radius * Math.cos(a), y: p.radius * Math.sin(a) };
  });

  // ── 수식 (surface.py 와 동일) ───────────────────────────────
  const own = (p, x, y) => {
    const dx = x - p.x, dy = y - p.y, d2 = dx * dx + dy * dy;
    let f = p.height * Math.exp(-d2 / (2 * p.sigma ** 2));
    const lb = p.lobes;
    if (lb) {
      const th = Math.atan2(dy, dx) - lb.phase_deg * Math.PI / 180;
      const dip = lb.depth * (1 - Math.cos(lb.count * th)) / 2;
      f *= 1 - dip * (1 - Math.exp(-d2 / (2 * lb.core ** 2)));
    }
    return f;
  };
  const nowF = (x, y, H) => H * Math.exp(-(x * x + y * y) / (2 * C.sigma ** 2));
  const zf = (x, y, g, H) => ZS * (g * P.reduce((z, p) => z + own(p, x, y), 0) + nowF(x, y, H));
  const ease = v => { v = Math.min(1, Math.max(0, v)); return v * v * (3 - 2 * v); };
  const state = u => ({
    frac: [0, 1, 2].map(i => ease((u - 0.25 * i) / 0.5)),
    g: ease(u - 1),
    H: C.h_now * ease(u - 2) + (C.h_future - C.h_now) * ease(u - 3),
  });
  const rootsOf = p => {
    if (!p.roots) return [];
    const r = p.roots;
    return Array.from({ length: r.count }, (_, k) => {
      const a = 2 * Math.PI * k / r.count + 0.13;
      return { x: r.center[0] + r.radius * Math.cos(a), y: r.center[1] + r.radius * Math.sin(a) };
    });
  };
  // 3D 라벨의 한/영 문구. 연도는 surface.json 의 now_year 한 곳에서 온다
  const YEAR = C.now_year;
  const TXT = {
    ko: { now: `현재 ${YEAR}`, nowShallow: `현재 ${YEAR} — 가장 얕다`, future: "미래 기대값", depth: "깊이 · 전문성" },
    en: { now: `Now ${YEAR}`, nowShallow: `Now ${YEAR} — the shallowest`, future: "expected future", depth: "Depth · expertise" },
  };
  let lang = "ko";
  const OWN_CUT = 0.3;       // 개별 곡면은 자기 꼭짓점의 30% 이상인 영역만 (render.py 와 동일)
  const L1_LABEL_Z = 2.7;    // L1 라벨 최소 높이 (render.py 와 동일)

  // ── 테마별 색 ───────────────────────────────────────────────
  const PAL = {
    dark: { bg: cfg.background, plane: "#2a3350", axis: "#8b93a8", surface: S.color,
            L1: P[0].color, L2: P[1].color, L3: P[2].color, Lnow: C.color },
    light: { ...cfg.light, bg: cfg.light.background },
  };

  // ── 장면 ────────────────────────────────────────────────────
  const THREE = window.THREE;
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
  camera.position.set(2.5, 5.2, 10.2);   // render.py 의 AZIM(-75°)과 같은 방향
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 1.9, 0);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 4; controls.maxDistance = 14;
  // 자동 회전은 끈다 — 라벨이 겹치지 않는 각도(AZIM)로 시작하고, 돌려 보는 건 방문자 몫
  controls.update();

  const V = (x, y, z) => new THREE.Vector3(x, z, -y);
  const tinted = [];   // [material, 팔레트 키] — 테마 전환 시 색을 바꾼다
  const mat = (key, kind = "line", opacity = 1) => {
    const o = { transparent: opacity < 1, opacity };
    const m = kind === "mesh" ? new THREE.MeshBasicMaterial(o)
            : kind === "dash" ? new THREE.LineDashedMaterial({ dashSize: 0.05, gapSize: 0.05, ...o })
            : new THREE.LineBasicMaterial(o);
    tinted.push([m, key]);
    return m;
  };

  // 극좌표 격자
  const nr = S.n_r, nt = S.n_theta;
  const grid = [];
  for (let i = 0; i < nr; i++) for (let j = 0; j <= nt; j++) {
    const r = S.r_max * i / (nr - 1), t = 2 * Math.PI * j / nt;
    grid.push([r * Math.cos(t), r * Math.sin(t)]);
  }
  const idx = (i, j) => i * (nt + 1) + j;
  const segs = [];
  for (let i = 0; i < nr; i++) for (let j = 0; j < nt; j++) segs.push(idx(i, j), idx(i, j + 1));
  for (let j = 0; j < nt; j++) for (let i = 0; i < nr - 1; i++) segs.push(idx(i, j), idx(i + 1, j));

  function gridLines(key, opacity) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(segs.length * 3), 3));
    const l = new THREE.LineSegments(geo, mat(key, "line", opacity));
    scene.add(l);
    return l;
  }
  // zOf 가 null 을 주면 그 선분을 접는다(개별 곡면의 약한 영역을 지울 때)
  function setGrid(lines, zOf) {
    const a = lines.geometry.attributes.position.array;
    for (let n = 0; n < segs.length; n += 2) {
      const [x0, y0] = grid[segs[n]], [x1, y1] = grid[segs[n + 1]];
      let z0 = zOf(x0, y0), z1 = zOf(x1, y1);
      const v0 = V(x0, y0, z0 ?? 0), v1 = (z0 === null || z1 === null) ? v0 : V(x1, y1, z1);
      a.set([v0.x, v0.y, v0.z, v1.x, v1.y, v1.z], n * 3);
    }
    lines.geometry.attributes.position.needsUpdate = true;
  }

  const plane = gridLines("plane", 0.9);
  setGrid(plane, () => 0);
  const surf = gridLines("surface", 0.7);
  const ownGrids = [...P.map(p => gridLines(p.id, 0.75)), gridLines("Lnow", 0.75)];
  let showOwn = false, showSum = true;

  // z축 = 깊이 · 전문성 (정성적, 눈금 없음)
  const AX = [1.9, 1.6], AXH = 4.6;
  if (cfg.depth_axis) {
    const axLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([V(AX[0], AX[1], 0), V(AX[0], AX[1], AXH)]), mat("axis"));
    const head = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.16, 12), mat("axis", "mesh"));
    head.position.copy(V(AX[0], AX[1], AXH));
    scene.add(axLine, head);
  }

  function pillar(key, radius, opacity = 1) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, 1, 20), mat(key, "mesh", opacity));
    scene.add(m);
    return m;
  }
  function setSpan(m, x, y, z0, z1) {
    m.visible = z1 - z0 > 0.001;
    m.scale.y = Math.max(z1 - z0, 1e-4);
    m.position.copy(V(x, y, (z0 + z1) / 2));
  }
  const ball = (key, r, opacity = 1) => {
    const m = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), mat(key, "mesh", opacity));
    scene.add(m); return m;
  };
  const segment = (key, opacity = 1) => {
    const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([V(0, 0, 0), V(0, 0, 1)]), mat(key, "line", opacity));
    scene.add(l); return l;
  };
  const setSeg = (l, a, b) => l.geometry.setFromPoints([a, b]);

  const side = P.map(p => ({ p, body: pillar(p.id, 0.03), cap: ball(p.id, 0.066), roots: rootsOf(p) }));
  // L1 의 뿌리: L2·L3 자리까지 덮는 넓은 바닥에서 여러 가닥이 모여 한 기둥이 된다
  side.forEach(q => {
    if (!q.roots.length) return;
    const r = q.p.roots, ring = [];
    for (let k = 0; k <= 96; k++) {
      const a = 2 * Math.PI * k / 96;
      ring.push(V(r.center[0] + r.radius * Math.cos(a), r.center[1] + r.radius * Math.sin(a), 0));
    }
    q.ring = new THREE.Line(new THREE.BufferGeometry().setFromPoints(ring), mat(q.p.id, "line", 0.55));
    q.strands = new THREE.LineSegments(new THREE.BufferGeometry(), mat(q.p.id, "line", 0.55));
    q.dots = q.roots.map(pt => { const m = ball(q.p.id, 0.022); m.position.copy(V(pt.x, pt.y, 0)); return m; });
    scene.add(q.ring, q.strands);
  });

  const nowSolid = pillar("Lnow", 0.045);
  const nowFuture = pillar("Lnow", 0.045, 0.42);
  const nowCap = ball("Lnow", 0.1);
  const nowMark = ball("Lnow", 0.06);
  const nowLeader = segment("Lnow", 0.8);

  // HTML 라벨 (색은 CSS 변수 --k 로 받아 테마를 따른다)
  const label = (html, key) => {
    const el = document.createElement("div");
    el.className = "lbl"; el.innerHTML = html; el.dataset.key = key;
    overlay.appendChild(el);
    return el;
  };
  side.forEach((q, i) => {
    const sub = q.roots.length ? `<br><small>${q.p.roots.fields.join(" · ")}</small>` : "";
    q.lbl = label(`<i>L<sub>${i + 1}</sub></i> ${q.p.en}<br>${q.p.ko}${sub}`, q.p.id);
    // L1 은 뒤쪽 가운데라 L_now 를 가리므로 왼쪽 뒤·더 높이 비킨다 (render.py 와 같은 규칙)
    q.la = Math.atan2(q.p.y, q.p.x) + (i === 0 ? 38 * Math.PI / 180 : 0);
    q.align = i === 0 ? "right" : "center";
  });
  const cName = `<i>L<sub>now</sub></i> ${C.en}<br>${C.ko}`;
  const cLbl = label("", "Lnow");
  const markLbl = label("", "Lnow"); markLbl.classList.add("small");
  const sLbl = label("<i>S</i>", "surface");
  const axLbl = label("", "axis"); axLbl.classList.add("axis");
  axLbl.at = cfg.depth_axis ? V(AX[0], AX[1], AXH + 0.25) : null;

  let u = U_MAX;
  function apply() {
    const { frac, g, H } = state(u);
    surf.visible = showSum && g > 0.001;
    surf.material.opacity = 0.2 + 0.5 * g;
    if (surf.visible) setGrid(surf, (x, y) => zf(x, y, g, H));

    // 개별 곡면 (선택 표시)
    P.forEach((p, i) => {
      const gr = ownGrids[i];
      gr.visible = showOwn && g > 0.001;
      if (gr.visible) setGrid(gr, (x, y) => { const f = own(p, x, y); return f >= OWN_CUT * p.height ? ZS * g * f : null; });
    });
    const gn = ownGrids[3];
    gn.visible = showOwn && H > 0.01;
    if (gn.visible) setGrid(gn, (x, y) => { const f = nowF(x, y, H); return f >= OWN_CUT * H ? ZS * f : null; });

    side.forEach((q, i) => {
      const top = ZS * q.p.height * frac[i];
      setSpan(q.body, q.p.x, q.p.y, 0, top);
      q.cap.visible = top > 0.001; q.cap.position.copy(V(q.p.x, q.p.y, top));
      if (q.roots.length) {
        const on = top > 0.001;
        q.ring.visible = q.strands.visible = on;
        q.ring.material.opacity = q.strands.material.opacity = 0.55 * frac[i];
        q.dots.forEach(d => { d.visible = on; });
        q.strands.geometry.setFromPoints(q.roots.flatMap(pt =>
          [V(pt.x, pt.y, 0), V(q.p.x, q.p.y, top * q.p.roots.join)]));
      }
      const lx = 1.7 * Math.cos(q.la), ly = 1.7 * Math.sin(q.la);
      let zl = Math.max(top, zf(lx, ly, g, H)) + 0.2;
      if (i === 0) zl = Math.max(zl, L1_LABEL_Z);
      q.lbl.at = frac[i] > 0.6 ? V(lx, ly, zl) : null;
    });

    // L_now: 현재 높이까지 실선, 그 위(미래 기대값)는 반투명
    const hn = ZS * C.h_now, ht = ZS * H;
    setSpan(nowSolid, 0, 0, 0, Math.min(ht, hn));
    setSpan(nowFuture, 0, 0, hn, Math.max(ht, hn));
    nowCap.visible = H > 0.01; nowCap.position.copy(V(0, 0, ht));
    const future = ht > hn + 0.01;
    nowMark.visible = future; nowMark.position.copy(V(0, 0, hn));
    markLbl.at = future ? V(0.18, -0.18, hn) : null;
    const top = H > (C.h_now + C.h_future) / 2;
    nowLeader.visible = H > C.h_now * 0.5 && !top;
    setSeg(nowLeader, V(0, -1.75, 0.05), V(0, 0, ht));
    if (H > C.h_now * 0.5) {
      cLbl.innerHTML = cName + (top ? `<br>${TXT[lang].future}` : `<br><small>${TXT[lang].nowShallow}</small>`);
      cLbl.at = top ? V(0, 0, zf(0, 0, g, H) + 0.25) : V(0, -1.75, 0);
      cLbl.below = !top;
    } else cLbl.at = null;

    markLbl.textContent = TXT[lang].now;
    axLbl.textContent = TXT[lang].depth;
    const e = [P[1].x * 1.95, P[1].y * 1.95];
    sLbl.at = showSum && g > 0.6 ? V(e[0], e[1], zf(e[0], e[1], g, H) + 0.1) : null;
  }

  function placeLabels() {
    const w = renderer.domElement.clientWidth, h = renderer.domElement.clientHeight;
    const all = [...side.map(q => [q.lbl, q.lbl.at, q.align]), [cLbl, cLbl.at, "center"],
                 [markLbl, markLbl.at, "left"], [sLbl, sLbl.at, "center"], [axLbl, axLbl.at, "center"]];
    all.forEach(([el, at, align]) => {
      if (!at) { el.style.opacity = 0; return; }
      const p = at.clone().project(camera);
      const tx = align === "right" ? "-100%" : align === "left" ? "0%" : "-50%";
      const ty = el === cLbl && cLbl.below ? "0%" : el === markLbl ? "-50%" : "-100%";
      el.style.opacity = 1;
      el.style.transform = `translate(${tx},${ty}) translate(${(p.x + 1) / 2 * w}px,${(1 - p.y) / 2 * h}px)`;
    });
  }

  function setTheme(mode) {
    const pal = PAL[mode === "light" ? "light" : "dark"];
    renderer.setClearColor(pal.bg);
    tinted.forEach(([m, key]) => m.color.set(pal[key]));
    container.dataset.theme = mode === "light" ? "light" : "dark";
    overlay.querySelectorAll(".lbl").forEach(el => el.style.setProperty("--k", pal[el.dataset.key]));
  }

  function resize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = w + "px";
    renderer.domElement.style.height = h + "px";
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  resize();
  setTheme("dark");
  apply();

  (function loop() {
    controls.update();
    renderer.render(scene, camera);
    placeLabels();
    requestAnimationFrame(loop);
  })();

  return {
    setU(v) { u = v; apply(); },
    getU: () => u,
    // 곡면 표시: sum = 전체(합), own = 개별 곡면
    setSurfaces({ sum, own }) { showSum = sum; showOwn = own; apply(); },
    setTheme,
    setLang(v) { lang = v === "en" ? "en" : "ko"; apply(); },
  };
}

// 이력 본문 렌더러 — 홈페이지(index.html)의 "이력" 절과 인쇄용 이력서(cv.html → PDF)가 이 함수 하나를 쓴다.
// 그래서 두 곳의 정보는 항상 같다 (본인 지시 2026-10-03). 데이터는 data/profile.json 에서만 온다.
// 모양은 web/cv.css. 색은 각 페이지의 --ink · --muted · --line · --panel · --c-in · --c-l1~3 을 쓴다.

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

const LABEL = {
  ko: {
    current: "현재", project: "국가 R&D 과제", pi: "과제책임자", edu: "학력 · 교육", minor: "부전공",
    gpa: "누적 GPA", pct: "백분위", major: "전공", credits: "학점", honors: "우등", sems: "개 학기",
    courses: "주요 이수 과목", schol: "장학", proj: "프로젝트", skills: "기술", act: "대외 활동", mil: "병역",
  },
  en: {
    current: "Current position", project: "National R&D project", pi: "PI", edu: "Education & training", minor: "Minor",
    gpa: "Cumulative GPA", pct: "percentile", major: "major", credits: "credits", honors: "Academic honors", sems: " semesters",
    courses: "Key coursework", schol: "Scholarships", proj: "Projects", skills: "Skills", act: "Activities", mil: "Military service",
  },
};
const COLOR = { L1: "var(--c-l1)", L2: "var(--c-l2)", L3: "var(--c-l3)" };

export function cvHTML(pf, L) {
  const S = LABEL[L], T = (o, k) => o[`${k}_${L}`];
  const c = pf.current, pj = c.project, e = pf.education, g = e.gpa;
  const row = (when, body) => `<div class="cv-row"><div class="cv-when">${esc(when)}</div><div>${body}</div></div>`;
  const sec = (title, body) => `<div class="cv-sec"><h3 class="cv-h">${title}</h3>${body}</div>`;
  const l3 = pf.pillars.find(p => p.id === "L3");
  const military = pf.timeline.find(t => t.when.startsWith("2021"));
  const logo = c.logo?.src ? `<img class="cv-logo" src="${esc(c.logo.src)}" alt="${esc(T(c.logo, "alt"))}">` : "";

  return [
    sec(S.current, row(T(c, "period"), `
      <div class="cv-cur">${logo}<div>
        <div class="cv-t">${esc(c.org)} · ${esc(T(c, "role"))}</div>
        <p>${esc(T(c, "detail"))}</p></div></div>
      ${pj ? `<div class="cv-box">
        <div>${S.project} · ${esc(T(pj, "role"))}</div>
        <div class="cv-t">${esc(T(pj, "title"))}</div>
        <div>${esc(T(pj, "program"))} · ${esc(pj.number)}</div>
        <div>${S.pi}: ${esc(T(pj, "pi"))} · ${esc(T(pj, "period"))}</div></div>` : ""}`)),

    sec(S.edu,
      row(T(e, "period"), `
        <div class="cv-t"><span class="cv-dot" style="background:${COLOR.L1}"></span>${esc(T(e, "school"))} — ${esc(T(e, "degree"))}</div>
        <div class="cv-w">${esc(T(e, "dept"))}</div>
        <div class="cv-w"><span class="cv-dot" style="background:${COLOR.L2}"></span>${S.minor}: ${esc(T(e, "minor"))}</div>
        <div class="cv-gpa"><b>${S.gpa} ${g.overall} / ${g.scale}</b> (${S.pct} ${g.pct}) · ${S.major} ${g.major} (${g.major_pct}) · ${S.minor.toLowerCase()} ${g.minor} (${g.minor_pct}) · ${g.credits} ${S.credits}</div>
        <div class="cv-w">${S.honors} ${e.honors.length}${S.sems} — ${e.honors.map(esc).join(" · ")}</div>`)
      + (l3 ? row(pf.timeline.find(t => t.pillar === "L3")?.when ?? "", `
        <div class="cv-t"><span class="cv-dot" style="background:${COLOR.L3}"></span>${esc(T(l3, "title"))}</div>
        <div class="cv-w">${esc(T(l3, "where"))}</div>`) : "")
      + row(S.courses, e.courses.map(grp => `
        <div class="cv-cg"><span class="cv-cl">${esc(grp[L])}</span><span class="cv-chips">${grp.list.map(x => `<span class="cv-chip">${esc(x)}</span>`).join("")}</span></div>`).join(""))),

    sec(S.schol, e.scholarships.map(s => row(s.when,
      `<div class="${s.highlight ? "cv-hl" : ""}">${s.highlight ? "★ " : ""}${esc(s[L])}</div>`)).join("")),

    sec(S.proj, pf.projects.map(p => {
      const name = esc(p[`name_${L}`] ?? p.name);
      return row(p.when ?? "", `<div class="cv-t">${p.href ? `<a href="${esc(p.href)}">${name}</a>` : name}</div><p>${esc(p[L])}</p>`);
    }).join("")),

    sec(S.skills, pf.pillars.map(p => row(T(p, "title").split(/\s[—(]/)[0],
      `<span class="cv-chips">${T(p, "skills").map(s => `<span class="cv-chip">${esc(s)}</span>`).join("")}</span>`)).join("")),

    sec(S.act, e.activities.map(a => row(a.when, esc(a[L]))).join("")),

    military ? sec(S.mil, row(military.when, esc(military[L]))) : "",
  ].join("");
}

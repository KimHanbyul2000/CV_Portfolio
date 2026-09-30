# 배포 — GitHub Pages (내부)

이 저장소의 홈페이지(`index.html`)가 어떻게 공개 주소로 서비스되는지, 무엇을 어떻게 켰는지 적는다.

| | |
|---|---|
| 공개 주소 | https://kimhanbyul2000.github.io/CV_Portfolio/ |
| 저장소 | https://github.com/KimHanbyul2000/CV_Portfolio (공개) |
| 배포 원본 | `main` 브랜치의 루트(`/`) |
| 켠 날짜 | 2026-09-30 |

## GitHub Pages 가 무엇을 하나

저장소의 정해진 브랜치·폴더에 있는 파일을 **그대로** 정적 웹사이트로 내보낸다. 빌드 서버나 백엔드는
없다. `index.html` 이 첫 화면이 되고, 그 옆의 `data/*.json`·`web/surface.js`·`assets/` 는 같은 주소
아래 경로로 열린다. 그래서 `index.html` 이 `fetch("data/profile.json")` 으로 읽는 구조가 그대로 동작한다.

사용자 계정 이름 저장소(`KimHanbyul2000.github.io`)는 `https://kimhanbyul2000.github.io/` 루트를 쓰고,
이 저장소 같은 **일반 저장소는 그 아래 `/<저장소 이름>/` 경로**를 쓴다. 이름을 바꾸면 주소도 바뀐다.

## 어떻게 켰나

웹 화면(Settings → Pages)에서 켜도 되지만, 이번엔 명령줄(GitHub CLI)로 API 를 한 번 호출했다.

```bash
# 1. 공개 저장소를 만들고 현재 폴더를 올린다
gh repo create KimHanbyul2000/CV_Portfolio --public --source . --remote origin --push

# 2. Pages 를 켠다 — main 브랜치의 루트를 배포 원본으로
gh api -X POST repos/KimHanbyul2000/CV_Portfolio/pages \
  -f "source[branch]=main" -f "source[path]=/"
```

웹 화면으로 같은 일을 하려면: 저장소 **Settings → Pages → Build and deployment → Source: Deploy from a
branch → Branch: `main` / `/ (root)` → Save**.

무료 계정에서 Pages 는 **공개 저장소**에서만 쓸 수 있다. 저장소를 비공개로 바꾸면 사이트가 내려간다.

## 켠 뒤 확인한 것

켜고 나면 GitHub 가 첫 배포를 만드는 데 1~2분 걸린다. 그동안 주소는 404 다.

```bash
gh api repos/KimHanbyul2000/CV_Portfolio/pages --jq .status          # building → built
curl -s -o /dev/null -w "%{http_code}\n" https://kimhanbyul2000.github.io/CV_Portfolio/   # 200
```

그다음 브라우저로 열어 3D 화면(캔버스)이 뜨는지, 곡면 버튼이 동작하는지 봤다. 로컬 서버에서 되던 게
배포에서 안 되는 흔한 원인은 **절대 경로**(`/data/...`)다 — 배포 주소가 `/CV_Portfolio/` 아래라서
루트 기준 경로는 깨진다. 이 저장소는 전부 상대 경로(`data/...`)를 쓴다.

## 이후 갱신

`main` 에 푸시하면 Pages 가 자동으로 다시 배포한다(1~2분). 따로 할 일은 없다.

## 관련 파일

| 파일 | 역할 |
|---|---|
| `.nojekyll` | GitHub Pages 는 기본으로 Jekyll(정적 사이트 생성기)을 거치는데, Jekyll 은 `_` 로 시작하는 파일·폴더를 빼 버린다. 이 빈 파일이 있으면 Jekyll 을 건너뛰고 파일을 그대로 서빙한다. **지우지 않는다** |

## 첫 푸시가 실패했던 일 (2026-09-30)

첫 푸시(파일 약 22MB, 영상 11MB 포함)가 `HTTP 400 ... the remote end hung up unexpectedly` 로 실패했다.
GitHub 의 파일 크기 제한(파일당 100MB) 문제가 아니라, git 이 HTTPS 로 한 번에 보내는 버퍼 기본값(1MB)을
넘는 큰 요청에서 생기는 문제다. **이 저장소에만** 버퍼를 키워 해결했다.

```bash
git config http.postBuffer 157286400     # 150MB. --global 이 없으므로 이 저장소의 .git/config 에만 기록
git push -u origin main
```

- 이 설정은 `.git/config` 에만 있고 **커밋되지 않는다**(원격에도 안 올라감). 다른 저장소, 다른 PC 에는
  영향이 없다. 확인: `git config --show-origin --get http.postBuffer` → `file:.git/config`.
- 이 저장소를 새로 clone 한 곳에서 큰 파일을 다시 올릴 일이 있으면 같은 명령을 한 번 더 실행한다.

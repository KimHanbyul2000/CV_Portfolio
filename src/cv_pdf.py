"""PDF 이력서 만들기 — cv.html 을 헤드리스 Chromium 으로 인쇄해 assets/cv/ 에 한·영 두 개를 만든다.

내용은 data/profile.json 에서 나온다(cv.html 이 읽는다). profile.json 을 고쳤으면 다시 돌린다.

    pip install playwright && python3 -m playwright install chromium   # 처음 한 번
    python3 src/cv_pdf.py                                              # → assets/cv/KimHanbyul_CV_{ko,en}.pdf

글꼴(Noto Sans KR)은 Google Fonts 에서 받으므로 인터넷이 되는 곳에서 돌린다.
"""
import argparse
import functools
import http.server
import pathlib
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "cv"
LANGS = ("ko", "en")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    """저장소 루트를 임시 로컬 서버로 연다 — cv.html 이 fetch 로 profile.json 을 읽기 때문(file:// 로는 안 된다)."""
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def build(chromium=None, setup=None):
    """언어별 PDF 를 만들고 경로 목록을 돌려준다. setup(page) 은 페이지를 열기 전에 부른다(테스트용 훅)."""
    OUT.mkdir(parents=True, exist_ok=True)
    srv = serve()
    port = srv.server_address[1]
    paths = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=chromium)
            page = browser.new_page()
            if setup:
                setup(page)
            for lang in LANGS:
                page.goto(f"http://127.0.0.1:{port}/cv.html?lang={lang}")
                page.wait_for_selector("body[data-ready='1']", timeout=30000)
                path = OUT / f"KimHanbyul_CV_{lang}.pdf"
                page.pdf(path=str(path), print_background=True, prefer_css_page_size=True)
                paths.append(path)
            browser.close()
    finally:
        srv.shutdown()
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chromium", help="Chromium 실행 파일 경로 (기본: playwright 가 설치한 것)")
    args = ap.parse_args()
    for path in build(args.chromium):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()

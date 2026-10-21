"""Stage 1: live YouTube autocomplete, using only the Python standard library."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
import webbrowser

WEB_ROOT = Path(__file__).with_name("web")
SOURCE = "YouTube 자동완성"
MAX_RESPONSE_BYTES = 256_000


class RecommendationError(Exception):
    """An upstream problem that should be shown without invented results."""


def clean_query(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip()
    if not value or len(value) > 100 or any(ord(c) < 32 for c in value):
        raise ValueError("게임 이름이나 주제를 1~100자로 입력해 주세요.")
    return value


def parse_suggestions(payload: object, query: str) -> list[str]:
    if (
        not isinstance(payload, list)
        or len(payload) < 2
        or not isinstance(payload[0], str)
        or payload[0] != query
        or not isinstance(payload[1], list)
        or any(not isinstance(item, str) for item in payload[1])
    ):
        raise RecommendationError("추천 데이터 형식이 변경되었습니다. 잠시 후 다시 시도해 주세요.")
    seen = set()
    suggestions = []
    for raw in payload[1]:
        term = unicodedata.normalize("NFKC", raw).strip()
        key = re.sub(r"\s+", " ", term).casefold()
        if not term or len(term) > 200 or any(ord(c) < 32 for c in term) or key in seen:
            continue
        seen.add(key)
        suggestions.append(term)
        if len(suggestions) == 10:
            break
    return suggestions


def recommend(query: str) -> dict:
    query = clean_query(query)
    url = "https://suggestqueries.google.com/complete/search?" + urlencode(
        {"client": "firefox", "ds": "yt", "q": query, "hl": "ko", "gl": "KR"}
    )
    request = Request(url, headers={"User-Agent": "24HReplier/0.1", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=12) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise RecommendationError("추천 응답이 너무 큽니다. 다른 검색어로 시도해 주세요.")
            charset = response.headers.get_content_charset() or "utf-8"
            payload = json.loads(raw.decode(charset))
        terms = parse_suggestions(payload, query)
    except RecommendationError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError):
        raise RecommendationError("YouTube 추천에 연결하지 못했습니다. 인터넷 연결을 확인하고 다시 시도해 주세요.") from None
    except (ValueError, UnicodeError, LookupError):
        raise RecommendationError("추천 응답을 읽지 못했습니다. 잠시 후 다시 시도해 주세요.") from None
    return {
        "query": query,
        "source": SOURCE,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "suggestions": [
            {"term": term, "search_url": "https://www.youtube.com/results?" + urlencode({"search_query": term})}
            for term in terms
        ],
        "notice": "자동완성 제안이며 검색량·조회수·인기 순위를 뜻하지 않습니다.",
    }



# These are discovery entry points, not invented recommendations or trend claims.
DISCOVERY_SEEDS = (
    "스팀 신작 게임", "게임 웃긴 장면", "공포 게임", "게임 보스 공략",
    "인디 게임 추천", "게임 챌린지", "생존 게임", "게임 업데이트",
    "오픈월드 게임", "게임 버그", "협동 게임", "게임 스토리",
    "게임 초보 공략", "추억의 게임", "게임 숨겨진 요소", "무료 게임 추천",
    "로그라이크 게임", "게임 명장면", "시뮬레이션 게임", "게임 리뷰",
)
FOCUSED_SUFFIXES = ("공략", "웃긴 장면", "초보", "보스", "업데이트", "챌린지",
                    "스토리", "버그", "숨겨진 요소", "리뷰", "직업", "팁")


def term_key(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()


def discover_topics(query="", excluded=(), cursor=0, provider=recommend):
    from concurrent.futures import ThreadPoolExecutor
    if not isinstance(query, str):
        raise ValueError("관심 게임을 문자로 입력해 주세요.")
    query = clean_query(query) if query.strip() else ""
    if not isinstance(cursor, int) or isinstance(cursor, bool) or not 0 <= cursor <= 1_000_000:
        raise ValueError("추천 순서를 읽지 못했습니다. 화면을 새로고침해 주세요.")
    if (not isinstance(excluded, (list, tuple)) or len(excluded) > 300
            or any(not isinstance(term, str) or len(term) > 200 for term in excluded)):
        raise ValueError("추천 이력 형식이 잘못되었습니다.")
    seeds = tuple(query + " " + suffix for suffix in FOCUSED_SUFFIXES) if query and query != "게임" else DISCOVERY_SEEDS
    selected = [seeds[(cursor * 4 + offset) % len(seeds)] for offset in range(4)]

    def fetch(seed):
        try:
            return seed, provider(seed), None
        except RecommendationError as exc:
            return seed, None, str(exc)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, selected))
    succeeded = [(seed, data["suggestions"]) for seed, data, error in results if data is not None]
    failed = [seed for seed, data, error in results if data is None]
    if not succeeded:
        raise RecommendationError("YouTube 추천을 가져오지 못했습니다. 잠시 후 다시 눌러주세요.")
    seen = {term_key(term) for term in excluded}
    suggestions = []
    # Interleave sources so one popular seed cannot fill the whole screen.
    for index in range(10):
        for seed, items in succeeded:
            if index >= len(items):
                continue
            item = items[index]
            key = term_key(item["term"])
            if key in seen:
                continue
            seen.add(key)
            suggestions.append({**item, "discovered_from": seed})
            if len(suggestions) == 12:
                break
        if len(suggestions) == 12:
            break
    return {
        "query": query,
        "source": SOURCE,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "suggestions": suggestions,
        "queried_seeds": selected,
        "next_cursor": (cursor + 1) % 1_000_001,
        "failed_sources": len(failed),
        "notice": "여러 게임 분야의 자동완성 제안을 모았습니다. 검색량·조회수 순위는 아닙니다.",
    }



def make_handler(provider=recommend):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Do not log queries or user-provided text.
            pass

        def send_data(self, status: int, body: bytes, content_type: str):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def json_response(self, status: int, data: dict):
            self.send_data(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            allowed_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if self.headers.get("Host") not in allowed_hosts:
                self.json_response(403, {"error": "로컬 주소로 접속해 주세요."})
                return
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://{host}" for host in allowed_hosts}:
                self.json_response(403, {"error": "다른 사이트에서 보낸 요청은 허용하지 않습니다."})
                return
            parsed = urlsplit(self.path)
            static = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            if parsed.path in static:
                filename, mime = static[parsed.path]
                self.send_data(200, (WEB_ROOT / filename).read_bytes(), mime)
                return
            if parsed.path == "/api/recommendations":
                values = parse_qs(parsed.query, keep_blank_values=True).get("q", [])
                if len(values) != 1:
                    self.json_response(400, {"error": "검색 기준을 하나 입력해 주세요."})
                    return
                try:
                    result = provider(clean_query(values[0]))
                    self.json_response(200, result)
                except ValueError as exc:
                    self.json_response(400, {"error": str(exc)})
                except RecommendationError as exc:
                    self.json_response(502, {"error": str(exc)})
                except Exception:
                    self.json_response(500, {"error": "추천 처리 중 오류가 발생했습니다. 다시 시도해 주세요."})
                return
            self.json_response(404, {"error": "찾을 수 없는 페이지입니다."})

        def do_POST(self):
            if urlsplit(self.path).path != "/api/topics":
                self.json_response(405, {"error": "현재 버전에는 게시 기능이 없습니다."})
                return
            hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if self.headers.get("Host") not in hosts or (
                self.headers.get("Origin") and self.headers.get("Origin") not in {f"http://{host}" for host in hosts}
            ):
                self.json_response(403, {"error": "로컬 화면에서 요청해 주세요."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    raise ValueError("요청 크기가 올바르지 않습니다.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("요청 형식이 올바르지 않습니다.")
                result = discover_topics(payload.get("query", ""), payload.get("excluded", []),
                                         payload.get("cursor", 0), provider)
                self.json_response(200, result)
            except (ValueError, UnicodeError) as exc:
                self.json_response(400, {"error": "추천 요청을 읽지 못했습니다. 입력을 확인해 주세요."})
            except RecommendationError as exc:
                self.json_response(502, {"error": str(exc)})
            except Exception:
                self.json_response(500, {"error": "추천 처리 중 오류가 발생했습니다. 다시 시도해 주세요."})

    return Handler


def main():
    parser = argparse.ArgumentParser(description="24HReplier 검색어 추천")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler())
    except OSError:
        parser.exit(1, "실행할 포트를 사용할 수 없습니다. --port로 다른 포트를 선택해 주세요.\n")
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"24HReplier: {url}", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

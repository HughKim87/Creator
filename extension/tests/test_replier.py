"""Contract tests for upstream data integrity and the read-only local app."""
import json
from http.server import ThreadingHTTPServer
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from replier.server import RecommendationError, clean_query, make_handler, parse_suggestions


class SuggestionsTests(unittest.TestCase):
    def test_realistic_response_keeps_order_and_deduplicates(self):
        payload = ["게임", ["게임 추천", "게임 추천", " 게임 리뷰 ", "게임 공략"], [], {}]
        self.assertEqual(parse_suggestions(payload, "게임"), ["게임 추천", "게임 리뷰", "게임 공략"])

    def test_upstream_format_or_query_mismatch_is_not_a_result(self):
        for payload in ({"suggestions": ["가짜"]}, ["다른검색", ["추천"]], ["게임", [123]]):
            with self.subTest(payload=payload), self.assertRaises(RecommendationError):
                parse_suggestions(payload, "게임")

    def test_empty_upstream_results_stay_empty(self):
        self.assertEqual(parse_suggestions(["게임", []], "게임"), [])

    def test_invalid_input(self):
        for query in ("", "   ", "x" * 101, "게임\n주제"):
            with self.subTest(query=query), self.assertRaises(ValueError):
                clean_query(query)


class ServerTests(unittest.TestCase):
    def setUp(self):
        def provider(query):
            if query == "오류":
                raise RecommendationError("upstream unavailable")
            return {"query": query, "suggestions": [{"term": "<script>text</script>"}]}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(provider))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_api_validation_and_upstream_failure(self):
        for suffix, code in (("", 400), ("?q=", 400), ("?q=a&q=b", 400), ("?q=%EC%98%A4%EB%A5%98", 502)):
            with self.subTest(suffix=suffix), self.assertRaises(HTTPError) as error:
                urlopen(self.url + "/api/recommendations" + suffix)
            self.assertEqual(error.exception.code, code)

    def test_stage_one_has_no_write_endpoint(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.url + "/api/publish", data=b"{}", method="POST"))
        self.assertEqual(error.exception.code, 405)

    def test_cross_site_request_is_blocked(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.url + "/api/recommendations?q=game", headers={"Origin": "https://example.com"}))
        self.assertEqual(error.exception.code, 403)

    def test_serves_ui_and_unicode_json_without_html_interpolation(self):
        with urlopen(self.url + "/") as response:
            self.assertIn("다른 게임 주제 추천받기", response.read().decode())
        with urlopen(self.url + "/api/recommendations?q=game") as response:
            self.assertEqual(json.load(response)["suggestions"][0]["term"], "<script>text</script>")



class DiscoveryTests(unittest.TestCase):
    @staticmethod
    def provider(seed):
        from urllib.parse import urlencode
        return {"suggestions": [
            {"term": seed + " 실제추천" + str(i), "search_url": "https://www.youtube.com/results?" + urlencode({"search_query": seed + str(i)})}
            for i in range(5)
        ]}

    def test_next_click_changes_categories_and_never_reuses_seen_terms(self):
        from replier.server import discover_topics
        first = discover_topics(provider=self.provider)
        terms = [item["term"] for item in first["suggestions"]]
        second = discover_topics(excluded=terms, cursor=first["next_cursor"], provider=self.provider)
        self.assertFalse(set(terms) & {item["term"] for item in second["suggestions"]})
        self.assertFalse(set(first["queried_seeds"]) & set(second["queried_seeds"]))
        self.assertEqual(len({item["discovered_from"] for item in first["suggestions"]}), 4)
        # After the category rotation wraps, prior results must still be excluded.
        wrapped = discover_topics(excluded=terms, cursor=5, provider=self.provider)
        self.assertFalse(set(terms) & {item["term"] for item in wrapped["suggestions"]})

    def test_focused_query_and_empty_results_never_invent_topics(self):
        from replier.server import discover_topics
        result = discover_topics("디아블로", provider=lambda seed: {"suggestions": []})
        self.assertEqual(result["suggestions"], [])
        self.assertTrue(all(seed.startswith("디아블로 ") for seed in result["queried_seeds"]))

    def test_all_upstream_failures_remain_errors(self):
        from replier.server import discover_topics
        def failure(seed):
            raise RecommendationError("offline")
        with self.assertRaises(RecommendationError):
            discover_topics(provider=failure)

    def test_partial_failure_returns_only_verified_sources(self):
        from replier.server import discover_topics, DISCOVERY_SEEDS
        def partial(seed):
            if seed == DISCOVERY_SEEDS[0]:
                raise RecommendationError("offline")
            return self.provider(seed)
        result = discover_topics(provider=partial)
        self.assertEqual(result["failed_sources"], 1)
        self.assertNotIn(DISCOVERY_SEEDS[0], {item["discovered_from"] for item in result["suggestions"]})



if __name__ == "__main__":
    unittest.main()

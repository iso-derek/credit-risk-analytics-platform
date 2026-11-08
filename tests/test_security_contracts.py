import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from unittest.mock import Mock, patch

from data_sources import MAX_DOWNLOAD_BYTES, UCI_URL, _download_bounded


class SecurityContractTests(unittest.TestCase):
    def test_public_source_is_https(self):
        self.assertTrue(UCI_URL.startswith("https://"))
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            _download_bounded("http://example.test/data.csv")

    @patch("data_sources.requests.get")
    def test_content_length_rejects_oversized_response_before_streaming(self, get):
        response = Mock()
        response.headers = {"Content-Length": str(MAX_DOWNLOAD_BYTES + 1)}
        get.return_value = response
        with self.assertRaisesRegex(ValueError, "large"):
            _download_bounded()
        response.iter_content.assert_not_called()
        response.close.assert_called_once()
        get.assert_called_once_with(UCI_URL, timeout=(5, 30), stream=True)

    @patch("data_sources.requests.get")
    def test_streaming_cap_rejects_missing_or_false_content_length(self, get):
        response = Mock()
        response.headers = {}
        response.iter_content.return_value = [b"a" * 6, b"b" * 5]
        get.return_value = response
        with self.assertRaisesRegex(ValueError, "large"):
            _download_bounded(max_bytes=10)
        response.close.assert_called_once()

    @patch("data_sources.requests.get")
    def test_invalid_content_length_falls_back_to_streaming_cap(self, get):
        response = Mock()
        response.headers = {"Content-Length": "not-a-number"}
        response.iter_content.return_value = [b"abc", b"def"]
        get.return_value = response
        self.assertEqual(_download_bounded(max_bytes=6), b"abcdef")
        response.close.assert_called_once()

    @patch("data_sources.requests.get")
    def test_bounded_stream_returns_exact_content(self, get):
        response = Mock()
        response.headers = {"Content-Length": "6"}
        response.iter_content.return_value = [b"abc", b"", b"def"]
        get.return_value = response
        self.assertEqual(_download_bounded(max_bytes=6), b"abcdef")
        response.raise_for_status.assert_called_once()
        response.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

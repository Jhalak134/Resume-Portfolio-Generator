import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai import ConfigError, get_resume_json
import ai.gemini as gemini_module


class TestMissingApiKey(unittest.TestCase):
    """Brief test case: 'Missing API key -> Show a configuration error.'"""

    def test_missing_api_key_raises_config_error(self):
        with patch.object(gemini_module, "API_KEY", ""):
            with self.assertRaises(ConfigError) as ctx:
                get_resume_json("John Doe\nSoftware Engineer\n" + "x" * 50)
        self.assertIn("google_api", str(ctx.exception))

    def test_missing_api_key_never_calls_gemini(self):
        # The client should never even be constructed when the key is
        # missing, so no network call happens.
        with patch.object(gemini_module, "API_KEY", ""):
            with patch("ai.gemini.genai.Client") as mock_client_cls:
                with self.assertRaises(ConfigError):
                    get_resume_json("John Doe\nSoftware Engineer\n" + "x" * 50)
                mock_client_cls.assert_not_called()


class TestInvalidJsonResponse(unittest.TestCase):
    """Brief test case: 'Invalid JSON response -> Show a clear error and
    stop safely.'"""

    def _make_fake_client(self, response_text):
        fake_response = MagicMock()
        fake_response.text = response_text
        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = fake_response
        return fake_client

    def test_non_json_response_raises_value_error(self):
        fake_client = self._make_fake_client("This is not JSON at all.")
        with patch.object(gemini_module, "API_KEY", "fake-key-for-test"):
            with patch.object(gemini_module, "_get_client", return_value=fake_client):
                with self.assertRaises(ValueError) as ctx:
                    get_resume_json("John Doe\nSoftware Engineer\n" + "x" * 50)
        self.assertIn("did not return valid JSON", str(ctx.exception))

    def test_truncated_json_raises_value_error(self):
        # Simulates a response cut off mid-object.
        fake_client = self._make_fake_client('{"name": "John Doe", "skills": [')
        with patch.object(gemini_module, "API_KEY", "fake-key-for-test"):
            with patch.object(gemini_module, "_get_client", return_value=fake_client):
                with self.assertRaises(ValueError):
                    get_resume_json("John Doe\nSoftware Engineer\n" + "x" * 50)

    def test_code_fenced_valid_json_still_parses(self):
        # Gemini sometimes wraps JSON in ```json fences despite instructions
        # not to -- this should still parse successfully, not raise.
        fake_client = self._make_fake_client('```json\n{"name": "John Doe"}\n```')
        with patch.object(gemini_module, "API_KEY", "fake-key-for-test"):
            with patch.object(gemini_module, "_get_client", return_value=fake_client):
                data = get_resume_json("John Doe\nSoftware Engineer\n" + "x" * 50)
        self.assertEqual(data.get("name"), "John Doe")


class TestApiFailure(unittest.TestCase):
    """Brief test case: 'API failure -> Handle the failure without
    crashing.' (i.e. it should raise a catchable exception, not hang or
    crash the interpreter -- callers like main.py and app.py wrap this in
    their own try/except.)"""

    def test_network_error_propagates_as_exception(self):
        fake_client = MagicMock()
        fake_client.models.generate_content.side_effect = ConnectionError(
            "Simulated network failure"
        )
        with patch.object(gemini_module, "API_KEY", "fake-key-for-test"):
            with patch.object(gemini_module, "_get_client", return_value=fake_client):
                with self.assertRaises(ConnectionError):
                    get_resume_json("John Doe\nSoftware Engineer\n" + "x" * 50)

    def test_generic_api_exception_propagates(self):
        fake_client = MagicMock()
        fake_client.models.generate_content.side_effect = RuntimeError(
            "500 Internal Server Error from Gemini"
        )
        with patch.object(gemini_module, "API_KEY", "fake-key-for-test"):
            with patch.object(gemini_module, "_get_client", return_value=fake_client):
                with self.assertRaises(RuntimeError):
                    get_resume_json("John Doe\nSoftware Engineer\n" + "x" * 50)


if __name__ == "__main__":
    unittest.main()
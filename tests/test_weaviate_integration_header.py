import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
import weaviate  # noqa: E402
from app.database.weaviate import client as weaviate_client  # noqa: E402

HEADER = "X-Weaviate-Client-Integration"


class TestWeaviateIntegrationHeader(unittest.TestCase):
    def test_version_comes_from_pyproject(self):
        self.assertEqual(weaviate_client._integration_version(), "0.1.0")

    def test_header_is_sent_on_rest_and_grpc(self):
        client = weaviate.use_async_with_local()
        weaviate_client._register_integration(client)

        expected = f"devr-ai/{weaviate_client._integration_version()}"
        connection = client._connection
        self.assertEqual(connection._headers[HEADER], expected)
        self.assertIn((HEADER.lower(), expected), connection.grpc_headers())

    def test_registration_failure_does_not_raise(self):
        broken = MagicMock()
        broken.integrations.configure.side_effect = RuntimeError("boom")
        weaviate_client._register_integration(broken)


if __name__ == "__main__":
    unittest.main()

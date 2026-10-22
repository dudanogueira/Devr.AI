import weaviate
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

_client = None

# Reported to Weaviate (server >= 1.38) as the `X-Weaviate-Client-Integration`
# header, formatted `{name}/{version}`, so Weaviate can attribute traffic to Devr.AI.
_INTEGRATION_NAME = "devr-ai"
_PYPROJECT = Path(__file__).resolve().parents[4] / "pyproject.toml"


def _integration_version() -> str:
    """Devr.AI version from pyproject.toml; "unknown" when it cannot be read."""
    try:
        try:
            import tomllib
            with open(_PYPROJECT, "rb") as f:
                data = tomllib.load(f)
        except ImportError:  # Python 3.10
            import toml
            data = toml.load(_PYPROJECT)
        return str(data["project"]["version"]).strip() or "unknown"
    except Exception:  # telemetry must never break the client
        return "unknown"


def _register_integration(client) -> None:
    """Best-effort: tag the client's REST and gRPC requests with the integration header.

    `_IntegrationConfig` is private weaviate-client API, so failures are only logged.
    """
    try:
        from pydantic import Field
        from weaviate.connect.integrations import _IntegrationConfig

        value = f"{_INTEGRATION_NAME}/{_integration_version()}"

        class _DevrAIIntegration(_IntegrationConfig):
            integration: str = Field(default=value, serialization_alias="X-Weaviate-Client-Integration")

        client.integrations.configure(_DevrAIIntegration())
    except Exception:
        logger.debug("Could not register the Devr.AI Weaviate integration header", exc_info=True)


def get_client():
    """Get or create the global Weaviate client instance."""
    global _client
    if _client is None:
        _client = weaviate.use_async_with_local()
        _register_integration(_client)
    return _client

@asynccontextmanager
async def get_weaviate_client() -> AsyncGenerator[weaviate.WeaviateClient, None]:
    """Async context manager for Weaviate client."""
    client = get_client()
    try:
        await client.connect()
        yield client
    except Exception as e:
        logger.error(f"Weaviate client error: {str(e)}")
        raise
    finally:
        try:
            await client.close()
        except Exception as e:
            logger.warning(f"Error closing Weaviate client: {str(e)}")

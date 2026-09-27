"""Reasoning orchestrator — selects the provider, handles timeouts/errors."""
from __future__ import annotations

from app.config import get_settings
from app.services.reasoning.carma_adapter import CARMAReasoningAdapter
from app.services.reasoning.mock_provider import (
    MODEL_VERSION_NAME as MOCK_VERSION_NAME,
)
from app.services.reasoning.mock_provider import MockReasoningProvider
from app.services.reasoning.provider import (
    ReasoningRequest,
    ReasoningResponse,
)


_PROVIDERS = {
    "mock": MockReasoningProvider(),
    # The CARMA adapter is the Phase 2 integration point. It is registered
    # here so the orchestrator has a single switch point; the adapter
    # itself returns a graceful ESCALATE response until CARMA exposes a
    # live endpoint.
    "carma": CARMAReasoningAdapter(),
}


def get_reasoning_provider():
    settings = get_settings()
    return _PROVIDERS[settings.reasoning_provider]


def reason(request: ReasoningRequest) -> ReasoningResponse:
    """Single entry point used by the API layer."""
    return get_reasoning_provider().reason(request)

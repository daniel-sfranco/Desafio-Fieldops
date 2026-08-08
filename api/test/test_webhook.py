import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest

from models.Auditoria import Auditoria
from models.enums.Status import Status
from utils.webhook import get_data, get_signature, get_env_data, notify


def test_webhook_get_data_payload_structure_and_idempotency():
    audit = Auditoria(
        id=10,
        workOrderId=1,
        actorId=2,
        fromStatus=Status.OPEN,
        toStatus=Status.IN_PROGRESS,
        createdAt=datetime(2026, 6, 19, 14, 0, 0)
    )

    payload = get_data(audit)

    # Verifica os campos obrigatórios da especificação
    assert payload["eventId"] is not None
    assert payload["workOrderId"] == 1
    assert payload["fromStatus"] == "open"
    assert payload["toStatus"] == "in_progress"
    assert payload["actorId"] == 2
    assert payload["occurredAt"] == "2026-06-19T14:00:00.000Z"

    # Teste de idempotência: o mesmo evento de auditoria gera exatamente o mesmo eventId
    payload2 = get_data(audit)
    assert payload["eventId"] == payload2["eventId"]


def test_webhook_get_signature():
    secret = "mysecretkey"
    payload_dict = {"eventId": "123", "status": "open"}
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    expected_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    calculated_sig = get_signature(payload_bytes, secret)

    assert calculated_sig == expected_sig


@pytest.mark.asyncio
async def test_webhook_notify_success(monkeypatch):
    monkeypatch.setenv("WEBHOOK_URL", "https://webhook.site/test-uuid")
    monkeypatch.setenv("WEBHOOK_SECRET", "supersecret123")

    audit = Auditoria(
        id=1,
        workOrderId=100,
        actorId=5,
        fromStatus=Status.IN_PROGRESS,
        toStatus=Status.DONE,
        createdAt=datetime.now()
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.is_error = False
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        await notify(audit)

        assert mock_post.called
        call_kwargs = mock_post.call_args.kwargs

        headers = call_kwargs["headers"]
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Api-Revision"] == "2026.2"
        assert "X-Signature" in headers

        content_bytes = call_kwargs["content"]
        payload = json.loads(content_bytes.decode("utf-8"))
        assert payload["workOrderId"] == 100
        assert payload["fromStatus"] == "in_progress"
        assert payload["toStatus"] == "done"

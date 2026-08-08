import os
import uuid
import hmac
import hashlib
import json
import logging
from enum import Enum
from typing import Any, Dict, Optional, Tuple
import httpx
from dotenv import load_dotenv, find_dotenv

from models.Auditoria import Auditoria

# Carrega as variáveis do arquivo .env automaticamente
load_dotenv(find_dotenv(usecwd=True))

logger = logging.getLogger(__name__)


def get_data(event: Auditoria) -> Dict[str, Any]:
    from_status = (
        event.fromStatus.value
        if isinstance(event.fromStatus, Enum)
        else event.fromStatus
    )
    to_status = (
        event.toStatus.value
        if isinstance(event.toStatus, Enum)
        else event.toStatus
    )

    # Idempotency key: deterministic UUID generated from the unique audit record
    event_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"fieldops:workorder:{event.workOrderId}:audit:{event.id}"
        )
    )

    created_at_str = (
        event.createdAt.isoformat()
        if event.createdAt
        else None
    )

    return {
        "eventId": event_id,
        "workOrderId": event.workOrderId,
        "fromStatus": from_status,
        "toStatus": to_status,
        "actorId": event.actorId,
        "occurredAt": created_at_str
    }


def get_env_data() -> Optional[Tuple[str, str]]:
    url = os.getenv("WEBHOOK_URL")
    secret = os.getenv("WEBHOOK_SECRET")

    if not url or "change-me" in url:
        msg = "[Webhook] WEBHOOK_URL não configurada ou com valor padrão. Disparo ignorado."
        print(f"⚠️  {msg}", flush=True)
        logger.warning(msg)
        return None

    if not secret or "change-me" in secret:
        msg = "[Webhook] WEBHOOK_SECRET não configurado ou com valor padrão. Disparo ignorado."
        print(f"⚠️  {msg}", flush=True)
        logger.warning(msg)
        return None

    return url, secret


def get_signature(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()


async def notify(event: Auditoria):
    env_data = get_env_data()
    if env_data is None:
        return

    url, secret = env_data

    payload_dict = get_data(event)
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    signature = get_signature(payload_bytes, secret)

    headers = {
        "Content-Type": "application/json",
        "X-Api-Revision": "2026.2",
        "X-Signature": signature
    }

    print(f"🚀 [Webhook] Disparando POST para {url} (eventId: {payload_dict['eventId']})...", flush=True)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, content=payload_bytes, headers=headers)
            if response.is_error:
                msg = f"[Webhook] Servidor respondeu com status {response.status_code}: {response.text}"
                print(f"⚠️  {msg}", flush=True)
                logger.warning(msg)
            else:
                msg = f"[Webhook] Enviado com sucesso para {url} (status {response.status_code})"
                print(f"✅ {msg}", flush=True)
                logger.info(msg)
    except Exception as exc:
        msg = f"[Webhook] Falha de conexão ao enviar webhook para {url}: {exc}"
        print(f"❌ {msg}", flush=True)
        logger.error(msg)
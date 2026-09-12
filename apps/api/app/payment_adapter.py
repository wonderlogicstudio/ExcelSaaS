"""Official test-only PG transport. No customer data or provider payload is logged."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from .delivery_inputs import reject


@dataclass(frozen=True)
class PaymentObservation:
    order_id: str
    payment_key: str
    amount: int
    currency: str
    status: str
    balance: int


class PaymentUnknown(Exception):
    """The provider outcome is not known; reconcile the same order."""


class TossTestAdapter:
    mode = "TOSS_TEST"

    def __init__(self, secret: str, *, transport=None):
        if not re.fullmatch(r"test_(?:g?sk)_[A-Za-z0-9_-]{10,250}", secret):
            reject(
                "TEST_PG_KEY_REQUIRED", "공식 테스트 키만 허용합니다. 실결제 키는 차단합니다.", 503
            )
        import logging

        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self._client = httpx.Client(
            base_url="https://api.tosspayments.com",
            auth=(secret, ""),
            timeout=httpx.Timeout(10, connect=3),
            follow_redirects=False,
            transport=transport,
            trust_env=False,
        )

    def close(self):
        self._client.close()

    def _request(self, method, path, *, body=None, key=None):
        headers = {"Idempotency-Key": key} if key else {}
        try:
            with self._client.stream(method, path, json=body, headers=headers) as response:
                if response.status_code != 200:
                    raise PaymentUnknown()
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 128 * 1024:
                        raise PaymentUnknown()
            import json

            value = json.loads(data)
            if (
                not isinstance(value, dict)
                or type(value.get("totalAmount")) is not int
                or type(value.get("balanceAmount")) is not int
                or not isinstance(value.get("orderId"), str)
                or not isinstance(value.get("paymentKey"), str)
                or len(value["paymentKey"]) > 200
                or value.get("status")
                not in {
                    "READY",
                    "IN_PROGRESS",
                    "WAITING_FOR_DEPOSIT",
                    "DONE",
                    "CANCELED",
                    "PARTIAL_CANCELED",
                    "ABORTED",
                    "EXPIRED",
                }
            ):
                raise PaymentUnknown()
            return PaymentObservation(
                value["orderId"],
                value["paymentKey"],
                value["totalAmount"],
                value.get("currency", ""),
                value["status"],
                value["balanceAmount"],
            )
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            raise PaymentUnknown() from None

    def confirm(self, order, payment_key):
        if not isinstance(payment_key, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{6,200}", payment_key
        ):
            reject("INVALID_PAYMENT_REFERENCE", "테스트 결제 참조를 확인하세요.")
        return self._request(
            "POST",
            "/v1/payments/confirm",
            body={"orderId": order["id"], "amount": order["amount"], "paymentKey": payment_key},
            key=order["confirm_key"],
        )

    def query(self, order):
        return self._request("GET", "/v1/payments/orders/" + order["id"])

    def cancel(self, order):
        key = order.get("payment_key")
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{6,200}", key):
            raise PaymentUnknown()
        return self._request(
            "POST",
            "/v1/payments/" + key + "/cancel",
            body={"cancelReason": "Synthetic sandbox cancellation", "currency": "KRW"},
            key=order["cancel_key"],
        )


class LocalContractAdapter:
    """Operator-seeded contract rehearsal. This is never official PG evidence."""

    mode = "LOCAL_CONTRACT"

    def __init__(self, store):
        self.store = store

    def close(self):
        pass

    def query(self, order):
        with self.store.connection() as db:
            row = db.execute(
                "SELECT state FROM payment_contract_receipts WHERE order_id=?", (order["id"],)
            ).fetchone()
        if not row:
            raise PaymentUnknown()
        import json

        return PaymentObservation(**json.loads(row["state"]))

    def confirm(self, order, payment_key):
        return self.query(order)

    def cancel(self, order):
        current = self.query(order)
        if current.status not in {"DONE", "CANCELED"}:
            raise PaymentUnknown()
        import json
        from dataclasses import asdict, replace

        cancelled = replace(current, status="CANCELED", balance=0)
        with self.store.connection() as db:
            db.execute(
                "UPDATE payment_contract_receipts SET state=? WHERE order_id=?",
                (json.dumps(asdict(cancelled)), order["id"]),
            )
        return cancelled

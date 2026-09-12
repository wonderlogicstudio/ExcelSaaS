"""Operator-only local contract receipts. Never represents a PG transaction."""

from __future__ import annotations

import argparse

from .config import get_settings
from .delivery_api import get_store
from .delivery_inputs import reject
from .payment_service import get_order, seed_contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--order-id", required=True)
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_env != "internal_beta" or settings.payment_mode != "LOCAL_CONTRACT":
        reject("LOCAL_CONTRACT_ONLY", "내부 계약 모형 시험 전용입니다.", 403)
    store = get_store()
    with store.connection() as db:
        row = db.execute("SELECT owner FROM payment_orders WHERE id=?", (args.order_id,)).fetchone()
    if not row:
        reject("ORDER_NOT_FOUND", "합성 주문이 없습니다.", 404)
    order = get_order(store, row["owner"], args.order_id)
    seed_contract(store, order, settings)
    print(
        "Local contract receipt recorded. NOT official PG proof. Separate change approval required."
    )


if __name__ == "__main__":
    main()

from typing import Any, Dict, Optional, Tuple

from services.asaas_service import get_asaas_service


def create_payment(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    return get_asaas_service().create_payment(payload)


def create_subscription(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    return get_asaas_service().create_subscription(payload)


def get_payment_billing_info(payment_id: str) -> Tuple[Dict[str, Any], int]:
    return get_asaas_service().get_payment_billing_info(payment_id)


def list_payments(
    external_reference: Optional[str] = None,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    return get_asaas_service().list_payments(
        external_reference=external_reference,
        extra_params=extra_params,
    )


def create_customer(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    return get_asaas_service().create_customer(payload)

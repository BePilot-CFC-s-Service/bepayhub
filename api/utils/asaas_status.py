from models.enums import PaymentStatus

def map_asaas_status_to_payment_status(asaas_status: str) -> str:
    """
    Converte o status retornado pelo Asaas para o enum do Supabase.
    """
    status_map = {
        "PENDING": PaymentStatus.PENDING.value,
        "RECEIVED": PaymentStatus.PAID.value,
        "CONFIRMED": PaymentStatus.PAID.value,
        "REFUNDED": PaymentStatus.REFUNDED.value,
        "CANCELLED": PaymentStatus.CANCELLED.value,
        "OVERDUE": PaymentStatus.CANCELLED.value,
        "FAILED": PaymentStatus.CANCELLED.value,
    }
    return status_map.get(asaas_status.upper(), PaymentStatus.PENDING.value)
from dataclasses import dataclass
from typing import Optional

@dataclass
class CustomerRequestDTO:
    user_type: str
    user_id: int

@dataclass
class PaymentRequestDTO:
    payment_method: str
    credit_card: Optional[dict] = None
    credit_card_holder_info: Optional[dict] = None
    remote_ip: Optional[str] = None
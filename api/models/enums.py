
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "Pending"
    PAID = "Paid"
    REFUNDED = "Refunded"
    CANCELLED = "Cancelled"

class PayoutStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    DEPOSITED = "Deposited"
    FAILED = "Failed"

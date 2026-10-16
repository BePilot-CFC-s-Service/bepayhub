
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "Pending"
    PAID = "Paid"
    REFUNDED = "Refunded"
    CANCELLED = "Cancelled"

class LessonStatus(Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    AWAITING_PAYMENT = "AwaitingPayment"
    PAID = "Paid"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "NoShow"

class PayoutStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    DEPOSITED = "Deposited"
    FAILED = "Failed"

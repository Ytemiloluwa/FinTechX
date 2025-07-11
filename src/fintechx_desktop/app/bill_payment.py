import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple


class BillStatus(Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    PAID = "Paid"
    FAILED = "Failed"
    CANCELED = "Canceled"


class PaymentMethod(Enum):
    CREDIT_CARD = "Credit Card"
    BANK_ACCOUNT = "Bank Account"
    WALLET = "Digital Wallet"


class Bill:
    def __init__(
            self,
            payee: str,
            amount: float,
            due_date: datetime,
            description: str = "",
            category: str = "Other",
            recurring: bool = False,
            frequency: str = None,
    ):
        self.id = str(uuid.uuid4())
        self.payee = payee
        self.amount = amount
        self.due_date = due_date
        self.description = description
        self.category = category
        self.recurring = recurring
        self.frequency = frequency
        self.status = BillStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.payment_date = None
        self.payment_method = None
        self.payment_reference = None
        self.notes = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "payee": self.payee,
            "amount": self.amount,
            "due_date": self.due_date,
            "description": self.description,
            "category": self.category,
            "recurring": self.recurring,
            "frequency": self.frequency,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "payment_date": self.payment_date,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Bill':
        bill = cls(
            payee=data["payee"],
            amount=data["amount"],
            due_date=data["due_date"],
            description=data.get("description", ""),
            category=data.get("category", "Other"),
            recurring=data.get("recurring", False),
            frequency=data.get("frequency"),
        )
        bill.id = data["id"]
        bill.status = BillStatus(data["status"])
        bill.created_at = data["created_at"]
        bill.updated_at = data["updated_at"]
        bill.payment_date = data.get("payment_date")
        if data.get("payment_method"):
            bill.payment_method = PaymentMethod(data["payment_method"])
        bill.payment_reference = data.get("payment_reference")
        bill.notes = data.get("notes", "")
        return bill


class BillPaymentManager:
    def __init__(self):
        self.bills = {}
        self.logger = logging.getLogger("fintechx_desktop.app.bill_payment")

    def add_bill(self, bill: Bill) -> str:
        self.bills[bill.id] = bill
        self.logger.info(f"Added bill {bill.id} for {bill.payee}, amount: ${bill.amount:.2f}")
        return bill.id

    def get_bill(self, bill_id: str) -> Optional[Bill]:
        return self.bills.get(bill_id)

    def update_bill(self, bill_id: str, updates: Dict) -> bool:
        bill = self.get_bill(bill_id)
        if not bill:
            self.logger.warning(f"Attempted to update non-existent bill: {bill_id}")
            return False

        for key, value in updates.items():
            if key == "status" and isinstance(value, str):
                try:
                    bill.status = BillStatus(value)
                except ValueError:
                    self.logger.error(f"Invalid bill status: {value}")
                    continue
            elif key == "payment_method" and isinstance(value, str):
                try:
                    bill.payment_method = PaymentMethod(value)
                except ValueError:
                    self.logger.error(f"Invalid payment method: {value}")
                    continue
            elif hasattr(bill, key):
                setattr(bill, key, value)

        bill.updated_at = datetime.now()
        self.logger.info(f"Updated bill {bill_id}")
        return True

    def delete_bill(self, bill_id: str) -> bool:
        if bill_id in self.bills:
            del self.bills[bill_id]
            self.logger.info(f"Deleted bill {bill_id}")
            return True
        self.logger.warning(f"Attempted to delete non-existent bill: {bill_id}")
        return False

    def get_all_bills(self) -> List[Bill]:
        return list(self.bills.values())

    def get_bills_by_status(self, status: BillStatus) -> List[Bill]:
        return [bill for bill in self.bills.values() if bill.status == status]

    def get_bills_by_due_date_range(self, start_date: datetime, end_date: datetime) -> List[Bill]:
        return [
            bill for bill in self.bills.values()
            if start_date <= bill.due_date <= end_date
        ]

    def get_upcoming_bills(self, days: int = 7) -> List[Bill]:
        now = datetime.now()
        end_date = datetime(now.year, now.month, now.day) + timedelta(days=days)
        return [
            bill for bill in self.bills.values()
            if bill.status in [BillStatus.PENDING, BillStatus.SCHEDULED]
               and bill.due_date <= end_date
        ]

    def schedule_payment(self, bill_id: str, payment_date: datetime,
                         payment_method: PaymentMethod) -> bool:
        bill = self.get_bill(bill_id)
        if not bill:
            self.logger.warning(f"Attempted to schedule payment for non-existent bill: {bill_id}")
            return False

        if bill.status not in [BillStatus.PENDING, BillStatus.FAILED]:
            self.logger.warning(f"Cannot schedule payment for bill {bill_id} with status {bill.status}")
            return False

        bill.status = BillStatus.SCHEDULED
        bill.payment_date = payment_date
        bill.payment_method = payment_method
        bill.updated_at = datetime.now()
        self.logger.info(f"Scheduled payment for bill {bill_id} on {payment_date}")
        return True

    def process_payment(self, bill_id: str) -> Tuple[bool, str]:
        bill = self.get_bill(bill_id)
        if not bill:
            return False, "Bill not found"

        if bill.status != BillStatus.SCHEDULED:
            return False, f"Bill is not scheduled for payment (status: {bill.status.value})"

        try:
            payment_reference = f"PAY-{uuid.uuid4().hex[:8].upper()}"
            bill.status = BillStatus.PAID
            bill.payment_reference = payment_reference
            bill.updated_at = datetime.now()
            self.logger.info(f"Processed payment for bill {bill_id}, reference: {payment_reference}")
            return True, payment_reference
        except Exception as e:
            bill.status = BillStatus.FAILED
            bill.updated_at = datetime.now()
            error_msg = str(e)
            self.logger.error(f"Payment failed for bill {bill_id}: {error_msg}")
            return False, error_msg

    def cancel_scheduled_payment(self, bill_id: str) -> bool:
        bill = self.get_bill(bill_id)
        if not bill:
            return False

        if bill.status != BillStatus.SCHEDULED:
            return False

        bill.status = BillStatus.PENDING
        bill.payment_date = None
        bill.payment_method = None
        bill.updated_at = datetime.now()
        self.logger.info(f"Canceled scheduled payment for bill {bill_id}")
        return True

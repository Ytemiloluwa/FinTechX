import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid
import json


class TransactionType(Enum):
    PAYMENT = "Payment"
    REFUND = "Refund"
    AUTHORIZATION = "Authorization"
    CAPTURE = "Capture"
    VOID = "Void"
    CHARGEBACK = "Chargeback"
    REVERSAL = "Reversal"


class TransactionStatus(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    DECLINED = "Declined"
    FAILED = "Failed"
    SETTLED = "Settled"
    VOIDED = "Voided"
    REFUNDED = "Refunded"
    DISPUTED = "Disputed"


class Transaction:
    def __init__(
            self,
            amount: float,
            card_number: str,
            merchant: str,
            transaction_type: TransactionType,
            status: TransactionStatus = TransactionStatus.PENDING,
            description: str = "",
            reference_id: str = None,
            metadata: Dict = None
    ):
        self.id = str(uuid.uuid4())
        self.amount = amount
        self.card_number = card_number
        self.masked_card = self._mask_card_number(card_number)
        self.merchant = merchant
        self.transaction_type = transaction_type
        self.status = status
        self.description = description
        self.reference_id = reference_id or f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.updated_at = self.timestamp

    def _mask_card_number(self, card_number: str) -> str:
        if not card_number or len(card_number) < 13:
            return "Invalid Card"
        return f"{'*' * (len(card_number) - 4)}{card_number[-4:]}"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "card_number": self.card_number,
            "masked_card": self.masked_card,
            "merchant": self.merchant,
            "transaction_type": self.transaction_type.value,
            "status": self.status.value,
            "description": self.description,
            "reference_id": self.reference_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        transaction = cls(
            amount=data["amount"],
            card_number=data["card_number"],
            merchant=data["merchant"],
            transaction_type=TransactionType(data["transaction_type"]),
            status=TransactionStatus(data["status"]),
            description=data.get("description", ""),
            reference_id=data.get("reference_id"),
            metadata=data.get("metadata", {})
        )
        transaction.id = data["id"]
        transaction.timestamp = datetime.fromisoformat(data["timestamp"])
        transaction.updated_at = datetime.fromisoformat(data["updated_at"])
        return transaction


class TransactionManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.transactions = []
        self.logger = logging.getLogger("fintechx_desktop.app.transaction_history")
        self.storage_path = storage_path

    def add_transaction(self, transaction: Transaction) -> str:
        self.transactions.append(transaction)
        self.logger.info(f"Added transaction {transaction.id} for {transaction.amount:.2f} at {transaction.merchant}")
        return transaction.id

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        for transaction in self.transactions:
            if transaction.id == transaction_id:
                return transaction
        return None

    def update_transaction_status(self, transaction_id: str, new_status: TransactionStatus) -> bool:
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            self.logger.warning(f"Attempted to update non-existent transaction: {transaction_id}")
            return False

        transaction.status = new_status
        transaction.updated_at = datetime.now()
        self.logger.info(f"Updated transaction {transaction_id} status to {new_status.value}")
        return True

    def get_all_transactions(self) -> List[Transaction]:
        return self.transactions

    def get_transactions_by_card(self, card_number: str) -> List[Transaction]:
        return [t for t in self.transactions if t.card_number == card_number]

    def get_transactions_by_status(self, status: TransactionStatus) -> List[Transaction]:
        return [t for t in self.transactions if t.status == status]

    def get_transactions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        return [
            t for t in self.transactions
            if start_date <= t.timestamp <= end_date
        ]

    def get_transactions_by_merchant(self, merchant: str) -> List[Transaction]:
        return [t for t in self.transactions if merchant.lower() in t.merchant.lower()]

    def get_transactions_by_type(self, transaction_type: TransactionType) -> List[Transaction]:
        return [t for t in self.transactions if t.transaction_type == transaction_type]

    def get_transaction_volume_by_date(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        transactions = self.get_transactions_by_date_range(start_date, end_date)
        result = {}

        for transaction in transactions:
            date_str = transaction.timestamp.strftime("%Y-%m-%d")
            if date_str not in result:
                result[date_str] = 0

            if transaction.transaction_type in [TransactionType.PAYMENT, TransactionType.CAPTURE]:
                result[date_str] += transaction.amount
            elif transaction.transaction_type in [TransactionType.REFUND, TransactionType.CHARGEBACK]:
                result[date_str] -= transaction.amount

        return result

    def get_transaction_count_by_status(self) -> Dict[str, int]:
        result = {status.value: 0 for status in TransactionStatus}

        for transaction in self.transactions:
            result[transaction.status.value] += 1

        return result

    def get_transaction_volume_by_merchant(self, top_n: int = 5) -> Dict[str, float]:
        result = {}

        for transaction in self.transactions:
            if transaction.merchant not in result:
                result[transaction.merchant] = 0

            if transaction.transaction_type in [TransactionType.PAYMENT, TransactionType.CAPTURE]:
                result[transaction.merchant] += transaction.amount
            elif transaction.transaction_type in [TransactionType.REFUND, TransactionType.CHARGEBACK]:
                result[transaction.merchant] -= transaction.amount

        sorted_merchants = sorted(result.items(), key=lambda x: abs(x[1]), reverse=True)
        return dict(sorted_merchants[:top_n])

    def export_to_json(self, file_path: str) -> bool:
        try:
            with open(file_path, 'w') as f:
                json.dump([t.to_dict() for t in self.transactions], f, indent=2)
            self.logger.info(f"Exported {len(self.transactions)} transactions to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export transactions: {e}")
            return False

    def import_from_json(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            imported_transactions = []
            for item in data:
                try:
                    transaction = Transaction.from_dict(item)
                    imported_transactions.append(transaction)
                except Exception as e:
                    self.logger.error(f"Failed to import transaction: {e}")

            if imported_transactions:
                self.transactions.extend(imported_transactions)
                self.logger.info(f"Imported {len(imported_transactions)} transactions from {file_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to import transactions: {e}")
            return False

    def generate_transaction_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        transactions = self.get_transactions_by_date_range(start_date, end_date)

        if not transactions:
            return {
                "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "total_count": 0,
                "total_volume": 0,
                "message": "No transactions found for the specified period"
            }

        total_volume = 0
        type_counts = {t.value: 0 for t in TransactionType}
        status_counts = {s.value: 0 for s in TransactionStatus}
        merchant_volumes = {}

        for transaction in transactions:
            if transaction.transaction_type in [TransactionType.PAYMENT, TransactionType.CAPTURE]:
                total_volume += transaction.amount
            elif transaction.transaction_type in [TransactionType.REFUND, TransactionType.CHARGEBACK]:
                total_volume -= transaction.amount

            type_counts[transaction.transaction_type.value] += 1
            status_counts[transaction.status.value] += 1

            if transaction.merchant not in merchant_volumes:
                merchant_volumes[transaction.merchant] = 0

            if transaction.transaction_type in [TransactionType.PAYMENT, TransactionType.CAPTURE]:
                merchant_volumes[transaction.merchant] += transaction.amount
            elif transaction.transaction_type in [TransactionType.REFUND, TransactionType.CHARGEBACK]:
                merchant_volumes[transaction.merchant] -= transaction.amount

        top_merchants = sorted(merchant_volumes.items(), key=lambda x: abs(x[1]), reverse=True)[:5]

        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "total_count": len(transactions),
            "total_volume": total_volume,
            "type_distribution": type_counts,
            "status_distribution": status_counts,
            "top_merchants": dict(top_merchants)
        }

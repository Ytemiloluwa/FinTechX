import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any


class MerchantCategory(Enum):
    RETAIL = "Retail"
    RESTAURANT = "Restaurant"
    TRAVEL = "Travel"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    TECHNOLOGY = "Technology"
    FINANCIAL = "Financial"
    TRANSPORTATION = "Transportation"
    UTILITIES = "Utilities"
    OTHER = "Other"


class MerchantStatus(Enum):
    ACTIVE = "Active"
    PENDING = "Pending"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"


class Merchant:
    def __init__(
            self,
            name: str,
            category: MerchantCategory,
            contact_email: str,
            contact_phone: str,
            address: str,
            tax_id: str = "",
            status: MerchantStatus = MerchantStatus.PENDING,
            metadata: Dict = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.category = category
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.address = address
        self.tax_id = tax_id
        self.status = status
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.terminals = []
        self.payment_methods = []
        self.settlement_info = {}
        self.transaction_volume = 0.0
        self.transaction_count = 0
        self.risk_score = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "address": self.address,
            "tax_id": self.tax_id,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "terminals": self.terminals,
            "payment_methods": self.payment_methods,
            "settlement_info": self.settlement_info,
            "transaction_volume": self.transaction_volume,
            "transaction_count": self.transaction_count,
            "risk_score": self.risk_score
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Merchant':
        try:
            category = MerchantCategory(data["category"])
        except ValueError:
            category = MerchantCategory.OTHER

        try:
            status = MerchantStatus(data["status"])
        except ValueError:
            status = MerchantStatus.PENDING

        merchant = cls(
            name=data["name"],
            category=category,
            contact_email=data["contact_email"],
            contact_phone=data["contact_phone"],
            address=data["address"],
            tax_id=data.get("tax_id", ""),
            status=status,
            metadata=data.get("metadata", {})
        )

        merchant.id = data["id"]
        merchant.created_at = datetime.fromisoformat(data["created_at"])
        merchant.updated_at = datetime.fromisoformat(data["updated_at"])
        merchant.terminals = data.get("terminals", [])
        merchant.payment_methods = data.get("payment_methods", [])
        merchant.settlement_info = data.get("settlement_info", {})
        merchant.transaction_volume = data.get("transaction_volume", 0.0)
        merchant.transaction_count = data.get("transaction_count", 0)
        merchant.risk_score = data.get("risk_score", 0)

        return merchant


class Terminal:
    def __init__(
            self,
            merchant_id: str,
            name: str,
            terminal_type: str,
            location: str,
            serial_number: str = "",
            status: str = "Active"
    ):
        self.id = str(uuid.uuid4())
        self.merchant_id = merchant_id
        self.name = name
        self.terminal_type = terminal_type
        self.location = location
        self.serial_number = serial_number
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.last_transaction = None
        self.transaction_count = 0
        self.transaction_volume = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "name": self.name,
            "terminal_type": self.terminal_type,
            "location": self.location,
            "serial_number": self.serial_number,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_transaction": self.last_transaction.isoformat() if self.last_transaction else None,
            "transaction_count": self.transaction_count,
            "transaction_volume": self.transaction_volume
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Terminal':
        terminal = cls(
            merchant_id=data["merchant_id"],
            name=data["name"],
            terminal_type=data["terminal_type"],
            location=data["location"],
            serial_number=data.get("serial_number", ""),
            status=data.get("status", "Active")
        )

        terminal.id = data["id"]
        terminal.created_at = datetime.fromisoformat(data["created_at"])
        terminal.updated_at = datetime.fromisoformat(data["updated_at"])

        if data.get("last_transaction"):
            terminal.last_transaction = datetime.fromisoformat(data["last_transaction"])

        terminal.transaction_count = data.get("transaction_count", 0)
        terminal.transaction_volume = data.get("transaction_volume", 0.0)

        return terminal


class MerchantManager:
    def __init__(self):
        self.merchants = {}
        self.terminals = {}
        self.logger = logging.getLogger("fintechx_desktop.app.merchant_management")

    def create_merchant(
            self,
            name: str,
            category: MerchantCategory,
            contact_email: str,
            contact_phone: str,
            address: str,
            tax_id: str = "",
            status: MerchantStatus = MerchantStatus.PENDING,
            metadata: Dict = None
    ) -> str:
        merchant = Merchant(
            name=name,
            category=category,
            contact_email=contact_email,
            contact_phone=contact_phone,
            address=address,
            tax_id=tax_id,
            status=status,
            metadata=metadata
        )

        self.merchants[merchant.id] = merchant
        self.logger.info(f"Created merchant {merchant.id}: {name}")
        return merchant.id

    def get_merchant(self, merchant_id: str) -> Optional[Merchant]:
        return self.merchants.get(merchant_id)

    def get_all_merchants(self) -> List[Merchant]:
        return list(self.merchants.values())

    def get_merchants_by_status(self, status: MerchantStatus) -> List[Merchant]:
        return [m for m in self.merchants.values() if m.status == status]

    def get_merchants_by_category(self, category: MerchantCategory) -> List[Merchant]:
        return [m for m in self.merchants.values() if m.category == category]

    def update_merchant(self, merchant_id: str, updates: Dict) -> bool:
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            self.logger.warning(f"Attempted to update non-existent merchant: {merchant_id}")
            return False

        for key, value in updates.items():
            if key == "category" and isinstance(value, str):
                try:
                    merchant.category = MerchantCategory(value)
                except ValueError:
                    self.logger.error(f"Invalid merchant category: {value}")
                    continue
            elif key == "status" and isinstance(value, str):
                try:
                    merchant.status = MerchantStatus(value)
                except ValueError:
                    self.logger.error(f"Invalid merchant status: {value}")
                    continue
            elif hasattr(merchant, key) and key not in ["id", "created_at"]:
                setattr(merchant, key, value)

        merchant.updated_at = datetime.now()
        self.logger.info(f"Updated merchant {merchant_id}")
        return True

    def delete_merchant(self, merchant_id: str) -> bool:
        if merchant_id in self.merchants:
            # Delete associated terminals
            terminals_to_delete = [t.id for t in self.terminals.values() if t.merchant_id == merchant_id]
            for terminal_id in terminals_to_delete:
                del self.terminals[terminal_id]

            del self.merchants[merchant_id]
            self.logger.info(f"Deleted merchant {merchant_id}")
            return True

        self.logger.warning(f"Attempted to delete non-existent merchant: {merchant_id}")
        return False

    def change_merchant_status(self, merchant_id: str, status: MerchantStatus) -> bool:
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            self.logger.warning(f"Attempted to change status of non-existent merchant: {merchant_id}")
            return False

        merchant.status = status
        merchant.updated_at = datetime.now()
        self.logger.info(f"Changed status of merchant {merchant_id} to {status.value}")
        return True

    def add_terminal(
            self,
            merchant_id: str,
            name: str,
            terminal_type: str,
            location: str,
            serial_number: str = "",
            status: str = "Active"
    ) -> Optional[str]:
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            self.logger.warning(f"Attempted to add terminal to non-existent merchant: {merchant_id}")
            return None

        terminal = Terminal(
            merchant_id=merchant_id,
            name=name,
            terminal_type=terminal_type,
            location=location,
            serial_number=serial_number,
            status=status
        )

        self.terminals[terminal.id] = terminal
        merchant.terminals.append(terminal.id)
        merchant.updated_at = datetime.now()

        self.logger.info(f"Added terminal {terminal.id} to merchant {merchant_id}")
        return terminal.id

    def get_terminal(self, terminal_id: str) -> Optional[Terminal]:
        return self.terminals.get(terminal_id)

    def get_merchant_terminals(self, merchant_id: str) -> List[Terminal]:
        return [t for t in self.terminals.values() if t.merchant_id == merchant_id]

    def update_terminal(self, terminal_id: str, updates: Dict) -> bool:
        terminal = self.get_terminal(terminal_id)
        if not terminal:
            self.logger.warning(f"Attempted to update non-existent terminal: {terminal_id}")
            return False

        for key, value in updates.items():
            if hasattr(terminal, key) and key not in ["id", "merchant_id", "created_at"]:
                setattr(terminal, key, value)

        terminal.updated_at = datetime.now()
        self.logger.info(f"Updated terminal {terminal_id}")
        return True

    def delete_terminal(self, terminal_id: str) -> bool:
        terminal = self.get_terminal(terminal_id)
        if not terminal:
            self.logger.warning(f"Attempted to delete non-existent terminal: {terminal_id}")
            return False

        merchant = self.get_merchant(terminal.merchant_id)
        if merchant and terminal_id in merchant.terminals:
            merchant.terminals.remove(terminal_id)
            merchant.updated_at = datetime.now()

        del self.terminals[terminal_id]
        self.logger.info(f"Deleted terminal {terminal_id}")
        return True

    def search_merchants(self, query: str) -> List[Merchant]:
        query = query.lower()
        results = []

        for merchant in self.merchants.values():
            if (query in merchant.name.lower() or
                    query in merchant.contact_email.lower() or
                    query in merchant.address.lower() or
                    query in merchant.tax_id.lower()):
                results.append(merchant)

        return results

    def get_merchant_by_name(self, name: str) -> Optional[Merchant]:
        for merchant in self.merchants.values():
            if merchant.name.lower() == name.lower():
                return merchant
        return None

    def get_merchant_by_tax_id(self, tax_id: str) -> Optional[Merchant]:
        for merchant in self.merchants.values():
            if merchant.tax_id == tax_id:
                return merchant
        return None

    def update_merchant_transaction_stats(self, merchant_id: str, amount: float) -> bool:
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            self.logger.warning(f"Attempted to update stats for non-existent merchant: {merchant_id}")
            return False

        merchant.transaction_volume += amount
        merchant.transaction_count += 1
        merchant.updated_at = datetime.now()

        self.logger.info(f"Updated transaction stats for merchant {merchant_id}")
        return True

    def update_terminal_transaction_stats(self, terminal_id: str, amount: float) -> bool:
        terminal = self.get_terminal(terminal_id)
        if not terminal:
            self.logger.warning(f"Attempted to update stats for non-existent terminal: {terminal_id}")
            return False

        terminal.transaction_volume += amount
        terminal.transaction_count += 1
        terminal.last_transaction = datetime.now()
        terminal.updated_at = datetime.now()

        self.logger.info(f"Updated transaction stats for terminal {terminal_id}")
        return True

    def get_top_merchants_by_volume(self, limit: int = 10) -> List[Merchant]:
        sorted_merchants = sorted(
            self.merchants.values(),
            key=lambda m: m.transaction_volume,
            reverse=True
        )
        return sorted_merchants[:limit]

    def get_top_merchants_by_count(self, limit: int = 10) -> List[Merchant]:
        sorted_merchants = sorted(
            self.merchants.values(),
            key=lambda m: m.transaction_count,
            reverse=True
        )
        return sorted_merchants[:limit]

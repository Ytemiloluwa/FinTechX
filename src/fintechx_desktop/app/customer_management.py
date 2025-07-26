import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any


class CustomerStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"
    CLOSED = "Closed"


class CustomerType(Enum):
    INDIVIDUAL = "Individual"
    BUSINESS = "Business"
    GOVERNMENT = "Government"
    NON_PROFIT = "Non-Profit"


class Customer:
    def __init__(
            self,
            first_name: str,
            last_name: str,
            email: str,
            phone: str,
            address: str,
            customer_type: CustomerType = CustomerType.INDIVIDUAL,
            status: CustomerStatus = CustomerStatus.ACTIVE,
            tax_id: str = "",
            date_of_birth: Optional[datetime] = None,
            metadata: Dict = None
    ):
        self.id = str(uuid.uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address
        self.customer_type = customer_type
        self.status = status
        self.tax_id = tax_id
        self.date_of_birth = date_of_birth
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.cards = []
        self.accounts = []
        self.risk_score = 0
        self.kyc_verified = False
        self.total_transaction_volume = 0.0
        self.total_transaction_count = 0

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "customer_type": self.customer_type.value,
            "status": self.status.value,
            "tax_id": self.tax_id,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "cards": self.cards,
            "accounts": self.accounts,
            "risk_score": self.risk_score,
            "kyc_verified": self.kyc_verified,
            "total_transaction_volume": self.total_transaction_volume,
            "total_transaction_count": self.total_transaction_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Customer':
        try:
            customer_type = CustomerType(data["customer_type"])
        except ValueError:
            customer_type = CustomerType.INDIVIDUAL

        try:
            status = CustomerStatus(data["status"])
        except ValueError:
            status = CustomerStatus.ACTIVE

        date_of_birth = None
        if data.get("date_of_birth"):
            try:
                date_of_birth = datetime.fromisoformat(data["date_of_birth"])
            except (ValueError, TypeError):
                pass

        customer = cls(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data["phone"],
            address=data["address"],
            customer_type=customer_type,
            status=status,
            tax_id=data.get("tax_id", ""),
            date_of_birth=date_of_birth,
            metadata=data.get("metadata", {})
        )

        customer.id = data["id"]
        customer.created_at = datetime.fromisoformat(data["created_at"])
        customer.updated_at = datetime.fromisoformat(data["updated_at"])
        customer.cards = data.get("cards", [])
        customer.accounts = data.get("accounts", [])
        customer.risk_score = data.get("risk_score", 0)
        customer.kyc_verified = data.get("kyc_verified", False)
        customer.total_transaction_volume = data.get("total_transaction_volume", 0.0)
        customer.total_transaction_count = data.get("total_transaction_count", 0)

        return customer


class Account:
    def __init__(
            self,
            customer_id: str,
            account_number: str,
            account_type: str,
            balance: float = 0.0,
            currency: str = "USD",
            status: str = "Active"
    ):
        self.id = str(uuid.uuid4())
        self.customer_id = customer_id
        self.account_number = account_number
        self.account_type = account_type
        self.balance = balance
        self.currency = currency
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.last_transaction_date = None
        self.transaction_count = 0
        self.overdraft_limit = 0.0
        self.interest_rate = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "account_number": self.account_number,
            "account_type": self.account_type,
            "balance": self.balance,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_transaction_date": self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            "transaction_count": self.transaction_count,
            "overdraft_limit": self.overdraft_limit,
            "interest_rate": self.interest_rate
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Account':
        account = cls(
            customer_id=data["customer_id"],
            account_number=data["account_number"],
            account_type=data["account_type"],
            balance=data.get("balance", 0.0),
            currency=data.get("currency", "USD"),
            status=data.get("status", "Active")
        )

        account.id = data["id"]
        account.created_at = datetime.fromisoformat(data["created_at"])
        account.updated_at = datetime.fromisoformat(data["updated_at"])

        if data.get("last_transaction_date"):
            account.last_transaction_date = datetime.fromisoformat(data["last_transaction_date"])

        account.transaction_count = data.get("transaction_count", 0)
        account.overdraft_limit = data.get("overdraft_limit", 0.0)
        account.interest_rate = data.get("interest_rate", 0.0)

        return account


class CustomerManager:
    def __init__(self):
        self.customers = {}
        self.accounts = {}
        self.logger = logging.getLogger("fintechx_desktop.app.customer_management")

    def create_customer(
            self,
            first_name: str,
            last_name: str,
            email: str,
            phone: str,
            address: str,
            customer_type: CustomerType = CustomerType.INDIVIDUAL,
            status: CustomerStatus = CustomerStatus.ACTIVE,
            tax_id: str = "",
            date_of_birth: Optional[datetime] = None,
            metadata: Dict = None
    ) -> str:
        customer = Customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            customer_type=customer_type,
            status=status,
            tax_id=tax_id,
            date_of_birth=date_of_birth,
            metadata=metadata
        )

        self.customers[customer.id] = customer
        self.logger.info(f"Created customer {customer.id}: {customer.full_name}")
        return customer.id

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def get_all_customers(self) -> List[Customer]:
        return list(self.customers.values())

    def get_customers_by_status(self, status: CustomerStatus) -> List[Customer]:
        return [c for c in self.customers.values() if c.status == status]

    def get_customers_by_type(self, customer_type: CustomerType) -> List[Customer]:
        return [c for c in self.customers.values() if c.customer_type == customer_type]

    def update_customer(self, customer_id: str, updates: Dict) -> bool:
        customer = self.get_customer(customer_id)
        if not customer:
            self.logger.warning(f"Attempted to update non-existent customer: {customer_id}")
            return False

        for key, value in updates.items():
            if key == "customer_type" and isinstance(value, str):
                try:
                    customer.customer_type = CustomerType(value)
                except ValueError:
                    self.logger.error(f"Invalid customer type: {value}")
                    continue
            elif key == "status" and isinstance(value, str):
                try:
                    customer.status = CustomerStatus(value)
                except ValueError:
                    self.logger.error(f"Invalid customer status: {value}")
                    continue
            elif key == "date_of_birth" and isinstance(value, str):
                try:
                    customer.date_of_birth = datetime.fromisoformat(value)
                except ValueError:
                    self.logger.error(f"Invalid date format: {value}")
                    continue
            elif hasattr(customer, key) and key not in ["id", "created_at"]:
                setattr(customer, key, value)

        customer.updated_at = datetime.now()
        self.logger.info(f"Updated customer {customer_id}")
        return True

    def delete_customer(self, customer_id: str) -> bool:
        if customer_id in self.customers:
            # Delete associated accounts
            accounts_to_delete = [a.id for a in self.accounts.values() if a.customer_id == customer_id]
            for account_id in accounts_to_delete:
                del self.accounts[account_id]

            del self.customers[customer_id]
            self.logger.info(f"Deleted customer {customer_id}")
            return True

        self.logger.warning(f"Attempted to delete non-existent customer: {customer_id}")
        return False

    def change_customer_status(self, customer_id: str, status: CustomerStatus) -> bool:
        customer = self.get_customer(customer_id)
        if not customer:
            self.logger.warning(f"Attempted to change status of non-existent customer: {customer_id}")
            return False

        customer.status = status
        customer.updated_at = datetime.now()
        self.logger.info(f"Changed status of customer {customer_id} to {status.value}")
        return True

    def create_account(
            self,
            customer_id: str,
            account_number: str,
            account_type: str,
            balance: float = 0.0,
            currency: str = "USD",
            status: str = "Active"
    ) -> Optional[str]:
        customer = self.get_customer(customer_id)
        if not customer:
            self.logger.warning(f"Attempted to add account to non-existent customer: {customer_id}")
            return None

        account = Account(
            customer_id=customer_id,
            account_number=account_number,
            account_type=account_type,
            balance=balance,
            currency=currency,
            status=status
        )

        self.accounts[account.id] = account
        customer.accounts.append(account.id)
        customer.updated_at = datetime.now()

        self.logger.info(f"Created account {account.id} for customer {customer_id}")
        return account.id

    def get_account(self, account_id: str) -> Optional[Account]:
        return self.accounts.get(account_id)

    def get_customer_accounts(self, customer_id: str) -> List[Account]:
        return [a for a in self.accounts.values() if a.customer_id == customer_id]

    def update_account(self, account_id: str, updates: Dict) -> bool:
        account = self.get_account(account_id)
        if not account:
            self.logger.warning(f"Attempted to update non-existent account: {account_id}")
            return False

        for key, value in updates.items():
            if hasattr(account, key) and key not in ["id", "customer_id", "created_at"]:
                setattr(account, key, value)

        account.updated_at = datetime.now()
        self.logger.info(f"Updated account {account_id}")
        return True

    def delete_account(self, account_id: str) -> bool:
        account = self.get_account(account_id)
        if not account:
            self.logger.warning(f"Attempted to delete non-existent account: {account_id}")
            return False

        customer = self.get_customer(account.customer_id)
        if customer and account_id in customer.accounts:
            customer.accounts.remove(account_id)
            customer.updated_at = datetime.now()

        del self.accounts[account_id]
        self.logger.info(f"Deleted account {account_id}")
        return True

    def search_customers(self, query: str) -> List[Customer]:
        query = query.lower()
        results = []

        for customer in self.customers.values():
            if (query in customer.first_name.lower() or
                    query in customer.last_name.lower() or
                    query in customer.email.lower() or
                    query in customer.phone.lower() or
                    query in customer.address.lower() or
                    query in customer.tax_id.lower()):
                results.append(customer)

        return results

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        for customer in self.customers.values():
            if customer.email.lower() == email.lower():
                return customer
        return None

    def get_customer_by_tax_id(self, tax_id: str) -> Optional[Customer]:
        for customer in self.customers.values():
            if customer.tax_id == tax_id:
                return customer
        return None

    def update_customer_transaction_stats(self, customer_id: str, amount: float) -> bool:
        customer = self.get_customer(customer_id)
        if not customer:
            self.logger.warning(f"Attempted to update stats for non-existent customer: {customer_id}")
            return False

        customer.total_transaction_volume += amount
        customer.total_transaction_count += 1
        customer.updated_at = datetime.now()

        self.logger.info(f"Updated transaction stats for customer {customer_id}")
        return True

    def update_account_transaction(self, account_id: str, amount: float) -> bool:
        account = self.get_account(account_id)
        if not account:
            self.logger.warning(f"Attempted to update non-existent account: {account_id}")
            return False

        account.balance += amount
        account.transaction_count += 1
        account.last_transaction_date = datetime.now()
        account.updated_at = datetime.now()

        self.logger.info(f"Updated account {account_id} with transaction amount {amount}")
        return True

    def get_top_customers_by_volume(self, limit: int = 10) -> List[Customer]:
        sorted_customers = sorted(
            self.customers.values(),
            key=lambda c: c.total_transaction_volume,
            reverse=True
        )
        return sorted_customers[:limit]

    def get_top_customers_by_count(self, limit: int = 10) -> List[Customer]:
        sorted_customers = sorted(
            self.customers.values(),
            key=lambda c: c.total_transaction_count,
            reverse=True
        )
        return sorted_customers[:limit]

    def verify_kyc(self, customer_id: str, verified: bool = True) -> bool:
        customer = self.get_customer(customer_id)
        if not customer:
            self.logger.warning(f"Attempted to verify KYC for non-existent customer: {customer_id}")
            return False

        customer.kyc_verified = verified
        customer.updated_at = datetime.now()

        self.logger.info(f"Set KYC verification for customer {customer_id} to {verified}")
        return True

    def update_risk_score(self, customer_id: str, risk_score: int) -> bool:
        customer = self.get_customer(customer_id)
        if not customer:
            self.logger.warning(f"Attempted to update risk score for non-existent customer: {customer_id}")
            return False

        customer.risk_score = risk_score
        customer.updated_at = datetime.now()

        self.logger.info(f"Updated risk score for customer {customer_id} to {risk_score}")
        return True

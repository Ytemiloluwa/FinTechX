import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class CardType(Enum):
    VISA = "Visa"
    MASTERCARD = "Mastercard"
    AMEX = "American Express"
    DISCOVER = "Discover"
    JCB = "JCB"
    DINERS = "Diners Club"
    UNKNOWN = "Unknown"


class CardStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BLOCKED = "Blocked"
    EXPIRED = "Expired"
    PENDING = "Pending Activation"
    REPORTED_LOST = "Reported Lost"
    REPORTED_STOLEN = "Reported Stolen"


class Card:
    def __init__(
            self,
            card_number: str,
            cardholder_name: str,
            expiry_month: int,
            expiry_year: int,
            cvv: str = None,
            card_type: CardType = None,
            status: CardStatus = CardStatus.PENDING,
            billing_address: Dict = None,
            metadata: Dict = None
    ):
        self.id = str(uuid.uuid4())
        self.card_number = card_number
        self.masked_number = self._mask_card_number(card_number)
        self.cardholder_name = cardholder_name
        self.expiry_month = expiry_month
        self.expiry_year = expiry_year
        self.cvv = cvv
        self.card_type = card_type or self._detect_card_type(card_number)
        self.status = status
        self.billing_address = billing_address or {}
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.last_used_at = None

    def _mask_card_number(self, card_number: str) -> str:
        if not card_number or len(card_number) < 13:
            return "Invalid Card"
        return f"{'*' * (len(card_number) - 4)}{card_number[-4:]}"

    def _detect_card_type(self, card_number: str) -> CardType:
        if not card_number:
            return CardType.UNKNOWN

        card_number = card_number.replace(" ", "")

        if card_number.startswith("4"):
            return CardType.VISA
        elif card_number.startswith(("51", "52", "53", "54", "55")) or (
                int(card_number[:6]) >= 222100 and int(card_number[:6]) <= 272099):
            return CardType.MASTERCARD
        elif card_number.startswith(("34", "37")):
            return CardType.AMEX
        elif card_number.startswith(("6011", "644", "645", "646", "647", "648", "649", "65")):
            return CardType.DISCOVER
        elif card_number.startswith(("3528", "3529", "353", "354", "355", "356", "357", "358")):
            return CardType.JCB
        elif card_number.startswith(("300", "301", "302", "303", "304", "305", "36", "38", "39")):
            return CardType.DINERS
        else:
            return CardType.UNKNOWN

    def is_expired(self) -> bool:
        now = datetime.now()
        return (self.expiry_year < now.year or
                (self.expiry_year == now.year and self.expiry_month < now.month))

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "card_number": self.card_number,
            "masked_number": self.masked_number,
            "cardholder_name": self.cardholder_name,
            "expiry_month": self.expiry_month,
            "expiry_year": self.expiry_year,
            "cvv": self.cvv,
            "card_type": self.card_type.value,
            "status": self.status.value,
            "billing_address": self.billing_address,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Card':
        card = cls(
            card_number=data["card_number"],
            cardholder_name=data["cardholder_name"],
            expiry_month=data["expiry_month"],
            expiry_year=data["expiry_year"],
            cvv=data.get("cvv"),
            card_type=CardType(data["card_type"]),
            status=CardStatus(data["status"]),
            billing_address=data.get("billing_address", {}),
            metadata=data.get("metadata", {})
        )
        card.id = data["id"]
        card.created_at = datetime.fromisoformat(data["created_at"])
        card.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("last_used_at"):
            card.last_used_at = datetime.fromisoformat(data["last_used_at"])
        return card


class CardManager:
    def __init__(self):
        self.cards = {}
        self.logger = logging.getLogger("fintechx_desktop.app.card_management")

    def add_card(self, card: Card) -> str:
        self.cards[card.id] = card
        self.logger.info(f"Added card {card.id} for {card.cardholder_name}")
        return card.id

    def get_card(self, card_id: str) -> Optional[Card]:
        return self.cards.get(card_id)

    def get_card_by_number(self, card_number: str) -> Optional[Card]:
        for card in self.cards.values():
            if card.card_number == card_number:
                return card
        return None

    def update_card(self, card_id: str, updates: Dict) -> bool:
        card = self.get_card(card_id)
        if not card:
            self.logger.warning(f"Attempted to update non-existent card: {card_id}")
            return False

        for key, value in updates.items():
            if key == "status" and isinstance(value, str):
                try:
                    card.status = CardStatus(value)
                except ValueError:
                    self.logger.error(f"Invalid card status: {value}")
                    continue
            elif key == "card_type" and isinstance(value, str):
                try:
                    card.card_type = CardType(value)
                except ValueError:
                    self.logger.error(f"Invalid card type: {value}")
                    continue
            elif hasattr(card, key):
                setattr(card, key, value)

        card.updated_at = datetime.now()
        self.logger.info(f"Updated card {card_id}")
        return True

    def delete_card(self, card_id: str) -> bool:
        if card_id in self.cards:
            del self.cards[card_id]
            self.logger.info(f"Deleted card {card_id}")
            return True
        self.logger.warning(f"Attempted to delete non-existent card: {card_id}")
        return False

    def get_all_cards(self) -> List[Card]:
        return list(self.cards.values())

    def get_cards_by_status(self, status: CardStatus) -> List[Card]:
        return [card for card in self.cards.values() if card.status == status]

    def get_cards_by_type(self, card_type: CardType) -> List[Card]:
        return [card for card in self.cards.values() if card.card_type == card_type]

    def get_cards_by_cardholder(self, cardholder_name: str) -> List[Card]:
        return [
            card for card in self.cards.values()
            if cardholder_name.lower() in card.cardholder_name.lower()
        ]

    def get_expired_cards(self) -> List[Card]:
        return [card for card in self.cards.values() if card.is_expired()]

    def get_active_cards(self) -> List[Card]:
        return [
            card for card in self.cards.values()
            if card.status == CardStatus.ACTIVE and not card.is_expired()
        ]

    def activate_card(self, card_id: str) -> bool:
        card = self.get_card(card_id)
        if not card:
            self.logger.warning(f"Attempted to activate non-existent card: {card_id}")
            return False

        if card.status != CardStatus.PENDING:
            self.logger.warning(f"Cannot activate card {card_id} with status {card.status}")
            return False

        if card.is_expired():
            self.logger.warning(f"Cannot activate expired card {card_id}")
            return False

        card.status = CardStatus.ACTIVE
        card.updated_at = datetime.now()
        self.logger.info(f"Activated card {card_id}")
        return True

    def block_card(self, card_id: str, reason: str = None) -> bool:
        card = self.get_card(card_id)
        if not card:
            self.logger.warning(f"Attempted to block non-existent card: {card_id}")
            return False

        if card.status == CardStatus.BLOCKED:
            self.logger.warning(f"Card {card_id} is already blocked")
            return False

        card.status = CardStatus.BLOCKED
        card.updated_at = datetime.now()
        if reason:
            if "block_reasons" not in card.metadata:
                card.metadata["block_reasons"] = []
            card.metadata["block_reasons"].append({
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
        self.logger.info(f"Blocked card {card_id}")
        return True

    def report_lost_stolen(self, card_id: str, is_stolen: bool = False, details: str = None) -> bool:
        card = self.get_card(card_id)
        if not card:
            self.logger.warning(f"Attempted to report non-existent card: {card_id}")
            return False

        card.status = CardStatus.REPORTED_STOLEN if is_stolen else CardStatus.REPORTED_LOST
        card.updated_at = datetime.now()

        report_type = "stolen" if is_stolen else "lost"
        if "reports" not in card.metadata:
            card.metadata["reports"] = []

        card.metadata["reports"].append({
            "type": report_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

        self.logger.info(f"Reported card {card_id} as {report_type}")
        return True

    def update_usage(self, card_id: str) -> bool:
        card = self.get_card(card_id)
        if not card:
            self.logger.warning(f"Attempted to update usage for non-existent card: {card_id}")
            return False

        card.last_used_at = datetime.now()
        self.logger.info(f"Updated usage timestamp for card {card_id}")
        return True

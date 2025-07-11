import logging
import re
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class FraudRiskLevel(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


class FraudDetectionRule:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger("fintechx_desktop.app.fraud_detection")

    def evaluate(self, transaction: Dict) -> Tuple[bool, FraudRiskLevel, str]:
        raise NotImplementedError("Subclasses must implement evaluate method")


class AmountThresholdRule(FraudDetectionRule):
    def __init__(self, threshold: float):
        super().__init__(
            "Amount Threshold",
            f"Flags transactions with amount greater than ${threshold}"
        )
        self.threshold = threshold

    def evaluate(self, transaction: Dict) -> Tuple[bool, FraudRiskLevel, str]:
        amount = transaction.get('amount', 0.0)
        if amount > self.threshold:
            return True, FraudRiskLevel.MEDIUM, f"Transaction amount (${amount}) exceeds threshold (${self.threshold})"
        return False, FraudRiskLevel.LOW, ""


class GeographicAnomalyRule(FraudDetectionRule):
    def __init__(self, allowed_countries: List[str]):
        super().__init__(
            "Geographic Anomaly",
            "Flags transactions from countries outside the allowed list"
        )
        self.allowed_countries = [country.upper() for country in allowed_countries]

    def evaluate(self, transaction: Dict) -> Tuple[bool, FraudRiskLevel, str]:
        country = transaction.get('country', '').upper()
        if country and country not in self.allowed_countries:
            return True, FraudRiskLevel.HIGH, f"Transaction from non-allowed country: {country}"
        return False, FraudRiskLevel.LOW, ""


class VelocityCheckRule(FraudDetectionRule):
    def __init__(self, max_transactions: int, time_window_minutes: int):
        super().__init__(
            "Velocity Check",
            f"Flags if more than {max_transactions} transactions occur within {time_window_minutes} minutes"
        )
        self.max_transactions = max_transactions
        self.time_window = timedelta(minutes=time_window_minutes)
        self.transaction_history = {}

    def evaluate(self, transaction: Dict) -> Tuple[bool, FraudRiskLevel, str]:
        card_id = transaction.get('card_id')
        timestamp = transaction.get('timestamp', datetime.now())

        if not card_id:
            return False, FraudRiskLevel.LOW, ""

        if card_id not in self.transaction_history:
            self.transaction_history[card_id] = []

        self.transaction_history[card_id].append(timestamp)

        cutoff_time = timestamp - self.time_window
        recent_transactions = [t for t in self.transaction_history[card_id] if t >= cutoff_time]

        self.transaction_history[card_id] = recent_transactions

        if len(recent_transactions) > self.max_transactions:
            return True, FraudRiskLevel.HIGH, f"Velocity check: {len(recent_transactions)} transactions in {self.time_window.total_seconds() / 60} minutes"

        return False, FraudRiskLevel.LOW, ""


class PatternMatchingRule(FraudDetectionRule):
    def __init__(self):
        super().__init__(
            "Pattern Matching",
            "Detects suspicious patterns in transaction data"
        )
        self.suspicious_merchants = ["test-merchant", "unauthorized-vendor"]

    def evaluate(self, transaction: Dict) -> Tuple[bool, FraudRiskLevel, str]:
        merchant = transaction.get('merchant', '').lower()
        description = transaction.get('description', '').lower()

        if any(sm in merchant for sm in self.suspicious_merchants):
            return True, FraudRiskLevel.HIGH, f"Suspicious merchant detected: {merchant}"

        test_pattern = re.compile(r'test|dummy|unauthorized', re.IGNORECASE)
        if test_pattern.search(description):
            return True, FraudRiskLevel.MEDIUM, f"Suspicious keywords in description: {description}"

        return False, FraudRiskLevel.LOW, ""


class FraudDetectionEngine:
    def __init__(self):
        self.rules = []
        self.logger = logging.getLogger("fintechx_desktop.app.fraud_detection")
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        self.add_rule(AmountThresholdRule(1000.0))
        self.add_rule(GeographicAnomalyRule(["US", "CA", "GB", "AU"]))
        self.add_rule(VelocityCheckRule(3, 5))
        self.add_rule(PatternMatchingRule())

    def add_rule(self, rule: FraudDetectionRule):
        self.rules.append(rule)
        self.logger.info(f"Added fraud detection rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        removed = len(self.rules) < initial_count
        if removed:
            self.logger.info(f"Removed fraud detection rule: {rule_name}")
        return removed

    def evaluate_transaction(self, transaction: Dict) -> List[Dict]:
        results = []
        highest_risk = FraudRiskLevel.LOW

        for rule in self.rules:
            try:
                triggered, risk_level, message = rule.evaluate(transaction)

                if triggered:
                    results.append({
                        "rule_name": rule.name,
                        "risk_level": risk_level,
                        "message": message
                    })

                    if risk_level.value > highest_risk.value:
                        highest_risk = risk_level

            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule.name}: {e}")

        transaction_id = transaction.get('id', 'unknown')
        if results:
            self.logger.warning(
                f"Transaction {transaction_id} flagged by {len(results)} fraud rules. Highest risk: {highest_risk.name}")
        else:
            self.logger.info(f"Transaction {transaction_id} passed all fraud checks")

        return results

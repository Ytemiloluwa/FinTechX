import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox, QLineEdit,
    QHeaderView, QHBoxLayout, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSlot

from ..app.fraud_detection import FraudDetectionEngine, FraudRiskLevel


class FraudDetectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("fintechx_desktop.ui.fraud_detection")
        self.fraud_engine = FraudDetectionEngine()

        main_layout = QVBoxLayout(self)

        # Transaction simulation section
        simulation_group = QGroupBox("Transaction Simulation")
        simulation_layout = QFormLayout()

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 10000.00)
        self.amount_input.setValue(500.00)
        self.amount_input.setPrefix("$")
        self.amount_input.setDecimals(2)

        self.merchant_input = QLineEdit()
        self.merchant_input.setPlaceholderText("Enter merchant name")
        self.merchant_input.setText("Example Store")

        self.country_input = QComboBox()
        self.country_input.addItems(["US", "CA", "GB", "AU", "FR", "DE", "JP", "CN", "RU"])

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Transaction description")
        self.description_input.setText("Purchase")

        self.card_id_input = QLineEdit()
        self.card_id_input.setPlaceholderText("Card identifier")
        self.card_id_input.setText("4111111111111111")

        self.evaluate_button = QPushButton("Evaluate Transaction")

        simulation_layout.addRow("Amount:", self.amount_input)
        simulation_layout.addRow("Merchant:", self.merchant_input)
        simulation_layout.addRow("Country:", self.country_input)
        simulation_layout.addRow("Description:", self.description_input)
        simulation_layout.addRow("Card ID:", self.card_id_input)
        simulation_layout.addRow(self.evaluate_button)

        simulation_group.setLayout(simulation_layout)

        # Results section
        results_group = QGroupBox("Fraud Detection Results")
        results_layout = QVBoxLayout()

        self.status_label = QLabel("No transaction evaluated yet")

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Rule", "Risk Level", "Message"])
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.transaction_details = QTextEdit()
        self.transaction_details.setReadOnly(True)
        self.transaction_details.setMaximumHeight(100)

        results_layout.addWidget(self.status_label)
        results_layout.addWidget(self.results_table)
        results_layout.addWidget(QLabel("Transaction Details:"))
        results_layout.addWidget(self.transaction_details)

        results_group.setLayout(results_layout)

        # Add both groups to main layout
        main_layout.addWidget(simulation_group)
        main_layout.addWidget(results_group)

        # Connect signals
        self.evaluate_button.clicked.connect(self.evaluate_transaction)

    @pyqtSlot()
    def evaluate_transaction(self):
        transaction = {
            'id': f"T-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'amount': self.amount_input.value(),
            'merchant': self.merchant_input.text(),
            'country': self.country_input.currentText(),
            'description': self.description_input.text(),
            'card_id': self.card_id_input.text(),
            'timestamp': datetime.now()
        }

        self.transaction_details.setText(
            f"ID: {transaction['id']}\n"
            f"Amount: ${transaction['amount']:.2f}\n"
            f"Merchant: {transaction['merchant']}\n"
            f"Country: {transaction['country']}\n"
            f"Description: {transaction['description']}\n"
            f"Card ID: {transaction['card_id']}\n"
            f"Timestamp: {transaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        )

        results = self.fraud_engine.evaluate_transaction(transaction)

        self.results_table.setRowCount(0)

        if not results:
            self.status_label.setText("Transaction passed all fraud checks")
            self.status_label.setStyleSheet("color: green;")
            return

        self.status_label.setText(f"Transaction flagged by {len(results)} rule(s)")
        self.status_label.setStyleSheet("color: red;")

        self.results_table.setRowCount(len(results))

        for row, result in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(result["rule_name"]))

            risk_item = QTableWidgetItem(result["risk_level"].name)
            if result["risk_level"] == FraudRiskLevel.HIGH:
                risk_item.setBackground(Qt.GlobalColor.red)
            elif result["risk_level"] == FraudRiskLevel.MEDIUM:
                risk_item.setBackground(Qt.GlobalColor.yellow)
            else:
                risk_item.setBackground(Qt.GlobalColor.green)

            self.results_table.setItem(row, 1, risk_item)
            self.results_table.setItem(row, 2, QTableWidgetItem(result["message"]))

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QHeaderView, QTextEdit,
    QMessageBox, QTabWidget, QDateEdit, QCheckBox, QDialog, QDialogButtonBox,
    QGridLayout, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSlot, QDate
from PyQt6.QtGui import QColor

from ..app.card_managment import (
    CardManager, Card, CardType, CardStatus
)


class CardDetailsDialog(QDialog):
    def __init__(self, card=None, parent=None):
        super().__init__(parent)
        self.card = card
        self.setWindowTitle("Card Details" if card else "Add New Card")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.cardholder_name = QLineEdit()
        form_layout.addRow("Cardholder Name:", self.cardholder_name)

        self.card_number = QLineEdit()
        self.card_number.setPlaceholderText("16-digit card number")
        form_layout.addRow("Card Number:", self.card_number)

        expiry_layout = QHBoxLayout()
        self.expiry_month = QSpinBox()
        self.expiry_month.setRange(1, 12)
        self.expiry_month.setValue(datetime.now().month)

        self.expiry_year = QSpinBox()
        current_year = datetime.now().year
        self.expiry_year.setRange(current_year, current_year + 10)
        self.expiry_year.setValue(current_year + 3)

        expiry_layout.addWidget(self.expiry_month)
        expiry_layout.addWidget(QLabel("/"))
        expiry_layout.addWidget(self.expiry_year)
        form_layout.addRow("Expiry (MM/YYYY):", expiry_layout)

        self.cvv = QLineEdit()
        self.cvv.setPlaceholderText("3 or 4 digits")
        self.cvv.setMaxLength(4)
        form_layout.addRow("CVV:", self.cvv)

        self.card_type = QComboBox()
        for card_type in CardType:
            self.card_type.addItem(card_type.value)
        form_layout.addRow("Card Type:", self.card_type)

        self.status = QComboBox()
        for status in CardStatus:
            self.status.addItem(status.value)
        form_layout.addRow("Status:", self.status)

        # Billing address fields
        address_group = QGroupBox("Billing Address")
        address_layout = QFormLayout()

        self.address_line1 = QLineEdit()
        address_layout.addRow("Address Line 1:", self.address_line1)

        self.address_line2 = QLineEdit()
        address_layout.addRow("Address Line 2:", self.address_line2)

        self.city = QLineEdit()
        address_layout.addRow("City:", self.city)

        self.state = QLineEdit()
        address_layout.addRow("State/Province:", self.state)

        self.postal_code = QLineEdit()
        address_layout.addRow("Postal Code:", self.postal_code)

        self.country = QLineEdit()
        address_layout.addRow("Country:", self.country)

        address_group.setLayout(address_layout)

        # Notes field
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self.notes = QTextEdit()
        notes_layout.addWidget(self.notes)
        notes_group.setLayout(notes_layout)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Add all components to main layout
        layout.addLayout(form_layout)
        layout.addWidget(address_group)
        layout.addWidget(notes_group)
        layout.addWidget(button_box)

        # If editing an existing card, populate fields
        if self.card:
            self.cardholder_name.setText(self.card.cardholder_name)
            self.card_number.setText(self.card.card_number)
            self.card_number.setReadOnly(True)  # Don't allow changing card number
            self.expiry_month.setValue(self.card.expiry_month)
            self.expiry_year.setValue(self.card.expiry_year)
            if self.card.cvv:
                self.cvv.setText(self.card.cvv)

            type_index = self.card_type.findText(self.card.card_type.value)
            if type_index >= 0:
                self.card_type.setCurrentIndex(type_index)

            status_index = self.status.findText(self.card.status.value)
            if status_index >= 0:
                self.status.setCurrentIndex(status_index)

            # Populate billing address
            if self.card.billing_address:
                self.address_line1.setText(self.card.billing_address.get("line1", ""))
                self.address_line2.setText(self.card.billing_address.get("line2", ""))
                self.city.setText(self.card.billing_address.get("city", ""))
                self.state.setText(self.card.billing_address.get("state", ""))
                self.postal_code.setText(self.card.billing_address.get("postal_code", ""))
                self.country.setText(self.card.billing_address.get("country", ""))

            # Populate notes
            if "notes" in self.card.metadata:
                self.notes.setText(self.card.metadata["notes"])

    def get_card_data(self):
        billing_address = {
            "line1": self.address_line1.text(),
            "line2": self.address_line2.text(),
            "city": self.city.text(),
            "state": self.state.text(),
            "postal_code": self.postal_code.text(),
            "country": self.country.text()
        }

        metadata = {}
        if self.notes.toPlainText():
            metadata["notes"] = self.notes.toPlainText()

        card_type = None
        for ct in CardType:
            if ct.value == self.card_type.currentText():
                card_type = ct
                break

        status = None
        for st in CardStatus:
            if st.value == self.status.currentText():
                status = st
                break

        return {
            "card_number": self.card_number.text().strip().replace(" ", ""),
            "cardholder_name": self.cardholder_name.text().strip(),
            "expiry_month": self.expiry_month.value(),
            "expiry_year": self.expiry_year.value(),
            "cvv": self.cvv.text().strip(),
            "card_type": card_type,
            "status": status,
            "billing_address": billing_address,
            "metadata": metadata
        }


class CardManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("fintechx_desktop.ui.card_management")
        self.card_manager = CardManager()

        main_layout = QVBoxLayout(self)

        # Create tabs for different views
        self.tab_widget = QTabWidget()

        # Create the cards list tab
        self.cards_list_widget = QWidget()
        self.setup_cards_list_tab()
        self.tab_widget.addTab(self.cards_list_widget, "Cards")

        # Create the card actions tab
        self.card_actions_widget = QWidget()
        self.setup_card_actions_tab()
        self.tab_widget.addTab(self.card_actions_widget, "Card Actions")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Initialize with some sample data
        self.load_sample_data()

    def load_sample_data(self):
        # Add sample cards for demonstration
        cards = [
            Card(
                card_number="4111111111111111",
                cardholder_name="John Doe",
                expiry_month=12,
                expiry_year=datetime.now().year + 2,
                cvv="123",
                status=CardStatus.ACTIVE,
                billing_address={
                    "line1": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                    "country": "USA"
                }
            ),
            Card(
                card_number="5555555555554444",
                cardholder_name="Jane Smith",
                expiry_month=6,
                expiry_year=datetime.now().year + 3,
                cvv="456",
                status=CardStatus.ACTIVE,
                billing_address={
                    "line1": "456 Oak Ave",
                    "city": "Somewhere",
                    "state": "NY",
                    "postal_code": "67890",
                    "country": "USA"
                }
            ),
            Card(
                card_number="378282246310005",
                cardholder_name="Robert Johnson",
                expiry_month=9,
                expiry_year=datetime.now().year + 1,
                cvv="1234",
                status=CardStatus.PENDING,
                billing_address={
                    "line1": "789 Pine Rd",
                    "city": "Elsewhere",
                    "state": "TX",
                    "postal_code": "54321",
                    "country": "USA"
                }
            ),
            Card(
                card_number="6011111111111117",
                cardholder_name="Sarah Williams",
                expiry_month=3,
                expiry_year=datetime.now().year - 1,  # Expired card
                cvv="789",
                status=CardStatus.EXPIRED,
                billing_address={
                    "line1": "321 Elm St",
                    "city": "Nowhere",
                    "state": "FL",
                    "postal_code": "98765",
                    "country": "USA"
                }
            ),
            Card(
                card_number="3530111333300000",
                cardholder_name="Michael Brown",
                expiry_month=10,
                expiry_year=datetime.now().year + 4,
                cvv="321",
                status=CardStatus.BLOCKED,
                billing_address={
                    "line1": "654 Maple Dr",
                    "city": "Someplace",
                    "state": "WA",
                    "postal_code": "13579",
                    "country": "USA"
                },
                metadata={
                    "block_reasons": [
                        {
                            "reason": "Suspicious activity",
                            "timestamp": datetime.now().isoformat()
                        }
                    ]
                }
            )
        ]

        for card in cards:
            self.card_manager.add_card(card)

        self.refresh_cards_table()
        self.refresh_card_selector()

    def setup_cards_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_group = QGroupBox("Filter Cards")
        filter_layout = QHBoxLayout()

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        for status in CardStatus:
            self.status_filter.addItem(status.value)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        for card_type in CardType:
            self.type_filter.addItem(card_type.value)

        self.cardholder_filter = QLineEdit()
        self.cardholder_filter.setPlaceholderText("Cardholder name...")

        self.show_expired_checkbox = QCheckBox("Show Expired")
        self.show_expired_checkbox.setChecked(True)

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.refresh_cards_table)

        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(QLabel("Cardholder:"))
        filter_layout.addWidget(self.cardholder_filter)
        filter_layout.addWidget(self.show_expired_checkbox)
        filter_layout.addWidget(self.apply_filter_button)
        filter_group.setLayout(filter_layout)

        # Cards table
        self.cards_table = QTableWidget(0, 7)
        self.cards_table.setHorizontalHeaderLabels([
            "Cardholder", "Card Number", "Type", "Expiry", "Status", "Actions", "ID"
        ])
        self.cards_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.cards_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.cards_table.setColumnHidden(6, True)  # Hide ID column

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_cards_table)

        self.add_card_button = QPushButton("Add New Card")
        self.add_card_button.clicked.connect(self.add_new_card)

        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.add_card_button)

        layout.addWidget(filter_group)
        layout.addWidget(self.cards_table)
        layout.addLayout(action_layout)

        self.cards_list_widget.setLayout(layout)

    def setup_card_actions_tab(self):
        layout = QVBoxLayout()

        # Card selector
        selector_group = QGroupBox("Select Card")
        selector_layout = QHBoxLayout()

        self.card_selector = QComboBox()
        self.refresh_card_selector_button = QPushButton("Refresh")
        self.refresh_card_selector_button.clicked.connect(self.refresh_card_selector)

        selector_layout.addWidget(QLabel("Card:"))
        selector_layout.addWidget(self.card_selector, 1)
        selector_layout.addWidget(self.refresh_card_selector_button)
        selector_group.setLayout(selector_layout)

        # Card details
        details_group = QGroupBox("Card Details")
        details_layout = QGridLayout()

        self.details_cardholder = QLabel()
        self.details_card_number = QLabel()
        self.details_card_type = QLabel()
        self.details_expiry = QLabel()
        self.details_status = QLabel()
        self.details_billing_address = QLabel()
        self.details_billing_address.setWordWrap(True)

        details_layout.addWidget(QLabel("Cardholder:"), 0, 0)
        details_layout.addWidget(self.details_cardholder, 0, 1)
        details_layout.addWidget(QLabel("Card Number:"), 1, 0)
        details_layout.addWidget(self.details_card_number, 1, 1)
        details_layout.addWidget(QLabel("Card Type:"), 2, 0)
        details_layout.addWidget(self.details_card_type, 2, 1)
        details_layout.addWidget(QLabel("Expiry:"), 3, 0)
        details_layout.addWidget(self.details_expiry, 3, 1)
        details_layout.addWidget(QLabel("Status:"), 4, 0)
        details_layout.addWidget(self.details_status, 4, 1)
        details_layout.addWidget(QLabel("Billing Address:"), 5, 0)
        details_layout.addWidget(self.details_billing_address, 5, 1)

        details_group.setLayout(details_layout)

        # Card actions
        actions_group = QGroupBox("Card Actions")
        actions_layout = QVBoxLayout()

        self.activate_button = QPushButton("Activate Card")
        self.activate_button.clicked.connect(self.activate_card)

        self.block_button = QPushButton("Block Card")
        self.block_button.clicked.connect(self.block_card)

        self.report_lost_button = QPushButton("Report Lost")
        self.report_lost_button.clicked.connect(lambda: self.report_lost_stolen(False))

        self.report_stolen_button = QPushButton("Report Stolen")
        self.report_stolen_button.clicked.connect(lambda: self.report_lost_stolen(True))

        self.edit_button = QPushButton("Edit Card Details")
        self.edit_button.clicked.connect(self.edit_card)

        self.delete_button = QPushButton("Delete Card")
        self.delete_button.clicked.connect(self.delete_card)

        actions_layout.addWidget(self.activate_button)
        actions_layout.addWidget(self.block_button)
        actions_layout.addWidget(self.report_lost_button)
        actions_layout.addWidget(self.report_stolen_button)
        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.delete_button)

        actions_group.setLayout(actions_layout)

        # Add all components to main layout
        layout.addWidget(selector_group)
        layout.addWidget(details_group)
        layout.addWidget(actions_group)

        self.card_actions_widget.setLayout(layout)

        # Connect card selector signal
        self.card_selector.currentIndexChanged.connect(self.update_card_details)

    @pyqtSlot()
    def refresh_cards_table(self):
        self.cards_table.setRowCount(0)

        status_filter = self.status_filter.currentText()
        type_filter = self.type_filter.currentText()
        cardholder_filter = self.cardholder_filter.text().strip()
        show_expired = self.show_expired_checkbox.isChecked()

        cards = self.card_manager.get_all_cards()

        if status_filter != "All Statuses":
            status = None
            for st in CardStatus:
                if st.value == status_filter:
                    status = st
                    break
            if status:
                cards = [c for c in cards if c.status == status]

        if type_filter != "All Types":
            card_type = None
            for ct in CardType:
                if ct.value == type_filter:
                    card_type = ct
                    break
            if card_type:
                cards = [c for c in cards if c.card_type == card_type]

        if cardholder_filter:
            cards = [c for c in cards if cardholder_filter.lower() in c.cardholder_name.lower()]

        if not show_expired:
            cards = [c for c in cards if not c.is_expired()]

        self.cards_table.setRowCount(len(cards))

        for row, card in enumerate(cards):
            self.cards_table.setItem(row, 0, QTableWidgetItem(card.cardholder_name))
            self.cards_table.setItem(row, 1, QTableWidgetItem(card.masked_number))
            self.cards_table.setItem(row, 2, QTableWidgetItem(card.card_type.value))

            expiry_item = QTableWidgetItem(f"{card.expiry_month:02d}/{card.expiry_year}")
            if card.is_expired():
                expiry_item.setForeground(QColor(255, 0, 0))  # Red for expired
            self.cards_table.setItem(row, 3, expiry_item)

            status_item = QTableWidgetItem(card.status.value)
            if card.status == CardStatus.ACTIVE:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif card.status in [CardStatus.BLOCKED, CardStatus.REPORTED_LOST, CardStatus.REPORTED_STOLEN]:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif card.status == CardStatus.EXPIRED:
                status_item.setBackground(QColor(220, 220, 220))  # Light gray
            self.cards_table.setItem(row, 4, status_item)

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_button = QPushButton("View")
            view_button.setProperty("card_id", card.id)
            view_button.clicked.connect(self.view_card_details)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("card_id", card.id)
            edit_button.clicked.connect(self.edit_card_from_list)

            actions_layout.addWidget(view_button)
            actions_layout.addWidget(edit_button)

            self.cards_table.setCellWidget(row, 5, actions_widget)
            self.cards_table.setItem(row, 6, QTableWidgetItem(card.id))

    @pyqtSlot()
    def refresh_card_selector(self):
        current_card_id = self.card_selector.currentData()

        self.card_selector.clear()

        cards = self.card_manager.get_all_cards()
        for card in cards:
            self.card_selector.addItem(
                f"{card.cardholder_name} - {card.masked_number} ({card.status.value})",
                card.id
            )

        if current_card_id:
            for i in range(self.card_selector.count()):
                if self.card_selector.itemData(i) == current_card_id:
                    self.card_selector.setCurrentIndex(i)
                    break

        self.update_card_details()

    @pyqtSlot()
    def update_card_details(self):
        card_id = self.card_selector.currentData()

        if not card_id:
            self.clear_card_details()
            self.disable_card_actions()
            return

        card = self.card_manager.get_card(card_id)
        if not card:
            self.clear_card_details()
            self.disable_card_actions()
            return

        self.details_cardholder.setText(card.cardholder_name)
        self.details_card_number.setText(card.masked_number)
        self.details_card_type.setText(card.card_type.value)
        self.details_expiry.setText(f"{card.expiry_month:02d}/{card.expiry_year}")

        status_text = card.status.value
        if card.is_expired():
            status_text += " (Expired)"
        self.details_status.setText(status_text)

        address_parts = []
        if card.billing_address:
            if card.billing_address.get("line1"):
                address_parts.append(card.billing_address["line1"])
            if card.billing_address.get("line2"):
                address_parts.append(card.billing_address["line2"])

            city_state = []
            if card.billing_address.get("city"):
                city_state.append(card.billing_address["city"])
            if card.billing_address.get("state"):
                city_state.append(card.billing_address["state"])

            if city_state:
                address_parts.append(", ".join(city_state))

            if card.billing_address.get("postal_code"):
                address_parts.append(card.billing_address["postal_code"])

            if card.billing_address.get("country"):
                address_parts.append(card.billing_address["country"])

        self.details_billing_address.setText("\n".join(address_parts) if address_parts else "No address on file")

        # Enable/disable action buttons based on card status
        self.activate_button.setEnabled(card.status == CardStatus.PENDING and not card.is_expired())
        self.block_button.setEnabled(card.status == CardStatus.ACTIVE)
        self.report_lost_button.setEnabled(card.status == CardStatus.ACTIVE)
        self.report_stolen_button.setEnabled(card.status == CardStatus.ACTIVE)
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def clear_card_details(self):
        self.details_cardholder.setText("")
        self.details_card_number.setText("")
        self.details_card_type.setText("")
        self.details_expiry.setText("")
        self.details_status.setText("")
        self.details_billing_address.setText("")

    def disable_card_actions(self):
        self.activate_button.setEnabled(False)
        self.block_button.setEnabled(False)
        self.report_lost_button.setEnabled(False)
        self.report_stolen_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    @pyqtSlot()
    def add_new_card(self):
        dialog = CardDetailsDialog(parent=self)
        if dialog.exec():
            card_data = dialog.get_card_data()

            # Validate card data
            if not card_data["card_number"] or not card_data["cardholder_name"]:
                QMessageBox.warning(self, "Input Error", "Card number and cardholder name are required.")
                return

            # Check if card already exists
            existing_card = self.card_manager.get_card_by_number(card_data["card_number"])
            if existing_card:
                QMessageBox.warning(self, "Card Exists", "A card with this number already exists.")
                return

            # Create and add new card
            card = Card(
                card_number=card_data["card_number"],
                cardholder_name=card_data["cardholder_name"],
                expiry_month=card_data["expiry_month"],
                expiry_year=card_data["expiry_year"],
                cvv=card_data["cvv"],
                card_type=card_data["card_type"],
                status=card_data["status"],
                billing_address=card_data["billing_address"],
                metadata=card_data["metadata"]
            )

            card_id = self.card_manager.add_card(card)

            if card_id:
                QMessageBox.information(self, "Success", "Card added successfully.")
                self.refresh_cards_table()
                self.refresh_card_selector()
            else:
                QMessageBox.warning(self, "Error", "Failed to add card.")

    @pyqtSlot()
    def view_card_details(self):
        button = self.sender()
        card_id = button.property("card_id")

        # Find the card in the selector and select it
        for i in range(self.card_selector.count()):
            if self.card_selector.itemData(i) == card_id:
                self.card_selector.setCurrentIndex(i)
                self.tab_widget.setCurrentIndex(1)  # Switch to Card Actions tab
                break

    @pyqtSlot()
    def edit_card_from_list(self):
        button = self.sender()
        card_id = button.property("card_id")

        card = self.card_manager.get_card(card_id)
        if not card:
            QMessageBox.warning(self, "Error", "Card not found.")
            return

        self.edit_card_dialog(card)

    @pyqtSlot()
    def edit_card(self):
        card_id = self.card_selector.currentData()
        if not card_id:
            QMessageBox.warning(self, "Error", "No card selected.")
            return

        card = self.card_manager.get_card(card_id)
        if not card:
            QMessageBox.warning(self, "Error", "Card not found.")
            return

        self.edit_card_dialog(card)

    def edit_card_dialog(self, card):
        dialog = CardDetailsDialog(card=card, parent=self)
        if dialog.exec():
            card_data = dialog.get_card_data()

            # Validate card data
            if not card_data["cardholder_name"]:
                QMessageBox.warning(self, "Input Error", "Cardholder name is required.")
                return

            # Update card
            updates = {
                "cardholder_name": card_data["cardholder_name"],
                "expiry_month": card_data["expiry_month"],
                "expiry_year": card_data["expiry_year"],
                "cvv": card_data["cvv"],
                "card_type": card_data["card_type"],
                "status": card_data["status"],
                "billing_address": card_data["billing_address"],
                "metadata": card_data["metadata"]
            }

            success = self.card_manager.update_card(card.id, updates)

            if success:
                QMessageBox.information(self, "Success", "Card updated successfully.")
                self.refresh_cards_table()
                self.refresh_card_selector()
            else:
                QMessageBox.warning(self, "Error", "Failed to update card.")

    @pyqtSlot()
    def delete_card(self):
        card_id = self.card_selector.currentData()
        if not card_id:
            QMessageBox.warning(self, "Error", "No card selected.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this card?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.card_manager.delete_card(card_id)

            if success:
                QMessageBox.information(self, "Success", "Card deleted successfully.")
                self.refresh_cards_table()
                self.refresh_card_selector()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete card.")

    @pyqtSlot()
    def activate_card(self):
        card_id = self.card_selector.currentData()
        if not card_id:
            QMessageBox.warning(self, "Error", "No card selected.")
            return

        success = self.card_manager.activate_card(card_id)

        if success:
            QMessageBox.information(self, "Success", "Card activated successfully.")
            self.refresh_cards_table()
            self.refresh_card_selector()
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to activate card. Card may be expired or not in pending status."
            )

    @pyqtSlot()
    def block_card(self):
        card_id = self.card_selector.currentData()
        if not card_id:
            QMessageBox.warning(self, "Error", "No card selected.")
            return

        reason, ok = QMessageBox.getText(
            self,
            "Block Card",
            "Enter reason for blocking (optional):"
        )

        if ok:
            success = self.card_manager.block_card(card_id, reason if reason else None)

            if success:
                QMessageBox.information(self, "Success", "Card blocked successfully.")
                self.refresh_cards_table()
                self.refresh_card_selector()
            else:
                QMessageBox.warning(self, "Error", "Failed to block card.")

    def report_lost_stolen(self, is_stolen):
        card_id = self.card_selector.currentData()
        if not card_id:
            QMessageBox.warning(self, "Error", "No card selected.")
            return

        report_type = "stolen" if is_stolen else "lost"

        details, ok = QMessageBox.getText(
            self,
            f"Report Card as {report_type.capitalize()}",
            "Enter details (optional):"
        )

        if ok:
            success = self.card_manager.report_lost_stolen(
                card_id,
                is_stolen=is_stolen,
                details=details if details else None
            )

            if success:
                QMessageBox.information(self, "Success", f"Card reported as {report_type} successfully.")
                self.refresh_cards_table()
                self.refresh_card_selector()
            else:
                QMessageBox.warning(self, "Error", f"Failed to report card as {report_type}.")

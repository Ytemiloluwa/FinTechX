import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QHeaderView, QTextEdit,
    QMessageBox, QTabWidget, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor

from ..app.merchant_management import ( MerchantCategory, MerchantStatus
)


class MerchantDetailsDialog(QDialog):
    def __init__(self, merchant_manager, merchant=None, parent=None):
        super().__init__(parent)
        self.merchant_manager = merchant_manager
        self.merchant = merchant
        self.setWindowTitle("Merchant Details" if merchant else "Add New Merchant")
        self.setMinimumWidth(600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Merchant info form
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        form_layout.addRow("Merchant Name:", self.name_input)

        self.category_combo = QComboBox()
        for category in MerchantCategory:
            self.category_combo.addItem(category.value)
        form_layout.addRow("Category:", self.category_combo)

        self.email_input = QLineEdit()
        form_layout.addRow("Contact Email:", self.email_input)

        self.phone_input = QLineEdit()
        form_layout.addRow("Contact Phone:", self.phone_input)

        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("Address:", self.address_input)

        self.tax_id_input = QLineEdit()
        form_layout.addRow("Tax ID:", self.tax_id_input)

        self.status_combo = QComboBox()
        for status in MerchantStatus:
            self.status_combo.addItem(status.value)
        form_layout.addRow("Status:", self.status_combo)

        # Additional metadata
        metadata_group = QGroupBox("Additional Information")
        metadata_layout = QFormLayout()

        self.website_input = QLineEdit()
        metadata_layout.addRow("Website:", self.website_input)

        self.contact_name_input = QLineEdit()
        metadata_layout.addRow("Contact Name:", self.contact_name_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        metadata_layout.addRow("Notes:", self.notes_input)

        metadata_group.setLayout(metadata_layout)

        # Settlement info
        settlement_group = QGroupBox("Settlement Information")
        settlement_layout = QFormLayout()

        self.bank_name_input = QLineEdit()
        settlement_layout.addRow("Bank Name:", self.bank_name_input)

        self.account_number_input = QLineEdit()
        settlement_layout.addRow("Account Number:", self.account_number_input)

        self.routing_number_input = QLineEdit()
        settlement_layout.addRow("Routing Number:", self.routing_number_input)

        settlement_group.setLayout(settlement_layout)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        # Add all components to main layout
        layout.addLayout(form_layout)
        layout.addWidget(metadata_group)
        layout.addWidget(settlement_group)
        layout.addWidget(button_box)

        # If editing an existing merchant, populate fields
        if self.merchant:
            self.name_input.setText(self.merchant.name)

            category_index = self.category_combo.findText(self.merchant.category.value)
            if category_index >= 0:
                self.category_combo.setCurrentIndex(category_index)

            self.email_input.setText(self.merchant.contact_email)
            self.phone_input.setText(self.merchant.contact_phone)
            self.address_input.setText(self.merchant.address)
            self.tax_id_input.setText(self.merchant.tax_id)

            status_index = self.status_combo.findText(self.merchant.status.value)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

            # Populate metadata fields
            self.website_input.setText(self.merchant.metadata.get("website", ""))
            self.contact_name_input.setText(self.merchant.metadata.get("contact_name", ""))
            self.notes_input.setText(self.merchant.metadata.get("notes", ""))

            # Populate settlement info
            settlement_info = self.merchant.settlement_info
            self.bank_name_input.setText(settlement_info.get("bank_name", ""))
            self.account_number_input.setText(settlement_info.get("account_number", ""))
            self.routing_number_input.setText(settlement_info.get("routing_number", ""))

    @pyqtSlot()
    def validate_and_accept(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Merchant name is required.")
            return

        if not email:
            QMessageBox.warning(self, "Input Error", "Contact email is required.")
            return

        if not phone:
            QMessageBox.warning(self, "Input Error", "Contact phone is required.")
            return

        if not address:
            QMessageBox.warning(self, "Input Error", "Address is required.")
            return

        self.accept()

    def get_merchant_data(self):
        category = None
        for c in MerchantCategory:
            if c.value == self.category_combo.currentText():
                category = c
                break

        status = None
        for s in MerchantStatus:
            if s.value == self.status_combo.currentText():
                status = s
                break

        metadata = {
            "website": self.website_input.text().strip(),
            "contact_name": self.contact_name_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip()
        }

        settlement_info = {
            "bank_name": self.bank_name_input.text().strip(),
            "account_number": self.account_number_input.text().strip(),
            "routing_number": self.routing_number_input.text().strip()
        }

        data = {
            "name": self.name_input.text().strip(),
            "category": category,
            "contact_email": self.email_input.text().strip(),
            "contact_phone": self.phone_input.text().strip(),
            "address": self.address_input.toPlainText().strip(),
            "tax_id": self.tax_id_input.text().strip(),
            "status": status,
            "metadata": metadata,
            "settlement_info": settlement_info
        }

        return data


class TerminalDetailsDialog(QDialog):
    def __init__(self, merchant_manager, merchant_id, terminal=None, parent=None):
        super().__init__(parent)
        self.merchant_manager = merchant_manager
        self.merchant_id = merchant_id
        self.terminal = terminal
        self.setWindowTitle("Terminal Details" if terminal else "Add New Terminal")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        form_layout.addRow("Terminal Name:", self.name_input)

        self.terminal_type_combo = QComboBox()
        self.terminal_type_combo.addItems([
            "Physical POS", "Mobile POS", "Virtual Terminal", "E-commerce", "Other"
        ])
        form_layout.addRow("Terminal Type:", self.terminal_type_combo)

        self.location_input = QLineEdit()
        form_layout.addRow("Location:", self.location_input)

        self.serial_number_input = QLineEdit()
        form_layout.addRow("Serial Number:", self.serial_number_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Maintenance"])
        form_layout.addRow("Status:", self.status_combo)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        # If editing an existing terminal, populate fields
        if self.terminal:
            self.name_input.setText(self.terminal.name)

            type_index = self.terminal_type_combo.findText(self.terminal.terminal_type)
            if type_index >= 0:
                self.terminal_type_combo.setCurrentIndex(type_index)

            self.location_input.setText(self.terminal.location)
            self.serial_number_input.setText(self.terminal.serial_number)

            status_index = self.status_combo.findText(self.terminal.status)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

    @pyqtSlot()
    def validate_and_accept(self):
        name = self.name_input.text().strip()
        location = self.location_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Input Error", "Terminal name is required.")
            return

        if not location:
            QMessageBox.warning(self, "Input Error", "Location is required.")
            return

        self.accept()

    def get_terminal_data(self):
        data = {
            "name": self.name_input.text().strip(),
            "terminal_type": self.terminal_type_combo.currentText(),
            "location": self.location_input.text().strip(),
            "serial_number": self.serial_number_input.text().strip(),
            "status": self.status_combo.currentText()
        }

        return data


class MerchantManagementWidget(QWidget):
    def __init__(self, merchant_manager, parent=None):
        super().__init__(parent)
        self.merchant_manager = merchant_manager
        self.logger = logging.getLogger("fintechx_desktop.ui.merchant_management")

        main_layout = QVBoxLayout(self)

        # Create tabs for different views
        self.tab_widget = QTabWidget()

        # Create the merchants list tab
        self.merchants_list_widget = QWidget()
        self.setup_merchants_list_tab()
        self.tab_widget.addTab(self.merchants_list_widget, "Merchants")

        # Create the terminals tab
        self.terminals_widget = QWidget()
        self.setup_terminals_tab()
        self.tab_widget.addTab(self.terminals_widget, "Terminals")

        # Create the analytics tab
        self.analytics_widget = QWidget()
        self.setup_analytics_tab()
        self.tab_widget.addTab(self.analytics_widget, "Analytics")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def setup_merchants_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_group = QGroupBox("Filter Merchants")
        filter_layout = QHBoxLayout()

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        for category in MerchantCategory:
            self.category_filter.addItem(category.value)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        for status in MerchantStatus:
            self.status_filter.addItem(status.value)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search merchants...")

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.refresh_merchants_table)

        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.apply_filter_button)
        filter_group.setLayout(filter_layout)

        # Merchants table
        self.merchants_table = QTableWidget(0, 7)
        self.merchants_table.setHorizontalHeaderLabels([
            "Name", "Category", "Contact", "Status", "Terminals", "Transaction Volume", "Actions"
        ])
        self.merchants_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.merchants_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_merchants_table)

        self.add_merchant_button = QPushButton("Add New Merchant")
        self.add_merchant_button.clicked.connect(self.add_new_merchant)

        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.add_merchant_button)

        layout.addWidget(filter_group)
        layout.addWidget(self.merchants_table)
        layout.addLayout(action_layout)

        self.merchants_list_widget.setLayout(layout)

        # Initial data load
        self.refresh_merchants_table()

    def setup_terminals_tab(self):
        layout = QVBoxLayout()

        # Merchant selection
        merchant_group = QGroupBox("Select Merchant")
        merchant_layout = QHBoxLayout()

        self.merchant_combo = QComboBox()
        self.refresh_merchant_combo()

        self.refresh_merchant_combo_button = QPushButton("Refresh")
        self.refresh_merchant_combo_button.clicked.connect(self.refresh_merchant_combo)

        merchant_layout.addWidget(QLabel("Merchant:"))
        merchant_layout.addWidget(self.merchant_combo, 1)
        merchant_layout.addWidget(self.refresh_merchant_combo_button)
        merchant_group.setLayout(merchant_layout)

        # Terminals table
        self.terminals_table = QTableWidget(0, 6)
        self.terminals_table.setHorizontalHeaderLabels([
            "Name", "Type", "Location", "Status", "Transaction Count", "Actions"
        ])
        self.terminals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.terminals_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_terminals_button = QPushButton("Refresh Terminals")
        self.refresh_terminals_button.clicked.connect(self.refresh_terminals_table)

        self.add_terminal_button = QPushButton("Add New Terminal")
        self.add_terminal_button.clicked.connect(self.add_new_terminal)

        action_layout.addWidget(self.refresh_terminals_button)
        action_layout.addWidget(self.add_terminal_button)

        layout.addWidget(merchant_group)
        layout.addWidget(self.terminals_table)
        layout.addLayout(action_layout)

        self.terminals_widget.setLayout(layout)

        # Connect merchant selection change
        self.merchant_combo.currentIndexChanged.connect(self.refresh_terminals_table)

    def setup_analytics_tab(self):
        layout = QVBoxLayout()

        # Top merchants by volume
        volume_group = QGroupBox("Top Merchants by Transaction Volume")
        volume_layout = QVBoxLayout()

        self.volume_table = QTableWidget(0, 3)
        self.volume_table.setHorizontalHeaderLabels([
            "Merchant", "Category", "Transaction Volume"
        ])
        self.volume_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        volume_layout.addWidget(self.volume_table)
        volume_group.setLayout(volume_layout)

        # Top merchants by count
        count_group = QGroupBox("Top Merchants by Transaction Count")
        count_layout = QVBoxLayout()

        self.count_table = QTableWidget(0, 3)
        self.count_table.setHorizontalHeaderLabels([
            "Merchant", "Category", "Transaction Count"
        ])
        self.count_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        count_layout.addWidget(self.count_table)
        count_group.setLayout(count_layout)

        # Refresh button
        refresh_button = QPushButton("Refresh Analytics")
        refresh_button.clicked.connect(self.refresh_analytics)

        layout.addWidget(volume_group)
        layout.addWidget(count_group)
        layout.addWidget(refresh_button)

        self.analytics_widget.setLayout(layout)

    @pyqtSlot(int)
    def on_tab_changed(self, index):
        if index == 0:  # Merchants tab
            self.refresh_merchants_table()
        elif index == 1:  # Terminals tab
            self.refresh_merchant_combo()
            self.refresh_terminals_table()
        elif index == 2:  # Analytics tab
            self.refresh_analytics()

    @pyqtSlot()
    def refresh_merchants_table(self):
        self.merchants_table.setRowCount(0)

        category_filter = self.category_filter.currentText()
        status_filter = self.status_filter.currentText()
        search_text = self.search_input.text().strip().lower()

        merchants = self.merchant_manager.get_all_merchants()

        # Apply category filter
        if category_filter != "All Categories":
            category = None
            for c in MerchantCategory:
                if c.value == category_filter:
                    category = c
                    break
            if category:
                merchants = [m for m in merchants if m.category == category]

        # Apply status filter
        if status_filter != "All Statuses":
            status = None
            for s in MerchantStatus:
                if s.value == status_filter:
                    status = s
                    break
            if status:
                merchants = [m for m in merchants if m.status == status]

        # Apply search filter
        if search_text:
            merchants = self.merchant_manager.search_merchants(search_text)

        self.merchants_table.setRowCount(len(merchants))

        for row, merchant in enumerate(merchants):
            self.merchants_table.setItem(row, 0, QTableWidgetItem(merchant.name))
            self.merchants_table.setItem(row, 1, QTableWidgetItem(merchant.category.value))

            contact_info = f"{merchant.contact_email}\n{merchant.contact_phone}"
            self.merchants_table.setItem(row, 2, QTableWidgetItem(contact_info))

            status_item = QTableWidgetItem(merchant.status.value)
            if merchant.status == MerchantStatus.ACTIVE:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif merchant.status == MerchantStatus.PENDING:
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            elif merchant.status == MerchantStatus.SUSPENDED:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif merchant.status == MerchantStatus.TERMINATED:
                status_item.setBackground(QColor(200, 200, 200))  # Light gray

            self.merchants_table.setItem(row, 3, status_item)

            terminal_count = len(merchant.terminals)
            self.merchants_table.setItem(row, 4, QTableWidgetItem(str(terminal_count)))

            volume_item = QTableWidgetItem(f"${merchant.transaction_volume:.2f}")
            self.merchants_table.setItem(row, 5, volume_item)

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_button = QPushButton("View")
            view_button.setProperty("merchant_id", merchant.id)
            view_button.clicked.connect(self.view_merchant)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("merchant_id", merchant.id)
            edit_button.clicked.connect(self.edit_merchant)

            if merchant.status == MerchantStatus.ACTIVE:
                suspend_button = QPushButton("Suspend")
                suspend_button.setProperty("merchant_id", merchant.id)
                suspend_button.clicked.connect(self.suspend_merchant)
                actions_layout.addWidget(suspend_button)
            elif merchant.status == MerchantStatus.SUSPENDED:
                activate_button = QPushButton("Activate")
                activate_button.setProperty("merchant_id", merchant.id)
                activate_button.clicked.connect(self.activate_merchant)
                actions_layout.addWidget(activate_button)

            actions_layout.addWidget(view_button)
            actions_layout.addWidget(edit_button)

            self.merchants_table.setCellWidget(row, 6, actions_widget)

    @pyqtSlot()
    def refresh_merchant_combo(self):
        current_text = self.merchant_combo.currentText()

        self.merchant_combo.clear()
        self.merchant_combo.addItem("Select a merchant...")

        merchants = self.merchant_manager.get_all_merchants()
        for merchant in merchants:
            self.merchant_combo.addItem(merchant.name, merchant.id)

        # Try to restore previous selection
        if current_text:
            index = self.merchant_combo.findText(current_text)
            if index >= 0:
                self.merchant_combo.setCurrentIndex(index)

    @pyqtSlot()
    def refresh_terminals_table(self):
        self.terminals_table.setRowCount(0)

        merchant_id = self.merchant_combo.currentData()
        if not merchant_id:
            return

        terminals = self.merchant_manager.get_merchant_terminals(merchant_id)

        self.terminals_table.setRowCount(len(terminals))

        for row, terminal in enumerate(terminals):
            self.terminals_table.setItem(row, 0, QTableWidgetItem(terminal.name))
            self.terminals_table.setItem(row, 1, QTableWidgetItem(terminal.terminal_type))
            self.terminals_table.setItem(row, 2, QTableWidgetItem(terminal.location))

            status_item = QTableWidgetItem(terminal.status)
            if terminal.status == "Active":
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif terminal.status == "Inactive":
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif terminal.status == "Maintenance":
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow

            self.terminals_table.setItem(row, 3, status_item)

            self.terminals_table.setItem(row, 4, QTableWidgetItem(str(terminal.transaction_count)))

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("terminal_id", terminal.id)
            edit_button.clicked.connect(self.edit_terminal)

            delete_button = QPushButton("Delete")
            delete_button.setProperty("terminal_id", terminal.id)
            delete_button.clicked.connect(self.delete_terminal)

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)

            self.terminals_table.setCellWidget(row, 5, actions_widget)

    @pyqtSlot()
    def refresh_analytics(self):
        # Top merchants by volume
        self.volume_table.setRowCount(0)

        top_volume_merchants = self.merchant_manager.get_top_merchants_by_volume(10)

        self.volume_table.setRowCount(len(top_volume_merchants))

        for row, merchant in enumerate(top_volume_merchants):
            self.volume_table.setItem(row, 0, QTableWidgetItem(merchant.name))
            self.volume_table.setItem(row, 1, QTableWidgetItem(merchant.category.value))

            volume_item = QTableWidgetItem(f"${merchant.transaction_volume:.2f}")
            self.volume_table.setItem(row, 2, volume_item)

        # Top merchants by count
        self.count_table.setRowCount(0)

        top_count_merchants = self.merchant_manager.get_top_merchants_by_count(10)

        self.count_table.setRowCount(len(top_count_merchants))

        for row, merchant in enumerate(top_count_merchants):
            self.count_table.setItem(row, 0, QTableWidgetItem(merchant.name))
            self.count_table.setItem(row, 1, QTableWidgetItem(merchant.category.value))
            self.count_table.setItem(row, 2, QTableWidgetItem(str(merchant.transaction_count)))

    @pyqtSlot()
    def add_new_merchant(self):
        dialog = MerchantDetailsDialog(self.merchant_manager, parent=self)
        if dialog.exec():
            merchant_data = dialog.get_merchant_data()

            merchant_id = self.merchant_manager.create_merchant(
                name=merchant_data["name"],
                category=merchant_data["category"],
                contact_email=merchant_data["contact_email"],
                contact_phone=merchant_data["contact_phone"],
                address=merchant_data["address"],
                tax_id=merchant_data["tax_id"],
                status=merchant_data["status"],
                metadata=merchant_data["metadata"]
            )

            if merchant_id:
                merchant = self.merchant_manager.get_merchant(merchant_id)
                if merchant:
                    merchant.settlement_info = merchant_data["settlement_info"]

                QMessageBox.information(self, "Success", "Merchant created successfully.")
                self.refresh_merchants_table()
                self.refresh_merchant_combo()
            else:
                QMessageBox.warning(self, "Error", "Failed to create merchant.")

    @pyqtSlot()
    def view_merchant(self):
        button = self.sender()
        merchant_id = button.property("merchant_id")

        merchant = self.merchant_manager.get_merchant(merchant_id)
        if not merchant:
            QMessageBox.warning(self, "Error", "Merchant not found.")
            return

        # Find the merchant in the combo box and select it
        for i in range(self.merchant_combo.count()):
            if self.merchant_combo.itemData(i) == merchant_id:
                self.merchant_combo.setCurrentIndex(i)
                break

        # Switch to terminals tab
        self.tab_widget.setCurrentIndex(1)

    @pyqtSlot()
    def edit_merchant(self):
        button = self.sender()
        merchant_id = button.property("merchant_id")

        merchant = self.merchant_manager.get_merchant(merchant_id)
        if not merchant:
            QMessageBox.warning(self, "Error", "Merchant not found.")
            return

        dialog = MerchantDetailsDialog(self.merchant_manager, merchant, parent=self)
        if dialog.exec():
            merchant_data = dialog.get_merchant_data()

            updates = {
                "name": merchant_data["name"],
                "category": merchant_data["category"].value,
                "contact_email": merchant_data["contact_email"],
                "contact_phone": merchant_data["contact_phone"],
                "address": merchant_data["address"],
                "tax_id": merchant_data["tax_id"],
                "status": merchant_data["status"].value,
                "metadata": merchant_data["metadata"],
                "settlement_info": merchant_data["settlement_info"]
            }

            success = self.merchant_manager.update_merchant(merchant_id, updates)

            if success:
                QMessageBox.information(self, "Success", "Merchant updated successfully.")
                self.refresh_merchants_table()
                self.refresh_merchant_combo()
            else:
                QMessageBox.warning(self, "Error", "Failed to update merchant.")

    @pyqtSlot()
    def suspend_merchant(self):
        button = self.sender()
        merchant_id = button.property("merchant_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Suspension",
            "Are you sure you want to suspend this merchant?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.merchant_manager.change_merchant_status(merchant_id, MerchantStatus.SUSPENDED)

            if success:
                QMessageBox.information(self, "Success", "Merchant suspended successfully.")
                self.refresh_merchants_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to suspend merchant.")

    @pyqtSlot()
    def activate_merchant(self):
        button = self.sender()
        merchant_id = button.property("merchant_id")

        success = self.merchant_manager.change_merchant_status(merchant_id, MerchantStatus.ACTIVE)

        if success:
            QMessageBox.information(self, "Success", "Merchant activated successfully.")
            self.refresh_merchants_table()
        else:
            QMessageBox.warning(self, "Error", "Failed to activate merchant.")

    @pyqtSlot()
    def add_new_terminal(self):
        merchant_id = self.merchant_combo.currentData()
        if not merchant_id:
            QMessageBox.warning(self, "Error", "Please select a merchant first.")
            return

        dialog = TerminalDetailsDialog(self.merchant_manager, merchant_id, parent=self)
        if dialog.exec():
            terminal_data = dialog.get_terminal_data()

            terminal_id = self.merchant_manager.add_terminal(
                merchant_id=merchant_id,
                name=terminal_data["name"],
                terminal_type=terminal_data["terminal_type"],
                location=terminal_data["location"],
                serial_number=terminal_data["serial_number"],
                status=terminal_data["status"]
            )

            if terminal_id:
                QMessageBox.information(self, "Success", "Terminal added successfully.")
                self.refresh_terminals_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to add terminal.")

    @pyqtSlot()
    def edit_terminal(self):
        button = self.sender()
        terminal_id = button.property("terminal_id")

        terminal = self.merchant_manager.get_terminal(terminal_id)
        if not terminal:
            QMessageBox.warning(self, "Error", "Terminal not found.")
            return

        dialog = TerminalDetailsDialog(self.merchant_manager, terminal.merchant_id, terminal, parent=self)
        if dialog.exec():
            terminal_data = dialog.get_terminal_data()

            updates = {
                "name": terminal_data["name"],
                "terminal_type": terminal_data["terminal_type"],
                "location": terminal_data["location"],
                "serial_number": terminal_data["serial_number"],
                "status": terminal_data["status"]
            }

            success = self.merchant_manager.update_terminal(terminal_id, updates)

            if success:
                QMessageBox.information(self, "Success", "Terminal updated successfully.")
                self.refresh_terminals_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to update terminal.")

    @pyqtSlot()
    def delete_terminal(self):
        button = self.sender()
        terminal_id = button.property("terminal_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this terminal?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.merchant_manager.delete_terminal(terminal_id)

            if success:
                QMessageBox.information(self, "Success", "Terminal deleted successfully.")
                self.refresh_terminals_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete terminal.")

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QHeaderView, QTextEdit,
    QMessageBox, QTabWidget, QDialog, QDialogButtonBox, QCheckBox, QDateEdit
)
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor

from ..app.customer_management import (CustomerType, CustomerStatus,
)


class CustomerDetailsDialog(QDialog):
    def __init__(self, customer_manager, customer=None, parent=None):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.customer = customer
        self.setWindowTitle("Customer Details" if customer else "Add New Customer")
        self.setMinimumWidth(600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Customer info form
        form_layout = QFormLayout()

        self.first_name_input = QLineEdit()
        form_layout.addRow("First Name:", self.first_name_input)

        self.last_name_input = QLineEdit()
        form_layout.addRow("Last Name:", self.last_name_input)

        self.email_input = QLineEdit()
        form_layout.addRow("Email:", self.email_input)

        self.phone_input = QLineEdit()
        form_layout.addRow("Phone:", self.phone_input)

        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("Address:", self.address_input)

        self.customer_type_combo = QComboBox()
        for ctype in CustomerType:
            self.customer_type_combo.addItem(ctype.value)
        form_layout.addRow("Customer Type:", self.customer_type_combo)

        self.status_combo = QComboBox()
        for status in CustomerStatus:
            self.status_combo.addItem(status.value)
        form_layout.addRow("Status:", self.status_combo)

        self.tax_id_input = QLineEdit()
        form_layout.addRow("Tax ID:", self.tax_id_input)

        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDate(datetime.now().date())
        form_layout.addRow("Date of Birth:", self.dob_input)

        # Additional metadata
        metadata_group = QGroupBox("Additional Information")
        metadata_layout = QFormLayout()

        self.kyc_verified_checkbox = QCheckBox("KYC Verified")
        metadata_layout.addRow(self.kyc_verified_checkbox)

        self.risk_score_input = QComboBox()
        self.risk_score_input.addItems(["0 - Low", "1 - Low-Medium", "2 - Medium", "3 - Medium-High", "4 - High"])
        metadata_layout.addRow("Risk Score:", self.risk_score_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        metadata_layout.addRow("Notes:", self.notes_input)

        metadata_group.setLayout(metadata_layout)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        # Add all components to main layout
        layout.addLayout(form_layout)
        layout.addWidget(metadata_group)
        layout.addWidget(button_box)

        # If editing an existing customer, populate fields
        if self.customer:
            self.first_name_input.setText(self.customer.first_name)
            self.last_name_input.setText(self.customer.last_name)
            self.email_input.setText(self.customer.email)
            self.phone_input.setText(self.customer.phone)
            self.address_input.setText(self.customer.address)

            type_index = self.customer_type_combo.findText(self.customer.customer_type.value)
            if type_index >= 0:
                self.customer_type_combo.setCurrentIndex(type_index)

            status_index = self.status_combo.findText(self.customer.status.value)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

            self.tax_id_input.setText(self.customer.tax_id)

            if self.customer.date_of_birth:
                self.dob_input.setDate(self.customer.date_of_birth.date())

            self.kyc_verified_checkbox.setChecked(self.customer.kyc_verified)

            risk_index = min(self.customer.risk_score, 4)
            self.risk_score_input.setCurrentIndex(risk_index)

            self.notes_input.setText(self.customer.metadata.get("notes", ""))

    @pyqtSlot()
    def validate_and_accept(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()

        if not first_name:
            QMessageBox.warning(self, "Input Error", "First name is required.")
            return

        if not last_name:
            QMessageBox.warning(self, "Input Error", "Last name is required.")
            return

        if not email:
            QMessageBox.warning(self, "Input Error", "Email is required.")
            return

        if not phone:
            QMessageBox.warning(self, "Input Error", "Phone is required.")
            return

        if not address:
            QMessageBox.warning(self, "Input Error", "Address is required.")
            return

        self.accept()

    def get_customer_data(self):
        customer_type = None
        for ct in CustomerType:
            if ct.value == self.customer_type_combo.currentText():
                customer_type = ct
                break

        status = None
        for s in CustomerStatus:
            if s.value == self.status_combo.currentText():
                status = s
                break

        dob = self.dob_input.date().toPyDate()
        dob_datetime = datetime.combine(dob, datetime.min.time())

        risk_score = self.risk_score_input.currentIndex()

        metadata = {
            "notes": self.notes_input.toPlainText().strip()
        }

        data = {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.toPlainText().strip(),
            "customer_type": customer_type,
            "status": status,
            "tax_id": self.tax_id_input.text().strip(),
            "date_of_birth": dob_datetime,
            "metadata": metadata,
            "kyc_verified": self.kyc_verified_checkbox.isChecked(),
            "risk_score": risk_score
        }

        return data


class AccountDetailsDialog(QDialog):
    def __init__(self, customer_manager, customer_id, account=None, parent=None):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.customer_id = customer_id
        self.account = account
        self.setWindowTitle("Account Details" if account else "Add New Account")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.account_number_input = QLineEdit()
        form_layout.addRow("Account Number:", self.account_number_input)

        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems([
            "Checking", "Savings", "Credit Card", "Loan", "Investment", "Other"
        ])
        form_layout.addRow("Account Type:", self.account_type_combo)

        self.balance_input = QLineEdit()
        self.balance_input.setText("0.00")
        form_layout.addRow("Balance:", self.balance_input)

        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "JPY", "CAD", "AUD"])
        form_layout.addRow("Currency:", self.currency_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Suspended", "Closed"])
        form_layout.addRow("Status:", self.status_combo)

        self.overdraft_limit_input = QLineEdit()
        self.overdraft_limit_input.setText("0.00")
        form_layout.addRow("Overdraft Limit:", self.overdraft_limit_input)

        self.interest_rate_input = QLineEdit()
        self.interest_rate_input.setText("0.00")
        form_layout.addRow("Interest Rate (%):", self.interest_rate_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        # If editing an existing account, populate fields
        if self.account:
            self.account_number_input.setText(self.account.account_number)

            type_index = self.account_type_combo.findText(self.account.account_type)
            if type_index >= 0:
                self.account_type_combo.setCurrentIndex(type_index)

            self.balance_input.setText(f"{self.account.balance:.2f}")

            currency_index = self.currency_combo.findText(self.account.currency)
            if currency_index >= 0:
                self.currency_combo.setCurrentIndex(currency_index)

            status_index = self.status_combo.findText(self.account.status)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

            self.overdraft_limit_input.setText(f"{self.account.overdraft_limit:.2f}")
            self.interest_rate_input.setText(f"{self.account.interest_rate:.2f}")

    @pyqtSlot()
    def validate_and_accept(self):
        account_number = self.account_number_input.text().strip()

        if not account_number:
            QMessageBox.warning(self, "Input Error", "Account number is required.")
            return

        try:
            balance = float(self.balance_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Balance must be a valid number.")
            return

        try:
            overdraft_limit = float(self.overdraft_limit_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Overdraft limit must be a valid number.")
            return

        try:
            interest_rate = float(self.interest_rate_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Interest rate must be a valid number.")
            return

        self.accept()

    def get_account_data(self):
        try:
            balance = float(self.balance_input.text().strip())
        except ValueError:
            balance = 0.0

        try:
            overdraft_limit = float(self.overdraft_limit_input.text().strip())
        except ValueError:
            overdraft_limit = 0.0

        try:
            interest_rate = float(self.interest_rate_input.text().strip())
        except ValueError:
            interest_rate = 0.0

        data = {
            "account_number": self.account_number_input.text().strip(),
            "account_type": self.account_type_combo.currentText(),
            "balance": balance,
            "currency": self.currency_combo.currentText(),
            "status": self.status_combo.currentText(),
            "overdraft_limit": overdraft_limit,
            "interest_rate": interest_rate
        }

        return data


class CustomerManagementWidget(QWidget):
    def __init__(self, customer_manager, parent=None):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.logger = logging.getLogger("fintechx_desktop.ui.customer_management")

        main_layout = QVBoxLayout(self)

        # Create tabs for different views
        self.tab_widget = QTabWidget()

        # Create the customers list tab
        self.customers_list_widget = QWidget()
        self.setup_customers_list_tab()
        self.tab_widget.addTab(self.customers_list_widget, "Customers")

        # Create the accounts tab
        self.accounts_widget = QWidget()
        self.setup_accounts_tab()
        self.tab_widget.addTab(self.accounts_widget, "Accounts")

        # Create the analytics tab
        self.analytics_widget = QWidget()
        self.setup_analytics_tab()
        self.tab_widget.addTab(self.analytics_widget, "Analytics")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def setup_customers_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_group = QGroupBox("Filter Customers")
        filter_layout = QHBoxLayout()

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        for ctype in CustomerType:
            self.type_filter.addItem(ctype.value)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        for status in CustomerStatus:
            self.status_filter.addItem(status.value)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers...")

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.refresh_customers_table)

        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.apply_filter_button)
        filter_group.setLayout(filter_layout)

        # Customers table
        self.customers_table = QTableWidget(0, 7)
        self.customers_table.setHorizontalHeaderLabels([
            "Name", "Type", "Contact", "Status", "KYC", "Risk Score", "Actions"
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_customers_table)

        self.add_customer_button = QPushButton("Add New Customer")
        self.add_customer_button.clicked.connect(self.add_new_customer)

        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.add_customer_button)

        layout.addWidget(filter_group)
        layout.addWidget(self.customers_table)
        layout.addLayout(action_layout)

        self.customers_list_widget.setLayout(layout)

        # Initial data load
        self.refresh_customers_table()

    def setup_accounts_tab(self):
        layout = QVBoxLayout()

        # Customer selection
        customer_group = QGroupBox("Select Customer")
        customer_layout = QHBoxLayout()

        self.customer_combo = QComboBox()
        self.refresh_customer_combo()

        self.refresh_customer_combo_button = QPushButton("Refresh")
        self.refresh_customer_combo_button.clicked.connect(self.refresh_customer_combo)

        customer_layout.addWidget(QLabel("Customer:"))
        customer_layout.addWidget(self.customer_combo, 1)
        customer_layout.addWidget(self.refresh_customer_combo_button)
        customer_group.setLayout(customer_layout)

        # Accounts table
        self.accounts_table = QTableWidget(0, 6)
        self.accounts_table.setHorizontalHeaderLabels([
            "Account Number", "Type", "Balance", "Currency", "Status", "Actions"
        ])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.accounts_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_accounts_button = QPushButton("Refresh Accounts")
        self.refresh_accounts_button.clicked.connect(self.refresh_accounts_table)

        self.add_account_button = QPushButton("Add New Account")
        self.add_account_button.clicked.connect(self.add_new_account)

        action_layout.addWidget(self.refresh_accounts_button)
        action_layout.addWidget(self.add_account_button)

        layout.addWidget(customer_group)
        layout.addWidget(self.accounts_table)
        layout.addLayout(action_layout)

        self.accounts_widget.setLayout(layout)

        # Connect customer selection change
        self.customer_combo.currentIndexChanged.connect(self.refresh_accounts_table)

    def setup_analytics_tab(self):
        layout = QVBoxLayout()

        # Top customers by volume
        volume_group = QGroupBox("Top Customers by Transaction Volume")
        volume_layout = QVBoxLayout()

        self.volume_table = QTableWidget(0, 3)
        self.volume_table.setHorizontalHeaderLabels([
            "Customer", "Type", "Transaction Volume"
        ])
        self.volume_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        volume_layout.addWidget(self.volume_table)
        volume_group.setLayout(volume_layout)

        # Top customers by count
        count_group = QGroupBox("Top Customers by Transaction Count")
        count_layout = QVBoxLayout()

        self.count_table = QTableWidget(0, 3)
        self.count_table.setHorizontalHeaderLabels([
            "Customer", "Type", "Transaction Count"
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
        if index == 0:  # Customers tab
            self.refresh_customers_table()
        elif index == 1:  # Accounts tab
            self.refresh_customer_combo()
            self.refresh_accounts_table()
        elif index == 2:  # Analytics tab
            self.refresh_analytics()

    @pyqtSlot()
    def refresh_customers_table(self):
        self.customers_table.setRowCount(0)

        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()
        search_text = self.search_input.text().strip().lower()

        customers = self.customer_manager.get_all_customers()

        # Apply type filter
        if type_filter != "All Types":
            customer_type = None
            for ct in CustomerType:
                if ct.value == type_filter:
                    customer_type = ct
                    break
            if customer_type:
                customers = [c for c in customers if c.customer_type == customer_type]

        # Apply status filter
        if status_filter != "All Statuses":
            status = None
            for s in CustomerStatus:
                if s.value == status_filter:
                    status = s
                    break
            if status:
                customers = [c for c in customers if c.status == status]

        # Apply search filter
        if search_text:
            customers = self.customer_manager.search_customers(search_text)

        self.customers_table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            self.customers_table.setItem(row, 0, QTableWidgetItem(customer.full_name))
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer.customer_type.value))

            contact_info = f"{customer.email}\n{customer.phone}"
            self.customers_table.setItem(row, 2, QTableWidgetItem(contact_info))

            status_item = QTableWidgetItem(customer.status.value)
            if customer.status == CustomerStatus.ACTIVE:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif customer.status == CustomerStatus.INACTIVE:
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            elif customer.status == CustomerStatus.SUSPENDED:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif customer.status == CustomerStatus.CLOSED:
                status_item.setBackground(QColor(200, 200, 200))  # Light gray

            self.customers_table.setItem(row, 3, status_item)

            kyc_item = QTableWidgetItem("Verified" if customer.kyc_verified else "Not Verified")
            if customer.kyc_verified:
                kyc_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                kyc_item.setBackground(QColor(255, 200, 200))  # Light red

            self.customers_table.setItem(row, 4, kyc_item)

            risk_score_item = QTableWidgetItem(str(customer.risk_score))
            if customer.risk_score <= 1:
                risk_score_item.setBackground(QColor(200, 255, 200))  # Light green
            elif customer.risk_score <= 2:
                risk_score_item.setBackground(QColor(255, 255, 200))  # Light yellow
            else:
                risk_score_item.setBackground(QColor(255, 200, 200))  # Light red

            self.customers_table.setItem(row, 5, risk_score_item)

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_button = QPushButton("View")
            view_button.setProperty("customer_id", customer.id)
            view_button.clicked.connect(self.view_customer)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("customer_id", customer.id)
            edit_button.clicked.connect(self.edit_customer)

            if customer.status == CustomerStatus.ACTIVE:
                suspend_button = QPushButton("Suspend")
                suspend_button.setProperty("customer_id", customer.id)
                suspend_button.clicked.connect(self.suspend_customer)
                actions_layout.addWidget(suspend_button)
            elif customer.status == CustomerStatus.SUSPENDED:
                activate_button = QPushButton("Activate")
                activate_button.setProperty("customer_id", customer.id)
                activate_button.clicked.connect(self.activate_customer)
                actions_layout.addWidget(activate_button)

            actions_layout.addWidget(view_button)
            actions_layout.addWidget(edit_button)

            self.customers_table.setCellWidget(row, 6, actions_widget)

    @pyqtSlot()
    def refresh_customer_combo(self):
        current_text = self.customer_combo.currentText()

        self.customer_combo.clear()
        self.customer_combo.addItem("Select a customer...")

        customers = self.customer_manager.get_all_customers()
        for customer in customers:
            self.customer_combo.addItem(customer.full_name, customer.id)

        # Try to restore previous selection
        if current_text:
            index = self.customer_combo.findText(current_text)
            if index >= 0:
                self.customer_combo.setCurrentIndex(index)

    @pyqtSlot()
    def refresh_accounts_table(self):
        self.accounts_table.setRowCount(0)

        customer_id = self.customer_combo.currentData()
        if not customer_id:
            return

        accounts = self.customer_manager.get_customer_accounts(customer_id)

        self.accounts_table.setRowCount(len(accounts))

        for row, account in enumerate(accounts):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account.account_number))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account.account_type))

            balance_item = QTableWidgetItem(f"{account.balance:.2f}")
            if account.balance < 0:
                balance_item.setForeground(QColor(255, 0, 0))  # Red text for negative balance

            self.accounts_table.setItem(row, 2, balance_item)
            self.accounts_table.setItem(row, 3, QTableWidgetItem(account.currency))

            status_item = QTableWidgetItem(account.status)
            if account.status == "Active":
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif account.status == "Inactive":
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            elif account.status == "Suspended":
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif account.status == "Closed":
                status_item.setBackground(QColor(200, 200, 200))  # Light gray

            self.accounts_table.setItem(row, 4, status_item)

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("account_id", account.id)
            edit_button.clicked.connect(self.edit_account)

            delete_button = QPushButton("Delete")
            delete_button.setProperty("account_id", account.id)
            delete_button.clicked.connect(self.delete_account)

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)

            self.accounts_table.setCellWidget(row, 5, actions_widget)

    @pyqtSlot()
    def refresh_analytics(self):
        # Top customers by volume
        self.volume_table.setRowCount(0)

        top_volume_customers = self.customer_manager.get_top_customers_by_volume(10)

        self.volume_table.setRowCount(len(top_volume_customers))

        for row, customer in enumerate(top_volume_customers):
            self.volume_table.setItem(row, 0, QTableWidgetItem(customer.full_name))
            self.volume_table.setItem(row, 1, QTableWidgetItem(customer.customer_type.value))

            volume_item = QTableWidgetItem(f"${customer.total_transaction_volume:.2f}")
            self.volume_table.setItem(row, 2, volume_item)

        # Top customers by count
        self.count_table.setRowCount(0)

        top_count_customers = self.customer_manager.get_top_customers_by_count(10)

        self.count_table.setRowCount(len(top_count_customers))

        for row, customer in enumerate(top_count_customers):
            self.count_table.setItem(row, 0, QTableWidgetItem(customer.full_name))
            self.count_table.setItem(row, 1, QTableWidgetItem(customer.customer_type.value))
            self.count_table.setItem(row, 2, QTableWidgetItem(str(customer.total_transaction_count)))

    @pyqtSlot()
    def add_new_customer(self):
        dialog = CustomerDetailsDialog(self.customer_manager, parent=self)
        if dialog.exec():
            customer_data = dialog.get_customer_data()

            customer_id = self.customer_manager.create_customer(
                first_name=customer_data["first_name"],
                last_name=customer_data["last_name"],
                email=customer_data["email"],
                phone=customer_data["phone"],
                address=customer_data["address"],
                customer_type=customer_data["customer_type"],
                status=customer_data["status"],
                tax_id=customer_data["tax_id"],
                date_of_birth=customer_data["date_of_birth"],
                metadata=customer_data["metadata"]
            )

            if customer_id:
                customer = self.customer_manager.get_customer(customer_id)
                if customer:
                    customer.kyc_verified = customer_data["kyc_verified"]
                    customer.risk_score = customer_data["risk_score"]

                QMessageBox.information(self, "Success", "Customer created successfully.")
                self.refresh_customers_table()
                self.refresh_customer_combo()
            else:
                QMessageBox.warning(self, "Error", "Failed to create customer.")

    @pyqtSlot()
    def view_customer(self):
        button = self.sender()
        customer_id = button.property("customer_id")

        customer = self.customer_manager.get_customer(customer_id)
        if not customer:
            QMessageBox.warning(self, "Error", "Customer not found.")
            return

        # Find the customer in the combo box and select it
        for i in range(self.customer_combo.count()):
            if self.customer_combo.itemData(i) == customer_id:
                self.customer_combo.setCurrentIndex(i)
                break

        # Switch to accounts tab
        self.tab_widget.setCurrentIndex(1)

    @pyqtSlot()
    def edit_customer(self):
        button = self.sender()
        customer_id = button.property("customer_id")

        customer = self.customer_manager.get_customer(customer_id)
        if not customer:
            QMessageBox.warning(self, "Error", "Customer not found.")
            return

        dialog = CustomerDetailsDialog(self.customer_manager, customer, parent=self)
        if dialog.exec():
            customer_data = dialog.get_customer_data()

            updates = {
                "first_name": customer_data["first_name"],
                "last_name": customer_data["last_name"],
                "email": customer_data["email"],
                "phone": customer_data["phone"],
                "address": customer_data["address"],
                "customer_type": customer_data["customer_type"].value,
                "status": customer_data["status"].value,
                "tax_id": customer_data["tax_id"],
                "date_of_birth": customer_data["date_of_birth"].isoformat(),
                "metadata": customer_data["metadata"],
                "kyc_verified": customer_data["kyc_verified"],
                "risk_score": customer_data["risk_score"]
            }

            success = self.customer_manager.update_customer(customer_id, updates)

            if success:
                QMessageBox.information(self, "Success", "Customer updated successfully.")
                self.refresh_customers_table()
                self.refresh_customer_combo()
            else:
                QMessageBox.warning(self, "Error", "Failed to update customer.")

    @pyqtSlot()
    def suspend_customer(self):
        button = self.sender()
        customer_id = button.property("customer_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Suspension",
            "Are you sure you want to suspend this customer?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.customer_manager.change_customer_status(customer_id, CustomerStatus.SUSPENDED)

            if success:
                QMessageBox.information(self, "Success", "Customer suspended successfully.")
                self.refresh_customers_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to suspend customer.")

    @pyqtSlot()
    def activate_customer(self):
        button = self.sender()
        customer_id = button.property("customer_id")

        success = self.customer_manager.change_customer_status(customer_id, CustomerStatus.ACTIVE)

        if success:
            QMessageBox.information(self, "Success", "Customer activated successfully.")
            self.refresh_customers_table()
        else:
            QMessageBox.warning(self, "Error", "Failed to activate customer.")

    @pyqtSlot()
    def add_new_account(self):
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            QMessageBox.warning(self, "Error", "Please select a customer first.")
            return

        dialog = AccountDetailsDialog(self.customer_manager, customer_id, parent=self)
        if dialog.exec():
            account_data = dialog.get_account_data()

            account_id = self.customer_manager.create_account(
                customer_id=customer_id,
                account_number=account_data["account_number"],
                account_type=account_data["account_type"],
                balance=account_data["balance"],
                currency=account_data["currency"],
                status=account_data["status"]
            )

            if account_id:
                account = self.customer_manager.get_account(account_id)
                if account:
                    account.overdraft_limit = account_data["overdraft_limit"]
                    account.interest_rate = account_data["interest_rate"]

                QMessageBox.information(self, "Success", "Account added successfully.")
                self.refresh_accounts_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to add account.")

    @pyqtSlot()
    def edit_account(self):
        button = self.sender()
        account_id = button.property("account_id")

        account = self.customer_manager.get_account(account_id)
        if not account:
            QMessageBox.warning(self, "Error", "Account not found.")
            return

        dialog = AccountDetailsDialog(self.customer_manager, account.customer_id, account, parent=self)
        if dialog.exec():
            account_data = dialog.get_account_data()

            updates = {
                "account_number": account_data["account_number"],
                "account_type": account_data["account_type"],
                "balance": account_data["balance"],
                "currency": account_data["currency"],
                "status": account_data["status"],
                "overdraft_limit": account_data["overdraft_limit"],
                "interest_rate": account_data["interest_rate"]
            }

            success = self.customer_manager.update_account(account_id, updates)

            if success:
                QMessageBox.information(self, "Success", "Account updated successfully.")
                self.refresh_accounts_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to update account.")

    @pyqtSlot()
    def delete_account(self):
        button = self.sender()
        account_id = button.property("account_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.customer_manager.delete_account(account_id)

            if success:
                QMessageBox.information(self, "Success", "Account deleted successfully.")
                self.refresh_accounts_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete account.")

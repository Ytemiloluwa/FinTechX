import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox, QLineEdit,
    QHeaderView, QTextEdit, QDateEdit, QCheckBox, QDialog, QDialogButtonBox,
    QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSlot, QDate

from ..app.bill_payment import BillPaymentManager, Bill, BillStatus, PaymentMethod


class BillPaymentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("fintechx_desktop.ui.bill_payment")
        self.bill_manager = BillPaymentManager()

        main_layout = QVBoxLayout(self)

        # Create tabs for different views
        self.tab_widget = QTabWidget()

        # Create the bills list tab
        self.bills_list_widget = QWidget()
        self.setup_bills_list_tab()
        self.tab_widget.addTab(self.bills_list_widget, "Bills")

        # Create the add/edit bill tab
        self.bill_form_widget = QWidget()
        self.setup_bill_form_tab()
        self.tab_widget.addTab(self.bill_form_widget, "Add/Edit Bill")

        # Create the payment tab
        self.payment_widget = QWidget()
        self.setup_payment_tab()
        self.tab_widget.addTab(self.payment_widget, "Payments")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Initialize with some sample data
        self.load_sample_data()

    def load_sample_data(self):
        # Add a few sample bills for demonstration
        bill1 = Bill(
            payee="Electric Company",
            amount=125.50,
            due_date=datetime.now() + timedelta(days=5),
            description="Monthly electricity bill",
            category="Utilities"
        )

        bill2 = Bill(
            payee="Internet Provider",
            amount=79.99,
            due_date=datetime.now() + timedelta(days=10),
            description="High-speed internet",
            category="Utilities",
            recurring=True,
            frequency="Monthly"
        )

        bill3 = Bill(
            payee="Credit Card Company",
            amount=350.00,
            due_date=datetime.now() + timedelta(days=15),
            description="Credit card payment",
            category="Credit"
        )

        self.bill_manager.add_bill(bill1)
        self.bill_manager.add_bill(bill2)
        self.bill_manager.add_bill(bill3)

        self.refresh_bills_table()

    def setup_bills_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_group = QGroupBox("Filter Bills")
        filter_layout = QHBoxLayout()

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        for status in BillStatus:
            self.status_filter.addItem(status.value)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["All Categories", "Utilities", "Rent", "Insurance", "Credit", "Other"])

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.refresh_bills_table)

        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(self.apply_filter_button)
        filter_group.setLayout(filter_layout)

        # Bills table
        self.bills_table = QTableWidget(0, 7)
        self.bills_table.setHorizontalHeaderLabels([
            "Payee", "Amount", "Due Date", "Category", "Status", "Actions", "ID"
        ])
        self.bills_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.bills_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.bills_table.setColumnHidden(6, True)  # Hide ID column

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_bills_table)
        self.add_bill_button = QPushButton("Add New Bill")
        self.add_bill_button.clicked.connect(self.show_add_bill_form)

        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.add_bill_button)

        layout.addWidget(filter_group)
        layout.addWidget(self.bills_table)
        layout.addLayout(action_layout)

        self.bills_list_widget.setLayout(layout)

    def setup_bill_form_tab(self):
        layout = QFormLayout()

        self.payee_input = QLineEdit()
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 10000.00)
        self.amount_input.setPrefix("$")
        self.amount_input.setDecimals(2)

        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addDays(7))

        self.description_input = QLineEdit()

        self.category_input = QComboBox()
        self.category_input.addItems(["Utilities", "Rent", "Insurance", "Credit", "Other"])

        self.recurring_input = QCheckBox("Recurring Bill")

        self.frequency_input = QComboBox()
        self.frequency_input.addItems(["Weekly", "Bi-weekly", "Monthly", "Quarterly", "Annually"])
        self.frequency_input.setEnabled(False)

        self.recurring_input.stateChanged.connect(
            lambda state: self.frequency_input.setEnabled(state == Qt.CheckState.Checked)
        )

        self.save_bill_button = QPushButton("Save Bill")
        self.save_bill_button.clicked.connect(self.save_bill)

        self.clear_form_button = QPushButton("Clear Form")
        self.clear_form_button.clicked.connect(self.clear_bill_form)

        self.current_bill_id = None

        layout.addRow("Payee:", self.payee_input)
        layout.addRow("Amount:", self.amount_input)
        layout.addRow("Due Date:", self.due_date_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Category:", self.category_input)
        layout.addRow("", self.recurring_input)
        layout.addRow("Frequency:", self.frequency_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_bill_button)
        button_layout.addWidget(self.clear_form_button)
        layout.addRow("", button_layout)

        self.bill_form_widget.setLayout(layout)

    def setup_payment_tab(self):
        layout = QVBoxLayout()

        # Payment scheduling
        schedule_group = QGroupBox("Schedule Payment")
        schedule_layout = QFormLayout()

        self.bill_selector = QComboBox()
        self.payment_date_input = QDateEdit()
        self.payment_date_input.setCalendarPopup(True)
        self.payment_date_input.setDate(QDate.currentDate())

        self.payment_method_input = QComboBox()
        for method in PaymentMethod:
            self.payment_method_input.addItem(method.value)

        self.schedule_button = QPushButton("Schedule Payment")
        self.schedule_button.clicked.connect(self.schedule_payment)

        schedule_layout.addRow("Select Bill:", self.bill_selector)
        schedule_layout.addRow("Payment Date:", self.payment_date_input)
        schedule_layout.addRow("Payment Method:", self.payment_method_input)
        schedule_layout.addRow("", self.schedule_button)

        schedule_group.setLayout(schedule_layout)

        # Scheduled payments
        payments_group = QGroupBox("Scheduled Payments")
        payments_layout = QVBoxLayout()

        self.payments_table = QTableWidget(0, 5)
        self.payments_table.setHorizontalHeaderLabels([
            "Payee", "Amount", "Payment Date", "Method", "Actions"
        ])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.payments_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.refresh_payments_button = QPushButton("Refresh Payments")
        self.refresh_payments_button.clicked.connect(self.refresh_payments_table)

        payments_layout.addWidget(self.payments_table)
        payments_layout.addWidget(self.refresh_payments_button)

        payments_group.setLayout(payments_layout)

        layout.addWidget(schedule_group)
        layout.addWidget(payments_group)

        self.payment_widget.setLayout(layout)

    @pyqtSlot()
    def refresh_bills_table(self):
        self.bills_table.setRowCount(0)

        status_filter = self.status_filter.currentText()
        category_filter = self.category_filter.currentText()

        bills = self.bill_manager.get_all_bills()

        if status_filter != "All Statuses":
            bills = [b for b in bills if b.status.value == status_filter]

        if category_filter != "All Categories":
            bills = [b for b in bills if b.category == category_filter]

        self.bills_table.setRowCount(len(bills))

        for row, bill in enumerate(bills):
            self.bills_table.setItem(row, 0, QTableWidgetItem(bill.payee))

            amount_item = QTableWidgetItem(f"${bill.amount:.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.bills_table.setItem(row, 1, amount_item)

            due_date = bill.due_date.strftime("%Y-%m-%d")
            self.bills_table.setItem(row, 2, QTableWidgetItem(due_date))

            self.bills_table.setItem(row, 3, QTableWidgetItem(bill.category))

            status_item = QTableWidgetItem(bill.status.value)
            if bill.status == BillStatus.PAID:
                status_item.setBackground(Qt.GlobalColor.green)
            elif bill.status == BillStatus.SCHEDULED:
                status_item.setBackground(Qt.GlobalColor.cyan)
            elif bill.status == BillStatus.FAILED:
                status_item.setBackground(Qt.GlobalColor.red)
            elif bill.due_date < datetime.now():
                status_item.setBackground(Qt.GlobalColor.yellow)

            self.bills_table.setItem(row, 4, status_item)

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("bill_id", bill.id)
            edit_button.clicked.connect(self.edit_bill)

            delete_button = QPushButton("Delete")
            delete_button.setProperty("bill_id", bill.id)
            delete_button.clicked.connect(self.delete_bill)

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)

            self.bills_table.setCellWidget(row, 5, actions_widget)
            self.bills_table.setItem(row, 6, QTableWidgetItem(bill.id))

        self.refresh_bill_selector()
        self.refresh_payments_table()

    @pyqtSlot()
    def refresh_payments_table(self):
        self.payments_table.setRowCount(0)

        scheduled_bills = self.bill_manager.get_bills_by_status(BillStatus.SCHEDULED)

        self.payments_table.setRowCount(len(scheduled_bills))

        for row, bill in enumerate(scheduled_bills):
            self.payments_table.setItem(row, 0, QTableWidgetItem(bill.payee))

            amount_item = QTableWidgetItem(f"${bill.amount:.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.payments_table.setItem(row, 1, amount_item)

            payment_date = bill.payment_date.strftime("%Y-%m-%d") if bill.payment_date else ""
            self.payments_table.setItem(row, 2, QTableWidgetItem(payment_date))

            method = bill.payment_method.value if bill.payment_method else ""
            self.payments_table.setItem(row, 3, QTableWidgetItem(method))

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            process_button = QPushButton("Process")
            process_button.setProperty("bill_id", bill.id)
            process_button.clicked.connect(self.process_payment)

            cancel_button = QPushButton("Cancel")
            cancel_button.setProperty("bill_id", bill.id)
            cancel_button.clicked.connect(self.cancel_payment)

            actions_layout.addWidget(process_button)
            actions_layout.addWidget(cancel_button)

            self.payments_table.setCellWidget(row, 4, actions_widget)

    def refresh_bill_selector(self):
        self.bill_selector.clear()

        pending_bills = self.bill_manager.get_bills_by_status(BillStatus.PENDING)
        failed_bills = self.bill_manager.get_bills_by_status(BillStatus.FAILED)

        bills = pending_bills + failed_bills

        for bill in bills:
            self.bill_selector.addItem(f"{bill.payee} - ${bill.amount:.2f} - Due: {bill.due_date.strftime('%Y-%m-%d')}",
                                       bill.id)

    @pyqtSlot()
    def show_add_bill_form(self):
        self.tab_widget.setCurrentIndex(1)
        self.clear_bill_form()

    @pyqtSlot()
    def clear_bill_form(self):
        self.payee_input.clear()
        self.amount_input.setValue(0.01)
        self.due_date_input.setDate(QDate.currentDate().addDays(7))
        self.description_input.clear()
        self.category_input.setCurrentIndex(0)
        self.recurring_input.setChecked(False)
        self.frequency_input.setCurrentIndex(0)
        self.frequency_input.setEnabled(False)
        self.current_bill_id = None

    @pyqtSlot()
    def save_bill(self):
        payee = self.payee_input.text().strip()
        amount = self.amount_input.value()
        due_date_qdate = self.due_date_input.date()
        due_date = datetime(due_date_qdate.year(), due_date_qdate.month(), due_date_qdate.day())
        description = self.description_input.text().strip()
        category = self.category_input.currentText()
        recurring = self.recurring_input.isChecked()
        frequency = self.frequency_input.currentText() if recurring else None

        if not payee:
            QMessageBox.warning(self, "Input Error", "Payee name is required.")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Input Error", "Amount must be greater than zero.")
            return

        if due_date < datetime.now():
            QMessageBox.warning(self, "Input Error", "Due date must be in the future.")
            return

        if self.current_bill_id:
            # Update existing bill
            updates = {
                "payee": payee,
                "amount": amount,
                "due_date": due_date,
                "description": description,
                "category": category,
                "recurring": recurring,
                "frequency": frequency
            }

            success = self.bill_manager.update_bill(self.current_bill_id, updates)

            if success:
                QMessageBox.information(self, "Success", "Bill updated successfully.")
                self.clear_bill_form()
                self.refresh_bills_table()
                self.tab_widget.setCurrentIndex(0)
            else:
                QMessageBox.warning(self, "Error", "Failed to update bill.")
        else:
            # Create new bill
            bill = Bill(
                payee=payee,
                amount=amount,
                due_date=due_date,
                description=description,
                category=category,
                recurring=recurring,
                frequency=frequency
            )

            bill_id = self.bill_manager.add_bill(bill)

            if bill_id:
                QMessageBox.information(self, "Success", "Bill added successfully.")
                self.clear_bill_form()
                self.refresh_bills_table()
                self.tab_widget.setCurrentIndex(0)
            else:
                QMessageBox.warning(self, "Error", "Failed to add bill.")

    @pyqtSlot()
    def edit_bill(self):
        button = self.sender()
        bill_id = button.property("bill_id")

        bill = self.bill_manager.get_bill(bill_id)
        if not bill:
            QMessageBox.warning(self, "Error", "Bill not found.")
            return

        self.current_bill_id = bill_id
        self.payee_input.setText(bill.payee)
        self.amount_input.setValue(bill.amount)

        due_date = bill.due_date
        self.due_date_input.setDate(QDate(due_date.year, due_date.month, due_date.day))

        self.description_input.setText(bill.description)

        category_index = self.category_input.findText(bill.category)
        if category_index >= 0:
            self.category_input.setCurrentIndex(category_index)

        self.recurring_input.setChecked(bill.recurring)

        if bill.frequency:
            frequency_index = self.frequency_input.findText(bill.frequency)
            if frequency_index >= 0:
                self.frequency_input.setCurrentIndex(frequency_index)

        self.frequency_input.setEnabled(bill.recurring)

        self.tab_widget.setCurrentIndex(1)

    @pyqtSlot()
    def delete_bill(self):
        button = self.sender()
        bill_id = button.property("bill_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this bill?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.bill_manager.delete_bill(bill_id)

            if success:
                QMessageBox.information(self, "Success", "Bill deleted successfully.")
                self.refresh_bills_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete bill.")

    @pyqtSlot()
    def schedule_payment(self):
        if self.bill_selector.count() == 0:
            QMessageBox.warning(self, "Error", "No bills available for payment.")
            return

        bill_id = self.bill_selector.currentData()

        payment_date_qdate = self.payment_date_input.date()
        payment_date = datetime(payment_date_qdate.year(), payment_date_qdate.month(), payment_date_qdate.day())

        payment_method_text = self.payment_method_input.currentText()
        payment_method = None

        for method in PaymentMethod:
            if method.value == payment_method_text:
                payment_method = method
                break

        if not payment_method:
            QMessageBox.warning(self, "Error", "Invalid payment method.")
            return

        if payment_date < datetime.now():
            QMessageBox.warning(self, "Input Error", "Payment date must be today or in the future.")
            return

        success = self.bill_manager.schedule_payment(bill_id, payment_date, payment_method)

        if success:
            QMessageBox.information(self, "Success", "Payment scheduled successfully.")
            self.refresh_bills_table()
            self.tab_widget.setCurrentIndex(2)
        else:
            QMessageBox.warning(self, "Error", "Failed to schedule payment.")

    @pyqtSlot()
    def process_payment(self):
        button = self.sender()
        bill_id = button.property("bill_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Payment",
            "Are you sure you want to process this payment now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.bill_manager.process_payment(bill_id)

            if success:
                QMessageBox.information(self, "Success", f"Payment processed successfully.\nReference: {message}")
                self.refresh_bills_table()
            else:
                QMessageBox.warning(self, "Error", f"Failed to process payment: {message}")

    @pyqtSlot()
    def cancel_payment(self):
        button = self.sender()
        bill_id = button.property("bill_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Cancellation",
            "Are you sure you want to cancel this scheduled payment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.bill_manager.cancel_scheduled_payment(bill_id)

            if success:
                QMessageBox.information(self, "Success", "Payment cancelled successfully.")
                self.refresh_bills_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to cancel payment.")

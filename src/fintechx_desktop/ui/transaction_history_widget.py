import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit, QHeaderView, QTextEdit,
    QFileDialog, QMessageBox, QTabWidget, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot, QDate
from PyQt6.QtGui import QColor

from ..app.transaction_history import (
    TransactionManager, Transaction, TransactionType, TransactionStatus
)


class TransactionHistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("fintechx_desktop.ui.transaction_history")
        self.transaction_manager = TransactionManager()

        main_layout = QVBoxLayout(self)

        # Create tabs for different views
        self.tab_widget = QTabWidget()

        # Create the transactions list tab
        self.transactions_list_widget = QWidget()
        self.setup_transactions_list_tab()
        self.tab_widget.addTab(self.transactions_list_widget, "Transactions")

        # Create the reporting tab
        self.reporting_widget = QWidget()
        self.setup_reporting_tab()
        self.tab_widget.addTab(self.reporting_widget, "Reports")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Initialize with some sample data
        self.load_sample_data()

    def load_sample_data(self):
        # Add sample transactions for demonstration
        transactions = [
            Transaction(
                amount=125.50,
                card_number="4111111111111111",
                merchant="Online Store Inc.",
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.APPROVED,
                description="Purchase of electronics"
            ),
            Transaction(
                amount=75.25,
                card_number="5555555555554444",
                merchant="Grocery Market",
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.SETTLED,
                description="Weekly groceries"
            ),
            Transaction(
                amount=25.00,
                card_number="4111111111111111",
                merchant="Online Store Inc.",
                transaction_type=TransactionType.REFUND,
                status=TransactionStatus.REFUNDED,
                description="Partial refund for returned item"
            ),
            Transaction(
                amount=200.00,
                card_number="378282246310005",
                merchant="Travel Agency",
                transaction_type=TransactionType.AUTHORIZATION,
                status=TransactionStatus.PENDING,
                description="Hotel reservation"
            ),
            Transaction(
                amount=50.00,
                card_number="6011111111111117",
                merchant="Gas Station",
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.APPROVED,
                description="Fuel purchase"
            ),
            Transaction(
                amount=350.75,
                card_number="5555555555554444",
                merchant="Department Store",
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.DISPUTED,
                description="Clothing purchase"
            ),
            Transaction(
                amount=1200.00,
                card_number="378282246310005",
                merchant="Electronics Store",
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.SETTLED,
                description="New laptop"
            ),
            Transaction(
                amount=15.99,
                card_number="4111111111111111",
                merchant="Streaming Service",
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.SETTLED,
                description="Monthly subscription"
            ),
            Transaction(
                amount=350.75,
                card_number="5555555555554444",
                merchant="Department Store",
                transaction_type=TransactionType.CHARGEBACK,
                status=TransactionStatus.DISPUTED,
                description="Customer dispute"
            ),
            Transaction(
                amount=45.50,
                card_number="6011111111111117",
                merchant="Restaurant",
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.SETTLED,
                description="Dinner"
            )
        ]

        # Adjust timestamps to spread over the last 30 days
        now = datetime.now()
        for i, transaction in enumerate(transactions):
            days_ago = i % 30
            transaction.timestamp = now - timedelta(days=days_ago)
            transaction.updated_at = transaction.timestamp
            self.transaction_manager.add_transaction(transaction)

        self.refresh_transactions_table()
        self.refresh_report_data()

    def setup_transactions_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_group = QGroupBox("Filter Transactions")
        filter_layout = QHBoxLayout()

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        for status in TransactionStatus:
            self.status_filter.addItem(status.value)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        for t_type in TransactionType:
            self.type_filter.addItem(t_type.value)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        self.merchant_filter = QComboBox()
        self.merchant_filter.setEditable(True)
        self.merchant_filter.addItem("All Merchants")

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.refresh_transactions_table)

        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QLabel("Merchant:"))
        filter_layout.addWidget(self.merchant_filter)
        filter_layout.addWidget(self.apply_filter_button)
        filter_group.setLayout(filter_layout)

        # Transactions table
        self.transactions_table = QTableWidget(0, 8)
        self.transactions_table.setHorizontalHeaderLabels([
            "Reference", "Date", "Card", "Merchant", "Amount", "Type", "Status", "Description"
        ])
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.transactions_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_transactions_table)

        self.export_button = QPushButton("Export Transactions")
        self.export_button.clicked.connect(self.export_transactions)

        self.import_button = QPushButton("Import Transactions")
        self.import_button.clicked.connect(self.import_transactions)

        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.export_button)
        action_layout.addWidget(self.import_button)

        layout.addWidget(filter_group)
        layout.addWidget(self.transactions_table)
        layout.addLayout(action_layout)

        self.transactions_list_widget.setLayout(layout)

    def setup_reporting_tab(self):
        layout = QVBoxLayout()

        # Report controls
        report_group = QGroupBox("Generate Report")
        report_layout = QHBoxLayout()

        self.report_date_from = QDateEdit()
        self.report_date_from.setCalendarPopup(True)
        self.report_date_from.setDate(QDate.currentDate().addDays(-30))

        self.report_date_to = QDateEdit()
        self.report_date_to.setCalendarPopup(True)
        self.report_date_to.setDate(QDate.currentDate())

        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self.generate_report)

        report_layout.addWidget(QLabel("From:"))
        report_layout.addWidget(self.report_date_from)
        report_layout.addWidget(QLabel("To:"))
        report_layout.addWidget(self.report_date_to)
        report_layout.addWidget(self.generate_report_button)
        report_group.setLayout(report_layout)

        # Report display area
        report_display = QSplitter(Qt.Orientation.Horizontal)

        # Summary section
        summary_frame = QFrame()
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.addWidget(QLabel("<b>Transaction Summary</b>"))

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)

        # Status distribution section
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        status_layout.addWidget(QLabel("<b>Status Distribution</b>"))

        self.status_table = QTableWidget(0, 2)
        self.status_table.setHorizontalHeaderLabels(["Status", "Count"])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        status_layout.addWidget(self.status_table)

        # Type distribution section
        type_frame = QFrame()
        type_layout = QVBoxLayout(type_frame)
        type_layout.addWidget(QLabel("<b>Transaction Type Distribution</b>"))

        self.type_table = QTableWidget(0, 2)
        self.type_table.setHorizontalHeaderLabels(["Type", "Count"])
        self.type_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        type_layout.addWidget(self.type_table)

        # Top merchants section
        merchant_frame = QFrame()
        merchant_layout = QVBoxLayout(merchant_frame)
        merchant_layout.addWidget(QLabel("<b>Top Merchants by Volume</b>"))

        self.merchant_table = QTableWidget(0, 2)
        self.merchant_table.setHorizontalHeaderLabels(["Merchant", "Volume"])
        self.merchant_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        merchant_layout.addWidget(self.merchant_table)

        # Add all sections to the splitter
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(summary_frame)
        left_splitter.addWidget(status_frame)

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(type_frame)
        right_splitter.addWidget(merchant_frame)

        report_display.addWidget(left_splitter)
        report_display.addWidget(right_splitter)

        layout.addWidget(report_group)
        layout.addWidget(report_display)

        self.reporting_widget.setLayout(layout)

    @pyqtSlot()
    def refresh_transactions_table(self):
        self.transactions_table.setRowCount(0)

        status_filter = self.status_filter.currentText()
        type_filter = self.type_filter.currentText()
        merchant_filter = self.merchant_filter.currentText()

        from_date = self.date_from.date().toPyDate()
        from_datetime = datetime.combine(from_date, datetime.min.time())

        to_date = self.date_to.date().toPyDate()
        to_datetime = datetime.combine(to_date, datetime.max.time())

        transactions = self.transaction_manager.get_transactions_by_date_range(from_datetime, to_datetime)

        if status_filter != "All Statuses":
            transactions = [t for t in transactions if t.status.value == status_filter]

        if type_filter != "All Types":
            transactions = [t for t in transactions if t.transaction_type.value == type_filter]

        if merchant_filter != "All Merchants":
            transactions = [t for t in transactions if merchant_filter.lower() in t.merchant.lower()]

        self.transactions_table.setRowCount(len(transactions))

        for row, transaction in enumerate(transactions):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(transaction.reference_id))

            date_item = QTableWidgetItem(transaction.timestamp.strftime("%Y-%m-%d %H:%M"))
            self.transactions_table.setItem(row, 1, date_item)

            self.transactions_table.setItem(row, 2, QTableWidgetItem(transaction.masked_card))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(transaction.merchant))

            amount_item = QTableWidgetItem(f"${transaction.amount:.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            if transaction.transaction_type in [TransactionType.REFUND, TransactionType.CHARGEBACK]:
                amount_item.setForeground(QColor(255, 0, 0))  # Red for refunds/chargebacks
            self.transactions_table.setItem(row, 4, amount_item)

            type_item = QTableWidgetItem(transaction.transaction_type.value)
            self.transactions_table.setItem(row, 5, type_item)

            status_item = QTableWidgetItem(transaction.status.value)
            if transaction.status == TransactionStatus.APPROVED or transaction.status == TransactionStatus.SETTLED:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif transaction.status == TransactionStatus.DECLINED or transaction.status == TransactionStatus.FAILED:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif transaction.status == TransactionStatus.DISPUTED:
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            self.transactions_table.setItem(row, 6, status_item)

            self.transactions_table.setItem(row, 7, QTableWidgetItem(transaction.description))

        # Update merchant filter dropdown with unique merchants
        current_merchant = self.merchant_filter.currentText()
        self.merchant_filter.clear()
        self.merchant_filter.addItem("All Merchants")

        merchants = set()
        for transaction in self.transaction_manager.get_all_transactions():
            merchants.add(transaction.merchant)

        for merchant in sorted(merchants):
            self.merchant_filter.addItem(merchant)

        index = self.merchant_filter.findText(current_merchant)
        if index >= 0:
            self.merchant_filter.setCurrentIndex(index)

    @pyqtSlot()
    def export_transactions(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Transactions", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        if not file_path.endswith('.json'):
            file_path += '.json'

        success = self.transaction_manager.export_to_json(file_path)

        if success:
            QMessageBox.information(
                self, "Export Successful",
                f"Successfully exported {len(self.transaction_manager.get_all_transactions())} transactions."
            )
        else:
            QMessageBox.warning(
                self, "Export Failed",
                "Failed to export transactions. Please check the logs for details."
            )

    @pyqtSlot()
    def import_transactions(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Transactions", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        success = self.transaction_manager.import_from_json(file_path)

        if success:
            self.refresh_transactions_table()
            self.refresh_report_data()
            QMessageBox.information(
                self, "Import Successful",
                "Successfully imported transactions."
            )
        else:
            QMessageBox.warning(
                self, "Import Failed",
                "Failed to import transactions. Please check the logs for details."
            )

    @pyqtSlot()
    def generate_report(self):
        from_date = self.report_date_from.date().toPyDate()
        from_datetime = datetime.combine(from_date, datetime.min.time())

        to_date = self.report_date_to.date().toPyDate()
        to_datetime = datetime.combine(to_date, datetime.max.time())

        report = self.transaction_manager.generate_transaction_report(from_datetime, to_datetime)

        # Update summary text
        summary = f"<h3>Transaction Report</h3>"
        summary += f"<p><b>Period:</b> {report['period']}</p>"
        summary += f"<p><b>Total Transactions:</b> {report['total_count']}</p>"
        summary += f"<p><b>Total Volume:</b> ${report['total_volume']:.2f}</p>"

        if 'message' in report:
            summary += f"<p>{report['message']}</p>"

        self.summary_text.setHtml(summary)

        # Update status distribution table
        self.status_table.setRowCount(0)
        if 'status_distribution' in report:
            status_data = report['status_distribution']
            self.status_table.setRowCount(len(status_data))

            for row, (status, count) in enumerate(status_data.items()):
                self.status_table.setItem(row, 0, QTableWidgetItem(status))
                self.status_table.setItem(row, 1, QTableWidgetItem(str(count)))

        # Update type distribution table
        self.type_table.setRowCount(0)
        if 'type_distribution' in report:
            type_data = report['type_distribution']
            self.type_table.setRowCount(len(type_data))

            for row, (type_name, count) in enumerate(type_data.items()):
                self.type_table.setItem(row, 0, QTableWidgetItem(type_name))
                self.type_table.setItem(row, 1, QTableWidgetItem(str(count)))

        # Update merchant table
        self.merchant_table.setRowCount(0)
        if 'top_merchants' in report:
            merchant_data = report['top_merchants']
            self.merchant_table.setRowCount(len(merchant_data))

            for row, (merchant, volume) in enumerate(merchant_data.items()):
                self.merchant_table.setItem(row, 0, QTableWidgetItem(merchant))

                volume_item = QTableWidgetItem(f"${volume:.2f}")
                volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if volume < 0:
                    volume_item.setForeground(QColor(255, 0, 0))  # Red for negative values
                self.merchant_table.setItem(row, 1, volume_item)

    def refresh_report_data(self):
        self.generate_report()

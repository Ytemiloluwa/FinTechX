import logging
from datetime import datetime
from typing import Dict, List, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QHeaderView, QTextEdit,
    QMessageBox, QTabWidget, QDialog, QDialogButtonBox, QFileDialog, QProgressBar,
    QSpinBox
)
from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtGui import QColor

from ..app.batch_processing import (
    BatchManager, BatchJob, BatchStatus, BatchType
)


class BatchItemsDialog(QDialog):
    def __init__(self, batch_type: BatchType, parent=None):
        super().__init__(parent)
        self.batch_type = batch_type
        self.setWindowTitle(f"Add {batch_type.value} Batch Items")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.items_data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create form based on batch type
        form_group = QGroupBox("Item Template")
        form_layout = QFormLayout()

        self.form_fields = {}

        if self.batch_type == BatchType.PAYMENT:
            fields = [
                ("amount", "Amount", "text"),
                ("card_number", "Card Number", "text"),
                ("expiry", "Expiry (MM/YY)", "text"),
                ("cvv", "CVV", "text"),
                ("description", "Description", "text")
            ]
        elif self.batch_type == BatchType.REFUND:
            fields = [
                ("transaction_id", "Transaction ID", "text"),
                ("amount", "Amount", "text"),
                ("reason", "Reason", "text")
            ]
        elif self.batch_type == BatchType.TRANSFER:
            fields = [
                ("source_account", "Source Account", "text"),
                ("destination_account", "Destination Account", "text"),
                ("amount", "Amount", "text"),
                ("description", "Description", "text")
            ]
        elif self.batch_type == BatchType.CARD_ISSUANCE:
            fields = [
                ("customer_id", "Customer ID", "text"),
                ("card_type", "Card Type", "combo", ["Debit", "Credit", "Prepaid"]),
                ("card_level", "Card Level", "combo", ["Standard", "Gold", "Platinum", "Black"])
            ]
        elif self.batch_type == BatchType.CUSTOMER_IMPORT:
            fields = [
                ("first_name", "First Name", "text"),
                ("last_name", "Last Name", "text"),
                ("email", "Email", "text"),
                ("phone", "Phone", "text"),
                ("address", "Address", "text")
            ]
        elif self.batch_type == BatchType.MERCHANT_IMPORT:
            fields = [
                ("name", "Merchant Name", "text"),
                ("category", "Category", "text"),
                ("contact_email", "Contact Email", "text"),
                ("contact_phone", "Contact Phone", "text"),
                ("address", "Address", "text")
            ]
        else:
            fields = []

        for field_id, field_label, field_type, *args in fields:
            if field_type == "text":
                field_widget = QLineEdit()
            elif field_type == "combo":
                field_widget = QComboBox()
                field_widget.addItems(args[0])
            else:
                field_widget = QLineEdit()

            form_layout.addRow(field_label, field_widget)
            self.form_fields[field_id] = field_widget

        form_group.setLayout(form_layout)

        # Add item button
        add_item_button = QPushButton("Add Item")
        add_item_button.clicked.connect(self.add_item)

        # Items table
        self.items_table = QTableWidget(0, len(fields) + 1)  # +1 for actions
        headers = [field[1] for field in fields] + ["Actions"]
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Import/Export buttons
        import_export_layout = QHBoxLayout()

        import_csv_button = QPushButton("Import from CSV")
        import_csv_button.clicked.connect(self.import_from_csv)

        export_csv_button = QPushButton("Export to CSV")
        export_csv_button.clicked.connect(self.export_to_csv)

        import_export_layout.addWidget(import_csv_button)
        import_export_layout.addWidget(export_csv_button)

        # Batch size controls
        batch_size_layout = QHBoxLayout()

        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(1, 1000)
        self.batch_size_spinbox.setValue(10)

        generate_dummy_button = QPushButton("Generate Dummy Items")
        generate_dummy_button.clicked.connect(self.generate_dummy_items)

        batch_size_layout.addWidget(QLabel("Batch Size:"))
        batch_size_layout.addWidget(self.batch_size_spinbox)
        batch_size_layout.addWidget(generate_dummy_button)
        batch_size_layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Add all components to main layout
        layout.addWidget(form_group)
        layout.addWidget(add_item_button)
        layout.addLayout(batch_size_layout)
        layout.addWidget(self.items_table)
        layout.addLayout(import_export_layout)
        layout.addWidget(button_box)

    @pyqtSlot()
    def add_item(self):
        item_data = {}

        for field_id, field_widget in self.form_fields.items():
            if isinstance(field_widget, QLineEdit):
                value = field_widget.text().strip()
            elif isinstance(field_widget, QComboBox):
                value = field_widget.currentText()
            else:
                value = ""

            item_data[field_id] = value

        # Validate required fields
        if not self.validate_item(item_data):
            return

        self.items_data.append(item_data)
        self.update_items_table()

        # Clear form fields
        for field_widget in self.form_fields.values():
            if isinstance(field_widget, QLineEdit):
                field_widget.clear()

    def validate_item(self, item_data: Dict[str, Any]) -> bool:
        # Basic validation based on batch type
        if self.batch_type == BatchType.PAYMENT:
            if not item_data.get("amount") or not item_data.get("card_number"):
                QMessageBox.warning(self, "Validation Error", "Amount and Card Number are required.")
                return False

            try:
                amount = float(item_data.get("amount", "0"))
                if amount <= 0:
                    QMessageBox.warning(self, "Validation Error", "Amount must be greater than zero.")
                    return False
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Amount must be a valid number.")
                return False

        elif self.batch_type == BatchType.REFUND:
            if not item_data.get("transaction_id") or not item_data.get("amount"):
                QMessageBox.warning(self, "Validation Error", "Transaction ID and Amount are required.")
                return False

        elif self.batch_type == BatchType.TRANSFER:
            if not item_data.get("source_account") or not item_data.get("destination_account") or not item_data.get(
                    "amount"):
                QMessageBox.warning(self, "Validation Error",
                                    "Source Account, Destination Account, and Amount are required.")
                return False

        elif self.batch_type == BatchType.CARD_ISSUANCE:
            if not item_data.get("customer_id"):
                QMessageBox.warning(self, "Validation Error", "Customer ID is required.")
                return False

        elif self.batch_type == BatchType.CUSTOMER_IMPORT:
            if not item_data.get("first_name") or not item_data.get("last_name") or not item_data.get("email"):
                QMessageBox.warning(self, "Validation Error", "First Name, Last Name, and Email are required.")
                return False

        elif self.batch_type == BatchType.MERCHANT_IMPORT:
            if not item_data.get("name") or not item_data.get("category") or not item_data.get("contact_email"):
                QMessageBox.warning(self, "Validation Error", "Name, Category, and Contact Email are required.")
                return False

        return True

    def update_items_table(self):
        self.items_table.setRowCount(len(self.items_data))

        for row, item_data in enumerate(self.items_data):
            for col, (field_id, _) in enumerate(self.form_fields.items()):
                self.items_table.setItem(row, col, QTableWidgetItem(str(item_data.get(field_id, ""))))

            # Add delete button
            delete_button = QPushButton("Delete")
            delete_button.setProperty("row", row)
            delete_button.clicked.connect(self.delete_item)

            self.items_table.setCellWidget(row, len(self.form_fields), delete_button)

    @pyqtSlot()
    def delete_item(self):
        button = self.sender()
        row = button.property("row")

        if 0 <= row < len(self.items_data):
            del self.items_data[row]
            self.update_items_table()

    @pyqtSlot()
    def import_from_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Items from CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            import csv

            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    item_data = {}

                    for field_id in self.form_fields.keys():
                        if field_id in row:
                            item_data[field_id] = row[field_id]

                    if self.validate_item(item_data):
                        self.items_data.append(item_data)

            self.update_items_table()
            QMessageBox.information(self, "Import Successful", f"Imported {len(self.items_data)} items.")

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import CSV: {str(e)}")

    @pyqtSlot()
    def export_to_csv(self):
        if not self.items_data:
            QMessageBox.warning(self, "Export Error", "No items to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Items to CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            import csv

            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = list(self.form_fields.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for item_data in self.items_data:
                    writer.writerow(item_data)

            QMessageBox.information(self, "Export Successful", f"Exported {len(self.items_data)} items to {file_path}.")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {str(e)}")

    @pyqtSlot()
    def generate_dummy_items(self):
        batch_size = self.batch_size_spinbox.value()

        import random
        import string

        def random_string(length=10):
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        def random_digits(length=10):
            return ''.join(random.choices(string.digits, k=length))

        def random_amount():
            return str(round(random.uniform(10, 1000), 2))

        def random_card():
            prefixes = ['4', '51', '37', '6011']
            prefix = random.choice(prefixes)
            return prefix + random_digits(16 - len(prefix))

        def random_expiry():
            month = random.randint(1, 12)
            year = random.randint(23, 30)
            return f"{month:02d}/{year:02d}"

        def random_email():
            domains = ['example.com', 'test.com', 'domain.com', 'mail.com']
            return f"{random_string(8)}@{random.choice(domains)}"

        def random_phone():
            return f"+1{random_digits(10)}"

        def random_address():
            streets = ['Main St', 'Oak Ave', 'Maple Rd', 'Broadway', 'Park Ave']
            cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
            states = ['NY', 'CA', 'IL', 'TX', 'AZ']
            return f"{random.randint(100, 9999)} {random.choice(streets)}, {random.choice(cities)}, {random.choice(states)} {random_digits(5)}"

        def random_category():
            categories = ['Retail', 'Food', 'Technology', 'Healthcare', 'Finance', 'Education', 'Entertainment']
            return random.choice(categories)

        # Generate dummy items based on batch type
        for _ in range(batch_size):
            item_data = {}

            if self.batch_type == BatchType.PAYMENT:
                item_data = {
                    "amount": random_amount(),
                    "card_number": random_card(),
                    "expiry": random_expiry(),
                    "cvv": random_digits(3),
                    "description": f"Payment for {random_string(10)}"
                }
            elif self.batch_type == BatchType.REFUND:
                item_data = {
                    "transaction_id": random_string(20),
                    "amount": random_amount(),
                    "reason": f"Refund for {random_string(10)}"
                }
            elif self.batch_type == BatchType.TRANSFER:
                item_data = {
                    "source_account": random_digits(10),
                    "destination_account": random_digits(10),
                    "amount": random_amount(),
                    "description": f"Transfer for {random_string(10)}"
                }
            elif self.batch_type == BatchType.CARD_ISSUANCE:
                item_data = {
                    "customer_id": random_string(10),
                    "card_type": random.choice(["Debit", "Credit", "Prepaid"]),
                    "card_level": random.choice(["Standard", "Gold", "Platinum", "Black"])
                }
            elif self.batch_type == BatchType.CUSTOMER_IMPORT:
                item_data = {
                    "first_name": random_string(8),
                    "last_name": random_string(10),
                    "email": random_email(),
                    "phone": random_phone(),
                    "address": random_address()
                }
            elif self.batch_type == BatchType.MERCHANT_IMPORT:
                item_data = {
                    "name": f"{random_string(8)} {random.choice(['Inc', 'LLC', 'Corp'])}",
                    "category": random_category(),
                    "contact_email": random_email(),
                    "contact_phone": random_phone(),
                    "address": random_address()
                }

            self.items_data.append(item_data)

        self.update_items_table()
        QMessageBox.information(self, "Generation Complete", f"Generated {batch_size} dummy items.")

    def get_items_data(self) -> List[Dict[str, Any]]:
        return self.items_data


class BatchDetailsDialog(QDialog):
    def __init__(self, batch_manager: BatchManager, batch_job: BatchJob, parent=None):
        super().__init__(parent)
        self.batch_manager = batch_manager
        self.batch_job = batch_job
        self.setWindowTitle(f"Batch Details: {batch_job.name}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setup_ui()

        # Set up timer for auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)

        if batch_job.status == BatchStatus.PROCESSING:
            self.refresh_timer.start(1000)  # Refresh every second while processing

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Batch info
        info_group = QGroupBox("Batch Information")
        info_layout = QFormLayout()

        info_layout.addRow("ID:", QLabel(self.batch_job.id))
        info_layout.addRow("Name:", QLabel(self.batch_job.name))
        info_layout.addRow("Type:", QLabel(self.batch_job.batch_type.value))
        info_layout.addRow("Description:", QLabel(self.batch_job.description))
        info_layout.addRow("Created:", QLabel(self.batch_job.created_at.strftime("%Y-%m-%d %H:%M:%S")))

        if self.batch_job.started_at:
            info_layout.addRow("Started:", QLabel(self.batch_job.started_at.strftime("%Y-%m-%d %H:%M:%S")))

        if self.batch_job.completed_at:
            info_layout.addRow("Completed:", QLabel(self.batch_job.completed_at.strftime("%Y-%m-%d %H:%M:%S")))

        status_label = QLabel(self.batch_job.status.value)
        if self.batch_job.status == BatchStatus.COMPLETED:
            status_label.setStyleSheet("color: green; font-weight: bold;")
        elif self.batch_job.status == BatchStatus.FAILED:
            status_label.setStyleSheet("color: red; font-weight: bold;")
        elif self.batch_job.status == BatchStatus.PARTIALLY_COMPLETED:
            status_label.setStyleSheet("color: orange; font-weight: bold;")
        elif self.batch_job.status == BatchStatus.PROCESSING:
            status_label.setStyleSheet("color: blue; font-weight: bold;")

        info_layout.addRow("Status:", status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(self.batch_job.get_progress()))
        info_layout.addRow("Progress:", self.progress_bar)

        # Stats
        stats_layout = QHBoxLayout()

        self.total_label = QLabel(f"Total: {self.batch_job.total_items}")
        self.processed_label = QLabel(f"Processed: {self.batch_job.processed_items}")
        self.success_label = QLabel(f"Success: {self.batch_job.successful_items}")
        self.failed_label = QLabel(f"Failed: {self.batch_job.failed_items}")

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.processed_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.failed_label)

        info_group.setLayout(info_layout)

        # Items table
        self.items_table = QTableWidget(0, 4)
        self.items_table.setHorizontalHeaderLabels(["ID", "Status", "Error", "Data"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.update_items_table()

        # Action buttons
        action_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)

        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.export_button)
        action_layout.addStretch()
        action_layout.addWidget(self.close_button)

        # Add all components to main layout
        layout.addWidget(info_group)
        layout.addLayout(stats_layout)
        layout.addWidget(self.items_table)
        layout.addLayout(action_layout)

    def update_items_table(self):
        self.items_table.setRowCount(len(self.batch_job.items))

        for row, item in enumerate(self.batch_job.items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item.id))

            status_item = QTableWidgetItem(item.status)
            if item.status == "Completed":
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif item.status == "Failed":
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif item.status == "Processing":
                status_item.setBackground(QColor(200, 200, 255))  # Light blue

            self.items_table.setItem(row, 1, status_item)
            self.items_table.setItem(row, 2, QTableWidgetItem(item.error_message or ""))

            # Format data as string
            data_str = ", ".join([f"{k}: {v}" for k, v in item.data.items()])
            self.items_table.setItem(row, 3, QTableWidgetItem(data_str))

    @pyqtSlot()
    def refresh_data(self):
        # Get fresh batch job data
        updated_job = self.batch_manager.get_batch_job(self.batch_job.id)
        if not updated_job:
            return

        self.batch_job = updated_job

        # Update progress and stats
        self.progress_bar.setValue(int(self.batch_job.get_progress()))
        self.total_label.setText(f"Total: {self.batch_job.total_items}")
        self.processed_label.setText(f"Processed: {self.batch_job.processed_items}")
        self.success_label.setText(f"Success: {self.batch_job.successful_items}")
        self.failed_label.setText(f"Failed: {self.batch_job.failed_items}")

        # Update items table
        self.update_items_table()

        # Stop timer if processing is complete
        if self.batch_job.status != BatchStatus.PROCESSING:
            self.refresh_timer.stop()

    @pyqtSlot()
    def export_results(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Batch Results",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )

        if not file_path:
            return

        format_type = "csv" if selected_filter == "CSV Files (*.csv)" else "json"

        success = self.batch_manager.export_batch_job_results(
            self.batch_job.id,
            file_path,
            format_type
        )

        if success:
            QMessageBox.information(self, "Export Successful", f"Batch results exported to {file_path}")
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export batch results")


class BatchProcessingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_manager = BatchManager()
        self.logger = logging.getLogger("fintechx_desktop.ui.batch_processing")

        main_layout = QVBoxLayout(self)

        # Create tabs for different views
        self.tab_widget = QTabWidget()

        # Create the batch jobs list tab
        self.jobs_list_widget = QWidget()
        self.setup_jobs_list_tab()
        self.tab_widget.addTab(self.jobs_list_widget, "Batch Jobs")

        # Create the new batch tab
        self.new_batch_widget = QWidget()
        self.setup_new_batch_tab()
        self.tab_widget.addTab(self.new_batch_widget, "Create Batch")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Set up timer for auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_jobs_table)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def setup_jobs_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_group = QGroupBox("Filter Batch Jobs")
        filter_layout = QHBoxLayout()

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        for batch_type in BatchType:
            self.type_filter.addItem(batch_type.value)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses")
        for status in BatchStatus:
            self.status_filter.addItem(status.value)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search batch jobs...")

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.refresh_jobs_table)

        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.apply_filter_button)
        filter_group.setLayout(filter_layout)

        # Jobs table
        self.jobs_table = QTableWidget(0, 7)
        self.jobs_table.setHorizontalHeaderLabels([
            "Name", "Type", "Status", "Progress", "Items", "Created", "Actions"
        ])
        self.jobs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_jobs_table)

        action_layout.addWidget(self.refresh_button)
        action_layout.addStretch()

        layout.addWidget(filter_group)
        layout.addWidget(self.jobs_table)
        layout.addLayout(action_layout)

        self.jobs_list_widget.setLayout(layout)

        # Initial data load
        self.refresh_jobs_table()

    def setup_new_batch_tab(self):
        layout = QVBoxLayout()

        # Batch details form
        form_group = QGroupBox("Batch Details")
        form_layout = QFormLayout()

        self.batch_name_input = QLineEdit()
        form_layout.addRow("Name:", self.batch_name_input)

        self.batch_type_combo = QComboBox()
        for batch_type in BatchType:
            self.batch_type_combo.addItem(batch_type.value)
        form_layout.addRow("Type:", self.batch_type_combo)

        self.batch_description_input = QTextEdit()
        self.batch_description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.batch_description_input)

        form_group.setLayout(form_layout)

        # Add items button
        self.add_items_button = QPushButton("Add Batch Items")
        self.add_items_button.clicked.connect(self.show_add_items_dialog)

        # Items summary
        self.items_summary_label = QLabel("No items added yet.")

        # Create batch button
        self.create_batch_button = QPushButton("Create Batch")
        self.create_batch_button.clicked.connect(self.create_batch)
        self.create_batch_button.setEnabled(False)

        # Import batch button
        self.import_batch_button = QPushButton("Import Batch from CSV")
        self.import_batch_button.clicked.connect(self.import_batch)

        # Add all components to main layout
        layout.addWidget(form_group)
        layout.addWidget(self.add_items_button)
        layout.addWidget(self.items_summary_label)
        layout.addWidget(self.create_batch_button)
        layout.addWidget(self.import_batch_button)
        layout.addStretch()

        self.new_batch_widget.setLayout(layout)

        # Store batch items
        self.batch_items = []

    @pyqtSlot(int)
    def on_tab_changed(self, index):
        if index == 0:  # Jobs list tab
            self.refresh_jobs_table()

    @pyqtSlot()
    def refresh_jobs_table(self):
        self.jobs_table.setRowCount(0)

        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()
        search_text = self.search_input.text().strip().lower()

        batch_jobs = self.batch_manager.get_all_batch_jobs()

        # Apply type filter
        if type_filter != "All Types":
            batch_type = None
            for bt in BatchType:
                if bt.value == type_filter:
                    batch_type = bt
                    break
            if batch_type:
                batch_jobs = [job for job in batch_jobs if job.batch_type == batch_type]

        # Apply status filter
        if status_filter != "All Statuses":
            status = None
            for s in BatchStatus:
                if s.value == status_filter:
                    status = s
                    break
            if status:
                batch_jobs = [job for job in batch_jobs if job.status == status]

        # Apply search filter
        if search_text:
            batch_jobs = [job for job in batch_jobs if
                          search_text in job.name.lower() or search_text in job.description.lower()]

        self.jobs_table.setRowCount(len(batch_jobs))

        for row, job in enumerate(batch_jobs):
            self.jobs_table.setItem(row, 0, QTableWidgetItem(job.name))
            self.jobs_table.setItem(row, 1, QTableWidgetItem(job.batch_type.value))

            status_item = QTableWidgetItem(job.status.value)
            if job.status == BatchStatus.COMPLETED:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif job.status == BatchStatus.FAILED:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif job.status == BatchStatus.PARTIALLY_COMPLETED:
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
            elif job.status == BatchStatus.PROCESSING:
                status_item.setBackground(QColor(200, 200, 255))  # Light blue

            self.jobs_table.setItem(row, 2, status_item)

            # Progress bar in cell
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(job.get_progress()))
            self.jobs_table.setCellWidget(row, 3, progress_bar)

            items_text = f"{job.processed_items}/{job.total_items} ({job.successful_items} success, {job.failed_items} failed)"
            self.jobs_table.setItem(row, 4, QTableWidgetItem(items_text))

            created_at = job.created_at.strftime("%Y-%m-%d %H:%M:%S")
            self.jobs_table.setItem(row, 5, QTableWidgetItem(created_at))

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            view_button = QPushButton("View")
            view_button.setProperty("job_id", job.id)
            view_button.clicked.connect(self.view_batch_job)

            actions_layout.addWidget(view_button)

            if job.status == BatchStatus.PENDING:
                start_button = QPushButton("Start")
                start_button.setProperty("job_id", job.id)
                start_button.clicked.connect(self.start_batch_job)
                actions_layout.addWidget(start_button)

            delete_button = QPushButton("Delete")
            delete_button.setProperty("job_id", job.id)
            delete_button.clicked.connect(self.delete_batch_job)

            if job.status == BatchStatus.PROCESSING:
                delete_button.setEnabled(False)

            actions_layout.addWidget(delete_button)

            self.jobs_table.setCellWidget(row, 6, actions_widget)

    @pyqtSlot()
    def show_add_items_dialog(self):
        batch_type_text = self.batch_type_combo.currentText()
        batch_type = None

        for bt in BatchType:
            if bt.value == batch_type_text:
                batch_type = bt
                break

        if not batch_type:
            QMessageBox.warning(self, "Error", "Invalid batch type selected.")
            return

        dialog = BatchItemsDialog(batch_type, self)

        if dialog.exec():
            self.batch_items = dialog.get_items_data()
            self.items_summary_label.setText(f"{len(self.batch_items)} items added.")
            self.create_batch_button.setEnabled(len(self.batch_items) > 0)

    @pyqtSlot()
    def create_batch(self):
        name = self.batch_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Batch name is required.")
            return

        batch_type_text = self.batch_type_combo.currentText()
        batch_type = None

        for bt in BatchType:
            if bt.value == batch_type_text:
                batch_type = bt
                break

        if not batch_type:
            QMessageBox.warning(self, "Error", "Invalid batch type selected.")
            return

        description = self.batch_description_input.toPlainText().strip()

        if not self.batch_items:
            QMessageBox.warning(self, "Error", "No batch items added.")
            return

        job_id = self.batch_manager.create_batch_job(
            name=name,
            batch_type=batch_type,
            items=self.batch_items,
            description=description
        )

        if job_id:
            QMessageBox.information(self, "Success", f"Batch job created with ID: {job_id}")

            # Clear form
            self.batch_name_input.clear()
            self.batch_description_input.clear()
            self.batch_items = []
            self.items_summary_label.setText("No items added yet.")
            self.create_batch_button.setEnabled(False)

            # Switch to jobs list tab
            self.tab_widget.setCurrentIndex(0)
            self.refresh_jobs_table()
        else:
            QMessageBox.critical(self, "Error", "Failed to create batch job.")

    @pyqtSlot()
    def import_batch(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Batch from CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        batch_type_text = self.batch_type_combo.currentText()
        batch_type = None

        for bt in BatchType:
            if bt.value == batch_type_text:
                batch_type = bt
                break

        if not batch_type:
            QMessageBox.warning(self, "Error", "Invalid batch type selected.")
            return

        name = self.batch_name_input.text().strip()
        if not name:
            name = f"Imported {batch_type.value} Batch - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        description = self.batch_description_input.toPlainText().strip()

        job_id = self.batch_manager.import_batch_from_csv(
            file_path=file_path,
            batch_type=batch_type,
            name=name,
            description=description
        )

        if job_id:
            QMessageBox.information(self, "Success", f"Batch job imported with ID: {job_id}")

            # Clear form
            self.batch_name_input.clear()
            self.batch_description_input.clear()
            self.batch_items = []
            self.items_summary_label.setText("No items added yet.")
            self.create_batch_button.setEnabled(False)

            # Switch to jobs list tab
            self.tab_widget.setCurrentIndex(0)
            self.refresh_jobs_table()
        else:
            QMessageBox.critical(self, "Error", "Failed to import batch job.")

    @pyqtSlot()
    def view_batch_job(self):
        button = self.sender()
        job_id = button.property("job_id")

        batch_job = self.batch_manager.get_batch_job(job_id)
        if not batch_job:
            QMessageBox.warning(self, "Error", "Batch job not found.")
            return

        dialog = BatchDetailsDialog(self.batch_manager, batch_job, self)
        dialog.exec()

        # Refresh table after viewing details
        self.refresh_jobs_table()

    @pyqtSlot()
    def start_batch_job(self):
        button = self.sender()
        job_id = button.property("job_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Start",
            "Are you sure you want to start this batch job?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.batch_manager.start_batch_job(job_id)

            if success:
                QMessageBox.information(self, "Success", "Batch job started successfully.")
                self.refresh_jobs_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to start batch job.")

    @pyqtSlot()
    def delete_batch_job(self):
        button = self.sender()
        job_id = button.property("job_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this batch job?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.batch_manager.delete_batch_job(job_id)

            if success:
                QMessageBox.information(self, "Success", "Batch job deleted successfully.")
                self.refresh_jobs_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete batch job.")

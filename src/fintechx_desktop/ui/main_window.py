import logging
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton,
    QStackedWidget, QLineEdit, QFormLayout, QSpinBox, QTextEdit,
    QGroupBox, QComboBox, QMessageBox
)
from PyQt6.QtCore import pyqtSlot

# Import UI widgets
from .virtual_terminal_widget import VirtualTerminalWidget
from .analytics_dashboard_widget import AnalyticsDashboardWidget
from .bill_payment_widget import BillPaymentWidget
from .transaction_history_widget import TransactionHistoryWidget
from .card_management_widget import CardManagementWidget
from .user_management_widget import UserManagementWidget, LoginDialog
from .merchant_management_widget import MerchantManagementWidget
from .customer_management_widget import CustomerManagementWidget

# Import the app modules
from ..app.auth import AuthManager, UserRole, Permission
from ..app.merchant_management import MerchantManager
from ..app.customer_management import CustomerManager

# Import the native C++ module
try:
    from fintechx_desktop.infrastructure import fintechx_native
except ImportError:
    logging.error("Native C++ module (fintechx_native) not found. Ensure it is built and installed.")
    class DummyNative:
        def luhn_check(self, pan): return False
        def generate_pan(self, prefix, length): return None
        def generate_pan_batch(self, prefix, length, count): return []
    fintechx_native = DummyNative()


# Placeholder Widgets for other views
class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Main Dashboard Placeholder (Different from Analytics)"))
        self.setLayout(layout)


# --- PAN Tools Widget ---
class PanToolsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        validation_group = QGroupBox("Validate PAN")
        validation_layout = QFormLayout()
        self.pan_validate_input = QLineEdit()
        self.pan_validate_input.setPlaceholderText("Enter PAN to validate")
        self.validate_button = QPushButton("Validate")
        self.validate_result_label = QLabel("Result: ")
        validation_layout.addRow("PAN:", self.pan_validate_input)
        validation_layout.addRow(self.validate_button)
        validation_layout.addRow(self.validate_result_label)
        validation_group.setLayout(validation_layout)
        generation_group = QGroupBox("Generate PAN(s)")
        generation_layout = QFormLayout()
        self.pan_prefix_input = QLineEdit()
        self.pan_prefix_input.setPlaceholderText("e.g., 4, 51, 37")
        self.pan_length_combo = QComboBox()
        self.pan_length_combo.addItems(["16 (Visa/Mastercard)", "15 (Amex)", "13 (Visa)"])
        self.pan_count_spinbox = QSpinBox()
        self.pan_count_spinbox.setRange(1, 1000)
        self.pan_count_spinbox.setValue(1)
        self.generate_button = QPushButton("Generate")
        self.generated_pans_output = QTextEdit()
        self.generated_pans_output.setReadOnly(True)
        generation_layout.addRow("Prefix (IIN):", self.pan_prefix_input)
        generation_layout.addRow("Length:", self.pan_length_combo)
        generation_layout.addRow("Count:", self.pan_count_spinbox)
        generation_layout.addRow(self.generate_button)
        generation_layout.addRow("Generated PANs:", self.generated_pans_output)
        generation_group.setLayout(generation_layout)
        main_layout.addWidget(validation_group)
        main_layout.addWidget(generation_group)
        self.setLayout(main_layout)
        self.validate_button.clicked.connect(self.validate_pan)
        self.generate_button.clicked.connect(self.generate_pans)

    @pyqtSlot()
    def validate_pan(self):
        pan_to_validate = self.pan_validate_input.text().strip().replace(" ", "")
        if not pan_to_validate or not pan_to_validate.isdigit():
            self.validate_result_label.setText("Result: Invalid PAN format.")
            return
        try:
            is_valid = fintechx_native.luhn_check(pan_to_validate)
            self.validate_result_label.setText(
                f"Result: <font color=\"{'green' if is_valid else 'red'}\">{'Valid (Luhn Check Passed)' if is_valid else 'Invalid (Luhn Check Failed)'}</font>")
        except Exception as e:
            logging.error(f"Error during PAN validation: {e}")
            self.validate_result_label.setText("Result: <font color=\"red\">Error during validation.</font>")

    @pyqtSlot()
    def generate_pans(self):
        prefix = self.pan_prefix_input.text().strip()
        count = self.pan_count_spinbox.value()
        length_text = self.pan_length_combo.currentText()
        try:
            length = int(length_text.split(" ")[0])
        except (ValueError, IndexError):
            self.generated_pans_output.setText("Error: Invalid length selected.")
            return
        if not prefix or not prefix.isdigit() or len(prefix) >= length:
            self.generated_pans_output.setText("Error: Invalid prefix or length.")
            return
        try:
            if count == 1:
                pan = fintechx_native.generate_pan(prefix, length)
                self.generated_pans_output.setText(pan if pan else "Failed to generate PAN.")
            else:
                pans = fintechx_native.generate_pan_batch(prefix, length, count)
                self.generated_pans_output.setText("\n".join(pans) if pans else "Failed to generate PAN batch.")
        except Exception as e:
            logging.error(f"Error during PAN generation: {e}")
            self.generated_pans_output.setText("Error during generation.")


# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinTechX Desktop")
        self.setGeometry(100, 100, 1000, 800)

        # Initialize managers
        self.auth_manager = AuthManager()
        self.merchant_manager = MerchantManager()
        self.customer_manager = CustomerManager()
        self.session_id = None
        self.current_user = None

        # Create default admin user if no users exist
        if not self.auth_manager.get_all_users():
            self.auth_manager.create_user(
                username="admin",
                email="admin@fintechx.com",
                password="admin123",
                role=UserRole.ADMIN,
                first_name="System",
                last_name="Administrator"
            )
            logging.info("Created default admin user")

        # Set up UI
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.create_widgets()
        self.add_widgets_to_stack()
        self.setup_menus()

        # Show login dialog
        self.show_login_dialog()

        self.statusBar().showMessage("Ready")

    def create_widgets(self):
        self.dashboard_view = DashboardWidget()
        self.pan_tools_view = PanToolsWidget()
        self.virtual_terminal_view = VirtualTerminalWidget()
        self.analytics_dashboard_view = AnalyticsDashboardWidget()
        self.bill_payment_view = BillPaymentWidget()
        self.transaction_history_view = TransactionHistoryWidget()
        self.card_management_view = CardManagementWidget()
        self.user_management_view = UserManagementWidget(self.auth_manager)
        self.merchant_management_view = MerchantManagementWidget(self.merchant_manager)
        self.customer_management_view = CustomerManagementWidget(self.customer_manager)

    def add_widgets_to_stack(self):
        self.central_widget.addWidget(self.dashboard_view)
        self.central_widget.addWidget(self.pan_tools_view)
        self.central_widget.addWidget(self.virtual_terminal_view)
        self.central_widget.addWidget(self.analytics_dashboard_view)
        self.central_widget.addWidget(self.bill_payment_view)
        self.central_widget.addWidget(self.transaction_history_view)
        self.central_widget.addWidget(self.card_management_view)
        self.central_widget.addWidget(self.user_management_view)
        self.central_widget.addWidget(self.merchant_management_view)
        self.central_widget.addWidget(self.customer_management_view)

    def setup_menus(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        self.logout_action = file_menu.addAction("&Logout")
        self.logout_action.triggered.connect(self.logout)

        change_password_action = file_menu.addAction("Change &Password")
        change_password_action.triggered.connect(self.show_change_password_dialog)

        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        dashboard_action = view_menu.addAction("Dashboard")
        dashboard_action.triggered.connect(self.show_dashboard)

        pan_tools_action = view_menu.addAction("PAN Tools")
        pan_tools_action.triggered.connect(self.show_pan_tools)

        vt_action = view_menu.addAction("&Virtual Terminal")
        vt_action.triggered.connect(self.show_virtual_terminal)

        analytics_action = view_menu.addAction("&Analytics Dashboard")
        analytics_action.triggered.connect(self.show_analytics_dashboard)

        bill_payment_action = view_menu.addAction("&Bill Payment")
        bill_payment_action.triggered.connect(self.show_bill_payment)

        transaction_history_action = view_menu.addAction("&Transaction History")
        transaction_history_action.triggered.connect(self.show_transaction_history)

        card_management_action = view_menu.addAction("&Card Management")
        card_management_action.triggered.connect(self.show_card_management)

        # Admin menu
        self.admin_menu = menu_bar.addMenu("&Admin")
        self.admin_menu.setObjectName("Admin")

        user_management_action = self.admin_menu.addAction("&User Management")
        user_management_action.triggered.connect(self.show_user_management)

        merchant_management_action = self.admin_menu.addAction("&Merchant Management")
        merchant_management_action.triggered.connect(self.show_merchant_management)

        customer_management_action = self.admin_menu.addAction("&Customer Management")
        customer_management_action.triggered.connect(self.show_customer_management)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self.show_about_dialog)

    def show_login_dialog(self):
        dialog = LoginDialog(self.auth_manager, self)
        dialog.login_successful.connect(self.handle_successful_login)

        result = dialog.exec()
        if result != LoginDialog.DialogCode.Accepted:
            self.close()
            return

    @pyqtSlot(str, str)
    def handle_successful_login(self, session_id, username):
        self.session_id = session_id
        self.current_user = self.auth_manager.get_user_by_session(session_id)

        if not self.current_user:
            QMessageBox.critical(self, "Error", "Authentication error. Please try again.")
            self.show_login_dialog()
            return

        self.statusBar().showMessage(f"Logged in as {username}")
        self.update_ui_for_permissions()
        self.show_dashboard()

    def update_ui_for_permissions(self):
        if not self.current_user:
            return

        # Show/hide admin menu based on permissions
        has_admin_permission = (
                self.current_user.has_permission(Permission.MANAGE_USERS) or
                self.current_user.has_permission(Permission.MANAGE_MERCHANTS) or
                self.current_user.has_permission(Permission.MANAGE_CUSTOMERS)
        )
        self.admin_menu.menuAction().setVisible(has_admin_permission)

    @pyqtSlot()
    def logout(self):
        if self.session_id:
            self.auth_manager.logout(self.session_id)
            self.session_id = None
            self.current_user = None

        self.show_login_dialog()

    @pyqtSlot()
    def show_change_password_dialog(self):
        if not self.current_user:
            return

        from .user_management_widget import ChangePasswordDialog
        dialog = ChangePasswordDialog(self.auth_manager, self.current_user.id, self)

        if dialog.exec() == ChangePasswordDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Success", "Password changed successfully.")

    @pyqtSlot()
    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About FinTechX Desktop",
            "FinTechX Desktop\nVersion 1.0.0\n\nA robust banking desktop software."
        )

    def show_dashboard(self):
        self.central_widget.setCurrentWidget(self.dashboard_view)
        self.statusBar().showMessage("Dashboard Active")

    def show_pan_tools(self):
        self.central_widget.setCurrentWidget(self.pan_tools_view)
        self.statusBar().showMessage("PAN Tools Active")

    def show_virtual_terminal(self):
        self.central_widget.setCurrentWidget(self.virtual_terminal_view)
        self.statusBar().showMessage("Virtual Terminal Active")

    def show_analytics_dashboard(self):
        self.analytics_dashboard_view.refresh_dashboard()
        self.central_widget.setCurrentWidget(self.analytics_dashboard_view)
        self.statusBar().showMessage("Analytics Dashboard Active")

    def show_bill_payment(self):
        self.central_widget.setCurrentWidget(self.bill_payment_view)
        self.statusBar().showMessage("Bill Payment Management Active")

    def show_transaction_history(self):
        self.central_widget.setCurrentWidget(self.transaction_history_view)
        self.statusBar().showMessage("Transaction History and Reporting Active")

    def show_card_management(self):
        self.central_widget.setCurrentWidget(self.card_management_view)
        self.statusBar().showMessage("Card Management Active")

    def show_user_management(self):
        self.user_management_view.refresh_users_table()
        self.central_widget.setCurrentWidget(self.user_management_view)
        self.statusBar().showMessage("User Management Active")

    def show_merchant_management(self):
        self.central_widget.setCurrentWidget(self.merchant_management_view)
        self.statusBar().showMessage("Merchant Management Active")

    def show_customer_management(self):
        self.central_widget.setCurrentWidget(self.customer_management_view)
        self.statusBar().showMessage("Customer Management Active")

    def closeEvent(self, event):
        logging.info("Closing application...")
        event.accept()
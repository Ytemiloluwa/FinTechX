import logging
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton,
    QStackedWidget, QLineEdit, QFormLayout, QSpinBox, QTextEdit,
    QGroupBox, QComboBox
)
from PyQt6.QtCore import pyqtSlot

# Import other UI widgets
from .virtual_terminal_widget import VirtualTerminalWidget
from .analytics_dashboard_widget import AnalyticsDashboardWidget
from .fraud_detection_widget import FraudDetectionWidget
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
class LoginWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Login Screen Placeholder"))
        self.setLayout(layout)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Main Dashboard Placeholder (Different from Analytics)"))
        self.setLayout(layout)


# --- PAN Tools Widget ---
class PanToolsWidget(QWidget):
    # (Content from previous version - kept for brevity, assumed unchanged)
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
            if is_valid:
                self.validate_result_label.setText("Result: <font color='green'>Valid (Luhn Check Passed)</font>")
            else:
                self.validate_result_label.setText("Result: <font color='red'>Invalid (Luhn Check Failed)</font>")
        except Exception as e:
            logging.error(f"Error during PAN validation: {e}")
            self.validate_result_label.setText("Result: <font color='red'>Error during validation.</font>")

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
        self.setGeometry(100, 100, 900, 700)
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.create_widgets()
        self.add_widgets_to_stack()
        self.setup_menus()
        self.show_login_screen()
        self.statusBar().showMessage("Ready")

    def create_widgets(self):
        self.login_view = LoginWidget()
        self.dashboard_view = DashboardWidget()
        self.pan_tools_view = PanToolsWidget()
        self.virtual_terminal_view = VirtualTerminalWidget()
        self.analytics_dashboard_view = AnalyticsDashboardWidget()
        self.fraud_detection_view = FraudDetectionWidget()

    def add_widgets_to_stack(self):
        self.central_widget.addWidget(self.login_view)
        self.central_widget.addWidget(self.dashboard_view)
        self.central_widget.addWidget(self.pan_tools_view)
        self.central_widget.addWidget(self.virtual_terminal_view)
        self.central_widget.addWidget(self.analytics_dashboard_view)
        self.central_widget.addWidget(self.fraud_detection_view)


    def setup_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        view_menu = menu_bar.addMenu("&View")
        login_action = view_menu.addAction("Login Screen")
        dashboard_action = view_menu.addAction("Dashboard")
        pan_tools_action = view_menu.addAction("PAN Tools")
        vt_action = view_menu.addAction("&Virtual Terminal")
        analytics_action = view_menu.addAction("&Analytics Dashboard")
        fraud_action = view_menu.addAction("&Fraud Detection")


        login_action.triggered.connect(self.show_login_screen)
        dashboard_action.triggered.connect(self.show_dashboard)
        pan_tools_action.triggered.connect(self.show_pan_tools)
        vt_action.triggered.connect(self.show_virtual_terminal)
        analytics_action.triggered.connect(self.show_analytics_dashboard)
        fraud_action.triggered.connect(self.show_fraud_detection)


    def show_login_screen(self):
        self.central_widget.setCurrentWidget(self.login_view)
        self.statusBar().showMessage("Please Login")

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
        # Refresh data when the dashboard is shown
        self.analytics_dashboard_view.refresh_dashboard()
        self.central_widget.setCurrentWidget(self.analytics_dashboard_view)
        self.statusBar().showMessage("Analytics Dashboard Active")

    def show_fraud_detection(self):
        self.central_widget.setCurrentWidget(self.fraud_detection_view)
        self.statusBar().showMessage("Fraud Detection Active")

    def closeEvent(self, event):
        logging.info("Closing application...")
        event.accept()
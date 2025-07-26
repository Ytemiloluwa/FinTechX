import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QHeaderView, QTextEdit,
    QMessageBox, QTabWidget, QDialog, QDialogButtonBox, QCheckBox, QGridLayout,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QColor

from ..app.auth import (
    AuthManager, User, UserRole, Permission, RolePermissions
)


class LoginDialog(QDialog):
    login_successful = pyqtSignal(str, str)  # session_id, username

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.setWindowTitle("FinTechX Login")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Logo/title
        title_label = QLabel("FinTechX Desktop")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Secure Financial Management")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Login form
        form_group = QGroupBox("Login")
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)

        self.remember_checkbox = QCheckBox("Remember username")
        form_layout.addRow("", self.remember_checkbox)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Error message
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.attempt_login)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)

        layout.addLayout(button_layout)

        # Set default button and focus
        self.login_button.setDefault(True)
        self.username_input.setFocus()

    @pyqtSlot()
    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.show_error("Username and password are required.")
            return

        session_id = self.auth_manager.authenticate(username, password)

        if not session_id:
            self.show_error("Invalid username or password.")
            return

        user = self.auth_manager.get_user_by_session(session_id)
        if not user:
            self.show_error("Authentication error.")
            return

        self.login_successful.emit(session_id, user.username)
        self.accept()

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.setVisible(True)


class UserDetailsDialog(QDialog):
    def __init__(self, auth_manager, user=None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.user = user
        self.setWindowTitle("User Details" if user else "Add New User")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # User info form
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        form_layout.addRow("Username:", self.username_input)

        self.email_input = QLineEdit()
        form_layout.addRow("Email:", self.email_input)

        self.first_name_input = QLineEdit()
        form_layout.addRow("First Name:", self.first_name_input)

        self.last_name_input = QLineEdit()
        form_layout.addRow("Last Name:", self.last_name_input)

        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value)
        form_layout.addRow("Role:", self.role_combo)

        if not self.user:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            form_layout.addRow("Password:", self.password_input)

            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            form_layout.addRow("Confirm Password:", self.confirm_password_input)

        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)
        form_layout.addRow("Status:", self.active_checkbox)

        # Custom permissions
        permissions_group = QGroupBox("Custom Permissions")
        permissions_layout = QVBoxLayout()

        self.permissions_list = QListWidget()
        for permission in Permission:
            item = QListWidgetItem(permission.value)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.permissions_list.addItem(item)

        permissions_layout.addWidget(self.permissions_list)
        permissions_group.setLayout(permissions_layout)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        # Add all components to main layout
        layout.addLayout(form_layout)
        layout.addWidget(permissions_group)
        layout.addWidget(button_box)

        # If editing an existing user, populate fields
        if self.user:
            self.username_input.setText(self.user.username)
            self.username_input.setReadOnly(True)
            self.email_input.setText(self.user.email)
            self.first_name_input.setText(self.user.first_name)
            self.last_name_input.setText(self.user.last_name)

            role_index = self.role_combo.findText(self.user.role.value)
            if role_index >= 0:
                self.role_combo.setCurrentIndex(role_index)

            self.active_checkbox.setChecked(self.user.active)

            # Set custom permissions
            for i in range(self.permissions_list.count()):
                item = self.permissions_list.item(i)
                perm_text = item.text()
                try:
                    permission = Permission(perm_text)
                    if permission in self.user.custom_permissions:
                        item.setCheckState(Qt.CheckState.Checked)
                except ValueError:
                    pass

    @pyqtSlot()
    def validate_and_accept(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()

        if not username:
            QMessageBox.warning(self, "Input Error", "Username is required.")
            return

        if not email:
            QMessageBox.warning(self, "Input Error", "Email is required.")
            return

        if not self.user:
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()

            if not password:
                QMessageBox.warning(self, "Input Error", "Password is required.")
                return

            if password != confirm_password:
                QMessageBox.warning(self, "Input Error", "Passwords do not match.")
                return

        self.accept()

    def get_user_data(self):
        role = None
        for r in UserRole:
            if r.value == self.role_combo.currentText():
                role = r
                break

        custom_permissions = set()
        for i in range(self.permissions_list.count()):
            item = self.permissions_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                try:
                    permission = Permission(item.text())
                    custom_permissions.add(permission)
                except ValueError:
                    pass

        data = {
            "username": self.username_input.text().strip(),
            "email": self.email_input.text().strip(),
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "role": role,
            "active": self.active_checkbox.isChecked(),
            "custom_permissions": custom_permissions
        }

        if not self.user:
            data["password"] = self.password_input.text()

        return data


class ChangePasswordDialog(QDialog):
    def __init__(self, auth_manager, user_id, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.user_id = user_id
        self.setWindowTitle("Change Password")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Current Password:", self.current_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("New Password:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Confirm New Password:", self.confirm_password_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    @pyqtSlot()
    def validate_and_accept(self):
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not current_password:
            QMessageBox.warning(self, "Input Error", "Current password is required.")
            return

        if not new_password:
            QMessageBox.warning(self, "Input Error", "New password is required.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Input Error", "New passwords do not match.")
            return

        success = self.auth_manager.change_password(self.user_id, current_password, new_password)

        if not success:
            QMessageBox.warning(self, "Error", "Failed to change password. Current password may be incorrect.")
            return

        self.accept()


class UserManagementWidget(QWidget):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.logger = logging.getLogger("fintechx_desktop.ui.user_management")

        main_layout = QVBoxLayout(self)

        # Create tabs for different views
        self.tab_widget = QTabWidget()

        # Create the users list tab
        self.users_list_widget = QWidget()
        self.setup_users_list_tab()
        self.tab_widget.addTab(self.users_list_widget, "Users")

        # Create the roles and permissions tab
        self.roles_permissions_widget = QWidget()
        self.setup_roles_permissions_tab()
        self.tab_widget.addTab(self.roles_permissions_widget, "Roles & Permissions")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def setup_users_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_group = QGroupBox("Filter Users")
        filter_layout = QHBoxLayout()

        self.role_filter = QComboBox()
        self.role_filter.addItem("All Roles")
        for role in UserRole:
            self.role_filter.addItem(role.value)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Users", "Active Only", "Inactive Only", "Locked Users"])

        self.username_filter = QLineEdit()
        self.username_filter.setPlaceholderText("Search by username or name...")

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.refresh_users_table)

        filter_layout.addWidget(QLabel("Role:"))
        filter_layout.addWidget(self.role_filter)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.username_filter)
        filter_layout.addWidget(self.apply_filter_button)
        filter_group.setLayout(filter_layout)

        # Users table
        self.users_table = QTableWidget(0, 7)
        self.users_table.setHorizontalHeaderLabels([
            "Username", "Full Name", "Email", "Role", "Status", "Last Login", "Actions"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        # Action buttons
        action_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_users_table)

        self.add_user_button = QPushButton("Add New User")
        self.add_user_button.clicked.connect(self.add_new_user)

        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.add_user_button)

        layout.addWidget(filter_group)
        layout.addWidget(self.users_table)
        layout.addLayout(action_layout)

        self.users_list_widget.setLayout(layout)

        # Initial data load
        self.refresh_users_table()

    def setup_roles_permissions_tab(self):
        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Roles list
        roles_group = QGroupBox("Roles")
        roles_layout = QVBoxLayout()

        self.roles_list = QListWidget()
        for role in UserRole:
            self.roles_list.addItem(role.value)

        self.roles_list.currentRowChanged.connect(self.update_permissions_view)
        roles_layout.addWidget(self.roles_list)
        roles_group.setLayout(roles_layout)

        # Permissions for selected role
        permissions_group = QGroupBox("Permissions")
        permissions_layout = QVBoxLayout()

        self.permissions_table = QTableWidget(0, 2)
        self.permissions_table.setHorizontalHeaderLabels(["Permission", "Granted"])
        self.permissions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.permissions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        permissions_layout.addWidget(self.permissions_table)
        permissions_group.setLayout(permissions_layout)

        splitter.addWidget(roles_group)
        splitter.addWidget(permissions_group)
        splitter.setSizes([200, 400])

        layout.addWidget(splitter)

        self.roles_permissions_widget.setLayout(layout)

        # Initial selection
        if self.roles_list.count() > 0:
            self.roles_list.setCurrentRow(0)

    @pyqtSlot()
    def refresh_users_table(self):
        self.users_table.setRowCount(0)

        role_filter = self.role_filter.currentText()
        status_filter = self.status_filter.currentText()
        search_text = self.username_filter.text().strip().lower()

        users = self.auth_manager.get_all_users()

        # Apply role filter
        if role_filter != "All Roles":
            role = None
            for r in UserRole:
                if r.value == role_filter:
                    role = r
                    break
            if role:
                users = [u for u in users if u.role == role]

        # Apply status filter
        if status_filter == "Active Only":
            users = [u for u in users if u.active]
        elif status_filter == "Inactive Only":
            users = [u for u in users if not u.active]
        elif status_filter == "Locked Users":
            users = [u for u in users if u.is_locked()]

        # Apply search filter
        if search_text:
            filtered_users = []
            for user in users:
                if (search_text in user.username.lower() or
                        search_text in user.first_name.lower() or
                        search_text in user.last_name.lower() or
                        search_text in user.full_name.lower()):
                    filtered_users.append(user)
            users = filtered_users

        self.users_table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.full_name))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.email))
            self.users_table.setItem(row, 3, QTableWidgetItem(user.role.value))

            status_text = "Active" if user.active else "Inactive"
            if user.is_locked():
                status_text += " (Locked)"

            status_item = QTableWidgetItem(status_text)
            if not user.active or user.is_locked():
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            else:
                status_item.setBackground(QColor(200, 255, 200))  # Light green

            self.users_table.setItem(row, 4, status_item)

            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
            self.users_table.setItem(row, 5, QTableWidgetItem(last_login))

            # Action buttons in a widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("user_id", user.id)
            edit_button.clicked.connect(self.edit_user)

            if user.is_locked():
                unlock_button = QPushButton("Unlock")
                unlock_button.setProperty("user_id", user.id)
                unlock_button.clicked.connect(self.unlock_user)
                actions_layout.addWidget(unlock_button)
            elif user.active:
                lock_button = QPushButton("Lock")
                lock_button.setProperty("user_id", user.id)
                lock_button.clicked.connect(self.lock_user)
                actions_layout.addWidget(lock_button)

            if user.active:
                deactivate_button = QPushButton("Deactivate")
                deactivate_button.setProperty("user_id", user.id)
                deactivate_button.clicked.connect(self.deactivate_user)
                actions_layout.addWidget(deactivate_button)
            else:
                activate_button = QPushButton("Activate")
                activate_button.setProperty("user_id", user.id)
                activate_button.clicked.connect(self.activate_user)
                actions_layout.addWidget(activate_button)

            actions_layout.addWidget(edit_button)

            self.users_table.setCellWidget(row, 6, actions_widget)

    @pyqtSlot(int)
    def update_permissions_view(self, row):
        if row < 0:
            return

        role_text = self.roles_list.item(row).text()
        role = None
        for r in UserRole:
            if r.value == role_text:
                role = r
                break

        if not role:
            return

        permissions = RolePermissions.get_permissions_for_role(role)

        self.permissions_table.setRowCount(len(Permission))

        for row, permission in enumerate(Permission):
            self.permissions_table.setItem(row, 0, QTableWidgetItem(permission.value))

            granted = "Yes" if permission in permissions else "No"
            granted_item = QTableWidgetItem(granted)

            if granted == "Yes":
                granted_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                granted_item.setBackground(QColor(255, 200, 200))  # Light red

            self.permissions_table.setItem(row, 1, granted_item)

    @pyqtSlot()
    def add_new_user(self):
        dialog = UserDetailsDialog(self.auth_manager, parent=self)
        if dialog.exec():
            user_data = dialog.get_user_data()

            user_id = self.auth_manager.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                role=user_data["role"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                custom_permissions=user_data["custom_permissions"]
            )

            if user_id:
                if not user_data["active"]:
                    self.auth_manager.deactivate_user(user_id)

                QMessageBox.information(self, "Success", "User created successfully.")
                self.refresh_users_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to create user. Username or email may already exist.")

    @pyqtSlot()
    def edit_user(self):
        button = self.sender()
        user_id = button.property("user_id")

        user = self.auth_manager.get_user(user_id)
        if not user:
            QMessageBox.warning(self, "Error", "User not found.")
            return

        dialog = UserDetailsDialog(self.auth_manager, user, parent=self)
        if dialog.exec():
            user_data = dialog.get_user_data()

            updates = {
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "role": user_data["role"],
                "active": user_data["active"],
                "custom_permissions": [p.value for p in user_data["custom_permissions"]]
            }

            success = self.auth_manager.update_user(user_id, updates)

            if success:
                QMessageBox.information(self, "Success", "User updated successfully.")
                self.refresh_users_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to update user.")

    @pyqtSlot()
    def lock_user(self):
        button = self.sender()
        user_id = button.property("user_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Lock",
            "Are you sure you want to lock this user? They will be logged out and unable to log in.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.auth_manager.lock_user(user_id)

            if success:
                QMessageBox.information(self, "Success", "User locked successfully.")
                self.refresh_users_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to lock user.")

    @pyqtSlot()
    def unlock_user(self):
        button = self.sender()
        user_id = button.property("user_id")

        success = self.auth_manager.unlock_user(user_id)

        if success:
            QMessageBox.information(self, "Success", "User unlocked successfully.")
            self.refresh_users_table()
        else:
            QMessageBox.warning(self, "Error", "Failed to unlock user.")

    @pyqtSlot()
    def activate_user(self):
        button = self.sender()
        user_id = button.property("user_id")

        success = self.auth_manager.activate_user(user_id)

        if success:
            QMessageBox.information(self, "Success", "User activated successfully.")
            self.refresh_users_table()
        else:
            QMessageBox.warning(self, "Error", "Failed to activate user.")

    @pyqtSlot()
    def deactivate_user(self):
        button = self.sender()
        user_id = button.property("user_id")

        confirm = QMessageBox.question(
            self,
            "Confirm Deactivation",
            "Are you sure you want to deactivate this user? They will be logged out and unable to log in.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.auth_manager.deactivate_user(user_id)

            if success:
                QMessageBox.information(self, "Success", "User deactivated successfully.")
                self.refresh_users_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to deactivate user.")

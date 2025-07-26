import logging
import hashlib
import uuid
import os
import json
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any


class UserRole(Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    OPERATOR = "Operator"
    VIEWER = "Viewer"
    CUSTOMER = "Customer"
    MERCHANT = "Merchant"


class Permission(Enum):
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_TRANSACTIONS = "view_transactions"
    PROCESS_PAYMENTS = "process_payments"
    MANAGE_CARDS = "manage_cards"
    MANAGE_BILLS = "manage_bills"
    MANAGE_USERS = "manage_users"
    MANAGE_MERCHANTS = "manage_merchants"
    MANAGE_CUSTOMERS = "manage_customers"
    SYSTEM_SETTINGS = "system_settings"
    EXPORT_DATA = "export_data"
    VIEW_REPORTS = "view_reports"
    FRAUD_MANAGEMENT = "fraud_management"


class RolePermissions:
    DEFAULT_PERMISSIONS = {
        UserRole.ADMIN: {
            Permission.VIEW_DASHBOARD, Permission.VIEW_TRANSACTIONS,
            Permission.PROCESS_PAYMENTS, Permission.MANAGE_CARDS,
            Permission.MANAGE_BILLS, Permission.MANAGE_USERS,
            Permission.MANAGE_MERCHANTS, Permission.MANAGE_CUSTOMERS,
            Permission.SYSTEM_SETTINGS, Permission.EXPORT_DATA,
            Permission.VIEW_REPORTS, Permission.FRAUD_MANAGEMENT
        },
        UserRole.MANAGER: {
            Permission.VIEW_DASHBOARD, Permission.VIEW_TRANSACTIONS,
            Permission.PROCESS_PAYMENTS, Permission.MANAGE_CARDS,
            Permission.MANAGE_BILLS, Permission.MANAGE_CUSTOMERS,
            Permission.EXPORT_DATA, Permission.VIEW_REPORTS,
            Permission.FRAUD_MANAGEMENT
        },
        UserRole.OPERATOR: {
            Permission.VIEW_DASHBOARD, Permission.VIEW_TRANSACTIONS,
            Permission.PROCESS_PAYMENTS, Permission.VIEW_REPORTS
        },
        UserRole.VIEWER: {
            Permission.VIEW_DASHBOARD, Permission.VIEW_TRANSACTIONS,
            Permission.VIEW_REPORTS
        },
        UserRole.CUSTOMER: {
            Permission.VIEW_DASHBOARD, Permission.VIEW_TRANSACTIONS,
            Permission.MANAGE_CARDS, Permission.MANAGE_BILLS
        },
        UserRole.MERCHANT: {
            Permission.VIEW_DASHBOARD, Permission.VIEW_TRANSACTIONS,
            Permission.PROCESS_PAYMENTS, Permission.VIEW_REPORTS
        }
    }

    @classmethod
    def get_permissions_for_role(cls, role: UserRole) -> Set[Permission]:
        return cls.DEFAULT_PERMISSIONS.get(role, set())


class User:
    def __init__(
            self,
            username: str,
            email: str,
            password_hash: str,
            salt: str,
            role: UserRole = UserRole.VIEWER,
            first_name: str = "",
            last_name: str = "",
            custom_permissions: Set[Permission] = None,
            metadata: Dict = None
    ):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.salt = salt
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.custom_permissions = custom_permissions or set()
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.last_login = None
        self.failed_login_attempts = 0
        self.locked_until = None
        self.active = True

    @property
    def full_name(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

    @property
    def permissions(self) -> Set[Permission]:
        base_permissions = RolePermissions.get_permissions_for_role(self.role)
        return base_permissions.union(self.custom_permissions)

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    def is_locked(self) -> bool:
        if not self.locked_until:
            return False
        return datetime.now() < self.locked_until

    def to_dict(self, include_sensitive: bool = False) -> Dict:
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "custom_permissions": [p.value for p in self.custom_permissions],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "failed_login_attempts": self.failed_login_attempts,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            "active": self.active
        }

        if include_sensitive:
            data["password_hash"] = self.password_hash
            data["salt"] = self.salt

        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        custom_permissions = set()
        for perm_str in data.get("custom_permissions", []):
            try:
                custom_permissions.add(Permission(perm_str))
            except ValueError:
                pass

        user = cls(
            username=data["username"],
            email=data["email"],
            password_hash=data.get("password_hash", ""),
            salt=data.get("salt", ""),
            role=UserRole(data["role"]),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            custom_permissions=custom_permissions,
            metadata=data.get("metadata", {})
        )

        user.id = data["id"]
        user.created_at = datetime.fromisoformat(data["created_at"])
        user.updated_at = datetime.fromisoformat(data["updated_at"])

        if data.get("last_login"):
            user.last_login = datetime.fromisoformat(data["last_login"])

        user.failed_login_attempts = data.get("failed_login_attempts", 0)

        if data.get("locked_until"):
            user.locked_until = datetime.fromisoformat(data["locked_until"])

        user.active = data.get("active", True)

        return user


class AuthManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.users = {}
        self.logger = logging.getLogger("fintechx_desktop.app.auth")
        self.storage_path = storage_path
        self.active_sessions = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.session_timeout = timedelta(hours=8)

    def create_user(
            self,
            username: str,
            email: str,
            password: str,
            role: UserRole = UserRole.VIEWER,
            first_name: str = "",
            last_name: str = "",
            custom_permissions: Set[Permission] = None
    ) -> Optional[str]:
        if self.get_user_by_username(username) or self.get_user_by_email(email):
            self.logger.warning(f"Attempted to create user with existing username or email: {username}, {email}")
            return None

        salt = os.urandom(32).hex()
        password_hash = self._hash_password(password, salt)

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            salt=salt,
            role=role,
            first_name=first_name,
            last_name=last_name,
            custom_permissions=custom_permissions
        )

        self.users[user.id] = user
        self.logger.info(f"Created user {user.id} with username {username}")
        return user.id

    def authenticate(self, username: str, password: str) -> Optional[str]:
        user = self.get_user_by_username(username)

        if not user:
            self.logger.warning(f"Authentication attempt for non-existent user: {username}")
            return None

        if not user.active:
            self.logger.warning(f"Authentication attempt for inactive user: {username}")
            return None

        if user.is_locked():
            self.logger.warning(f"Authentication attempt for locked user: {username}")
            return None

        password_hash = self._hash_password(password, user.salt)

        if password_hash != user.password_hash:
            user.failed_login_attempts += 1
            user.updated_at = datetime.now()

            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.now() + self.lockout_duration
                self.logger.warning(f"User {username} locked due to too many failed login attempts")

            self.logger.warning(f"Failed authentication attempt for user: {username}")
            return None

        user.failed_login_attempts = 0
        user.last_login = datetime.now()
        user.updated_at = datetime.now()

        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "user_id": user.id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + self.session_timeout
        }

        self.logger.info(f"User {username} authenticated successfully")
        return session_id

    def validate_session(self, session_id: str) -> Optional[str]:
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        if datetime.now() > session["expires_at"]:
            del self.active_sessions[session_id]
            return None

        return session["user_id"]

    def logout(self, session_id: str) -> bool:
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        for user in self.users.values():
            if user.username.lower() == username.lower():
                return user
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return user
        return None

    def get_user_by_session(self, session_id: str) -> Optional[User]:
        user_id = self.validate_session(session_id)
        if user_id:
            return self.get_user(user_id)
        return None

    def update_user(self, user_id: str, updates: Dict) -> bool:
        user = self.get_user(user_id)
        if not user:
            self.logger.warning(f"Attempted to update non-existent user: {user_id}")
            return False

        for key, value in updates.items():
            if key == "role" and isinstance(value, str):
                try:
                    user.role = UserRole(value)
                except ValueError:
                    self.logger.error(f"Invalid user role: {value}")
                    continue
            elif key == "custom_permissions" and isinstance(value, list):
                custom_permissions = set()
                for perm_str in value:
                    try:
                        custom_permissions.add(Permission(perm_str))
                    except ValueError:
                        self.logger.error(f"Invalid permission: {perm_str}")
                user.custom_permissions = custom_permissions
            elif key == "password":
                salt = os.urandom(32).hex()
                password_hash = self._hash_password(value, salt)
                user.password_hash = password_hash
                user.salt = salt
            elif hasattr(user, key) and key not in ["id", "password_hash", "salt"]:
                setattr(user, key, value)

        user.updated_at = datetime.now()
        self.logger.info(f"Updated user {user_id}")
        return True

    def delete_user(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]

            # Remove any active sessions for this user
            session_ids_to_remove = []
            for session_id, session in self.active_sessions.items():
                if session["user_id"] == user_id:
                    session_ids_to_remove.append(session_id)

            for session_id in session_ids_to_remove:
                del self.active_sessions[session_id]

            self.logger.info(f"Deleted user {user_id}")
            return True

        self.logger.warning(f"Attempted to delete non-existent user: {user_id}")
        return False

    def get_all_users(self) -> List[User]:
        return list(self.users.values())

    def get_users_by_role(self, role: UserRole) -> List[User]:
        return [user for user in self.users.values() if user.role == role]

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            self.logger.warning(f"Attempted to change password for non-existent user: {user_id}")
            return False

        current_hash = self._hash_password(current_password, user.salt)
        if current_hash != user.password_hash:
            self.logger.warning(f"Incorrect current password for user: {user_id}")
            return False

        salt = os.urandom(32).hex()
        password_hash = self._hash_password(new_password, salt)

        user.password_hash = password_hash
        user.salt = salt
        user.updated_at = datetime.now()

        self.logger.info(f"Changed password for user {user_id}")
        return True

    def reset_password(self, user_id: str, new_password: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            self.logger.warning(f"Attempted to reset password for non-existent user: {user_id}")
            return False

        salt = os.urandom(32).hex()
        password_hash = self._hash_password(new_password, salt)

        user.password_hash = password_hash
        user.salt = salt
        user.failed_login_attempts = 0
        user.locked_until = None
        user.updated_at = datetime.now()

        self.logger.info(f"Reset password for user {user_id}")
        return True

    def lock_user(self, user_id: str, duration: Optional[timedelta] = None) -> bool:
        user = self.get_user(user_id)
        if not user:
            self.logger.warning(f"Attempted to lock non-existent user: {user_id}")
            return False

        lock_duration = duration or self.lockout_duration
        user.locked_until = datetime.now() + lock_duration
        user.updated_at = datetime.now()

        # Remove any active sessions for this user
        session_ids_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session["user_id"] == user_id:
                session_ids_to_remove.append(session_id)

        for session_id in session_ids_to_remove:
            del self.active_sessions[session_id]

        self.logger.info(f"Locked user {user_id} for {lock_duration}")
        return True

    def unlock_user(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            self.logger.warning(f"Attempted to unlock non-existent user: {user_id}")
            return False

        user.locked_until = None
        user.failed_login_attempts = 0
        user.updated_at = datetime.now()

        self.logger.info(f"Unlocked user {user_id}")
        return True

    def activate_user(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            self.logger.warning(f"Attempted to activate non-existent user: {user_id}")
            return False

        user.active = True
        user.updated_at = datetime.now()

        self.logger.info(f"Activated user {user_id}")
        return True

    def deactivate_user(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            self.logger.warning(f"Attempted to deactivate non-existent user: {user_id}")
            return False

        user.active = False
        user.updated_at = datetime.now()

        # Remove any active sessions for this user
        session_ids_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session["user_id"] == user_id:
                session_ids_to_remove.append(session_id)

        for session_id in session_ids_to_remove:
            del self.active_sessions[session_id]

        self.logger.info(f"Deactivated user {user_id}")
        return True

    def export_to_json(self, file_path: str) -> bool:
        try:
            with open(file_path, 'w') as f:
                json.dump([user.to_dict(include_sensitive=True) for user in self.users.values()], f, indent=2)
            self.logger.info(f"Exported {len(self.users)} users to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export users: {e}")
            return False

    def import_from_json(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            imported_users = []
            for item in data:
                try:
                    user = User.from_dict(item)
                    imported_users.append(user)
                except Exception as e:
                    self.logger.error(f"Failed to import user: {e}")

            if imported_users:
                for user in imported_users:
                    self.users[user.id] = user
                self.logger.info(f"Imported {len(imported_users)} users from {file_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to import users: {e}")
            return False

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            bytes.fromhex(salt),
            100000
        ).hex()

#!/usr/bin/python3
"""Macaque Classic greeter: a password-only account chooser for greetd.

Runs as _greetd (not root). PAM authentication is performed by greetd over
its Unix socket; the greeter never verifies or stores passwords itself.
"""
import json
import os
import pwd
import socket
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)

SOCKET_PATH = Path("/run/greetd.sock")
SESSION = ["/usr/local/bin/macaque-session"]


def accounts(passwd_entries=None):
    """Only human accounts with a real home, excluding the live preview user."""
    entries = passwd_entries if passwd_entries is not None else pwd.getpwall()
    result = []
    for user in entries:
        if user.pw_uid < 1000 or user.pw_uid >= 65534:
            continue
        if user.pw_name in ("nobody", "_greetd", "macaque"):
            continue
        if not user.pw_dir.startswith("/home/"):
            continue
        if user.pw_shell.endswith(("nologin", "false")):
            continue
        result.append(user.pw_name)
    return sorted(set(result))


class GreeterProtocol:
    def __init__(self, path=SOCKET_PATH):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(str(path))
        self.buffer = b""

    def message(self, payload):
        blob = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.sock.sendall(len(blob).to_bytes(4, "little") + blob)
        while len(self.buffer) < 4:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("Login service disconnected")
            self.buffer += chunk
        size = int.from_bytes(self.buffer[:4], "little")
        if size > 1024 * 1024:
            raise ValueError("Unexpected login response")
        self.buffer = self.buffer[4:]
        while len(self.buffer) < size:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("Login service disconnected")
            self.buffer += chunk
        result = json.loads(self.buffer[:size])
        self.buffer = self.buffer[size:]
        return result

    def close(self):
        self.sock.close()

    def authenticate(self, username, password):
        reply = self.message({"type": "create_session", "username": username})
        for _ in range(8):
            kind = reply.get("type")
            if kind == "error":
                raise ValueError(reply.get("description") or "Authentication failed")
            if kind == "success":
                return
            if kind != "auth_message":
                raise ValueError("Unexpected authentication response")
            prompt = reply.get("auth_message_type")
            if prompt == "secret":
                answer = password
            elif prompt == "visible":
                # A separate challenge (such as OTP) cannot safely be guessed.
                raise ValueError("This account needs an additional login challenge")
            else:
                raise ValueError("This account needs an unsupported login challenge")
            reply = self.message({"type": "post_auth_message_response", "response": answer})
        raise ValueError("Too many authentication challenges")

    def start(self):
        reply = self.message({"type": "start_session", "cmd": SESSION, "env": [
            "XDG_SESSION_TYPE=wayland", "XDG_CURRENT_DESKTOP=Macaque",
            "DESKTOP_SESSION=macaque",
        ]})
        if reply.get("type") != "success":
            raise ValueError(reply.get("description") or "Could not start desktop")


class Login(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macaque Classic Login")
        self.setObjectName("login")
        self.setMinimumSize(680, 420)
        outer = QVBoxLayout(self)
        outer.addStretch(1)
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(350)
        content = QVBoxLayout(card)
        content.setSpacing(13)
        header = QLabel("Macaque Classic")
        header.setObjectName("heading")
        header.setAlignment(Qt.AlignCenter)
        content.addWidget(header)
        avatar = QLabel("◉")
        avatar.setObjectName("avatar")
        avatar.setAlignment(Qt.AlignCenter)
        content.addWidget(avatar)
        self.users = QComboBox()
        self.users.setObjectName("users")
        self.users.addItems(accounts())
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setObjectName("username")
        if self.users.count():
            self.username.hide()
            content.addWidget(self.users)
            other = QPushButton("Other account…")
            other.setObjectName("other")
            other.clicked.connect(self.show_other)
            content.addWidget(other)
        else:
            content.addWidget(self.username)
        self.password = QLineEdit()
        self.password.setObjectName("password")
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.returnPressed.connect(self.login)
        content.addWidget(self.password)
        self.error = QLabel("")
        self.error.setObjectName("error")
        self.error.setWordWrap(True)
        content.addWidget(self.error)
        submit = QPushButton("Log In")
        submit.setObjectName("submit")
        submit.clicked.connect(self.login)
        content.addWidget(submit)
        holder = QHBoxLayout()
        holder.addStretch()
        holder.addWidget(card)
        holder.addStretch()
        outer.addLayout(holder)
        outer.addStretch(1)
        self.password.setFocus()

    def show_other(self):
        self.users.hide()
        self.username.show()
        self.username.setFocus()

    def login(self):
        username = (self.username.text() if self.username.isVisible() else self.users.currentText()).strip()
        password = self.password.text()
        if not username or not password:
            self.error.setText("Enter your password.")
            return
        self.error.setText("")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        client = None
        try:
            client = GreeterProtocol()
            client.authenticate(username, password)
            client.start()
        except (OSError, ValueError, ConnectionError) as exc:
            # Do not leave a secret in the input after a failure.
            self.password.clear()
            self.error.setText(str(exc))
            self.password.setFocus()
        else:
            QApplication.quit()
        finally:
            if client is not None:
                client.close()
            QApplication.restoreOverrideCursor()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget#login {background-color: #7895a9; color: #20242a;}
        QFrame#card {background: #ececec; border: 2px solid #454545;
                     border-radius: 8px; padding: 20px;}
        QLabel#heading {font-size: 22px; font-weight: bold;}
        QLabel#avatar {font-size: 48px; color: #5c7790;}
        QLineEdit, QComboBox {background: #fff; color: #20242a; padding: 9px;
                             border: 1px solid #888; border-radius: 5px; font-size: 15px;}
        QPushButton {border: 1px solid #666; border-radius: 5px; padding: 9px;
                     background: #ddd; color: #20242a;}
        QPushButton#submit {background: #b9d8ef; font-weight: bold;}
        QPushButton#other {border: none; background: transparent; color: #30587a;}
        QLabel#error {color: #9b2020;}
    """)
    w = Login()
    w.showFullScreen()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

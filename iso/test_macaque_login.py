"""Offline checks for the Macaque Classic account-picker greeter.

No PAM calls, host login changes or real greetd socket access.
"""
import importlib.util
import os
import pwd
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("macaque_login", ROOT/"wayland/macaque-login.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def user(name, uid, shell="/bin/bash", home=None):
    return SimpleNamespace(pw_name=name, pw_uid=uid, pw_dir=home or "/home/"+name, pw_shell=shell)

assert module.accounts([
    user("root", 0), user("_greetd", 999), user("macaque", 1000),
    user("drew", 1001), user("guest", 1002, "/usr/sbin/nologin"),
    user("another", 1003), user("other", 1004, home="/srv/other"),
]) == ["another", "drew"]

# The UI selects an existing account automatically, keeps the password masked,
# and allows selecting another account, without bypassing authentication.
from PySide6.QtWidgets import QApplication, QLineEdit
app = QApplication.instance() or QApplication([])
original = module.accounts
module.accounts = lambda: ["drew", "second"]
try:
    widget = module.Login()
    widget.show()
    app.processEvents()
    assert widget.users.currentText() == "drew"
    assert widget.password.echoMode() == QLineEdit.Password
    assert not widget.username.isVisible()
    widget.show_other()
    app.processEvents()
    assert widget.username.isVisible()
    widget.close()
finally:
    module.accounts = original

# Protocol exchanges always send the current chosen username and require the
# password challenge before launching the session.
class MockProtocol(module.GreeterProtocol):
    def __init__(self):
        self.requests = []
        self.replies = [
            {"type":"auth_message", "auth_message_type":"secret", "auth_message":"Password:"},
            {"type":"success"}, {"type":"success"}
        ]
    def message(self, data):
        self.requests.append(data)
        return self.replies.pop(0)

mock = MockProtocol()
mock.authenticate("drew", "test-password")
mock.start()
assert mock.requests[0] == {"type":"create_session", "username":"drew"}
assert mock.requests[1] == {"type":"post_auth_message_response", "response":"test-password"}
assert mock.requests[2]["type"] == "start_session"
assert mock.requests[2]["cmd"] == ["/usr/local/bin/macaque-session"]

print("Greeter account filtering, password UI and mocked greetd authentication passed.")

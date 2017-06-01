from PyQt4.QtGui import *
from PyQt4.QtCore import Qt


class SelectDialog(QDialog):
    def __init__(self, parent=None):
        super(SelectDialog, self).__init__(parent)
        self.directory = None

        layout = QVBoxLayout(self)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.layout().setAlignment(Qt.AlignCenter)
        buttons.accepted.connect(self.new_accept)
        buttons.rejected.connect(self.new_reject)
        layout.addWidget(QLabel("Do you want to choose the path for all the databases?"))
        layout.addWidget(buttons)

        self.setWindowTitle("Workspace")
        self.setWindowModality(Qt.ApplicationModal)

    def new_accept(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Pick the folder")
        self.accept()

    def new_reject(self):
        self.reject()


class MsgBoxCustom(QMessageBox):
    def __init__(self, icon, title, message, buttons):
        super(MsgBoxCustom, self).__init__(icon, title, message, buttons)
        self.setModal(True)


class MsgBoxWarning(MsgBoxCustom):
    def __init__(self, title, message):
        super(MsgBoxWarning, self).__init__(QMessageBox.Warning, title, message, QMessageBox.Ok)
        self.exec_()


class MsgBoxInfo(MsgBoxCustom):
    def __init__(self, title, message):
        super(MsgBoxInfo, self).__init__(QMessageBox.Information, title, message, QMessageBox.Ok)
        self.exec_()


class MsgBoxQuestion(MsgBoxCustom):
    def __init__(self, title, message):
        super(MsgBoxQuestion, self).__init__(QMessageBox.Question, title, message, QMessageBox.Yes | QMessageBox.No)

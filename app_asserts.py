import os
import sys
import traceback
import ConfigParser as cfg
from PyQt4 import QtGui, QtCore, uic
from functools import partial
from collections import defaultdict
import database_utils as dbu
import exports_imports as exp_imp

import dialogs

qtMainWindow = "window.ui"
qtNewDatabase = "new_database.ui"
qtNewTable = "new_table.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtMainWindow)
form_1, base_1 = uic.loadUiType(qtNewDatabase)
form_2, base_2 = uic.loadUiType(qtNewTable)

FIELD_NAME = 0
FIELD_TYPE = 1


def override(fnc):
    return fnc


class ResetWorkspaceException(Exception):
    pass


class QStandardItemUneditable(QtGui.QStandardItem):
    def __init__(self, *args):
        super(QStandardItemUneditable, self).__init__(*args)
        self.setEditable(False)


class QTableWidgetItemUneditable(QtGui.QTableWidgetItem):
    def __init__(self, *args):
        super(QTableWidgetItemUneditable, self).__init__(*args)
        self.setFlags(self.flags() ^ QtCore.Qt.ItemIsEditable)


class NewDatabase(base_1, form_1):
    def __init__(self):
        super(base_1, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Create new database")

        self.new_database_name = None

        self.textEdit.setFocus(QtCore.Qt.OtherFocusReason)
        self.buttonBox.clicked.connect(self.submit)

    def submit(self):
        self.new_database_name = self.textEdit.text()


class NewTable(base_2, form_2):
    def __init__(self, title):
        assert isinstance(title, str), 'Title argument must be str!'

        super(base_2, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("New table for %s's database" % (title))

        self.new_table_name = None
        self.combo_boxes = []
        self.combo_boxes_changed = [False] * 10
        self.text_edits_name = []
        # self.text_edits_value = []

        # self.buttonBox.accepted.connect(self.accept)
        # self.buttonBox.rejected.connect(self.reject)

        self.field_types = ["int", "float", "str"]
        self.addItems()

    def addItems(self):
        self.gridLayoutTable.setSpacing(10)
        label = QtGui.QLabel("Table name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.gridLayoutTable.addWidget(label, 0, 0, alignment=QtCore.Qt.AlignCenter)
        self.table_name = QtGui.QLineEdit()
        self.gridLayoutTable.addWidget(self.table_name, 0, 1, 1, 2)
        label = QtGui.QLabel("Field no.")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.gridLayoutTable.addWidget(label, 1, 0, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.gridLayoutTable.addWidget(label, 1, 1, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field type")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.gridLayoutTable.addWidget(label, 1, 2, alignment=QtCore.Qt.AlignCenter)
        # label = QtGui.QLabel("Field value")
        # label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        # self.gridLayoutTable.addWidget(label, 1, 3, alignment=QtCore.Qt.AlignCenter)

        for i in range(10):
            self.addLineField(i)

        self.table_name.setFocus(QtCore.Qt.OtherFocusReason)

    def addLineField(self, i):
        assert i <= len(self.combo_boxes_changed)

        label = QtGui.QLabel("#" + str(i + 1))
        combo_box = QtGui.QComboBox()
        combo_box.addItems(self.field_types)
        combo_box.setCurrentIndex(-1)
        combo_box.currentIndexChanged.connect(partial(self.combo_box_changed, i))
        text_edit_name = QtGui.QLineEdit()
        # text_edit_value = QtGui.QLineEdit()

        self.gridLayoutTable.addWidget(label, (i + 2), 0, alignment=QtCore.Qt.AlignCenter)
        self.gridLayoutTable.addWidget(text_edit_name, (i + 2), 1)
        self.gridLayoutTable.addWidget(combo_box, (i + 2), 2)
        # self.gridLayoutTable.addWidget(text_edit_value, (i + 2), 3)

        self.combo_boxes.append(combo_box)
        self.text_edits_name.append(text_edit_name)
        # self.text_edits_value.append(text_edit_value)

    def combo_box_changed(self, id):
        if not self.combo_boxes_changed[id]:
            self.combo_boxes_changed[id] = True
            if all(self.combo_boxes_changed):
                self.addLineField(len(self.combo_boxes_changed))
                self.combo_boxes_changed.append(False)

    @override
    def accept(self):
        self.new_table_name = self.table_name.displayText()
        if not len(self.new_table_name):
            dialogs.MsgBoxWarning("Warning", "Please complete the table's name field!")
        else:
            if not any(self.combo_boxes_changed):
                dialogs.MsgBoxWarning("Warning", "No fields selected!")
            else:
                for (idx, value) in enumerate(self.combo_boxes_changed):
                    if value and not len(self.text_edits_name[idx].text()) or \
                       len(self.text_edits_name[idx].text()) and not value:
                        dialogs.MsgBoxWarning("Warning", "Field %d is not fully completed!" % (idx + 1))
                        return

                super(NewTable, self).accept()


class InsertRow(QtGui.QDialog):
    def __init__(self, table_name, database_name, parent=None):
        assert isinstance(table_name, str) and \
            isinstance(database_name, str) and \
            isinstance(parent, QtCore.QObject) or isinstance(parent, type(None))

        super(InsertRow, self).__init__(parent)
        self.table_name = table_name
        self.database_name = database_name
        self.setWindowTitle("Insert row")

        self.text_edits_value = []

        self.layout = QtGui.QGridLayout(self)
        self.layout.setSpacing(10)
        self.addItems()

    def addLineField(self, i):
        label = QtGui.QLabel("#" + str(i + 1))
        combo_box_type = QtGui.QComboBox()
        combo_box_type.addItems([self.schema[i][FIELD_TYPE]])
        combo_box_type.setDisabled(True)
        # combo_box_type.setCurrentIndex(-1)
        # combo_box_type.currentIndexChanged.connect(partial(self.combo_box_changed, i))
        text_edit_name = QtGui.QLineEdit()
        text_edit_name.setText(self.schema[i][FIELD_NAME])
        text_edit_name.setDisabled(True)

        text_edit_value = QtGui.QLineEdit()
        text_edit_value.setText("")

        self.layout.addWidget(label, (i + 2), 0, alignment=QtCore.Qt.AlignCenter)
        self.layout.addWidget(text_edit_name, (i + 2), 1)
        self.layout.addWidget(combo_box_type, (i + 2), 2)
        self.layout.addWidget(text_edit_value, (i + 2), 3)

        self.text_edits_value.append(text_edit_value)

    def addItems(self):
        label = QtGui.QLabel("Inserting row in table '%s' from database '%s'" % (self.table_name, self.database_name), alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 10)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 15)
        self.layout.addWidget(label, 0, 0, 1, 4, alignment=QtCore.Qt.AlignCenter)
        # self.layout.setRowStretch(0, 1)

        label = QtGui.QLabel("Field no.")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 0, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 1, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field type")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 2, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field value")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 3, alignment=QtCore.Qt.AlignCenter)

        self.schema = dbu.get_schema(self.database_name, self.table_name)
        no_of_fields = len(self.schema)
        for i in range(no_of_fields):
            self.addLineField(i)

        self.buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons, self.layout.count(), 1, 1, 3, alignment=QtCore.Qt.AlignCenter)
        self.buttons.setFocus()

    def accept(self):
        if not any(self.text_edits_value):
            dialogs.MsgBoxWarning("Warning", "No fields completed!")
        else:
            # TODO: Insert physical row
            super(self.__class__, self).accept()

    def reject(self):
        super(self.__class__, self).reject()


class UpdateRows(QtGui.QDialog):
    def __init__(self, table_name, database_name, parent=None):
        assert isinstance(table_name, str) and \
            isinstance(database_name, str) and \
            isinstance(parent, QtCore.QObject) or isinstance(parent, type(None))

        super(UpdateRows, self).__init__(parent)
        self.table_name = table_name
        self.database_name = database_name
        self.setWindowTitle("Update rows")

        self.criteria = defaultdict(int)
        self.field_types = ["int", "float", "str"]
        self.operators = {"int": ["==", "!=", "<", ">", "<=", ">="],
                          "float": ["==", "!=", "<", ">", "<=", ">="],
                          "str": ["==", "!="]}

        self.text_edits_update_value = []

        self.layout = QtGui.QGridLayout(self)
        self.layout.setSpacing(10)
        self.addItems()

    def addLineField(self, i):
        label = QtGui.QLabel("#" + str(i + 1))
        combo_box_type = QtGui.QComboBox()
        combo_box_type.addItems([self.fields[i]])
        combo_box_type.setDisabled(True)
        # combo_box_type.setCurrentIndex(-1)
        # combo_box_type.currentIndexChanged.connect(partial(self.combo_box_changed, i))
        text_edit_name = QtGui.QLineEdit()
        text_edit_name.setText(self.names[i])
        text_edit_name.setDisabled(True)

        text_edit_value = QtGui.QLineEdit()
        # text_edit_value.setText("Value")

        self.layout.addWidget(label, (i + 2), 0, alignment=QtCore.Qt.AlignCenter)
        self.layout.addWidget(text_edit_name, (i + 2), 1)
        self.layout.addWidget(combo_box_type, (i + 2), 2)
        self.layout.addWidget(text_edit_value, (i + 2), 3)

        self.text_edits_update_value.append(text_edit_value)

    def combo_box_changed(self, id):
        field_name = str(self.criteria[id]["name"].currentText())
        field_type = self.fields[self.names.index(field_name)]

        self.criteria[id]["type"].setCurrentIndex(self.field_types.index(field_type))

        self.criteria[id]["comparison"].setDisabled(False)
        self.criteria[id]["comparison"].clear()
        self.criteria[id]["comparison"].addItems(self.operators[field_type])

    def addWhereField(self, i):
        idx = i
        i += self.no_of_fields + 1

        label = QtGui.QLabel("#" + str(i - self.no_of_fields))
        combo_box_name = QtGui.QComboBox()
        combo_box_name.addItems(self.names)
        combo_box_name.setCurrentIndex(-1)

        combo_box_type = QtGui.QComboBox()
        combo_box_type.addItems(self.field_types)
        combo_box_type.setCurrentIndex(-1)
        combo_box_type.setDisabled(True)

        combo_box_comparison = QtGui.QComboBox()
        combo_box_comparison.setDisabled(True)

        text_edit_compare_value = QtGui.QLineEdit()

        self.layout.addWidget(label, (i + 2), 0, alignment=QtCore.Qt.AlignCenter)
        self.layout.addWidget(combo_box_name, (i + 2), 1)
        self.layout.addWidget(combo_box_type, (i + 2), 2)
        self.layout.addWidget(combo_box_comparison, (i + 2), 3)
        self.layout.addWidget(text_edit_compare_value, (i + 2), 4)

        self.last_add_button_idx = idx + 1
        if idx == 0:
            self.last_add_button = QtGui.QPushButton(QtGui.QIcon(":ico/insert_table.ico"), "")
            self.last_add_button.clicked.connect(lambda: self.addWhereField(self.last_add_button_idx))
            self.layout.addWidget(self.last_add_button, (i + 2), 5)

        self.criteria[idx] = {"name": combo_box_name,
                              "type": combo_box_type,
                              "comparison": combo_box_comparison,
                              "compare_value": text_edit_compare_value}

        combo_box_name.currentIndexChanged.connect(partial(self.combo_box_changed, idx))

    def addItems(self):
        label = QtGui.QLabel("Updating rows from table '%s' from database '%s'" % (self.table_name, self.database_name), alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 10)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 15)
        self.layout.addWidget(label, 0, 0, 1, 5, alignment=QtCore.Qt.AlignCenter)
        # self.layout.setRowStretch(0, 1)

        label = QtGui.QLabel("Field no.")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 0, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 1, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field type")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 2, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field value")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 3, alignment=QtCore.Qt.AlignCenter)

        schema = dbu.get_schema(self.database_name, self.table_name)
        self.names = [i[0] for i in schema]
        self.fields = [i[1] for i in schema]
        assert len(self.names) == len(self.fields), "Number of names (%r) is different than the number of fields (%r)" % (len(self.names), len(self.fields))

        self.no_of_fields = len(self.names)
        for i in range(self.no_of_fields):
            self.addLineField(i)

        label = QtGui.QLabel("Field no.")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, self.no_of_fields + 2, 0, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, self.no_of_fields + 2, 1, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field type")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, self.no_of_fields + 2, 2, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field comparation operator")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, self.no_of_fields + 2, 3, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field value to compare")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, self.no_of_fields + 2, 4, alignment=QtCore.Qt.AlignCenter)

        self.addWhereField(0)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons, self.layout.count(), 1, 1, 3, alignment=QtCore.Qt.AlignCenter)
        buttons.setFocus()

    def accept(self):
        for value in (self.criteria.values()):
            if len(value["compare_value"].text()) and not value["name"].currentIndex() != -1 or \
               value["name"].currentIndex() != -1 and not len(value["compare_value"].text()) or \
               value["name"].currentIndex() == -1 and not len(value["compare_value"].text()):
                dialogs.MsgBoxWarning("Warning", "No fields selected!")
                return

        if not any(len(str(i.text())) for i in self.text_edits_update_value):
            dialogs.MsgBoxWarning("Warning", "No updating values completed!")
        else:
            super(self.__class__, self).accept()

    def reject(self):
        super(self.__class__, self).reject()


class DeleteRows(QtGui.QDialog):
    def __init__(self, table_name, database_name, parent=None):
        assert isinstance(table_name, str) and \
            isinstance(database_name, str) and \
            isinstance(parent, QtCore.QObject) or isinstance(parent, type(None))

        super(DeleteRows, self).__init__(parent)
        self.table_name = table_name
        self.database_name = database_name
        self.setWindowTitle("Delete rows")

        self.criteria = defaultdict(int)
        self.field_types = ["int", "float", "str"]
        self.operators = {"int": ["==", "!=", "<", ">", "<=", ">="],
                          "float": ["==", "!=", "<", ">", "<=", ">="],
                          "str": ["==", "!="]}

        self.layout = QtGui.QGridLayout(self)
        self.layout.setSpacing(10)
        self.addItems()

    def combo_box_changed(self, id):
        field_name = str(self.criteria[id]["name"].currentText())
        field_type = self.fields[self.names.index(field_name)]

        self.criteria[id]["type"].setCurrentIndex(self.field_types.index(field_type))

        self.criteria[id]["comparison"].setDisabled(False)
        self.criteria[id]["comparison"].clear()
        self.criteria[id]["comparison"].addItems(self.operators[field_type])

    def addWhereField(self, i):
        label = QtGui.QLabel("#" + str(i + 1))
        combo_box_name = QtGui.QComboBox()
        combo_box_name.addItems(self.names)
        combo_box_name.setCurrentIndex(-1)

        combo_box_type = QtGui.QComboBox()
        combo_box_type.addItems(self.field_types)
        combo_box_type.setCurrentIndex(-1)
        combo_box_type.setDisabled(True)

        combo_box_comparison = QtGui.QComboBox()
        combo_box_comparison.setDisabled(True)

        text_edit_compare_value = QtGui.QLineEdit()

        self.layout.addWidget(label, (i + 2), 0, alignment=QtCore.Qt.AlignCenter)
        self.layout.addWidget(combo_box_name, (i + 2), 1)
        self.layout.addWidget(combo_box_type, (i + 2), 2)
        self.layout.addWidget(combo_box_comparison, (i + 2), 3)
        self.layout.addWidget(text_edit_compare_value, (i + 2), 4)

        self.last_add_button_idx = i + 1
        if i == 0:
            self.last_add_button = QtGui.QPushButton(QtGui.QIcon(":ico/insert_table.ico"), "")
            self.last_add_button.clicked.connect(lambda: self.addWhereField(self.last_add_button_idx))
            self.layout.addWidget(self.last_add_button, (i + 2), 5)

        self.criteria[i] = {"name": combo_box_name,
                            "type": combo_box_type,
                            "comparison": combo_box_comparison,
                            "compare_value": text_edit_compare_value}

        combo_box_name.currentIndexChanged.connect(partial(self.combo_box_changed, i))

    def addItems(self):
        label = QtGui.QLabel("Deleting rows from table '%s' from database '%s'" % (self.table_name, self.database_name), alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 10)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 15)
        self.layout.addWidget(label, 0, 0, 1, 5, alignment=QtCore.Qt.AlignCenter)

        label = QtGui.QLabel("Field no.")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 0, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 1, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field type")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 2, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field comparation operator")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 3, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field value to compare")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 4, alignment=QtCore.Qt.AlignCenter)

        schema = dbu.get_schema(self.database_name, self.table_name)
        self.names = [i[0] for i in schema]
        self.fields = [i[1] for i in schema]
        assert len(self.names) == len(self.fields), "Number of names (%r) is different than the number of fields (%r)" % (len(self.names), len(self.fields))

        self.addWhereField(0)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons, self.layout.count(), 1, 1, 3, alignment=QtCore.Qt.AlignCenter)
        buttons.setFocus()

    def accept(self):
        for value in (self.criteria.values()):
            if len(value["compare_value"].text()) and not value["name"].currentIndex() != -1 or \
               value["name"].currentIndex() != -1 and not len(value["compare_value"].text()) or \
               value["name"].currentIndex() == -1 and not len(value["compare_value"].text()):
                dialogs.MsgBoxWarning("Warning", "No fields selected!")
                return

        super(self.__class__, self).accept()

    def reject(self):
        super(self.__class__, self).reject()


class ModifyTable(QtGui.QDialog):
    def __init__(self, table_name, database_name, parent=None):
        assert isinstance(table_name, str) and \
            isinstance(database_name, str) and \
            isinstance(parent, QtCore.QObject) or isinstance(parent, type(None))

        super(ModifyTable, self).__init__(parent)
        self.table_name = table_name
        self.database_name = database_name
        self.setWindowTitle("Modify table")

        self.deleted = []
        self.new_columns = []

        self.text_edits_name = []
        self.old_text_edits_name = []  # TODO: for delete

        # self.text_edits_value = []
        self.combo_boxes = []
        self.combo_boxes_changed = None
        self.delete_buttons = []
        self.field_types = ["int", "float", "str"]

        self.layout = QtGui.QGridLayout(self)
        self.layout.setSpacing(10)
        self.addItems()

    def combo_box_changed(self, id):
        if not self.combo_boxes_changed[id]:
            self.combo_boxes_changed[id] = True
            if False not in self.combo_boxes_changed:
                try:
                    free_index = next(i for (i, v) in enumerate(self.combo_boxes_changed) if not v)
                    self.combo_boxes_changed[free_index] = False
                    self.addLineField(free_index, should_append=False)
                except StopIteration:
                    free_index = len(self.combo_boxes_changed)
                    self.combo_boxes_changed.append(False)
                    self.addLineField(free_index)

    def deleteWidget(self, id, iterable):
        assert isinstance(id, int) and \
            id >= 0 and id < len(iterable)

        self.layout.removeWidget(iterable[id])
        iterable[id].deleteLater()  # remove all references
        iterable[id] = None

    def delete_button_pressed(self, id):
        if id < len(self.schema):
            self.deleted.append(self.schema[id][FIELD_NAME])

        if self.combo_boxes_changed[id] and len(self.combo_boxes_changed) > 1:
            self.combo_boxes_changed[id] = None

            self.deleteWidget(id, self.delete_buttons)
            self.deleteWidget(id, self.text_edits_name)
            self.deleteWidget(id, self.combo_boxes)
            # self.deleteWidget(id, self.text_edits_value)

    def addLineField(self, i, init=False, should_append=True):
        delete_button = QtGui.QPushButton(QtGui.QIcon(":ico/delete_table.ico"), "#%d" % (i + 1))
        # delete_button.clicked.connect(partial(self.delete_button_pressed, i))

        combo_box = QtGui.QComboBox()
        text_edit_name = QtGui.QLineEdit()
        if init:
            self.combo_boxes_changed[i] = True
            combo_box.addItems([self.schema[i][FIELD_TYPE]])
            combo_box.setEditable(False)

            text_edit_name.setText(self.schema[i][FIELD_NAME])
            self.old_text_edits_name.append(str(text_edit_name.text()))
        else:
            combo_box.addItems(self.field_types)
            combo_box.setCurrentIndex(-1)
            self.new_columns.append(combo_box)

        combo_box.currentIndexChanged.connect(partial(self.combo_box_changed, i))
        # text_edit_value = QtGui.QLineEdit()
        # text_edit_value.setText("")

        self.layout.addWidget(delete_button, (i + 2), 0, alignment=QtCore.Qt.AlignCenter)
        self.layout.addWidget(text_edit_name, (i + 2), 1)
        self.layout.addWidget(combo_box, (i + 2), 2)
        # self.layout.addWidget(text_edit_value, (i + 2), 3)

        if should_append:
            self.delete_buttons.append(delete_button)
            self.text_edits_name.append(text_edit_name)
            self.combo_boxes.append(combo_box)
            # self.text_edits_value.append(text_edit_value)
        else:
            self.delete_buttons[i] = delete_button
            self.text_edits_name[i] = text_edit_name
            self.combo_boxes[i] = combo_box
            # self.text_edits_value[i] = text_edit_value

    def addItems(self):
        label = QtGui.QLabel("Modifying table '%s' from database '%s'" % (self.table_name, self.database_name), alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 10)
        # font.setUnderline(True)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 15)
        self.layout.addWidget(label, 0, 0, 1, 3, alignment=QtCore.Qt.AlignCenter)
        # self.layout.setRowStretch(0, 1)

        label = QtGui.QLabel("Field no.")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 0, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 1, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field type")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 1, 2, alignment=QtCore.Qt.AlignCenter)
        # label = QtGui.QLabel("Field value")
        # label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        # self.layout.addWidget(label, 1, 3, alignment=QtCore.Qt.AlignCenter)

        self.schema = dbu.get_schema(self.database_name, self.table_name)
        no_of_fields = len(self.schema)
        assert no_of_fields > 0, 'no_of_fields for database %s and table %s is 0' % (self.database_name, self.table_name)

        self.combo_boxes_changed = [False] * no_of_fields

        for i in range(no_of_fields):
            self.addLineField(i, init=True)

        if all(self.combo_boxes_changed):
            self.addLineField(len(self.combo_boxes_changed))
            self.combo_boxes_changed.append(False)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons, self.layout.count(), 1, alignment=QtCore.Qt.AlignCenter)
        buttons.setFocus()

    def accept(self):
        if not any(self.combo_boxes_changed):
            dialogs.MsgBoxWarning("Warning", "No fields selected!")
        else:
            for (idx, value) in enumerate(self.combo_boxes_changed):
                if value and not len(self.text_edits_name[idx].text()) or \
                   len(self.text_edits_name[idx].text()) and not value:
                    dialogs.MsgBoxWarning("Warning", "Field %d does not contain a name!" % (idx + 1))
                    return

        super(ModifyTable, self).accept()

    def reject(self):
        super(ModifyTable, self).reject()


class ImportTable(QtGui.QDialog):
    def __init__(self, table_name, database_name, workspace_dir, parent=None):
        assert isinstance(table_name, str) and \
            isinstance(database_name, str) and \
            isinstance(workspace_dir, str) and \
            isinstance(parent, QtCore.QObject) or isinstance(parent, type(None))

        super(ImportTable, self).__init__(parent)
        self.table_name = table_name
        self.database_name = database_name
        self.workspace_dir = workspace_dir
        self.import_table_file = None
        self.setWindowTitle("Import table")

        self.layout = QtGui.QGridLayout(self)
        self.layout.setSpacing(10)
        self.addItems()

    def select_button_clicked(self):
        self.import_table_file = QtGui.QFileDialog.getOpenFileName(self, "Pick the import table", self.workspace_dir, "XML (*.xml);;CSV (*.csv);;Plain (*.txt)")

    def addItems(self):
        label = QtGui.QLabel("<b>Select import table<b>", alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 8)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 5)
        self.layout.addWidget(label, 0, 1, 1, 4, alignment=QtCore.Qt.AlignCenter)

        self.select_button = QtGui.QPushButton("Select")
        self.select_button.clicked.connect(self.select_button_clicked)
        self.layout.addWidget(self.select_button, 1, 1, 1, 3, alignment=QtCore.Qt.AlignCenter)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons, self.layout.count(), 1, 1, 3, alignment=QtCore.Qt.AlignCenter)
        buttons.setFocus()

    def accept(self):
        if not self.import_table_file:
            dialogs.MsgBoxWarning("Warning", "No import table selected!")
            return

        super(self.__class__, self).accept()

    def reject(self):
        super(self.__class__, self).reject()


class ExportTable(QtGui.QDialog):
    def __init__(self, table_name, database_name, parent=None):
        assert isinstance(table_name, str) and \
            isinstance(database_name, str) and \
            isinstance(parent, QtCore.QObject) or isinstance(parent, type(None))

        super(ExportTable, self).__init__(parent)
        self.table_name = table_name
        self.database_name = database_name
        self.setWindowTitle("Export table")

        self.layout = QtGui.QGridLayout(self)
        self.layout.setSpacing(10)
        self.addItems()

    def addItems(self):
        label = QtGui.QLabel("<b>Select export method<b>", alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 8)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 5)
        self.layout.addWidget(label, 0, 1, 1, 4, alignment=QtCore.Qt.AlignCenter)

        self.combo_box = QtGui.QComboBox()
        self.combo_box.addItems(["plain", "xml", "csv"])
        self.combo_box.setCurrentIndex(-1)
        self.layout.addWidget(self.combo_box, 1, 1, 1, 3, alignment=QtCore.Qt.AlignCenter)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons, self.layout.count(), 1, 1, 3, alignment=QtCore.Qt.AlignCenter)
        buttons.setFocus()

    def accept(self):
        if self.combo_box.currentIndex() == -1:
            dialogs.MsgBoxWarning("Warning", "No export method selected!")
            return

        super(self.__class__, self).accept()

    def reject(self):
        super(self.__class__, self).reject()


class SelectRows(QtGui.QDialog):
    def __init__(self, table_name, database_name, parent=None):
        assert isinstance(table_name, str) and \
            isinstance(database_name, str) and \
            isinstance(parent, QtCore.QObject) or isinstance(parent, type(None))

        super(SelectRows, self).__init__(parent)
        self.table_name = table_name
        self.database_name = database_name
        self.setWindowTitle("Select rows")

        self.criteria = defaultdict(int)
        self.field_types = ["int", "float", "str"]
        self.operators = {"int": ["==", "!=", "<", ">", "<=", ">="],
                          "float": ["==", "!=", "<", ">", "<=", ">="],
                          "str": ["==", "!="]}

        self.layout = QtGui.QGridLayout(self)
        self.layout.setSpacing(10)
        self.addItems()

    def combo_box_changed(self, id):
        field_name = str(self.criteria[id]["name"].currentText())
        field_type = self.fields[self.names.index(field_name)]

        self.criteria[id]["type"].setCurrentIndex(self.field_types.index(field_type))

        self.criteria[id]["comparison"].setDisabled(False)
        self.criteria[id]["comparison"].clear()
        self.criteria[id]["comparison"].addItems(self.operators[field_type])

    def addWhereField(self, i):
        idx = i
        i += 3

        label = QtGui.QLabel("#" + str(idx + 1))
        combo_box_name = QtGui.QComboBox()
        combo_box_name.addItems(self.names)
        combo_box_name.setCurrentIndex(-1)

        combo_box_type = QtGui.QComboBox()
        combo_box_type.addItems(self.field_types)
        combo_box_type.setCurrentIndex(-1)
        combo_box_type.setDisabled(True)

        combo_box_comparison = QtGui.QComboBox()
        combo_box_comparison.setDisabled(True)
        # combo_box_comparison.addItems(self.operators[self.field_types[0]])

        text_edit_compare_value = QtGui.QLineEdit()

        self.layout.addWidget(label, (i + 2), 0, alignment=QtCore.Qt.AlignCenter)
        self.layout.addWidget(combo_box_name, (i + 2), 1)
        self.layout.addWidget(combo_box_type, (i + 2), 2)
        self.layout.addWidget(combo_box_comparison, (i + 2), 3)
        self.layout.addWidget(text_edit_compare_value, (i + 2), 4)

        self.last_add_button_idx = idx + 1
        if idx == 0:
            self.last_add_button = QtGui.QPushButton(QtGui.QIcon(":ico/insert_table.ico"), "")
            self.last_add_button.clicked.connect(lambda: self.addWhereField(self.last_add_button_idx))
            self.layout.addWidget(self.last_add_button, (i + 2), 5)

        self.criteria[idx] = {"name": combo_box_name,
                              "type": combo_box_type,
                              "comparison": combo_box_comparison,
                              "compare_value": text_edit_compare_value}

        combo_box_name.currentIndexChanged.connect(partial(self.combo_box_changed, idx))

    def addItems(self):
        label = QtGui.QLabel("Selecting rows from table '%s' from database '%s'" % (self.table_name, self.database_name), alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 10)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 15)
        self.layout.addWidget(label, 0, 0, 1, 5, alignment=QtCore.Qt.AlignCenter)

        label = QtGui.QLabel("<b>Select the fields<b>", alignment=QtCore.Qt.AlignCenter)
        font = QtGui.QFont("MS Shell Dlg", 8)
        label.setFont(font)
        label.setContentsMargins(0, 0, 0, 5)
        self.layout.addWidget(label, 1, 1, 1, 4, alignment=QtCore.Qt.AlignCenter)

        # TODO: Get field names
        self.list = QtGui.QListWidget()
        self.list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        schema = dbu.get_schema(self.database_name, self.table_name)
        self.names = [i[0] for i in schema]
        self.fields = [i[1] for i in schema]
        assert len(self.names) == len(self.fields), "Number of names (%r) is different than the number of fields (%r)" % (len(self.names), len(self.fields))

        self.list.addItems(self.names)
        self.list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list.setFixedSize(self.list.sizeHintForColumn(0) + 2 * self.list.frameWidth() + 100, self.list.sizeHintForRow(0) * self.list.count() + 2 * self.list.frameWidth())
        self.layout.addWidget(self.list, 2, 1, 2, 4, alignment=QtCore.Qt.AlignCenter)

        label = QtGui.QLabel("Field no.")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 4, 0, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field name")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 4, 1, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field type")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 4, 2, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field comparation operator")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 4, 3, alignment=QtCore.Qt.AlignCenter)
        label = QtGui.QLabel("Field value to compare")
        label.setFont(QtGui.QFont("MS Shell Dlg", 9, QtGui.QFont.Bold))
        self.layout.addWidget(label, 4, 4, alignment=QtCore.Qt.AlignCenter)

        self.addWhereField(0)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons, self.layout.count(), 1, 1, 3, alignment=QtCore.Qt.AlignCenter)
        buttons.setFocus()

    def accept(self):
        for value in (self.criteria.values()):
            if len(value["compare_value"].text()) and not value["name"].currentIndex() != -1 or \
               value["name"].currentIndex() != -1 and not len(value["compare_value"].text()):
                dialogs.MsgBoxWarning("Warning", "No fields selected!")
                return

        # TODO: Insert physical row
        super(self.__class__, self).accept()

    def reject(self):
        super(self.__class__, self).reject()


class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        self.setupUi(self)
        self.initUi()

        self.databases_dir = None
        self.checkDatabasesDirectory(False)

        # self.last_table_selected = None

    def checkDatabasesDirectory(self, reset=True):
        databases_dir = self.dialogChooseDatabasesDirectory(reset)
        if isinstance(databases_dir, QtCore.QString):
            databases_dir = str(databases_dir)

        self.populate_tree(databases_dir)

    def populate_tree(self, databases_dir):
        self.treeModel = QtGui.QStandardItemModel()
        rootNode = self.treeModel.invisibleRootItem()

        if not databases_dir:
            first_branch = QStandardItemUneditable(QtGui.QIcon(":ico/no_workspace.ico"), "Workspace unavailable")
            rootNode.appendRow([first_branch, None])
        else:
            self.databases_dir = databases_dir
            dbu.set_root_location(self.databases_dir)
            exp_imp.set_root_location(self.databases_dir)

            at_least_one_db = False
            if os.path.isdir(databases_dir):
                for d in os.listdir(databases_dir):
                    dir_path = os.path.join(databases_dir, d)
                    if not os.path.isdir(dir_path):
                        continue

                    branch = QStandardItemUneditable(QtGui.QIcon(":ico/database_item_tree.ico"), d)
                    for f in os.listdir(dir_path):
                        file_path = os.path.join(dir_path, f)
                        if not os.path.isfile(file_path) or file_path.endswith("_schema"):
                            continue

                        leaf = QStandardItemUneditable(QtGui.QIcon(":ico/table_item_tree.ico"), f)
                        branch.appendRow([leaf, None])
                    rootNode.appendRow([branch, None])
                    at_least_one_db = True

            if not at_least_one_db:
                first_branch = QStandardItemUneditable(QtGui.QIcon(":ico/no_workspace.ico"), "No databases found")
                rootNode.appendRow([first_branch, None])

        self.treeModel.setColumnCount(1)
        self.treeView.setModel(self.treeModel)
        QtCore.QObject.connect(self.treeView.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.onClickItem)

    def updateTableWidget(self, all_data, field_names):
        self.tableWidget.clear()
        self.tableWidget.setRowCount(len(all_data))
        self.tableWidget.setColumnCount(len(field_names))
        for idx, value in enumerate(field_names):
            self.tableWidget.setHorizontalHeaderItem(idx, QTableWidgetItemUneditable(value))

        for i in range(len(all_data)):
            for j in range(len(field_names)):
                try:
                    self.tableWidget.setItem(i, j, QTableWidgetItemUneditable(all_data[i][j]))
                except IndexError:
                    self.tableWidget.setItem(i, j, QTableWidgetItemUneditable(""))

    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def onClickItem(self, selected, deselected):
        if len(selected.indexes()) == 2:  # Table
            table_name = str(selected.indexes()[0].data().toPyObject())
            database_name = str(selected.indexes()[0].parent().data().toPyObject())
            # self.last_table_selected = table_name

            schema = dbu.get_schema(database_name, table_name)
            names = [i[0] for i in schema]
            assert len(names) > 0, 'No of names for database %s and table %s is 0' % (database_name, table_name)
            # fields = [i[1] for i in schema]

            all_data = dbu.select_in_table(database_name, table_name, names)
            self.updateTableWidget(all_data, names)
        else:  # Database
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)

        # print selected.count()
        # print selected.indexes()[1].data().toPyObject()
        # item = self.treeView.selectedIndexes()[0]
        # print item.model().itemFromIndex(index).text()

    def dialogChooseDatabasesDirectory(self, reset):
        config = cfg.ConfigParser()
        config.read("settings.ini")

        databases_dir = None
        try:
            databases_dir = config.get("Settings", "DatabasesDirectory")
            if reset:
                raise ResetWorkspaceException
            return databases_dir
        except (cfg.NoOptionError, cfg.NoSectionError, ResetWorkspaceException):
            dialog = dialogs.SelectDialog()
            if dialog.exec_():
                if dialog.directory:
                    if "Settings" not in config.sections():
                        config.add_section("Settings")

                    config.set("Settings", "DatabasesDirectory", dialog.directory)
                    with open("settings.ini", "w+") as f:
                        config.write(f)

                    return dialog.directory
            return databases_dir

    def createDatabase(self):
        if not self.databases_dir:
            return self.dialogChooseDatabasesDirectory(reset=False)
            # return dialogs.MsgBoxWarning("Warning", "No workspace defined!")

        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir
        new_db = NewDatabase()
        if new_db.exec_():
            try:
                db_name = str(new_db.new_database_name)
                dbu.create_database(db_name)
                dialogs.MsgBoxInfo("Informatiton", "Database %s has been created!" % (db_name))
                self.treeModel.appendRow(QStandardItemUneditable(QtGui.QIcon(":ico/database_item_tree.ico"), db_name))
            except Exception:
                dialogs.MsgBoxWarning("Warning", "Could not create database '%s'" % (db_name))
                traceback.print_exc()
            # TODO: Create physical database

    def deleteDatabase(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if not len(selected):
            return dialogs.MsgBoxWarning("Warning", "No database selected!")

        if len(selected) == 2:  # has children
            database_name = str(selected[0].parent().data().toPyObject())
            dialog = dialogs.MsgBoxQuestion("Delete database", "Are you sure you want to delete database '%s' and all its tables?" % (database_name))
            if dialog.exec_() == QtGui.QMessageBox.No:
                return
            self.treeModel.removeRow(selected[0].parent().row())

        elif len(selected) == 1:
            database_name = str(selected[0].data().toPyObject())
            self.treeModel.removeRow(selected[0].row())

        try:
            dbu.delete_database(database_name)
            dialogs.MsgBoxInfo("Info", "Database '%s' has been deleted!" % (database_name))
        except Exception:
            dialogs.MsgBoxWarning("Warning", "Could not delete database '%s'" % (database_name))
            traceback.print_exc()

    def createTable(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        database_name = None
        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            database = table.parent()
            branch = self.treeModel.item(database.row(), database.column())
            database_name = database.data().toPyObject()
        elif len(selected) == 1:
            database = selected[0]
            branch = self.treeModel.item(database.row(), database.column())
            database_name = database.data().toPyObject()
        else:
            return dialogs.MsgBoxWarning("Warning", "No database selected!")

        new_table = NewTable(str(database_name))
        if new_table.exec_():
            try:
                database_name = str(database_name)
                table_name = str(new_table.new_table_name)
                field_types = [str(i.currentText()) for i in new_table.combo_boxes if len(str(i.currentText()))]
                field_names = [str(i.text()) for i in new_table.text_edits_name if len(str(i.text()))]
                dbu.create_table(database_name, table_name, zip(field_names, field_types))

                leaf = QStandardItemUneditable(QtGui.QIcon(":ico/table_item_tree.ico"), table_name)
                branch.appendRow([leaf, None])

                dialogs.MsgBoxInfo("Informatiton", "Table '%s' has been created successfully in database '%s'!" % (table_name, database_name))
            except Exception:
                dialogs.MsgBoxWarning("Warning", "Could not create table %s in database '%s'" % (table_name, database_name))
                traceback.print_exc()

    def modifyTable(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            database = table.parent()
            table_name = str(table.data().toPyObject())
            database_name = str(database.data().toPyObject())
            modify_table = ModifyTable(table_name=table_name, database_name=database_name)

            if modify_table.exec_() == QtGui.QDialog.Accepted:
                old_names = modify_table.old_text_edits_name
                new_names = [str(i.text()) for i in modify_table.text_edits_name[:len(modify_table.schema)] if len(str(i.text()))]

                added_items_names = [str(i.text()) for i in modify_table.text_edits_name[len(modify_table.schema):] if len(str(i.text()))]
                added_items_types = [str(i.currentText()) for i in modify_table.combo_boxes[len(modify_table.schema):] if len(str(i.currentText()))]

                success = False
                if len(old_names):
                    try:
                        dbu.change_fields_in_table(database_name, table_name, zip(old_names, new_names))
                        success = True
                    except Exception:
                        dialogs.MsgBoxWarning("Warning", "Could not edit names for table %s from database '%s'" % (table_name, database_name))
                        traceback.print_exc()

                if len(added_items_names):
                    try:
                        dbu.add_column_to_table(database_name, table_name, zip(added_items_names, added_items_types))
                        success = True
                    except Exception:
                        dialogs.MsgBoxWarning("Warning", "Could not add new columns to table %s from database '%s'" % (table_name, database_name))
                        traceback.print_exc()

                if success:
                    names = [i[0] for i in dbu.get_schema(database_name, table_name)]
                    all_data = dbu.select_in_table(database_name, table_name, names, [])
                    self.updateTableWidget(all_data, names)

                # TODO: dbu.drop_column_in_table

        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def deleteTable(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            table_name = str(table.data().toPyObject())
            database_name = str(table.parent().data().toPyObject())

            dialog = dialogs.MsgBoxQuestion("Delete table %s" % (table_name), "Are you sure you want to delete table %s?" % (table_name))
            if dialog.exec_() == QtGui.QMessageBox.Yes:
                try:
                    dbu.delete_table(database_name, table_name)
                    self.treeModel.removeRows(table.row(), 1, parent=table.parent())
                except Exception:
                    dialogs.MsgBoxWarning("Warning", "Could not delete table '%s' from database '%s'" % (table_name, database_name))
                    traceback.print_exc()
        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def importTable(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            table_name = str(table.data().toPyObject())
            database_name = str(table.parent().data().toPyObject())

            import_table = ImportTable(table_name=table_name, database_name=database_name, workspace_dir=self.databases_dir)
            if import_table.exec_() == QtGui.QDialog.Accepted:
                try:
                    import_table.import_table_file = str(import_table.import_table_file)
                    if import_table.import_table_file.endswith(".txt"):
                        # export_type = "plain"
                        exp_imp.import_plain(database_name, table_name, import_table.import_table_file)
                    elif import_table.import_table_file.endswith(".xml"):
                        # export_type = "xml"
                        exp_imp.import_xml(database_name, table_name, import_table.import_table_file)
                    elif import_table.import_table_file.endswith(".csv"):
                        # export_type = "csv"
                        exp_imp.import_csv(database_name, table_name, import_table.import_table_file)

                    dialogs.MsgBoxInfo("Informatiton", "Data from '%s' has been imported in table '%s' from database '%s'" % (import_table.import_table_file, table_name, database_name))
                    names = [i[0] for i in dbu.get_schema(database_name, table_name)]
                    assert len(names) > 0, 'No of names for database %s and table %s is 0' % (database_name, table_name)

                    all_data = dbu.select_in_table(database_name, table_name, names, [])
                    self.updateTableWidget(all_data, names)
                except Exception:
                    dialogs.MsgBoxWarning("Warning", "Could not import data from '%s' in table '%s' from database '%s'" % (import_table.import_table_file, table_name, database_name))
                    traceback.print_exc()
        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def exportTable(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            table_name = str(table.data().toPyObject())
            database_name = str(table.parent().data().toPyObject())

            export_table = ExportTable(table_name=table_name, database_name=database_name)
            if export_table.exec_() == QtGui.QDialog.Accepted:
                export_type = ""
                try:
                    index = export_table.combo_box.currentIndex()
                    assert index >= 0 and index <= 2, "index is %d" % (index)

                    if index == 0:
                        export_type = "plain"
                        exp_imp.export_plain(database_name, table_name)
                    elif index == 1:
                        export_type = "xml"
                        exp_imp.export_xml(database_name, table_name)
                    elif index == 2:
                        export_type = "csv"
                        exp_imp.export_csv(database_name, table_name)

                    dialogs.MsgBoxInfo("Informatiton", "Table '%s' from database '%s' has been exported to type %s!" % (table_name, database_name, export_type))
                except Exception:
                    dialogs.MsgBoxWarning("Warning", "Could not export table '%s' from database '%s' to type %s" % (table_name, database_name, export_type))
                    traceback.print_exc()
        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def selectRows(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            database = table.parent()
            table_name = str(table.data().toPyObject())
            database_name = str(database.data().toPyObject())
            select_row = SelectRows(table_name=table_name, database_name=database_name)

            if select_row.exec_() == QtGui.QDialog.Accepted:
                field_names = []
                operators = []
                compare_values = []

                for value in select_row.criteria.values():
                    field_names.append(str(value["name"].currentText()))
                    operators.append(str(value["comparison"].currentText()))
                    if str(value["type"].currentText()) == "int":
                        compare_values.append(int(str(value["compare_value"].text())))
                    elif str(value["type"].currentText()) == "float":
                        compare_values.append(float(str(value["compare_value"].text())))
                    else:
                        compare_values.append((str(value["compare_value"].text())))

                if len(select_row.list.selectedItems()):  # If at least one column is selected
                    names_to_select = [str(i.text()) for i in select_row.list.selectedItems()]
                else:  # Otherwise, select all of them
                    names_to_select = [str(select_row.list.item(i).text()) for i in range(select_row.list.count())]

                where_list = zip(field_names, operators, compare_values) if len(field_names) and field_names[0] != '' else []
                all_data = dbu.select_in_table(database_name, table_name, names_to_select, where_list)
                self.updateTableWidget(all_data, names_to_select)
        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def insertRow(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            database = table.parent()
            table_name = str(table.data().toPyObject())
            database_name = str(database.data().toPyObject())
            insert_row = InsertRow(table_name=table_name, database_name=database_name)

            if insert_row.exec_() == QtGui.QDialog.Accepted:
                names = []
                values = []
                all_names = [i[FIELD_NAME] for i in insert_row.schema]
                for i, value in enumerate(insert_row.text_edits_value):
                    text = str(value.text())
                    if len(text):
                        names.append(insert_row.schema[i][FIELD_NAME])
                        if insert_row.schema[i][FIELD_TYPE] == 'float':
                            values.append(float(text))
                        elif insert_row.schema[i][FIELD_TYPE] == 'int':
                            values.append(int(text))
                        else:
                            values.append(text)

                if len(names):
                    dbu.insert_in_table(database_name, table_name, zip(names, values))
                    all_data = dbu.select_in_table(database_name, table_name, all_names, [])
                    self.updateTableWidget(all_data, all_names)
        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def updateRows(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            database = table.parent()
            table_name = str(table.data().toPyObject())
            database_name = str(database.data().toPyObject())
            update_rows = UpdateRows(table_name=table_name, database_name=database_name)

            if update_rows.exec_() == QtGui.QDialog.Accepted:
                field_names = []
                operators = []
                compare_values = []

                updated_names = []
                updated_values = []
                for i, value in enumerate(update_rows.text_edits_update_value):
                    text = str(value.text())
                    if len(text):
                        updated_names.append(update_rows.names[i])
                        if update_rows.fields[i] == "int":
                            updated_values.append(int(text))
                        elif update_rows.fields[i] == "float":
                            updated_values.append(float(text))
                        else:
                            updated_values.append(text)

                for value in update_rows.criteria.values():
                    field_names.append(str(value["name"].currentText()))
                    operators.append(str(value["comparison"].currentText()))
                    if str(value["type"].currentText()) == "int":
                        compare_values.append(int(str(value["compare_value"].text())))
                    elif str(value["type"].currentText()) == "float":
                        compare_values.append(float(str(value["compare_value"].text())))
                    else:
                        compare_values.append((str(value["compare_value"].text())))

                update_list = zip(updated_names, updated_values)
                where_list = zip(field_names, operators, compare_values) if len(field_names) and field_names[0] != '' else []
                dbu.update_in_table(database_name, table_name, update_list, where_list)

                all_data = dbu.select_in_table(database_name, table_name, update_rows.names, [])
                self.updateTableWidget(all_data, update_rows.names)
        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def deleteRows(self):
        assert os.path.isdir(self.databases_dir), '%s is not a directory' % self.databases_dir

        selected = self.treeView.selectedIndexes()
        if len(selected) == 2:
            table = selected[0]
            database = table.parent()
            table_name = str(table.data().toPyObject())
            database_name = str(database.data().toPyObject())
            delete_rows = DeleteRows(table_name=table_name, database_name=database_name)

            if delete_rows.exec_() == QtGui.QDialog.Accepted:
                field_names = []
                operators = []
                compare_values = []

                for value in delete_rows.criteria.values():
                    field_names.append(str(value["name"].currentText()))
                    operators.append(str(value["comparison"].currentText()))
                    if str(value["type"].currentText()) == "int":
                        compare_values.append(int(str(value["compare_value"].text())))
                    elif str(value["type"].currentText()) == "float":
                        compare_values.append(float(str(value["compare_value"].text())))
                    else:
                        compare_values.append((str(value["compare_value"].text())))

                where_list = zip(field_names, operators, compare_values) if len(field_names) and field_names[0] != '' else []
                dbu.delete_in_table(database_name, table_name, where_list)
                all_data = dbu.select_in_table(database_name, table_name, delete_rows.names, [])
                self.updateTableWidget(all_data, delete_rows.names)
        else:
            dialogs.MsgBoxWarning("Warning", "No table selected!")

    def initUi(self):
        self.treeView.setHeaderHidden(True)
        self.treeView.setColumnWidth(0, 150)
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.actionExit.setShortcut('CTRL+Q')
        self.actionExit.setStatusTip('Exit application')
        self.actionExit.triggered.connect(QtGui.qApp.quit)

        self.actionNew_Database.triggered.connect(self.createDatabase)
        self.actionDelete_Database.triggered.connect(self.deleteDatabase)

        self.pushButton_selectRows.clicked.connect(self.selectRows)
        self.pushButton_insertRow.clicked.connect(self.insertRow)
        self.pushButton_updateRows.clicked.connect(self.updateRows)
        self.pushButton_deleteRows.clicked.connect(self.deleteRows)

        self.actionCreate_Table.triggered.connect(self.createTable)
        self.actionModify_Table.triggered.connect(self.modifyTable)
        self.actionDelete_Table.triggered.connect(self.deleteTable)
        self.actionExport_Table.triggered.connect(self.exportTable)
        self.actionImport_Table.triggered.connect(self.importTable)

        self.actionWorkspace.triggered.connect(lambda: self.checkDatabasesDirectory(True))


def main():
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

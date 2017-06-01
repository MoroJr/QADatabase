import sys
import unittest
from PyQt4 import QtGui
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
import app
import random

a = QtGui.QApplication(sys.argv)


class AppTest(unittest.TestCase):
    def setUp(self):
        self.NewDatabase = app.NewDatabase()
        self.NewTable = app.NewTable("")
        self.MainApp = app.MyApp()

    def test_grid_layout(self):
        gridLayout = self.NewTable.gridLayoutTable
        old_count = gridLayout.count()
        widget = gridLayout.itemAt(0).widget()
        gridLayout.removeWidget(widget)
        self.assertNotEqual(old_count, gridLayout.count())

    def test_create_database(self):
        okWidget = self.NewDatabase.buttonBox.button(self.NewDatabase.buttonBox.Ok)
        self.assertEqual(self.NewDatabase.textEdit.text(), str())
        # self.NewDatabase.textEdit.setText("NewDatabase")
        QTest.keyClicks(self.NewDatabase.textEdit, "NewDatabase")
        QTest.mouseClick(okWidget, Qt.LeftButton)
        self.assertEqual(self.NewDatabase.textEdit.text(), "NewDatabase")

    def test_cancel_create_database(self):
        self.assertEqual(self.NewDatabase.textEdit.text(), str())
        cancelWidget = self.NewDatabase.buttonBox.button(self.NewDatabase.buttonBox.Cancel)
        old_row_count = self.MainApp.treeModel.rowCount()
        QTest.mouseClick(cancelWidget, Qt.LeftButton)
        self.assertEqual(self.NewDatabase.textEdit.text(), str())
        self.assertEqual(self.MainApp.treeModel.rowCount(), old_row_count)

    def test_modify_tree_model(self):
        tree = self.MainApp.treeModel
        old_row_count = tree.rowCount()
        item = QtGui.QStandardItem("new")
        tree.appendRow(item)
        self.assertNotEqual(old_row_count, tree.rowCount())
        old_row_count = tree.rowCount()
        tree.removeRow(old_row_count - 1)
        self.assertNotEqual(old_row_count, tree.rowCount())
        for i in range(tree.rowCount() + 1):
            tree.removeRow(0)
        self.assertEqual(tree.rowCount(), 0)

    def test_modify_table_widget(self):
        table = self.MainApp.tableWidget
        table.clear()
        table.setRowCount(2)
        table.setColumnCount(2)
        for i in range(table.rowCount()):
            for j in range(table.columnCount()):
                table.setItem(i, j, QtGui.QTableWidgetItem(str(i + j)))
        self.assertEqual(table.rowCount(), 2) and self.assertEqual(table.columnCount(), 2)
        table.clear()
        self.assertNotEqual(table.itemAt(0, 0), 0) and \
            self.assertNotEqual(table.rowCount(), 2) and \
            self.assertNotEqual(table.columnCount(), 2)

    def test_disabled_items(self):
        self.NewDatabase.textEdit.setDisabled(True)
        # self.NewDatabase.textEdit.setText("NewDatabase")
        QTest.keyClicks(self.NewDatabase.textEdit, "NewDatabase")
        self.assertNotEqual(self.NewDatabase.textEdit.text(), "NewDatabase")

    def test_new_table(self):
        okWidget = self.NewTable.buttonBox.button(self.NewTable.buttonBox.Ok)
        self.NewTable.table_name.setText("NewTable")

        for k in range(len(self.NewTable.field_types)):
            combos = self.NewTable.combo_boxes
            text_edits = self.NewTable.text_edits_name

            for j in range(len(self.NewTable.field_types)):
                old_text_edits = text_edits[:]
                for i in range(len(combos)):
                    d = {"int": random.randint(-1000, 1000),
                         "float": random.uniform(-10.0, 100.0),
                         "str": ["", "_test213"][random.randint(0, 1)]
                         }

                    combos[i].setCurrentIndex(j)
                    old_text_edits[i].setText(text_edits[i].text())
                    text_edits[i].setText(str(d[self.NewTable.field_types[k]]))

                QTest.mouseClick(okWidget, Qt.LeftButton)
                self.assertNotEqual(text_edits[i].text(), old_text_edits[i])

        self.assertEqual(self.NewTable.table_name.displayText(), "NewTable")


if __name__ == "__main__":
    unittest.main()

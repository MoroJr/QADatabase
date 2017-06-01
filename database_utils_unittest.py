import unittest
from database_utils import *


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        set_root_location(r'D:\db')

    def test_create_database(self):
        self.assertRaises(FileExistsError, create_database, "bazadate")

    def test_delete_database(self):
        self.assertRaises(FileNotFoundError, delete_database, "baza")

    def test_change_database1(self):
        self.assertRaises(FileExistsError, change_database, "bazadate", "bazadate")

    def test_change_database2(self):
        self.assertRaises(FileNotFoundError, change_database, "baza", "bazadate")


class TableTestCase(unittest.TestCase):
    def setUp(self):
        set_root_location(r'D:\db')
        self.db = "bazadate"

    def test_create_table1(self):
        self.assertRaises(FileExistsError, create_table, self.db, "tabela", [("field1","str"), ("field2","int"), ("field3","float")])

    def test_create_table2(self):
        self.assertRaises(FileNotFoundError, create_table, "baza", "tabela", [])

    def test_delete_table1(self):
        self.assertRaises(FileNotFoundError, delete_table, self.db, "tabel")

    def test_delete_table2(self):
        self.assertRaises(FileNotFoundError, delete_table, "baza", "tabel")

    def test_change_table_name1(self):
        self.assertRaises(FileNotFoundError, change_table_name, self.db, "tabel", "table1")

    def test_change_table_name2(self):
        self.assertRaises(FileExistsError, change_table_name, self.db, "tabela", "tabela")

    def test_change_table_name3(self):
        self.assertRaises(FileNotFoundError, change_table_name, "baza", "tabel", "table1")

    def test_insert_in_table1(self):
        self.assertRaises(FileNotFoundError, insert_in_table, "baza", "tabel", [])

    def test_insert_in_table2(self):
        self.assertRaises(FileNotFoundError, insert_in_table, self.db, "tabel", [])

    def test_insert_in_table3(self):
        self.assertRaises(IndexError, insert_in_table,  self.db, "tabela", [(), (), (), ()])

    @unittest.expectedFailure
    def test_insert_in_table4(self):
        self.assertRaises(TypeError, insert_in_table, self.db, "tabela", [("field2", "bine")])

    def test_insert_in_table5(self):
        self.assertRaises(TypeError, insert_in_table, self.db, "tabela", [("field1", 2)])

    def test_insert_in_table6(self):
        self.assertRaises(TypeError, insert_in_table, self.db, "tabela", [("field3", "str")])

    def test_insert_in_table7(self):
        self.assertRaises(IndexError, insert_in_table, self.db, "tabela", [()])

    @unittest.expectedFailure
    def test_insert_in_table8(self):
        self.assertRaises(IndexError, insert_in_table, self.db, "tabela", [])

    def test_change_fields_in_table1(self):
        self.assertRaises(FileNotFoundError, change_fields_in_table, "baza", "tabela", [])

    def test_change_fields_in_table2(self):
        self.assertRaises(FileNotFoundError, change_fields_in_table, self.db, "tabel", [])

    def test_change_fields_in_table3(self):
        self.assertRaises(IndexError, change_fields_in_table, self.db, "tabela", [])

    @unittest.expectedFailure
    def test_change_fields_in_table4(self):
        self.assertRaises(ValueError, change_fields_in_table, self.db, "tabela", [("field6", "field7")])

    @unittest.expectedFailure
    @unittest.skip
    def test_change_fields_in_table5(self):
        self.assertRaises(ValueError, change_fields_in_table, self.db, "tabela", [("field2", "field3")])

    def test_add_column_in_table1(self):
        self.assertRaises(FileNotFoundError, add_column_to_table, "baza", "tabela", [])

    def test_add_column_in_table2(self):
        self.assertRaises(FileNotFoundError, add_column_to_table, self.db, "tabel", [])

    def test_add_column_in_table3(self):
        self.assertRaises(IndexError, add_column_to_table, self.db, "tabela", [])

    def test_add_column_in_table4(self):
        self.assertRaises(ValueError, add_column_to_table, self.db, "tabela", [("field1", "str")])

    def test_add_column_in_table5(self):
        self.assertRaises(ValueError, add_column_to_table, self.db, "tabela", [("field1", "str"), ("field4", "float"), ("field7", "int")])

    def test_drop_column_in_table1(self):
        self.assertRaises(FileNotFoundError, drop_column_in_table, "baza", "tabela", "")

    def test_drop_column_in_table2(self):
        self.assertRaises(FileNotFoundError, drop_column_in_table, self.db, "tabel", "")

    def test_drop_column_in_table3(self):
        self.assertRaises(ValueError, drop_column_in_table, self.db, "tabela", "")

    def test_delete_in_table1(self):
        self.assertRaises(FileNotFoundError, delete_in_table, "baza", "tabela", [])

    def test_delete_in_table2(self):
        self.assertRaises(FileNotFoundError, delete_in_table, self.db, "tabel", [])

    @unittest.expectedFailure
    def test_delete_in_table3(self):
        self.assertRaises(IndexError, delete_in_table, self.db, "tabela", [])

    def test_delete_in_table4(self):
        self.assertRaises(ValueError, delete_in_table, self.db, "tabela", [("field1", "==", 4)])

    def test_delete_in_table5(self):
        self.assertRaises(NotImplementedError, delete_in_table, self.db, "tabela", [("field1", ">", "str")])

    def test_select_in_table1(self):
        self.assertRaises(FileNotFoundError, select_in_table, "baza", "tabela",  [])

    def test_select_in_table2(self):
        self.assertRaises(FileNotFoundError, select_in_table, self.db, "tabel", [])

    @unittest.expectedFailure
    def test_select_in_table3(self):
        self.assertRaises(IndexError, select_in_table, self.db, "tabela", [])

    def test_select_in_table4(self):
        self.assertRaises(ValueError, select_in_table, self.db, "tabela", ["field7"], [("field1", "==", 4)])

    def test_select_in_table5(self):
        self.assertRaises(NotImplementedError, select_in_table, self.db, "tabela", ["field2"], [("field1", ">", "str")])

    @unittest.expectedFailure
    def test_select_in_table6(self):
        self.assertRaises(ValueError, select_in_table, self.db, "tabela", ["field1"], [("field7", "==", 4)])

    def test_select_in_table7(self):
        self.assertRaises(ValueError, select_in_table, self.db, "tabela", ["field1"], [("field1", "==", 4)])

    @unittest.expectedFailure
    def test_select_in_table8(self):
        insert_in_table(self.db, "tabela", [("field1", "bine"), ("field2", 4), ("field3", 3.0)])
        self.assertEqual(select_in_table(self.db, "tabela", ["field1"], [("field3", "==", 3.0)]), [['bine']])

    def test_select_in_table9(self):
        insert_in_table(self.db, "tabela", [("field1", "ceva"), ("field2", 3), ("field3", 7.0)])
        self.assertNotEqual(select_in_table(self.db, "tabela", ["field1"], [("field3", "==", 7.0)]), [['ceva', '3', '7.0']])

    def test_get_schema1(self):
        self.assertRaises(FileNotFoundError, get_schema, "baza", "tabela")

    def test_get_schema2(self):
        self.assertRaises(FileNotFoundError, get_schema, self.db, "tabel")

    def test_get_schema3(self):
        self.assertEqual(get_schema(self.db, "tabela"), [('field1', 'str'), ('field2', 'int'), ('field3', 'float')], 'Incorrect schema')

    def test_get_schema4(self):
        self.assertNotEqual(get_schema(self.db, "tabela"), [], 'Incorrect schema')

    def test_update_in_table1(self):
        self.assertRaises(FileNotFoundError, update_in_table, 'baza', "tabel", [])

    def test_update_in_table2(self):
        self.assertRaises(FileNotFoundError, update_in_table, self.db, "tabel", [])

    @unittest.expectedFailure
    def test_update_in_table3(self):
        self.assertRaises(IndexError, update_in_table, self.db, "tabela", [])

    def test_update_in_table4(self):
        self.assertRaises(NotImplementedError, update_in_table, self.db, "tabela", [("field1", "ceva")], [("field1", ">", "ceva")])

    @unittest.expectedFailure
    def test_update_in_table5(self):
        self.assertRaises(ValueError, update_in_table, self.db, "tabela", [("field9", "ceva")], [("field1", "==", "ceva")])

    @unittest.expectedFailure
    def test_update_in_table6(self):
        self.assertRaises(ValueError, update_in_table, self.db, "tabela", [("field1", "ceva")], [("field9", ">", "ceva")])

    def test_where1(self):
        self.assertEqual(where(1, "<", 2), True)

    @unittest.expectedFailure
    def test_where2(self):
        self.assertEqual(where("str", ">", "strc"), True)

    def test_where3(self):
        self.assertEqual(where(236.0, "==", 236.0), True)

    def test_where4(self):
        self.assertEqual(where(16.0, "!=", 3), True)

    @unittest.expectedFailure
    def test_convert1(self):
        types = ['int', 'str', 'float']
        values = ['5', 'ceva', 'str']
        self.assertRaises(TypeError, convert, types, values)

    def test_convert2(self):
        types = ['int', 'str', 'float']
        values = ['5', 'ceva', '3.0']
        self.assertEqual(convert(types, values), [5, 'ceva', 3.0])

    def test_convert_string1(self):
        temp_lista = [5,6,7]
        self.assertEqual(convert_to_string(temp_lista), ['5','6','7'])

unittest.main()
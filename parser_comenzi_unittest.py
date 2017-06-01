import unittest
import parser_comenzi as PC
import exports_imports as EI
import database_utils as DU
import sys
import shutil
import os

DB_ROOT_LOCATION = r'C:\Users\iungureanu\Desktop\facultate\calitatea_sist\proiect\DB'

class TestStringMethods(unittest.TestCase):
    def setUp(self):
        
        if os.path.exists(DB_ROOT_LOCATION):
            shutil.rmtree(DB_ROOT_LOCATION)
            
        os.mkdir(DB_ROOT_LOCATION)

        PC.parse_command('create database INU')
        PC.parse_command('use INU')
        PC.parse_command('create table inu2 (nume str, an int)')

        PC.parse_command('create table inu3 (id int, nume str, an int)')
        PC.parse_command('insert into inu3 (id, nume, an) values (1, inu, 1)')
        PC.parse_command('insert into inu3 (id, nume, an) values (2, inu2, 2)')
        PC.parse_command('insert into inu3 (id, nume, an) values (3, inu3, 3)')
        PC.parse_command('export inu3 plain')
        PC.parse_command('export inu3 csv')
        PC.parse_command('export inu3 xml')
        


    def test_select_simplu(self):
        command = 'select2 nume from table'
        self.assertRaises(PC.CommandNotImplemented, PC.parse_command, command)

    def test_comanda_nu_exista(self):
        command = 'a sada qd'
        self.assertRaises(PC.CommandNotImplemented, PC.parse_command, command)

    def test_select_incomplet(self):
        command = 'select '
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_select_fara_for(self):
        command = 'select nume where id == 5'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_select_where_pozitie_incorecta(self):
        command = 'select nume from tabel  asd  where id == 5'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)


    def test_where_parser(self):
        command = ['nume', '==', 'inu', 'prenume==', 'danut']
        result = PC.get_tokens_after_where(command)

        self.assertEqual(result, [('nume', '==', 'inu'), ('prenume', '==', 'danut')])

    def test_where_parser2(self): #bug fixed
        command = ['nume', '==', 'inu', 'prenume   ==', 'danut']
        result = PC.get_tokens_after_where(command)

        self.assertEqual(result, [('nume', '==', 'inu'), ('prenume', '==', 'danut')])

    def test_where_parser3(self): #bug fixed
        command = ['nume  ==   ', 'inu', 'prenume   ==', 'danut']
        result = PC.get_tokens_after_where(command)

        self.assertEqual(result, [('nume', '==', 'inu'), ('prenume', '==', 'danut')])

    def test_where_parser4(self): #e ok pt ca schema e NONE
        command = ['nume', '==', '2', 'prenume   ==', 'danut']
        result = PC.get_tokens_after_where(command)

        self.assertEqual(result, [('nume', '==', '2'), ('prenume', '==', 'danut')])

    def test_where_parser5(self):
        command = ['nume', '==', 'inu', 'prenume   ==', 'danut']
        schema = [('nume', 'int'), ('prenume', 'str')]
        #result = PC.get_tokens_after_where(command, schema=schema)

        self.assertRaises(ValueError, PC.get_tokens_after_where, command, False, schema)
        #self.assertEqual(result, [('nume', '==', 'inu'), ('prenume', '==', 'danut')])

    def test_where_parser6(self): #ar trebui sa il fac sa crash-eze
        command = ['nume', '==', 'inu', 'prenume   ==', 'danut']
        schema = [('nume', 'str')]
        #result = PC.get_tokens_after_where(command, schema=schema)

        self.assertRaises(PC.SyntexError, PC.get_tokens_after_where, command)
        #self.assertEqual(result, [('nume', '==', 'inu'), ('prenume', '==', 'danut')])

    def test_where_parser7(self): #ar trebui sa il fac sa crape
        command = ['nume', '==', 'inu', 'prenume   ==']

        self.assertRaises(PC.SyntexError, PC.get_tokens_after_where, command)

    def test_create_Database_incomplete(self):
        command = 'create database   '
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_create_database_correct(self):
        command = 'create database INU2'
        PC.parse_command(command)

    def test_create_database3(self):
        command = 'create database INU'
        self.assertRaises(DU.FileExistsError, PC.parse_command, command)

    def test_create_table(self): #e success 
        command = 'create table inu (nume int)'
        PC.parse_command(command)

    def test_create_table(self): 
        command = 'create table inu asd (nume int)'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_create_table2(self): 
        command = 'create table inu (nume int, prenume)'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_create_table3(self): 
        command = 'create table inu (((nume int, prenume)))'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_create_table4(self): 
        command = 'create table inu (nume int, prenume'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_create_table5(self): 
        command = 'create table inu nume int, prenume)'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_create_table6(self): 
        command = 'create table inu nume int, prenume'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_alter_table(self): 
        command = 'alter tabl inu add column varsta'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_alter_table2(self): 
        command = 'alter table inu invalid column varsta'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_alter_table3(self): #fixed
        command = 'alter table inu2 add column varsta'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_drop_column(self):
        command = 'alter table inu2 drop varsta'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_insert(self): # nu corespunde cu schema...
        command = 'insert into inu2 (nume  ,   prenume) values (inu   , best)'
        self.assertRaises(TypeError, PC.parse_command, command)

    def test_insert2(self): 
        command = 'insert into inu2 (nume)'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_insert3(self): 
        command = 'insert inu2 (nume) values (inu)'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_insert4(self): 
        command = 'insert into inu2 (nume,  ) values (inu)'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_insert5(self): #tipuri diferite de date
        command = 'insert into inu2 (nume, an) values (inu, inu)'
        self.assertRaises(TypeError, PC.parse_command, command)

    def test_delete(self): #fixed. modificat in or
        command = 'delete from inu2 wh id == 5'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_delete2(self):
        command = 'delete fro inu2 where id == 5'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_delete3(self):
        command = 'delete from inu2 where   '
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_delete4(self):
        command = 'delete from inu2 where id '
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_update(self):
        command = 'update inu2 se nume=best, prenume = best2 ,  age =  23 where nume = inu'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_update2(self): #ar trebui sa dea erori
        command = 'update inu2 set nume   = best, ,  an =  23 where nume = inu'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_update3(self):
        command = 'update inu2 set nume=best,  where nume = '
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_update4(self): #poate trebuie validata de alin
        command = 'update inu2 set an=best,  where id == 3'
        self.assertRaises(TypeError, PC.parse_command, command)

    def test_import_txt(self):
        command = 'import inu3 plain export_table.txt'
        PC.parse_command(command)

    def test_import_xml(self):
        command = 'import inu2 xml export_table.xml'
        self.assertRaises(EI.SchemaNotMatch, PC.parse_command, command)
    
    def test_import_xml2(self):
        command = 'import inu2 xml2 export_table.xml'
        self.assertRaises(PC.SyntexError, PC.parse_command, command)

    def test_import_xml3(self):
        command = 'import inu2 xml export_table.txt'
        self.assertRaises(EI.SchemaNotMatch, PC.parse_command, command) 

    def test_import_xml4(self):
        command = 'import inu2 csv export_table.txt'
        self.assertRaises(EI.SchemaNotMatch, PC.parse_command, command) 

if __name__ == '__main__':
    unittest.main()
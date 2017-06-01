import sys
import os
import re
import database_utils as DB
import exports_imports as EI

if sys.version_info[0] < 3:
    class FileExistsError(Exception):
        pass

    class FileNotFoundError(Exception):
        pass
    class SyntexError(Exception):
        pass
    class CommandNotImplemented(Exception):
        pass

COMMAND_LIST = ['select', 'insert', 'drop', 'create']
COMP_OP_LIST = ['<=', '>=', '!=', '<', '>', '==', '=']

DATABASE = ''

def get_tokens_between_parenthesis(tokens, schema = None):

    result = []
    i = 0
    is_valid = False

    while i < len(tokens):
        token = tokens[i].strip()
        if token[0] == '(':
            is_valid = True
            token = token[1:]

        if is_valid == True and len(token) > 0 and token != ',':
            if token[-1] == ',':
                token = token[:-1]
            result.append(token)

        if token[-1] == ')':
            result[len(result) - 1] = result[len(result) - 1][:-1]
            return result

        i += 1

    # poate ar trebui sa iesim
    return result

def get_tokens_after_where(tokens, is_set=False, schema = None):
    print 'Tok: ' + str(tokens)
    new_tokens = []
    for item in tokens:
        if is_set == True:
            if item == ',':
                continue
            if item[-1] == ',':
                item = item[:-1]
        splited = False
        for op in COMP_OP_LIST:
            if op == '=' and is_set == False:
                continue
            if op in item and len(item) > len(op):
                if splited == True:
                    raise SyntexError
                    #eroare
                
                tmp = item.split(op)
                if len(tmp) != 2:
                    #eroare
                    raise SyntexError

                if len(tmp[0]):
                    new_tokens.append(tmp[0])
                new_tokens.append(op)
                if len(tmp[1]):
                    new_tokens.append(tmp[1])
                
                splited = True

        if splited == False:
            new_tokens.append(item)

    result = []
    i = 0
    #print 'New tokens: ' + str(new_tokens)
    while i < len(new_tokens):
        if new_tokens[i] == 'and':
            i += 1
            continue
        if i + 2 >= len(new_tokens):
            #print 'Numar tokeni invalid in where'
            raise SyntexError

        f_name = new_tokens[i]
        op = new_tokens[i + 1]
        f_value = new_tokens[i + 2]

        if len(f_value) == 0:
            i+=3
            continue

        if schema is not None:
            for ii in schema:
                (nume, tip) = ii

                if nume == f_name:
                    if tip == 'str':
                        f_value = str(f_value)
                    elif tip == 'int':
                        f_value = int(f_value)
                    elif tip == 'float':
                        f_value = float(f_value)

        result.append((f_name, op, f_value))

        i += 3
    
    return result

# send: db_name, table_name, selected_fields = [field1, field2,...] where_list = [(field, op, value), (...), ...]
def parse_select(tokens):

    fields_to_select = []
    where_list = []
    from_token_position = None
    where_token_position = None
    table_name = None

    if len(tokens) == 0:
        raise SyntexError

    try:
        from_token_position = tokens.index('from')
    except ValueError as ve:
        raise SyntexError
    
    try:
        where_token_position = tokens.index('where')
    except ValueError as ve:
        pass

    
    i = 0
    while i < from_token_position:
        field_token = tokens[i].split(',')
        for item in field_token:
            if len(item) > 0:
                fields_to_select.append(item)
        i += 1

    if len(fields_to_select) == 0:
        raise SyntexError
    
    if from_token_position + 1 < len(tokens):
        table_name = tokens[from_token_position + 1]
    else:
        raise SyntexError

    if where_token_position is not None:
        if where_token_position != from_token_position + 2:
            #print 'Where clause index error'
            raise SyntexError

        schema = DB.get_schema(DATABASE, table_name)
        where_list = get_tokens_after_where(tokens[where_token_position + 1:], schema=schema)

        if len(where_list) == 0:
            raise SyntexError
    
    #print fields_to_select
    #print where_list
    


    result = DB.select_in_table(DATABASE, table_name, fields_to_select, where_list)
    
    print result

# send for table db_name, table_name, schema = [(f_type, f_name), (...)]
def parse_create(tokens, tokens_create):

    if len(tokens) == 0:
        raise SyntexError

    name = None
    schema = []
    if tokens[0] == 'database':
        if len(tokens) < 2:
            raise SyntexError

        name = tokens[1]
        DB.create_database(name)
    elif tokens[0] == 'table':
        if len(tokens) < 2:
            raise SyntexError

        name = tokens[1]
        if len(tokens_create) > 2:
            #print 'Too many tokens create ' + str(len(tokens_create))
            raise SyntexError
        tokens_create = tokens_create[1][:-1].split(',')
        for item in tokens_create:
            data = item.strip().split(' ')
            schema.append((data[0], data[1]))
        
        #print schema
        DB.create_table(DATABASE, name, schema)
        

def parse_drop(tokens):
    if len(tokens) != 1:
        raise SyntexError

    name = tokens[1]
    if tokens[0] == 'database':
        DB.delete_database(DATABASE)
    elif tokens[0] == 'table':
        DB.delete_table(DATABASE, name)

# send: db_name ,table_name, 
#   param: add|drop|modify
#       add: [(f_name, f_type)]
def parse_alter(tokens):

    if len (tokens) < 2:
        raise SyntexError
    
    if tokens[0] != 'table':
        #print 'Alter table invalid'
        raise SyntexError

    table_name = tokens[1]

    if tokens[2] == 'add': # add column
        if len(tokens) != 5:
            raise SyntexError
        column_name = tokens[3]
        column_type = tokens[4]
        DB.add_column_to_table(DATABASE, table_name, [(column_name, column_type)])
        pass
    elif tokens[2] == 'drop': # drop column
        if len(tokens) != 4:
            raise SyntexError
        column_name = tokens[3]
        DB.drop_column_in_table(DATABASE, table_name, column_name)
        pass
    elif tokens[2] == 'modify': # modify column
        if len(tokens) != 5:
            raise SyntexError
        column_name = tokens[3]
        new_column_name = tokens[4]
        DB.change_fields_in_table(DATABASE, table_name, [(column_name, new_column_name)])
        pass
    else:
        raise SyntexError

# send db_name, table_name, [(f_name, f_value)]
def parse_insert(tokens):

    if len(tokens) < 2:
        raise SyntexError

    if tokens[0] != 'into':
        #print 'Insert invalid'
        raise SyntexError

    table_name = tokens[1]
    values_to_insert = []
    columns_to_insert = []
    data = []

    if tokens[2] == 'values':
        values_to_insert = get_tokens_between_parenthesis(tokens)
        print 'Insert values: ' + str(values_to_insert)
        # call the script
        pass
    else:
        columns_to_insert = get_tokens_between_parenthesis(tokens)
        if len(columns_to_insert) == 0:
            raise SyntexError

        try:
            values_token_position = tokens.index('values')
            values_to_insert = get_tokens_between_parenthesis(tokens[values_token_position:])
        except ValueError as ve:
            #print 'values token not found'
            raise SyntexError

        schema = DB.get_schema(DATABASE, table_name)

        for i in xrange(len(columns_to_insert)):
            if schema is not None:
                for ii in schema:
                    (nume, tip) = ii

                    if nume == columns_to_insert[i]:
                        print 'Match: ' + str(tip)
                        if tip == 'str':
                            values_to_insert[i] = str(values_to_insert[i])
                        elif tip == 'int':
                            values_to_insert[i] = int(values_to_insert[i])
                        elif tip == 'float':
                            values_to_insert[i] = float(values_to_insert[i])

            data.append((columns_to_insert[i], values_to_insert[i]))
        
        #print 'Insert data: ' + str(data)
        if len(data) == 0:
            raise SyntexError
        DB.insert_in_table(DATABASE, table_name, data)

def parse_delete(tokens):

    if len(tokens) < 3:
        raise SyntexError
    
    if tokens[0] != 'from' and tokens[2] != 'where':
        #print 'Invalid delete'
        raise SyntexError

    table_name = tokens[1]

    try:
        where_token_position = tokens.index('where')
        schema = DB.get_schema(DATABASE, table_name)
        where_list = get_tokens_after_where(tokens[where_token_position + 1:], schema = schema)
        if len(where_list) == 0:
            raise SyntexError
    except ValueError as ve:
        #print 'delete invalid'
        raise SyntexError

    #print where_list
    DB.delete_in_table(DATABASE, table_name, where_list)
    # to fix !!!!!!
    # parse where cond starting from pos 3

def parse_update(tokens):

    if len(tokens) < 2:
        raise SyntexError
    
    table_name = tokens[0]
    columns_to_set = []
    where_list = []

    if tokens[1] != 'set':
        #print 'Update syntax error'
        raise SyntexError

    try:
        where_token_position = tokens.index('where')
        columns_to_set_tmp = get_tokens_after_where(tokens[2:where_token_position], True)
        for item in columns_to_set_tmp:
            (a,b,c) = item
            columns_to_set.append((a,c))
        schema = DB.get_schema(DATABASE, table_name)
        where_list = get_tokens_after_where(tokens[where_token_position + 1:], schema = schema)
    except ValueError as ve:
        #print 'update invalid'
        raise SyntexError

    #print columns_to_set
    #print where_list
    if len(where_list) == 0 or len(columns_to_set) == 0:
        raise SyntexError
    DB.update_in_table(DATABASE, table_name, columns_to_set, where_list)

def parse_use(tokens):
    global DATABASE

    if len(tokens) != 1:
        raise SyntexError
    
    DATABASE = tokens[0]

def parse_change_database(tokens):
    if len(tokens) != 2:
        raise SyntexError
    
    old_name = tokens[0]
    new_name = tokens[1]

    DB.change_database(old_name, new_name)

def parse_export(tokens):

    if len(tokens) != 2:
        raise SyntexError
    
    table_name = tokens[0]
    file_type = tokens[1]

    if file_type == 'plain':
        EI.export_plain(DATABASE, table_name)
    elif file_type == 'csv':
        EI.export_csv(DATABASE, table_name)
    elif file_type == 'xml':
        EI.export_xml(DATABASE, table_name)

def parse_import(tokens):

    if len (tokens) != 3:
        raise SyntexError

    table_name = tokens[0]
    file_type = tokens[1]
    file_path = tokens[2]

    if file_type == 'plain':
        EI.import_plain(DATABASE, table_name, file_path)
    elif file_type == 'csv':
        EI.import_csv(DATABASE, table_name, file_path)
    elif file_type == 'xml':
        EI.import_xml(DATABASE, table_name, file_path)

if __name__ == '__main__':

    tokens = []
    
    command_select = 'select nume,prenume,  nume2 from plm where a > b'
    command_select2 = 'select nume,prenume,  nume2 from inu where a     > b and a<c'
    command_create_table = 'create table inu (id int, nume str   ,    prenume str   )'
    command_insert_into = 'insert into inu (nume  ,   prenume) values (inu   , best)'
    command_insert_into2 = 'insert into inu values (inu, best)' # nu implementam
    command_update = 'update inu set nume=best, prenume = best2 ,  age =  23 where nume = inu'

    #command = 'alter table inu add coloana3 int'
    #command = 'alter table inu modify coloana3 prenume'
    #command = 'create table inu2 (id int, c str)'
    #command = 'delete from inu where id == 3'
    #command = 'update inu set nume=inu44 where id==2'
    #command = command_update

    global DATABASE
    DATABASE = 'INU'

    

    while True:
        try:
            command = ''
            tokens = []
            command = raw_input('-->')

            tokens_tmp = command.split(' ')
            tokens2 = command.split('(')
        
            for item in tokens_tmp:
                if len(item) > 0:
                    tokens.append(item)

            print 'Tokens: ' + str(tokens)
            print 'Tokens2: ' + str(tokens2)

            
            if tokens[0] == 'select':
                parse_select(tokens[1:])
            elif tokens[0] == 'drop':
                parse_drop(tokens[1:])
            elif tokens[0] == 'create':
                parse_create(tokens[1:], tokens2)
            elif tokens[0] == 'alter':
                parse_alter(tokens[1:])
            elif tokens[0] == 'insert':
                parse_insert(tokens[1:])
            elif tokens[0] == 'delete':
                parse_delete(tokens[1:])
            elif tokens[0] == 'update':
                parse_update(tokens[1:])
            elif tokens[0] == 'use':
                parse_use(tokens[1:])
            elif tokens[0] == 'change':
                parse_change_database(tokens[1:])
            elif tokens[0] == 'export':
                parse_export(tokens[1:])
            else:
                raise CommandNotImplemented
    
        except FileExistsError as e:
            print 'File error'
        except FileNotFoundError as e:
            print 'File not found'
        except SyntexError as e:
            print 'Syntax error'
        except CommandNotImplemented as e:
            print 'Command not implemented'
        except DB.FileExistsError as e:
            print 'File error'
        except DB.FileNotFoundError as e:
            print 'File not found'
        except DB.SyntexError as e:
            print 'Syntax error'
        except DB.CommandNotImplemented as e:
            print 'Command not implemented'


    

# insert into inu (id, nume, prenume) values (1, inu, inu)
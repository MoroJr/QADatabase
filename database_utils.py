import os
import shutil
import time
import sys
if sys.version_info[0] < 3:
    class FileExistsError(Exception):
        pass

    class FileNotFoundError(Exception):
        pass

DB_ROOT_LOCATION = r'C:\Users\asimion\Desktop\bit\FAC\CSS'


def set_root_location(workspace_path):
    global DB_ROOT_LOCATION
    DB_ROOT_LOCATION = workspace_path


def create_database(db_name):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if os.path.exists(db_location):
        raise FileExistsError
    else:
        os.mkdir(db_location)
        return True


def delete_database(db_name):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if os.path.exists(db_location):
        shutil.rmtree(db_location)
        return True
    else:
        raise FileNotFoundError


def create_table(db_name, table_name, args_list):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if os.path.exists(table_location):
        raise FileExistsError

    schema_path = os.path.join(db_location, str(table_name)+'_schema')
    if os.path.exists(schema_path):
        raise FileExistsError

    with open(schema_path, 'w+') as schema:
        for arg in args_list:
            schema.write(str(arg[0])+','+str(arg[1]))
            if arg != args_list[len(args_list)-1]:
                schema.write('|')
    f = open(table_location, 'w+')
    return True


def delete_table(db_name, table_name):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if os.path.exists(table_location):
        os.remove(table_location)
        if os.path.exists(table_location+'_schema'):
            os.remove(table_location+'_schema')
        else:
            raise FileNotFoundError
        return True
    else:
        raise FileNotFoundError


def check_type(upl1, upl2):
    clasa = str
    if upl1[1] == 'str':
        clasa = str
    elif upl1[1] == 'int':
        clasa = int
    elif upl1[1] == 'float':
        clasa = float

    if isinstance(upl2[1], clasa):
        return True
    else:
        return False


def insert_in_table(db_name, table_name, args_list):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    schema_location = os.path.join(db_location, table_name+'_schema')
    if not os.path.exists(table_location) and os.path.exists(schema_location):
        raise FileNotFoundError

    lista_args = []
    with open(schema_location, 'r+') as schema:
        line = schema.readline()

        for i in line.split('|'):
            lista_args.append(tuple([i.split(',')[0], i.split(',')[1]])) # = [(args_name, arg_type),(..),(..)]

    if len(args_list) > len(lista_args):
        raise IndexError

    message = ''
    with open(table_location, 'a+') as table:
        for i in lista_args:
            for j in args_list:
                if i[0] == j[0]:
                    if not check_type(i, j):
                        raise TypeError
                    else:
                        message += str(j[1])
            if i != lista_args[len(lista_args)-1]:
                message += '\t'
        table.write(message+'\n')


def change_database(old_db_name, new_db_name):
    global DB_ROOT_LOCATION
    old_db_location = os.path.join(DB_ROOT_LOCATION, old_db_name)
    if not os.path.exists(old_db_location):
        raise FileNotFoundError

    new_db_location = os.path.join(DB_ROOT_LOCATION, new_db_name)
    if os.path.exists(new_db_location):
        raise FileExistsError

    os.mkdir(new_db_location)

    for table in os.listdir(old_db_location):
        old_table_path = os.path.join(old_db_location, table)
        new_table_path = os.path.join(new_db_location, table)
        shutil.copyfile(old_table_path, new_table_path)

    shutil.rmtree(old_db_location)


def change_table_name(db_name, old_table_name,  new_table_name):
    global DB_ROOT_LOCATION
    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, old_table_name)
    table_schema_path = os.path.join(db_path, str(old_table_name)+'_schema')
    if not os.path.exists(table_path) or not os.path.exists(table_schema_path):
        raise FileNotFoundError

    new_table_path = os.path.join(db_path, new_table_name)
    new_table_schema_path = os.path.join(db_path, str(new_table_name)+'_schema')
    if os.path.exists(new_table_path) or os.path.exists(new_table_schema_path):
        raise FileExistsError

    os.rename(table_path, new_table_path)
    os.rename(table_schema_path, new_table_schema_path)


def change_fields_in_table(db_name, table_name, args_list): # args_list = [(old_f_name, new_f_name), ()]
    global DB_ROOT_LOCATION

    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, table_name)
    if not os.path.exists(table_path):
        raise FileNotFoundError

    schema_path = os.path.join(db_path, str(table_name)+'_schema')

    if not os.path.exists(schema_path):
        raise FileNotFoundError

    if len(args_list) < 1:
        raise IndexError

    field_list = []
    with open(schema_path, 'r') as schema:
        line = schema.readline().split('|')
        for i in line:
            camps = i.split(',')
            field_list.append((camps[0], camps[1]))
        for i in args_list:
            for j in range(0, len(field_list)):
                if i[0] == field_list[j][0]:
                    field_list[j] = (i[1], field_list[j][1])

    os.remove(schema_path)

    with open(schema_path, 'w+') as schema:
        for i in field_list:
            schema.write(i[0]+','+i[1])
            if i != field_list[len(field_list)-1]:
                schema.write('|')


def add_column_to_table(db_name, table_name, columns):
    global DB_ROOT_LOCATION

    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, table_name)
    if not os.path.exists(table_path):
        raise FileNotFoundError

    schema_path = os.path.join(db_path, str(table_name)+'_schema')

    if not os.path.exists(schema_path):
        raise FileNotFoundError

    if len(columns) < 1:
        raise IndexError

    line = ""
    with open(schema_path, 'r+') as schema:
        line = schema.readline()
        for i in line.split('|'):
            for j in columns:
                f_name = i.split(',')[0]
                if f_name == j[0]:
                    raise ValueError
        for i in columns:
            line += '|'+i[0]+','+i[1]

    os.remove(schema_path)

    with open(schema_path, 'w+') as schema:
        schema.write(line)

    linii = []
    with open(table_path, 'r+') as table:
        linii = table.readlines()

    os.remove(table_path)

    with open(table_path, 'w+') as table:
        if len(linii) > 0:
            for j in linii:
                if j != '\n' and j != '':
                    good_line = j.replace('\n', '\t')
                    table.write(good_line)
                    if not good_line.endswith('\n'):
                        table.write('\n')


def drop_column_in_table(db_name, table_name, column_name):
    global DB_ROOT_LOCATION

    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, table_name)
    if not os.path.exists(table_path):
        raise FileNotFoundError

    schema_path = os.path.join(db_path, str(table_name)+'_schema')

    if not os.path.exists(schema_path):
        raise FileNotFoundError

    if column_name == '':
        raise ValueError

    column_index = 0
    counter = -1
    temp_line = []
    with open(schema_path, 'r+') as schema:
        line = schema.readline()
        for i in line.split('|'):
            counter += 1
            schema_column_name = i.split(',')[0]
            if column_name == schema_column_name:
                column_index = counter
                continue
            else:
                temp_line.append(i)

    if len(temp_line) < 1:
        raise ValueError

    os.remove(schema_path)

    with open(schema_path, 'w+') as schema:
        message = ''
        for i in temp_line:
            message += str(i)
            if i != temp_line[len(temp_line)-1]:
                message += '|'
        schema.write(message)

    records = []
    with open(table_path, 'r+') as table:
        records = table.readlines()

    os.remove(table_path)
    with open(table_path, 'w+') as table:
        for linie in records:
            new_line = ''
            linie = linie.replace('\n', '')
            linie_list = linie.split('\t')
            for field_no in range(0, len(linie_list)):
                if field_no != column_index:
                    new_line += linie_list[field_no]
                    if field_no != len(linie_list)-2 and linie_list[field_no] != '\n':
                        new_line += '\t'
            table.write(new_line+'\n')


def where(value1, op, value2):
    if op == '>':
        return value1 > value2
    elif op == '==':
        return value1 == value2
    elif op == '<':
        return value1 < value2
    elif op == '!=':
        return value1 != value2


def convert(types_list, field_value_list):
    for i in range(0, len(types_list)):
        if types_list[i] == 'str':
            field_value_list[i] = str(field_value_list[i])
            continue
        elif types_list[i] == 'int':
            field_value_list[i] = int(field_value_list[i])
            continue
        elif types_list[i] == 'float':
            field_value_list[i] = float(field_value_list[i])
            continue
    return field_value_list


def convert_to_string(lista):
    temp_list = []
    for elem in lista:
        temp_list.append(str(elem))
    return temp_list


def delete_in_table(db_name, table_name, where_list):
    global DB_ROOT_LOCATION

    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, table_name)
    if not os.path.exists(table_path):
        raise FileNotFoundError

    schema_path = os.path.join(db_path, str(table_name)+'_schema')

    if not os.path.exists(schema_path):
        raise FileNotFoundError

    linii = []
    with open(table_path, 'r+') as table:
        linii = table.readlines()
        for i in range(0, len(linii)):
            linii[i] = linii[i].replace('\n', '')

    field_names = []
    perechi = []
    types = []
    with open(schema_path, 'r+') as schema:
        perechi = schema.readline().split('|')
        for pereche in perechi:
            field_names.append(pereche.split(',')[0])
            types.append(pereche.split(',')[1])

    for i in perechi:
        for j in where_list:
            field_name1 = i.split(',')[0]
            field_name2 = j[0]
            if field_name1 == field_name2:
                upl1 = (i.split(',')[0], i.split(',')[1])
                upl2 = (j[0], j[2])
                if not check_type(upl1, upl2):
                    raise ValueError
                if j[1] == '>' or j[1] == '<':
                    if upl1[1] == 'str':
                        raise NotImplementedError

    indexes = []
    for i in where_list:
        for j in range(0, len(field_names)):
            if i[0] == field_names[j]:
                indexes.append(j)

    temp_linii = []
    for linie in linii:
        temp_linii.append(linie.split('\t'))


    copie_linii = temp_linii
    for temp_linie in temp_linii:
        temp_linie = convert(types, temp_linie)
        check = 0
        for i in range(0, len(indexes)):
            if where(temp_linie[indexes[i]], where_list[i][1], where_list[i][2]):
                check = 1
            else:
                check = 0
        if check == 1:
            copie_linii.remove(temp_linie)


    os.remove(table_path)

    with open(table_path, 'w+') as table:
        for linie in copie_linii:
            for i in range(0, len(linie)):
                table.write(str(linie[i]))
                if i != len(linie)-1:
                    table.write('\t')

            table.write('\n')


def select_in_table(db_name, table_name, select_list, where_list=[]):
    global DB_ROOT_LOCATION

    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, table_name)
    if not os.path.exists(table_path):
        raise FileNotFoundError

    schema_path = os.path.join(db_path, str(table_name)+'_schema')

    if not os.path.exists(schema_path):
        raise FileNotFoundError

    linii = []
    with open(table_path, 'r+') as table:
        linii = table.readlines()
        for i in range(0, len(linii)):
            linii[i] = linii[i].replace('\n', '')

    field_names = []
    perechi = []
    types = []
    with open(schema_path, 'r+') as schema:
        perechi = schema.readline().split('|')
        for pereche in perechi:
            field_names.append(pereche.split(',')[0])
            types.append(pereche.split(',')[1])

    for i in perechi:
        for j in where_list:
            field_name1 = i.split(',')[0]
            field_name2 = j[0]
            if field_name1 == field_name2:
                upl1 = (i.split(',')[0], i.split(',')[1])
                upl2 = (j[0], j[2])
                if not check_type(upl1, upl2):
                    raise ValueError
                if j[1] == '>' or j[1] == '<':
                    if upl1[1] == 'str':
                        raise NotImplementedError

    indexes = []
    for i in where_list:
        for j in range(0, len(field_names)):
            if i[0] == field_names[j]:
                indexes.append(j)

    temp_linii = []
    for linie in linii:
        temp_linii.append(linie.split('\t'))

    selected_indexes = []

    for i in select_list:
        for j in range(0, len(field_names)):
            if i == field_names[j]:
                selected_indexes.append(j)
    selected_indexes = sorted(selected_indexes)

    select_return = []
    temp_select = []
    copie_linii = temp_linii
    if len(where_list) > 0:
        for temp_linie in temp_linii:
            temp_linie = convert(types, temp_linie)
            #print(temp_linie)
            check = 0
            for i in range(0, len(indexes)):
                for j in range(0, len(where_list)):
                    if where(temp_linie[indexes[i]], where_list[j][1], where_list[j][2]):
                        check = 1
                    else:
                        check = 0
            if check == 1:
                temp_linie = convert_to_string(temp_linie)
                #copie_linii.remove(temp_linie)
                temp_select.append(temp_linie)
        select_return = temp_select
    else:
        for linie in copie_linii:
            temp_list = []
            for j in range(0, len(linie)):
                if j in selected_indexes:
                    temp_list.append(linie[j])
            select_return.append(temp_list)
        select_return
    return select_return


def get_schema(db_name, table_name):
    global DB_ROOT_LOCATION

    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, table_name)
    if not os.path.exists(table_path):
        raise FileNotFoundError

    schema_path = os.path.join(db_path, str(table_name)+'_schema')

    if not os.path.exists(schema_path):
        raise FileNotFoundError

    schema_list = []
    with open(schema_path, 'r+') as schema:
        line = schema.readline()
        for i in line.split('|'):
            schema_list.append((i.split(',')[0],i.split(',')[1]))
    return schema_list


def update_in_table(db_name, table_name, update_list, where_list=[]):
    global DB_ROOT_LOCATION

    db_path = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_path):
        raise FileNotFoundError

    table_path = os.path.join(db_path, table_name)

    if not os.path.exists(table_path):
        raise FileNotFoundError

    schema_path = os.path.join(db_path, str(table_name)+'_schema')

    if not os.path.exists(schema_path):
        raise FileNotFoundError

    linii = []
    with open(table_path, 'r+') as table:
        linii = table.readlines()
        for i in range(0, len(linii)):
            linii[i] = linii[i].replace('\n', '')

    field_names = []
    perechi = []
    types = []
    with open(schema_path, 'r+') as schema:
        perechi = schema.readline().split('|')
        for pereche in perechi:
            field_names.append(pereche.split(',')[0])
            types.append(pereche.split(',')[1])

    for i in perechi:
        for j in where_list:
            field_name1 = i.split(',')[0]
            field_name2 = j[0]
            if field_name1 == field_name2:
                upl1 = (i.split(',')[0], i.split(',')[1])
                upl2 = (j[0], j[2])
                if not check_type(upl1, upl2):
                    raise ValueError
                if j[1] == '>' or j[1] == '<':
                    if upl1[1] == 'str':
                        raise NotImplementedError

    indexes = []
    for i in where_list:
        for j in range(0, len(field_names)):
            if i[0] == field_names[j]:
                indexes.append(j)

    temp_linii = []
    for linie in linii:
        temp_linii.append(linie.split('\t'))


    update_indexes = []


    copie_linii = temp_linii
    for temp_linie in temp_linii:
        temp_linie = convert(types, temp_linie)
        check = 0
        for i in range(0, len(indexes)):
            if where(temp_linie[indexes[i]], where_list[i][1], where_list[i][2]):
                check = 1
            else:
                check = 0
        if check == 1:
            for i in update_list:
                index = field_names.index(i[0])
                temp_linie[index] = i[1]

    print(temp_linii)

    os.remove(table_path)

    with open(table_path, 'w+') as table:
        for linie in temp_linii:
            for i in range(0, len(linie)):
                table.write(str(linie[i]))
                if i != len(linie)-1:
                    table.write('\t')

            table.write('\n')

# update_in_table('bazadate','tabela',[('camp3', 400)] ,[('camp3','>', 200)])
#print(get_schema('bazadate','tabela'))
#
# ceva = u"123"
# print(ceva.isnumeric())
#insert_in_table('bazadate','tabela' ,[('camp3', 200)])

# CREATE_TABLE :
# input  db_name, table_name, args_list= [ (f_type, f_name), ()]
# output : True / False
#
# INSERT :
# input : db_name, table_name, [(f_name, f_value)]
#
# ALTER DB : change db name
# input : old_db_name ,  new_db_name
#
# ALTER TABLE NAME
# input : db_name , old_table_name, new_table_name
#
# ALTER TABLE FIELDS NAMES:
#   _input : [(old_f_name, new_f_name)]
#
# ALTER TABLE - ADD COLUMNS:
# _input : [(f_name, f_type)]
#
# ALTER TABLE - DROP COLUMN
# _input : column_name = str
#
# DELETE IN TABLE :
# input : db_name, table_name, where_list
#



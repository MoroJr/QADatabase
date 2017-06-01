import sys
import os

if sys.version_info[0] < 3:
    class FileExistsError(Exception):
        pass

    class FileNotFoundError(Exception):
        pass


DB_ROOT_LOCATION = r'C:\Users\iungureanu\Desktop\facultate\calitatea_sist\proiect\DB'

def set_root_location(workspace_path):
    global DB_ROOT_LOCATION
    DB_ROOT_LOCATION = workspace_path

def export_plain(db_name, table_name):

    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if not os.path.exists(table_location):
        raise FileExistsError

    schema_path = os.path.join(db_location, str(table_name)+'_schema')
    if not os.path.exists(schema_path):
        raise FileExistsError


    g = open('export_table.txt', 'w')

    with open(schema_path, 'r') as f:
        for line in f:
            g.write(line)

    g.write('\n--END_OF_SCHEMA--\n\n')

    with open(table_location) as f:
        for line in f:
            g.write(line)


def export_csv(db_name, table_name):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if not os.path.exists(table_location):
        raise FileExistsError

    schema_path = os.path.join(db_location, str(table_name)+'_schema')
    if not os.path.exists(schema_path):
        raise FileExistsError


    g = open('export_table.csv', 'w')

    with open(schema_path, 'r') as f:
        for line in f:
            g.write(line)

    g.write('\n--END_OF_SCHEMA--\n\n')

    with open(table_location) as f:
        for line in f:
            g.write(line.replace('\t', ','))

def export_xml(db_name, table_name):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if not os.path.exists(table_location):
        raise FileExistsError

    schema_path = os.path.join(db_location, str(table_name)+'_schema')
    if not os.path.exists(schema_path):
        raise FileExistsError


    g = open('export_table.xml', 'w')

    schema = []


    with open(schema_path, 'r') as f:
        txt = f.read()
        lines = txt.split('|')
        for line in lines:
            (a,b)=line.split(',')
            schema.append((a, b))

    with open(table_location, 'r') as f:
        for line in f:
            while len(line) and (line[-1] == '\n' or line[-1] == '\r'):
                line = line[:-1]
            
            column_values = line.split('\t')
            
            g.write('<row>\n')
            for i in range(len(schema)):
                (name, tip) = schema[i]
                g.write('\t<column name=%s type=%s>\n'%(name, tip))
                g.write('\t\t' + column_values[i] + '\n')
                g.write('\t</column>\n')
            g.write('</row>\n')

    print schema

def import_plain(db_name, table_name, file_path):

    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if not os.path.exists(table_location):
        raise FileExistsError

    schema_path = os.path.join(db_location, str(table_name)+'_schema')
    if not os.path.exists(schema_path):
        raise FileExistsError

    with open(schema_path) as f:
        schema = f.read()

    with open(file_path) as f:
        txt = f.read()

        data = txt.split('--END_OF_SCHEMA--')
        imported_schema = data[0].rstrip('\n')
        imported_data = data[1].rstrip('\n')
        
        while imported_data[0] == '\n' or imported_data[0] == '\r':
            imported_data = imported_data[1:]

        if imported_schema != schema:
            print 'schema differ'
        else:
            print 'Schema ok'
            

    with open(table_location, 'a+') as g:
        g.write(imported_data)


def import_csv(db_name, table_name, file_path):

    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if not os.path.exists(table_location):
        raise FileExistsError

    schema_path = os.path.join(db_location, str(table_name)+'_schema')
    if not os.path.exists(schema_path):
        raise FileExistsError

    with open(schema_path) as f:
        schema = f.read()

    with open(file_path) as f:
        txt = f.read()

        data = txt.split('--END_OF_SCHEMA--')
        imported_schema = data[0].rstrip('\n')
        imported_data = data[1].rstrip('\n')
        
        while imported_data[0] == '\n' or imported_data[0] == '\r':
            imported_data = imported_data[1:]

        if imported_schema != schema:
            print 'schema differ'
        else:
            print 'Schema ok'
            

    with open(table_location, 'a+') as g:
        g.write(imported_data.replace(',', '\t'))


def parse_tag(tag):
    if tag == 'row':
        return None

    tags = tag.split(' ')
    
    name_attr = tags[1].split('=')
    type_attr = tags[2].split('=')

    if name_attr[0] != 'name' or type_attr[0] != 'type':
        print 'Error'
        pass

    col_name = name_attr[1]
    col_type = type_attr[1]

    return (col_name, col_type)



def parse_value(value):

    return value.lstrip().rstrip()
    


def import_xml(db_name, table_name, file_path):
    db_location = os.path.join(DB_ROOT_LOCATION, db_name)
    if not os.path.exists(db_location):
        raise FileNotFoundError

    table_location = os.path.join(db_location, table_name)
    if not os.path.exists(table_location):
        raise FileExistsError

    schema_path = os.path.join(db_location, str(table_name)+'_schema')
    if not os.path.exists(schema_path):
        raise FileExistsError

    with open(schema_path) as f:
        schema = f.read()

    print schema

    g = open(table_location, 'a+')

    with open(file_path) as f:
        txt = f.read()

        open_tag = False
        close_tag = False
        word = ''
        value = ''
        imported_schema = ''
        values = []
        
        for i in xrange(len(txt)):
            if txt[i] == '<' and txt[i+1] == '/':
                value = parse_value(word)
                if len(value):
                    values.append(value)
                    (nume, tip) = column_data
                    imported_schema = imported_schema + nume + ',' + tip + '|'

                word = ''
            elif txt[i] == '<':
                word = ''
                value = ''
                column_data = None
            elif txt[i] == '>':
                if word[0] == '/': # </tag> 
                    pass
                else:   # <tag attr=var ...>
                    column_data = parse_tag(word)
                    if column_data == None and word == 'row':
                        if len(imported_schema):
                            imported_schema = imported_schema[:-1] # eliminam ultimul |
                            if imported_schema == schema and len(values):
                                print 'Schema ok'
                                g.write(values[0])
                                for j in xrange(1, len(values)):
                                    g.write('\t' + values[j])
                                g.write('\n')

                            else:
                                print 'Schema not ok'

                        imported_schema = ''
                        values = []

                
                word = ''
            else:
                word += txt[i]

        if len(imported_schema):
            imported_schema = imported_schema[:-1] # eliminam ultimul |
            if imported_schema == schema and len(values):
                print 'Schema ok'
                g.write(values[0])
                for j in xrange(1, len(values)):
                    g.write('\t' + values[j])
                g.write('\n')

            else:
                print 'Schema not ok'



if __name__ == '__main__':
    
    export_xml('INU', 'inu')
    import_xml('INU', 'inu', 'export_Table.txt')
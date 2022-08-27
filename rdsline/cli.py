from rdsline.tabulate import tabulate
import readline # needed in order to get nice behavior of input()
import rdsline.settings as settings
import os

def to_string(val):
    if 'isNull' in val and val['isNull']:
        return 'NULL'
    if 'stringValue' in val:
        return val['stringValue']
    if 'booleanValue' in val:
        return str(val['booleanValue'])
    if 'doubleValue' in val:
        return str(val['doubleValue'])
    if 'longValue' in val:
        return str(val['longValue'])
    if 'blobValue' in val:
        # TODO
        return 'BLOB'
    if 'arrayValue' in val:
        # TODO
        return 'ARRAY'
    return 'UNKTYPE'

def execute(connection, sql):
    response = connection.execute(sql)
    headers = [col["name"] for col in response["columnMetadata"]]
    records = [[to_string(value) for value in row] for row in response["records"]]
    return (headers, records)

def help():
    print(".quit - quits the REPL")
    print(".config <config_file> - sets new connection settings from a file")
    print(".show - displays current connection settings")

def read(prompt):
    try:
        return input("%s " % prompt)
    except EOFError:
        return ".quit"

def main():
    connection = settings.from_args()
    done = False
    buffer = ''
    prompt = '>'
    print("RDS-REPL -- Type .help for help")
    while not done:
        line = read(prompt)
        if line == '.help':
            help()
        elif line == '.quit':
            done = True
        elif line.startswith('.config'):
            (_, config_file) = line.split(' ')
            connection = settings.from_file(os.path.expanduser(config_file))
            connection.print()
        elif line.startswith('.show'):
            connection.print()
        elif line.endswith(';') or line == '':
            buffer += line
            if not connection.is_executable():
                print("Connection settings not set. Maybe you need to call .connect")
                connection.print()
                buffer = ''
                prompt = '>'
                continue
            try:
                (headers, records) = execute(connection, buffer)
                print(tabulate(records, headers=headers, tablefmt='psql'))
            except Exception as e:
                print("Error: %s" % str(e))
            finally:
                buffer = ''
                prompt = '>'
        else:
            buffer += line + ' '
            prompt = '|'
                

if __name__ == '__main__':
    main()
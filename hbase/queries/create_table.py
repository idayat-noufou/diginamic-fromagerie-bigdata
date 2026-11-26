import happybase

def create_hbase_table():
    connection = happybase.Connection(host='localhost', port=9090)

    if b'fromagerie' in connection.tables():
        print("Table existante, suppression...")
        connection.delete_table('fromagerie', disable=True)

    families = {
        'client': dict(),
        'order': dict()
    }
    connection.create_table('fromagerie', families)
    print("Table 'fromagerie' créée avec succès.")
    connection.close()

if __name__ == "__main__":
    create_hbase_table()

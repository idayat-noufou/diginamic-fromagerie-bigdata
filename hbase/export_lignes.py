import happybase
import pandas as pd

def export_lignes():
    connection = happybase.Connection(host='localhost', port=9090)
    table = connection.table('fromagerie')

    lignes = []
    for key, data in table.scan():
        ligne = {'rowkey': key.decode()}
        for col, val in data.items():
            ligne[col.decode().split(':')[1]] = val.decode()
        lignes.append(ligne)

    df = pd.DataFrame(lignes)
    df.to_csv('lignes.csv', index=False)
    print(f"{len(df)} lignes exportées dans lignes.csv")
    connection.close()

if __name__ == "__main__":
    export_lignes()

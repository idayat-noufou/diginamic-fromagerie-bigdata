import csv
import happybase

CSV_PATH = 'dataw_fro_clean.csv'
SEP = ','

def load_data():
    connection = happybase.Connection(host='localhost', port=9090)
    table = connection.table('fromagerie')

    n = 0
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=SEP)
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        with table.batch(batch_size=5000) as batch:
            for row in reader:
                date = row['datcde'].strip()[:10].replace('-', '')
                rowkey = f"{date}_{int(float(row['codcde'])):08d}_{int(float(row['codobj'])):06d}"

                batch.put(rowkey.encode(), {
                    b'client:codcli':    row['codcli'].encode(),
                    b'client:nom':       row['nomcli'].encode(),
                    b'client:prenom':    row['prenomcli'].encode(),
                    b'client:ville':     row['villecli'].strip().upper().encode(),
                    b'client:cp':        row['cpcli'].encode(),
                    b'order:codcde':     row['codcde'].encode(),
                    b'order:datcde':     row['datcde'].encode(),
                    b'order:timbrecde':  row['timbrecde'].encode(),
                    b'order:codobj':     row['codobj'].encode(),
                    b'order:qte':        row['qte'].encode(),
                    b'order:libobj':     row['libobj'].encode(),
                })
                n += 1

    print(f"{n} lignes chargées.")
    connection.close()

if __name__ == "__main__":
    load_data()

import happybase
import pandas as pd

def meilleure_commande_nantes_2020():
    connection = happybase.Connection(host='localhost', port=9090)
    table = connection.table('fromagerie')

    commandes = {}
    for key, data in table.scan(row_prefix=b'2020'):
        if data.get(b'client:ville', b'').decode() != 'NANTES':
            continue
        codcde = data[b'order:codcde'].decode()
        if codcde not in commandes:
            commandes[codcde] = {
                'codcde': codcde,
                'date': data[b'order:datcde'].decode(),
                'timbrecde': float(data[b'order:timbrecde']),
                'somme_qte': 0.0,
            }
        commandes[codcde]['somme_qte'] += float(data[b'order:qte'])

    best = max(commandes.values(), key=lambda c: (c['somme_qte'], c['timbrecde']))
    df = pd.DataFrame([best])
    df.to_csv('q1_meilleure_commande_nantes_2020.csv', index=False)
    print(df)
    connection.close()

if __name__ == "__main__":
    meilleure_commande_nantes_2020()

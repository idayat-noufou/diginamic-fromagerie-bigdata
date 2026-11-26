import happybase
import pandas as pd


def nombre(valeur):
    try:
        return float(valeur)
    except (ValueError, TypeError):
        return 0.0

def client_max_timbrecde():
    connection = happybase.Connection(host='localhost', port=9090)
    table = connection.table('fromagerie')

    lignes = []
    for key, data in table.scan():
        lignes.append({
            'codcli': data[b'client:codcli'].decode(),
            'nom': data[b'client:nom'].decode(),
            'prenom': data[b'client:prenom'].decode(),
            'codcde': data[b'order:codcde'].decode(),
            'timbrecde': nombre(data[b'order:timbrecde']),
            'qte': nombre(data[b'order:qte']),
        })
    df = pd.DataFrame(lignes)

    par_commande = df.drop_duplicates(subset=['codcli', 'codcde'])
    frais = par_commande.groupby('codcli').agg(
        nb_commandes=('codcde', 'count'),
        total_timbrecde=('timbrecde', 'sum'),
    )
    frais['somme_quantites'] = df.groupby('codcli')['qte'].sum()

    top = frais.sort_values('total_timbrecde', ascending=False).head(1).reset_index()
    top = top.merge(df[['codcli', 'nom', 'prenom']].drop_duplicates('codcli'), on='codcli')
    # !important,pour faire le xlsx, il faut modifier le docker file en ajoutant le module
    # `openpyxl` à la ligne pip install
    #top.to_excel('q3_client_max_timbrecde.xlsx', index=False)
    top.to_csv('q3_client_timbrecde.csv', index=False)
    print(top)
    connection.close()

if __name__ == "__main__":
    client_max_timbrecde()

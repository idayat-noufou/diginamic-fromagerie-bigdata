import happybase
import pandas as pd
import matplotlib.pyplot as plt

def commandes_par_annee():
    connection = happybase.Connection(host='localhost', port=9090)
    table = connection.table('fromagerie')

    commandes = set()
    for key, data in table.scan(row_start=b'2010', row_stop=b'2016'):
        commandes.add((key[:4].decode(), data[b'order:codcde'].decode()))

    df = pd.DataFrame(list(commandes), columns=['annee', 'codcde'])
    resultat = df.groupby('annee').size().reset_index(name='nb_commandes')
    resultat.to_csv('q2_commandes_par_annee.csv', index=False)
    print(resultat)

    plt.bar(resultat['annee'], resultat['nb_commandes'])
    plt.title('Nombre de commandes par année (2010-2015)')
    plt.xlabel('Année')
    plt.ylabel('Nombre de commandes')
    plt.savefig('q2_commandes_par_annee.pdf')
    connection.close()

if __name__ == "__main__":
    commandes_par_annee()

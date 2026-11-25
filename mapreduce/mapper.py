#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOT 3 - Mapper : requête A recodée en MapReduce streaming.
Top 100 des commandes 2006-2010, départements 53, 61 et 28.

Entrée  : les lignes du fichier TSV stocké dans HDFS
          (/data/fromagerie/commandes, le même fichier que la table Hive).
          1 ligne = 1 article d'une commande, 25 colonnes séparées par des
          tabulations, sans en-tête.

Rôle    : équivalent du WHERE de la requête Hive. Pour chaque ligne qui
          respecte le filtre, émettre une paire clé / valeur :
              clé    = numéro de commande (codcde)
              valeur = quantité, timbrecde, ville, département, date
          Hadoop trie ensuite les paires par clé (étape shuffle & sort) :
          toutes les lignes d'une même commande arrivent groupées au reducer.

Sortie  : codcde \t qte \t timbrecde \t ville \t departement \t datcde

Test local (sans Hadoop) :
    cat dataw_fro_clean.tsv | python3 mapper.py | sort | python3 reducer.py
"""

import sys

# Position des colonnes utiles dans le TSV (ordre de la table Hive)
CPCLI, VILLECLI, CODCDE, DATCDE, TIMBRECDE, QTE = 4, 5, 6, 7, 9, 15

ANNEES = range(2006, 2011)            # 2006 à 2010 inclus
DEPARTEMENTS = {"53", "61", "28"}


def main():
    for ligne in sys.stdin:
        champs = ligne.rstrip("\n").split("\t")
        if len(champs) != 25:
            continue                  # ligne malformée : ignorée

        datcde = champs[DATCDE]       # format AAAA-MM-JJ
        departement = champs[CPCLI][:2]
        try:
            annee = int(datcde[:4])
        except ValueError:
            continue
        if annee not in ANNEES or departement not in DEPARTEMENTS:
            continue

        print("\t".join([
            champs[CODCDE],
            champs[QTE],              # peut être vide (3 lignes dans le fichier)
            champs[TIMBRECDE],
            champs[VILLECLI],
            departement,
            datcde,
        ]))


if __name__ == "__main__":
    main()

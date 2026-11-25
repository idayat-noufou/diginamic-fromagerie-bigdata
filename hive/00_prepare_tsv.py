#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prépare le fichier qualifié pour Hive et MapReduce : CSV -> TSV.

Pourquoi : 12 lignes de dataw_fro_clean.csv ont un prénom entre guillemets
qui contient des virgules (ex. "Christophe, Quentin, Marianne"). Hive, avec
FIELDS TERMINATED BY ',', ne comprend pas les guillemets : il couperait ces
lignes au mauvais endroit et décalerait toutes les colonnes (code postal,
date, quantité...). Le module csv de Python, lui, sait lire les guillemets.
On réécrit donc le fichier avec des tabulations comme séparateur : aucune
valeur ne contient de tabulation, il n'y a plus d'ambiguïté.

On retire aussi la ligne d'en-tête : Hive et le mapper MapReduce n'ont ainsi
pas à la sauter. L'ordre des 25 colonnes est documenté dans
hive/01_create_external_table.hql.

Même démarche que le script du cours 7-prepare-spotify-tsv.py.

Usage :
    python hive/00_prepare_tsv.py cleaning/dataw_fro_clean.csv hive/data/dataw_fro_clean.tsv
"""

import csv
import os
import sys

NB_COLONNES = 25


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage : python 00_prepare_tsv.py <entree.csv> <sortie.tsv>")
    entree, sortie = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.dirname(sortie) or ".", exist_ok=True)

    lues = ecrites = ecartees = avec_virgule = 0
    with open(entree, "r", encoding="utf-8", newline="") as fin, \
         open(sortie, "w", encoding="utf-8", newline="") as fout:
        lecteur = csv.reader(fin)
        next(lecteur)  # en-tête retiré
        for ligne in lecteur:
            lues += 1
            if len(ligne) != NB_COLONNES:
                ecartees += 1
                print("Ligne ecartee (%d colonnes) : %s" % (len(ligne), ligne),
                      file=sys.stderr)
                continue
            if any("," in valeur for valeur in ligne):
                avec_virgule += 1
            fout.write("\t".join(ligne) + "\n")
            ecrites += 1

    # Messages sans accents : la console Windows les affiche mal.
    print("Lignes lues     : %d" % lues)
    print("Lignes ecrites  : %d" % ecrites)
    print("Lignes ecartees : %d" % ecartees)
    print("Dont lignes avec virgule dans une valeur (sauvees) : %d" % avec_virgule)


if __name__ == "__main__":
    main()

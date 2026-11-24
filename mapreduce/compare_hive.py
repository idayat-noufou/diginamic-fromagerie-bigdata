#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOT 3 - Vérification : le résultat MapReduce est-il identique au résultat Hive ?

Compare, ligne par ligne et dans l'ordre, le top 100 produit par Hive
(export CSV de la requête A) et celui produit par le job MapReduce.

Usage :
    python mapreduce/compare_hive.py exports/lot2a_top100_2006_2010.csv mapreduce/output/top100_mapreduce.tsv
"""

import csv
import sys

COLONNES = ["codcde", "ville", "departement", "date_commande", "somme_quantites", "timbrecde"]


def normaliser(ligne):
    """Mêmes types des deux côtés : '28' et 28, '6.4' et 6.4 sont égaux."""
    codcde, ville, dep, date, somme, timbre = ligne
    return (int(codcde), ville, dep.zfill(2), date, int(somme), float(timbre) if timbre else None)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8", newline="") as f:
        hive = [normaliser([l[c] for c in COLONNES]) for l in csv.DictReader(f)]
    with open(sys.argv[2], encoding="utf-8", newline="") as f:
        mapreduce = [normaliser(l.rstrip("\n").split("\t")) for l in f if l.strip()]

    print("Lignes Hive      : %d" % len(hive))
    print("Lignes MapReduce : %d" % len(mapreduce))
    differences = [(i, h, m) for i, (h, m) in enumerate(zip(hive, mapreduce), 1) if h != m]
    for rang, h, m in differences[:10]:
        print("Rang %d differe :\n  Hive      %s\n  MapReduce %s" % (rang, h, m))
    if not differences and len(hive) == len(mapreduce):
        print("RESULTAT : IDENTIQUES (memes commandes, memes valeurs, meme ordre)")
    else:
        print("RESULTAT : %d difference(s)" % (len(differences) + abs(len(hive) - len(mapreduce))))
        sys.exit(1)


if __name__ == "__main__":
    main()

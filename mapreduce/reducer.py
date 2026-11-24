#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOT 3 - Reducer : requête A recodée en MapReduce streaming.
Top 100 des commandes 2006-2010, départements 53, 61 et 28.

Entrée  : la sortie du mapper, triée par Hadoop sur la clé (codcde) :
          codcde \t qte \t timbrecde \t ville \t departement \t datcde
          Toutes les lignes d'une même commande sont donc consécutives.

Rôle    : deux traitements, équivalents des deux étapes Hive :
  1. GROUP BY : tant que la clé ne change pas, additionner les quantités
     de la commande. timbrecde, ville, département et date sont identiques
     sur toutes les lignes d'une commande : on les garde une seule fois
     (et non additionnés, comme le MAX() de la requête Hive).
  2. ORDER BY + LIMIT : garder les 100 meilleures commandes au fil de
     l'eau dans un tas (heapq), sans stocker toutes les commandes en
     mémoire. Classement : somme des quantités DESC, timbrecde DESC,
     codcde ASC (mêmes critères que Hive).

Le job doit tourner avec UN SEUL reducer (-D mapreduce.job.reduces=1) :
le top 100 est un classement global, il doit voir toutes les commandes.

Sortie  : codcde \t ville \t departement \t date \t somme_quantites \t timbrecde
          (100 lignes, de la meilleure à la moins bonne : mêmes colonnes et
          même ordre que le résultat Hive, pour pouvoir les comparer)
"""

import heapq
import sys

TOP_N = 100


def cle_classement(commande):
    """Plus la clé est grande, meilleure est la commande.
    codcde est pris en négatif pour que le plus petit numéro gagne en cas
    d'égalité. Un timbrecde manquant passe après tous les autres (comme
    les NULL d'un ORDER BY DESC dans Hive)."""
    codcde, _, _, _, somme, timbre = commande
    return (somme, timbre if timbre is not None else float("-inf"), -codcde)


def en_nombre(texte):
    return float(texte) if texte else None


def main():
    top = []                  # tas des TOP_N meilleures commandes
    courante = None           # commande en cours d'agrégation

    def cloturer(commande):
        """Commande terminée : la proposer au top 100."""
        element = (cle_classement(commande), commande)
        if len(top) < TOP_N:
            heapq.heappush(top, element)
        elif element[0] > top[0][0]:      # meilleure que la moins bonne du top
            heapq.heapreplace(top, element)

    for ligne in sys.stdin:
        champs = ligne.rstrip("\n").split("\t")
        if len(champs) != 6:
            continue
        codcde, qte, timbre, ville, departement, datcde = champs
        codcde = int(codcde)
        qte = en_nombre(qte) or 0.0       # quantité vide : ignorée, comme SUM() en SQL

        if courante is not None and courante[0] == codcde:
            courante[4] += qte            # même commande : on cumule
        else:
            if courante is not None:
                cloturer(courante)        # nouvelle clé : la précédente est complète
            courante = [codcde, ville, departement, datcde, qte, en_nombre(timbre)]

    if courante is not None:
        cloturer(courante)                # ne pas oublier la dernière commande

    # Affichage du meilleur au moins bon
    for _, (codcde, ville, departement, datcde, somme, timbre) in sorted(top, reverse=True):
        print("\t".join([str(codcde), ville, departement, datcde,
                         str(int(somme)), "" if timbre is None else str(timbre)]))


if __name__ == "__main__":
    main()

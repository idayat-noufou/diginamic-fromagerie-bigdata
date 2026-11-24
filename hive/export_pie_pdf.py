#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requête B : produit le PDF avec un graphe en secteurs (pie) par ville.

Entrée : le résultat Beeline (csv2) de hive/03_lot2b_2011_2016.hql, soit les
5 commandes tirées au hasard parmi le top 100 (ville, somme_quantites,
moyenne_quantites, codcde, departement, date_commande).

Le PDF contient :
  - à gauche, le camembert : une part par ville, taille = somme des quantités
    d'articles, avec le nom de la ville et la valeur écrits sur chaque part ;
  - à droite, le tableau des commandes tirées (ville, commande, somme,
    moyenne), qui sert aussi de légende (pastille de couleur par ville).
Une copie CSV propre est écrite à côté du PDF (réutilisable par PowerBI).

Dépendances : matplotlib, openpyxl (pip install matplotlib openpyxl)

Usage :
    python hive/export_pie_pdf.py hive/data/lot2b_beeline.csv exports/lot2b_pie_villes_2011_2016.pdf
"""

import csv
import math
import sys
from collections import OrderedDict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # pas de fenêtre : génération directe du fichier
import matplotlib.pyplot as plt

from export_excel import lire_resultat  # même nettoyage des logs Beeline

# Palette catégorielle validée (couleurs distinctes, y compris pour les
# daltoniens), attribuée dans un ordre fixe.
COULEURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
            "#008300", "#6250d6", "#e34948"]
ENCRE = "#1f1f1f"
ENCRE_SECONDAIRE = "#5f5f5f"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    entree, sortie = sys.argv[1], Path(sys.argv[2])
    entete, *lignes = lire_resultat(entree)
    commandes = [dict(zip(entete, l)) for l in lignes]

    # Copie CSV propre
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie.with_suffix(".csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=entete)
        w.writeheader()
        w.writerows(commandes)

    # Somme des quantités par ville (une ville peut avoir plusieurs commandes)
    par_ville = OrderedDict()
    for c in commandes:
        par_ville[c["ville"]] = par_ville.get(c["ville"], 0) + int(c["somme_quantites"])
    villes = sorted(par_ville, key=par_ville.get, reverse=True)
    valeurs = [par_ville[v] for v in villes]
    couleur = {v: COULEURS[i % len(COULEURS)] for i, v in enumerate(villes)}
    total = sum(valeurs)

    fig = plt.figure(figsize=(11.69, 8.27))  # A4 paysage
    fig.patch.set_facecolor("white")
    fig.text(0.05, 0.93, "Requête B — Répartition par ville des commandes tirées au hasard",
             fontsize=17, fontweight="bold", color=ENCRE)
    fig.text(0.05, 0.86,
             "5 % des 100 meilleures commandes 2011-2016, départements 22, 49 et 53, sans timbrecli\n"
             "Taille des parts : somme des quantités d'articles",
             fontsize=10.5, color=ENCRE_SECONDAIRE)

    # Camembert : parts séparées par un liseré blanc, libellés directs
    ax = fig.add_axes([0.30, 0.40, 0.40, 0.42])  # en haut, centré
    parts, _ = ax.pie(
        valeurs, colors=[couleur[v] for v in villes], startangle=90, counterclock=False,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for part, ville, val in zip(parts, villes, valeurs):
        angle = math.radians((part.theta1 + part.theta2) / 2)
        x, y = math.cos(angle), math.sin(angle)
        ax.annotate(
            "%s\n%d articles (%d %%)" % (ville, val, round(100 * val / total)),
            xy=(0.98 * x, 0.98 * y), xytext=(1.25 * x, 1.18 * y),
            ha="left" if x >= 0 else "right", va="center", fontsize=10, color=ENCRE,
            arrowprops={"arrowstyle": "-", "color": ENCRE_SECONDAIRE, "lw": 0.8},
        )
    ax.set_aspect("equal")

    # Tableau des commandes : sert aussi de légende (pastille de couleur)
    axt = fig.add_axes([0.15, 0.10, 0.70, 0.25])  # en bas, pleine largeur
    axt.axis("off")
    corps = [["", c["ville"], c["codcde"], c["date_commande"],
              c["somme_quantites"], c["moyenne_quantites"]]
             for c in sorted(commandes, key=lambda c: -int(c["somme_quantites"]))]
    table = axt.table(
        cellText=corps,
        colLabels=["", "Ville", "Commande", "Date", "Somme des quantités", "Moyenne des quantités"],
        colWidths=[0.03, 0.30, 0.12, 0.14, 0.20, 0.21],
        loc="upper center", cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.6)
    for (r, col), cell in table.get_celld().items():
        cell.set_edgecolor("#dddddd")
        if r == 0:
            cell.set_text_props(fontweight="bold", color=ENCRE)
            cell.set_facecolor("#f2f2f2")
        elif col == 0:
            cell.set_facecolor(couleur[corps[r - 1][1]])
    fig.text(0.05, 0.035,
             "Moyenne des quantités : quantité moyenne par article de la commande. "
             "Tirage aléatoire reproductible (rand avec graine 2026).\n"
             "Source : table Hive fromagerie.commandes — script hive/03_lot2b_2011_2016.hql",
             fontsize=8.5, color=ENCRE_SECONDAIRE)
    fig.savefig(sortie)
    print("PDF -> %s (+ %s)" % (sortie, sortie.with_suffix(".csv").name))


if __name__ == "__main__":
    main()

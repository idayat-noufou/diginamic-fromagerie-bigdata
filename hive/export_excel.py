#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertit un résultat Beeline (format csv2) en fichier Excel mis en forme,
et en écrit aussi une copie CSV propre (réutilisable par PowerBI).

Beeline mélange parfois ses messages de log (Log4j) avec le résultat : ces
lignes sont retirées avant la conversion.

Dépendance : openpyxl  (pip install openpyxl)

Usage :
    python hive/export_excel.py <resultat_beeline.csv> <sortie.xlsx> "<titre de la feuille>"
Exemple :
    python hive/export_excel.py hive/data/lot2a_beeline.csv exports/lot2a_top100_2006_2010.xlsx "Top 100 2006-2010"
"""

import csv
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# Lignes de log Beeline/Log4j à ignorer
LOG = re.compile(r"^(\d{4}-\d{2}-\d{2}T\S+ .*(INFO|WARN|ERROR)|Please remove|See https)")


def lire_resultat(chemin):
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = [l for l in f if l.strip() and not LOG.match(l)]
    return list(csv.reader(lignes))


def typer(valeur):
    """Convertit '42' en 42 et '9.85' en 9.85 pour qu'Excel les traite comme des nombres."""
    for conv in (int, float):
        try:
            return conv(valeur)
        except ValueError:
            pass
    return valeur


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    entree, sortie, titre = sys.argv[1], Path(sys.argv[2]), sys.argv[3][:31]
    entete, *donnees = lire_resultat(entree)

    # Copie CSV propre, sans les logs, avec une colonne rang
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(sortie.with_suffix(".csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rang"] + entete)
        for i, ligne in enumerate(donnees, 1):
            w.writerow([i] + ligne)

    # Classeur Excel
    wb = Workbook()
    ws = wb.active
    ws.title = titre
    ws.append(["rang"] + entete)
    for i, ligne in enumerate(donnees, 1):
        ws.append([i] + [typer(v) for v in ligne])

    # Mise en forme : en-tête coloré, filtres, volet figé, largeurs adaptées
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center")
    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "A2"
    for col in ws.columns:
        largeur = max(len(str(c.value)) for c in col if c.value is not None)
        ws.column_dimensions[get_column_letter(col[0].column)].width = largeur + 3

    wb.save(sortie)
    print("%d lignes exportees -> %s (+ %s)" % (len(donnees), sortie, sortie.with_suffix(".csv").name))


if __name__ == "__main__":
    main()

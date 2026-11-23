"""
ÉTAPE 2 - NETTOYAGE

Corrige les données et met de côté les lignes rejetées.
Les anomalies sont affichées par verification.py ; les règles sont dans config.py.
"""
from config import (load_data, text_columns, remove_accents,
                    parse_dates, compute_motif,
                    COL_DATE, OUTPUT_OK, OUTPUT_REJ)

# ---------------------------------------------------------------
# 1. Chargement
# ---------------------------------------------------------------
df = load_data()
df_clean = df.copy()            

# ---------------------------------------------------------------
# 2. Suppression des accents
# ---------------------------------------------------------------
cols = text_columns(df_clean)
df_clean[cols] = df_clean[cols].apply(lambda col: col.map(remove_accents))

# ---------------------------------------------------------------
# 3. Suppression des doublons exacts (AVANT de calculer motif et dates)
# ---------------------------------------------------------------
n_before = len(df_clean)
df_clean = df_clean.drop_duplicates()                 
n_dup = n_before - len(df_clean)

# ---------------------------------------------------------------
# 4. Mise de côté des lignes rejetées 
# ---------------------------------------------------------------
motif = compute_motif(df_clean)
df_clean["motif_rejet"] = motif
rejet = motif != ""             # True = au moins un motif de rejet

df_rejet = df_clean[rejet]
df_ok    = df_clean[~rejet].drop(columns="motif_rejet")

# Dates conservées stockées comme vraies dates (heure supprimée)
dates = parse_dates(df_clean)
df_ok[COL_DATE] = dates[~rejet].dt.normalize()

# ---------------------------------------------------------------
# 5. Enregistrement
# ---------------------------------------------------------------
df_ok.to_csv(OUTPUT_OK, index=False)
df_rejet.to_csv(OUTPUT_REJ, index=False)

# ---------------------------------------------------------------
# 6. Résumé court de ce qui a été fait
# ---------------------------------------------------------------
print("=== NETTOYAGE FAIT===")
print(f"Lignes lues         : {len(df)}")
print(f"Les doublons ont été supprimés : {n_dup}")
print(f"Lignes conservées  : {len(df_ok)} -> {OUTPUT_OK}")
print(f"Lignes rejetées    : {len(df_rejet)} -> {OUTPUT_REJ}")
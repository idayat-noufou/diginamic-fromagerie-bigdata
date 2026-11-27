"""
ÉTAPE 1 - VÉRIFICATION
Détecte et affiche les anomalies. Ne modifie rien, n'écrit aucun fichier.
À lancer en premier : lire le rapport, ajuster les règles dans config.py si besoin,
puis lancer clean.py.
"""
import pandas as pd
from config import (load_data, accent_mask, parse_dates, compute_motif,
                    null_rule, text_columns, remove_accents,
                    COL_DATE, YEAR_MIN, YEAR_MAX, COLS_NEG_OK, CLE_HBASE)

# Afficher les tableaux en entier (toutes les colonnes, sur une seule largeur)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

df = load_data()
print(f"Données chargées : {len(df)} lignes x {df.shape[1]} colonnes")
print("\nTypes des colonnes :")
print(df.dtypes)

# ---------------------------------------------------------------
# 1. Valeurs NULL
# ---------------------------------------------------------------
nulls = df.isna().sum()
nulls_report = pd.DataFrame({
    "nb_null": nulls,
    "type": df.dtypes,
    "rule": [null_rule(c) for c in df.columns],   # 'to reject' ou 'ok' (voir config.py)
})
nulls_report = nulls_report[nulls_report["nb_null"] > 0]   # seulement les colonnes concernées

print("\n=== VALEURS NULL ===")
print(nulls_report.sort_values("nb_null", ascending=False))
print(f"Lignes contenant au moins une valeur NULL : {df.isna().any(axis=1).sum()} / {len(df)}")

# Détail des NULL non critiques (conservés) : une liste par colonne
print("\n=== DÉTAIL DES NULL NON CRITIQUES (lignes conservées) ===")
for col in ["Colis", "Nbcolis", "qte", "timbrecli", "timbrecde"]:
    lignes = df[df[col].isna()]
    print(f"\n--- {col} : {len(lignes)} lignes ---")
    print(lignes)

# ---------------------------------------------------------------
# 2. Accents / caractères spéciaux
# ---------------------------------------------------------------
row_mask = accent_mask(df)
print("\n=== ACCENTS ===")
print(f"Lignes avec caractères spéciaux : {row_mask.sum()} / {len(df)}")
print(df[row_mask])

# ---------------------------------------------------------------
# 3. Dates
# ---------------------------------------------------------------
dates = parse_dates(df)
invalide   = dates.isna()                                              # vide ou mauvais format
hors_plage = dates.notna() & ~dates.dt.year.between(YEAR_MIN, YEAR_MAX)  # hors période

print("\n=== DATES ===")
print(f"Non valides (vides / format incorrect) : {invalide.sum()}")
print(f"Hors {YEAR_MIN}-{YEAR_MAX} : {hors_plage.sum()}")
print(df.loc[invalide | hors_plage, [COL_DATE]])

# ---------------------------------------------------------------
# 4. Valeurs négatives
# ---------------------------------------------------------------
print("\n=== VALEURS NÉGATIVES ===")
num_cols = df.select_dtypes(include="number").columns
for col in [c for c in num_cols if c not in COLS_NEG_OK]:
    n = (df[col] < 0).sum()
    if n > 0:
        print(f"{col} : {n} valeurs négatives")

# ---------------------------------------------------------------
# 5. Doublons exacts
# ---------------------------------------------------------------
print("\n=== DOUBLONS EXACTS ===")
n_extra = df.duplicated().sum()                       # copies en trop (toutes sauf la première)
print(f"Lignes en double : {n_extra}")

dup = df.duplicated(keep=False)                       # marque TOUTES les copies, original compris
print(df[dup].sort_values(list(df.columns)))          # tri : les copies apparaissent côte à côte

# ---------------------------------------------------------------
# 6. Préparation de la synthèse : mêmes étapes que clean.py, sur une copie
#    (accents -> doublons -> règles de rejet)
# ---------------------------------------------------------------
df_sim = df.copy()
cols = text_columns(df_sim)
df_sim[cols] = df_sim[cols].apply(lambda col: col.map(remove_accents))
n_dup = df_sim.duplicated().sum()          # inclut les doublons masqués par les accents
df_sim = df_sim.drop_duplicates()

motif = compute_motif(df_sim)
rejet = motif != ""

# ---------------------------------------------------------------
# 7. Clés HBase en double (date + commande + objet)
#    Lignes différentes mais de même clé : la 2e écraserait la 1re dans HBase
# ---------------------------------------------------------------
cle_dup = motif.str.contains("doublon_cle_hbase")
print("\n=== CLÉS HBASE EN DOUBLE ===")
print(f"Lignes rejetées pour clé en double : {cle_dup.sum()}")
# Afficher les paires concernées, parmi les lignes valides par ailleurs
valides_sans_cle = motif.str.replace("doublon_cle_hbase;", "") == ""
candidates = df_sim[valides_sans_cle]
paires = candidates[candidates.duplicated(CLE_HBASE, keep=False)].sort_values(CLE_HBASE)
print(paires)

# ---------------------------------------------------------------
# 8. Synthèse : ce que clean.py va faire
# ---------------------------------------------------------------
n_lues = len(df)
n_rejet = rejet.sum()
n_ok = (~rejet).sum()

print("\n=== SYNTHÈSE (ce que clean.py va faire) ===")
print(f"Lignes lues                     : {n_lues}")
print(f"Lignes avec accents à nettoyer  : {row_mask.sum()}")
print(f"Doublons exacts à supprimer     : {n_dup}")
print(f"Doublons Hbase                  : {cle_dup.sum()}")
print(f"Lignes rejetées                 : {n_rejet} ({n_rejet / n_lues:.1%})")
print(f"Lignes conservées               : {n_ok}")


print("\nRejets par motif :")
# Une ligne peut avoir plusieurs motifs : on les sépare avant de compter
print(motif.str.split(";").explode().loc[lambda s: s != ""].value_counts())
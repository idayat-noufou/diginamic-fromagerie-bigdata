"""
ÉTAPE 1 - VÉRIFICATION
Détecte et affiche les anomalies. 

À lancer en premier : lire le rapport, ajuster les règles dans config.py si besoin,
puis lancer clean.py.
"""


import pandas as pd
from config import (load_data, accent_mask, parse_dates, compute_motif,
                    null_rule, text_columns, remove_accents,
                    COL_DATE, YEAR_MIN, YEAR_MAX, COLS_NEG_OK)

df = load_data()
print(f"Data loaded: {len(df)} rows x {df.shape[1]} columns")

# ---------------------------------------------------------------
# 1. Valeurs NULL
# ---------------------------------------------------------------
nulls = df.isna().sum()
nulls_report = pd.DataFrame({
    "nb_null": nulls,
    "type": df.dtypes,
    "rule": [null_rule(c) for c in df.columns],   # 'to reject' ou 'ok' 
})
nulls_report = nulls_report[nulls_report["nb_null"] > 0]   # seulement les colonnes concernées

print("\n=== NULL VALUES ===")
print(nulls_report.sort_values("nb_null", ascending=False))
print(f"Lignes contenant au moins une valeur NULL: {df.isna().any(axis=1).sum()} / {len(df)}")


# ---------------------------------------------------------------
# 2. Accents / caractères spéciaux
# ---------------------------------------------------------------
row_mask = accent_mask(df)
print("\n=== ACCENTS ===")
print(f"Lignes avec caractères spéciaux: {row_mask.sum()} / {len(df)}")
print(df[row_mask])

# ---------------------------------------------------------------
# 3. Dates
# ---------------------------------------------------------------
dates = parse_dates(df)
invalide   = dates.isna()                                              
hors_plage = dates.notna() & ~dates.dt.year.between(YEAR_MIN, YEAR_MAX)  

print("\n=== DATES ===")
print("Non valide (vide / format incorrect)", invalide.sum())
print(f"Outside {YEAR_MIN}-{YEAR_MAX}:", hors_plage.sum())
print(df.loc[invalide | hors_plage, [COL_DATE]])

# ---------------------------------------------------------------
# 4. Valeurs négatives
# ---------------------------------------------------------------
print("\n=== NEGATIVE VALUES ===")
num_cols = df.select_dtypes(include="number").columns
for col in [c for c in num_cols if c not in COLS_NEG_OK]:
    n = (df[col] < 0).sum()
    if n > 0:
        print(f"{col}: {n} negative")

# ---------------------------------------------------------------
# 5. Doublons
# ---------------------------------------------------------------
print("\n=== EXACT DUPLICATES ===")

n_extra = df.duplicated().sum()                      
print(f"Lignes en double: {n_extra}")

dup = df.duplicated(keep=False)                       
print(df[dup].sort_values(list(df.columns)))          

# ---------------------------------------------------------------
# 6. Synthèse : ce que clean.py va faire
# # ---------------------------------------------------------------
df_sim = df.copy()
cols = text_columns(df_sim)
df_sim[cols] = df_sim[cols].apply(lambda col: col.map(remove_accents))
n_dup = df_sim.duplicated().sum()          # inclut les doublons masqués par les accents
df_sim = df_sim.drop_duplicates()

motif = compute_motif(df_sim)
rejet = motif != ""

print("\n=== SUMMARY (what clean.py will do) ===")
print(f"Lignes lues                  : {len(df)}")
print(f"Lignes avec accents à nettoyer : {row_mask.sum()}")
print(f"Lignes en double à supprimer       : {n_dup}")
print(f"Lignes rejetées : {rejet.sum()}")
print(f"Lignes conservées     : {(~rejet).sum()}")
print("\nRejets par raison:")
# Une ligne peut avoir plusieurs motifs : on les sépare avant de compter
print(motif.str.split(";").explode().loc[lambda s: s != ""].value_counts())


print(df.dtypes)

print("\n=== NULL VALUES details ===")

print("\n=== colis ===")
with pd.option_context("display.max_columns", None, "display.width", None):
    print(df[df["Colis"].isna()])
  
print("\n=== nbcolis ===")   
with pd.option_context("display.max_columns", None, "display.width", None):
    print(df[df["Nbcolis"].isna()])
    
print("\n=== qte ===")      
with pd.option_context("display.max_columns", None, "display.width", None):
    print(df[df["qte"].isna()])

print("\n=== timbrecli ===")    
with pd.option_context("display.max_columns", None, "display.width", None):
    print(df[df["timbrecli"].isna()])
    
print("\n=== timbrecde ===")       
with pd.option_context("display.max_columns", None, "display.width", None):
    print(df[df["timbrecde"].isna()])
    
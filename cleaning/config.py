"""
Paramètres et fonctions partagés, utilisés par verification.py et clean.py.
"""
import pandas as pd
import unicodedata

# ---------------------------------------------------------------
# 1. Files
# ---------------------------------------------------------------
INPUT_FILE  = "dataw_fro03.csv"
OUTPUT_OK   = "dataw_fro_clean.csv"
OUTPUT_REJ  = "dataw_fro_rejets.csv"
CLE_HBASE = ["datcde", "codcde", "codobj"]

def load_data():
    """Lit le fichier brut (codes postaux lus comme texte pour garder les zéros initiaux)."""
    
    return pd.read_csv(INPUT_FILE, dtype={"cpcli": "str"})

# ---------------------------------------------------------------
# 2. Rules
# ---------------------------------------------------------------
COL_DATE    = "datcde"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
YEAR_MIN, YEAR_MAX = 2000, 2026

# # Règles pour les colonnes numériques (par défaut : valeur négative -> rejet)

COLS_NEG_OK  = ["points"]      # # valeurs négatives autorisées

# Règles pour les valeurs NULL (par défaut : NULL autorisé -> ligne conservée)

COLS_NULL_KO = ["points", "datcde"]      # NULL interdit -> ligne rejetée
COLS_NULL_OK = ["cheqcli"]     # NULL autorisé 

# Contrôle de cohérence : une colonne ne peut pas être dans les deux listes NULL
conflict = set(COLS_NULL_KO) & set(COLS_NULL_OK)
if conflict:
    raise ValueError(f"Columns in both COLS_NULL_KO and COLS_NULL_OK: {conflict}")

# ---------------------------------------------------------------
# 3. Accents
# ---------------------------------------------------------------
PATTERN = r"[^\x00-\x7F]"      # tout caractère hors ASCII de base

# Lettres qui ne sont pas « lettre + accent » en Unicode : remplacement manuel
SPECIAL_CHARS = {
    'ß': 'ss',
    'æ': 'ae', 'Æ': 'AE',
    'œ': 'oe', 'Œ': 'OE',
    'ø': 'o',  'Ø': 'O',
    'ł': 'l',  'Ł': 'L',
    'đ': 'd',  'Đ': 'D',
}

def remove_accents(s):
    """Convertit les caractères accentués / spéciaux en lettres ASCII simples."""
    if not isinstance(s, str):          # nombres, NaN, None : inchangés
        return s
    for char, replacement in SPECIAL_CHARS.items():
        s = s.replace(char, replacement)
    decomposed = unicodedata.normalize("NFKD", s)      
    return "".join(c for c in decomposed if not unicodedata.combining(c))  

def text_columns(df):
    """Renvoie les colonnes de type texte."""
    return df.select_dtypes(include=["object", "string"]).columns

def accent_mask(df):
    """True pour chaque ligne contenant au moins un caractère spécial."""
    cols = text_columns(df)
    cell_mask = df[cols].apply(
        lambda col: col.str.contains(PATTERN, regex=True, na=False)
    )
    return cell_mask.any(axis=1)

# ---------------------------------------------------------------
# 4. Règles NULL
# ---------------------------------------------------------------
def null_rule(col):
    """Renvoie la règle NULL d'une colonne : 'to reject' ou 'ok'."""
    return "to reject" if col in COLS_NULL_KO else "ok"

# ---------------------------------------------------------------
# 5. Contrôles de rejet (dates, négatifs, NULL interdits)
# ---------------------------------------------------------------
def parse_dates(df):
    """Convertit la colonne date ; format incorrect / date impossible -> NaT."""
    return pd.to_datetime(df[COL_DATE], format=DATE_FORMAT, errors="coerce")

def compute_motif(df):
    """
    Renvoie, pour chaque ligne, un texte listant les motifs de rejet
    ("" = ligne correcte). Ne modifie PAS df.
    """
    motif = pd.Series("", index=df.index)

    # Dates
    dates = parse_dates(df)
    invalide   = dates.isna()                                             
    hors_plage = dates.notna() & ~dates.dt.year.between(YEAR_MIN, YEAR_MAX)  
    motif += invalide.map({True: "date_invalide;", False: ""})
    motif += hors_plage.map({True: "date_hors_plage;", False: ""})

    # Négatifs : toutes les colonnes numériques sauf celles autorisées
    num_cols = df.select_dtypes(include="number").columns
    for col in [c for c in num_cols if c not in COLS_NEG_OK]:
        negatif = df[col] < 0
        motif += negatif.map({True: f"{col}_negatif;", False: ""})

    # NULL interdits
    for col in COLS_NULL_KO:
        vide = df[col].isna()
        motif += vide.map({True: f"{col}_vide;", False: ""})
    
    # Clé HBase en double (date + commande + objet) : la 2e ligne écraserait la 1re.
    valides = motif == ""
    doublon_cle = df[valides].duplicated(CLE_HBASE).reindex(df.index, fill_value=False)
    motif += doublon_cle.map({True: "doublon_cle_hbase;", False: ""})

    return motif
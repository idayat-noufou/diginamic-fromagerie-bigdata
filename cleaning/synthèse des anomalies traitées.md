# Contrôle qualité et nettoyage – `dataw_fro03.csv`

Ce projet vérifie la qualité du fichier de commandes `dataw_fro03.csv`, corrige ce qui peut l'être et met de côté les lignes inexploitables, avec le motif du rejet.

## Fichiers

| Fichier | Rôle |
|---|---|
| `config.py` | Paramètres (noms de fichiers, règles) et fonctions partagées | 
| `verification.py` | **Étape 1** : détecte et affiche les anomalies, prévoit le résultat du nettoyage | 
| `clean.py` | **Étape 2** : corrige, rejette, enregistre les deux fichiers de sortie | 

Les règles ne sont écrites qu'une seule fois, dans `config.py`. Les deux scripts appellent les mêmes fonctions 

## Synthèse des anomalies traitées

### Anomalies corrigées (la ligne est conservée)

| Anomalie | Détection | Traitement |
|---|---|---|
| **Accents et caractères spéciaux** (`é`, `ï`, `ß`, `æ`, `ø`…) dans les colonnes texte | Tout caractère hors ASCII de base (`[^\x00-\x7F]`) | Conversion en lettres simples : `é → e`, `ß → ss`, `æ → ae`… (décomposition Unicode NFKD + table `SPECIAL_CHARS`) |
| **Doublons exacts** (lignes identiques sur toutes les colonnes) | `df.duplicated()` | Suppression des copies en trop, la première est conservée. Faite **après** la suppression des accents, ce qui élimine aussi les doublons masqués par un accent (`Lefèvre` / `Lefevre`) |
| **Codes postaux** lus comme nombres (`01000 → 1000`) | Prévention dès la lecture | `cpcli` est lu comme texte, les zéros initiaux sont conservés |
| **Dates stockées comme texte** (`2021-07-26 00:00:00`) | – | Les dates conservées deviennent de vraies dates, sans l'heure |

### Anomalies rejetées (la ligne part dans le fichier de rejets)

| Motif dans `motif_rejet` | Règle | Colonnes concernées |
|---|---|---|
| `date_invalide` | Date vide, mal écrite (format attendu `AAAA-MM-JJ HH:MM:SS`) ou impossible (ex. 30 février) | `datcde` |
| `date_hors_plage` | Date valide mais en dehors de `2000`–`2026` | `datcde` |
| `<colonne>_negatif` | Valeur négative | Toutes les colonnes numériques **sauf** `points` |
| `<colonne>_vide` | Valeur NULL interdite | `points`, `datcde` |

Une ligne peut cumuler plusieurs motifs, par exemple `date_hors_plage;qte_negatif;`.

### Signalées, mais ni corrigées ni rejetées

- **Valeurs NULL dans les autres colonnes** (`cheqcli`, `qte`, `Colis`…) : autorisées et conservées. Le rapport de vérification indique leur nombre par colonne.
- **Valeurs négatives dans `points`** : autorisées.

# Le rapport de vérification détaillé peut être obtenu avec la commande`python verification.py > rapport_anomalies_traitées.txt`


## Fichiers produits par `clean.py`

| Fichier | Contenu |
|---|---|
| `dataw_fro03_clean.csv` | Lignes valides et nettoyées, prêtes à l'emploi |
| `dataw_fro03_rejets.csv` | Lignes rejetées, avec une colonne supplémentaire `motif_rejet` |



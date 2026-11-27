# 1. Source et chargement

| Élément                          | Valeur                                            |
| -------------------------------- | ------------------------------------------------- |
| Source                           | `dataw_fro_clean.csv` (fichier qualifié du LOT 0) |
| Outil                            | Python + happybase, via Thrift (`localhost:9090`) |
| Table                            | `fromagerie`, familles `client` et `order`        |
| Lignes dans le CSV qualifié      | 134 945                                           |


Scripts : `01_create_table.py` (création, supprime et recrée la table), `02_load.py` (chargement par paquets de 5 000). Le CSV est lu avec le module `csv`, qui comprend les guillemets : les 12 lignes dont le prénom contient des virgules sont lues correctement, sans conversion en TSV.

# 2. Schéma et rowkey

Une ligne HBase = une ligne du CSV = un article d'une commande.

**Rowkey : `datcde_codcde_codobj`**, avec la date au format `AAAAMMJJ`. Exemple : `20041022_00000478_000038`.

| Choix                         | Raison                                                                                                                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Date en tête                  | Les clés sont triées par HBase : les scripts des questions 1 et 2 lisent une année (`row_prefix=b'2020'`) ou une plage (2010 à 2015) sans parcourir toute la table |
| `codcde` + `codobj`           | Une clé par article d'une commande                                                                                                                                 |
| Codes complétés par des zéros | Pour le trisinon `478` passerait après `21239`                                                                                                                     |

|Famille|Colonnes|
|---|---|
|`client`|codcli, nom, prénom, ville, cp|
|`order`|codcde, datcde, timbrecde, codobj, qte, libobj|


# 3. Les trois requêtes

| Question                                        | Méthode                                                                                                                                    | Résultat                                                                                                | Export            |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ----------------- |
| **Q1** Meilleure commande de Nantes en 2020     | Scan `row_prefix=b'2020'`, filtre `NANTES`, somme des quantités par commande ; meilleure = plus grande somme, puis plus grand `timbrecde`  | Commande n° **85301**, le 2020-01-08, **6 articles**, `timbrecde` **3,05**                              | CSV               |
| **Q2** Commandes 2010-2015 par année            | Scan de `2010` à `2016` (exclu), comptage des `codcde` distincts par année                                                                 | 2010 : **5 592** ; 2011 : 4 878 ; 2012 : 3 970 ; 2013 : 3 622 ; 2014 : 3 814 ; 2015 : 3 748             | Barplot PDF + CSV |
| **Q3** Client avec le plus de frais `timbrecde` | Scan complet, `timbrecde` pris une fois par commande, regroupement par client                                                              | **Nicole CROTTE** (client 786) : **57 commandes**, **142 articles**, **303,40** de frais de `timbrecde` | Excel + CSV       |

# 4. Les deux précautions clés

**`timbrecde` une seule fois par commande.** Le montant est répété sur chaque ligne d'une commande (une ligne par article). Un simple total le compterait autant de fois que la commande a d'article donc le script ne le prend qu'une fois par commande.

**Les valeurs vides.** Certains `timbrecde` sont vides (NULL conservés au LOT 0 car non critiques). Un `float('')` plante : la décision de l'équipe est de les remplacer par 0, et une petite fonction de conversion l'applique dans les scripts.

# 5. Livrables

`01_create_table.py`, `02_load.py`, `03_query1_nantes_2020.py`, `04_query2_commandes_par_annee.py`, `05_query3_client_max_timbrecde.py`, `06_export_lignes.py` (export complet pour PowerBI), ; exports `q1_nantes_2020.csv`, `q2_commandes_par_annee.pdf` et `.csv`, `q3_client_max_timbrecde.xlsx` et `q3_client_timbrecde.csv`, `lignes.csv`.

> info
> Pour plus de détail, voir [hbase/demarche.md](/hbase/demarche.md)

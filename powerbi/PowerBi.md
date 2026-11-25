
## 1. Sources

Toutes les données du dashboard viennent de la chaîne Big Data du projet, exportées en CSV :

| Fichier | Origine | Contenu |
|---|---|---|
| `lignes.csv` | **HBase** — scan complet de la table `fromagerie` (happybase → pandas) | 134 926 lignes de commande : 70 819 commandes, 29 727 clients, 114 objets (2004–2021) |
| `q1_meilleure_commande_nantes_2020.csv` | **HBase** — requête Q1 (LOT 4) | Meilleure commande de Nantes en 2020 |
| `q2_commandes_par_annee.csv` | **HBase** — requête Q2 (LOT 4) | Nombre de commandes par année, 2010–2015 |
| `q3_client_timbrecde.csv` | **HBase** — requête Q3 (LOT 4) | Client ayant payé le plus de frais de timbre |
| `hive_lot2a_top100_commandes_2006_2010.csv` | **Hive** — besoin A (LOT 2) | Top 100 des commandes 2006–2010, départements 28, 53, 61 |
| `hive_lot2b_echantillon5_commandes_2011_2016.csv` | **Hive** — besoin B (LOT 2) | Échantillon aléatoire de 5 commandes du top 100 2011–2016 |
| `mapreduce_lot3_top100_commandes_2006_2010.csv` | **MapReduce** — LOT 3 | Top 100 du besoin A recalculé en MapReduce |

## 2. Connexion

Nous avons utilisé **l'alternative prévue par l'énoncé : des fichiers CSV** chargés via *Obtenir les données → Texte/CSV*, au lieu d'une connexion ODBC directe à HBase.

## 3. Modèle et relations

Le fichier source est un datawarehouse « à plat » : une ligne par objet commandé, avec les informations du client et de la commande répétées. Nous l'avons réorganisé en **schéma en étoile** :

- **Table de faits** : `lignes`.
- **Dimensions**, créées dans Power Query à partir de `lignes` (*Référence* → colonnes utiles → suppression des doublons sur la clé) :
  - `Clients` (codcli, nom, prénom, cp, ville, département) ;
  - `Objects` (codobj, libobj).
- **Calendrier**, en DAX : une ligne par jour de 2004 à 2021, avec l'année et le mois.

| Relation | Cardinalité | Filtre |
|---|---|---|
| `Clients[codcli]` → `lignes[codcli]` | 1 → plusieurs | simple |
| `Objects[codobj]` → `lignes[codobj]` | 1 → plusieurs | simple |
| `Calendrier[Date]` → `lignes[datcde]` | 1 → plusieurs | simple |
| `Top100_A[codcde]` → `lignes[codcde]` | 1 → plusieurs | simple |
| `Echantillon_B[codcde]` → `lignes[codcde]` | 1 → plusieurs | simple |
| `q3_client_timbrecde[codcli]` → `lignes[codcli]` | 1 → plusieurs | simple |

Les relations depuis `Top100_A` et `Echantillon_B` permettent d'afficher les objets d'une commande en cliquant dessus ; celle depuis `q3_client_timbrecde` permet d'afficher les commandes du client trouvé en Q3. Les tables Q1, Q2 et le top 100 MapReduce sont des résultats déjà calculés : elles sont affichées telles quelles, sans relation.

**Filtres des pages de résultats.** Les tables de résultats ne sont pas reliées à `Calendrier` ni à `Clients` : une telle relation créerait un second chemin vers `lignes` (par exemple `Calendrier → Top100_A → lignes`), ce que PowerBI refuse comme une ambiguïté. Nous avons donc ajouté une colonne `annee` à ces tables dans Power Query (*Ajouter une colonne → Date → Année* sur la date de commande). Les pages LOT 2 ont leurs propres segments `annee` et `departement`, construits sur ces colonnes. Les segments synchronisés `Calendrier[Annee]` et `Clients[departement]` sont réservés aux pages construites sur `lignes`.

![Vue Modèle de PowerBI](powerbi\captures\Screenshot 2026-11-25 140754.png)

## 4. Mesure clé : « Frais timbre »

```dax
Frais timbre = SUMX(VALUES(lignes[codcde]), CALCULATE(MAX(lignes[timbrecde])))
```

`timbrecde` est un montant **par commande**, mais il est répété sur **chaque ligne** de la commande (une ligne par objet). Un simple `SUM(lignes[timbrecde])` compterait donc ce montant autant de fois que la commande contient d'objets : une commande de 3 objets à 4,80 € donnerait 14,40 € au lieu de 4,80 €.

La mesure parcourt chaque commande **une seule fois** (`VALUES(lignes[codcde])`), prend son montant (`MAX`, toutes les lignes ayant la même valeur), puis additionne. C'est la même logique que dans le script de la requête Q3 du LOT 4.

Autres mesures :

```dax
Nb commandes = DISTINCTCOUNT(lignes[codcde])
Nb clients   = DISTINCTCOUNT(lignes[codcli])
Quantité     = SUM(lignes[qte])
```

**Contrôle de cohérence :** filtré sur 2010, `Nb commandes` donne 5 592, comme la requête Q2 exécutée sur HBase.

## 5. La saisonnalité des commandes

Une **matrice** croise les années (`Calendrier[Annee]`, en lignes) et les mois (`Calendrier[Mois]`, en colonnes), avec la mesure `Nb commandes` en valeurs. Une **mise en forme conditionnelle** (couleur d'arrière-plan en dégradé) colore chaque case selon le nombre de commandes : plus la case est foncée, plus le mois est fort.

La matrice ne s'appuie que sur le modèle (table `Calendrier` reliée à `lignes`) : elle ne demande aucun export supplémentaire. Elle est filtrée sur **2006–2020**, les seules années complètes : 2004 et 2005 ne comptent que quelques commandes, et 2021 s'arrête en juillet.

Ce que l'on y lit :
- **janvier** est le mois le plus fort sur la période, **avril et mai** les plus faibles (environ 25 % de commandes en moins) ;
- des **pics ponctuels** ressortent, qui ressemblent à des opérations commerciales : juin–juillet 2008, août 2009 et août 2010 ;
- le volume mensuel **baisse progressivement**, d'environ 500 à 900 commandes par mois en 2006–2008 à environ 200 à 350 en 2020.

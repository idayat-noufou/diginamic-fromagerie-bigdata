# Démarche Hive et MapReduce (LOT 2 et LOT 3)

Ce document retrace, étape par étape, ce qui a été fait pour les LOTs 2 (Hive) et 3 (MapReduce).
Il sert de base au support de soutenance : chaque étape indique son objectif, les commandes
lancées, le résultat obtenu, et les captures d'écran à prendre pour les diapositives
(repérées par 📸).

## Environnement technique

| Composant | Version | Rôle dans le projet |
|---|---|---|
| Hadoop (HDFS + YARN) | 3.3.6 | Stockage distribué des fichiers et exécution des jobs MapReduce |
| Hive | 4.1.0 | Requêtes SQL (HiveQL) sur les fichiers stockés dans HDFS |
| Python | 3.11.2 (conteneur) | Mapper et reducer MapReduce streaming |
| Java | OpenJDK 17 | Moteur d'exécution de Hadoop et Hive |
| Docker | Desktop, backend WSL2 | Cluster local : 1 master + 2 slaves |

Le cluster tourne sur le poste en local, à partir du dépôt du cours
[DiginamicAcademy/Hadoop](https://github.com/DiginamicAcademy/Hadoop).

---

## Étape 1 : démarrer le cluster Hadoop

**Objectif.** Hive et MapReduce ont besoin d'un cluster Hadoop en marche : HDFS pour stocker les
données, YARN pour exécuter les traitements, HiveServer2 pour recevoir les requêtes SQL.

**Choix.** Seuls le master et les deux slaves sont démarrés. Le conteneur NiFi n'est pas lancé,
car le LOT 1 n'est pas réalisé par le groupe : cela économise environ 1 Go de RAM.

**Commandes** (depuis le dossier du dépôt `Hadoop` du cours) :

```bash
# 1. Démarrer les conteneurs (master + 2 slaves, sans NiFi)
docker compose up -d master slave1 slave2

# 2. Démarrer les services Hadoop dans le master, dans l'ordre :
#    ZooKeeper, HDFS, YARN, JobHistory, HBase, Thrift, REST, HiveServer2
docker exec -it hadoop-master bash
./start-all.sh
```

**Vérifications** (dans le conteneur master) :

```bash
jps                                          # liste des processus Java lancés
hdfs dfsadmin -report | grep "Live datanodes" # nombre de nœuds de stockage actifs
beeline -u jdbc:hive2://localhost:10000 -e "SELECT version();"
```

**Résultat.**

- `jps` affiche les services du master : NameNode, SecondaryNameNode, ResourceManager,
  JobHistoryServer, HMaster, ThriftServer, RESTServer, QuorumPeerMain (ZooKeeper) et RunJar
  (HiveServer2).
- HDFS compte **2 datanodes actifs** : `hadoop-slave1` et `hadoop-slave2`.
- Beeline se connecte à HiveServer2 et renvoie la version **Hive 4.1.0**.

**Architecture du cluster :**

| Conteneur | Rôle | Services principaux |
|---|---|---|
| `hadoop-master` | Nœud maître | NameNode (HDFS), ResourceManager (YARN), HiveServer2, HMaster |
| `hadoop-slave1` | Nœud de travail | DataNode (stockage), NodeManager (calcul) |
| `hadoop-slave2` | Nœud de travail | DataNode (stockage), NodeManager (calcul) |

📸 **Capture (facultative) :** l'interface du NameNode sur <http://localhost:9870>, onglet
**Datanodes**, avec les 2 slaves « In service ». Elle peut illustrer la diapositive
d'architecture ; sinon le tableau ci-dessus suffit.

---

## Étape 2 : déposer les données dans HDFS

**Objectif.** Hive ne lit pas les fichiers du PC : il lit ceux qui sont stockés dans HDFS, le
système de fichiers distribué du cluster. Il faut donc y déposer le fichier qualifié produit au
LOT 0 (`cleaning/dataw_fro_clean.csv`).

### Problème détecté : des virgules dans les prénoms

En contrôlant le fichier avant l'import, 12 lignes présentent 26 ou 27 colonnes au lieu de 25.
La cause : le champ `prenomcli` contient parfois plusieurs prénoms séparés par des virgules,
entourés de guillemets.

```text
17466,,FONTAINE,"Christophe, Quentin, Marianne",53000,LAVAL,20686,2006-09-12,...
```

Le format texte par défaut de Hive (`FIELDS TERMINATED BY ','`) ne gère pas les guillemets : il
couperait ces lignes à chaque virgule et décalerait toutes les colonnes suivantes (code postal,
date, quantités). Plusieurs de ces lignes tombent dans le périmètre de la requête A
(Laval 2006, Mantilly 2007), le résultat aurait donc été faussé.

**Solution retenue : convertir le CSV en TSV**, c'est-à-dire avec des tabulations comme séparateur.
Le script [`hive/00_prepare_tsv.py`](../hive/00_prepare_tsv.py) lit le CSV avec le module `csv` de
Python, qui comprend les guillemets, puis réécrit chaque ligne séparée par des tabulations.
Aucune valeur ne contient de tabulation, il n'y a donc plus d'ambiguïté. L'en-tête est retiré
pour que ni Hive ni le mapper MapReduce n'aient à le sauter. C'est la même démarche que celle du
cours pour le fichier Spotify (`7-prepare-spotify-tsv.py`).

Alternative écartée : le `OpenCSVSerde` de Hive sait lire les guillemets, mais il type toutes les
colonnes en `STRING`. Il aurait fallu des conversions (`CAST`) dans chaque requête. Le TSV garde
des colonnes typées, et il simplifie aussi le mapper MapReduce.

### Commandes

Sur le PC, depuis la racine du projet (PowerShell) :

```powershell
# Conversion CSV -> TSV
python hive/00_prepare_tsv.py cleaning/dataw_fro_clean.csv hive/data/dataw_fro_clean.tsv

# Copie du fichier dans le conteneur master
docker cp hive/data/dataw_fro_clean.tsv hadoop-master:/tmp/

# Ouverture d'un shell dans le master
docker exec -it hadoop-master bash
```

Dans le conteneur master :

```bash
hdfs dfs -mkdir -p /data/fromagerie/commandes
hdfs dfs -put /tmp/dataw_fro_clean.tsv /data/fromagerie/commandes/
hdfs dfs -ls -h /data/fromagerie/commandes
```

### Résultat

| Contrôle | Valeur |
|---|---|
| Lignes lues dans le CSV (hors en-tête) | 134 945 |
| Lignes écrites dans le TSV | 134 945, toutes à 25 colonnes |
| Lignes sauvées par la conversion | 12 |
| Fichier dans HDFS | `/data/fromagerie/commandes/dataw_fro_clean.tsv`, 18,7 Mo |
| Lignes relues depuis HDFS (`hdfs dfs -cat … \| wc -l`) | 134 945 |
| Stockage | 1 bloc (taille de bloc 128 Mo), réplication 1, stocké sur `hadoop-slave2` |

**Remarque sur la réplication.** Le cluster du cours est configuré avec un facteur de
réplication de 1 : chaque bloc n'existe qu'en un seul exemplaire. C'est suffisant pour un poste
de développement, mais en production on utilise un facteur de 3, afin de ne perdre aucune
donnée si un nœud tombe en panne. Le fichier, plus petit qu'un bloc, n'est pas découpé.

📸 **Capture :** interface du NameNode (<http://localhost:9870>, *Utilities → Browse the file
system*), avec le détail du fichier : son bloc et le datanode qui le stocke.

---

## Étape 3 : créer la table externe Hive

**Objectif.** Décrire à Hive la structure du fichier déposé dans HDFS (colonnes, types,
séparateur, emplacement) pour pouvoir l'interroger en SQL.

**Table externe ou table gérée ?** Une table **externe** (`CREATE EXTERNAL TABLE … LOCATION`)
n'enregistre que la définition dans le metastore de Hive : les données restent dans le fichier
HDFS, sans copie. Supprimer la table (`DROP TABLE`) efface la définition mais pas le fichier.
C'est le bon choix quand les données sont produites en amont, ici par le LOT 0, et peuvent
servir à d'autres outils, comme le job MapReduce du LOT 3.

**Script :** [`hive/01_create_external_table.hql`](../hive/01_create_external_table.hql)

### Choix de modélisation

| Choix | Raison |
|---|---|
| Base `fromagerie`, table `commandes` | Isoler le projet des bases des TP |
| `FIELDS TERMINATED BY '\t'` | Le fichier a été converti en TSV à l'étape 2 |
| `cpcli` en `STRING` | Garder les zéros initiaux des codes postaux ; le département s'obtient par `substr(cpcli, 1, 2)` |
| `datcde` en `DATE` | Le format `AAAA-MM-JJ` est lu nativement ; permet `year(datcde)` |
| `qte`, `timbrecde`, `timbrecli` en `DOUBLE` | Le fichier écrit `2.0` et non `2` : un type `INT` aurait lu ces valeurs comme NULL |
| `serialization.null.format = ''` | Une valeur vide est lue comme NULL, y compris pour le texte : « non renseigné » est traité de la même façon partout |
| Commentaires de colonnes sans accents | Le metastore Derby du cluster affiche mal les caractères accentués |

**Granularité des données.** Une ligne correspond à un article d'une commande. Une commande
(`codcde`) occupe donc plusieurs lignes, sur lesquelles les informations de la commande (client,
ville, date, `timbrecde`) sont répétées. Il faudra en tenir compte dans les agrégations : on
additionne `qte`, mais on ne prend `timbrecde` qu'une fois par commande.

### Commandes

```powershell
docker cp hive/01_create_external_table.hql hadoop-master:/tmp/
docker exec -it hadoop-master bash
```

```bash
beeline -u jdbc:hive2://localhost:10000 -f /tmp/01_create_external_table.hql
```

### Résultat des contrôles

| Contrôle | Résultat | Attendu |
|---|---|---|
| Nombre de lignes | 134 945 | 134 945 lignes dans le fichier qualifié |
| Nombre de commandes distinctes | 70 819 | Environ 1,9 article par commande |
| Période couverte | 2004-10-22 → 2021-07-26 | Datawarehouse « depuis 2004 » |
| Dates NULL | 0 | Aucune date mal typée |
| Quantités NULL | 3 | Les 3 quantités vides du fichier source |
| Lignes à prénoms multiples | 12, colonnes correctement alignées | Correction de l'étape 2 validée |

📸 **Capture :** sortie Beeline de la requête de contrôle sur les prénoms contenant des virgules
(12 lignes bien alignées), éventuellement accompagnée du tableau nombre de commandes / période.

---

## Étape 4 : requête A, top 100 des commandes 2006-2010 (départements 53, 61, 28)

**Besoin client.** Ressortir les 100 meilleures commandes de 2006 à 2010 pour les départements
53 (Mayenne), 61 (Orne) et 28 (Eure-et-Loir), avec la ville, la somme des quantités d'articles
et la valeur de `timbrecde`, puis exporter le résultat dans un fichier Excel.

**Définition retenue de la « meilleure commande ».** Un tri à deux niveaux :

1. la plus grande somme des quantités d'articles ;
2. en cas d'égalité, le plus grand `timbrecde`.

Le numéro de commande sert de troisième critère, uniquement pour rendre le classement
déterministe (voir plus bas).

**Script :** [`hive/02_lot2a_2006_2010.hql`](../hive/02_lot2a_2006_2010.hql)

```sql
SELECT codcde, villecli AS ville, substr(cpcli, 1, 2) AS departement, datcde AS date_commande,
       CAST(SUM(qte) AS INT) AS somme_quantites,
       MAX(timbrecde)        AS timbrecde
FROM commandes
WHERE year(datcde) BETWEEN 2006 AND 2010
  AND substr(cpcli, 1, 2) IN ('53', '61', '28')
GROUP BY codcde, villecli, substr(cpcli, 1, 2), datcde
ORDER BY somme_quantites DESC, timbrecde DESC, codcde ASC
LIMIT 100;
```

### Points clés de la requête

| Élément | Explication |
|---|---|
| `GROUP BY codcde` | Une ligne du fichier correspond à un article : on regroupe pour obtenir une ligne par commande |
| `SUM(qte)` | Somme des quantités de tous les articles de la commande |
| `MAX(timbrecde)` et non `SUM` | `timbrecde` est répété sur chaque ligne de la commande. Un `SUM` le multiplierait par le nombre d'articles. Un contrôle préalable a vérifié que ville, date, client et `timbrecde` sont identiques sur toutes les lignes d'une même commande (0 incohérence sur 70 819 commandes). |
| `substr(cpcli, 1, 2)` | Le département n'existe pas comme colonne : ce sont les 2 premiers caractères du code postal |
| `year(datcde)` | Possible car `datcde` est typée `DATE` |
| `codcde ASC` en dernier critère | Rend le classement stable (voir ci-dessous) |

### Exécution : Hive génère du MapReduce

Sur ce cluster, Hive utilise le moteur MapReduce (`hive.execution.engine = mr`). La requête
HiveQL est traduite automatiquement en **2 jobs MapReduce**, visibles dans l'interface YARN :

- **Stage-1** : filtre et regroupement par commande (`WHERE` + `GROUP BY`) ;
- **Stage-2** : tri global et limite (`ORDER BY` + `LIMIT 100`).

Durée totale : environ 1 minute, dont environ 27 secondes par job. Ce point sera repris dans la
comparaison Hive / MapReduce du LOT 3.

### Commandes

```powershell
# Capture Beeline (affichage en tableau)
docker cp hive/02_lot2a_2006_2010.hql hadoop-master:/tmp/
docker exec -it hadoop-master bash
#   beeline -u jdbc:hive2://localhost:10000 -f /tmp/02_lot2a_2006_2010.hql

# Export : résultat CSV -> Excel mis en forme
docker exec hadoop-master bash -c "beeline -u jdbc:hive2://localhost:10000 --silent=true --outputformat=csv2 -f /tmp/02_lot2a_2006_2010.hql 2>/dev/null > /tmp/lot2a.csv"
docker cp hadoop-master:/tmp/lot2a.csv hive/data/lot2a_beeline.csv
pip install openpyxl
python hive/export_excel.py hive/data/lot2a_beeline.csv exports/lot2a_top100_2006_2010.xlsx "Top 100 2006-2010"
```

Le script [`hive/export_excel.py`](../hive/export_excel.py) retire les messages de log que
Beeline mélange au résultat, ajoute une colonne de rang, met en forme le classeur (en-tête,
filtres, volet figé, largeurs) et écrit une copie CSV propre, réutilisable dans PowerBI.

### Résultat

**Livrables :** [`exports/lot2a_top100_2006_2010.xlsx`](../exports/lot2a_top100_2006_2010.xlsx)
et [`exports/lot2a_top100_2006_2010.csv`](../exports/lot2a_top100_2006_2010.csv).

**Top 10 :**

| Rang | Commande | Ville | Dépt | Date | Somme des quantités | timbrecde |
|---|---|---|---|---|---|---|
| 1 | 25862 | ARROU | 28 | 2007-05-10 | 42 | 9,85 |
| 2 | 25861 | ARROU | 28 | 2007-05-10 | 30 | 7,85 |
| 3 | 42997 | SAINT GEORGES DES GROSEILLERS | 61 | 2009-12-03 | 23 | 6,40 |
| 4 | 26620 | BOUCE | 61 | 2007-06-21 | 20 | 5,80 |
| 5 | 16235 | ARROU | 28 | 2006-03-03 | 18 | 6,40 |
| 6 | 22609 | COMMUNE NOUVELLE D ARROU | 28 | 2006-11-29 | 18 | 6,40 |
| 7 | 36865 | LE MERLERAULT | 61 | 2008-11-28 | 18 | 5,80 |
| 8 | 20375 | SAINT GERMAIN DU CORBEIS | 61 | 2006-08-31 | 17 | 5,80 |
| 9 | 45087 | DOMFRONT EN POIRAIE | 61 | 2010-04-26 | 16 | 7,80 |
| 10 | 42676 | LA GONFRIERE | 61 | 2009-11-13 | 16 | 7,00 |

**Chiffres clés :**

- **10 633 commandes** correspondent au filtre (période et départements) ; on en retient 100.
- Répartition du top 100 par département : **Orne (61) : 74**, Mayenne (53) : 16,
  Eure-et-Loir (28) : 10.
- Répartition par année : 2010 domine (38 commandes), devant 2008 (23).
- Les 2 premières commandes viennent du même lieu (Arrou), le même jour, avec des numéros
  consécutifs (25861 et 25862) : probablement une seule grosse commande scindée en deux.
- Le top 100 va de 42 articles (1re) à 9 articles (100e).

**Égalités à la frontière du top 100.** 84 commandes ont plus de 9 articles ; il reste donc
16 places pour les 47 commandes qui en ont exactement 9. Le second critère (`timbrecde`) ne
suffit pas à les départager : 21 d'entre elles ont le même `timbrecde` de 6,40. Sans troisième
critère, Hive pourrait renvoyer un top 100 différent d'une exécution à l'autre. Le tri final
sur `codcde` garantit un résultat reproductible, indispensable pour comparer Hive et MapReduce
au LOT 3.

**Vérification indépendante.** Le même top 100 a été recalculé en Python pur, directement sur
le CSV qualifié : le résultat est identique.

📸 **Captures :**

1. Sortie Beeline de la requête A (haut du tableau de résultats).
2. Interface YARN (<http://localhost:8088>) : les jobs MapReduce (Stage-1, Stage-2) générés par
   Hive pour cette requête.

---

## Étape 5 : requête B, 5 % du top 100 2011-2016 sans timbrecli (départements 22, 49, 53)

**Besoin client.** Pour les années 2011 à 2016 et les départements 22 (Côtes-d'Armor),
49 (Maine-et-Loire) et 53 (Mayenne), ne garder que les commandes sans `timbrecli` (non
renseigné ou à 0). Tirer au hasard 5 % des 100 meilleures, avec la ville, la somme des
quantités d'articles et la moyenne des quantités de chaque commande. Produire un PDF avec un
graphe en secteurs par ville.

**Script :** [`hive/03_lot2b_2011_2016.hql`](../hive/03_lot2b_2011_2016.hql)

La requête est découpée en 3 sous-requêtes `WITH`, une par étape du raisonnement :

```sql
WITH commandes_sans_timbrecli AS (       -- 1. filtrer, puis regrouper par commande
    SELECT codcde, villecli AS ville, ...,
           CAST(SUM(qte) AS INT) AS somme_quantites,
           ROUND(AVG(qte), 2)    AS moyenne_quantites,
           MAX(timbrecde)        AS timbrecde
    FROM commandes
    WHERE year(datcde) BETWEEN 2011 AND 2016
      AND substr(cpcli, 1, 2) IN ('22', '49', '53')
      AND (timbrecli IS NULL OR timbrecli = 0)
    GROUP BY codcde, villecli, substr(cpcli, 1, 2), datcde
),
top100 AS (                               -- 2. même classement que la requête A
    SELECT * FROM commandes_sans_timbrecli
    ORDER BY somme_quantites DESC, timbrecde DESC, codcde ASC
    LIMIT 100
)
SELECT ville, somme_quantites, moyenne_quantites, codcde, departement, date_commande
FROM top100
ORDER BY rand(2026)                       -- 3. tirage aléatoire de 5 % de 100 = 5
LIMIT 5;
```

### Choix d'interprétation

| Point du besoin | Choix retenu |
|---|---|
| « Sans timbrecli » | `timbrecli IS NULL OR timbrecli = 0`. Le contrôle préalable montre que `timbrecli` est identique sur toutes les lignes d'une commande : filtrer les lignes revient à filtrer les commandes. |
| « 100 meilleures commandes » | Même définition que la requête A : somme des quantités, puis `timbrecde`, puis `codcde` pour un classement stable |
| « 5 % » | 5 % de 100 = exactement 5 commandes (`LIMIT 5` après un tri aléatoire) |
| « Moyenne des quantités de chaque commande » | `AVG(qte)` sur les lignes de la commande, soit la quantité moyenne par article |
| Aléatoire | `rand(2026)` : une graine fixe rend le tirage reproductible. La capture Beeline et le PDF montrent ainsi les mêmes commandes. Remplacer par `rand()` pour un nouveau tirage à chaque exécution. |
| « Graphe en secteurs par ville » | Un camembert dont chaque part est une ville, de taille égale à la somme des quantités de ses commandes tirées |

### Commandes

```powershell
docker cp hive/03_lot2b_2011_2016.hql hadoop-master:/tmp/
docker exec hadoop-master bash -c "beeline -u jdbc:hive2://localhost:10000 --silent=true --outputformat=csv2 -f /tmp/03_lot2b_2011_2016.hql 2>/dev/null > /tmp/lot2b.csv"
docker cp hadoop-master:/tmp/lot2b.csv hive/data/lot2b_beeline.csv
pip install matplotlib
python hive/export_pie_pdf.py hive/data/lot2b_beeline.csv exports/lot2b_pie_villes_2011_2016.pdf
```

Le script [`hive/export_pie_pdf.py`](../hive/export_pie_pdf.py) produit un PDF A4 paysage : le
camembert en haut, avec le nom de la ville et sa valeur écrits sur chaque part, et le tableau
des 5 commandes en bas, qui sert aussi de légende. Les couleurs viennent d'une palette
catégorielle validée pour rester distinctes, y compris pour les personnes daltoniennes.

### Résultat

**Livrables :** [`exports/lot2b_pie_villes_2011_2016.pdf`](../exports/lot2b_pie_villes_2011_2016.pdf)
et [`exports/lot2b_pie_villes_2011_2016.csv`](../exports/lot2b_pie_villes_2011_2016.csv).

| Ville | Commande | Dépt | Date | Somme des quantités | Moyenne des quantités | Part |
|---|---|---|---|---|---|---|
| LONGUE JUMELLES | 66988 | 49 | 2015-02-06 | 14 | 3,50 | 24 % |
| SAINT MARTIN DU LIMET | 63449 | 53 | 2014-03-10 | 13 | 4,33 | 22 % |
| LA MENITRE | 50322 | 49 | 2011-02-28 | 12 | 4,00 | 20 % |
| GORRON | 69970 | 53 | 2015-11-16 | 11 | 1,83 | 19 % |
| PORT BRILLET | 73436 | 53 | 2016-09-05 | 9 | 2,25 | 15 % |

**Chiffres clés :**

- **3 630 commandes** correspondent à la période et aux départements, dont **3 605 sans
  timbrecli** : sur cette période, le timbre client n'est quasiment plus facturé, et le filtre
  n'écarte que 25 commandes.
- Le top 100 s'étend de 23 articles (Angers) à 9 articles.
- Aucune commande du département 22 n'apparaît dans le tirage : les 5 commandes viennent du 49
  et du 53. C'est un effet du hasard, sur un échantillon de 5.
- Deux exécutions successives donnent le même tirage, ce qui valide la graine fixe.

📸 **Captures :**

1. Sortie Beeline de la requête B (les 5 commandes tirées).
2. Le PDF du camembert (à intégrer directement dans le support de soutenance).

---

## Bilan de la partie Hive

| Livrable demandé | Fichier |
|---|---|
| Table externe sur HDFS | [`hive/01_create_external_table.hql`](../hive/01_create_external_table.hql) |
| Requête A commentée | [`hive/02_lot2a_2006_2010.hql`](../hive/02_lot2a_2006_2010.hql) |
| Requête B commentée | [`hive/03_lot2b_2011_2016.hql`](../hive/03_lot2b_2011_2016.hql) |
| Export Excel (A) | [`exports/lot2a_top100_2006_2010.xlsx`](../exports/lot2a_top100_2006_2010.xlsx) |
| Export PDF (B) | [`exports/lot2b_pie_villes_2011_2016.pdf`](../exports/lot2b_pie_villes_2011_2016.pdf) |
| Captures Beeline | `hive/screenshots/` |
| Procédure de relance | [`hive/run.md`](../hive/run.md) |

Scripts utilitaires : [`hive/00_prepare_tsv.py`](../hive/00_prepare_tsv.py) (CSV vers TSV),
[`hive/export_excel.py`](../hive/export_excel.py) (résultat Beeline vers Excel),
[`hive/export_pie_pdf.py`](../hive/export_pie_pdf.py) (résultat Beeline vers PDF).

---

## Étape 6 : requête A recodée en MapReduce streaming Python (LOT 3)

**Objectif.** Reprendre l'une des deux analyses Hive et la recoder en MapReduce, pour vérifier
le résultat par un calcul indépendant et comparer les deux approches. Le choix s'est porté sur
la **requête A** : elle est déterministe, alors que la requête B comporte un tirage aléatoire.
On peut donc comparer les deux résultats ligne par ligne.

**Fichiers :** [`mapreduce/mapper.py`](../mapreduce/mapper.py),
[`mapreduce/reducer.py`](../mapreduce/reducer.py), [`mapreduce/run_job.sh`](../mapreduce/run_job.sh),
[`mapreduce/compare_hive.py`](../mapreduce/compare_hive.py). Procédure :
[`mapreduce/run.md`](../mapreduce/run.md).

### Le modèle MapReduce appliqué à la requête

```text
 Fichier TSV (HDFS)      MAP                   SHUFFLE & SORT          REDUCE
 134 945 lignes   ─►  filtre période   ─►   Hadoop trie et     ─►  additionne par commande
                      et départements       regroupe par           et garde les 100
                      émet (codcde,         codcde                 meilleures (heapq)
                      qte, timbrecde…)
                      15 620 paires         10 633 groupes         100 lignes
```

| Étape | Rôle | Équivalent Hive |
|---|---|---|
| **Map** (`mapper.py`) | Lit chaque ligne, garde celles de 2006-2010 et des départements 53, 61, 28, émet une paire clé / valeur : clé = `codcde`, valeur = quantité, `timbrecde`, ville, département, date | `WHERE` |
| **Shuffle & sort** (Hadoop) | Trie toutes les paires par clé : les lignes d'une même commande arrivent groupées au reducer | Préparation du `GROUP BY` |
| **Reduce** (`reducer.py`) | Tant que la clé ne change pas, additionne les quantités ; à chaque changement de clé, propose la commande terminée au top 100, tenu dans un tas (`heapq`) de 100 éléments | `GROUP BY` + `ORDER BY` + `LIMIT 100` |

**Points de conception :**

- **Un seul reducer** (`-D mapreduce.job.reduces=1`). Le top 100 est un classement global :
  avec plusieurs reducers, chacun ne verrait qu'une partie des commandes.
- **Un tas plutôt qu'un tri complet.** Le reducer ne garde en mémoire que les 100 meilleures
  commandes rencontrées, quel que soit le nombre total de commandes : la mémoire utilisée reste
  constante.
- **Mêmes règles que Hive** : `timbrecde` pris une seule fois par commande ; mêmes critères de
  classement (somme des quantités, puis `timbrecde`, puis `codcde`) ; quantité vide ignorée,
  comme le fait `SUM()` en SQL.
- **Même source** : le job lit le même fichier HDFS que la table Hive.

### Commandes

```powershell
docker cp mapreduce hadoop-master:/tmp/mapreduce
docker exec -it hadoop-master bash
```

```bash
cd /tmp/mapreduce
# Test local sans Hadoop : le tube "sort" simule le shuffle & sort
cat /tmp/dataw_fro_clean.tsv | python3 mapper.py | sort | python3 reducer.py | head -5
# Job sur le cluster
bash run_job.sh
```

La commande `hadoop jar … -files mapper.py,reducer.py …` et ses options sont détaillées dans
[`mapreduce/run.md`](../mapreduce/run.md).

### Résultat

| Contrôle | Valeur |
|---|---|
| `Map input records` | 134 945 (tout le fichier) |
| `Map output records` | 15 620 lignes dans le périmètre |
| `Reduce input groups` | 10 633 commandes, le même nombre que dans Hive |
| `Reduce output records` | 100 |
| Durée du job | 24 à 27 s au total selon l'exécution (environ 19 à 21 s dans YARN), contre 57 à 67 s pour Hive |
| Test local par tubes | 0,3 s, même résultat |
| Comparaison avec Hive | **IDENTIQUES** : mêmes commandes, mêmes valeurs, même ordre |

**Livrable :** [`mapreduce/output/top100_mapreduce.tsv`](../mapreduce/output/top100_mapreduce.tsv).

La comparaison détaillée (volume de code, temps d'exécution, lisibilité, quand choisir quoi)
fait l'objet d'un document dédié : [`docs/comparaison-hive-mapreduce.md`](comparaison-hive-mapreduce.md).

**En résumé :** la requête Hive fait 14 lignes contre 64 pour le mapper et le reducer, soit
environ 5 fois moins de code. Pourtant, le job écrit à la main est 2 fois plus rapide, parce
qu'il fait en un seul job ce que Hive découpe en deux. Sur 19 Mo, un simple script Python local
est 100 fois plus rapide que les deux : le cluster ne devient rentable que sur de très gros
volumes.

📸 **Captures :**

1. Fin de la sortie de `run_job.sh` : temps `real` et 10 premières commandes :
   [`mapreduce/screenshots/mr_sortie_job_top100.png`](../mapreduce/screenshots/mr_sortie_job_top100.png).
2. Sortie de `compare_hive.py` (`RESULTAT : IDENTIQUES`) :
   [`mapreduce/screenshots/mr_comparaison_hive_identiques.png`](../mapreduce/screenshots/mr_comparaison_hive_identiques.png).

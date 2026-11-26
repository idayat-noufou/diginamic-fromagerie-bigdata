# Comparaison Hive / MapReduce (LOT 3)

La requête A du LOT 2 (top 100 des commandes 2006-2010, départements 53, 61 et 28) a été
écrite deux fois : en HiveQL, puis en MapReduce streaming Python. Les deux versions lisent le
même fichier HDFS et produisent **exactement le même résultat** : mêmes 100 commandes, mêmes
valeurs, même ordre. La vérification est faite par
[`mapreduce/compare_hive.py`](../mapreduce/compare_hive.py).

Ce document compare les deux approches sur le volume de code, le temps d'exécution et la
lisibilité, puis indique quand choisir l'une ou l'autre.

## Les deux implémentations

| | Hive | MapReduce streaming |
|---|---|---|
| Fichiers | [`hive/02_lot2a_2006_2010.hql`](../hive/02_lot2a_2006_2010.hql) | [`mapreduce/mapper.py`](../mapreduce/mapper.py), [`mapreduce/reducer.py`](../mapreduce/reducer.py), [`mapreduce/run_job.sh`](../mapreduce/run_job.sh) |
| Langage | SQL (HiveQL), déclaratif | Python, impératif |
| Données lues | Table externe `fromagerie.commandes` | Fichier TSV brut dans HDFS |
| Prérequis | Table déclarée dans le metastore (schéma) | Connaître la position des colonnes |

## 1. Volume de code

Lignes de code effectives, hors commentaires, docstrings et lignes vides :

| | Hive | MapReduce |
|---|---|---|
| Logique de calcul | **14 lignes** (une requête) | **64 lignes** (mapper 27 + reducer 37) |
| Lancement | `beeline -f fichier.hql` | Commande `hadoop jar` de 9 lignes |
| Rapport | 1 | environ 5 fois plus |

Le SQL décrit **ce que l'on veut** (filtrer, regrouper, trier). Hive s'occupe du comment. En
MapReduce, il faut écrire **comment le calculer** : découper chaque ligne, convertir les types,
détecter le changement de clé dans le reducer, ne pas oublier la dernière commande, gérer le
classement des 100 meilleures avec un tas (`heapq`), traiter les valeurs vides.

## 2. Temps d'exécution

Mesures faites sur le cluster local (1 master et 2 slaves), sur le fichier qualifié de
19 Mo (134 945 lignes) :

| | Hive | MapReduce | Script Python local (pipes) |
|---|---|---|---|
| Jobs YARN lancés | 2 | 1 | 0 |
| Durée d'un job (interface YARN) | environ 27 s chacun | environ 19 à 21 s | — |
| Durée totale vue par l'utilisateur | **57 à 67 s** (environ 1 min) | **24 à 27 s** | **0,3 s** |

Les durées varient d'une exécution à l'autre. Côté Hive, 57,5 s correspond au temps affiché par
Beeline (capture de la requête A) et 67 s à un chronométrage complet avec `time beeline`, qui
inclut le démarrage du client et la connexion à HiveServer2. Côté MapReduce, les deux exécutions
chronométrées avec `time hadoop jar` ont duré 23,7 s (capture) et 26,5 s. Dans tous les cas, le
job MapReduce écrit à la main est **plus de 2 fois plus rapide** que Hive sur cette requête.

**Pourquoi Hive est plus lent ici.** Hive traduit la requête en 2 jobs MapReduce enchaînés :
le premier fait le `WHERE` et le `GROUP BY`, le second fait le `ORDER BY` global et le
`LIMIT`. Chaque job paie un coût fixe de démarrage : réservation des ressources auprès de
YARN, lancement des JVM, écriture des résultats intermédiaires dans HDFS. La version écrite à la
main fait tout en un seul job : le reducer additionne et garde directement les 100 meilleures
commandes en mémoire.

**Pourquoi le script local est 100 fois plus rapide.** Sur 19 Mo, le temps de calcul réel est
négligeable : presque tout le temps du cluster passe dans l'organisation du travail (lancer les
tâches, les distribuer, rassembler les résultats). Hadoop n'est rentable que lorsque les données
ne tiennent plus sur une seule machine. Le coût fixe d'environ 20 secondes devient alors
négligeable face au gain de la parallélisation.

**Compteurs du job MapReduce** (sortie de `hadoop jar`) :

| Compteur | Valeur | Signification |
|---|---|---|
| `Launched map tasks` | 2 | Le fichier est lu par 2 mappers en parallèle |
| `Map input records` | 134 945 | Toutes les lignes du fichier |
| `Map output records` | 15 620 | Lignes qui passent le filtre (période et départements) |
| `Reduce input groups` | 10 633 | Commandes distinctes, le même nombre que dans Hive |
| `Reduce output records` | 100 | Le top 100 |

## 3. Lisibilité et maintenance

| Critère | Hive | MapReduce |
|---|---|---|
| Lecture | Compréhensible par toute personne qui connaît SQL, y compris un analyste métier | Demande de connaître le modèle map / shuffle & sort / reduce |
| Changer un filtre (autres années, autres départements) | Modifier le `WHERE` | Modifier les constantes du mapper |
| Ajouter une colonne au résultat | L'ajouter au `SELECT` et au `GROUP BY` | Modifier le format de sortie du mapper, puis la lecture et l'écriture du reducer |
| Pièges | Prendre `timbrecde` avec `MAX` et non `SUM` | Le même piège, plus : clé qui change, dernière commande à clôturer, un seul reducer obligatoire pour un classement global, valeurs vides |
| Tester | Lancer la requête, ou `EXPLAIN` pour voir le plan | Test local très rapide sans cluster : `cat fichier \| python3 mapper.py \| sort \| python3 reducer.py` |
| Contrôle de l'exécution | Laissé à l'optimiseur de Hive | Total : nombre de reducers, mémoire, algorithme |

## 4. Quand choisir quoi ?

**Choisir Hive** lorsque :

- les données sont structurées en colonnes et le besoin s'exprime en SQL (filtres, agrégats,
  jointures, classements) ;
- la question est ponctuelle ou évolue souvent : on modifie une requête plutôt qu'un programme ;
- les utilisateurs sont des analystes plutôt que des développeurs ;
- plusieurs requêtes portent sur la même table : le schéma est déclaré une fois pour toutes.

**Choisir MapReduce** lorsque :

- le traitement ne s'exprime pas bien en SQL : texte libre, logs non structurés, algorithmes
  sur mesure ;
- on veut maîtriser finement l'exécution (nombre de jobs, mémoire, algorithme), comme ici avec
  un seul job au lieu de deux ;
- on ne dispose pas de metastore ou de schéma, mais seulement de fichiers bruts.

**Dans ce projet**, Hive est le bon choix pour les besoins du client : la requête est 5 fois
plus courte, lisible par tous, et facile à adapter (la requête B réutilise la même structure).
MapReduce a servi à **vérifier le résultat par un calcul indépendant** et à comprendre ce que
Hive exécute réellement.

**Pour aller plus loin.** Aujourd'hui, ni Hive sur MapReduce ni MapReduce écrit à la main ne
sont les choix par défaut : Spark (et Spark SQL) garde les données en mémoire entre les étapes,
ce qui évite l'écriture des résultats intermédiaires sur disque, et propose à la fois une
interface SQL et une interface programmatique. Hive lui-même s'utilise surtout avec le moteur
Tez plutôt que MapReduce.

# MapReduce : procédure de lancement (LOT 3)

Le job recode en MapReduce streaming Python la requête A du LOT 2 : top 100 des commandes
2006-2010 pour les départements 53, 61 et 28. Les explications et les résultats sont dans
[`docs/demarche-hive-mapreduce.md`](../docs/demarche-hive-mapreduce.md). La comparaison avec Hive
est dans [`docs/comparaison-hive-mapreduce.md`](../docs/comparaison-hive-mapreduce.md).

## Prérequis

- Cluster démarré et fichier TSV présent dans HDFS sous `/data/fromagerie/commandes`
  (voir [`hive/run.md`](../hive/run.md), étape 1).
- Pour le test local : le TSV copié dans le conteneur sous `/tmp/dataw_fro_clean.tsv`.

## 1. Copier les scripts dans le conteneur (PowerShell, racine du dépôt)

```powershell
docker cp mapreduce hadoop-master:/tmp/mapreduce
docker exec -it hadoop-master bash
```

## 2. Tester sans Hadoop (dans le conteneur)

Le tube `sort` joue le rôle de l'étape shuffle & sort de Hadoop :

```bash
cd /tmp/mapreduce
cat /tmp/dataw_fro_clean.tsv | python3 mapper.py | sort | python3 reducer.py | head -5
```

## 3. Lancer le job sur le cluster (dans le conteneur)

```bash
bash run_job.sh
```

Commande `hadoop jar` exécutée par le script :

```bash
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
    -D mapreduce.job.name="LOT3 top100 commandes 2006-2010" \
    -D mapreduce.job.reduces=1 \
    -files mapper.py,reducer.py \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -input /data/fromagerie/commandes \
    -output /data/fromagerie/mr_lot2a_top100
```

| Option | Rôle |
|---|---|
| `-files mapper.py,reducer.py` | Envoie les deux scripts sur chaque nœud qui exécute une tâche |
| `-mapper` / `-reducer` | Commande lancée par chaque tâche ; les données passent par l'entrée et la sortie standard |
| `-D mapreduce.job.reduces=1` | Un seul reducer : le top 100 est un classement global, il doit voir toutes les commandes |
| `-input` | Dossier HDFS lu, le même que la table Hive |
| `-output` | Dossier HDFS du résultat ; il ne doit pas exister (le script le supprime avant) |

## 4. Récupérer le résultat et le comparer avec Hive (PowerShell)

```powershell
docker exec hadoop-master hdfs dfs -get -f /data/fromagerie/mr_lot2a_top100/part-00000 /tmp/top100_mapreduce.tsv
New-Item -ItemType Directory -Force mapreduce/output
docker cp hadoop-master:/tmp/top100_mapreduce.tsv mapreduce/output/
python mapreduce/compare_hive.py exports/lot2a_top100_2006_2010.csv mapreduce/output/top100_mapreduce.tsv
```

Résultat attendu : `RESULTAT : IDENTIQUES (memes commandes, memes valeurs, meme ordre)`.

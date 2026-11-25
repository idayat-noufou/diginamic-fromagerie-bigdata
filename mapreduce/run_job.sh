#!/bin/bash
# =============================================================================
# LOT 3 - Lancement du job MapReduce streaming (requête A)
# =============================================================================
# À exécuter DANS le conteneur hadoop-master, depuis le dossier qui contient
# mapper.py et reducer.py :
#     cd /tmp/mapreduce && bash run_job.sh
#
# Entrée : /data/fromagerie/commandes   (le même fichier que la table Hive)
# Sortie : /data/fromagerie/mr_lot2a_top100  (part-00000, 100 lignes)
# =============================================================================
set -e

ENTREE=/data/fromagerie/commandes
SORTIE=/data/fromagerie/mr_lot2a_top100
STREAMING_JAR=$(ls $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar)

# Hadoop refuse d'écrire dans un dossier de sortie existant : on le supprime.
hdfs dfs -rm -r -f "$SORTIE"

# -files   : envoie mapper.py et reducer.py à chaque nœud qui exécute une tâche
# -mapper  / -reducer : commandes lancées sur chaque nœud
# -D mapreduce.job.reduces=1 : un seul reducer, car le top 100 est un
#            classement global qui doit voir toutes les commandes
time hadoop jar "$STREAMING_JAR" \
    -D mapreduce.job.name="LOT3 top100 commandes 2006-2010" \
    -D mapreduce.job.reduces=1 \
    -files mapper.py,reducer.py \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -input "$ENTREE" \
    -output "$SORTIE"

echo "=== Fichiers produits"
hdfs dfs -ls "$SORTIE"
echo "=== 10 premières commandes"
hdfs dfs -cat "$SORTIE/part-00000" | head -10
echo "=== Nombre de lignes"
hdfs dfs -cat "$SORTIE/part-00000" | wc -l

# Hive : procédure de relance (LOT 2)

Procédure complète pour rejouer la partie Hive de zéro. Les explications détaillées, les choix
et les résultats sont dans [`docs/demarche-hive-mapreduce.md`](../docs/demarche-hive-mapreduce.md).

## Prérequis

- Cluster démarré (dépôt du cours `DiginamicAcademy/Hadoop`) :
  `docker compose up -d master slave1 slave2`, puis `./start-all.sh` dans `hadoop-master`.
- Python 3 sur le poste, avec `pip install openpyxl matplotlib`.

Toutes les commandes PowerShell se lancent depuis la racine de ce dépôt.

## 1. Préparer les données et les déposer dans HDFS

```powershell
python hive/00_prepare_tsv.py cleaning/dataw_fro_clean.csv hive/data/dataw_fro_clean.tsv
docker cp hive/data/dataw_fro_clean.tsv hadoop-master:/tmp/
docker exec hadoop-master bash -c "hdfs dfs -mkdir -p /data/fromagerie/commandes && hdfs dfs -put -f /tmp/dataw_fro_clean.tsv /data/fromagerie/commandes/"
```

## 2. Copier les scripts dans le conteneur

```powershell
docker cp hive/01_create_external_table.hql hadoop-master:/tmp/
docker cp hive/02_lot2a_2006_2010.hql hadoop-master:/tmp/
docker cp hive/03_lot2b_2011_2016.hql hadoop-master:/tmp/
```

## 3. Créer la table externe

```powershell
docker exec hadoop-master beeline -u jdbc:hive2://localhost:10000 -f /tmp/01_create_external_table.hql
```

Contrôle attendu : 134 945 lignes, 70 819 commandes.

## 4. Requête A et export Excel

```powershell
docker exec hadoop-master bash -c "beeline -u jdbc:hive2://localhost:10000 --silent=true --outputformat=csv2 -f /tmp/02_lot2a_2006_2010.hql 2>/dev/null > /tmp/lot2a.csv"
docker cp hadoop-master:/tmp/lot2a.csv hive/data/lot2a_beeline.csv
python hive/export_excel.py hive/data/lot2a_beeline.csv exports/lot2a_top100_2006_2010.xlsx "Top 100 2006-2010"
```

## 5. Requête B et export PDF

```powershell
docker exec hadoop-master bash -c "beeline -u jdbc:hive2://localhost:10000 --silent=true --outputformat=csv2 -f /tmp/03_lot2b_2011_2016.hql 2>/dev/null > /tmp/lot2b.csv"
docker cp hadoop-master:/tmp/lot2b.csv hive/data/lot2b_beeline.csv
python hive/export_pie_pdf.py hive/data/lot2b_beeline.csv exports/lot2b_pie_villes_2011_2016.pdf
```

## Affichage en tableau (captures)

Pour afficher un résultat sous forme de tableau, lancer la requête sans les options `--silent`
et `--outputformat` :

```powershell
docker exec -it hadoop-master beeline -u jdbc:hive2://localhost:10000 -f /tmp/02_lot2a_2006_2010.hql
```

# Projet Big Data - Fromagerie

Chaine Big Data complete (NiFi, Hive, MapReduce, HBase, PowerBI) sur la stack Docker du cours (DiginamicAcademy/Hadoop).

## Correspondance dossier / LOT

| LOT | Dossier    | Livrable                               |
| --- | ---------- | -------------------------------------- |
| 0   | cleaning/  | clean_data.py + dataw_fro_clean.csv    |
| 1   | nifi/      | flow.json + captures                   |
| 2   | hive/      | scripts .hql + captures Beeline        |
| 3   | mapreduce/ | mapper.py, reducer.py                  |
| 4   | hbase/     | scripts happybase + exports + captures |
| 5   | powerbi/   | dashboard.pbix + PDF + model.md        |

Autres dossiers :  docs/ (dossier de synthese contenant les explications pour chaques parties), soutenance/ (support).

## Prerequis

- Docker Desktop (WSL2), environ 5 Go de RAM alloues
- Git, Python 3 (pip), PowerBI Desktop
- Depot DiginamicAcademy/Hadoop clone

## Lancement rapide

```bash
git clone https://github.com/DiginamicAcademy/Hadoop.git
cd Hadoop
./container_start.sh
docker exec -it hadoop-master bash
./start-all.sh
```

## Ports

| Service         | Port  |
|-----------------|-------|
| NameNode        | 9870  |
| ResourceManager | 8088  |
| HBase Master    | 16010 |
| HBase Thrift    | 9090  |
| HiveServer2     | 10000 |
| NiFi (HTTPS)    | 8443  |

## Conventions

- exports/ : livrables finaux

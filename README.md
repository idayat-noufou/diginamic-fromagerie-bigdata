# Projet Big Data - Fromagerie

Chaine Big Data complete (NiFi, Hive, MapReduce, HBase, PowerBI) sur la stack Docker du cours (DiginamicAcademy/Hadoop).

## Correspondance dossier / LOT

| LOT | Dossier        | Livrable                                  |
|-----|----------------|-------------------------------------------|
| 0   | cleaning/      | clean_data.py + dataw_fro_clean.csv       |
| 1   | nifi/          | flow.json + captures                      |
| 2   | hive/          | scripts .hql + captures Beeline           |
| 3   | mapreduce/     | mapper.py, reducer.py                     |
| 4   | hbase/         | scripts happybase + analyse pandas        |
| 5   | powerbi/       | dashboard.pbix + PDF + model.md           |

Autres dossiers : docs/ (dossier de synthese), exports/ (livrables finaux), soutenance/ (support), scripts/ (utilitaires).

## Prerequis

- Docker Desktop (WSL2), environ 5 Go de RAM alloues
- Git, Python 3 (pip), PowerBI Desktop
- Depot DiginamicAcademy/Hadoop clone

## Lancement rapide

    cp nifi/credentials.env.example nifi/credentials.env   (mot de passe >= 12 caracteres)
    ./container_start.sh
    docker exec -it hadoop-master bash
    ./start-all.sh

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
- powerbi/csv_exports/ : entrees intermediaires de PowerBI (repli si pas de driver ODBC)

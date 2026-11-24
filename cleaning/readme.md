# Configuration technique

## Langage et versions

| Élément | Version |  |
|---|---|---|
| Python | 3.11 ou plus |  |
| pandas | 2.0 ou plus |  |
| `unicodedata` | module standard de Python |  |

## Installation

```bash
pip install "pandas>=2.0"
```

Pour vérifier les versions installées :

```bash
python --version
python -c "import pandas; print(pandas.__version__)"
```

## Fichiers nécessaires (dans le même dossier)

```
config.py
verification.py
clean.py
dataw_fro03.csv
```

## Ordre d'exécution

Ouvrir un terminal dans ce dossier, puis :

| Ordre | Commande | Résultat |
|---|---|---|
| 1 | `python verification.py` | Rapport des anomalies affiché à l'écran, aucun fichier modifié |
| 1bis  | `python verification.py > rapport_anomalies_traitées.txt`                         | Enregister le rapport de vérification détaillé                                                                |
| 2 | `python clean.py` | Création de `dataw_fro_clean.csv` et `dataw_fro_rejets.csv` |

`config.py` ne se lance pas : les deux scripts l'importent automatiquement.


### Copier dataw_fro_clean.csv 

`docker cp "chemin vers le doc\dataw_fro_clean.csv" hadoop-master:/home/`

`docker exec hadoop-master hdfs dfs -mkdir -p /data/fromagerie`

`docker exec hadoop-master hdfs dfs -put /home/dataw_fro_clean.csv /data/fromagerie/`

`hdfs dfs -ls /data/fromagerie`



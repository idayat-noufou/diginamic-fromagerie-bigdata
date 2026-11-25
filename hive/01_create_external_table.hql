-- =============================================================================
-- LOT 2 - Étape 3 : création de la table externe Hive sur la zone HDFS
-- =============================================================================
-- Source : /data/fromagerie/commandes/dataw_fro_clean.tsv
--          (fichier qualifié du LOT 0, converti en TSV par hive/00_prepare_tsv.py)
--
-- Table EXTERNE : Hive enregistre seulement la structure (colonnes, types,
-- emplacement) dans son metastore. Les données restent dans le fichier HDFS,
-- elles ne sont ni copiées ni déplacées. Un DROP TABLE supprime la définition
-- mais laisse le fichier intact.
--
-- Granularité : 1 ligne = 1 article d'une commande. Une commande (codcde)
-- s'étale donc sur plusieurs lignes ; les informations de la commande
-- (client, ville, date, timbrecde...) sont répétées sur chacune d'elles.
--
-- Exécution :
--   beeline -u jdbc:hive2://localhost:10000 -f /tmp/01_create_external_table.hql
-- =============================================================================

CREATE DATABASE IF NOT EXISTS fromagerie
COMMENT 'Datawarehouse de la fromagerie (commandes depuis 2004)';

USE fromagerie;

-- Relance possible du script : on supprime l'ancienne définition (le fichier
-- HDFS n'est pas touché, la table étant externe).
DROP TABLE IF EXISTS commandes;

CREATE EXTERNAL TABLE commandes (
    -- Client
    codcli      INT     COMMENT 'Code client',
    genrecli    STRING  COMMENT 'Civilite (M., Mme...)',
    nomcli      STRING  COMMENT 'Nom du client',
    prenomcli   STRING  COMMENT 'Prenom(s) du client',
    cpcli       STRING  COMMENT 'Code postal, en texte pour garder les zeros initiaux ; departement = 2 premiers caracteres',
    villecli    STRING  COMMENT 'Ville du client',
    -- Commande
    codcde      INT     COMMENT 'Numero de commande',
    datcde      DATE    COMMENT 'Date de la commande (AAAA-MM-JJ)',
    timbrecli   DOUBLE  COMMENT 'Frais de timbre payes par le client',
    timbrecde   DOUBLE  COMMENT 'Frais de timbre de la commande (repetes sur chaque ligne de la commande)',
    nbcolis     DOUBLE  COMMENT 'Nombre de colis de la commande',
    cheqcli     DOUBLE  COMMENT 'Montant du cheque client',
    barchive    INT     COMMENT 'Indicateur archive',
    bstock      INT     COMMENT 'Indicateur stock',
    -- Article
    codobj      INT     COMMENT 'Code article',
    qte         DOUBLE  COMMENT 'Quantite commandee (ecrite 2.0 dans le fichier, donc DOUBLE)',
    colis       DOUBLE  COMMENT 'Numero de colis',
    libobj      STRING  COMMENT 'Libelle article',
    tailleobj   STRING  COMMENT 'Taille ou variante article',
    poidsobj    INT     COMMENT 'Poids article (g)',
    points      DOUBLE  COMMENT 'Points fidelite',
    indispobj   INT     COMMENT 'Indicateur article indisponible',
    libcondit   STRING  COMMENT 'Conditionnement',
    prixcond    INT     COMMENT 'Prix du conditionnement',
    puobj       INT     COMMENT 'Prix unitaire article'
)
COMMENT 'Lignes de commande de la fromagerie (fichier qualifie LOT 0)'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'        -- séparateur tabulation (voir 00_prepare_tsv.py)
    LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION '/data/fromagerie/commandes'
-- Une valeur vide dans le fichier est lue comme NULL, y compris pour les
-- colonnes texte : « non renseigné » = NULL partout.
TBLPROPERTIES ('serialization.null.format' = '');


-- =============================================================================
-- Contrôles après création
-- =============================================================================

-- 1. Structure de la table
DESCRIBE commandes;

-- 2. Nombre de lignes : doit valoir 134 945 (lignes du fichier qualifié)
SELECT COUNT(*) AS nb_lignes FROM commandes;

-- 3. Aperçu : les colonnes doivent être bien alignées (pas de décalage)
SELECT codcli, nomcli, prenomcli, cpcli, villecli, codcde, datcde, timbrecde, qte, libobj
FROM commandes
LIMIT 5;

-- 4. Typage : aucune date ni quantité ne doit être tombée à NULL par erreur
--    de type (les 3 qte vides du fichier source sont attendues).
SELECT
    COUNT(DISTINCT codcde)                         AS nb_commandes,
    MIN(datcde)                                    AS premiere_date,
    MAX(datcde)                                    AS derniere_date,
    SUM(CASE WHEN datcde IS NULL THEN 1 ELSE 0 END) AS dates_nulles,
    SUM(CASE WHEN qte    IS NULL THEN 1 ELSE 0 END) AS qte_nulles
FROM commandes;

-- 5. Les lignes à prénoms multiples (virgules) sont bien lues
SELECT codcli, prenomcli, cpcli, villecli, datcde
FROM commandes
WHERE prenomcli LIKE '%,%';

-- =============================================================================
-- LOT 2 - Requête B : 5 % tirés au hasard parmi les 100 meilleures commandes
--         Années 2011 à 2016, départements 22, 49 et 53, sans timbrecli
-- =============================================================================
-- Besoin client :
--   Ressortir de façon aléatoire 5 % des 100 meilleures commandes, avec la
--   ville, la somme des quantités d'articles et la moyenne des quantités de
--   chaque commande, pour les commandes sans timbrecli (non renseigné ou à 0).
--   Le résultat alimente un PDF avec un graphe en secteurs par ville.
--
-- Démarche en 3 temps (une sous-requête WITH par temps) :
--   1. commandes_sans_timbrecli : filtre puis regroupement par commande ;
--   2. top100 : même classement que la requête A (somme des quantités, puis
--      timbrecde, puis codcde pour un classement stable) ;
--   3. tirage : 5 % de 100 = 5 commandes, tirées au hasard avec rand().
--
-- Points d'attention :
--   - timbrecli est identique sur toutes les lignes d'une commande (vérifié) :
--     filtrer les lignes revient à filtrer les commandes.
--   - « Non renseigné » = NULL (la table lit les valeurs vides comme NULL),
--     d'où le test IS NULL OR = 0.
--   - moyenne_quantites = quantité moyenne par article de la commande
--     (AVG(qte) sur les lignes de la commande).
--   - rand(2026) : graine fixe. Le tirage est aléatoire mais reproductible :
--     la capture Beeline et le PDF montrent les mêmes 5 commandes. Pour un
--     tirage différent à chaque exécution, remplacer par rand().
--
-- Exécution (export CSV pour le PDF) :
--   beeline -u jdbc:hive2://localhost:10000 --silent=true --outputformat=csv2 \
--           -f /tmp/03_lot2b_2011_2016.hql > /tmp/lot2b.csv
-- =============================================================================

USE fromagerie;

WITH commandes_sans_timbrecli AS (
    SELECT
        codcde,
        villecli                    AS ville,
        substr(cpcli, 1, 2)         AS departement,
        datcde                      AS date_commande,
        CAST(SUM(qte) AS INT)       AS somme_quantites,
        ROUND(AVG(qte), 2)          AS moyenne_quantites,
        MAX(timbrecde)              AS timbrecde   -- pris une fois par commande
    FROM commandes
    WHERE year(datcde) BETWEEN 2011 AND 2016
      AND substr(cpcli, 1, 2) IN ('22', '49', '53')
      AND (timbrecli IS NULL OR timbrecli = 0)
    GROUP BY codcde, villecli, substr(cpcli, 1, 2), datcde
),
top100 AS (
    SELECT *
    FROM commandes_sans_timbrecli
    ORDER BY somme_quantites DESC, timbrecde DESC, codcde ASC
    LIMIT 100
)
SELECT
    ville,
    somme_quantites,
    moyenne_quantites,
    codcde,
    departement,
    date_commande
FROM top100
ORDER BY rand(2026)
LIMIT 5;

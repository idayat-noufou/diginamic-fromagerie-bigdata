-- =============================================================================
-- LOT 2 - Requête A : top 100 des meilleures commandes
--         Années 2006 à 2010, départements 53, 61 et 28
-- =============================================================================
-- Besoin client :
--   Ressortir les 100 meilleures commandes avec la ville, la somme des
--   quantités d'articles et la valeur de timbrecde.
--
-- Définition de la « meilleure commande » (tri à deux niveaux) :
--   1. la plus grande somme des quantités d'articles ;
--   2. en cas d'égalité, le plus grand timbrecde.
--   Le numéro de commande sert de 3e critère, uniquement pour que le
--   classement soit stable d'une exécution à l'autre (et comparable au
--   résultat MapReduce du LOT 3).
--
-- Points d'attention :
--   - 1 ligne = 1 article : on regroupe par commande (codcde).
--   - La ville et timbrecde sont identiques sur toutes les lignes d'une
--     commande (vérifié sur le fichier). On additionne donc qte, mais on
--     prend timbrecde une seule fois avec MAX() ; un SUM() le multiplierait
--     par le nombre d'articles.
--   - Le département n'est pas une colonne : ce sont les 2 premiers
--     caractères du code postal (cpcli, stocké en texte).
--
-- Exécution (export CSV pour l'Excel) :
--   beeline -u jdbc:hive2://localhost:10000 --silent=true --outputformat=csv2 \
--           -f /tmp/02_lot2a_2006_2010.hql > /tmp/lot2a_top100.csv
-- =============================================================================

USE fromagerie;

SELECT
    codcde,
    villecli                    AS ville,
    substr(cpcli, 1, 2)         AS departement,
    datcde                      AS date_commande,
    CAST(SUM(qte) AS INT)       AS somme_quantites,
    MAX(timbrecde)              AS timbrecde
FROM commandes
WHERE year(datcde) BETWEEN 2006 AND 2010
  AND substr(cpcli, 1, 2) IN ('53', '61', '28')
GROUP BY codcde, villecli, substr(cpcli, 1, 2), datcde
ORDER BY somme_quantites DESC, timbrecde DESC, codcde ASC
LIMIT 100;

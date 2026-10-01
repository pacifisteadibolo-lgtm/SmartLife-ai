-- Phase 9 ne crée pas de tables : les statistiques sont calculées à partir
-- des tables académiques existantes (inscriptions, matières, résultats, bulletins).
CREATE INDEX IF NOT EXISTS idx_resultats_matiere_publie_semestre ON resultats_matieres(matiere_id, publie, semestre_id);
CREATE INDEX IF NOT EXISTS idx_inscriptions_filiere_niveau_annee ON inscriptions_etudiants(filiere_id, niveau_id, annee_academique_id, statut);

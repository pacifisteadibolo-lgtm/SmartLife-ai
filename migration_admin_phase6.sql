ALTER TABLE resultats_matieres
    ADD COLUMN IF NOT EXISTS statut VARCHAR(20) NOT NULL DEFAULT 'brouillon';

ALTER TABLE resultats_matieres
    ADD COLUMN IF NOT EXISTS soumis_le TIMESTAMP;

ALTER TABLE resultats_matieres
    ADD COLUMN IF NOT EXISTS valide_le TIMESTAMP;

ALTER TABLE resultats_matieres
    ADD COLUMN IF NOT EXISTS valide_par_id INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_resultats_statut ON resultats_matieres(statut);
CREATE INDEX IF NOT EXISTS idx_professeurs_utilisateur ON professeurs(utilisateur_id);

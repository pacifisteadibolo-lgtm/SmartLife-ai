-- SmartLife AI — Phase 1 administration
-- PostgreSQL

ALTER TABLE utilisateurs
    ADD COLUMN IF NOT EXISTS role VARCHAR(30) NOT NULL DEFAULT 'etudiant';

ALTER TABLE utilisateurs
    ADD COLUMN IF NOT EXISTS matricule VARCHAR(50);

ALTER TABLE utilisateurs
    ADD COLUMN IF NOT EXISTS statut VARCHAR(20) NOT NULL DEFAULT 'actif';

CREATE UNIQUE INDEX IF NOT EXISTS uq_utilisateurs_matricule
    ON utilisateurs(matricule)
    WHERE matricule IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_utilisateurs_role
    ON utilisateurs(role);

CREATE INDEX IF NOT EXISTS idx_utilisateurs_statut
    ON utilisateurs(statut);

-- Après avoir vérifié l'adresse du compte administratif, utiliser par exemple :
-- UPDATE utilisateurs SET role='administrateur' WHERE email='admin@votre-etablissement.tg';

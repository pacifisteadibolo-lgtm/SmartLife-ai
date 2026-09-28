ALTER TABLE utilisateurs
    ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE utilisateurs
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_utilisateurs_role_statut
    ON utilisateurs(role, statut);

CREATE INDEX IF NOT EXISTS idx_professeurs_utilisateur
    ON professeurs(utilisateur_id);

-- Phase 3 : préinscriptions + inscriptions officielles des étudiants
ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS activation_token_hash VARCHAR(64);
ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS activation_expires_at TIMESTAMP;
CREATE UNIQUE INDEX IF NOT EXISTS uq_utilisateurs_activation_token_hash ON utilisateurs(activation_token_hash) WHERE activation_token_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS preinscriptions (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    telephone VARCHAR(40) NOT NULL,
    date_naissance DATE,
    lieu_naissance VARCHAR(150),
    adresse VARCHAR(255),
    filiere_id INTEGER NOT NULL REFERENCES filieres(id) ON DELETE RESTRICT,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE RESTRICT,
    annee_academique_id INTEGER NOT NULL REFERENCES annees_academiques(id) ON DELETE RESTRICT,
    statut VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    motif_admin TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_preinscriptions_statut ON preinscriptions(statut);
CREATE INDEX IF NOT EXISTS idx_preinscriptions_email ON preinscriptions(email);

CREATE TABLE IF NOT EXISTS inscriptions_etudiants (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
    matricule VARCHAR(50) NOT NULL UNIQUE,
    filiere_id INTEGER NOT NULL REFERENCES filieres(id) ON DELETE RESTRICT,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE RESTRICT,
    annee_academique_id INTEGER NOT NULL REFERENCES annees_academiques(id) ON DELETE RESTRICT,
    statut VARCHAR(20) NOT NULL DEFAULT 'actif',
    date_inscription TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inscription_etudiant_annee UNIQUE (utilisateur_id, annee_academique_id)
);
CREATE INDEX IF NOT EXISTS idx_inscriptions_etudiants_statut ON inscriptions_etudiants(statut);
CREATE INDEX IF NOT EXISTS idx_inscriptions_etudiants_utilisateur ON inscriptions_etudiants(utilisateur_id);

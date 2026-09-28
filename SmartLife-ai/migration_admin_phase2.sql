-- SmartLife AI — Phase 2 : structure académique
-- PostgreSQL

CREATE TABLE IF NOT EXISTS annees_academiques (
    id SERIAL PRIMARY KEY,
    libelle VARCHAR(20) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS filieres (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) NOT NULL UNIQUE,
    code VARCHAR(30) NOT NULL UNIQUE,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS niveaux (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(80) NOT NULL,
    code VARCHAR(30) NOT NULL,
    filiere_id INTEGER NOT NULL REFERENCES filieres(id) ON DELETE CASCADE,
    annee_academique_id INTEGER NOT NULL REFERENCES annees_academiques(id) ON DELETE RESTRICT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_niveau_filiere_annee UNIQUE (nom, filiere_id, annee_academique_id)
);

CREATE TABLE IF NOT EXISTS semestres (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(80) NOT NULL,
    code VARCHAR(30) NOT NULL UNIQUE,
    ordre INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS professeurs (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER UNIQUE REFERENCES utilisateurs(id) ON DELETE SET NULL,
    nom VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    telephone VARCHAR(40),
    matricule VARCHAR(50) UNIQUE,
    specialite VARCHAR(150),
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matieres (
    id SERIAL PRIMARY KEY,
    code VARCHAR(30) NOT NULL,
    nom VARCHAR(150) NOT NULL,
    coefficient NUMERIC(5,2) NOT NULL DEFAULT 1,
    credits NUMERIC(5,2) NOT NULL DEFAULT 1,
    niveau_id INTEGER NOT NULL REFERENCES niveaux(id) ON DELETE CASCADE,
    semestre_id INTEGER NOT NULL REFERENCES semestres(id) ON DELETE RESTRICT,
    professeur_id INTEGER REFERENCES professeurs(id) ON DELETE SET NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_matiere_code_niveau UNIQUE (code, niveau_id)
);

CREATE INDEX IF NOT EXISTS idx_niveaux_filiere ON niveaux(filiere_id);
CREATE INDEX IF NOT EXISTS idx_niveaux_annee ON niveaux(annee_academique_id);
CREATE INDEX IF NOT EXISTS idx_matieres_niveau ON matieres(niveau_id);
CREATE INDEX IF NOT EXISTS idx_matieres_semestre ON matieres(semestre_id);
CREATE INDEX IF NOT EXISTS idx_matieres_professeur ON matieres(professeur_id);

INSERT INTO semestres (nom, code, ordre) VALUES
('Semestre 1', 'S1', 1),
('Semestre 2', 'S2', 2)
ON CONFLICT (code) DO NOTHING;

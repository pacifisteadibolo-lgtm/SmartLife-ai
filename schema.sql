-- ============================================================
--  SmartLife AI v2.0 — Schéma de base de données
--  PostgreSQL  |  Encodage : UTF-8
--  Exécuter avec : psql "$DATABASE_URL" -f schema.sql
--  (converti depuis MySQL 8.x — la note ON UPDATE CURRENT_TIMESTAMP
--   pour taches.updated_at a été retirée : Postgres gère ça via un
--   trigger si besoin, pas via une clause de colonne)
-- ============================================================

-- ──────────────────────────────────────────
--  1. UTILISATEURS
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS utilisateurs (
    id            SERIAL PRIMARY KEY,
    nom           VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  NOT NULL UNIQUE,
    mot_de_passe  VARCHAR(255)  NOT NULL,
    photo         VARCHAR(255)  DEFAULT 'default.png',
    bio           TEXT,
    filiere       VARCHAR(100),
    niveau        VARCHAR(50),
    created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────
--  2. DÉPENSES
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS depenses (
    id          SERIAL PRIMARY KEY,
    montant     DECIMAL(10,2)  NOT NULL,
    categorie   VARCHAR(100)   NOT NULL,
    description VARCHAR(255),
    date        DATE           NOT NULL,
    user_id     INT            NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  3. REVENUS
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS revenus (
    id         SERIAL PRIMARY KEY,
    montant    DECIMAL(10,2)  NOT NULL,
    source     VARCHAR(100)   NOT NULL,
    date       DATE           NOT NULL,
    user_id    INT            NOT NULL,
    created_at TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  4. TÂCHES (Planificateur)
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS taches (
    id          SERIAL PRIMARY KEY,
    titre       VARCHAR(255)  NOT NULL,
    description TEXT,
    priorite    VARCHAR(20) DEFAULT 'moyenne',
    statut      VARCHAR(20) DEFAULT 'a_faire',
    date_limite TIMESTAMP,
    user_id     INT NOT NULL,
    created_at  TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  5. PUBLICATIONS (Feed UniShare)
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS publications (
    id      SERIAL PRIMARY KEY,
    user_id INT  NOT NULL,
    contenu TEXT,
    type    VARCHAR(20) DEFAULT 'texte',
    likes   INT DEFAULT 0,
    date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  6. FICHIERS
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fichiers (
    id         SERIAL PRIMARY KEY,
    user_id    INT          NOT NULL,
    pub_id     INT,
    nom        VARCHAR(255) NOT NULL,
    chemin     VARCHAR(500) NOT NULL,
    type_mime  VARCHAR(100),
    taille     INT,
    matiere    VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (pub_id)  REFERENCES publications(id) ON DELETE SET NULL
);

-- ──────────────────────────────────────────
--  7. AUDIOS (Messages vocaux)
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audios (
    id            SERIAL PRIMARY KEY,
    user_id       INT          NOT NULL,
    pub_id        INT,
    chemin        VARCHAR(500) NOT NULL,
    duree         INT,
    transcription TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (pub_id)  REFERENCES publications(id) ON DELETE SET NULL
);

-- ──────────────────────────────────────────
--  8. COMMENTAIRES
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS commentaires (
    id      SERIAL PRIMARY KEY,
    pub_id  INT  NOT NULL,
    user_id INT  NOT NULL,
    contenu TEXT NOT NULL,
    date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pub_id)  REFERENCES publications(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  9. NOTIFICATIONS
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id      SERIAL PRIMARY KEY,
    user_id INT         NOT NULL,
    type    VARCHAR(50),
    message VARCHAR(255) NOT NULL,
    lu      BOOLEAN     DEFAULT FALSE,
    lien    VARCHAR(255),
    date    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  10. MESSAGES PRIVÉS
-- ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages_prives (
    id              SERIAL PRIMARY KEY,
    expediteur_id   INT NOT NULL,
    destinataire_id INT NOT NULL,
    contenu         TEXT,
    type            VARCHAR(20) DEFAULT 'texte',
    lu              BOOLEAN  DEFAULT FALSE,
    date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expediteur_id)   REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (destinataire_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

-- ──────────────────────────────────────────
--  Index utiles pour les performances
-- ──────────────────────────────────────────
CREATE INDEX idx_depenses_user_date   ON depenses(user_id, date);
CREATE INDEX idx_revenus_user_date    ON revenus(user_id, date);
CREATE INDEX idx_taches_user_statut   ON taches(user_id, statut);
CREATE INDEX idx_publications_date    ON publications(date DESC);
CREATE INDEX idx_notifs_user_lu       ON notifications(user_id, lu);
CREATE INDEX idx_messages_expediteur  ON messages_prives(expediteur_id);
CREATE INDEX idx_messages_destinataire ON messages_prives(destinataire_id);

-- ──────────────────────────────────────────
--  Données de test (optionnel)
-- ──────────────────────────────────────────
INSERT INTO utilisateurs (nom, email, mot_de_passe, filiere, niveau, bio) VALUES
('Alice Dupont', 'alice@univ.tg', 'hashed_pwd_ici', 'Informatique', 'Licence 3', 'Passionnée de dev web'),
('Bob Martin',  'bob@univ.tg',   'hashed_pwd_ici', 'Mathématiques','Master 1',  'Fan d''IA et de maths');

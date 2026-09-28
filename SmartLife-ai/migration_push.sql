-- ============================================================
--  SmartLife AI — Migration : notifications push
--  A exécuter APRES migration_messagerie_v2.sql :
--  psql "$DATABASE_URL" -f migration_push.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS abonnements_push (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL,
    endpoint   TEXT NOT NULL UNIQUE,
    p256dh     VARCHAR(255) NOT NULL,
    auth       VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_abonnements_push_user ON abonnements_push(user_id);

CREATE TABLE IF NOT EXISTS journal_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES utilisateurs(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    methode VARCHAR(10) NOT NULL,
    endpoint VARCHAR(180),
    objet VARCHAR(255),
    ip VARCHAR(64),
    user_agent VARCHAR(500),
    details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_journal_audit_created_at ON journal_audit(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_journal_audit_user ON journal_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_journal_audit_action ON journal_audit(action);

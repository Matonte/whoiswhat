CREATE TABLE IF NOT EXISTS hoss_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    input_summary TEXT,
    f_scale_items_json TEXT NOT NULL,
    square REAL NOT NULL,
    punisher REAL NOT NULL,
    power REAL NOT NULL,
    skull REAL NOT NULL,
    hoss_score REAL NOT NULL,
    hoss_level INTEGER NOT NULL,
    display_label TEXT NOT NULL,
    internal_label TEXT NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hoss_profiles_source ON hoss_profiles(source);
CREATE INDEX IF NOT EXISTS idx_hoss_profiles_level ON hoss_profiles(hoss_level);

CREATE TABLE IF NOT EXISTS hoss_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name TEXT,
    profile_source TEXT,
    request_payload_json TEXT NOT NULL,
    response_payload_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
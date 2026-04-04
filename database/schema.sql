-- ============================================================
-- GateKeeper Database Schema (SQLite Reference)
-- Note: Tables are auto-created by Flask-SQLAlchemy / Flask-Migrate
-- This file serves as documentation only.
-- ============================================================

CREATE TABLE visitors (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name          VARCHAR(100)  NOT NULL,
    last_name           VARCHAR(100)  NOT NULL,
    company             VARCHAR(200)  NOT NULL,
    contact_person      VARCHAR(200)  NOT NULL,
    license_plate       VARCHAR(20)   NULL,           -- KFZ-Kennzeichen (optional)
    pin                 VARCHAR(6)    NOT NULL,        -- 4-6 digits (dynamic length)
    arrival_time        DATETIME      NOT NULL DEFAULT (datetime('now')),
    departure_time      DATETIME      NULL,
    signature_data      TEXT          NULL,            -- Base64 PNG data URL
    dsgvo_consent       BOOLEAN       NOT NULL DEFAULT 0,
    hygiene_consent     BOOLEAN       NOT NULL DEFAULT 0,
    safety_consent      BOOLEAN       NOT NULL DEFAULT 0,
    -- Legacy health questionnaire columns (kept for backward compat)
    q1_flu              BOOLEAN       NULL,
    q2_diarrhea         BOOLEAN       NULL,
    q3_food_poisoning   BOOLEAN       NULL,
    q4_parasites        BOOLEAN       NULL,
    q5_ent              BOOLEAN       NULL,
    q6_skin             BOOLEAN       NULL,
    created_at          DATETIME      NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_visitors_active_pin
    ON visitors (pin)
    WHERE departure_time IS NULL;

CREATE INDEX idx_visitors_arrival_time
    ON visitors (arrival_time);

CREATE TABLE health_questions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    position            INTEGER       NOT NULL DEFAULT 0,
    text_de             TEXT          NOT NULL,
    text_en             TEXT          NOT NULL DEFAULT '',
    short_key           VARCHAR(50)   NOT NULL UNIQUE,
    active              BOOLEAN       NOT NULL DEFAULT 1,
    created_at          DATETIME      NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE visitor_answers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id          INTEGER       NOT NULL REFERENCES visitors(id),
    question_id         INTEGER       NOT NULL REFERENCES health_questions(id),
    answer              BOOLEAN       NOT NULL,
    UNIQUE(visitor_id, question_id)
);

CREATE TABLE admin_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)   NOT NULL UNIQUE,
    password_hash   VARCHAR(255)  NOT NULL,
    created_at      DATETIME      NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE smtp_settings (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    smtp_host             VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_port             INTEGER       NOT NULL DEFAULT 587,
    smtp_user             VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_password         VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_sender           VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_recipients       TEXT          NOT NULL DEFAULT '',  -- Monatlicher Report-Empfänger
    emergency_recipients  TEXT          NOT NULL DEFAULT '',  -- Notfall-Evakuierungsliste-Empfänger
    use_tls               BOOLEAN       NOT NULL DEFAULT 1,
    enabled               BOOLEAN       NOT NULL DEFAULT 0,
    updated_at            DATETIME      NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE static_pages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            VARCHAR(50)   NOT NULL UNIQUE,
    title_de        VARCHAR(200)  NOT NULL,
    title_en        VARCHAR(200)  NOT NULL,
    content_de      TEXT          NOT NULL DEFAULT '',
    content_en      TEXT          NOT NULL DEFAULT '',
    updated_at      DATETIME      NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO static_pages (slug, title_de, title_en, content_de, content_en) VALUES
('emergency_contacts',  'Notfallkontakte',                    'Emergency Contacts',          '<p>Inhalt wird noch eingepflegt.</p>', '<p>Content will be added soon.</p>'),
('emergency_plans',     'Notfallpläne',                       'Emergency Plans',             '<p>Inhalt wird noch eingepflegt.</p>', '<p>Content will be added soon.</p>'),
('emergency_numbers',   'Notrufnummern',                      'Emergency Numbers',           '<p>Inhalt wird noch eingepflegt.</p>', '<p>Content will be added soon.</p>'),
('visitor_info',        'Besucherinformationen',              'Visitor Information',         '<p>Inhalt wird noch eingepflegt.</p>', '<p>Content will be added soon.</p>'),
('hygiene_rules',       'Hygieneregeln',                      'Hygiene Rules',               '<p>Inhalt wird noch eingepflegt.</p>', '<p>Content will be added soon.</p>'),
('safety_conduct',      'Sicherheits-/Verhaltenshinweise',    'Rules of safety / conduct',  '<p>Inhalt wird noch eingepflegt.</p>', '<p>Content will be added soon.</p>');

-- Migration hints for existing installations:
-- v1 -> v2 (Hygiene/Safety/Fragebogen):
-- ALTER TABLE visitors ADD COLUMN hygiene_consent   BOOLEAN NOT NULL DEFAULT 0;
-- ALTER TABLE visitors ADD COLUMN safety_consent    BOOLEAN NOT NULL DEFAULT 0;
-- ALTER TABLE visitors ADD COLUMN q1_flu            BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q2_diarrhea       BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q3_food_poisoning BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q4_parasites      BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q5_ent            BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q6_skin           BOOLEAN NULL;
-- v2 -> v3 (KFZ-Kennzeichen + Notfall-Empfaenger):
-- ALTER TABLE visitors ADD COLUMN license_plate VARCHAR(20) NULL;
-- ALTER TABLE smtp_settings ADD COLUMN emergency_recipients TEXT NOT NULL DEFAULT '';
-- v3 -> v4 (Dynamic health questions):
-- CREATE TABLE health_questions (...);
-- CREATE TABLE visitor_answers (...);

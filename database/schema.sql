-- ============================================================
-- GateKeeper Database Schema (PostgreSQL Reference)
-- Note: Tables are auto-created by Flask-SQLAlchemy / Flask-Migrate
-- This file serves as documentation only.
-- ============================================================

CREATE TABLE visitors (
    id                  SERIAL PRIMARY KEY,
    first_name          VARCHAR(100)  NOT NULL,
    last_name           VARCHAR(100)  NOT NULL,
    company             VARCHAR(200)  NOT NULL,
    contact_person      VARCHAR(200)  NOT NULL,
    license_plate       VARCHAR(20)   NULL,           -- KFZ-Kennzeichen (optional)
    pin                 CHAR(4)       NOT NULL,
    arrival_time        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    departure_time      TIMESTAMPTZ   NULL,
    signature_data      TEXT          NULL,          -- Base64 PNG data URL
    dsgvo_consent       BOOLEAN       NOT NULL DEFAULT FALSE,
    hygiene_consent     BOOLEAN       NOT NULL DEFAULT FALSE,
    safety_consent      BOOLEAN       NOT NULL DEFAULT FALSE,
    -- Health questionnaire (TRUE = Ja/Yes, FALSE = Nein/No)
    q1_flu              BOOLEAN       NULL,           -- Erkältungskrankheiten / Flu diseases
    q2_diarrhea         BOOLEAN       NULL,           -- Durchfall/Erbrechen / Diarrhoea or vomiting
    q3_food_poisoning   BOOLEAN       NULL,           -- Salmonellen etc. / Food poisoning
    q4_parasites        BOOLEAN       NULL,           -- Parasitäre Infektionen / Parasitic infection
    q5_ent              BOOLEAN       NULL,           -- HNO-Infektionen / ENT infections
    q6_skin             BOOLEAN       NULL,           -- Hauterkrankungen / Skin rashes
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_visitors_active_pin
    ON visitors (pin)
    WHERE departure_time IS NULL;

CREATE INDEX idx_visitors_arrival_time
    ON visitors (arrival_time);

CREATE TABLE admin_users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50)   NOT NULL UNIQUE,
    password_hash   VARCHAR(255)  NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE smtp_settings (
    id                    SERIAL PRIMARY KEY,
    smtp_host             VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_port             INTEGER       NOT NULL DEFAULT 587,
    smtp_user             VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_password         VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_sender           VARCHAR(200)  NOT NULL DEFAULT '',
    smtp_recipients       TEXT          NOT NULL DEFAULT '',  -- Monatlicher Report-Empfänger
    emergency_recipients  TEXT          NOT NULL DEFAULT '',  -- Notfall-Evakuierungsliste-Empfänger
    use_tls               BOOLEAN       NOT NULL DEFAULT TRUE,
    enabled               BOOLEAN       NOT NULL DEFAULT FALSE,
    updated_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE static_pages (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(50)   NOT NULL UNIQUE,
    title_de        VARCHAR(200)  NOT NULL,
    title_en        VARCHAR(200)  NOT NULL,
    content_de      TEXT          NOT NULL DEFAULT '',
    content_en      TEXT          NOT NULL DEFAULT '',
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
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
-- ALTER TABLE visitors ADD COLUMN hygiene_consent   BOOLEAN NOT NULL DEFAULT FALSE;
-- ALTER TABLE visitors ADD COLUMN safety_consent    BOOLEAN NOT NULL DEFAULT FALSE;
-- ALTER TABLE visitors ADD COLUMN q1_flu            BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q2_diarrhea       BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q3_food_poisoning BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q4_parasites      BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q5_ent            BOOLEAN NULL;
-- ALTER TABLE visitors ADD COLUMN q6_skin           BOOLEAN NULL;
-- v2 -> v3 (KFZ-Kennzeichen + Notfall-Empfaenger):
-- ALTER TABLE visitors ADD COLUMN license_plate VARCHAR(20) NULL;
-- ALTER TABLE smtp_settings ADD COLUMN emergency_recipients TEXT NOT NULL DEFAULT '';

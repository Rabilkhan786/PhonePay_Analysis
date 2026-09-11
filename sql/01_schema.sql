CREATE TABLE IF NOT EXISTS state_transactions (
    state VARCHAR(100) NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    period_id INT UNSIGNED NOT NULL,
    transaction_count BIGINT UNSIGNED NOT NULL,
    transaction_amount DECIMAL(24, 2) UNSIGNED NOT NULL,
    PRIMARY KEY (state, year, quarter),
    INDEX idx_state_transactions_period (period_id),
    CHECK (quarter BETWEEN 1 AND 4),
    CHECK (period_id = year * 4 + quarter - 1)
);

CREATE TABLE IF NOT EXISTS district_transactions (
    state VARCHAR(100) NOT NULL,
    district VARCHAR(150) NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    period_id INT UNSIGNED NOT NULL,
    transaction_count BIGINT UNSIGNED NOT NULL,
    transaction_amount DECIMAL(24, 2) UNSIGNED NOT NULL,
    PRIMARY KEY (state, district, year, quarter),
    INDEX idx_district_transactions_period (period_id),
    CHECK (quarter BETWEEN 1 AND 4),
    CHECK (period_id = year * 4 + quarter - 1)
);

CREATE TABLE IF NOT EXISTS state_users (
    state VARCHAR(100) NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    period_id INT UNSIGNED NOT NULL,
    registered_users BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (state, year, quarter),
    INDEX idx_state_users_period (period_id),
    CHECK (quarter BETWEEN 1 AND 4),
    CHECK (period_id = year * 4 + quarter - 1)
);

CREATE TABLE IF NOT EXISTS district_users (
    state VARCHAR(100) NOT NULL,
    district VARCHAR(150) NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    period_id INT UNSIGNED NOT NULL,
    registered_users BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (state, district, year, quarter),
    INDEX idx_district_users_period (period_id),
    CHECK (quarter BETWEEN 1 AND 4),
    CHECK (period_id = year * 4 + quarter - 1)
);

CREATE TABLE IF NOT EXISTS state_merchants (
    state VARCHAR(100) NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    period_id INT UNSIGNED NOT NULL,
    registered_merchants BIGINT UNSIGNED NULL,
    PRIMARY KEY (state, year, quarter),
    INDEX idx_state_merchants_period (period_id),
    CHECK (quarter BETWEEN 1 AND 4),
    CHECK (period_id = year * 4 + quarter - 1)
);

CREATE TABLE IF NOT EXISTS district_merchants (
    state VARCHAR(100) NOT NULL,
    district VARCHAR(150) NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    period_id INT UNSIGNED NOT NULL,
    registered_merchants BIGINT UNSIGNED NULL,
    PRIMARY KEY (state, district, year, quarter),
    INDEX idx_district_merchants_period (period_id),
    CHECK (quarter BETWEEN 1 AND 4),
    CHECK (period_id = year * 4 + quarter - 1)
);

CREATE TABLE IF NOT EXISTS state_transaction_categories (
    state VARCHAR(100) NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    period_id INT UNSIGNED NOT NULL,
    category VARCHAR(30) NOT NULL,
    transaction_count BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (state, year, quarter, category),
    INDEX idx_state_categories_period (period_id),
    CHECK (quarter BETWEEN 1 AND 4),
    CHECK (period_id = year * 4 + quarter - 1)
);


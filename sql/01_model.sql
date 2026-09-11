-- A fresh, dedicated portfolio database is required. Never run against production.
CREATE DATABASE IF NOT EXISTS phonepe_portfolio;
USE phonepe_portfolio;
CREATE TABLE IF NOT EXISTS stage_state (
 state VARCHAR(100) NOT NULL, district VARCHAR(120), period_id int NOT NULL, year int, quarter int,
 transactions bigint, value_inr double precision, registered_users bigint, registered_merchants bigint,
 PRIMARY KEY(state,period_id), CHECK(quarter BETWEEN 1 AND 4));
CREATE TABLE IF NOT EXISTS stage_district (
 state VARCHAR(100) NOT NULL, district VARCHAR(120) NOT NULL, period_id int NOT NULL,
 year int, quarter int, transactions bigint, value_inr double,
 registered_users bigint, registered_merchants bigint,
 PRIMARY KEY(state,district,period_id), CHECK(quarter BETWEEN 1 AND 4));
CREATE TABLE IF NOT EXISTS stage_category (state VARCHAR(100),year int,quarter int,period_id int,category_raw VARCHAR(30),transactions bigint,
 PRIMARY KEY(state,period_id,category_raw));
CREATE OR REPLACE VIEW dim_period AS
 SELECT DISTINCT period_id, year, quarter, STR_TO_DATE(CONCAT(year, '-', quarter * 3 - 2, '-01'), '%Y-%m-%d') AS quarter_start,
 CONCAT(year, '-Q', quarter) AS period_label FROM stage_state;
CREATE OR REPLACE VIEW dim_district AS
 SELECT DISTINCT CONCAT(state, '|', district) AS district_key,state,district FROM stage_district;
CREATE OR REPLACE VIEW dim_state AS SELECT DISTINCT state FROM stage_state;
CREATE OR REPLACE VIEW fact_district_quarter AS
 SELECT CONCAT(state, '|', district) AS district_key,period_id,transactions,value_inr,registered_users,registered_merchants
 FROM stage_district;
CREATE OR REPLACE VIEW fact_state_quarter AS
 SELECT state,period_id,transactions,value_inr,registered_users,registered_merchants FROM stage_state;
-- State category facts stay separate to prevent multiplying district rows.
CREATE OR REPLACE VIEW fact_state_category AS SELECT * FROM stage_category WHERE state<>'india';

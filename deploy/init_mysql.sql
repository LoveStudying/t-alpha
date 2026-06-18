-- t-alpha manual MySQL initialization script.
-- Intended for first-time setup by an operator with database creation privileges.
-- Safe to run repeatedly for project-created tables; existing rows are not overwritten.

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS `t_alpha` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `t_alpha`;

CREATE TABLE IF NOT EXISTS `alert_records` (
  `id` INTEGER NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(32) NOT NULL,
  `signal_time` DATETIME NOT NULL,
  `signal_type` VARCHAR(64) NOT NULL,
  `payload_json` TEXT NOT NULL,
  `sent` TINYINT(1) NOT NULL,
  `error_message` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_alert_records_code` (`code`),
  KEY `ix_alert_records_signal_time` (`signal_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `strategy_backtests` (
  `id` INTEGER NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(32) NOT NULL,
  `strategy_name` VARCHAR(64) NOT NULL,
  `start_date` VARCHAR(8) NOT NULL,
  `end_date` VARCHAR(8) NOT NULL,
  `params_json` TEXT NOT NULL,
  `metrics_json` TEXT NOT NULL,
  `report_path` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_strategy_backtests_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `t0_positions` (
  `id` INTEGER NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(32) NOT NULL,
  `strategy_name` VARCHAR(64) NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `payload_json` TEXT NOT NULL,
  `opened_at` DATETIME NOT NULL,
  `closed_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `ix_t0_positions_code` (`code`),
  KEY `ix_t0_positions_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `t0_strategy_reports` (
  `id` INTEGER NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(32) NOT NULL,
  `strategy_name` VARCHAR(64) NOT NULL,
  `params_json` TEXT NOT NULL,
  `report_json` TEXT NOT NULL,
  `eligible` TINYINT(1) NOT NULL,
  `eligibility_level` VARCHAR(32) NOT NULL,
  `generated_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_t0_report_code_strategy` (`code`, `strategy_name`),
  KEY `ix_t0_strategy_reports_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `watchlist` (
  `id` INTEGER NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(32) NOT NULL,
  `name` VARCHAR(128) NOT NULL,
  `enabled` TINYINT(1) NOT NULL,
  `strategy_name` VARCHAR(64) NOT NULL,
  `note` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_watchlist_code_strategy` (`code`, `strategy_name`),
  KEY `ix_watchlist_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `watchlist` (
  `code`,
  `name`,
  `enabled`,
  `strategy_name`,
  `note`,
  `created_at`,
  `updated_at`
) VALUES (
  '601318.SH',
  '中国平安',
  1,
  'mean_reversion_t0_v1',
  '用户指定的首个测试与监控股票',
  UTC_TIMESTAMP(),
  UTC_TIMESTAMP()
);

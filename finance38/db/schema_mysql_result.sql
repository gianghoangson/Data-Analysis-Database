-- Finance38 Normalized MySQL Schema
-- 3 tables: companies, indices, financial_data

CREATE DATABASE IF NOT EXISTS finance38_result
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finance38_result;

-- Companies reference table
CREATE TABLE IF NOT EXISTS companies (
  company_code VARCHAR(20) PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Financial indices reference table
CREATE TABLE IF NOT EXISTS indices (
  index_id INT PRIMARY KEY,
  index_name VARCHAR(255) NOT NULL,
  name_vn VARCHAR(255),
  unit VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_index_name (index_name),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Financial data fact table
CREATE TABLE IF NOT EXISTS financial_data (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  company_code VARCHAR(20) NOT NULL,
  year INT NOT NULL,
  index_id INT NOT NULL,
  value_raw VARCHAR(255),
  value_num DECIMAL(20, 4),
  source VARCHAR(100),
  loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  UNIQUE KEY uk_company_year_index (company_code, year, index_id),
  
  FOREIGN KEY (company_code) REFERENCES companies(company_code),
  FOREIGN KEY (index_id) REFERENCES indices(index_id),
  
  INDEX idx_company_code (company_code),
  INDEX idx_year (year),
  INDEX idx_index_id (index_id),
  INDEX idx_source (source),
  INDEX idx_loaded_at (loaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


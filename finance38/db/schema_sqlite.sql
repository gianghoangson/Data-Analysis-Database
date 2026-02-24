-- Schema cho finance38.sqlite
-- Lưu trữ 38 chỉ số tài chính theo cấu trúc panel data

-- Bảng chính: Dữ liệu panel dạng long format
CREATE TABLE IF NOT EXISTS finance_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_code TEXT NOT NULL,           -- Mã công ty (VD: HPG, VNM, SAB)
    year INTEGER NOT NULL,                -- Năm báo cáo
    index_id INTEGER NOT NULL,            -- Mã chỉ số (1-38)
    index_name TEXT NOT NULL,             -- Tên chỉ số
    value REAL,                           -- Giá trị
    unit TEXT DEFAULT 'VND',              -- Đơn vị (VND, %, số lượng)
    source TEXT,                          -- Nguồn (pdf, yahoo, computed, manual)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_code, year, index_id)  -- Mỗi công ty/năm/chỉ số chỉ có 1 bản ghi
);

-- Bảng tham chiếu 38 chỉ số
CREATE TABLE IF NOT EXISTS index_reference (
    index_id INTEGER PRIMARY KEY,
    index_name TEXT NOT NULL,
    category TEXT NOT NULL,               -- ownership, revenue, expense, asset, liability, cashflow, ratio, derived
    source_type TEXT NOT NULL,            -- manual, pdf, yahoo, computed
    unit TEXT DEFAULT 'VND',
    description TEXT
);

-- Bảng thông tin công ty
CREATE TABLE IF NOT EXISTS companies (
    company_code TEXT PRIMARY KEY,
    company_name TEXT,
    founding_year INTEGER,
    industry TEXT,
    exchange TEXT                         -- HSX, HNX, UPCOM
);

-- Bảng log xử lý PDF
CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_code TEXT NOT NULL,
    year INTEGER NOT NULL,
    pdf_filename TEXT,
    status TEXT,                          -- success, partial, error
    extracted_count INTEGER DEFAULT 0,
    error_message TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert 38 chỉ số tham chiếu
INSERT OR IGNORE INTO index_reference (index_id, index_name, category, source_type, unit, description) VALUES
-- Ownership (manual)
(1, 'Managerial ownership', 'ownership', 'manual', '%', 'Tỷ lệ sở hữu của ban điều hành'),
(2, 'State ownership', 'ownership', 'manual', '%', 'Tỷ lệ sở hữu nhà nước'),
(3, 'Institutional ownership', 'ownership', 'manual', '%', 'Tỷ lệ sở hữu tổ chức'),
(4, 'Foreign ownership', 'ownership', 'manual', '%', 'Tỷ lệ sở hữu nước ngoài'),

-- Market data (yahoo)
(5, 'Total share outstanding', 'market', 'yahoo', 'shares', 'Tổng số cổ phiếu lưu hành'),
(23, 'Market value of equity', 'market', 'yahoo', 'VND', 'Vốn hóa thị trường'),
(38, 'Firm age', 'market', 'yahoo', 'years', 'Tuổi công ty'),

-- PDF - Revenue
(6, 'Total sales revenue and Net sales revenue', 'revenue', 'pdf', 'VND', 'Doanh thu thuần'),

-- PDF - Assets
(7, 'Total assets', 'asset', 'pdf', 'VND', 'Tổng tài sản'),
(10, 'Value of intangible assets', 'asset', 'pdf', 'VND', 'Tài sản cố định vô hình'),
(28, 'Cash and cash equivalent', 'asset', 'pdf', 'VND', 'Tiền và tương đương tiền'),
(30, 'Current assets', 'asset', 'pdf', 'VND', 'Tài sản ngắn hạn'),
(33, 'Total inventory', 'asset', 'pdf', 'VND', 'Hàng tồn kho'),
(37, 'Net plant, property and equipment', 'asset', 'pdf', 'VND', 'Tài sản cố định hữu hình'),

-- PDF - Expenses
(8, 'Selling expenses', 'expense', 'pdf', 'VND', 'Chi phí bán hàng'),
(9, 'General and administrative expenditure', 'expense', 'pdf', 'VND', 'Chi phí quản lý doanh nghiệp'),
(11, 'Manufacturing overhead', 'expense', 'pdf', 'VND', 'Chi phí sản xuất chung'),
(13, 'Consumption of raw material', 'expense', 'pdf', 'VND', 'Chi phí nguyên vật liệu'),
(14, 'Merchandise purchase of the year', 'expense', 'pdf', 'VND', 'Mua hàng hóa'),
(15, 'Work-in-progress goods purchase', 'expense', 'pdf', 'VND', 'Chi phí sản xuất dở dang'),
(16, 'Outside manufacturing expenses', 'expense', 'pdf', 'VND', 'Chi phí dịch vụ mua ngoài'),
(17, 'Production cost', 'expense', 'pdf', 'VND', 'Tổng chi phí sản xuất'),
(18, 'R&D expenditure', 'expense', 'pdf', 'VND', 'Chi phí nghiên cứu phát triển'),

-- PDF - Income
(12, 'Net operating income', 'income', 'pdf', 'VND', 'Lợi nhuận thuần từ HĐKD'),
(21, 'Net Income', 'income', 'pdf', 'VND', 'Lợi nhuận sau thuế'),
(35, 'EPS', 'income', 'pdf', 'VND', 'Lãi cơ bản trên cổ phiếu'),

-- PDF - Equity & Liabilities
(22, 'Total shareholders'' equity', 'equity', 'pdf', 'VND', 'Vốn chủ sở hữu'),
(24, 'Total liabilities', 'liability', 'pdf', 'VND', 'Nợ phải trả'),
(29, 'Long-term debt', 'liability', 'pdf', 'VND', 'Nợ dài hạn'),
(31, 'Current liabilities', 'liability', 'pdf', 'VND', 'Nợ ngắn hạn'),

-- PDF - Cash flow
(25, 'Net cash from operating activities', 'cashflow', 'pdf', 'VND', 'Lưu chuyển tiền thuần từ HĐKD'),
(26, 'Capital expenditure', 'cashflow', 'pdf', 'VND', 'Chi mua sắm TSCĐ'),
(27, 'Cash flows from investing activities', 'cashflow', 'pdf', 'VND', 'Lưu chuyển tiền từ HĐĐT'),
(34, 'Dividend payment', 'cashflow', 'pdf', 'VND', 'Chi trả cổ tức'),

-- PDF - Other
(19, 'Product innovation', 'innovation', 'manual', 'binary', 'Đổi mới sản phẩm (0/1)'),
(20, 'Process innovation', 'innovation', 'manual', 'binary', 'Đổi mới quy trình (0/1)'),
(36, 'Number of employees', 'hr', 'pdf', 'people', 'Số lượng nhân viên'),

-- Computed
(32, 'Growth ratio', 'ratio', 'computed', '%', 'Tỷ lệ tăng trưởng doanh thu');

-- Index cho truy vấn nhanh
CREATE INDEX IF NOT EXISTS idx_company_year ON finance_data(company_code, year);
CREATE INDEX IF NOT EXISTS idx_index_id ON finance_data(index_id);
CREATE INDEX IF NOT EXISTS idx_source ON finance_data(source);

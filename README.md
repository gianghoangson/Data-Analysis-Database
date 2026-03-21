# Finance38 - Financial Data Extraction Pipeline 📊

Hệ thống tự động **trích xuất và quản lý 38 chỉ số tài chính** từ Báo cáo tài chính (BCTC) PDF của các công ty niêm yết Việt Nam, dùng **Gemini AI API** để đọc PDF và kết hợp với dữ liệu từ Yahoo Finance.

## 🎯 Mục đích & Tính năng

**Finance38** là một pipeline hoàn chỉnh để:
- 🤖 Trích xuất dữ liệu từ BCTC PDF sử dụng **Gemini API** (độ chính xác cao, xử lý PDF scan tốt)
- 📊 Tải dữ liệu thị trường từ Yahoo Finance (giá cổ phiếu, vốn hóa...)
- 🔢 Tính toán các chỉ số phái sinh (tỉ lệ tài chính, so sánh...)
- 💾 Lưu trữ và quản lý dữ liệu JSON/CSV
- 📁 Xuất kết quả thành CSV theo công ty và năm
- ✅ Hỗ trợ nhập dữ liệu manual để điền lỗ trống

## 📋 Tình trạng - Status

### ✅ Đã hoàn thành:
- DCM (2020-2024)
- EVG (2020-2024)
- HAG (2020-2024)
- HPG (2020-2024)
- HSG (2020-2024)
- KDC (2020-2024)
- MSN (2020-2024)
- NAF (2020-2024)

### ⏳ Còn lại:
- NTP, PLX, PNJ, SAB, TRA, VNM, VOS

## � Cấu trúc Project Chi tiết

```
.
├── README.md                        # Tài liệu chính (bạn đang đọc)
├── run.py                           # Entry point chính - chạy PDF extraction
├── check_models.py                  # Model validation script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Template cho environment variables
│
├── BCTC/                            # Input: PDF files của các công ty
│   ├── EVG/
│   ├── HAG/
│   ├── HPG/
│   └── ...
│
├── finance38/                       # Core pipeline modules
│   ├── load_result_to_mysql.py      # ⭐ Script load CSV vào MySQL
│   │
│   ├── app/
│   │   ├── main.py                  # Entry point pipeline
│   │   ├── extract_pdf.py           # Gemini API PDF extraction
│   │   ├── external.py              # Yahoo Finance integration
│   │   ├── compute.py               # Derived indicators
│   │   ├── db.py                    # Database operations
│   │   ├── annual_report.py         # Report parser
│   │   ├── utils.py                 # Utilities
│   │   ├── fiingroup.py             # Company classification
│   │   └── worldbank.py             # World Bank data
│   │
│   ├── data/
│   │   ├── raw/filings/             # Input: PDF files (excluded from git)
│   │   ├── result/                  # Output: 75 CSV files (15 companies × 5 years)
│   │   ├── cache/                   # Cached data
│   │   └── manual_input_template.csv # Manual data input template
│   │
│   ├── db/
│   │   ├── schema_sqlite.sql        # SQLite schema
│   │   └── schema_mysql_result.sql  # MySQL normalized schema
│   │
│   ├── mapping/
│   │   └── mapping_index.yaml       # 38 financial indices definitions
│   │
│   └── requirements.txt             # finance38 dependencies
│
└── .gitignore                       # Exclude BCTC/ and data/raw/
```

## 🚀 Cài đặt & Sử dụng nhanh

### 1️⃣ Setup Gemini API Key

```bash
# Tạo file .env trong root directory
# Lấy API key từ https://ai.google.dev/
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

### 2️⃣ Chuẩn bị môi trường

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt (Windows)
.venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3️⃣ Chuẩn bị dữ liệu PDF

```bash
# Sao chép PDF vào thư mục BCTC (root):
BCTC/
├── EVG/
│   ├── EVG_2020.pdf
│   └── EVG_2023.pdf
├── HAG/
│   ├── HAG_2020.pdf
│   └── HAG_2024.pdf
└── ...
```

### 4️⃣ Chạy Pipeline Gemini PDF Extraction

```bash
# Chạy từ root directory - trích xuất BCTC PDF
python run.py

# Hoặc chạy từ finance38 folder
cd finance38
python -m app.main
```

### 5️⃣ Load CSV Data vào MySQL Database

Sau khi có file CSV kết quả, import vào MySQL:

```bash
# ⚠️ IMPORTANT: Chạy từ thư mục finance38
cd finance38

# Basic usage (localhost, default port 3306)
python load_result_to_mysql.py \
  --user root \
  --password YOUR_PASSWORD \
  --database finance38_result

# Custom host/port
python load_result_to_mysql.py \
  --host 127.0.0.1 \
  --port 3306 \
  --user root \
  --password 123456 \
  --database finance38_result

# Truncate tables trước khi load (fresh import)
python load_result_to_mysql.py \
  --user root \
  --password 123456 \
  --database finance38_result \
  --truncate
```

**Kết quả sau khi chạy (75 files):**
- 15 công ty (companies table)
- 38 chỉ số (indices table)
- 2,850 dòng dữ liệu (financial_data table)

**Database Schema:**
- `companies`: company_code (PK)
- `indices`: index_id (PK), index_name, name_vn, unit
- `financial_data`: normalized fact table with foreign keys, 3-column unique constraint

## � Mô tả chi tiết các thành phần

### 🤖 PDF Extraction (Gemini API)
- Sử dụng **Gemini 2.5 Flash** API để trích xuất dữ liệu từ PDF BCTC
- Xử lý cả PDF text-based và PDF scan (có OCR support)
- Độ chính xác cao, tốc độ nhanh, chi phí thấp
- Kết quả lưu thành CSV files trong `finance38/data/result/`

### 💾 Data Management
- **SQLite** (in-app): Database tạm cho pipeline
- **MySQL**: Database chính để lưu trữ và phân tích dữ liệu
  - Normalized 3-table schema (companies, indices, financial_data)
  - Hỗ trợ query, join, aggregation

### 🔢 38 Financial Indices
Bao gồm:
- Ownership metrics (Management, State, Institutional, Foreign ownership)
- Revenue & expenses breakdown
- Assets & liabilities
- Cash flow indicators
- Innovation metrics
- Market-based metrics (từ Yahoo Finance)
- Derived ratios (profitability, liquidity, solvency)

### 📥 MySQL Data Import
- Script `load_result_to_mysql.py` tự động convert CSV → normalized database
- Hỗ trợ upsert (insert or update)
- Full transaction management với rollback
- Proper foreign key relationships

## 🔗 Dependencies

**PDF Processing & Data Extraction:**
- `pdfplumber` - Text/table extraction từ PDF
- `PyMuPDF` / `fitz` - PDF manipulation
- `google-generativeai` - Gemini API client

**Data Processing:**
- `pandas` - Data manipulation & analysis
- `numpy` - Numerical operations
- `PyYAML` - YAML config parsing

**Database:**
- `pymysql` - Pure Python MySQL client (lightweight, compatible)
- `mysql-connector-python` - Official MySQL connector (fallback)

**Market Data:**
- `yfinance` - Yahoo Finance API

**Utilities:**
- `python-dotenv` - Environment variables
- `tqdm` - Progress bars

## 📅 Project Status & Changelog

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| v1.2 | 2026-03 | ✅ Active | Added MySQL loader, normalized database schema |
| v1.1 | 2025-12 | ✅ Complete | PDF extraction for 8 companies (2020-2024) |
| v1.0 | 2025-11 | ✅ MVP | Switched to Gemini API from P0.x OCR |

**Completed Companies (2020-2024):**
✅ DCM, EVG, HAG, HPG, HSG, KDC, MSN, NAF

**In Progress:**
⏳ NTP, PLX, PNJ, SAB, TRA, VNM, VOS
## 💡 Ghi chú & Best Practices

- **SQLite** được dùng cho in-app caching, dễ back-up và sharing
- **MySQL** là primary database cho production use, supports complex queries
- Pipeline có thể chạy incrementally (skip những bước không cần)
- Lưu trữ `source` info để track dữ liệu từ đâu (pdf/yahoo/manual/computed)
- Hỗ trợ nhập dữ liệu manual để fill gaps (ownership, innovation)
- Gemini 2.5 Flash được chọn vì cost-effective + tốc độ nhanh

## 📖 Troubleshooting

**MySQL Connection Failed:**
- Kiểm tra MySQL service đang chạy: `services.msc` (Windows)
- Verify credentials: localhost:3306, user/password
- Ensure database exists hoặc script sẽ tự tạo (`CREATE DATABASE IF NOT EXISTS`)

**File Not Found:**
- Chạy `load_result_to_mysql.py` từ folder `finance38/`
- Ensure `data/result/` có CSV files
- Ensure `db/schema_mysql_result.sql` tồn tại

**Gemini API Errors:**
- Verify API key trong `.env`
- Check quota limits on Google AI Studio
- Retry từ đầu nếu rate-limited

## 📝 License & Data Sources

**Data Sources:**
- BCTC PDF: Công ty niêm yết Việt Nam
- Market Data: Yahoo Finance API
- Economic Indicators: World Bank API
- Manual Input: User-provided data

**References:**
- [Gemini API Docs](https://ai.google.dev/)
- [Yahoo Finance](https://finance.yahoo.com/)
- [Vietnamese Stock Exchange](https://www.hsx.vn/)

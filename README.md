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

## 📂 Cấu trúc Project

```
finance38/
├── app/                          # Core modules
│   ├── main.py                  # Entry point - chạy pipeline
│   ├── extract_pdf.py           # PDF extraction logic
│   ├── external.py              # Yahoo Finance data
│   ├── compute.py               # Tính chỉ số phái sinh
│   ├── db.py                    # Database operations
│   ├── annual_report.py         # Annual report parser
│   ├── utils.py                 # Helper functions
│   ├── fiingroup.py             # Company classification
│   └── worldbank.py             # World Bank data
├── data/
│   ├── raw/filings/             # Input: PDF files theo company code
│   ├── processed/               # Output: Database & results
│   └── manual_input_template.csv # Manual data input
├── db/
│   └── schema_sqlite.sql        # Database schema
├── mapping/
│   └── mapping_index.yaml       # Config cho 38 chỉ số
├── requirements.txt             # Dependencies
├── RUNNING_GUIDE.md             # Hướng dẫn chi tiết
└── run_ocr.py                   # Standalone OCR script
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

### 3️⃣ Chuẩn bị dữ liệu

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

### 4️⃣ Chạy Pipeline

```bash
# Chạy từ root directory
python run.py

# Hoặc chạy từ finance38 folder
cd finance38
python -m app.main
```

### 📊 Kết quả
Options & Cách sử dụng

```bash
# Chạy từ root - sử dụng Gemini API
python run.py

# Chạy từ finance38 - sử dụng pipeline module
python -m app.main --filings ./BCTC     # Chỉ định folder PDF

# Hoặc từ root
python run.py → xuất vào ./finance38/data/result/
```

Mỗi file CSV chứa 38 cột với đầy đủ các chỉ số tài chính được Gemini AI trích xuất từ PDF.hon -m app.main --skip-yahoo         # Bỏ qua Yahoo Finance (offline)
python -m app.main --init-only          # Chỉ khởi tạo database

# Xem thống kê
python -m app.main --stats
python -m app.main --parallel --workers 4

# Custom PDF folder
python -m app.main --filings /path/to/pdfs

# Liệt kê thống kê database
python -m app.main --stats

# Khởi tạo database mới
python -m app.main --init-only
```

## 📚 Tài liệu chi tiết

Xem [RUNNING_GUIDE.md](./finance38/RUNNING_GUIDE.md) để có:
- Hướng dẫn cài đặt chi tiết
- Mô tả cấu trúc input/output
- Troubleshooting
- Công dụng của từng module

## 📊 38 Chỉ số tài chính

Xem [mapping_index.yaml](./finance38/mapping/) để biết danh sách đầy đủ 38 chỉ số, bao gồm:
- Doanh thu thuần (Net Sales)
- Lợi nhuận sau thuế (Net Income)
- Tổng tài sản (Total Assets)
- Vốn chủ sở hữu (Equity)
- Các chỉ số solvency, liquidity, profitability ratios
- Dữ liệu từ Yahoo Finance (giá, vốn hóa...)

## 🔗 Dependencies

- **pdfplumber** - Trích xuất text/table từ PDF
- **pandas** - Xử lý dữ liệu
- **google-generativeai** - Gemini API để đọc PDF 🤖
- **pandas** - Xử lý dữ liệu
- **yfinance** - Lấy dữ liệu chứng khoán
- **P0.x** - OCR-based extraction (độ chính xác thấp)
- **v1.0** - Chuyển sang Gemini API (độ chính xác cao) ✨
- **v1.1** (hiện tại) - Hoàn thành extraction cho 8 công ty (2020-2024)nt variablesuirements.txt)

## 📅 Lịch sử phát triển

- **Gemini 2.5 Flash** được sử dụng vì tốc độ và cost-effective
- Xử lý tốt cả PDF native text và PDF scan (có OCR support)
- Sử dụng SQLite cho dễ dàng back-up, sharing và query
- Hỗ trợ nhập dữ liệu manual để fill gaps (ownership, innovation)
- Lưu trữ source info để track dữ liệu từ đâu (pdf/yahoo/manual/computed)
## 💡 Ghi chú phát triển

- Sử dụng SQLite cho dễ dàng back-up và sharing
- Có hỗ trợ nhập dữ liệu manual để fill gaps
- Pipeline có thể chạy incrementally (skip bước không cần)
- Lưu trữ source info để track dữ liệu từ đâu

## 📝 License & References

Dữ liệu từ:
- BCTC PDF công ty niêm yết
- Yahoo Finance API
- Số liệu kinh tế Việt Nam

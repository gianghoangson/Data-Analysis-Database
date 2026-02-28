# Finance38 - Financial Data Extraction Pipeline 📊

Hệ thống tự động **trích xuất và quản lý 38 chỉ số tài chính** từ Báo cáo tài chính (BCTC) PDF của các công ty niêm yết Việt Nam, kết hợp với dữ liệu từ Yahoo Finance.

## 🎯 Mục đích & Tính năng

**Finance38** là một pipeline hoàn chỉnh để:
- 📄 Trích xuất dữ liệu từ BCTC PDF sử dụng pdfplumber (hỗ trợ OCR)
- 📊 Tải dữ liệu thị trường từ Yahoo Finance (giá cổ phiếu, lịch sử...)
- 🔢 Tính toán các chỉ số phái sinh (tỉ lệ tài chính, so sánh...)
- 💾 Lưu trữ dữ liệu trong SQLite database
- 📁 Xuất kết quả thành CSV theo công ty và năm
- ⚡ Hỗ trợ xử lý song song để tăng tốc độ

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

### 1️⃣ Chuẩn bị môi trường

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt (Windows)
.venv\Scripts\activate

# Cài đặt dependencies
pip install -r finance38/requirements.txt
```

### 2️⃣ Chuẩn bị dữ liệu

```bash
# Sao chép PDF vào:
finance38/data/raw/filings/{COMPANY_CODE}/{COMPANY_CODE}_{YEAR}.pdf

# Ví dụ:
# finance38/data/raw/filings/EVG/EVG_2023.pdf
# finance38/data/raw/filings/HAG/HAG_2022.pdf
```

### 3️⃣ Chạy Pipeline

```bash
cd finance38

# Chạy full pipeline
python -m app.main

# Hoặc chạy song song (3x nhanh hơn)
python -m app.main --parallel
```

### 📊 Kết quả

```
finance38/data/result/
├── DCM_2020_result.csv
├── DCM_2021_result.csv
├── EVG_2020_result.csv
├── HAG_2022_result.csv
└── ...
```

## 🔧 Command-line Options

```bash
# Bỏ qua bước cụ thể
python -m app.main --skip-ocr      # Bỏ qua trích xuất PDF
python -m app.main --skip-yahoo    # Bỏ qua Yahoo Finance (offline)
python -m app.main --skip-compute  # Bỏ qua tính toán chỉ số phái sinh
python -m app.main --no-export     # Không export CSV

# Parallel processing
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
- **yfinance** - Lấy dữ liệu chứng khoán
- **PyYAML** - Đọc config YAML
- **pytesseract** (optional) - OCR cho PDF scan

Chi tiết xem [requirements.txt](./finance38/requirements.txt)

## 📅 Lịch sử phát triển

- **v1.0** - Hoàn thành extraction cho 8 công ty (2020-2024)
- **v1.1** - Hỗ trợ parallel processing
- **Sắp tới** - Thêm 7 công ty còn lại

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

# 📖 Hướng dẫn chạy Finance38 Pipeline

## 📋 Nội dung
1. [Chuẩn bị môi trường](#chuẩn-bị-môi-trường)
2. [Cấu trúc dữ liệu đầu vào](#cấu-trúc-dữ-liệu-đầu-vào)
3. [Chạy Pipeline](#chạy-pipeline)
4. [Các lệnh thường dùng](#các-lệnh-thường-dùng)
5. [Kết quả đầu ra](#kết-quả-đầu-ra)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Chuẩn bị môi trường

### 1️⃣ Virtual Environment

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (Mac/Linux)
source venv/bin/activate
```

### 2️⃣ Cài đặt dependencies

```bash
# Từ thư mục finance38
pip install -r requirements.txt
```

### 3️⃣ Kiểm tra cài đặt

```bash
python -c "import pdfplumber, pandas, yfinance; print('✓ All dependencies OK')"
```

---

## 📁 Cấu trúc dữ liệu đầu vào

### Chuẩn bị folder PDF

```
data/raw/filings/
├── EVG/
│   ├── EVG_2020.pdf
│   ├── EVG_2021.pdf
│   └── EVG_2022.pdf
├── HAG/
│   ├── HAG_2020.pdf
│   └── HAG_2021.pdf
├── HPG/
│   ├── HPG_2020.pdf
│   └── HPG_2021.pdf
└── VNM/
    ├── VNM_2020.pdf
    └── VNM_2021.pdf
```

**Format tên file:** `{COMPANY_CODE}_{YEAR}.pdf`

**Thứ mục:**
- Đặt tất cả PDF vào `data/raw/filings/`
- Hoặc tạo subfolder theo company code
- Pipeline sẽ scan tất cả file `.pdf` recursively

### Optional: Manual Input Template

```
data/manual_input_template.csv
```

Dùng để nhập dữ liệu manual (ownership, manual indicators) nếu không thể extract từ PDF.

---

## 🚀 Chạy Pipeline

### 1️⃣ Chạy full pipeline (cơ bản)

```bash
cd finance38
python -m app.main
```

**Các bước chạy:**
- [1/5] Khởi tạo database
- [2/5] OCR Extract từ PDF
- [3/5] Lấy dữ liệu từ Yahoo Finance
- [4/5] Compute derived indicators
- [5/5] Export CSV

**Thời gian:**
- ~5-10 phút tùy số lượng PDF

### 2️⃣ Chạy song song (nhanh hơn) ⚡

```bash
python -m app.main -p
```

hoặc:

```bash
python -m app.main --parallel
```

**Tốc độ:** ~2-3x nhanh hơn tùy CPU

**Chỉ định số worker:**
```bash
python -m app.main -p --workers 4
```

### 3️⃣ Chạy với PDF folder khác

```bash
python -m app.main --filings D:\path\to\pdfs
```

hoặc:

```bash
python -m app.main -f ./BCTC
```

---

## 📚 Các lệnh thường dùng

### Bỏ qua bước cụ thể

```bash
# Bỏ qua OCR (chỉ chạy Yahoo + Compute)
python -m app.main --skip-ocr

# Bỏ qua Yahoo Finance (offline mode)
python -m app.main --skip-yahoo

# Bỏ qua compute derived indicators
python -m app.main --skip-compute

# Không export CSV
python -m app.main --no-export
```

### Combine multiple options

```bash
# Chạy parallel, skip Yahoo, có export
python -m app.main -p --skip-yahoo

# Chạy offline (skip Yahoo), không parallel
python -m app.main --skip-yahoo
```

### Xem thống kê database

```bash
# Xem số liệu thống kê
python -m app.main --stats

# Output:
# ==================
# DATABASE STATISTICS
# ==================
# • Số công ty:    15
# • Khoảng năm:    2020 - 2024
# • Tổng records:  1,234
# 
# Completeness (top 10):
#   [6] Net Sales Revenue                  95.2%
#   [7] Total Assets                       94.5%
#   ...
```

### Reset database

```bash
# Xóa database.sqlite và tạo schema mới
rm data/processed/database.sqlite
python -m app.main --init-only
```

---

## 📊 Kết quả đầu ra

### Database

```
data/processed/database.sqlite
```

Chứa tất cả dữ liệu từ:
- PDF extraction
- Yahoo Finance
- Computed indicators

**Bảng chính:** `finance_data`
- `company_code`: Mã công ty (EVG, HAG, ...)
- `year`: Năm (2020-2024)
- `index_id`: ID chỉ số (1-38)
- `index_name`: Tên chỉ số
- `value`: Giá trị
- `source`: Nguồn (pdf, yahoo, computed, manual)

### CSV Exports

```
data/processed/
├── EVG_2020_result.csv
├── EVG_2021_result.csv
├── ...
├── panel_long.csv       # Format long: company, year, index, value
└── panel_wide.csv       # Format wide: row=company-year, col=index
```

**panel_long.csv:**
```
company_code, year, index_id, index_name, value, source
EVG, 2020, 6, Net Sales Revenue, 1000000000, pdf
EVG, 2020, 7, Total Assets, 5000000000, pdf
```

**panel_wide.csv:**
```
company, year, Index_1, Index_2, ..., Index_38
EVG, 2020, 15.5, 22.3, ..., 5
HAG, 2020, 18.2, 25.1, ..., 8
```

---

## 🔍 Troubleshooting

### ❌ Error: Module not found

```
ModuleNotFoundError: No module named 'app'
```

**Giải pháp:**
```bash
# Chạy từ thư mục finance38
cd finance38
python -m app.main

# NÓ KHÔNG phải
python app/main.py
```

### ❌ Error: PDF folder not found

```
⚠ Folder không tồn tại: data/raw/filings
```

**Giải pháp:**
1. Tạo folder: `mkdir -p data/raw/filings`
2. Đặt PDF vào folder
3. Hoặc chỉ định folder khác:
```bash
python -m app.main --filings ./BCTC
```

### ❌ Error: Tesseract not found

```
pytesseract.TesseractNotFoundError
```

**Giải pháp:**
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài đặt (Windows default: `C:\Program Files\Tesseract-OCR`)
3. Nếu đặt ở nơi khác, sửa trong `run_ocr.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Your\Path\tesseract.exe"
```

### ❌ Error: Yahoo API error

```
yfinance.ticker.Ticker - No data found
```

**Giải pháp:**
- Bỏ qua Yahoo:
```bash
python -m app.main --skip-yahoo
```
- Hoặc nhập manual data qua CSV

### ❌ Database locked

```
sqlite3.OperationalError: database is locked
```

**Giải pháp:**
1. Tắt tất cả terminal/process chạy pipeline
2. Chạy lại
3. Nếu vẫn lỗi, xóa lock file:
```bash
rm data/processed/*.sqlite-wal
rm data/processed/*.sqlite-shm
```

### ⚠️ Parallel mode bị crash

**Giải pháp:**
- Giảm số workers:
```bash
python -m app.main -p --workers 2
```
- Hoặc chạy sequential (không parallel)

---

## 📈 Ví dụ workflow hoàn chỉnh

### Lần đầu setup

```bash
# 1. Chuẩn bị environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Chuẩn bị dữ liệu
# - Tạo folder data/raw/filings
# - Copy PDF vào

# 3. Chạy pipeline lần đầu
python -m app.main -p

# 4. Kiểm tra kết quả
python -m app.main --stats
ls data/processed/*.csv
```

### Chạy lại sau khi cập nhật PDF

```bash
# Thêm/sửa PDF, rồi chạy lại
python -m app.main -p

# Check kết quả
python -m app.main --stats
```

### Chỉ compute lại (skip OCR + Yahoo)

```bash
python -m app.main --skip-ocr --skip-yahoo
```

### Export dữ liệu hiện tại

```bash
python -m app.main --skip-ocr --skip-yahoo --skip-compute
```

---

## 🎯 Quick Start

```bash
# 1. Vào thư mục
cd "d:\Self study\Kì 2 - Năm 2\Database\Data-Analysis-Database\finance38"

# 2. Activate environment
.venv\Scripts\activate

# 3. Chạy full pipeline
python -m app.main -p

# 4. Xem kết quả
python -m app.main --stats
```

---

## 📞 Cần giúp?

Kiểm tra:
1. ✓ Virtual environment activated
2. ✓ Dependencies installed (`pip list | grep -E "pandas|pdfplumber|yfinance"`)
3. ✓ PDF folder có dữ liệu
4. ✓ Database folder writeable (`data/processed/`)

Log file (nếu có):
```
data/processed/debug_out.txt
```

---

**Happy analyzing! 🎉**

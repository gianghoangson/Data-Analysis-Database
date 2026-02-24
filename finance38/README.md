# Finance38

Trích xuất và quản lý **38 chỉ số tài chính** từ Báo cáo tài chính (BCTC) PDF của các công ty niêm yết Việt Nam.

## 📁 Cấu trúc thư mục

```
finance38/
├── README.md
├── requirements.txt
├── .env.example
│
├── data/
│   ├── raw/
│   │   └── filings/           # PDF BCTC theo company/year
│   │       ├── HPG/
│   │       │   ├── HPG_2020.pdf
│   │       │   └── HPG_2021.pdf
│   │       └── VNM/
│   │           └── VNM_2020.pdf
│   └── processed/
│       ├── finance38.sqlite   # Database SQLite
│       └── panel_long.csv     # Export panel data
│
├── db/
│   └── schema_sqlite.sql      # Database schema
│
├── mapping/
│   └── mapping_index.yaml     # 38 index definitions + keywords
│
└── app/
    ├── __init__.py
    ├── main.py                # Entry point - run pipeline
    ├── db.py                  # Database operations
    ├── extract_pdf.py         # PDF extraction
    ├── external.py            # Yahoo Finance + manual data
    ├── compute.py             # Derived indicators
    └── utils.py               # Utility functions
```

## 🚀 Cài đặt

```bash
# Clone hoặc copy vào project
cd finance38

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Cài dependencies
pip install -r requirements.txt
```

## 📊 38 Chỉ số tài chính

| ID | Tên chỉ số | Nguồn |
|----|-----------|-------|
| 1-4 | Ownership (Managerial/State/Institutional/Foreign) | Manual |
| 5 | Total share outstanding | Yahoo |
| 6 | Net sales revenue | PDF |
| 7 | Total assets | PDF |
| 8-18 | Expenses (Selling, G&A, Manufacturing, R&D...) | PDF |
| 19-20 | Innovation (Product/Process) | Manual |
| 21 | Net Income | PDF |
| 22 | Total shareholders' equity | PDF |
| 23 | Market value of equity | Yahoo |
| 24-31 | Liabilities & Cash flow | PDF |
| 32 | Growth ratio | Computed |
| 33-37 | Other (Inventory, Dividend, EPS, Employees, PPE) | PDF |
| 38 | Firm age | Computed |

## 💻 Sử dụng

### Chạy full pipeline

```bash
# Chạy từ thư mục finance38
python -m app.main

# Hoặc
python app/main.py
```

### Options

```bash
# Chỉ định folder PDF khác
python -m app.main --filings ./BCTC

# Bỏ qua Yahoo Finance (offline mode)
python -m app.main --skip-yahoo

# Chỉ khởi tạo database
python -m app.main --init-only

# Xem thống kê
python -m app.main --stats
```

### Sử dụng trong code

```python
from app import init_database, extract_pdf, get_db

# Khởi tạo database
db = init_database()

# Trích xuất từ PDF
data = extract_pdf('path/to/HPG_2024.pdf')
print(data)  # {6: 123456789, 7: 987654321, ...}

# Query database
df = db.get_panel_long()
print(df)
```

## 📝 Chuẩn bị dữ liệu

### 1. Đặt file PDF

```
data/raw/filings/
├── HPG/
│   ├── HPG_2020.pdf
│   ├── HPG_2021.pdf
│   └── HPG_2022.pdf
├── VNM/
│   └── VNM_2020.pdf
└── ...
```

Định dạng tên file: `{MÃ_CK}_{NĂM}.pdf`

### 2. Manual data (ownership, innovation)

Tạo file CSV với format:
```csv
company_code,year,index_id,value
HPG,2020,1,5.5
HPG,2020,2,0
HPG,2020,3,45.2
...
```

Chạy với:
```bash
python -m app.main --manual manual_data.csv
```

## 🗄️ Database

SQLite database với các bảng:
- `finance_data`: Panel data (company, year, index_id, value)
- `index_reference`: Định nghĩa 38 chỉ số
- `companies`: Thông tin công ty
- `processing_log`: Log xử lý PDF

Query ví dụ:
```sql
-- Lấy tất cả data của HPG
SELECT * FROM finance_data WHERE company_code = 'HPG';

-- Pivot to wide format
SELECT company_code, year,
    MAX(CASE WHEN index_id = 6 THEN value END) as revenue,
    MAX(CASE WHEN index_id = 21 THEN value END) as net_income
FROM finance_data
GROUP BY company_code, year;
```

## 📤 Export

```python
from app import get_db

db = get_db()

# Export panel data dạng long
db.export_panel_csv(format='long')
# -> data/processed/panel_long.csv

# Export dạng wide (cho Stata/EViews)
db.export_panel_csv(format='wide')
# -> data/processed/panel_wide.csv
```

## ⚙️ Configuration

Copy `.env.example` thành `.env` và chỉnh sửa:

```bash
cp .env.example .env
```

Chỉnh các config trong `mapping/mapping_index.yaml` nếu cần thay đổi keywords trích xuất.

## 🔧 Troubleshooting

### PDF không trích xuất được

1. Kiểm tra PDF có text layer không (không phải scan):
   ```python
   import pdfplumber
   with pdfplumber.open('test.pdf') as pdf:
       print(pdf.pages[0].extract_text()[:500])
   ```

2. Nếu là PDF scan, cần OCR:
   - Cài Tesseract OCR
   - Cài thêm: `pip install pytesseract Pillow`

### Số liệu sai

1. Kiểm tra keywords trong `mapping/mapping_index.yaml`
2. Thêm keywords mới nếu BCTC dùng từ khác
3. Điều chỉnh `min_value` để lọc số rác

## 📜 License

MIT License

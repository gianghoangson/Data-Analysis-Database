# Hệ Thống Xử Lý Hàng Loạt Báo Cáo Tài Chính

## 📋 Mô Tả
Hệ thống tự động xử lý hàng loạt báo cáo tài chính PDF từ nhiều công ty, trích xuất 38 biến tài chính và lưu kết quả dạng CSV.

## 🗂️ Cấu Trúc Thư Mục

```
Data-Analysis-Database/
├── BCTC/                          # Thư mục chứa các báo cáo tài chính
│   ├── SAB/                       # Folder công ty SAB
│   │   ├── SAB_2020.pdf
│   │   ├── SAB_2021.pdf
│   │   ├── SAB_2022.pdf
│   │   ├── SAB_2023.pdf
│   │   └── SAB_2024.pdf
│   ├── VNM/                       # Folder công ty VNM
│   │   ├── VNM_2020.pdf
│   │   └── VNM_2021.pdf
│   ├── FPT/                       # Folder công ty FPT
│   ├── VCB/                       # Folder công ty VCB
│   └── ...                        # Các công ty khác (tổng ~15 công ty)
│
├── result/                        # Thư mục chứa kết quả (tự động tạo)
│   ├── SAB_2020.csv
│   ├── SAB_2021.csv
│   ├── VNM_2020.csv
│   └── ...
│
├── pdf_processor.py               # Module xử lý PDF
├── batch_runner.py                # Script chạy hàng loạt
└── laydatatu_vietstock.py         # Script gốc (xử lý đơn lẻ)
```

## 🚀 Cách Sử Dụng

### Bước 1: Chuẩn Bị Dữ Liệu
1. Tạo thư mục `BCTC` trong thư mục dự án
2. Tạo các folder con theo mã công ty (VD: SAB, VNM, FPT, VCB, HPG, ...)
3. Đặt các file PDF vào folder tương ứng với định dạng: `[MÃ]_[NĂM].pdf`
   - Ví dụ: `SAB_2020.pdf`, `SAB_2021.pdf`

### Bước 2: Cài Đặt Thư Viện
```bash
pip install pymupdf pytesseract pillow pandas yfinance openpyxl
```

### Bước 3: Cấu Hình (Tùy Chọn)
Mở file `batch_runner.py` và chỉnh sửa:

```python
# Đường dẫn Tesseract OCR (nếu khác)
TESSERACT_PATH = "D:/tesseract ocr/tesseract.exe"

# Thêm năm thành lập công ty (để tính tuổi công ty)
COMPANY_FOUNDING_YEARS = {
    "SAB": 1875,
    "VNM": 1976,
    "FPT": 1988,
    "VCB": 1963,
    # Thêm công ty khác...
}
```

### Bước 4: Chạy Batch Processing
```bash
python batch_runner.py
```

## 📊 Kết Quả

Mỗi file CSV sẽ chứa 38 biến tài chính:

| Biến | Mô Tả | Nguồn |
|------|-------|-------|
| 1-4 | Managerial/State/Institutional/Foreign ownership | Nhập tay |
| 5 | Total share outstanding | Yahoo Finance |
| 6-37 | Các chỉ số tài chính từ BCTC | OCR từ PDF |
| 38 | Firm age | Tính toán |

## 🔧 Các File Chính

### 1. `pdf_processor.py`
Module xử lý PDF, chứa class `FinancialReportProcessor`:
- `process_report()`: Xử lý một báo cáo
- `extract_pdf_data()`: Trích xuất dữ liệu từ PDF
- `get_market_data()`: Lấy dữ liệu từ Yahoo Finance

### 2. `batch_runner.py`
Script runner chính:
- `process_all_companies()`: Xử lý tất cả công ty
- `get_company_folders()`: Quét các folder công ty
- `get_pdf_files()`: Lấy danh sách PDF trong folder

### 3. `laydatatu_vietstock.py`
Script gốc (xử lý đơn lẻ) - giữ lại để tham khảo

## 📝 Ví Dụ Output

### Màn hình hiển thị khi chạy:
```
================================================================================
🚀 BẮT ĐẦU XỬ LÝ HÀNG LOẠT BÁO CÁO TÀI CHÍNH
================================================================================

📁 Tìm thấy 15 công ty:
   • FPT
   • HPG
   • SAB
   • VCB
   • VNM
   ...

================================================================================
📊 [1/15] CÔNG TY: SAB
================================================================================
   Tìm thấy 5 file báo cáo
   📄 Đang xử lý: SAB_2020
      → Lấy dữ liệu Yahoo Finance...
      ✓ Giá đóng cửa 2020: 185,000 VND
      → Quét PDF...
      ✓ Đã lưu: ./result/SAB_2020.csv
   📄 Đang xử lý: SAB_2021
      ...

================================================================================
📈 TỔNG KẾT
================================================================================
✓ Tổng số file xử lý:     75
✓ Thành công:             73
✗ Lỗi:                    2
📁 Kết quả lưu tại:       D:\...\result
================================================================================
🎉 HOÀN THÀNH!
```

## ⚙️ Tùy Chỉnh

### Thêm từ khóa OCR mới
Chỉnh sửa `OCR_KEYWORDS` trong `pdf_processor.py`:
```python
OCR_KEYWORDS = {
    "Từ khóa tiếng Việt": "Tên biến tiếng Anh",
    # Thêm từ khóa mới...
}
```

### Thay đổi đường dẫn
Trong `batch_runner.py`:
```python
BCTC_PATH = "./BCTC"       # Thư mục input
RESULT_PATH = "./result"   # Thư mục output
```

## 🐛 Xử Lý Lỗi

### Lỗi không tìm thấy Tesseract
```
Error: Tesseract not found
```
**Giải pháp**: Cài đặt Tesseract OCR và cập nhật đường dẫn trong `batch_runner.py`

### Lỗi không tìm thấy thư mục BCTC
```
❌ Không tìm thấy thư mục BCTC
```
**Giải pháp**: Tạo thư mục `BCTC` và cấu trúc folder như hướng dẫn

### File PDF không đúng định dạng
```
⚠ Bỏ qua file không đúng định dạng: report.pdf
```
**Giải pháp**: Đổi tên file theo format `[MÃ]_[NĂM].pdf`

## 📞 Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra cấu trúc thư mục
2. Xác nhận định dạng tên file
3. Kiểm tra đường dẫn Tesseract
4. Xem log lỗi chi tiết trên màn hình

## 📝 Lưu Ý

- File PDF nên có chất lượng tốt để OCR hiệu quả
- Quá trình xử lý mất ~1-2 phút cho mỗi file PDF
- Với 15 công ty × 5 năm = 75 file, tổng thời gian ~2-3 giờ
- Kết quả được lưu dạng CSV để dễ import vào Excel/Python
- Backup file PDF gốc trước khi xử lý

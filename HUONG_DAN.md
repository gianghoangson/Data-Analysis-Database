# 📚 Hướng Dẫn Sử Dụng - Hệ Thống Xử Lý BCTC

## 📂 Giải Thích Các File Trong Project

### 1️⃣ **setup_demo.ps1** - Script Chuẩn Bị Ban Đầu
**Tác dụng:** Tạo cấu trúc thư mục mẫu để bắt đầu

**Chức năng:**
- Tự động tạo folder `BCTC/` với 3 công ty mẫu (SAB, VNM, FPT)
- Hiển thị hướng dẫn đặt tên file PDF
- Giúp setup nhanh môi trường làm việc

**Khi nào dùng:**
- Lần đầu tiên setup project
- Khi muốn tạo thêm folder công ty mới nhanh

**Cách chạy:**
```powershell
.\setup_demo.ps1
```

**Kết quả:**
```
BCTC/
├── SAB/    (folder trống - sẵn sàng nhận PDF)
├── VNM/    (folder trống - sẵn sàng nhận PDF)
└── FPT/    (folder trống - sẵn sàng nhận PDF)
```

---

### 2️⃣ **pdf_processor.py** - Module Xử Lý Chính
**Tác dụng:** Chứa logic xử lý PDF và trích xuất dữ liệu

**Class chính:** `FinancialReportProcessor`

**Chức năng:**
- 🔍 Đọc và OCR file PDF (dùng Tesseract + PyMuPDF)
- 📊 Lấy dữ liệu thị trường từ Yahoo Finance
- 🔢 Trích xuất 38 biến tài chính theo từ khóa
- 💾 Xuất kết quả ra CSV

**Methods quan trọng:**
- `process_report()` - Xử lý một báo cáo hoàn chỉnh
- `extract_pdf_data()` - Quét PDF và tìm từ khóa
- `get_market_data()` - Lấy giá cổ phiếu từ Yahoo

**Khi nào dùng:**
- File này là **thư viện** - không chạy trực tiếp
- Được import bởi `batch_runner.py`
- Có thể import vào script khác để xử lý đơn lẻ

**Ví dụ sử dụng độc lập:**
```python
from pdf_processor import FinancialReportProcessor

processor = FinancialReportProcessor()
df = processor.process_report(
    pdf_path="BCTC/SAB/SAB_2020.pdf",
    symbol="SAB",
    year=2020,
    output_csv="result/SAB_2020.csv"
)
```

---

### 3️⃣ **batch_runner.py** - Script Chạy Hàng Loạt
**Tác dụng:** Tự động xử lý tất cả công ty và tất cả năm

**Chức năng:**
- 🔄 Quét tất cả folder trong `BCTC/`
- 📋 Tìm tất cả file PDF theo format `[MÃ]_[NĂM].pdf`
- ⚙️ Xử lý từng file tuần tự
- 📊 Hiển thị tiến độ real-time trên màn hình
- ✅ Báo cáo tổng kết (thành công/lỗi)

**Khi nào dùng:**
- Khi có nhiều công ty, nhiều năm cần xử lý
- Muốn xử lý tự động toàn bộ thư mục BCTC

**Cách chạy:**
```powershell
python batch_runner.py
```

**Cấu hình quan trọng:**
```python
# Có thể chỉnh sửa trong file
BCTC_PATH = "./BCTC"          # Thư mục chứa PDF
RESULT_PATH = "./result"       # Thư mục lưu CSV
TESSERACT_PATH = "D:/tesseract ocr/tesseract.exe"

# Thêm năm thành lập công ty
COMPANY_FOUNDING_YEARS = {
    "SAB": 1875,
    "VNM": 1976,
    # Thêm công ty khác...
}
```

**Output:**
```
result/
├── SAB_2020.csv
├── SAB_2021.csv
├── VNM_2020.csv
└── ...
```

---

### 4️⃣ **laydatatu_vietstock.py** - Script Gốc (Xử Lý Đơn Lẻ)
**Tác dụng:** Script ban đầu - xử lý 1 file PDF cụ thể

**Chức năng:**
- Xử lý **1 công ty, 1 năm** cố định
- Xuất kết quả ra Excel (`.xlsx`)
- Code gốc trước khi được refactor

**Khi nào dùng:**
- Test nhanh với 1 file PDF
- Muốn xem kết quả dạng Excel thay vì CSV
- Tham khảo logic xử lý ban đầu

**Cách dùng:**
1. Mở file
2. Chỉnh cấu hình ở đầu file:
```python
input_pdf = "C:/path/to/SAB_2021.pdf"
symbol = "SAB"
year = 2021
```
3. Chạy:
```powershell
python laydatatu_vietstock.py
```

**Hạn chế:**
- ❌ Phải sửa code mỗi lần đổi công ty/năm
- ❌ Không xử lý hàng loạt
- ✅ Đơn giản, dễ debug

---

### 5️⃣ **README_BATCH.md** - Hướng Dẫn Chi Tiết
**Tác dụng:** Tài liệu đầy đủ về hệ thống batch processing

**Nội dung:**
- 📖 Giải thích cấu trúc thư mục chi tiết
- 🚀 Hướng dẫn sử dụng từng bước
- 🔧 Cách cấu hình và tùy chỉnh
- 🐛 Xử lý lỗi thường gặp
- 📊 Giải thích output

**Khi nào đọc:**
- Lần đầu sử dụng hệ thống
- Gặp lỗi và cần troubleshoot
- Muốn hiểu rõ cách thức hoạt động

---

### 6️⃣ **HUONG_DAN.md** (file này)
**Tác dụng:** Hướng dẫn ngắn gọn, dễ hiểu về từng file

**Mục đích:** Giúp nhanh chóng hiểu được vai trò của mỗi file

---

## 🎯 Quy Trình Làm Việc Đề Xuất

### Lần Đầu Setup (1 lần duy nhất)
```
1. Chạy setup_demo.ps1 → Tạo cấu trúc folder
2. Copy file PDF vào folder tương ứng
3. Cấu hình batch_runner.py (nếu cần)
```

### Xử Lý Hàng Loạt (Chính)
```
1. Đặt PDF vào BCTC/[MÃ]/[MÃ]_[NĂM].pdf
2. Chạy: python batch_runner.py
3. Lấy kết quả trong folder result/
```

### Xử Lý Đơn Lẻ (Test nhanh)
```
1. Sửa cấu hình trong laydatatu_vietstock.py
2. Chạy: python laydatatu_vietstock.py
3. Lấy file Excel kết quả
```

---

## 📊 So Sánh 3 Cách Xử Lý

| Đặc điểm | batch_runner.py | laydatatu_vietstock.py | pdf_processor.py |
|----------|----------------|----------------------|------------------|
| **Mục đích** | Xử lý hàng loạt | Xử lý đơn lẻ | Thư viện |
| **Input** | Cả folder BCTC/ | 1 file PDF cố định | Gọi từ code khác |
| **Output** | Nhiều CSV | 1 file Excel | DataFrame/CSV |
| **Cấu hình** | 1 lần trong file | Mỗi lần chạy phải sửa | Truyền tham số |
| **Hiển thị** | ✅ Tiến độ chi tiết | ✅ Đơn giản | ❌ Không có |
| **Khuyến nghị** | ⭐⭐⭐⭐⭐ Chính | ⭐⭐⭐ Test | ⭐⭐⭐⭐ Nâng cao |

---

## 🛠️ Cấu Trúc Thư Mục Hoàn Chỉnh

```
Data-Analysis-Database/
│
├── 📄 setup_demo.ps1           # [CHẠY 1 LẦN] Setup ban đầu
├── 📄 batch_runner.py          # [CHẠY CHÍNH] Xử lý hàng loạt
├── 📄 pdf_processor.py         # [THƯ VIỆN] Module xử lý
├── 📄 laydatatu_vietstock.py   # [TEST] Xử lý đơn lẻ
│
├── 📖 HUONG_DAN.md             # Hướng dẫn ngắn (file này)
├── 📖 README_BATCH.md          # Hướng dẫn chi tiết
├── 📖 README.md                # Ghi chú ban đầu
│
├── 📁 BCTC/                    # [INPUT] Chứa PDF
│   ├── SAB/
│   │   ├── SAB_2020.pdf
│   │   ├── SAB_2021.pdf
│   │   └── ...
│   ├── VNM/
│   └── ...
│
├── 📁 result/                  # [OUTPUT] Kết quả CSV
│   ├── SAB_2020.csv
│   ├── SAB_2021.csv
│   └── ...
│
└── 📁 vietstock_scraper/       # [THAM KHẢO] Code từ GitHub
    └── (code scraping từ Vietstock API)
```

---

## ❓ FAQ - Câu Hỏi Thường Gặp

### **Q1: File nào tôi cần chạy?**
**A:** Chạy `batch_runner.py` - nó sẽ tự động xử lý tất cả

### **Q2: Tôi có 20 công ty, làm thế nào?**
**A:** 
```powershell
# Tạo 20 folder trong BCTC/
mkdir BCTC/HPG, BCTC/VCB, BCTC/MBB, ...
# Đặt PDF vào
# Chạy batch_runner.py → Xong!
```

### **Q3: Tôi chỉ muốn xử lý 1 file test?**
**A:** Dùng `laydatatu_vietstock.py` - sửa đường dẫn PDF và chạy

### **Q4: File PDF tên khác được không? (VD: BaoCaoTaiChinh_SAB.pdf)**
**A:** Không. Phải đổi tên theo format: `SAB_2020.pdf`

### **Q5: Kết quả lưu ở đâu?**
**A:** Folder `result/` - file CSV, mỗi file là 1 công ty-năm

### **Q6: Tôi muốn thay đổi từ khóa OCR?**
**A:** Sửa `OCR_KEYWORDS` trong `pdf_processor.py`

### **Q7: setup_demo.ps1 có bắt buộc chạy không?**
**A:** Không bắt buộc. Nó chỉ giúp tạo folder nhanh. Bạn có thể tạo thủ công.

---

## 🚀 Quick Start - 3 Bước

```powershell
# Bước 1: Setup (1 lần)
.\setup_demo.ps1

# Bước 2: Đặt PDF vào folder
# Copy file vào BCTC/SAB/SAB_2020.pdf, BCTC/SAB/SAB_2021.pdf, ...

# Bước 3: Chạy
python batch_runner.py
```

**Xong!** Lấy kết quả trong `result/` 🎉

---

## 💡 Tips

1. **Đặt tên file đúng format** - Nếu không sẽ bị bỏ qua
2. **PDF chất lượng tốt** - OCR mới chính xác
3. **Chạy từng công ty test** - Trước khi chạy hết 15 công ty
4. **Backup PDF gốc** - Phòng trường hợp cần xử lý lại
5. **Kiểm tra result/** - Đảm bảo dữ liệu đúng trước khi dùng

---

📝 **Lưu ý:** File này là bản tóm tắt. Xem `README_BATCH.md` để hiểu sâu hơn!

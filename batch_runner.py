"""
Batch Runner - Xử lý hàng loạt báo cáo tài chính từ nhiều công ty
Cấu trúc thư mục:
    BCTC/
        SAB/
            SAB_2020.pdf
            SAB_2021.pdf
            ...
        VNM/
            VNM_2020.pdf
            ...
    result/
        SAB_2020.csv
        SAB_2021.csv
        ...
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from pdf_processor import FinancialReportProcessor

# Thông tin năm thành lập công ty (có thể thêm vào đây)
COMPANY_FOUNDING_YEARS = {
    "SAB": 1875,
    "VNM": 1976,
    # Thêm các công ty khác tại đây
    # "FPT": 1988,
    # "VCB": 1963,
}

def get_company_folders(bctc_path):
    """
    Lấy danh sách các folder công ty trong thư mục BCTC
    
    Args:
        bctc_path: Đường dẫn đến thư mục BCTC
        
    Returns:
        list: Danh sách tên các folder công ty
    """
    if not os.path.exists(bctc_path):
        print(f"❌ Không tìm thấy thư mục BCTC: {bctc_path}")
        return []
    
    folders = [f for f in os.listdir(bctc_path) 
               if os.path.isdir(os.path.join(bctc_path, f))]
    
    return sorted(folders)

def get_pdf_files(company_folder_path, company_code):
    """
    Lấy danh sách các file PDF trong folder công ty
    
    Args:
        company_folder_path: Đường dẫn đến folder công ty
        company_code: Mã công ty (VD: SAB)
        
    Returns:
        list: Danh sách tuple (file_path, year)
    """
    pdf_files = []
    
    if not os.path.exists(company_folder_path):
        return pdf_files
    
    for filename in os.listdir(company_folder_path):
        if filename.endswith('.pdf'):
            # Tách năm từ tên file (VD: SAB_2020.pdf -> 2020)
            try:
                # Loại bỏ phần mở rộng .pdf
                name_without_ext = filename.replace('.pdf', '')
                # Tách theo dấu gạch dưới
                parts = name_without_ext.split('_')
                if len(parts) >= 2:
                    year = int(parts[-1])  # Lấy phần cuối cùng là năm
                    file_path = os.path.join(company_folder_path, filename)
                    pdf_files.append((file_path, year))
            except ValueError:
                print(f"   ⚠ Bỏ qua file không đúng định dạng: {filename}")
                continue
    
    # Sắp xếp theo năm
    pdf_files.sort(key=lambda x: x[1])
    
    return pdf_files

def process_all_companies(bctc_path="./BCTC", result_path="./result", 
                         tesseract_path="D:/tesseract ocr/tesseract.exe"):
    """
    Xử lý tất cả các công ty trong thư mục BCTC
    
    Args:
        bctc_path: Đường dẫn thư mục BCTC
        result_path: Đường dẫn thư mục lưu kết quả
        tesseract_path: Đường dẫn Tesseract OCR
    """
    print("="*80)
    print("🚀 BẮT ĐẦU XỬ LÝ HÀNG LOẠT BÁO CÁO TÀI CHÍNH")
    print("="*80)
    
    # Tạo thư mục result nếu chưa có
    os.makedirs(result_path, exist_ok=True)
    
    # Khởi tạo processor
    processor = FinancialReportProcessor(tesseract_path=tesseract_path)
    
    # Lấy danh sách công ty
    company_folders = get_company_folders(bctc_path)
    
    if not company_folders:
        print("❌ Không tìm thấy folder công ty nào trong BCTC/")
        return
    
    print(f"\n📁 Tìm thấy {len(company_folders)} công ty:")
    for company in company_folders:
        print(f"   • {company}")
    
    print("\n" + "="*80)
    
    # Thống kê
    total_files = 0
    success_count = 0
    error_count = 0
    
    # Xử lý từng công ty
    for idx, company_code in enumerate(company_folders, 1):
        print(f"\n{'='*80}")
        print(f"📊 [{idx}/{len(company_folders)}] CÔNG TY: {company_code}")
        print(f"{'='*80}")
        
        company_folder_path = os.path.join(bctc_path, company_code)
        
        # Lấy danh sách file PDF
        pdf_files = get_pdf_files(company_folder_path, company_code)
        
        if not pdf_files:
            print(f"   ⚠ Không tìm thấy file PDF nào trong {company_code}/")
            continue
        
        print(f"   Tìm thấy {len(pdf_files)} file báo cáo")
        
        # Lấy năm thành lập
        nam_thanh_lap = COMPANY_FOUNDING_YEARS.get(company_code)
        
        # Xử lý từng file PDF
        for pdf_path, year in pdf_files:
            total_files += 1
            
            try:
                # Tạo tên file output
                output_filename = f"{company_code}_{year}.csv"
                output_path = os.path.join(result_path, output_filename)
                
                # Xử lý báo cáo
                processor.process_report(
                    pdf_path=pdf_path,
                    symbol=company_code,
                    year=year,
                    nam_thanh_lap=nam_thanh_lap,
                    output_csv=output_path
                )
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"      ✗ LỖI: {e}")
    
    # Tổng kết
    print("\n" + "="*80)
    print("📈 TỔNG KẾT")
    print("="*80)
    print(f"✓ Tổng số file xử lý:     {total_files}")
    print(f"✓ Thành công:             {success_count}")
    print(f"✗ Lỗi:                    {error_count}")
    print(f"📁 Kết quả lưu tại:       {os.path.abspath(result_path)}")
    print("="*80)
    print("🎉 HOÀN THÀNH!\n")

def main():
    """
    Hàm main để chạy batch processing
    """
    # Cấu hình đường dẫn
    BCTC_PATH = "./BCTC"  # Thư mục chứa các folder công ty
    RESULT_PATH = "./result"  # Thư mục lưu kết quả
    TESSERACT_PATH = "D:/tesseract ocr/tesseract.exe"  # Đường dẫn Tesseract
    
    # Kiểm tra thư mục BCTC
    if not os.path.exists(BCTC_PATH):
        print(f"❌ Không tìm thấy thư mục BCTC: {BCTC_PATH}")
        print(f"\n📝 Hướng dẫn:")
        print(f"   1. Tạo thư mục 'BCTC' trong thư mục hiện tại")
        print(f"   2. Tạo các folder công ty bên trong (VD: SAB, VNM, FPT, ...)")
        print(f"   3. Đặt các file PDF theo định dạng: [MÃ]_[NĂM].pdf")
        print(f"      Ví dụ: SAB_2020.pdf, SAB_2021.pdf, VNM_2020.pdf")
        print(f"\n   Cấu trúc thư mục:")
        print(f"   BCTC/")
        print(f"   ├── SAB/")
        print(f"   │   ├── SAB_2020.pdf")
        print(f"   │   ├── SAB_2021.pdf")
        print(f"   │   └── SAB_2022.pdf")
        print(f"   ├── VNM/")
        print(f"   │   ├── VNM_2020.pdf")
        print(f"   │   └── VNM_2021.pdf")
        print(f"   └── ...")
        return
    
    # Chạy xử lý
    try:
        process_all_companies(
            bctc_path=BCTC_PATH,
            result_path=RESULT_PATH,
            tesseract_path=TESSERACT_PATH
        )
    except KeyboardInterrupt:
        print("\n\n⚠ Đã dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi nghiêm trọng: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

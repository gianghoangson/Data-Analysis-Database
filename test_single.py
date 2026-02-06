"""
Script test nhanh - Xử lý 1 file PDF cụ thể
"""

from pdf_processor import FinancialReportProcessor

def test_single_file():
    """Test xử lý 1 file PDF"""
    
    # Cấu hình
    PDF_PATH = "BCTC/HPG/HPG_2024.pdf"
    COMPANY_CODE = "HPG"
    YEAR = 2024
    NAM_THANH_LAP = 2007  # HPG thành lập 2007
    OUTPUT_CSV = "result/HPG_2024.csv"
    TESSERACT_PATH = "D:/tesseract ocr/tesseract.exe"
    
    print("="*80)
    print("🧪 TEST XỬ LÝ ĐỜN LẺ - HPG_2024")
    print("="*80)
    
    # Khởi tạo processor
    processor = FinancialReportProcessor(tesseract_path=TESSERACT_PATH)
    
    # Xử lý file
    try:
        df = processor.process_report(
            pdf_path=PDF_PATH,
            symbol=COMPANY_CODE,
            year=YEAR,
            nam_thanh_lap=NAM_THANH_LAP,
            output_csv=OUTPUT_CSV
        )
        
        print("\n" + "="*80)
        print("✅ HOÀN THÀNH!")
        print("="*80)
        print(f"📁 File kết quả: {OUTPUT_CSV}")
        print(f"📊 Số biến thu thập được: {df.notna().sum().sum()}/38")
        print("\n📋 Preview dữ liệu:")
        print(df.T.head(10))
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_file()

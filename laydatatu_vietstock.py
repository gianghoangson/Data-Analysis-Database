import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import pandas as pd
import re
import os
import yfinance as yf

# ==============================================================================
# 1. CẤU HÌNH
# ==============================================================================
input_pdf = "C:/Users/Giang Hoang Son/OneDrive/Desktop/data analyse with python/SAB/2021FS - CONSO - VN.pdf"
path_to_tesseract = "D:/tesseract ocr/tesseract.exe"

symbol = "SAB"
year = 2021
nam_thanh_lap = 1875

# ==============================================================================
# 2. DANH SÁCH BIẾN & TỪ KHÓA
# ==============================================================================
DATA_38_VARS = {
    # --- Nhập tay ---
    "1. Managerial ownership": None, "2. State ownership": None,
    "3. Institutional ownership": None, "4. Foreign ownership": None,
    # --- Yahoo Finance ---
    "5. Total share outstanding": None, "23. Market value of equity": None, "38. Firm age": None,
    # --- OCR PDF ---
    "6. Total sales revenue and Net sales revenue": None, "7. Total assets": None,
    "8. Selling expenses": None, "9. General and administrative expenditure": None,
    "10. Value of intangible assets": None, "11. Manufacturing overhead": None,
    "12. Net operating income": None, "13. Consumption of raw material": None,
    "14. Merchandise purchase of the year": None, "15. Work-in-progess goods purchase": None,
    "16. Outside manufacturing expenses": None, "17. Production cost": None,
    "18. R&D expenditure": None, "19. Product innovation": None, "20. Process innovation": None,
    "21. Net Income": None, "22. Total shareholders' equity": None,
    "24. Total liabilities": None, "25. Net cash from operating activities": None,
    "26. Capital expenditure": None, "27. Cash flows from investing activities": None,
    "28. Cash and cash equivalent": None, "29. Long-term debt": None,
    "30. Current assets": None, "31. Current liabiltiies": None,
    "32. Growth ratio": None, "33. Total inventory": None,
    "34. Divident payment": None, "35. EPS": None,
    "36. Number of employees": None, "37. Net plant, property and equipment": None
}

OCR_KEYWORDS = {
    "Doanh thu thuần": "6. Total sales revenue and Net sales revenue",
    "Tổng cộng tài sản": "7. Total assets",
    "Chi phí bán hàng": "8. Selling expenses",
    "Chi phí quản lý doanh nghiệp": "9. General and administrative expenditure",
    "Tài sản cố định vô hình": "10. Value of intangible assets",
    "Chi phí sản xuất chung": "11. Manufacturing overhead",
    "Lợi nhuận thuần từ hoạt động kinh doanh": "12. Net operating income",
    "Chi phí nguyên liệu, vật liệu": "13. Consumption of raw material",
    "Hàng hóa": "14. Merchandise purchase of the year",
    "Chi phí sản xuất, kinh doanh dở dang": "15. Work-in-progess goods purchase",
    "Chi phí dịch vụ mua ngoài": "16. Outside manufacturing expenses",
    "Tổng chi phí sản xuất": "17. Production cost", 
    "Chi phí nghiên cứu": "18. R&D expenditure",
    "Lợi nhuận sau thuế thu nhập doanh nghiệp": "21. Net Income",
    "Vốn chủ sở hữu": "22. Total shareholders' equity",
    "Nợ phải trả": "24. Total liabilities",
    "Lưu chuyển tiền thuần từ hoạt động kinh doanh": "25. Net cash from operating activities",
    "Tiền chi để mua sắm, xây dựng": "26. Capital expenditure",
    "Lưu chuyển tiền thuần từ hoạt động đầu tư": "27. Cash flows from investing activities",
    "Tiền và các khoản tương đương tiền": "28. Cash and cash equivalent",
    "Vay và nợ thuê tài chính dài hạn": "29. Long-term debt",
    "Tài sản ngắn hạn": "30. Current assets",
    "Nợ ngắn hạn": "31. Current liabiltiies",
    "Hàng tồn kho": "33. Total inventory",
    "Cổ tức, lợi nhuận đã trả": "34. Divident payment",
    "Lãi cơ bản trên cổ phiếu": "35. EPS",
    "Số lượng nhân viên": "36. Number of employees",
    "Tài sản cố định hữu hình": "37. Net plant, property and equipment"
}

# ==============================================================================
# 3. HÀM XỬ LÝ
# ==============================================================================

def get_market_data():
    print("----- [BƯỚC 1] ĐANG TẢI DỮ LIỆU THỊ TRƯỜNG (YAHOO) -----")
    ticker = f"{symbol}.VN"
    try:
        df_price = yf.download(ticker, start=f"{year}-12-25", end=f"{year}-12-31", progress=False)
        if not df_price.empty:
            close_price = float(df_price['Close'].iloc[-1])
            print(f"   ✅ Giá đóng cửa {year}: {close_price:,.0f} VND")
            try:
                ticker_info = yf.Ticker(ticker)
                shares = ticker_info.info.get('sharesOutstanding', 0)
                if shares is None or shares == 0:
                    shares = 641281000 
                    print("   ⚠️ Dùng SL Cổ phiếu mặc định.")
                DATA_38_VARS["5. Total share outstanding"] = shares
                DATA_38_VARS["23. Market value of equity"] = close_price * shares
            except: pass
        else: print("   ⚠️ Không tìm thấy dữ liệu giá.")
        DATA_38_VARS["38. Firm age"] = year - nam_thanh_lap
    except Exception as e: print(f"   ❌ Lỗi Module Yahoo: {e}")

# Hàm tách riêng để xử lý text, tránh viết lại 2 lần
def process_extracted_text(text, mode_name):
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        line_lower = line.lower()
        
        # --- Tìm số trong dòng ---
        matches = re.findall(r'\b\d{1,3}(?:[.,]\d{3})+(?:\.\d+)?\b', line)
        val = 0
        has_val = False
        if matches:
            raw_val = matches[0].replace('.', '').replace(',', '')
            try:
                val_temp = float(raw_val)
                if val_temp > 1000: 
                    val = val_temp
                    has_val = True
            except: pass
        
        # --- LOGIC 1: CHI PHÍ BÁN HÀNG (MAX) ---
        if "chi phí bán hàng" in line_lower:
            if has_val:
                curr_max = DATA_38_VARS.get("8. Selling expenses")
                if curr_max is None or val > curr_max:
                    DATA_38_VARS["8. Selling expenses"] = val
                    print(f"      🔥 [{mode_name}] Cập nhật CP Bán hàng (Max): {val:,.0f}")
            continue

        # --- LOGIC 2: CÁC BIẾN KHÁC (FIRST MATCH) ---
        if not has_val: continue
        
        for key_vn, key_en in OCR_KEYWORDS.items():
            if key_en == "8. Selling expenses": continue
            if key_vn.lower() in line_lower:
                # Chỉ lưu nếu chưa có (Để PSM 3 không ghi đè bậy lên kết quả chuẩn của PSM 6)
                if DATA_38_VARS[key_en] is None:
                    DATA_38_VARS[key_en] = val
                    print(f"      ✅ [{mode_name}] Bắt được: {key_en} = {val:,.0f}")

def get_pdf_data():
    print("\n----- [BƯỚC 2] ĐANG QUÉT PDF (CHẾ ĐỘ KÉP: PSM 6 + PSM 3) -----")
    pytesseract.pytesseract.tesseract_cmd = path_to_tesseract
    
    if not os.path.exists(input_pdf):
        print(f"❌ Lỗi: Không tìm thấy file {input_pdf}")
        return

    try:
        doc = fitz.open(input_pdf)
        print(f"   -> Đang quét {len(doc)} trang...")

        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image_bytes_io = io.BytesIO(img_bytes)
            
            # --- PHA 1: QUÉT BẰNG PSM 6 (Ưu tiên Bảng biểu, Số chính xác) ---
            image = Image.open(image_bytes_io) # Mở lại ảnh
            try:
                text_psm6 = pytesseract.image_to_string(image, lang='vie', config='--psm 6')
                process_extracted_text(text_psm6, "PSM 6")
            except: pass

            # --- PHA 2: QUÉT BẰNG PSM 3 (Vét các dòng bị PSM 6 bỏ sót) ---
            # Chỉ cần reset pointer của ảnh hoặc mở lại
            image.seek(0) 
            try:
                text_psm3 = pytesseract.image_to_string(image, lang='vie', config='--psm 3')
                process_extracted_text(text_psm3, "PSM 3")
            except: pass

    except Exception as e:
        print(f"   ❌ Lỗi Module PDF: {e}")

# ==============================================================================
# 4. CHẠY
# ==============================================================================
if __name__ == "__main__":
    get_market_data()
    get_pdf_data()
    
    print("\n----- [BƯỚC 3] TỔNG HỢP VÀ XUẤT FILE -----")
    df = pd.DataFrame([DATA_38_VARS])
    output_filename = "Ket_qua_38_Bien.xlsx"
    df.T.to_excel(output_filename)
    print(f"🎉 XONG! File dữ liệu nằm tại: {output_filename}")
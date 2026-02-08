import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import pandas as pd
import re
import os
import yfinance as yf
from pytesseract import Output
import cv2
import numpy as np

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
    # --- BIẾN TẠM (Dùng để hứng số liệu thành phần) ---
    "_temp_khau_hao": None,         # Hứng "Chi phí khấu hao"
    "_temp_cp_bang_tien_khac": None, # Hứng "Chi phí bằng tiền khác"
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
    # Thay vì map trực tiếp vào biến 11, ta map vào biến tạm
    "Chi phí khấu hao": "_temp_khau_hao", 
    "Chi phí khác": "_temp_cp_bang_tien_khac",
    
    "Doanh thu thuần": "6. Total sales revenue and Net sales revenue",
    "Tổng tài sản": "7. Total assets",
    "Chi phí bán hàng": "8. Selling expenses",
    "Chi phí quản lý doanh nghiệp": "9. General and administrative expenditure",
    "Tài sản cố định vô hình": "10. Value of intangible assets",
    "Chi phí sản xuất chung": "11. Manufacturing overhead",
    "Lợi nhuận thuần từ hoạt động kinh doanh": "12. Net operating income",
    "Chi phí nguyên vật liệu trong chi phí sản xuất": "13. Consumption of raw material",
    "Hàng hóa": "14. Merchandise purchase of the year",
    "Chi phí sản xuất kinh doanh dở dang": "15. Work-in-progess goods purchase",
    "Chi phí dịch vụ mua ngoài": "16. Outside manufacturing expenses",
    "Tổng chi phí sản xuất": "17. Production cost", 
    "Chi phí nghiên cứu": "18. R&D expenditure",
    "Lợi nhuận thuần sau thuế": "21. Net Income",
    "Vốn chủ sở hữu": "22. Total shareholders' equity",
    "Nợ phải trả": "24. Total liabilities",
    "Lưu chuyển tiền thuần từ hoạt động kinh doanh": "25. Net cash from operating activities",
    "Tiền chi mua sắm, xây dựng tài sản cố định": "26. Capital expenditure",
    "Lưu chuyển tiền thuần từ hoạt động đầu tư": "27. Cash flows from investing activities",
    "Tiền và các khoản tương đương tiền": "28. Cash and cash equivalent",
    "Vay và nợ thuê tài chính dài hạn": "29. Long-term debt",
    "Tài sản ngắn hạn": "30. Current assets",
    "Nợ ngắn hạn": "31. Current liabiltiies",
    "Hàng tồn kho": "33. Total inventory",
    "Tiền chi trả cổ tức": "34. Divident payment",
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

def targeted_ocr_refinement_v10(doc, data_vars, keywords_dict):
    print("\n----- [BƯỚC 2.5] PHÂN TÍCH LAYOUT & GHÉP DÒNG (v10 - FIX BIẾN 12) -----")
    
    missing_items = {vn: en for vn, en in keywords_dict.items() if data_vars.get(en) is None}
    if not missing_items: return

    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(img_cv, 180, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        d = pytesseract.image_to_data(thresh, lang='vie', output_type=Output.DICT)
        
        # GOM TỪ THÀNH DÒNG (Giữ nguyên logic tọa độ)
        lines = []
        curr_line = []
        last_id = None
        for i in range(len(d['text'])):
            txt = d['text'][i].strip()
            if txt:
                line_id = (d['block_num'][i], d['line_num'][i])
                if line_id != last_id and curr_line:
                    lines.append(" ".join(curr_line))
                    curr_line = []
                curr_line.append(txt)
                last_id = line_id
        if curr_line: lines.append(" ".join(curr_line))

        # DUYỆT CỬA SỔ TRƯỢT VỚI CHUẨN HÓA CHUỖI
        for vn_key, en_key in missing_items.items():
            if data_vars[en_key] is not None: continue
            
            # Chuẩn hóa keyword: Xóa dấu cách thừa, chuyển thường
            clean_kw = "".join(vn_key.lower().split()) 
            
            for i in range(len(lines)):
                for w_size in [1, 2, 3]: # Thử ghép đến 3 dòng
                    if i + w_size > len(lines): continue
                    
                    window_text = " ".join(lines[i:i+w_size]).lower()
                    # Chuẩn hóa cụm từ trong cửa sổ quét
                    clean_window = "".join(window_text.split())
                    
                    # So khớp không quan trọng khoảng cách/dấu cách
                    if clean_kw in clean_window:
                        # Tìm số trong cả khối cửa sổ
                        full_context = " ".join(lines[i:i+w_size])
                        # Regex bắt số âm/dương nghìn tỷ
                        matches = re.findall(r'\(?\d{1,3}(?:[.,\s]\d{3})+\)?', full_context)
                        
                        potential_vals = []
                        for m in matches:
                            c = m.replace('.','').replace(',','').replace(' ','')
                            neg = '(' in c
                            try:
                                val = float(re.sub(r'[()]', '', c))
                                if neg: val = -val
                                # Loại bỏ mã số (như mã 30 của biến 12)
                                if abs(val) > 1000000: potential_vals.append(val)
                            except: continue
                        
                        if potential_vals:
                            data_vars[en_key] = potential_vals[0]
                            print(f"    ✨ [v10 FIXED] {en_key} = {potential_vals[0]:,.0f}")
                            break
                if data_vars[en_key] is not None: break

import unicodedata

def khong_dau(text):
    """Loại bỏ hoàn toàn dấu tiếng Việt để so khớp linh hoạt"""
    if not text: return ""
    text = unicodedata.normalize('NFKD', text)
    return "".join([c for c in text if not unicodedata.combining(c)]).lower()

def targeted_ocr_refinement_v11(doc, data_vars, keywords_dict):
    print("\n----- [BƯỚC 2.5] CHIẾN THUẬT V11: FUZZY ANCHOR & RADIUS SEARCH -----")
    
    missing_items = {vn: en for vn, en in keywords_dict.items() if data_vars.get(en) is None}
    if not missing_items: return

    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(dpi=400) # 400 DPI là tỷ lệ vàng cho SAB
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        # Tiền xử lý ảnh chuyên sâu
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        img_cv = cv2.GaussianBlur(img_cv, (1, 1), 0)
        _, thresh = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Lấy text thô theo dòng
        raw_text = pytesseract.image_to_string(thresh, lang='vie', config='--psm 6')
        lines = [l.strip() for l in raw_text.split('\n') if len(l.strip()) > 5]

        for vn_key, en_key in missing_items.items():
            if data_vars[en_key] is not None: continue
            
            # Chuẩn hóa tên biến cần tìm
            target_clean = khong_dau(vn_key)
            # Lấy "mồi" là 12 ký tự đầu không dấu
            anchor_mồi = target_clean[:12]

            for i in range(len(lines)):
                # Nếu dòng hiện tại chứa "mồi"
                if anchor_mồi in khong_dau(lines[i]):
                    # GOM BÁN KÍNH: Lấy dòng hiện tại và 2 dòng tiếp theo
                    context_block = " ".join(lines[i : i+3])
                    context_clean = khong_dau(context_block)
                    
                    # Kiểm tra xem toàn bộ tên biến có nằm trong khối 3 dòng này không
                    if target_clean in context_clean or khong_dau(vn_key.split()[-1]) in context_clean:
                        # TRÍCH XUẤT SỐ: Tìm mọi cụm giống số tiền
                        # Pattern này bắt được: (1.223.348.339.323)
                        matches = re.findall(r'\(?\d{1,3}(?:[.,\s]\d{3})+\)?', context_block)
                        
                        potential_numbers = []
                        for m in matches:
                            # Dọn dẹp số cực sạch
                            num_str = m.replace('.', '').replace(',', '').replace(' ', '')
                            is_negative = '(' in num_str
                            num_only = re.sub(r'[()]', '', num_str)
                            
                            try:
                                val = float(num_only)
                                if is_negative: val = -val
                                # Sabeco dùng đơn vị đồng -> bỏ qua các mã số nhỏ (21, 30)
                                if abs(val) > 1000000:
                                    potential_numbers.append(val)
                            except: continue
                        
                        if potential_numbers:
                            # Số đầu tiên sau tên biến luôn là cột "Năm nay"
                            data_vars[en_key] = potential_numbers[0]
                            print(f"    ✅ [v11 SUCCESS] {en_key} = {potential_numbers[0]:,.0f}")
                            break
            if data_vars[en_key] is not None: break

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

        targeted_ocr_refinement_v11(doc, DATA_38_VARS, OCR_KEYWORDS)

    except Exception as e:
        print(f"   ❌ Lỗi Module PDF: {e}")

    
    # Tính biến 11
    val_khau_hao = DATA_38_VARS.get("_temp_khau_hao")
    val_cp_khac = DATA_38_VARS.get("_temp_cp_bang_tien_khac")
    
    # Chuyển về 0 nếu không tìm thấy (để cộng không bị lỗi)
    num_khau_hao = val_khau_hao if val_khau_hao else 0
    num_cp_khac = val_cp_khac if val_cp_khac else 0
    
    if num_khau_hao > 0 or num_cp_khac > 0:
        total_11 = num_khau_hao + num_cp_khac
        DATA_38_VARS["11. Manufacturing overhead"] = total_11
        print(f"      ✅ Đã tính Biến 11 = Khấu hao ({num_khau_hao:,.0f}) + CP Khác ({num_cp_khac:,.0f}) = {total_11:,.0f}")
    else:
        print("      ⚠️ Không tìm thấy số liệu Khấu hao hoặc CP Khác để cộng.")

    # Xóa biến tạm cho sạch file Excel
    if "_temp_khau_hao" in DATA_38_VARS: del DATA_38_VARS["_temp_khau_hao"]
    if "_temp_cp_bang_tien_khac" in DATA_38_VARS: del DATA_38_VARS["_temp_cp_bang_tien_khac"]

# ==============================================================================
# 4. CHẠY
# ==============================================================================
if __name__ == "__main__":
    get_market_data()
    get_pdf_data()
    
    print("\n----- [BƯỚC 3] TỔNG HỢP VÀ XUẤT FILE -----")
    df = pd.DataFrame([DATA_38_VARS])
    output_filename = "Ket_qua_38_Bien_Final.xlsx"
    df.T.to_excel(output_filename)
    print(f"🎉 XONG! File dữ liệu nằm tại: {output_filename}")
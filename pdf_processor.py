"""
Module xử lý báo cáo tài chính PDF
Trích xuất 38 biến tài chính từ PDF và dữ liệu thị trường
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import pandas as pd
import re
import os
import yfinance as yf
from datetime import datetime

class FinancialReportProcessor:
    """Class xử lý báo cáo tài chính từ PDF"""
    
    # Từ khóa OCR mapping
    OCR_KEYWORDS = {
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
    
    def __init__(self, tesseract_path="D:/tesseract ocr/tesseract.exe"):
        """
        Khởi tạo processor
        
        Args:
            tesseract_path: Đường dẫn đến Tesseract OCR
        """
        self.tesseract_path = tesseract_path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
    def initialize_data_dict(self):
        """Khởi tạo dictionary 38 biến"""
        return {
            # --- BIẾN TẠM (Dùng để hứng số liệu thành phần) ---
            "_temp_khau_hao": None,
            "_temp_cp_bang_tien_khac": None,
            # --- Nhập tay ---
            "1. Managerial ownership": None, 
            "2. State ownership": None,
            "3. Institutional ownership": None, 
            "4. Foreign ownership": None,
            # --- Yahoo Finance ---
            "5. Total share outstanding": None, 
            "23. Market value of equity": None, 
            "38. Firm age": None,
            # --- OCR PDF ---
            "6. Total sales revenue and Net sales revenue": None, 
            "7. Total assets": None,
            "8. Selling expenses": None, 
            "9. General and administrative expenditure": None,
            "10. Value of intangible assets": None, 
            "11. Manufacturing overhead": None,
            "12. Net operating income": None, 
            "13. Consumption of raw material": None,
            "14. Merchandise purchase of the year": None, 
            "15. Work-in-progess goods purchase": None,
            "16. Outside manufacturing expenses": None, 
            "17. Production cost": None,
            "18. R&D expenditure": None, 
            "19. Product innovation": None, 
            "20. Process innovation": None,
            "21. Net Income": None, 
            "22. Total shareholders' equity": None,
            "24. Total liabilities": None, 
            "25. Net cash from operating activities": None,
            "26. Capital expenditure": None, 
            "27. Cash flows from investing activities": None,
            "28. Cash and cash equivalent": None, 
            "29. Long-term debt": None,
            "30. Current assets": None, 
            "31. Current liabiltiies": None,
            "32. Growth ratio": None, 
            "33. Total inventory": None,
            "34. Divident payment": None, 
            "35. EPS": None,
            "36. Number of employees": None, 
            "37. Net plant, property and equipment": None
        }
    
    def get_market_data(self, symbol, year, nam_thanh_lap=None):
        """
        Lấy dữ liệu thị trường từ Yahoo Finance
        
        Args:
            symbol: Mã chứng khoán (VD: SAB)
            year: Năm báo cáo
            nam_thanh_lap: Năm thành lập công ty (để tính tuổi)
            
        Returns:
            dict: Dictionary chứa dữ liệu thị trường
        """
        data = {}
        ticker = f"{symbol}.VN"
        
        try:
            # Lấy giá cổ phiếu cuối năm
            df_price = yf.download(ticker, start=f"{year}-12-25", end=f"{year}-12-31", progress=False)
            if not df_price.empty:
                close_price = float(df_price['Close'].iloc[-1])
                print(f"      ✓ Giá đóng cửa {year}: {close_price:,.0f} VND")
                
                # Lấy số lượng cổ phiếu
                ticker_info = yf.Ticker(ticker)
                shares = ticker_info.info.get('sharesOutstanding', 0)
                if shares is None or shares == 0:
                    shares = 641281000  # Giá trị mặc định
                    print("      ⚠ Dùng SL Cổ phiếu mặc định")
                
                data["5. Total share outstanding"] = shares
                data["23. Market value of equity"] = close_price * shares
            else:
                print("      ⚠ Không tìm thấy dữ liệu giá")
            
            # Tính tuổi công ty
            if nam_thanh_lap:
                data["38. Firm age"] = year - nam_thanh_lap
                
        except Exception as e:
            print(f"      ✗ Lỗi lấy dữ liệu Yahoo: {e}")
        
        return data
    
    def process_text_line(self, text, data_dict, mode_name):
        """
        Xử lý text đã trích xuất từ PDF
        
        Args:
            text: Text từ OCR
            data_dict: Dictionary chứa dữ liệu
            mode_name: Tên chế độ OCR (PSM 6 hoặc PSM 3)
        """
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Tìm số trong dòng
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
                except:
                    pass
            
            # LOGIC 1: CHI PHÍ BÁN HÀNG (MAX)
            if "chi phí bán hàng" in line_lower:
                if has_val:
                    curr_max = data_dict.get("8. Selling expenses")
                    if curr_max is None or val > curr_max:
                        data_dict["8. Selling expenses"] = val
                        # print(f"         [{mode_name}] CP Bán hàng: {val:,.0f}")
                continue
            
            # LOGIC 2: CÁC BIẾN KHÁC (FIRST MATCH)
            if not has_val:
                continue
            
            for key_vn, key_en in self.OCR_KEYWORDS.items():
                if key_en == "8. Selling expenses":
                    continue
                if key_vn.lower() in line_lower:
                    if data_dict[key_en] is None:
                        data_dict[key_en] = val
                        # print(f"         [{mode_name}] {key_en} = {val:,.0f}")
    
    def extract_pdf_data(self, pdf_path, data_dict):
        """
        Trích xuất dữ liệu từ file PDF
        
        Args:
            pdf_path: Đường dẫn đến file PDF
            data_dict: Dictionary để lưu dữ liệu
        """
        if not os.path.exists(pdf_path):
            print(f"      ✗ Không tìm thấy file: {pdf_path}")
            return
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            for i in range(total_pages):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                image_bytes_io = io.BytesIO(img_bytes)
                
                # PSM 6 - Ưu tiên bảng biểu
                image = Image.open(image_bytes_io)
                try:
                    text_psm6 = pytesseract.image_to_string(image, lang='vie', config='--psm 6')
                    self.process_text_line(text_psm6, data_dict, "PSM6")
                except:
                    pass
                
                # PSM 3 - Vét các dòng bị bỏ sót
                image.seek(0)
                try:
                    text_psm3 = pytesseract.image_to_string(image, lang='vie', config='--psm 3')
                    self.process_text_line(text_psm3, data_dict, "PSM3")
                except:
                    pass
            
            doc.close()
            
            # Tính biến 11: Manufacturing overhead
            val_khau_hao = data_dict.get("_temp_khau_hao")
            val_cp_khac = data_dict.get("_temp_cp_bang_tien_khac")
            
            num_khau_hao = val_khau_hao if val_khau_hao else 0
            num_cp_khac = val_cp_khac if val_cp_khac else 0
            
            if num_khau_hao > 0 or num_cp_khac > 0:
                total_11 = num_khau_hao + num_cp_khac
                data_dict["11. Manufacturing overhead"] = total_11
            
            # Xóa biến tạm
            if "_temp_khau_hao" in data_dict:
                del data_dict["_temp_khau_hao"]
            if "_temp_cp_bang_tien_khac" in data_dict:
                del data_dict["_temp_cp_bang_tien_khac"]
                
        except Exception as e:
            print(f"      ✗ Lỗi xử lý PDF: {e}")
    
    def process_report(self, pdf_path, symbol, year, nam_thanh_lap=None, output_csv=None):
        """
        Xử lý một báo cáo tài chính hoàn chỉnh
        
        Args:
            pdf_path: Đường dẫn đến file PDF
            symbol: Mã chứng khoán
            year: Năm báo cáo
            nam_thanh_lap: Năm thành lập công ty
            output_csv: Đường dẫn file CSV output (nếu không có sẽ tự tạo)
            
        Returns:
            pandas.DataFrame: DataFrame chứa kết quả
        """
        print(f"   📄 Đang xử lý: {symbol}_{year}")
        
        # Khởi tạo dữ liệu
        data_dict = self.initialize_data_dict()
        
        # Bước 1: Lấy dữ liệu thị trường
        print(f"      → Lấy dữ liệu Yahoo Finance...")
        market_data = self.get_market_data(symbol, year, nam_thanh_lap)
        data_dict.update(market_data)
        
        # Bước 2: Trích xuất PDF
        print(f"      → Quét PDF...")
        self.extract_pdf_data(pdf_path, data_dict)
        
        # Bước 3: Tạo DataFrame
        df = pd.DataFrame([data_dict])
        
        # Bước 4: Lưu file CSV nếu được chỉ định
        if output_csv:
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            df.T.to_csv(output_csv, encoding='utf-8-sig')
            print(f"      ✓ Đã lưu: {output_csv}")
        
        return df

"""
Module xử lý BCTC cải tiến - Sử dụng PDFPlumber trích xuất trực tiếp
"""
import pdfplumber
import pandas as pd
import re
import os

class AdvancedFinancialReportProcessor:
    def __init__(self):
        # Mapping từ khóa sang biến (Thêm regex để bắt chính xác hơn)
        self.MAPPING = {
            "Total sales revenue and Net sales revenue": ["Doanh thu bán hàng và cung cấp dịch vụ", "Doanh thu thuần"],
            "Total assets": ["TỔNG TÀI SẢN", "TỔNG CỘNG TÀI SẢN"],
            "Selling expenses": ["Chi phí bán hàng"],
            "General and administrative expenditure": ["Chi phí quản lý doanh nghiệp"],
            "Net operating income": ["Lợi nhuận thuần từ hoạt động kinh doanh"],
            "Net Income": ["Lợi nhuận sau thuế thu nhập doanh nghiệp", "Lợi nhuận sau thuế"],
            "Total shareholders' equity": ["Vốn chủ sở hữu"],
            "Total liabilities": ["Nợ phải trả"],
            "Net cash from operating activities": ["Lưu chuyển tiền thuần từ hoạt động kinh doanh"],
            "Current assets": ["Tài sản ngắn hạn"],
            "Total inventory": ["Hàng tồn kho"],
            # Thêm các biến khác tùy nhu cầu...
        }

    def clean_number(self, text):
        """Chuyển đổi chuỗi tiền tệ VN (100.000) sang float"""
        if not text: return None
        # Xử lý số âm trong ngoặc: (100.000) -> -100000
        is_negative = False
        if "(" in text and ")" in text:
            is_negative = True
            text = text.replace("(", "").replace(")", "")
            
        # Xóa dấu chấm phân cách hàng nghìn, giữ lại dấu phẩy thập phân (nếu có)
        # BCTC Việt Nam: 100.000.000
        clean_text = re.sub(r"[^0-9]", "", text) 
        
        try:
            val = float(clean_text)
            return -val if is_negative else val
        except:
            return None

    def extract_from_pdf(self, pdf_path):
        if not os.path.exists(pdf_path):
            print(f"Không tìm thấy file: {pdf_path}")
            return {}

        extracted_data = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Đang xử lý {len(pdf.pages)} trang...")
            
            for page in pdf.pages:
                # Trích xuất text theo cấu trúc từ trái sang phải, trên xuống dưới
                rows = page.extract_text(layout=True).split('\n')
                
                for line in rows:
                    line_text = line.strip()
                    
                    # Kiểm tra từng từ khóa
                    for key, keywords in self.MAPPING.items():
                        # Nếu đã tìm thấy giá trị rồi thì thôi (tránh trùng lặp không mong muốn)
                        # Hoặc có thể bỏ check này nếu muốn lấy giá trị cuối cùng
                        if key in extracted_data and extracted_data[key] > 0: 
                            continue

                        for kw in keywords:
                            # Kiểm tra keyword có trong dòng không (Case insensitive)
                            if kw.lower() in line_text.lower():
                                # LOGIC QUAN TRỌNG: Tách số từ dòng
                                # Tìm tất cả các chuỗi số có dạng tiền tệ
                                # Regex này bắt: số, số trong ngoặc (), có dấu chấm
                                number_matches = re.findall(r'\(?[\d\.]+\)?', line_text)
                                
                                # Lọc các số rác (số trang, số thuyết minh nhỏ)
                                valid_numbers = []
                                for num_str in number_matches:
                                    val = self.clean_number(num_str)
                                    # Giả sử số liệu tài chính phải > 1 tỷ (hoặc > 1000 tùy đơn vị) 
                                    # để tránh lấy nhầm số thuyết minh
                                    if val and abs(val) > 1000: 
                                        valid_numbers.append(val)
                                
                                if valid_numbers:
                                    # QUY TẮC:
                                    # BCTC thường có cột: [Thuyết minh] [Năm nay] [Năm trước]
                                    # Số "Năm nay" thường là số ĐẦU TIÊN (bên trái) hoặc số LỚN HƠN
                                    # Ở đây mình lấy số đầu tiên tìm thấy bên phải text
                                    
                                    # Cách an toàn: Lấy số đầu tiên trong danh sách số tìm được
                                    # (Vì layout=True thường giữ khoảng cách)
                                    extracted_data[key] = valid_numbers[0]
                                    print(f"Found {key}: {valid_numbers[0]:,.0f}")
                                    break # Đã tìm thấy keyword này trong dòng
        
        return extracted_data

# --- CHẠY THỬ ---
processor = AdvancedFinancialReportProcessor()
data = processor.extract_from_pdf("HPG_2024.pdf")

# Hiển thị kết quả
df_result = pd.DataFrame([data])
print("\nKẾT QUẢ TRÍCH XUẤT:")
print(df_result.T)
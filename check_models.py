import google.generativeai as genai

# Thay API Key của bạn vào dòng dưới
API_KEY = "" 
genai.configure(api_key=API_KEY)

print("🔍 ĐANG TÌM KIẾM CÁC MODEL KHẢ DỤNG...")
print("-" * 50)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

print("-" * 50)
import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# ตั้งค่า API Key จาก Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
else:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Secrets")
    st.stop()

# หน้า UI
st.title("🗑️ AI แยกขยะ")
st.write("📷 ถ่ายหรืออัปโหลดภาพขยะ แล้ว AI จะบอกว่าต้องทิ้งถังไหน")

# เลือกวิธีอัปโหลด
upload_method = st.radio("เลือกวิธีอัปโหลดภาพ:", ["📸 ถ่ายรูป", "📁 อัปโหลดไฟล์"])

uploaded_file = None

if upload_method == "📸 ถ่ายรูป":
    uploaded_file = st.camera_input("ถ่ายภาพขยะ")
else:
    uploaded_file = st.file_uploader("อัปโหลดภาพขยะ", type=["jpg","jpeg","png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="ภาพที่อัปโหลด", width=300)
    
    if st.button("🤖 วิเคราะห์ขยะ"):
        with st.spinner("กำลังวิเคราะห์..."):
            try:
                response = model.generate_content([
                    """วิเคราะห์ขยะในภาพนี้แล้วตอบเป็นภาษาไทยในรูปแบบนี้:
                    
                    🏷️ ประเภทขยะ: [ชื่อขยะ]
                    ♻️ จำแนกเป็น: [พลาสติก/กระดาษ/แก้ว/โลหะ/ขยะอินทรีย์/ขยะอันตราย/ขยะทั่วไป]
                    🗑️ ทิ้งที่: [ถังสีอะไร และวิธีทิ้งที่ถูกต้อง]
                    💡 เคล็ดลับ: [ข้อแนะนำเพิ่มเติม เช่น ล้างก่อนทิ้ง หรือแยกฝา]
                    """,
                    image
                ])
                
                st.success("✅ วิเคราะห์เสร็จแล้ว!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

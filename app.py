import streamlit as st
import google.generativeai as genai
from PIL import Image

# =========================
# CONFIG GEMINI
# =========================

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets")
    st.stop()

genai.configure(api_key=api_key)


# Cache model เพื่อไม่ให้สร้างใหม่ทุกครั้ง
@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        "gemini-3.6-flash",
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 150,
        }
    )


model = load_model()


# =========================
# PAGE UI
# =========================

st.set_page_config(
    page_title="AI แยกขยะ",
    page_icon="🗑️",
    layout="centered"
)

st.title("🗑️ AI แยกขยะ")

st.write(
    "📷 ถ่ายหรืออัปโหลดภาพขยะ "
    "แล้ว AI จะบอกว่าต้องทิ้งลงถังไหน"
)


# =========================
# UPLOAD METHOD
# =========================

upload_method = st.radio(
    "เลือกวิธี:",
    [
        "📸 ถ่ายรูป",
        "📁 อัปโหลดไฟล์"
    ],
    horizontal=True
)


uploaded_file = None


if upload_method == "📸 ถ่ายรูป":

    uploaded_file = st.camera_input(
        "ถ่ายภาพขยะ"
    )

else:

    uploaded_file = st.file_uploader(
        "อัปโหลดภาพขยะ",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )


# =========================
# IMAGE
# =========================

if uploaded_file is not None:

    image = Image.open(
        uploaded_file
    ).convert("RGB")

    st.image(
        image,
        caption="ภาพที่ต้องการตรวจสอบ",
        width=350
    )


    # =========================
    # ANALYZE BUTTON
    # =========================

    if st.button(
        "🔍 ตรวจสอบว่าต้องทิ้งถังไหน",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "🤖 กำลังตรวจสอบ..."
        ):

            try:

                # =========================
                # ลดขนาดรูป
                # =========================

                ai_image = image.copy()

                ai_image.thumbnail(
                    (800, 800),
                    Image.Resampling.LANCZOS
                )


                # =========================
                # PROMPT
                # =========================

                prompt = """
คุณคือ AI สำหรับช่วยแยกขยะ

ดูสิ่งของหรือขยะหลักในภาพ
แล้วตัดสินใจว่าควรทิ้งลงถังขยะประเภทใด

ให้เลือกเพียง 1 ถังจากรายการนี้:

🟢 ถังขยะรีไซเคิล
สำหรับ:
- ขวดพลาสติก
- กระป๋อง
- ขวดแก้ว
- กระดาษ
- กล่องกระดาษ
- วัสดุที่สามารถนำกลับมาใช้ใหม่ได้

🔵 ถังขยะทั่วไป
สำหรับ:
- ซองขนม
- ถุงพลาสติกเปื้อน
- โฟม
- ทิชชู่
- ขยะที่ไม่สามารถรีไซเคิลได้

🟡 ถังขยะอินทรีย์
สำหรับ:
- เศษอาหาร
- ผัก
- ผลไม้
- ใบไม้
- ขยะที่ย่อยสลายได้

🔴 ถังขยะอันตราย
สำหรับ:
- แบตเตอรี่
- ถ่านไฟฉาย
- หลอดไฟ
- กระป๋องสารเคมี
- ภาชนะสารเคมี
- อุปกรณ์อิเล็กทรอนิกส์บางประเภท


ตอบภาษาไทยสั้นๆ เท่านั้น

รูปแบบคำตอบ:

### 🗑️ ต้องทิ้งที่
[ชื่อถัง]

### ✅ ก่อนทิ้ง
[คำแนะนำสั้นๆ ไม่เกิน 1 ประโยค]


ข้อกำหนด:
- เลือกถังเพียง 1 ถัง
- เน้นว่าต้องทิ้งถังไหน
- ไม่ต้องบอกชื่อขยะ
- ไม่ต้องอธิบายเหตุผลยาว
- ถ้าไม่แน่ใจ ให้เลือกถังที่ปลอดภัยและเหมาะสมที่สุด
"""


                # =========================
                # CALL GEMINI
                # =========================

                response = model.generate_content(
                    [
                        prompt,
                        ai_image
                    ]
                )


                # =========================
                # RESULT
                # =========================

                st.success(
                    "✅ ตรวจสอบเรียบร้อย"
                )

                st.markdown(
                    response.text
                )


            except Exception as e:

                st.error(
                    f"❌ เกิดข้อผิดพลาด: {str(e)}"
                )

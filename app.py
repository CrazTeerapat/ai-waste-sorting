import streamlit as st
import google.generativeai as genai
from PIL import Image

# =========================
# Gemini Setup
# =========================

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Secrets")
    st.stop()

genai.configure(api_key=api_key)


@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        "gemini-3.6-flash",
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 250,
        }
    )


model = load_model()


# =========================
# UI
# =========================

st.title("🗑️ AI แยกขยะ")
st.write("📷 ถ่ายหรืออัปโหลดภาพขยะ แล้ว AI จะบอกว่าต้องทิ้งถังไหน")

upload_method = st.radio(
    "เลือกวิธีอัปโหลดภาพ:",
    ["📸 ถ่ายรูป", "📁 อัปโหลดไฟล์"]
)

uploaded_file = None

if upload_method == "📸 ถ่ายรูป":
    uploaded_file = st.camera_input("ถ่ายภาพขยะ")
else:
    uploaded_file = st.file_uploader(
        "อัปโหลดภาพขยะ",
        type=["jpg", "jpeg", "png"]
    )


# =========================
# Analyze
# =========================

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    # รูปสำหรับแสดงผล
    st.image(
        image,
        caption="ภาพที่อัปโหลด",
        width=300
    )

    if st.button(
        "🤖 วิเคราะห์ขยะ",
        type="primary",
        use_container_width=True
    ):

        with st.spinner("🔍 AI กำลังตรวจสอบ..."):

            try:

                # -------------------------
                # ลดขนาดภาพก่อนส่ง Gemini
                # -------------------------
                ai_image = image.copy()

                ai_image.thumbnail(
                    (800, 800),
                    Image.Resampling.LANCZOS
                )

                prompt = """
ระบุขยะหลักในภาพ และตอบภาษาไทยสั้นๆ เท่านั้น

🏷️ ประเภทขยะ:
♻️ จำแนกเป็น:
🗑️ ทิ้งที่:
💡 เคล็ดลับ:

ประเภทที่เลือกได้:
พลาสติก, กระดาษ, แก้ว, โลหะ,
ขยะอินทรีย์, ขยะอันตราย, ขยะทั่วไป
"""

                response = model.generate_content(
                    [
                        prompt,
                        ai_image
                    ]
                )

                st.success("✅ วิเคราะห์เสร็จแล้ว!")
                st.markdown(response.text)

            except Exception as e:

                st.error(
                    f"❌ เกิดข้อผิดพลาด: {str(e)}"
                )

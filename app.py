import streamlit as st
import google.generativeai as genai
from PIL import Image

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="AI แยกขยะ",
    page_icon="🗑️",
    layout="centered"
)

# =========================
# GEMINI SETUP
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
            "temperature": 0,
            "max_output_tokens": 100
        }
    )


model = load_model()


# =========================
# UI
# =========================
st.title("🗑️ AI แยกขยะ")
st.write("📷 ถ่ายหรืออัปโหลดภาพ แล้ว AI จะบอกว่าต้องทิ้งลงถังไหน")

upload_method = st.radio(
    "เลือกวิธี:",
    ["📸 ถ่ายรูป", "📁 อัปโหลดไฟล์"],
    horizontal=True
)

if upload_method == "📸 ถ่ายรูป":
    uploaded_file = st.camera_input("ถ่ายภาพขยะ")
else:
    uploaded_file = st.file_uploader(
        "อัปโหลดภาพขยะ",
        type=["jpg", "jpeg", "png"]
    )


# =========================
# IMAGE + ANALYZE
# =========================
if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    st.image(
        image,
        caption="ภาพที่ต้องการตรวจสอบ",
        width=300
    )

    if st.button(
        "🔍 ตรวจสอบถังขยะ",
        type="primary",
        use_container_width=True
    ):

        with st.spinner("กำลังตรวจสอบ..."):

            try:
                # -------------------------
                # ลดขนาดภาพเพื่อให้เร็วขึ้น
                # -------------------------
                ai_image = image.copy()

                ai_image.thumbnail(
                    (512, 512),
                    Image.Resampling.LANCZOS
                )

                # -------------------------
                # PROMPT สั้น
                # -------------------------
                prompt = """
เลือกถังที่เหมาะสมสำหรับขยะหลักในภาพ

GREEN = ขยะรีไซเคิล
BLUE = ขยะทั่วไป
YELLOW = ขยะอินทรีย์ / เศษอาหาร
RED = ขยะอันตราย

ตอบเพียงคำเดียว:
GREEN
BLUE
YELLOW
หรือ RED
"""

                # -------------------------
                # CALL GEMINI
                # -------------------------
                response = model.generate_content([
                    prompt,
                    ai_image
                ])

                # -------------------------
                # CHECK RESPONSE
                # -------------------------
                result = ""

                try:
                    result = response.text.strip().upper()
                except Exception:
                    pass

                if not result:

                    finish_reason = "UNKNOWN"

                    try:
                        finish_reason = str(
                            response.candidates[0].finish_reason
                        )
                    except Exception:
                        pass

                    st.error(
                        f"AI ไม่ได้ส่งคำตอบกลับมา "
                        f"(Finish reason: {finish_reason})"
                    )
                    st.stop()

                # -------------------------
                # CLEAN RESULT
                # -------------------------
                if "GREEN" in result:
                    result = "GREEN"

                elif "BLUE" in result:
                    result = "BLUE"

                elif "YELLOW" in result:
                    result = "YELLOW"

                elif "RED" in result:
                    result = "RED"


                # =========================
                # DISPLAY RESULT
                # =========================
                st.divider()

                if result == "GREEN":

                    st.success("♻️ ต้องทิ้งถังขยะรีไซเคิล")

                    st.markdown("""
### 🟢 ถังขยะรีไซเคิล

เทของเหลวออก และล้างก่อนทิ้งหากสามารถทำได้
""")


                elif result == "BLUE":

                    st.info("🗑️ ต้องทิ้งถังขยะทั่วไป")

                    st.markdown("""
### 🔵 ถังขยะทั่วไป

ทิ้งลงถังขยะทั่วไปได้
""")


                elif result == "YELLOW":

                    st.warning("🍌 ต้องทิ้งถังขยะอินทรีย์")

                    st.markdown("""
### 🟡 ถังขยะอินทรีย์ / เศษอาหาร

แยกบรรจุภัณฑ์ออกก่อนทิ้ง หากมี
""")


                elif result == "RED":

                    st.error("⚠️ ต้องทิ้งถังขยะอันตราย")

                    st.markdown("""
### 🔴 ถังขยะอันตราย

ห้ามทิ้งรวมกับขยะทั่วไป
""")


                else:

                    st.warning(
                        f"AI ตอบกลับมาไม่ตรงรูปแบบ: {result}"
                    )


            except Exception as e:

                st.error(
                    f"❌ เกิดข้อผิดพลาด: {str(e)}"
                )

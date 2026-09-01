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
        "gemini-2.0-flash",
        generation_config={
            "temperature": 0,
            "max_output_tokens": 10
        }
    )


model = load_model()


# =========================
# UI
# =========================

st.title("🗑️ AI แยกขยะ")

st.write(
    "📷 ถ่ายหรืออัปโหลดภาพ "
    "AI จะบอกว่าต้องทิ้งลงถังไหน"
)

upload_method = st.radio(
    "เลือกวิธี:",
    ["📸 ถ่ายรูป", "📁 อัปโหลดไฟล์"],
    horizontal=True
)


if upload_method == "📸 ถ่ายรูป":

    uploaded_file = st.camera_input(
        "ถ่ายภาพขยะ"
    )

else:

    uploaded_file = st.file_uploader(
        "อัปโหลดภาพขยะ",
        type=["jpg", "jpeg", "png"]
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
                # ลดรูปให้เล็กมากขึ้น
                # -------------------------

                ai_image = image.copy()

                ai_image.thumbnail(
                    (512, 512),
                    Image.Resampling.LANCZOS
                )


                # -------------------------
                # PROMPT สั้นมาก
                # -------------------------

                prompt = """
ดูขยะหลักในภาพและเลือกถังที่เหมาะสมที่สุด

GREEN = ขยะรีไซเคิล
BLUE = ขยะทั่วไป
YELLOW = ขยะอินทรีย์/เศษอาหาร
RED = ขยะอันตราย

ตอบเพียงคำเดียวเท่านั้น:
GREEN
BLUE
YELLOW
หรือ RED
"""


                # -------------------------
                # GEMINI
                # -------------------------

                response = model.generate_content(
                    [prompt, ai_image]
                )


                # -------------------------
                # ดึงผลลัพธ์อย่างปลอดภัย
                # -------------------------

                result = ""

                try:
                    result = response.text.strip().upper()
                except:
                    pass


                # Debug กรณีไม่มีข้อความ
                if not result:
                    st.error("AI วิเคราะห์แล้ว แต่ไม่ได้ส่งผลลัพธ์กลับมา")
                    st.write(response)
                    st.stop()


                # -------------------------
                # แสดงผล
                # -------------------------

                if "GREEN" in result:

                    st.success("♻️ ทิ้งถังขยะรีไซเคิล")

                    st.markdown(
                        """
                        ### 🟢 ถังขยะรีไซเคิล

                        ล้างหรือเทของเหลวออกก่อนทิ้ง หากสามารถทำได้
                        """
                    )


                elif "BLUE" in result:

                    st.info("🗑️ ทิ้งถังขยะทั่วไป")

                    st.markdown(
                        """
                        ### 🔵 ถังขยะทั่วไป

                        ทิ้งได้โดยไม่ต้องแยกเพื่อรีไซเคิล
                        """
                    )


                elif "YELLOW" in result:

                    st.warning("🍌 ทิ้งถังขยะอินทรีย์")

                    st.markdown(
                        """
                        ### 🟡 ถังขยะอินทรีย์ / เศษอาหาร

                        เทของเหลวและแยกบรรจุภัณฑ์ออกก่อน
                        """
                    )


                elif "RED" in result:

                    st.error("⚠️ ทิ้งถังขยะอันตราย")

                    st.markdown(
                        """
                        ### 🔴 ถังขยะอันตราย

                        ห้ามทิ้งรวมกับขยะทั่วไป
                        """
                    )


                else:

                    st.warning(
                        f"AI ตอบกลับ: {result}"
                    )


            except Exception as e:

                st.error(
                    f"❌ Error: {e}"
                )

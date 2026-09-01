import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="AI แยกขยะ",
    page_icon="🗑️",
    layout="centered"
)

# =====================================================
# GEMINI SETUP
# =====================================================

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets")
    st.stop()

genai.configure(api_key=api_key)


@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        "gemini-3.6-flash",
        generation_config={
            "temperature": 0,
            # สำคัญ: อย่าตั้งต่ำเกินไป
            "max_output_tokens": 1024
        }
    )


model = load_model()


# =====================================================
# UI
# =====================================================

st.title("🗑️ AI แยกขยะ")

st.write(
    "📷 ถ่ายหรืออัปโหลดภาพขยะ "
    "AI จะบอกว่าต้องทิ้งลงถังไหน"
)

upload_method = st.radio(
    "เลือกวิธี:",
    [
        "📸 ถ่ายรูป",
        "📁 อัปโหลดไฟล์"
    ],
    horizontal=True
)


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


# =====================================================
# IMAGE
# =====================================================

if uploaded_file is not None:

    image = Image.open(
        uploaded_file
    ).convert("RGB")

    st.image(
        image,
        caption="ภาพที่ต้องการตรวจสอบ",
        width=300
    )


    # =================================================
    # BUTTON
    # =================================================

    if st.button(
        "🔍 ตรวจสอบถังขยะ",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "🤖 กำลังตรวจสอบ..."
        ):

            try:

                # =====================================
                # RESIZE IMAGE
                # =====================================

                ai_image = image.copy()

                ai_image.thumbnail(
                    (512, 512),
                    Image.Resampling.LANCZOS
                )


                # =====================================
                # VERY SHORT PROMPT
                # =====================================

                prompt = """
ดูขยะหลักในภาพ แล้วเลือกหมายเลขถังที่ถูกต้องที่สุด

1 = รีไซเคิล
2 = ขยะทั่วไป
3 = ขยะอินทรีย์หรือเศษอาหาร
4 = ขยะอันตราย

ตอบเพียงหมายเลข 1, 2, 3 หรือ 4 เท่านั้น
"""


                # =====================================
                # CALL GEMINI
                # =====================================

                response = model.generate_content(
                    [
                        prompt,
                        ai_image
                    ]
                )


                # =====================================
                # GET RESPONSE
                # =====================================

                result_text = ""

                try:
                    result_text = response.text.strip()
                except Exception:
                    pass


                # =====================================
                # EMPTY RESPONSE
                # =====================================

                if not result_text:

                    finish_reason = "UNKNOWN"

                    try:
                        finish_reason = str(
                            response.candidates[0].finish_reason
                        )
                    except Exception:
                        pass

                    st.error(
                        "❌ AI วิเคราะห์แล้ว "
                        "แต่ไม่ได้ส่งผลลัพธ์กลับมา"
                    )

                    st.caption(
                        f"Finish reason: {finish_reason}"
                    )

                    st.stop()


                # =====================================
                # FIND 1 / 2 / 3 / 4
                # =====================================

                match = re.search(
                    r"\b([1-4])\b",
                    result_text
                )


                if match:

                    result = match.group(1)

                else:

                    # กรณี AI ตอบเป็นคำแทนเลข
                    text_upper = result_text.upper()

                    if "GREEN" in text_upper:
                        result = "1"

                    elif "BLUE" in text_upper:
                        result = "2"

                    elif "YELLOW" in text_upper:
                        result = "3"

                    elif "RED" in text_upper:
                        result = "4"

                    elif "รีไซเคิล" in result_text:
                        result = "1"

                    elif "ทั่วไป" in result_text:
                        result = "2"

                    elif (
                        "อินทรีย์" in result_text
                        or "เศษอาหาร" in result_text
                    ):
                        result = "3"

                    elif "อันตราย" in result_text:
                        result = "4"

                    else:
                        result = None


                # =====================================
                # SHOW RESULT
                # =====================================

                st.divider()


                # ---------- RECYCLE ----------
                if result == "1":

                    st.success(
                        "♻️ ต้องทิ้งถังขยะรีไซเคิล"
                    )

                    st.markdown(
                        """
## 🟢 ถังขยะรีไซเคิล

เทของเหลวออก และล้างก่อนทิ้งถ้าสามารถทำได้
"""
                    )


                # ---------- GENERAL ----------
                elif result == "2":

                    st.info(
                        "🗑️ ต้องทิ้งถังขยะทั่วไป"
                    )

                    st.markdown(
                        """
## 🔵 ถังขยะทั่วไป

ทิ้งลงถังขยะทั่วไป
"""
                    )


                # ---------- ORGANIC ----------
                elif result == "3":

                    st.warning(
                        "🍌 ต้องทิ้งถังขยะอินทรีย์"
                    )

                    st.markdown(
                        """
## 🟡 ถังขยะอินทรีย์ / เศษอาหาร

แยกบรรจุภัณฑ์ที่ไม่ใช่อาหารออกก่อนทิ้ง
"""
                    )


                # ---------- HAZARDOUS ----------
                elif result == "4":

                    st.error(
                        "⚠️ ต้องทิ้งถังขยะอันตราย"
                    )

                    st.markdown(
                        """
## 🔴 ถังขยะอันตราย

ห้ามทิ้งรวมกับขยะทั่วไป
"""
                    )


                # ---------- UNKNOWN ----------
                else:

                    st.error(
                        "❌ ไม่สามารถระบุถังขยะได้"
                    )

                    st.caption(
                        f"AI Response: {result_text}"
                    )


            except Exception as e:

                st.error(
                    f"❌ เกิดข้อผิดพลาด: {str(e)}"
                )

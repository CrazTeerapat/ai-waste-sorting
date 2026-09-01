import streamlit as st
import google.generativeai as genai
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
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
# GEMINI
# =====================================================
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY")
    st.stop()

genai.configure(api_key=api_key)

# =====================================================
# MODEL
# ใช้ตัวที่คุณทดสอบแล้วว่าใช้งานได้
# =====================================================
MODEL_NAME = "gemini-3.6-flash"

@st.cache_resource
def load_model():

    return genai.GenerativeModel(
        MODEL_NAME,
        generation_config={
            "temperature": 0,
            "max_output_tokens": 256
        }
    )

model = load_model()

# =====================================================
# GEMINI FUNCTION
# =====================================================
def analyze_waste(ai_image):

    prompt = """
Classify the MAIN waste item.

1 = RECYCLABLE
plastic bottle, glass bottle, can, paper, cardboard

2 = GENERAL WASTE
tissue, wrapper, plastic bag, foam, dirty packaging

3 = ORGANIC
food, fruit, vegetables, leftovers

4 = HAZARDOUS
battery, electronics, bulb, chemical, aerosol

Rules:
clean recyclable material = 1
dirty packaging = 2
food = 3
battery/electronic/chemical = 4

Return ONLY 1, 2, 3 or 4.
"""

    response = model.generate_content([
        prompt,
        ai_image
    ])

    return response.text.strip()


# =====================================================
# UI
# =====================================================
st.title("🗑️ AI แยกขยะ")

st.write(
    "📷 ถ่ายภาพขยะ แล้ว AI จะบอกว่าต้องทิ้งถังไหน"
)

method = st.radio(
    "เลือกวิธี:",
    [
        "📸 ถ่ายรูป",
        "📁 อัปโหลดไฟล์"
    ],
    horizontal=True
)

if method == "📸 ถ่ายรูป":

    uploaded_file = st.camera_input(
        "ถ่ายภาพ"
    )

else:

    uploaded_file = st.file_uploader(
        "อัปโหลดภาพ",
        type=["jpg", "jpeg", "png"]
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

        start = time.time()

        # =============================================
        # RESIZE
        # =============================================
        ai_image = image.copy()

        ai_image.thumbnail(
            (256, 256),
            Image.Resampling.BILINEAR
        )

        # =============================================
        # CALL GEMINI + TIMEOUT
        # =============================================
        try:

            with st.spinner(
                "🤖 กำลังตรวจสอบ..."
            ):

                executor = ThreadPoolExecutor(
                    max_workers=1
                )

                future = executor.submit(
                    analyze_waste,
                    ai_image
                )

                try:

                    # ---------------------------------
                    # สูงสุด 8 วินาที
                    # ---------------------------------
                    text = future.result(
                        timeout=8
                    )

                except TimeoutError:

                    future.cancel()

                    executor.shutdown(
                        wait=False
                    )

                    st.error(
                        "⏱️ AI ใช้เวลานานเกินไป กรุณาลองใหม่"
                    )

                    st.stop()

                executor.shutdown(
                    wait=False
                )

        except Exception as e:

            st.error(
                f"❌ Error: {e}"
            )

            st.stop()

        # =============================================
        # READ RESULT
        # =============================================
        match = re.search(
            r"\b([1-4])\b",
            text
        )

        if not match:

            st.error(
                "❌ AI ไม่สามารถจำแนกขยะได้"
            )

            st.caption(
                f"Response: {text}"
            )

            st.stop()

        result = match.group(1)

        elapsed = time.time() - start

        # =============================================
        # RESULT
        # =============================================
        st.divider()

        if result == "1":

            st.success(
                "♻️ ทิ้งถังรีไซเคิล"
            )

            st.markdown(
                """
# 🟢 RECYCLABLE

**เทของเหลวออกก่อนทิ้ง**
"""
            )

        elif result == "2":

            st.info(
                "🗑️ ทิ้งถังขยะทั่วไป"
            )

            st.markdown(
                """
# 🔵 GENERAL WASTE
"""
            )

        elif result == "3":

            st.warning(
                "🍌 ทิ้งถังขยะอินทรีย์"
            )

            st.markdown(
                """
# 🟡 ORGANIC WASTE

**แยกบรรจุภัณฑ์ออกก่อนทิ้ง**
"""
            )

        elif result == "4":

            st.error(
                "⚠️ ทิ้งถังขยะอันตราย"
            )

            st.markdown(
                """
# 🔴 HAZARDOUS WASTE

**ห้ามทิ้งรวมกับขยะทั่วไป**
"""
            )

        # =============================================
        # SPEED
        # =============================================
        st.caption(
            f"⚡ วิเคราะห์ {elapsed:.2f} วินาที"
        )

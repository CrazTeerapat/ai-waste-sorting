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
# GEMINI SETUP
# =====================================================
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Secrets")
    st.stop()

genai.configure(api_key=api_key)

# =====================================================
# MODEL
# =====================================================
# ใช้ model ที่คุณใช้งานได้อยู่
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
Look at the MAIN waste object in the image.

Identify the object and choose its waste category.

1 = RECYCLABLE
Examples: plastic bottle, plastic container, glass bottle,
glass jar, aluminum can, metal can, paper, cardboard.

2 = GENERAL WASTE
Examples: tissue, napkin, snack wrapper, plastic film,
plastic bag, foam, dirty packaging, non-recyclable waste.

3 = ORGANIC
Examples: food, leftover food, fruit, vegetable,
fruit peel, food scraps.

4 = HAZARDOUS
Examples: battery, electronic waste, light bulb,
chemical container, aerosol can, hazardous material.

Rules:
Clean recyclable material = 1
Dirty or contaminated packaging = 2
Food = 3
Battery/electronic/chemical = 4

Reply ONLY in this format:

object|number

Examples:
plastic bottle|1
banana peel|3
battery|4

No explanation.
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
    "📷 ถ่ายหรืออัปโหลดภาพขยะ "
    "AI จะบอกว่าเห็นเป็นอะไร และต้องทิ้งถังไหน"
)

upload_method = st.radio(
    "เลือกวิธี:",
    [
        "📸 ถ่ายรูป",
        "📁 อัปโหลดไฟล์"
    ],
    horizontal=True
)


# =====================================================
# IMAGE INPUT
# =====================================================
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
    # ANALYZE BUTTON
    # =================================================
    if st.button(
        "🔍 ตรวจสอบถังขยะ",
        type="primary",
        use_container_width=True
    ):

        start_time = time.time()

        # =============================================
        # RESIZE
        # =============================================
        # 256px เพื่อเน้นความเร็ว
        ai_image = image.copy()

        ai_image.thumbnail(
            (256, 256),
            Image.Resampling.BILINEAR
        )

        # =============================================
        # CALL GEMINI
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

                    # สูงสุด 8 วินาที
                    text = future.result(
                        timeout=8
                    )

                except TimeoutError:

                    future.cancel()

                    executor.shutdown(
                        wait=False
                    )

                    st.error(
                        "⏱️ AI ใช้เวลานานเกิน 8 วินาที"
                    )

                    st.info(
                        "กรุณากดตรวจสอบอีกครั้ง"
                    )

                    st.stop()

                executor.shutdown(
                    wait=False
                )

        except Exception as e:

            st.error(
                f"❌ Error: {str(e)}"
            )

            st.stop()

        # =================================================
        # READ RESPONSE
        # =================================================

        text = text.strip()

        # Gemini ควรตอบ object|number
        if "|" not in text:

            st.error(
                "❌ AI ตอบกลับไม่ตรงรูปแบบ"
            )

            st.caption(
                f"AI Response: {text}"
            )

            st.stop()

        # แยก object และ category
        parts = text.split("|", 1)

        object_name = parts[0].strip()

        category_text = parts[1].strip()

        # หาเลข 1-4
        match = re.search(
            r"[1-4]",
            category_text
        )

        if not match:

            st.error(
                "❌ AI ไม่สามารถระบุประเภทถังได้"
            )

            st.caption(
                f"AI Response: {text}"
            )

            st.stop()

        result = match.group(0)

        # =================================================
        # TIME
        # =================================================

        elapsed = time.time() - start_time

        # =================================================
        # SHOW WHAT AI SAW
        # =================================================

        st.divider()

        st.markdown(
            "### 👁️ AI เห็นเป็น"
        )

        st.markdown(
            f"## {object_name.title()}"
        )

        st.divider()

        # =================================================
        # RESULT
        # =================================================

        # -------------------------------------------------
        # RECYCLABLE
        # -------------------------------------------------
        if result == "1":

            st.success(
                "♻️ ทิ้งถังรีไซเคิล"
            )

            st.markdown(
                """
# 🟢 RECYCLABLE

### ถังขยะรีไซเคิล

เทของเหลวออกก่อนทิ้ง  
หากสกปรกควรล้างก่อน
"""
            )

        # -------------------------------------------------
        # GENERAL
        # -------------------------------------------------
        elif result == "2":

            st.info(
                "🗑️ ทิ้งถังขยะทั่วไป"
            )

            st.markdown(
                """
# 🔵 GENERAL WASTE

### ถังขยะทั่วไป
"""
            )

        # -------------------------------------------------
        # ORGANIC
        # -------------------------------------------------
        elif result == "3":

            st.warning(
                "🍌 ทิ้งถังขยะอินทรีย์"
            )

            st.markdown(
                """
# 🟡 ORGANIC WASTE

### ถังขยะอินทรีย์

แยกบรรจุภัณฑ์ออกก่อนทิ้ง
"""
            )

        # -------------------------------------------------
        # HAZARDOUS
        # -------------------------------------------------
        elif result == "4":

            st.error(
                "⚠️ ทิ้งถังขยะอันตราย"
            )

            st.markdown(
                """
# 🔴 HAZARDOUS WASTE

### ถังขยะอันตราย

ห้ามทิ้งรวมกับขยะทั่วไป
"""
            )

        # =================================================
        # SPEED
        # =================================================

        st.divider()

        st.caption(
            f"⚡ วิเคราะห์ {elapsed:.2f} วินาที "
            f"| {MODEL_NAME}"
        )

import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import re
import time

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="AI แยกขยะ",
    page_icon="🗑️",
    layout="centered"
)

# =====================================================
# API KEY
# =====================================================

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Secrets")
    st.stop()

genai.configure(api_key=api_key)

# =====================================================
# FAST MODEL
# =====================================================

@st.cache_resource
def get_fast_model():

    models = []

    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            models.append(
                m.name.replace("models/", "")
            )

    selected = None

    # เลือก Flash-Lite ก่อน
    for name in models:
        if (
            "flash-lite" in name.lower()
            and "2.0" not in name.lower()
        ):
            selected = name
            break

    # ถ้าไม่มี Flash-Lite ใช้ Flash
    if not selected:
        for name in models:
            if (
                "flash" in name.lower()
                and "2.0" not in name.lower()
            ):
                selected = name
                break

    if not selected:
        raise Exception(
            "ไม่พบ Gemini Flash model ที่รองรับ"
        )

    model = genai.GenerativeModel(
        selected,
        generation_config={
            "temperature": 0,
            "max_output_tokens": 256
        }
    )

    return model, selected


model, model_name = get_fast_model()

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

# =====================================================
# UPLOAD
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

        with st.spinner(
            "🤖 กำลังตรวจสอบ..."
        ):

            try:

                # =====================================
                # RESIZE IMAGE
                # =====================================

                ai_image = image.copy()

                ai_image.thumbnail(
                    (384, 384),
                    Image.Resampling.LANCZOS
                )

                # =====================================
                # JPEG COMPRESS
                # =====================================

                buffer = io.BytesIO()

                ai_image.save(
                    buffer,
                    format="JPEG",
                    quality=70,
                    optimize=False
                )

                buffer.seek(0)

                ai_image_small = Image.open(
                    buffer
                ).convert("RGB")

                # =====================================
                # PROMPT
                # =====================================

                prompt = """
Identify the MAIN waste item in the image and choose the most appropriate disposal bin.

Choose only one:

1 = RECYCLABLE
Examples:
clean plastic bottles,
plastic containers,
aluminum cans,
metal cans,
glass bottles,
clean paper,
cardboard.

2 = GENERAL WASTE
Examples:
dirty plastic packaging,
snack wrappers,
tissue,
foam,
contaminated packaging,
mixed non-recyclable waste.

3 = ORGANIC / FOOD WASTE
Examples:
food scraps,
leftover food,
fruit,
vegetables,
organic biodegradable waste.

4 = HAZARDOUS WASTE
Examples:
battery,
chemical container,
aerosol can,
electronic waste,
light bulb,
chemical contaminated material.

Important rules:

- Look at the MAIN object only.
- Do not classify only by color or shape.
- Consider what material the object is made from.
- If it contains food, separate the food from the packaging.
- Food itself = 3.
- Clean recyclable packaging = 1.
- Dirty or heavily contaminated packaging = 2.
- Battery, chemical, electrical or hazardous item = 4.
- Choose the safest and most appropriate disposal category.

Return ONLY one number:

1
2
3
or
4
"""

                # =====================================
                # CALL GEMINI
                # =====================================

                response = model.generate_content(
                    [
                        prompt,
                        ai_image_small
                    ]
                )

                # =====================================
                # GET RESPONSE
                # =====================================

                text = ""

                try:
                    text = (
                        response.text
                        .strip()
                    )
                except:
                    pass

                # =====================================
                # EXTRACT RESULT
                # =====================================

                match = re.search(
                    r"\b([1-4])\b",
                    text
                )

                if not match:

                    # fallback กรณีตอบเป็นคำ
                    text_upper = text.upper()

                    if "RECYCL" in text_upper:
                        result = "1"

                    elif "GENERAL" in text_upper:
                        result = "2"

                    elif (
                        "ORGANIC" in text_upper
                        or "FOOD" in text_upper
                    ):
                        result = "3"

                    elif (
                        "HAZARD" in text_upper
                        or "CHEMICAL" in text_upper
                    ):
                        result = "4"

                    else:

                        st.error(
                            "❌ AI ไม่สามารถระบุถังได้"
                        )

                        st.caption(
                            f"AI Response: {text}"
                        )

                        st.stop()

                else:

                    result = match.group(1)

                # =====================================
                # RESPONSE TIME
                # =====================================

                elapsed = (
                    time.time()
                    - start_time
                )

                st.divider()

                # =====================================
                # RESULT
                # =====================================

                if result == "1":

                    st.success(
                        "♻️ ต้องทิ้งถังรีไซเคิล"
                    )

                    st.markdown(
                        """
# 🟢 ถังรีไซเคิล

**เทของเหลวออก และล้างก่อนทิ้ง หากทำได้**
"""
                    )

                elif result == "2":

                    st.info(
                        "🗑️ ต้องทิ้งถังขยะทั่วไป"
                    )

                    st.markdown(
                        """
# 🔵 ถังขยะทั่วไป

**ทิ้งลงถังขยะทั่วไป**
"""
                    )

                elif result == "3":

                    st.warning(
                        "🍌 ต้องทิ้งถังขยะอินทรีย์"
                    )

                    st.markdown(
                        """
# 🟡 ถังขยะอินทรีย์

**แยกบรรจุภัณฑ์ออกจากเศษอาหารก่อน**
"""
                    )

                elif result == "4":

                    st.error(
                        "⚠️ ต้องทิ้งถังขยะอันตราย"
                    )

                    st.markdown(
                        """
# 🔴 ถังขยะอันตราย

**ห้ามทิ้งรวมกับขยะทั่วไป**
"""
                    )

                # =====================================
                # SHOW SPEED
                # =====================================

                st.caption(
                    f"⚡ วิเคราะห์ {elapsed:.2f} วินาที "
                    f"| Model: {model_name}"
                )

            except Exception as e:

                st.error(
                    f"❌ เกิดข้อผิดพลาด: {str(e)}"
                )

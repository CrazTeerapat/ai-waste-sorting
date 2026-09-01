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
# GEMINI SETUP
# =====================================================
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Secrets")
    st.stop()

genai.configure(api_key=api_key)


# =====================================================
# FIND FAST MODEL
# =====================================================
@st.cache_resource
def get_fast_model():

    available_models = []

    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            available_models.append(
                m.name.replace("models/", "")
            )

    selected = None

    # 1. Flash-Lite ก่อน
    for name in available_models:
        if (
            "flash-lite" in name.lower()
            and "2.0" not in name.lower()
        ):
            selected = name
            break

    # 2. ถ้าไม่มี ใช้ Flash
    if not selected:
        for name in available_models:
            if (
                "flash" in name.lower()
                and "2.0" not in name.lower()
            ):
                selected = name
                break

    if not selected:
        raise Exception("ไม่พบ Gemini Flash model")

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
    "แล้ว AI จะบอกว่าต้องทิ้งลงถังไหน"
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
        caption="ภาพที่ต้องการตรวจสอบ",
        width=300
    )


    # =================================================
    # ANALYZE
    # =================================================
    if st.button(
        "🔍 ตรวจสอบถังขยะ",
        type="primary",
        use_container_width=True
    ):

        start_time = time.time()

        with st.spinner("กำลังวิเคราะห์..."):

            try:

                # =====================================
                # RESIZE
                # 256x256 เพื่อเน้นความเร็ว
                # =====================================
                ai_image = image.copy()

                ai_image.thumbnail(
                    (256, 256),
                    Image.Resampling.BILINEAR
                )


                # =====================================
                # JPEG COMPRESS
                # =====================================
                buffer = io.BytesIO()

                ai_image.save(
                    buffer,
                    format="JPEG",
                    quality=65,
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
Identify the main waste object, then classify its disposal category.

Categories:

1 = RECYCLABLE
Clean plastic bottle/container, aluminum or metal can,
glass bottle/jar, clean paper, cardboard.

2 = GENERAL
Tissue, napkin, snack wrapper, plastic film/bag,
foam, dirty packaging, mixed non-recyclable waste.

3 = ORGANIC
Food scraps, leftovers, fruit, vegetables,
peels and biodegradable food waste.

4 = HAZARDOUS
Battery, electronic waste, light bulb,
chemical container, aerosol, chemical or hazardous material.

Rules:
Food itself = 3
Clean recyclable packaging = 1
Dirty/contaminated packaging = 2
Battery/electronic/chemical = 4
If uncertain between 1 and 2, use 2.

Reply exactly:
object|number

Example:
plastic_bottle|1
banana_peel|3

No explanation.
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
                # READ RESPONSE
                # =====================================
                text = ""

                try:
                    text = response.text.strip()
                except Exception:
                    pass


                if not text:

                    st.error(
                        "❌ AI ไม่ได้ส่งผลลัพธ์กลับมา"
                    )

                    st.stop()


                # =====================================
                # GET CATEGORY AFTER |
                # =====================================
                result = None

                if "|" in text:

                    parts = text.split("|")

                    if len(parts) >= 2:

                        bin_part = parts[-1].strip()

                        match = re.search(
                            r"[1-4]",
                            bin_part
                        )

                        if match:
                            result = match.group()


                # =====================================
                # FALLBACK
                # =====================================
                if result is None:

                    match = re.search(
                        r"\b([1-4])\b",
                        text
                    )

                    if match:
                        result = match.group(1)


                # =====================================
                # TIME
                # =====================================
                elapsed = time.time() - start_time


                # =====================================
                # RESULT
                # =====================================
                st.divider()


                # -------------------------------------
                # RECYCLABLE
                # -------------------------------------
                if result == "1":

                    st.success(
                        "♻️ ทิ้งถังรีไซเคิล"
                    )

                    st.markdown("""
# 🟢 RECYCLABLE

### ทิ้งถังขยะรีไซเคิล

เทของเหลวออกก่อนทิ้ง
""")


                # -------------------------------------
                # GENERAL
                # -------------------------------------
                elif result == "2":

                    st.info(
                        "🗑️ ทิ้งถังขยะทั่วไป"
                    )

                    st.markdown("""
# 🔵 GENERAL WASTE

### ทิ้งถังขยะทั่วไป
""")


                # -------------------------------------
                # ORGANIC
                # -------------------------------------
                elif result == "3":

                    st.warning(
                        "🍌 ทิ้งถังขยะอินทรีย์"
                    )

                    st.markdown("""
# 🟡 ORGANIC WASTE

### ทิ้งถังขยะอินทรีย์

แยกบรรจุภัณฑ์ออกก่อน
""")


                # -------------------------------------
                # HAZARDOUS
                # -------------------------------------
                elif result == "4":

                    st.error(
                        "⚠️ ทิ้งถังขยะอันตราย"
                    )

                    st.markdown("""
# 🔴 HAZARDOUS WASTE

### ทิ้งถังขยะอันตราย

ห้ามทิ้งรวมกับขยะทั่วไป
""")


                # -------------------------------------
                # UNKNOWN
                # -------------------------------------
                else:

                    st.error(
                        "❌ ไม่สามารถระบุถังขยะได้"
                    )

                    st.caption(
                        f"AI response: {text}"
                    )


                # =====================================
                # SPEED
                # =====================================
                st.caption(
                    f"⚡ {elapsed:.2f} วินาที "
                    f"| {model_name}"
                )


            except Exception as e:

                st.error(
                    f"❌ Error: {str(e)}"
                )

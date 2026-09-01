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
# หา MODEL ที่เร็วที่สุดที่ ACCOUNT ใช้ได้
# =====================================================

@st.cache_resource
def get_fast_model():

    models = []

    for m in genai.list_models():

        if "generateContent" in m.supported_generation_methods:
            models.append(m.name.replace("models/", ""))

    # เรียงลำดับความต้องการ
    preferred_keywords = [
        "flash-lite",
        "flash"
    ]

    selected = None

    for keyword in preferred_keywords:

        for name in models:

            if keyword in name.lower():

                # ไม่เลือก 2.0 เพราะ account คุณใช้ไม่ได้
                if "2.0" not in name.lower():

                    selected = name
                    break

        if selected:
            break

    if not selected:
        raise Exception(
            "ไม่พบ Gemini Flash model ที่รองรับ generateContent"
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

st.caption(
    "📷 ถ่ายภาพขยะ แล้วระบบจะบอกว่าต้องทิ้งถังไหน"
)

upload_method = st.radio(
    "เลือกวิธี",
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
        "ถ่ายภาพ"
    )

else:

    uploaded_file = st.file_uploader(
        "อัปโหลดภาพ",
        type=["jpg", "jpeg", "png"]
    )


# =====================================================
# ANALYZE
# =====================================================

if uploaded_file is not None:

    image = Image.open(
        uploaded_file
    ).convert("RGB")

    st.image(
        image,
        width=280
    )

    if st.button(
        "🔍 ตรวจสอบถังขยะ",
        type="primary",
        use_container_width=True
    ):

        start_time = time.time()

        try:

            # =================================================
            # ลดภาพเหลือ 256px
            # =================================================

            ai_image = image.copy()

            ai_image.thumbnail(
                (256, 256),
                Image.Resampling.BILINEAR
            )

            # =================================================
            # JPEG COMPRESS
            # =================================================

            buffer = io.BytesIO()

            ai_image.save(
                buffer,
                format="JPEG",
                quality=55,
                optimize=False
            )

            buffer.seek(0)

            # เปิดกลับเป็น PIL
            ai_image_small = Image.open(
                buffer
            )


            # =================================================
            # PROMPT สั้นที่สุด
            # =================================================

            prompt = """
Classify the main waste item.

1=recycle
2=general waste
3=food/organic
4=hazardous

Return ONLY 1, 2, 3 or 4.
"""


            # =================================================
            # GEMINI
            # =================================================

            response = model.generate_content(
                [
                    prompt,
                    ai_image_small
                ]
            )


            # =================================================
            # GET RESULT
            # =================================================

            text = ""

            try:
                text = response.text.strip()
            except:
                pass


            # =================================================
            # หาเลข 1-4
            # =================================================

            match = re.search(
                r"[1-4]",
                text
            )

            if not match:

                st.error(
                    "❌ AI ไม่สามารถจำแนกได้"
                )

                st.caption(
                    f"Response: {text}"
                )

                st.stop()


            result = match.group()


            # =================================================
            # CALCULATE TIME
            # =================================================

            elapsed = (
                time.time() - start_time
            )


            # =================================================
            # RESULT
            # =================================================

            if result == "1":

                st.success(
                    "♻️ ทิ้งถังรีไซเคิล"
                )

                st.markdown(
                    """
# 🟢 รีไซเคิล
**เทของเหลวออกก่อนทิ้ง**
"""
                )


            elif result == "2":

                st.info(
                    "🗑️ ทิ้งถังขยะทั่วไป"
                )

                st.markdown(
                    """
# 🔵 ขยะทั่วไป
"""
                )


            elif result == "3":

                st.warning(
                    "🍌 ทิ้งถังขยะอินทรีย์"
                )

                st.markdown(
                    """
# 🟡 ขยะอินทรีย์
**แยกบรรจุภัณฑ์ออกก่อน**
"""
                )


            elif result == "4":

                st.error(
                    "⚠️ ทิ้งถังขยะอันตราย"
                )

                st.markdown(
                    """
# 🔴 ขยะอันตราย
**ห้ามทิ้งรวมกับขยะทั่วไป**
"""
                )


            # เวลาใช้จริง
            st.caption(
                f"⚡ วิเคราะห์ {elapsed:.2f} วินาที | {model_name}"
            )


        except Exception as e:

            st.error(
                f"❌ Error: {str(e)}"
            )

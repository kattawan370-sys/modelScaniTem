import streamlit as st
import cv2
import numpy as np
import json
import os
from scanner_module import ShapeScanner

st.set_page_config(layout="wide", page_title="ระบบเช็คลิสต์เครื่องมือ")

# --- CSS ตกแต่ง ---
st.markdown("""
<style>
    .stCheckbox {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin-bottom: 8px;
    }
    small { color: #6c757d; font-size: 0.85em; }
</style>
""", unsafe_allow_html=True)

# --- 1. เตรียมตัวแปรความจำ (Session State) ---
if 'detected_list' not in st.session_state:
    st.session_state.detected_list = []

@st.cache_resource
def load_scanner():
    if not os.path.exists('mock_database'): os.makedirs('mock_database')
    return ShapeScanner()

def get_product_info(filename):
    try:
        with open('mock_database/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if item['filename'] == os.path.basename(filename):
                    return item
    except: return None
    return None

scanner = load_scanner()

st.title("📋 ระบบเช็คลิสต์เครื่องมือ (Multi-Object)")

# แบ่งคอลัมน์หลัก ซ้าย-ขวา
col_input, col_result = st.columns([1, 1.5])

# ==========================================
# 👈 ฝั่งซ้าย: Input & Visualization (แก้ไขใหม่)
# ==========================================
with col_input:
    st.header("📸 สแกนเครื่องมือ")
    input_method = st.radio("เลือกวิธี:", ["Camera", "Upload Image"])
    
    img_file = None
    if input_method == "Camera":
        img_file = st.camera_input("ถ่ายภาพ")
    else:
        img_file = st.file_uploader("อัปโหลดภาพ", type=['jpg','png'])

    if img_file:
        # 1. เตรียมภาพต้นฉบับ
        bytes_data = img_file.getvalue()
        opencv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        
        # 2. สร้างภาพจุดสแกน (Visualization)
        viz_img = None
        kp_count = 0
        try:
            # ต้องมีฟังก์ชัน visualize_keypoints ใน scanner_module.py ล่าสุด
            viz_img, kp_count = scanner.visualize_keypoints(opencv_img.copy())
        except AttributeError:
            # กันเหนียวเผื่อลืมอัปเดต scanner_module
            viz_img = opencv_img
            kp_count = "N/A (ฟังก์ชันไม่พร้อม)"

        # 3. [ส่วนที่แก้ไข] แสดงผล 2 รูปคู่กัน
        st.write("---") # เส้นคั่นเล็กน้อย
        img_col1, img_col2 = st.columns(2) # แบ่งคอลัมน์ย่อยสำหรับรูปภาพ

        with img_col1:
            # รูปซ้าย: ต้นฉบับ
            st.image(opencv_img, channels="BGR", caption="📸 ภาพต้นฉบับ", use_container_width=True)

        with img_col2:
            # รูปขวา: จุดสแกนสีเขียว
            caption_text = f"🟢 จุดสแกน (พบ {kp_count} จุด)"
            st.image(viz_img, channels="BGR", caption=caption_text, use_container_width=True)
        
        # แจ้งเตือนถ้าจุดน้อย
        if isinstance(kp_count, int) and kp_count < 500:
             st.warning(f"⚠️ พบจุดเด่นน้อย ({kp_count}) การสแกนอาจไม่แม่นยำ ลองเพิ่มแสงสว่าง")
        # ------------------------------------------------
        
        st.divider()

        if st.button("🔍 สแกนหาอุปกรณ์ทั้งหมด", type="primary", use_container_width=True):
            # ปรับ Threshold ตามความเหมาะสม (8-12 สำหรับภาพกว้าง)
            results = scanner.scan_multiple_items(opencv_img, threshold=10)
            
            if results:
                count_new = 0
                existing_files = [x['filename'] for x in st.session_state.detected_list]
                
                for res in results:
                    if res['filename'] not in existing_files:
                        info = get_product_info(res['filename'])
                        display_name = info['name'] if info else res['filename']
                        category = info['category'] if info else "Unknown"
                        description = info['description'] if info else "-"
                        
                        st.session_state.detected_list.append({
                            "filename": res['filename'],
                            "name": display_name,
                            "category": category,
                            "description": description,
                            "score": res['score'],
                            "checked": False 
                        })
                        count_new += 1
                
                if count_new > 0:
                    st.toast(f"✅ เจอเพิ่ม {count_new} รายการ!", icon="🎉")
                else:
                    st.toast("รายการนี้มีอยู่แล้ว", icon="ℹ️")
            else:
                st.error("ไม่พบอุปกรณ์ที่รู้จัก")

# ==========================================
# 👉 ฝั่งขวา: Checklist (เหมือนเดิม)
# ==========================================
with col_result:
    st.header(f"📝 รายการตรวจสอบ ({len(st.session_state.detected_list)})")
    
    # --- ปุ่มจัดการ ---
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    
    # ฟังก์ชันช่วยอัปเดต Checkbox (Force Update Widget)
    def update_all_checked(value):
        for i in range(len(st.session_state.detected_list)):
            st.session_state.detected_list[i]['checked'] = value
            if f"chk_{i}" in st.session_state:
                st.session_state[f"chk_{i}"] = value

    with c_btn1:
        if st.button("✅ เลือกทั้งหมด", use_container_width=True):
            update_all_checked(True)
            st.rerun()
            
    with c_btn2:
        if st.button("⬜ ยกเลิกเลือก", use_container_width=True):
            update_all_checked(False)
            st.rerun()
            
    with c_btn3:
        if st.button("🗑️ ล้างรายการ", type="primary", use_container_width=True):
            st.session_state.detected_list = []
            st.rerun()
            
    st.divider()

    # --- ส่วนแสดงรายการ ---
    if not st.session_state.detected_list:
        st.warning("ยังไม่มีรายการ... กรุณาถ่ายภาพหรืออัปโหลดทางฝั่งซ้าย")
    else:
        for i, item in enumerate(st.session_state.detected_list):
            
            c1, c2, c3, c4 = st.columns([0.15, 0.55, 0.2, 0.1])
            
            with c1:
                # Checkbox ที่ผูกค่ากับ Session State อย่างถูกต้อง
                is_checked = st.checkbox(
                    "", 
                    value=item['checked'], 
                    key=f"chk_{i}"
                )
                st.session_state.detected_list[i]['checked'] = is_checked
            
            with c2:
                st.markdown(f"**{item['name']}**")
                st.caption(f"📂 {item['category']} | ⭐ {item['score']}")
                st.markdown(f"<small>{item['description']}</small>", unsafe_allow_html=True)
                
            with c3:
                try:
                    st.image(f"mock_database/{item['filename']}", use_container_width=True)
                except: 
                    st.write("No Img")
                
            with c4:
                if st.button("❌", key=f"del_{i}"):
                    # ลบ Key ของ Widget ทิ้งด้วยเพื่อไม่ให้ Error
                    if f"chk_{i}" in st.session_state:
                        del st.session_state[f"chk_{i}"]
                    
                    st.session_state.detected_list.pop(i)
                    st.rerun()
            
            st.markdown("---")
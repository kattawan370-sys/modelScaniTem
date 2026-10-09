import streamlit as st
import streamlit.components.v1 as components
import cv2
import numpy as np
import json
import os
import time
import csv
import io
import base64
from datetime import datetime, timedelta
from scanner_module import ShapeScanner

# ==============================================================================
# 🎨 1. PAGE CONFIGURATION & GLOBAL DESIGN THEME
# ------------------------------------------------------------------------------
# [ลักษณะหน้าตา UI]: 
# - ตั้งค่าหน้าจอเป็นแบบ Wide Layout เต็มพื้นที่
# - ธีมสีสไตล์ Modern Industrial:
#   * สีหลัก (Brand Accent): แดงสปอร์ตคมชัด (#E81D23)
#   * สีพื้นหลัง (Background): ขาวสะอาด (#FFFFFF) และเทาอ่อน (#F8FAFC)
#   * สีตัวอักษรและกรอบ (Text & Borders): เทาเข้ม (#1E293B, #64748B, #E2E8F0)
# - ออกแบบให้ปุ่มสัมผัสง่าย (Touch-friendly 44px+) เหมาะสำหรับ iPad, Tablet และ PC
# ==============================================================================
st.set_page_config(
    layout="wide", 
    page_title="AI Tool Scanner & Handover System",
    page_icon="🔧"
)

st.markdown("""
<style>
    /* -------------------------------------------------------------
       🎨 Global Styles: พื้นหลัง, ฟอนต์ และระยะห่าง
       ------------------------------------------------------------- */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }

    /* หัวข้อหลักและหัวข้อย่อย */
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* เส้นคั่น */
    hr {
        border: none !important;
        border-top: 1px solid #E2E8F0 !important;
        margin: 1.2rem 0 !important;
    }

    /* -------------------------------------------------------------
       🔘 Button Styles: ปุ่มกดหลัก (Primary) และปุ่มรอง (Secondary)
       ------------------------------------------------------------- */
    button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background-color: #E81D23 !important;
        color: #FFFFFF !important;
        border: 1px solid #E81D23 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 6px rgba(232, 29, 35, 0.25) !important;
        transition: all 0.2s ease !important;
        min-height: 44px !important;
    }
    button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background-color: #C7161B !important;
        border-color: #C7161B !important;
        box-shadow: 0 4px 12px rgba(232, 29, 35, 0.35) !important;
        transform: translateY(-1px);
    }

    button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background-color: #FFFFFF !important;
        color: #334155 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
        min-height: 44px !important;
    }
    button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #F1F5F9 !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
    }

    /* -------------------------------------------------------------
       🎛️ Navigation Bar: แถบเมนูด้านบน 4 หน้าต่าง
       ------------------------------------------------------------- */
    .custom-nav-bar {
        margin-bottom: 18px;
        background: #FFFFFF;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    
    .custom-nav-bar div[data-testid="stHorizontalBlock"] {
        gap: 8px !important;
    }

    /* -------------------------------------------------------------
       📦 Cards & Containers: กล่องข้อมูลและกรอบไอเทม
       ------------------------------------------------------------- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #E2E8F0 !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        margin-bottom: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06) !important;
    }

    /* -------------------------------------------------------------
       🏷️ Badges & Score Pills: ป้ายกำกับหมวดหมู่และคะแนน
       ------------------------------------------------------------- */
    .badge-category {
        background-color: #F1F5F9;
        color: #475569;
        border: 1px solid #E2E8F0;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-score {
        background-color: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FEE2E2;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* Radio Controls */
    div[data-testid="stRadio"] > div {
        background-color: #F1F5F9;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 4px 10px;
        gap: 12px;
    }

    /* Checkbox ขนาดใหญ่แตะง่าย */
    div[data-testid="stCheckbox"] label span[role="checkbox"] {
        width: 22px !important;
        height: 22px !important;
        border-radius: 6px !important;
        border: 2px solid #CBD5E1 !important;
    }
    div[data-testid="stCheckbox"] label span[role="checkbox"][aria-checked="true"] {
        background-color: #E81D23 !important;
        border-color: #E81D23 !important;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #E81D23 !important;
        border-radius: 6px;
    }

    /* Radar Scan Animation สำหรับ Modal */
    @keyframes radar-sweep {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes pulse-ring {
        0% { box-shadow: 0 0 0 0 rgba(232, 29, 35, 0.4); }
        70% { box-shadow: 0 0 0 16px rgba(232, 29, 35, 0); }
        100% { box-shadow: 0 0 0 0 rgba(232, 29, 35, 0); }
    }
    .radar-scan-anim {
        width: 76px;
        height: 76px;
        border-radius: 50%;
        border: 3px solid #E81D23;
        background: radial-gradient(circle, rgba(232,29,35,0.1) 0%, rgba(241,245,249,0.5) 100%);
        margin: 0 auto;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse-ring 2s infinite;
    }
    .radar-beam {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        border-radius: 50%;
        background: conic-gradient(from 0deg, rgba(232, 29, 35, 0.4) 0deg, transparent 65deg);
        animation: radar-sweep 2s linear infinite;
    }

    /* -------------------------------------------------------------
       🔒 Selectbox Locking: ล็อคไม่ให้พิมพ์ข้อความ ปิดเคอร์เซอร์ และให้คลิกเลือกอย่างเดียว
       ------------------------------------------------------------- */
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        pointer-events: none !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        cursor: pointer !important;
    }
    div[data-baseweb="select"] input::selection {
        background: transparent !important;
    }
    div[data-baseweb="select"] {
        cursor: pointer !important;
    }
    div[data-baseweb="select"] * {
        cursor: pointer !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 🧠 2. SESSION STATE & ENGINE INITIALIZATION
# ------------------------------------------------------------------------------
# [ลักษณะการทำงาน]:
# - จัดการหน่วยความจำระหว่างสลับหน้า (Detected List, Active View, Tray Cache)
# - โหลดและบันทึกประวัติการส่งมอบงาน (Handover History Database)
# ==============================================================================
HISTORY_FILE = "mock_database/handover_history.json"

if 'detected_list' not in st.session_state:
    st.session_state.detected_list = []

if 'active_view' not in st.session_state:
    st.session_state.active_view = "scan"

if 'tray_check_results' not in st.session_state:
    st.session_state.tray_check_results = None

if 'tray_check_data' not in st.session_state:
    st.session_state.tray_check_data = None

if 'last_handover_success' not in st.session_state:
    st.session_state.last_handover_success = None


def detect_and_crop_board(image, min_area_ratio=0.15):
    """
    ตรวจจับขอบกระดานหรือถาดเครื่องมืออัตโนมัติ (Automatic Board / Tray Edge Detection)
    และทำ Perspective Transform (Crop) เพื่อตัดผนัง/พื้นหลังรอบนอกทิ้ง

    Returns:
        Tuple: (cropped_image, is_detected, quad_points)
    """
    if image is None or image.size == 0:
        return image, False, None

    h, w = image.shape[:2]

    # ย่อขนาดชั่วคราวเพื่อหาขอบอย่างรวดเร็วและแม่นยำ
    scale = 800.0 / max(h, w) if max(h, w) > 800 else 1.0
    if scale < 1.0:
        small = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        small = image.copy()

    small_h, small_w = small.shape[:2]
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    best_quad = None

    # 1. วิธี Canny Edge Detection
    edges = cv2.Canny(blurred, 30, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in sorted(contours, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(c)
        if area < min_area_ratio * (small_h * small_w):
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            best_quad = approx / scale
            break

    # 2. ถ้ายังไม่เจอ ลองวิธี Adaptive Threshold
    if best_quad is None:
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        thresh_dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours_t, _ = cv2.findContours(thresh_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(contours_t, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(c)
            if area < min_area_ratio * (small_h * small_w):
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                best_quad = approx / scale
                break

    if best_quad is not None:
        pts = best_quad.reshape(4, 2).astype('float32')
        rect = np.zeros((4, 2), dtype='float32')

        # จัดเรียง 4 จุด: top-left, top-right, bottom-right, bottom-left
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        if maxWidth > 60 and maxHeight > 60:
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype='float32')
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
            return warped, True, rect

    return image, False, None


def draw_board_boundary(image, rect_pts):
    """วาดเส้นกรอบสีเขียวแสดงตำแหน่งขอบกระดานที่ตรวจพบ"""
    if rect_pts is None:
        return image
    out = image.copy()
    pts = np.int32(rect_pts).reshape((-1, 1, 2))
    cv2.polylines(out, [pts], isClosed=True, color=(0, 230, 115), thickness=3)
    return out


def create_tool_mask(img_gray):
    """
    สร้าง Mask เพื่อคัดเอาเฉพาะตัวเครื่องมือ (Tools Foreground)
    และตัดพื้นหลังสีสว่าง หรือพื้นผิวเรียบออก
    """
    blurred = cv2.GaussianBlur(img_gray, (5, 5), 0)
    
    # 1. Intensity Threshold: ตัดพื้นหลังสว่างออก
    _, thresh_dark = cv2.threshold(blurred, 175, 255, cv2.THRESH_BINARY_INV)
    
    # 2. Gradient / Edge magnitude: เครื่องมือโลหะมีขอบและคอนทราสต์ชัดเจน
    grad_x = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(grad_x, grad_y)
    grad_norm = cv2.normalize(grad_mag, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
    _, edge_mask = cv2.threshold(grad_norm, 25, 255, cv2.THRESH_BINARY)
    
    # รวม Mask ทั้งความเข้มและขอบคม
    combined = cv2.bitwise_or(thresh_dark, edge_mask)
    
    # ลบ Noise จุดเล็กๆ ออก และขยายครอบคลุมตัวเครื่องมือ
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    tool_mask = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
    tool_mask = cv2.dilate(tool_mask, kernel, iterations=2)
    return tool_mask


def visualize_tool_keypoints(image):
    """
    วาดจุดลักษณะเฉพาะบนตัวเครื่องมือเท่านั้น (ไม่วาดบนพื้นหลัง)
    """
    output_img = image.copy()
    gray = cv2.cvtColor(output_img, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)
    
    # กรองเฉพาะบริเวณตัวเครื่องมือ ไม่เอาพื้นหลัง
    tool_mask = create_tool_mask(gray)
    sift = cv2.SIFT_create(contrastThreshold=0.03, edgeThreshold=10)
    kp, _ = sift.detectAndCompute(gray_clahe, tool_mask)
    
    # วาดกากบาทเล็กๆ สีแดงเฉพาะบนตัวเครื่องมือ
    for k in kp:
        x, y = int(k.pt[0]), int(k.pt[1])
        cv2.drawMarker(output_img, (x, y), (0, 0, 255), 
                      markerType=cv2.MARKER_CROSS, markerSize=5, thickness=1)
    
    return output_img, len(kp)


def load_handover_history():
    """โหลดประวัติการส่งมอบงานจาก JSON"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_handover_record(job_id, inspector_name, bay, note, items, is_complete, source_type="scan", tray_name=None):
    """บันทึกรายการส่งมอบงานลงใน JSON Database"""
    history = load_handover_history()
    now = datetime.now()
    if source_type == "tray":
        status_text = "เครื่องมือครบถ้วน (Complete)" if is_complete else "เครื่องมือไม่ครบ (Incomplete)"
    else:
        status_text = f"บันทึกตรวจนับ ({len(items)} ชิ้น)"

    record = {
        "job_id": job_id,
        "source_type": source_type,
        "tray_name": tray_name,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M"),
        "inspector": inspector_name,
        "bay": bay,
        "note": note,
        "total_items": len(items),
        "checked_items": sum(1 for x in items if x.get('checked', False)),
        "is_complete": is_complete,
        "status": status_text,
        "items": items
    }
    history.insert(0, record)  # เอาอันล่าสุดไว้บนสุด
    if not os.path.exists('mock_database'):
        os.makedirs('mock_database')
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return record


def mark_tool_as_found(job_id, item_index):
    """อัปเดตสถานะเครื่องมือที่ขาดว่าพบแล้วย้อนหลังในประวัติการส่งมอบ"""
    history = load_handover_history()
    for rec in history:
        if rec.get('job_id') == job_id:
            items = rec.get('items', [])
            if 0 <= item_index < len(items):
                items[item_index]['checked'] = True
                items[item_index]['resolved_at'] = datetime.now().strftime("%d/%m/%Y %H:%M น.")
                
                # คำนวณจำนวนชิ้นที่ตรวจพบใหม่
                rec['checked_items'] = sum(1 for x in items if x.get('checked', False))
                if rec['checked_items'] == rec.get('total_items', len(items)):
                    rec['is_complete'] = True
                    if rec.get('source_type') == 'tray':
                        rec['status'] = "เครื่องมือครบถ้วน (Complete - พบย้อนหลัง)"
                    else:
                        rec['status'] = f"บันทึกตรวจนับครบถ้วน ({rec['total_items']} ชิ้น)"
                
                if not os.path.exists('mock_database'):
                    os.makedirs('mock_database')
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                
                st.session_state['history_updated_msg'] = f"อัปเดตสถานะ '{items[item_index].get('name')}' ในงาน {job_id} เป็น 'พบแล้ว' เรียบร้อย"
                break


def keep_only_checked_items():
    """รักษาเฉพาะรายการที่ถูกติ๊กถูกไว้เมื่อมีการถ่ายรูป/เปลี่ยนภาพใหม่"""
    kept_items = [item for item in st.session_state.detected_list if item.get('checked', False)]
    st.session_state.detected_list = kept_items
    keys_to_del = [k for k in st.session_state.keys() if str(k).startswith("chk_")]
    for k in keys_to_del:
        del st.session_state[k]


def sync_checkbox_states():
    """ซิงค์สถานะการติ๊กถูกระหว่าง Widget กับ Session State ให้ตรงกันแบบเรียลไทม์"""
    for i in range(len(st.session_state.detected_list)):
        key = f"chk_{i}"
        if key in st.session_state:
            st.session_state.detected_list[i]['checked'] = st.session_state[key]


@st.cache_resource
def load_scanner():
    """โหลด Engine สแกนเนอร์"""
    if not os.path.exists('mock_database'):
        os.makedirs('mock_database')
    return ShapeScanner()


def get_product_info(filename):
    """ดึงข้อมูลสเปก ชื่อ และหมวดหมู่จาก mock_database/data.json"""
    try:
        with open('mock_database/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if item['filename'] == os.path.basename(filename):
                    return item
    except:
        return None
    return None


scanner = load_scanner()


# ==============================================================================
# 🧭 3. HEADER & SYSTEM STATUS BANNER
# ------------------------------------------------------------------------------
# [ลักษณะหน้าตา UI]:
# - แถบส่วนหัวด้านบนสุด (Top Banner)
# - ซ้าย: ไอคอนเครื่องมือสีแดง + ชื่อระบบ + สโลแกนเทคโนโลยี
# - ขวา: ป้ายสถานะระบบ (System Online 🟢) + จำนวนรายการที่ตรวจพบปัจจุบัน
# ==============================================================================
sync_checkbox_states()
total_items = len(st.session_state.detected_list)
checked_items = sum(1 for x in st.session_state.detected_list if x.get('checked', False))
history_records = load_handover_history()

st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; background: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; padding: 14px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); gap: 12px;">
    <div style="display: flex; align-items: center; gap: 14px;">
        <div style="background: linear-gradient(135deg, #E81D23, #B91C1C); color: #FFFFFF; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; box-shadow: 0 3px 8px rgba(232, 29, 35, 0.3);">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
        </div>
        <div>
            <h2 style="margin: 0; color: #0F172A; font-size: 20px; font-weight: 700;">ระบบตรวจนับและสแกนเครื่องมืออัจฉริยะ</h2>
            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 13px;">SIFT Feature Matching & Tool Handover Audit Log</p>
        </div>
    </div>
    <div style="display: flex; gap: 8px; align-items: center;">
        <span style="background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
            <span style="width: 7px; height: 7px; border-radius: 50%; background-color: #10B981; display: inline-block;"></span>
            AI Engine Ready
        </span>
        <span style="background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 8px;">
            ตรวจพบแล้ว: {checked_items}/{total_items} ชิ้น
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 🚨 DIALOG: QUICK RESOLVE PENDING INCOMPLETE JOBS (เคลียร์งานค้างด่วน)
# ==============================================================================
@st.dialog("🚨 รายการงานที่ยังตามหาเครื่องมือไม่ครบ (Pending Incomplete Jobs)", width="large")
def quick_resolve_dialog():
    history = load_handover_history()
    unresolved = [h for h in history if not h.get('is_complete', False)]

    if not unresolved:
        st.success("🎉 ยอดเยี่ยม! เครื่องมือครบถ้วนทุกงานแล้ว ไม่มีงานค้างในระบบ")
        return

    st.markdown(f"""<div style="background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 12px; margin-bottom: 14px;">
<strong style="color: #991B1B; font-size: 0.95rem;">⚠️ มีงานที่เครื่องมือยังไม่ครบทั้งหมด {len(unresolved)} รายการ:</strong>
<p style="color: #7F1D1D; font-size: 0.84rem; margin: 4px 0 0 0;">
กดปุ่ม <b>'✅ บันทึกว่าพบแล้ว'</b> ด้านหลังเครื่องมือที่ตามหาเจอแล้ว เพื่ออัปเดตสถานะและเคลียร์งานค้างได้ทันทีโดยไม่ต้องไปค้นหา
</p>
</div>""", unsafe_allow_html=True)

    for job in unresolved:
        missing_items = [(idx, itm) for idx, itm in enumerate(job.get('items', [])) if not itm.get('checked', False)]
        with st.container(border=True):
            st.markdown(f"""<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 8px;">
<div>
<strong style="font-size: 1rem; color: #0F172A;">🏷️ {job['job_id']}</strong>
<span style="font-size: 0.82rem; color: #64748B; margin-left: 8px;">ช่าง: <b>{job['inspector']}</b> | แผนก: <b>{job.get('bay', '-')}</b> | วันที่: {job['date']} {job['time']} น.</span>
</div>
<span style="background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
ขาด {len(missing_items)} ชิ้น (ตรวจพบ {job.get('checked_items', 0)}/{job.get('total_items', 0)})
</span>
</div>""", unsafe_allow_html=True)

            for itm_idx, itm in missing_items:
                fn = itm.get('filename', '')
                c_m1, c_m2, c_m3 = st.columns([0.12, 0.60, 0.28])
                with c_m1:
                    if fn and os.path.exists(f"mock_database/{fn}"):
                        try:
                            st.image(f"mock_database/{fn}", width=44)
                        except:
                            st.write("🔧")
                    else:
                        st.write("🔧")
                with c_m2:
                    st.markdown(f"""<div style="font-weight: 700; font-size: 0.88rem; color: #DC2626;">❌ {itm.get('name', fn)}</div>
<div style="font-size: 0.76rem; color: #64748B;"><span class='badge-category' style='font-size: 0.68rem;'>{itm.get('category', 'General')}</span> {itm.get('description', '')}</div>""", unsafe_allow_html=True)
                with c_m3:
                    st.button(
                        "✅ บันทึกว่าพบแล้ว",
                        key=f"btn_quick_found_{job['job_id']}_{itm_idx}",
                        on_click=mark_tool_as_found,
                        args=(job['job_id'], itm_idx),
                        use_container_width=True
                    )
                st.markdown("<div style='border-bottom: 1px dashed #F1F5F9; margin: 3px 0;'></div>", unsafe_allow_html=True)


# ==============================================================================
# 🗂️ 4. NAVIGATION TAB BAR (4 TABS)
# ------------------------------------------------------------------------------
# [ลักษณะหน้าตา UI]:
# - แถบเลือกสลับ 4 หน้าต่างหลัก:
#   1. สแกนเครื่องมือ (Scanner)
#   2. รายการเช็คลิสต์ (Checklist)
#   3. จัดการถาด (Tray)
#   4. ประวัติการส่งมอบงาน (Handover History)
# ==============================================================================
st.markdown("<div class='custom-nav-bar'>", unsafe_allow_html=True)
c_nav1, c_nav2, c_nav3, c_nav4 = st.columns(4)

with c_nav1:
    is_scan_active = (st.session_state.active_view == 'scan')
    if st.button("📷 1. สแกน (Scanner)", key="nav_btn_scan", type="primary" if is_scan_active else "secondary", use_container_width=True):
        st.session_state.active_view = "scan"
        st.rerun()

with c_nav2:
    is_check_active = (st.session_state.active_view == 'checklist')
    label_check = f"📋 2. เช็คลิสต์ ({total_items})"
    if st.button(label_check, key="nav_btn_check", type="primary" if is_check_active else "secondary", use_container_width=True):
        st.session_state.active_view = "checklist"
        st.rerun()

with c_nav3:
    is_tray_active = (st.session_state.active_view == 'tray')
    tray_count = len(scanner.list_tray_templates())
    label_tray = f"📥 3. ถาด ({tray_count})"
    if st.button(label_tray, key="nav_btn_tray", type="primary" if is_tray_active else "secondary", use_container_width=True):
        st.session_state.active_view = "tray"
        st.rerun()

with c_nav4:
    is_hist_active = (st.session_state.active_view == 'history')
    hist_count = len(history_records)
    label_hist = f"📜 4. ประวัติส่งมอบ ({hist_count})"
    if st.button(label_hist, key="nav_btn_history", type="primary" if is_hist_active else "secondary", use_container_width=True):
        st.session_state.active_view = "history"
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 🔍 5. DIALOG: SCAN PROCESSING POPUP
# ------------------------------------------------------------------------------
# [ลักษณะหน้าตา UI]:
# - กล่องป๊อปอัปอนิเมชันเรดาร์หมุน (Radar Scan Animation)
# - Progress bar วิ่งแสดง 3 สเต็ป: ค้นหา Keypoints ➔ เทียบ SIFT ➔ สรุปรายการ
# ==============================================================================
@st.dialog("กำลังวิเคราะห์รูปภาพเครื่องมือ", width="small")
def scan_processing_dialog(opencv_img):
    st.markdown("""
    <div style="text-align: center; padding: 6px 0 10px 0;">
        <div class="radar-scan-anim">
            <div class="radar-beam"></div>
            <div style="font-size: 28px; z-index: 2;">🔍</div>
        </div>
        <h4 style="color: #0F172A; margin: 14px 0 4px 0; font-size: 1.1rem; font-weight: 700;">AI กำลังค้นหาเครื่องมือ</h4>
        <p style="color: #64748B; font-size: 0.85rem; margin-bottom: 8px;">ใช้เทคนิค SIFT Feature Matching & Tiling Inspection</p>
    </div>
    """, unsafe_allow_html=True)
    
    status_text = st.empty()
    prog_bar = st.progress(25)
    
    status_text.markdown("<p style='text-align: center; color: #64748B; font-size: 0.86rem;'>ขั้นที่ 1/3: สกัดจุดลักษณะเด่น (Keypoints Extraction)...</p>", unsafe_allow_html=True)
    time.sleep(0.3)
    
    prog_bar.progress(60)
    status_text.markdown("<p style='text-align: center; color: #64748B; font-size: 0.86rem;'>ขั้นที่ 2/3: จับคู่รูปทรงกับฐานข้อมูล (Feature Matching)...</p>", unsafe_allow_html=True)
    
    # รันการค้นหาอุปกรณ์จริง
    results = scanner.scan_with_tiling(opencv_img, threshold=8)
    
    prog_bar.progress(95)
    status_text.markdown("<p style='text-align: center; color: #64748B; font-size: 0.86rem;'>ขั้นที่ 3/3: ประมวลผลและอัปเดตเช็คลิสต์...</p>", unsafe_allow_html=True)
    time.sleep(0.25)
    prog_bar.progress(100)
    
    if results:
        count_new = 0
        existing_files = [x['filename'] for x in st.session_state.detected_list]
        
        for res in results:
            if res['filename'] not in existing_files:
                info = get_product_info(res['filename'])
                display_name = info['name'] if info else res['filename']
                category = info['category'] if info else "General"
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
            status_text.markdown(f"""
            <div style="background-color: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 12px; margin: 10px 0; text-align: center;">
                <strong style="color: #065F46; font-size: 1rem; display: block;">🎉 ตรวจพบ {count_new} เครื่องมือใหม่!</strong>
                <span style="color: #047857; font-size: 0.84rem; display: block; margin-top: 2px;">กำลังนำคุณไปยังหน้ารายการเช็คลิสต์...</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            status_text.markdown(f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin: 10px 0; text-align: center;">
                <strong style="color: #334155; font-size: 0.96rem; display: block;">พบ {len(results)} รายการ (มีอยู่ในระบบแล้ว)</strong>
                <span style="color: #64748B; font-size: 0.84rem; display: block; margin-top: 2px;">กำลังนำคุณไปยังหน้ารายการเช็คลิสต์...</span>
            </div>
            """, unsafe_allow_html=True)
            
        time.sleep(0.9)
        st.session_state.active_view = "checklist"
        st.rerun()
    else:
        status_text.markdown("""
        <div style="background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 12px; margin: 10px 0; text-align: center;">
            <strong style="color: #B91C1C; font-size: 0.95rem; display: block;">ไม่พบเครื่องมือที่ตรงกับฐานข้อมูล</strong>
            <span style="color: #7F1D1D; font-size: 0.82rem; display: block; margin-top: 4px;">คำแนะนำ: วางเครื่องมือบนพื้นหลังเรียบ และปรับแสงให้ชัดเจน</span>
        </div>
        """, unsafe_allow_html=True)
        
        c_dlg1, c_dlg2 = st.columns(2)
        with c_dlg1:
            if st.button("ลองสแกนใหม่", use_container_width=True):
                st.rerun()
        with c_dlg2:
            if st.button("ไปยังรายการเช็คลิสต์", use_container_width=True):
                st.session_state.active_view = "checklist"
                st.rerun()


# ==============================================================================
# ==============================================================================
# 📷 6. VIEW 1: SCANNER INTERFACE (หน้าสแกนเครื่องมือ)
# ------------------------------------------------------------------------------
# [ลักษณะการทำงานแบบรวดเร็ว ไม่ซับซ้อน]:
# - ถ่ายรูปหรืออัปโหลดรูป ➔ กด [⚡ เริ่มสแกนหาเครื่องมือ]
# - เมื่อสแกนเสร็จ ระบบจะนำรายการเครื่องมือที่ตรวจพบทั้งหมด เข้าสู่หน้ารายการเช็คลิสต์ทันที!
# ==============================================================================
def render_scanner():
    st.markdown("""
    <div style="border-left: 4px solid #E81D23; padding-left: 12px; margin-bottom: 14px;">
        <h3 style="margin: 0; color: #0F172A; font-size: 19px;">📷 ถ่ายภาพหรืออัปโหลดเพื่อสแกน</h3>
        <p style="margin: 2px 0 0 0; color: #64748B; font-size: 13px;">ระบบรองรับการตรวจจับหลายชิ้นพร้อมกันในภาพเดียว (Multi-Object Detection)</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_ctrl, col_display = st.columns([1, 1.4], gap="medium")
    opencv_img = None
    
    with col_ctrl:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 15px; margin-bottom: 8px;'>1. แหล่งรูปภาพ</h4>", unsafe_allow_html=True)
            input_method = st.radio("เลือกวิธีนำเข้าภาพ:", ["📸 กล้อง (Camera)", "📁 อัปโหลดไฟล์ (Upload)"], horizontal=True, key="scan_input_method")
            
            if input_method == "📸 กล้อง (Camera)":
                st.caption("💡 คำแนะนำ: ถือกล้องขนานกับโต๊ะ วางเครื่องมือไม่ซ้อนทับกัน")
                img_file = st.camera_input("ถ่ายภาพเครื่องมือ", key="cam_input", on_change=keep_only_checked_items)
                if img_file:
                    opencv_img = cv2.imdecode(np.frombuffer(img_file.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            else:
                img_file = st.file_uploader("เลือกไฟล์ภาพเครื่องมือ", type=['jpg', 'jpeg', 'png'], key="file_input", on_change=keep_only_checked_items)
                if img_file:
                    opencv_img = cv2.imdecode(np.frombuffer(img_file.getvalue(), np.uint8), cv2.IMREAD_COLOR)

    with col_display:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 15px; margin-bottom: 8px;'>2. พรีวิวภาพและจุดสแกน (SIFT Keypoints Feed)</h4>", unsafe_allow_html=True)
            
            if opencv_img is not None:
                # ตรวจจับขอบกระดาน/ถาดอัตโนมัติ เพื่อตัดผนังหรือพื้นหลังที่ไม่เกี่ยวข้องออก
                target_scan_img, is_board_detected, board_pts = detect_and_crop_board(opencv_img)
                
                if is_board_detected:
                    st.success("✂️ **ตรวจพบขอบกระดาน/ถาดอัตโนมัติ**: ระบบทำการ Crop เพื่อสแกนเฉพาะเครื่องมือและตัดพื้นหลังผนังออกเรียบร้อย")
                    left_preview_img = draw_board_boundary(opencv_img, board_pts)
                    left_caption = "ภาพถ่ายต้นฉบับ (ตีกรอบขอบกระดาน 🟢)"
                else:
                    left_preview_img = opencv_img
                    left_caption = "ภาพถ่ายต้นฉบับ"

                viz_img, kp_count = visualize_tool_keypoints(target_scan_img.copy())

                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    st.image(left_preview_img, channels="BGR", caption=left_caption, use_container_width=True)
                with img_col2:
                    st.image(viz_img, channels="BGR", caption=f"จุดสแกนบนเครื่องมือ ({kp_count} จุด)", use_container_width=True)
                
                if isinstance(kp_count, int) and kp_count < 500:
                    st.warning(f"⚠️ จุดสแกนค่อนข้างน้อย ({kp_count} จุด) แนะนำให้เพิ่มแสงสว่างหรือขยับกล้องเข้าใกล้")
                
                st.divider()
                if st.button("⚡ เริ่มสแกนหาเครื่องมือทั้งหมด", type="primary", use_container_width=True):
                    with st.spinner("AI กำลังวิเคราะห์และตรวจจับเครื่องมือทั้งหมดในภาพ..."):
                        results = scanner.scan_with_tiling(target_scan_img, threshold=8)
                        
                        if results:
                            st.session_state.source_type = "scan"
                            st.session_state.current_tray_name = None
                            existing_files = [x['filename'] for x in st.session_state.detected_list]
                            for res in results:
                                if res['filename'] not in existing_files:
                                    info = get_product_info(res['filename'])
                                    st.session_state.detected_list.append({
                                        "filename": res['filename'],
                                        "name": info['name'] if info else res['filename'],
                                        "category": info['category'] if info else "General",
                                        "description": info['description'] if info else "-",
                                        "score": res['score'],
                                        "checked": False
                                    })
                            st.session_state.active_view = "checklist"
                            st.rerun()
                        else:
                            st.error("❌ ไม่พบเครื่องมือที่ตรงกับฐานข้อมูล กรุณาปรับแสงสว่างหรือวางเครื่องมือให้ชัดเจน")
            else:
                st.info("👈 กรุณาถ่ายภาพหรือเลือกไฟล์รูปภาพทางซ้าย เพื่อดูจุดสแกนและเริ่มการตรวจจับ")


# ==============================================================================
# 📝 DIALOG: HANDOVER CONFIRMATION POPUP (ป๊อปอัปส่งมอบงาน)
# ==============================================================================
@st.dialog("📝 บันทึกและส่งมอบงาน (Tool Handover)", width="medium")
def handover_dialog():
    total_c = len(st.session_state.detected_list)
    chk_c = sum(1 for x in st.session_state.detected_list if x.get('checked', False))
    is_100 = (chk_c == total_c and total_c > 0)
    
    st.markdown(f"""
    <div style="background: {'#ECFDF5' if is_100 else '#FFFBEB'}; border: 1px solid {'#A7F3D0' if is_100 else '#FDE68A'}; border-radius: 8px; padding: 12px; margin-bottom: 14px;">
        <strong style="color: {'#065F46' if is_100 else '#92400E'}; font-size: 1rem;">
            {'✅ ตรวจสอบเครื่องมือครบทุกชิ้น 100%' if is_100 else f'⚠️ ตรวจสอบแล้ว {chk_c}/{total_c} ชิ้น'}
        </strong>
        <p style="margin: 4px 0 0 0; color: {'#047857' if is_100 else '#B45309'}; font-size: 0.85rem;">
            กรอกข้อมูลผู้ตรวจและรหัสงานเพื่อบันทึกประวัติเข้าสู่ระบบ
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    auto_job_id = f"JOB-{datetime.now().strftime('%Y%m%d-%H%M')}"
    c_h1, c_h2 = st.columns(2)
    with c_h1:
        job_id = st.text_input("รหัสงาน (Job ID)", value=auto_job_id)
        inspector_name = st.text_input("ชื่อช่าง / ผู้ตรวจสอบ *", placeholder="เช่น สมชาย ช่างยนต์")
    with c_h2:
        bay = st.text_input("ช่องบริการ / แผนก", value="Bay 01 (ช็อปเครื่องกล)")
        note = st.text_input("หมายเหตุ / ป้ายทะเบียน", placeholder="เช่น ซ่อมบำรุงประจำรอบ 10,000 กม.")

    st.divider()
    
    c_sub1, c_sub2 = st.columns(2)
    with c_sub1:
        if st.button("💾 ยืนยันการบันทึกส่งมอบ", type="primary", use_container_width=True):
            if not inspector_name.strip():
                st.error("กรุณากรอกชื่อผู้ตรวจสอบก่อนบันทึก")
            else:
                src_type = st.session_state.get('source_type', 'scan')
                t_name = st.session_state.get('current_tray_name', None)
                saved_record = save_handover_record(
                    job_id=job_id,
                    inspector_name=inspector_name.strip(),
                    bay=bay.strip(),
                    note=note.strip(),
                    items=list(st.session_state.detected_list),
                    is_complete=is_100,
                    source_type=src_type,
                    tray_name=t_name
                )
                st.session_state.last_handover_success = saved_record
                # เคลียร์เช็คลิสต์เพื่อเริ่มงานใหม่
                st.session_state.detected_list = []
                for k in list(st.session_state.keys()):
                    if str(k).startswith("chk_"):
                        del st.session_state[k]
                st.session_state.active_view = "history"
                st.rerun()
    with c_sub2:
        if st.button("ยกเลิก", use_container_width=True):
            st.rerun()


# ==============================================================================
# 📋 7. VIEW 2: CHECKLIST INTERFACE (หน้ารายการเช็คลิสต์)
# ==============================================================================
def render_checklist():
    sync_checkbox_states()
    
    total_count = len(st.session_state.detected_list)
    checked_count = sum(1 for x in st.session_state.detected_list if x.get('checked', False))
    remaining_count = total_count - checked_count
    percent = int((checked_count / total_count * 100)) if total_count > 0 else 0

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #E81D23; padding-left: 12px; margin-bottom: 12px;">
        <div>
            <h3 style="margin: 0; color: #0F172A; font-size: 19px;">📋 รายการตรวจสอบเครื่องมือ</h3>
            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 13px;">ติ๊กเครื่องหมายถูกเมื่อตรวจสอบอุปกรณ์แต่ละชิ้นเรียบร้อย</p>
        </div>
        <span style="background-color: #E81D23; color: #FFFFFF; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 700;">
            {total_count} รายการ
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 3 กล่องสรุปสถานะ
    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin: 12px 0 8px 0;">
        <div style="flex: 1; background: #0F172A; color: #FFFFFF; border-radius: 10px; padding: 10px; text-align: center;">
            <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">ทั้งหมด</div>
            <div style="font-size: 22px; font-weight: 800; margin-top: 2px;">{total_count}</div>
        </div>
        <div style="flex: 1; background: #FFFFFF; color: #0F172A; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; color: #E81D23; text-transform: uppercase; font-weight: 600;">ยังไม่ตรวจ</div>
            <div style="font-size: 22px; font-weight: 800; color: #E81D23; margin-top: 2px;">{remaining_count}</div>
        </div>
        <div style="flex: 1; background: #FFFFFF; color: #0F172A; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; color: #10B981; text-transform: uppercase; font-weight: 600;">ตรวจแล้ว ({percent}%)</div>
            <div style="font-size: 22px; font-weight: 800; color: #10B981; margin-top: 2px;">{checked_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(percent / 100)

    # แถบแจ้งเตือนส่งมอบงานเมื่อตรวจครบ
    if total_count > 0:
        c_handover1, c_handover2 = st.columns([2, 1])
        with c_handover1:
            if checked_count == total_count:
                st.markdown("""
                <div style="background-color: #ECFDF5; border: 1px solid #10B981; border-radius: 8px; padding: 10px; margin: 4px 0;">
                    <strong style="color: #065F46; font-size: 14px;">🎉 ตรวจครบทุกชิ้น 100% เรียบร้อย พร้อมทำการส่งมอบงาน</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.caption(f"ตรวจแล้ว {checked_count} จาก {total_count} รายการ สามารถกดส่งมอบเพื่อบันทึกประวัติได้")
        with c_handover2:
            is_tray_source = (st.session_state.get('source_type') == 'tray')
            btn_title = "💾 ลงทะเบียนและบันทึกข้อมูล" if is_tray_source else "📝 บันทึกและส่งมอบงาน (Handover)"
            if st.button(btn_title, type="primary", use_container_width=True):
                handover_dialog()

    # ปุ่มจัดการ Bulk Actions
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    def update_all_checked(value):
        for i in range(len(st.session_state.detected_list)):
            st.session_state.detected_list[i]['checked'] = value
            st.session_state[f"chk_{i}"] = value

    with c_btn1:
        if st.button("✅ ตรวจครบทั้งหมด", use_container_width=True):
            update_all_checked(True)
            st.rerun()
    with c_btn2:
        if st.button("🔄 ยกเลิกที่ตรวจ", use_container_width=True):
            update_all_checked(False)
            st.rerun()
    with c_btn3:
        if st.button("🗑️ ล้างรายการทั้งหมด", use_container_width=True):
            st.session_state.detected_list = []
            for k in list(st.session_state.keys()):
                if str(k).startswith("chk_"):
                    del st.session_state[k]
            st.rerun()

    # ช่องค้นหาและตัวกรอง
    c_filter, c_search = st.columns([1, 1.2])
    with c_filter:
        filter_mode = st.radio(
            "กรองสถานะ:",
            options=["all", "unchecked", "checked"],
            format_func=lambda x: f"ทั้งหมด ({total_count})" if x == "all" else (f"ยังไม่ตรวจ ({remaining_count})" if x == "unchecked" else f"ตรวจแล้ว ({checked_count})"),
            horizontal=True,
            label_visibility="collapsed",
            key="chk_filter_radio"
        )
    with c_search:
        search_kw = st.text_input("ค้นหา", placeholder="🔍 พิมพ์ชื่อ หรือหมวดหมู่อุปกรณ์...", label_visibility="collapsed", key="chk_search_input")

    # กล่องแสดงรายการแบบ Scrollable Container
    with st.container(height=450):
        if not st.session_state.detected_list:
            st.info("💡 ยังไม่มีรายการเครื่องมือ กรุณาไปที่แท็บ '1. สแกน' เพื่อเริ่มต้น")
        else:
            filtered_indices = []
            for i, item in enumerate(st.session_state.detected_list):
                if search_kw:
                    kw = search_kw.lower()
                    if kw not in item['name'].lower() and kw not in item.get('category', '').lower():
                        continue
                if filter_mode == "unchecked" and item.get('checked', False):
                    continue
                if filter_mode == "checked" and not item.get('checked', False):
                    continue
                filtered_indices.append(i)

            if not filtered_indices:
                st.markdown("<p style='text-align: center; color: #64748B; padding: 24px 0;'>ไม่พบรายการที่ตรงกับคำค้นหา</p>", unsafe_allow_html=True)
            else:
                for orig_i in filtered_indices:
                    item = st.session_state.detected_list[orig_i]
                    is_item_checked = item.get('checked', False)
                    
                    with st.container(border=True):
                        c_chk, c_img, c_info, c_del = st.columns([0.08, 0.12, 0.72, 0.08])
                        
                        with c_chk:
                            def make_toggle_handler(idx):
                                def handler():
                                    st.session_state.detected_list[idx]['checked'] = st.session_state.get(f"chk_{idx}", False)
                                return handler

                            is_checked = st.checkbox(
                                label=f"เลือก {item['name']}", 
                                value=is_item_checked, 
                                key=f"chk_{orig_i}",
                                on_change=make_toggle_handler(orig_i),
                                label_visibility="collapsed"
                            )
                        
                        with c_img:
                            try:
                                st.image(f"mock_database/{item['filename']}", width=48)
                            except:
                                st.write("🔧")
                        
                        with c_info:
                            name_style = "color: #94A3B8; text-decoration: line-through;" if is_checked else "color: #0F172A; font-weight: 700;"
                            st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; align-items: baseline; gap: 6px;">
                                <span style="font-size: 0.95rem; {name_style}">
                                    {item['name']}
                                </span>
                                <span class='badge-score'>★ {item['score']}</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px; margin-top: 3px;">
                                <span class='badge-category'>{item['category']}</span>
                                <span style="font-size: 0.8rem; color: #64748B;">{item['description']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with c_del:
                            if st.button("✕", key=f"del_{orig_i}", help="ลบรายการนี้"):
                                st.session_state.detected_list.pop(orig_i)
                                for k in list(st.session_state.keys()):
                                    if str(k).startswith("chk_"):
                                        del st.session_state[k]
                                st.rerun()


@st.cache_data
def get_image_base64(filepath):
    """แปลงรูปภาพเครื่องมือเป็น Base64 Data URI เพื่อให้พิมพ์และแสดงผลได้คมชัด 100% (Cached)"""
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, "rb") as img_f:
                encoded = base64.b64encode(img_f.read()).decode('ascii')
                ext = filepath.split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{encoded}"
        except Exception:
            return ""
    return ""


def generate_printable_html(rec):
    """สร้างเนื้อหาเอกสาร HTML สำหรับพิมพ์ขนาด A4 เต็มหน้า อย่างเป็นทางการ ไร้พื้นหลังเว็บปน"""
    is_p = rec.get('is_complete', False)
    status_bg = "#ECFDF5" if is_p else "#FEF2F2"
    status_col = "#059669" if is_p else "#DC2626"
    status_bdr = "#A7F3D0" if is_p else "#FECACA"
    status_txt = "✅ ครบถ้วนสมบูรณ์ (PASSED)" if is_p else "⚠️ เครื่องมือไม่ครบถ้วน (INCOMPLETE)"

    rows_html = ""
    for idx, itm in enumerate(rec.get('items', []), 1):
        fn = itm.get('filename', '')
        img_b64 = get_image_base64(f"mock_database/{fn}") if fn else ""
        img_tag = f'<img src="{img_b64}" style="width: 40px; height: 40px; object-fit: contain; border-radius: 4px; border: 1px solid #E2E8F0;">' if img_b64 else '<span style="font-size: 20px;">🔧</span>'

        is_chk = itm.get('checked', False)
        status_cell = f'<span style="color: #059669; font-weight: bold;">✅ ผ่าน (ครบ)</span>' if is_chk else f'<span style="color: #DC2626; font-weight: bold;">❌ ไม่พบ</span>'
        if itm.get('resolved_at'):
            status_cell += f'<div style="color: #059669; font-size: 10.5px; margin-top: 2px;">(พบย้อนหลังเมื่อ {itm["resolved_at"]})</div>'

        rows_html += f"""
        <tr style="border-bottom: 1px solid #E2E8F0;">
            <td style="padding: 6px 8px; text-align: center; font-weight: bold; color: #64748B;">{idx}</td>
            <td style="padding: 6px 8px; text-align: center;">{img_tag}</td>
            <td style="padding: 6px 8px; font-weight: bold; color: #0F172A;">
                {itm.get('name', fn)}
                <div style="font-size: 11px; color: #64748B; font-weight: normal;">{itm.get('description', '')}</div>
            </td>
            <td style="padding: 6px 8px; font-size: 11.5px; color: #475569;">{itm.get('category', 'General')}</td>
            <td style="padding: 6px 8px; text-align: center; font-size: 11.5px; color: #E81D23; font-weight: bold;">★ {itm.get('score', 100)}</td>
            <td style="padding: 6px 8px; text-align: right;">{status_cell}</td>
        </tr>
        """

    note_text = rec.get('note') or '-'

    html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>ใบส่งมอบงาน - {rec['job_id']}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 12mm 15mm;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #0F172A;
            background: #FFFFFF;
            margin: 0;
            padding: 20px 24px;
            font-size: 12.5px;
            line-height: 1.4;
        }}
        .header-box {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2.5px solid #0F172A;
            padding-bottom: 12px;
            margin-bottom: 14px;
        }}
        .title-main {{
            font-size: 19px;
            font-weight: 800;
            color: #0F172A;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .title-sub {{
            font-size: 11.5px;
            color: #64748B;
            margin-top: 2px;
            font-weight: 600;
        }}
        .status-badge {{
            background-color: {status_bg};
            color: {status_col};
            border: 1.5px solid {status_bdr};
            padding: 5px 12px;
            border-radius: 6px;
            font-weight: 800;
            font-size: 12px;
            display: inline-block;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 16px;
        }}
        .info-item b {{
            color: #64748B;
            font-size: 10.5px;
            text-transform: uppercase;
            display: block;
            margin-bottom: 2px;
        }}
        .info-item span {{
            font-size: 13px;
            font-weight: 700;
            color: #0F172A;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th {{
            background-color: #0F172A;
            color: #FFFFFF;
            padding: 7px 8px;
            font-size: 11.5px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .signature-section {{
            margin-top: 28px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            text-align: center;
        }}
        .sig-line {{
            height: 40px;
            border-bottom: 1.5px dashed #94A3B8;
            margin-bottom: 6px;
        }}
        .footer-note {{
            margin-top: 24px;
            font-size: 10px;
            color: #94A3B8;
            text-align: center;
            border-top: 1px solid #F1F5F9;
            padding-top: 6px;
        }}
        @media print {{
            body {{
                padding: 0;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="header-box">
        <div>
            <div class="title-main">🔧 ใบส่งมอบและตรวจสอบเครื่องมือ</div>
            <div class="title-sub">TOOL SCANNER & HANDOVER AUDIT REPORT</div>
        </div>
        <div>
            <div class="status-badge">{status_txt}</div>
        </div>
    </div>

    <div class="info-grid">
        <div class="info-item">
            <b>🏷️ รหัสงาน (Job ID)</b>
            <span style="color: #E81D23;">{rec['job_id']}</span>
        </div>
        <div class="info-item">
            <b>📅 วันที่ - เวลา</b>
            <span>{rec['date']} {rec['time']} น.</span>
        </div>
        <div class="info-item">
            <b>👤 ช่างผู้รับผิดชอบ</b>
            <span>{rec['inspector']}</span>
        </div>
        <div class="info-item">
            <b>🏢 แผนก / โซน (Bay)</b>
            <span>{rec.get('bay', '-')}</span>
        </div>
        <div class="info-item">
            <b>🔧 สรุปจำนวนเครื่องมือ</b>
            <span>ตรวจครบ {rec.get('checked_items', 0)} / {rec.get('total_items', 0)} ชิ้น</span>
        </div>
        <div class="info-item">
            <b>📝 หมายเหตุ</b>
            <span style="font-weight: normal;">{note_text}</span>
        </div>
    </div>

    <table border="0">
        <thead>
            <tr>
                <th style="width: 35px; text-align: center;">#</th>
                <th style="width: 55px; text-align: center;">รูปภาพ</th>
                <th style="text-align: left;">ชื่อเครื่องมือ (Tool Name)</th>
                <th style="width: 110px; text-align: left;">หมวดหมู่</th>
                <th style="width: 60px; text-align: center;">คะแนน</th>
                <th style="width: 130px; text-align: right;">สถานะตรวจนับ</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="signature-section">
        <div>
            <div class="sig-line"></div>
            <div style="font-size: 11.5px; font-weight: bold; color: #1E293B;">ลงชื่อ .............................................................. (ผู้ส่งมอบงาน)</div>
            <div style="font-size: 10.5px; color: #64748B;">ช่างผู้ตรวจรับผิดชอบ / Inspector</div>
        </div>
        <div>
            <div class="sig-line"></div>
            <div style="font-size: 11.5px; font-weight: bold; color: #1E293B;">ลงชื่อ .............................................................. (ผู้ตรวจรับงาน)</div>
            <div style="font-size: 10.5px; color: #64748B;">หัวหน้าแผนก / Supervisor</div>
        </div>
    </div>

    <div class="footer-note">
        เอกสารนี้ออกโดยระบบ AI Tool Scanner & Handover System | วันที่พิมพ์: {datetime.now().strftime('%d/%m/%Y %H:%M น.')}
    </div>
</body>
</html>"""
    return html_content


# ==============================================================================
# 📜 8. VIEW 4: HANDOVER HISTORY & AUDIT LOG (หน้าประวัติการส่งมอบ)
# ------------------------------------------------------------------------------
# [ลักษณะหน้าตา UI]:
# - แถบสถิติประวัติ: จำนวนงานที่ส่งมอบแล้ว, อัตราผ่าน (Pass Rate), รวมชิ้นที่ตรวจ
# - ช่องค้นหาประวัติตาม Job ID หรือชื่อช่าง
# - รายการการ์ดประวัติแต่ละใบ พร้อมปุ่มดาวน์โหลด CSV, พิมพ์เอกสาร และดูรายละเอียด
# ==============================================================================
def render_history():
    history = load_handover_history()
    
    st.markdown("""
    <div style="border-left: 4px solid #E81D23; padding-left: 12px; margin-bottom: 14px;">
        <h3 style="margin: 0; color: #0F172A; font-size: 19px;">📜 ประวัติการตรวจสอบและส่งมอบงาน (Handover Audit Logs)</h3>
        <p style="margin: 2px 0 0 0; color: #64748B; font-size: 13px;">รายการเอกสารส่งมอบที่บันทึกแล้วในระบบ สามารถตรวจสอบย้อนหลังและดาวน์โหลดรายงานได้</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.last_handover_success:
        rec = st.session_state.last_handover_success
        st.success(f"🎉 บันทึกการส่งมอบงานรหัส **{rec['job_id']}** สำเร็จเรียบร้อย!")

    if 'history_updated_msg' in st.session_state and st.session_state.history_updated_msg:
        st.success(f"🎉 {st.session_state.history_updated_msg}")
        del st.session_state['history_updated_msg']

    if not history:
        st.info("💡 ยังไม่มีประวัติการส่งมอบงานในระบบ เมื่อตรวจเช็คลิสต์เสร็จให้กดปุ่ม 'บันทึกและส่งมอบงาน'")
        return

    # คำนวณสถิติภาพรวม
    total_jobs = len(history)
    complete_jobs = sum(1 for h in history if h.get('is_complete', False))
    total_tools_checked = sum(h.get('checked_items', 0) for h in history)
    pass_rate = int((complete_jobs / total_jobs * 100)) if total_jobs > 0 else 0

    # Summary KPI Cards
    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin-bottom: 16px;">
        <div style="flex: 1; background: #0F172A; color: #FFFFFF; border-radius: 10px; padding: 12px; text-align: center;">
            <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">งานส่งมอบทั้งหมด</div>
            <div style="font-size: 24px; font-weight: 800; margin-top: 2px;">{total_jobs} งาน</div>
        </div>
        <div style="flex: 1; background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; border-radius: 10px; padding: 12px; text-align: center;">
            <div style="font-size: 11px; color: #059669; text-transform: uppercase; font-weight: 600;">ความครบถ้วนสมบูรณ์ (Pass Rate)</div>
            <div style="font-size: 24px; font-weight: 800; color: #059669; margin-top: 2px;">{pass_rate}%</div>
        </div>
        <div style="flex: 1; background: #FFFFFF; color: #0F172A; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
            <div style="font-size: 11px; color: #64748B; text-transform: uppercase; font-weight: 600;">รวมเครื่องมือที่ตรวจสอบ</div>
            <div style="font-size: 24px; font-weight: 800; color: #E81D23; margin-top: 2px;">{total_tools_checked} ชิ้น</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def parse_record_date(rec):
        """แปลงวันที่และเวลาจาก Record เป็น datetime object"""
        if 'timestamp' in rec:
            try:
                return datetime.strptime(rec['timestamp'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        if 'date' in rec:
            try:
                return datetime.strptime(rec['date'], '%d/%m/%Y')
            except:
                pass
        return datetime.now()

    incomplete_count = sum(1 for h in history if not h.get('is_complete', False))
    complete_count = sum(1 for h in history if h.get('is_complete', False))

    def reset_all_filters():
        st.session_state.hist_search_input = ""
        st.session_state.hist_date_pills = "🌐 ทั้งหมด (All Time)"
        st.session_state.hist_status_filter = "🌐 งานทั้งหมด"
        if 'hist_status_pills' in st.session_state:
            del st.session_state['hist_status_pills']
        if 'hist_start_date' in st.session_state:
            del st.session_state['hist_start_date']
        if 'hist_end_date' in st.session_state:
            del st.session_state['hist_end_date']

    def reset_custom_date_filter():
        st.session_state.hist_date_pills = "🌐 ทั้งหมด (All Time)"
        if 'hist_start_date' in st.session_state:
            del st.session_state['hist_start_date']
        if 'hist_end_date' in st.session_state:
            del st.session_state['hist_end_date']

    # แถวที่ 1: ช่องค้นหา, ปุ่มรีเซ็ต และปุ่ม Export
    c_hsearch, c_hreset, c_hexport_all = st.columns([1.7, 0.5, 0.8])
    with c_hsearch:
        search_hist = st.text_input("ค้นหาประวัติ", placeholder="🔍 พิมพ์รหัสงาน (Job ID), ชื่อช่าง, หรือหมายเหตุ...", label_visibility="collapsed", key="hist_search_input")
    with c_hreset:
        st.button("🔄 ล้างค่า (Reset)", on_click=reset_all_filters, use_container_width=True, key="btn_reset_filters", help="ล้างคำค้นหาและรีเซ็ตช่วงเวลาทั้งหมด")

    # แถวที่ 2: กรองตามสถานะงาน (แยกแถวชัดเจน ไม่เบียดกัน)
    st.markdown("<p style='font-size: 0.84rem; font-weight: 700; color: #334155; margin: 6px 0 2px 0;'>📌 กรองสถานะงาน:</p>", unsafe_allow_html=True)
    pref_status = st.session_state.get('hist_status_filter', '🌐 งานทั้งหมด')
    if "ยังไม่ครบ" in pref_status:
        default_status = f"⚠️ เฉพาะงานที่ยังไม่ครบ ({incomplete_count})"
    elif "ครบถ้วน" in pref_status:
        default_status = f"✅ เฉพาะงานที่ครบถ้วน ({complete_count})"
    else:
        default_status = f"🌐 งานทั้งหมด ({total_jobs})"

    status_preset = st.pills(
        "กรองสถานะงาน:",
        options=[
            f"🌐 งานทั้งหมด ({total_jobs})",
            f"⚠️ เฉพาะงานที่ยังไม่ครบ ({incomplete_count})",
            f"✅ เฉพาะงานที่ครบถ้วน ({complete_count})"
        ],
        default=default_status,
        selection_mode="single",
        key="hist_status_pills",
        label_visibility="collapsed"
    ) or default_status

    # แถวที่ 3: กรองตามช่วงเวลา (แยกแถวชัดเจน)
    st.markdown("<p style='font-size: 0.84rem; font-weight: 700; color: #334155; margin: 6px 0 2px 0;'>📅 ช่วงเวลาที่ต้องการดู:</p>", unsafe_allow_html=True)
    date_preset = st.pills(
        "ช่วงเวลาที่ต้องการดู:",
        options=[
            "🌐 ทั้งหมด (All Time)",
            "🕒 1 เดือน (30 วัน)",
            "🕒 3 เดือน (90 วัน)",
            "🕒 6 เดือน (180 วัน)",
            "🕒 1 ปี (365 วัน)",
            "📅 กำหนดช่วงวันที่เอง"
        ],
        default="🌐 ทั้งหมด (All Time)",
        selection_mode="single",
        key="hist_date_pills",
        label_visibility="collapsed"
    ) or "🌐 ทั้งหมด (All Time)"

    now = datetime.now()
    cutoff_date = None
    custom_start_date = None
    custom_end_date = None

    if date_preset in ["🕒 1 เดือน (30 วัน)", "🕒 1 เดือน"]:
        cutoff_date = now - timedelta(days=30)
    elif date_preset in ["🕒 3 เดือน (90 วัน)", "🕒 3 เดือน"]:
        cutoff_date = now - timedelta(days=90)
    elif date_preset in ["🕒 6 เดือน (180 วัน)", "🕒 6 เดือน"]:
        cutoff_date = now - timedelta(days=180)
    elif date_preset in ["🕒 1 ปี (365 วัน)", "🕒 1 ปี"]:
        cutoff_date = now - timedelta(days=365)
    elif date_preset == "📅 กำหนดช่วงวันที่เอง":
        c_d1, c_d2, c_d3 = st.columns([1.2, 1.2, 0.8])
        today = now.date()
        default_start = (now - timedelta(days=30)).date()

        # ป้องกันวันที่ใน Session State เกินวันนี้
        if 'hist_start_date' in st.session_state and st.session_state.hist_start_date > today:
            st.session_state.hist_start_date = today

        with c_d1:
            custom_start_date = st.date_input(
                "📅 ตั้งแต่วันที่:", 
                value=default_start, 
                max_value=today,
                key="hist_start_date"
            )

        # วันสิ้นสุดต้องไม่น้อยกว่าวันเริ่มต้น และไม่เกินวันนี้
        min_end = custom_start_date if custom_start_date else default_start
        if 'hist_end_date' in st.session_state:
            if st.session_state.hist_end_date < min_end:
                st.session_state.hist_end_date = min_end
            elif st.session_state.hist_end_date > today:
                st.session_state.hist_end_date = today

        with c_d2:
            custom_end_date = st.date_input(
                "📅 ถึงวันที่:", 
                value=today, 
                min_value=min_end,
                max_value=today,
                key="hist_end_date"
            )
        with c_d3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            st.button("🔄 เคลียร์ช่วงวันที่", on_click=reset_custom_date_filter, use_container_width=True, key="btn_reset_custom_date")

    # กรองประวัติที่ตรงกับวันที่, คำค้นหา และสถานะงาน
    filtered_history = []
    for idx, rec in enumerate(history):
        rec_dt = parse_record_date(rec)

        # 1. กรองตามสถานะงาน (ครบ / ยังไม่ครบ)
        if "ยังไม่ครบ" in status_preset and rec.get('is_complete', False):
            continue
        if "ครบถ้วน" in status_preset and not rec.get('is_complete', False):
            continue

        # 2. กรองตามวันที่
        if cutoff_date and rec_dt < cutoff_date:
            continue
        if custom_start_date and custom_end_date:
            if not (custom_start_date <= rec_dt.date() <= custom_end_date):
                continue

        # 3. กรองตามคำค้นหา
        if search_hist:
            kw = search_hist.lower()
            match = (kw in rec['job_id'].lower() or 
                     kw in rec['inspector'].lower() or 
                     kw in rec.get('note', '').lower() or
                     kw in rec.get('bay', '').lower() or
                     (rec.get('tray_name') and kw in rec.get('tray_name', '').lower()))
            if not match:
                continue

        filtered_history.append((idx, rec))

    with c_hexport_all:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Job ID", "Date", "Time", "Inspector", "Bay", "Status", "Checked Items", "Total Items", "Note"])
        for _, h in filtered_history:
            writer.writerow([h['job_id'], h['date'], h['time'], h['inspector'], h['bay'], h['status'], h['checked_items'], h['total_items'], h.get('note', '')])
        
        st.download_button(
            label=f"📥 ดาวน์โหลด CSV ({len(filtered_history)} รายการ)",
            data=csv_buffer.getvalue().encode('utf-8-sig'),
            file_name=f"handovers_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    if not filtered_history:
        st.markdown("""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 32px 16px; text-align: center; margin-top: 10px;">
            <div style="font-size: 32px; margin-bottom: 8px;">🔍</div>
            <strong style="color: #475569; font-size: 1rem; display: block;">ไม่พบข้อมูลดังกล่าว</strong>
            <p style="color: #94A3B8; font-size: 0.84rem; margin: 4px 0 0 0;">ลองเปลี่ยนคำค้นหา หรือขยายช่วงวันที่ที่ต้องการดูข้อมูล</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # แสดงประวัติแต่ละรายการ
    for idx, rec in filtered_history:

        is_tray = (rec.get('source_type') == 'tray' or bool(rec.get('tray_name')))
        is_p = rec.get('is_complete', False)
        
        if is_tray:
            t_name = rec.get('tray_name') or "ถาดเครื่องมือ"
            s_col = "#059669" if is_p else "#DC2626"
            s_bg = "#ECFDF5" if is_p else "#FEF2F2"
            s_bdr = "#A7F3D0" if is_p else "#FECACA"
            s_txt = "✅ ครบถ้วน (Complete)" if is_p else "⚠️ ไม่ครบ (Incomplete)"
            badges_str = f'<span style="background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">📥 สแกนถาด: {t_name}</span> <span style="background-color: {s_bg}; color: {s_col}; border: 1px solid {s_bdr}; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">{s_txt}</span>'
        else:
            badges_str = f'<span style="background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 6px;">📷 สแกนปกติ</span>'

        with st.container(border=True):
            c_info1, c_info2, c_act = st.columns([1.5, 1.2, 0.8])
            with c_info1:
                st.markdown(f'<div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;"><strong style="color: #0F172A; font-size: 1.05rem;">🏷️ {rec["job_id"]}</strong>{badges_str}</div><div style="font-size: 0.85rem; color: #64748B; margin-top: 4px;">ช่างผู้ตรวจ: <b style="color: #334155;">{rec["inspector"]}</b> | แผนก: <b>{rec.get("bay", "-")}</b></div>', unsafe_allow_html=True)
            
            with c_info2:
                note_str = f" | 📝 {rec['note']}" if rec.get('note') else ""
                st.markdown(f'<div style="font-size: 0.85rem; color: #64748B;">📅 วันที่: <b>{rec["date"]} {rec["time"]} น.</b><br>🔧 เครื่องมือ: <b>{rec["checked_items"]}/{rec["total_items"]} ชิ้น</b>{note_str}</div>', unsafe_allow_html=True)

            with c_act:
                # ปุ่มดาวน์โหลด CSV เฉพาะใบนี้
                single_csv = io.StringIO()
                swriter = csv.writer(single_csv)
                swriter.writerow(["Job ID", rec['job_id']])
                swriter.writerow(["Date", rec['date'], "Time", rec['time']])
                swriter.writerow(["Inspector", rec['inspector'], "Bay", rec.get('bay', '')])
                swriter.writerow(["Status", rec['status']])
                swriter.writerow([])
                swriter.writerow(["No.", "Tool Name", "Category", "Match Score", "Checked"])
                for i_idx, itm in enumerate(rec.get('items', []), 1):
                    swriter.writerow([i_idx, itm.get('name'), itm.get('category'), itm.get('score'), "Yes (Resolved)" if itm.get('resolved_at') else ("Yes" if itm.get('checked') else "No")])
                
                c_act_b1, c_act_b2 = st.columns(2)
                with c_act_b1:
                    st.download_button(
                        label="📄 CSV",
                        data=single_csv.getvalue().encode('utf-8-sig'),
                        file_name=f"Handover_{rec['job_id']}.csv",
                        mime="text/csv",
                        key=f"dl_hist_{idx}",
                        use_container_width=True,
                        help="ดาวน์โหลดไฟล์ข้อมูล CSV"
                    )
                with c_act_b2:
                    if st.button("🖨️ พิมพ์", key=f"btn_print_job_{idx}", use_container_width=True, help="สั่งพิมพ์เอกสาร A4 / บันทึกเป็น PDF"):
                        st.session_state['active_print_job'] = rec
                        st.rerun()

            # แสดงรายการเครื่องมือในงานนี้ พร้อมรูปภาพประกอบ
            with st.expander("🔍 ดูรายการเครื่องมือทั้งหมดในงานนี้ (พร้อมรูปภาพ)"):
                for itm_idx, itm in enumerate(rec.get('items', [])):
                    is_item_checked = itm.get('checked', False)
                    chk_icon = "✅" if is_item_checked else "❌"
                    fn = itm.get('filename', '')
                    resolved_at = itm.get('resolved_at')
                    
                    c_hchk, c_hthumb, c_htext, c_hscore, c_hbtn = st.columns([0.05, 0.10, 0.50, 0.15, 0.20])
                    with c_hchk:
                        st.markdown(f"<div style='font-size: 1.1rem; padding-top: 6px;'>{chk_icon}</div>", unsafe_allow_html=True)
                    with c_hthumb:
                        if fn and os.path.exists(f"mock_database/{fn}"):
                            try:
                                st.image(f"mock_database/{fn}", width=46)
                            except:
                                st.write("🔧")
                        else:
                            st.write("🔧")
                    with c_htext:
                        resolved_badge = f'<span style="background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; font-size: 0.70rem; font-weight: 600; padding: 1px 6px; border-radius: 4px; margin-left: 6px;">✨ พบย้อนหลังเมื่อ {resolved_at}</span>' if resolved_at else ''
                        st.markdown(f"""
                        <div style="font-size: 0.92rem; font-weight: 700; color: #0F172A; display: flex; align-items: center; flex-wrap: wrap;">
                            {itm.get('name', fn)} {resolved_badge}
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px; margin-top: 2px;">
                            <span class='badge-category' style="font-size: 0.7rem;">{itm.get('category', 'General')}</span>
                            <span style="font-size: 0.78rem; color: #64748B;">{itm.get('description', '')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_hscore:
                        st.markdown(f"""
                        <div style="text-align: right; padding-top: 6px;">
                            <span class='badge-score'>★ {itm.get('score', 100)}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_hbtn:
                        if not is_item_checked:
                            st.button(
                                "✅ บันทึกว่าพบแล้ว",
                                key=f"btn_mark_found_{rec['job_id']}_{itm_idx}",
                                on_click=mark_tool_as_found,
                                args=(rec['job_id'], itm_idx),
                                use_container_width=True,
                                help="กดเมื่อตามหาเครื่องมือชิ้นนี้เจอแล้ว เพื่ออัปเดตประวัติย้อนหลัง"
                            )
                        else:
                            if resolved_at:
                                st.markdown("<div style='text-align: center; color: #059669; font-size: 0.78rem; font-weight: 600; padding-top: 8px;'>✨ พบย้อนหลังแล้ว</div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div style='text-align: center; color: #64748B; font-size: 0.78rem; padding-top: 8px;'>ตรวจพบปกติ</div>", unsafe_allow_html=True)
                    st.divider()

    # รัน Print Dialog ผ่าน hidden iframe เพียง 1 ตัว เมื่อผู้ใช้กดปุ่มพิมพ์เท่านั้น (ป้องกันเว็บค้างและเร็วทันใจ)
    if 'active_print_job' in st.session_state and st.session_state['active_print_job']:
        print_rec = st.session_state['active_print_job']
        del st.session_state['active_print_job']
        full_printable_html = generate_printable_html(print_rec)
        b64_html = base64.b64encode(full_printable_html.encode('utf-8')).decode('ascii')
        
        components.html(f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; }}</style>
        </head>
        <body>
        <script>
        (function() {{
            try {{
                var rawHtml = decodeURIComponent(escape(window.atob("{b64_html}")));
                var iframe = document.createElement('iframe');
                iframe.style.position = 'fixed';
                iframe.style.top = '-9999px';
                iframe.style.left = '-9999px';
                iframe.style.width = '0px';
                iframe.style.height = '0px';
                iframe.style.border = '0';
                document.body.appendChild(iframe);
                
                var doc = iframe.contentWindow.document;
                doc.open();
                doc.write(rawHtml);
                doc.close();
                
                iframe.contentWindow.focus();
                setTimeout(function() {{
                    iframe.contentWindow.print();
                }}, 250);
            }} catch(e) {{
                console.error(e);
            }}
        }})();
        </script>
        </body>
        </html>
        """, height=0)


# ==============================================================================
# 📥 9. VIEW 3: TRAY MANAGEMENT & SLOT INSPECTION (หน้าจัดการถาด)
# ==============================================================================
def render_tray_register():
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #E81D23; border-radius: 8px; padding: 12px; margin-bottom: 14px;">
        <p style="margin: 0; color: #0F172A; font-size: 0.9rem; font-weight: 700;">📋 ขั้นตอนการลงทะเบียน Template ถาด:</p>
        <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.84rem; line-height: 1.5;">
            1. วางเครื่องมือลงในถาดให้ครบทุกชิ้น<br>
            2. ถ่ายภาพจากมุมตั้งฉาก (Top-down) ให้เห็นถาดทั้งใบ<br>
            3. ตั้งชื่อถาด แล้วกดปุ่ม <b>⚡ สแกนหาเครื่องมือในถาด</b> เพื่อนำเข้าเช็คลิสต์
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_ctrl, col_display = st.columns([1, 1.4], gap="medium")
    opencv_img = None

    with col_ctrl:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 15px; margin-bottom: 8px;'>1. ข้อมูลถาดและภาพ</h4>", unsafe_allow_html=True)
            tray_name = st.text_input("ชื่อถาดเครื่องมือ", placeholder="เช่น ถาดเครื่องกลหนัก YA-01, ถาดไฟฟ้า EB-02", key="tray_reg_name")
            input_method = st.radio("วิธีนำเข้าภาพถาด:", ["📸 กล้อง (Camera)", "📁 อัปโหลดไฟล์ (Upload)"], horizontal=True, key="tray_reg_method")

            if input_method == "📸 กล้อง (Camera)":
                st.caption("💡 ถ่ายภาพถาดมุมตั้งฉาก ให้เห็นเครื่องมือครบทุกช่อง")
                img_file = st.camera_input("ถ่ายภาพถาดเต็ม", key="tray_reg_cam")
                if img_file:
                    opencv_img = cv2.imdecode(np.frombuffer(img_file.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            else:
                img_file = st.file_uploader("เลือกไฟล์ภาพถาด", type=['jpg', 'png', 'jpeg'], key="tray_reg_file")
                if img_file:
                    opencv_img = cv2.imdecode(np.frombuffer(img_file.getvalue(), np.uint8), cv2.IMREAD_COLOR)

    with col_display:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 15px; margin-bottom: 8px;'>2. พรีวิวภาพและจุดสแกน (SIFT Keypoints Feed)</h4>", unsafe_allow_html=True)
            
            if opencv_img is not None:
                target_scan_img, is_board_detected, board_pts = detect_and_crop_board(opencv_img)
                if is_board_detected:
                    st.success("✂️ **ตรวจพบขอบกระดาน/ถาดอัตโนมัติ**: ระบบทำการ Crop เพื่อสแกนเฉพาะเครื่องมือและตัดพื้นหลังผนังออกเรียบร้อย")
                    left_preview_img = draw_board_boundary(opencv_img, board_pts)
                    left_caption = "ภาพถ่ายถาดต้นฉบับ (ตีกรอบขอบถาด 🟢)"
                else:
                    left_preview_img = opencv_img
                    left_caption = "ภาพถ่ายถาดต้นฉบับ"

                viz_img, kp_count = visualize_tool_keypoints(target_scan_img.copy())

                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    st.image(left_preview_img, channels="BGR", caption=left_caption, use_container_width=True)
                with img_col2:
                    st.image(viz_img, channels="BGR", caption=f"จุดสแกนบนเครื่องมือ ({kp_count} จุด)", use_container_width=True)

                if isinstance(kp_count, int) and kp_count < 500:
                    st.warning(f"⚠️ จุดสแกนค่อนข้างน้อย ({kp_count} จุด) แนะนำให้เพิ่มแสงสว่างหรือขยับกล้องเข้าใกล้")

                st.divider()
                if not tray_name.strip():
                    st.warning("⚠️ กรุณากรอกชื่อถาดก่อนกดเริ่มสแกน")
                else:
                    if st.button("⚡ สแกนหาเครื่องมือในถาด", type="primary", use_container_width=True, key="tray_reg_btn"):
                        tray_id = tray_name.strip().replace(" ", "_").replace("/", "_").replace(".", "_")
                        with st.spinner(f"กำลังวิเคราะห์ตำแหน่งเครื่องมือในถาด '{tray_name}'..."):
                            tray_data = scanner.register_tray_template(target_scan_img, tray_id, tray_name.strip())

                        slots = tray_data.get('slots', [])
                        if slots:
                            st.session_state.source_type = "tray"
                            st.session_state.current_tray_name = tray_name.strip()
                            st.session_state.detected_list = []
                            for idx, slot in enumerate(slots):
                                st.session_state.detected_list.append({
                                    "filename": slot['filename'],
                                    "name": slot['name'],
                                    "category": slot['category'],
                                    "description": f"เครื่องมือในถาด '{tray_name}' (พิกัดช่อง)",
                                    "score": 100,
                                    "checked": True
                                })
                                st.session_state[f"chk_{idx}"] = True

                            st.session_state.active_view = "checklist"
                            st.rerun()
                        else:
                            st.error("❌ ไม่พบตำแหน่งเครื่องมือในภาพ กรุณาปรับแสงสว่างและลองใหม่อีกครั้ง")
            else:
                st.info("👈 กรุณากรอกชื่อถาดและถ่ายภาพ/เลือกไฟล์ภาพทางซ้าย เพื่อดูจุดสแกนและเริ่มลงทะเบียน")


def render_tray_check():
    templates = scanner.list_tray_templates()
    if not templates:
        st.info("💡 ยังไม่มี Template ถาดในระบบ กรุณาไปที่แท็บ 'ลงทะเบียนถาด' ด้านบนก่อน")
        return

    tray_options = {f"{t['tray_name']} ({t['slot_count']} ช่อง)": t['tray_id'] for t in templates}
    
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #E81D23; border-radius: 8px; padding: 12px; margin-bottom: 14px;">
        <p style="margin: 0; color: #0F172A; font-size: 0.9rem; font-weight: 700;">🔍 ขั้นตอนการตรวจสอบถาด:</p>
        <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.84rem; line-height: 1.5;">
            1. เลือกถาดที่ต้องการตรวจเช็ค<br>
            2. ถ่ายภาพถาดปัจจุบันมุมตั้งฉาก (Top-down)<br>
            3. กดปุ่ม <b>🔍 เริ่มตรวจสอบความครบถ้วนของถาด</b> เพื่อนำผลเข้าสู่เช็คลิสต์
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_ctrl, col_display = st.columns([1, 1.4], gap="medium")
    opencv_img = None

    with col_ctrl:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 15px; margin-bottom: 8px;'>1. เลือกถาดและภาพ</h4>", unsafe_allow_html=True)
            selected_label = st.selectbox("เลือกถาดที่ต้องการตรวจสอบ", options=list(tray_options.keys()), key="tray_check_select")
            selected_id = tray_options[selected_label]
            input_method = st.radio("วิธีนำเข้าภาพตรวจ:", ["📸 กล้อง (Camera)", "📁 อัปโหลดไฟล์ (Upload)"], horizontal=True, key="tray_check_method")

            if input_method == "📸 กล้อง (Camera)":
                st.caption("💡 ถ่ายภาพถาดมุมตั้งฉาก เพื่อให้ระบบเปรียบเทียบกับ Template")
                img_file = st.camera_input("ถ่ายภาพถาดปัจจุบัน", key="tray_check_cam")
                if img_file:
                    opencv_img = cv2.imdecode(np.frombuffer(img_file.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            else:
                img_file = st.file_uploader("อัปโหลดภาพถาดปัจจุบัน", type=['jpg', 'png', 'jpeg'], key="tray_check_file")
                if img_file:
                    opencv_img = cv2.imdecode(np.frombuffer(img_file.getvalue(), np.uint8), cv2.IMREAD_COLOR)

    with col_display:
        with st.container(border=True):
            st.markdown("<h4 style='font-size: 15px; margin-bottom: 8px;'>2. พรีวิวภาพและจุดสแกน (SIFT Keypoints Feed)</h4>", unsafe_allow_html=True)
            
            if opencv_img is not None:
                target_scan_img, is_board_detected, board_pts = detect_and_crop_board(opencv_img)
                if is_board_detected:
                    st.success("✂️ **ตรวจพบขอบกระดาน/ถาดอัตโนมัติ**: ระบบทำการ Crop เพื่อสแกนเฉพาะเครื่องมือและตัดพื้นหลังผนังออกเรียบร้อย")
                    left_preview_img = draw_board_boundary(opencv_img, board_pts)
                    left_caption = "ภาพถ่ายถาดปัจจุบัน (ตีกรอบขอบถาด 🟢)"
                else:
                    left_preview_img = opencv_img
                    left_caption = "ภาพถ่ายถาดปัจจุบัน"

                viz_img, kp_count = visualize_tool_keypoints(target_scan_img.copy())

                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    st.image(left_preview_img, channels="BGR", caption=left_caption, use_container_width=True)
                with img_col2:
                    st.image(viz_img, channels="BGR", caption=f"จุดสแกนบนเครื่องมือ ({kp_count} จุด)", use_container_width=True)

                if isinstance(kp_count, int) and kp_count < 500:
                    st.warning(f"⚠️ จุดสแกนค่อนข้างน้อย ({kp_count} จุด) แนะนำให้เพิ่มแสงสว่างหรือขยับกล้องเข้าใกล้")

                st.divider()
                if st.button("🔍 เริ่มตรวจสอบความครบถ้วนของถาด", type="primary", use_container_width=True, key="tray_check_btn"):
                    with st.spinner("กำลังเปรียบเทียบตำแหน่งเครื่องมือกับ Template ถาด..."):
                        results, tray_info = scanner.check_tray_slots(target_scan_img, selected_id)
                    if results is None:
                        st.error(f"เกิดข้อผิดพลาด: {tray_info}")
                    else:
                        st.session_state.tray_check_results = results
                        st.session_state.tray_check_data = tray_info
                        
                        tray_name_clean = selected_label.split(" (")[0]
                        st.session_state.source_type = "tray"
                        st.session_state.current_tray_name = tray_name_clean
                        
                        st.session_state.detected_list = []
                        for idx, r in enumerate(results):
                            is_present = (r['status'] == 'present')
                            st.session_state.detected_list.append({
                                "filename": r['filename'],
                                "name": r['name'],
                                "category": r['category'],
                                "description": r.get('description', f"ตำแหน่งช่องในถาด '{tray_name_clean}'"),
                                "score": r.get('score', 0),
                                "checked": is_present
                            })
                            st.session_state[f"chk_{idx}"] = is_present

                        st.session_state.active_view = "checklist"
                        st.rerun()
            else:
                tray_tmpl = scanner.get_tray_template(selected_id)
                if tray_tmpl:
                    t_name = tray_tmpl.get('tray_name', selected_label)
                    slots = tray_tmpl.get('slots', [])
                    img_path = tray_tmpl.get('image_path')

                    st.markdown(f"""
                    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div>
                                <span style="font-size: 0.76rem; font-weight: 700; color: #E81D23; text-transform: uppercase;">แม่แบบถาดมาตรฐาน (Master Template)</span>
                                <h4 style="margin: 2px 0 0 0; color: #0F172A; font-size: 1.05rem;">📥 {t_name}</h4>
                            </div>
                            <span style="background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; font-size: 0.76rem; font-weight: 700; padding: 3px 10px; border-radius: 20px;">
                                {len(slots)} ช่องเครื่องมือ
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if img_path and os.path.exists(img_path):
                        st.image(img_path, caption=f"🖼️ ภาพถ่ายแม่แบบถาด '{t_name}' ที่ลงทะเบียนไว้", use_container_width=True)

                    st.markdown(f"<p style='font-size: 0.86rem; font-weight: 700; color: #334155; margin: 10px 0 6px 0;'>🔧 รายการเครื่องมือมาตรฐานในถาดนี้ ({len(slots)} ชิ้น):</p>", unsafe_allow_html=True)

                    # แสดงรายการเครื่องมือมาตรฐานในถาดพร้อมภาพ Thumbnail
                    for s_idx, slot in enumerate(slots):
                        s_fn = slot.get('filename', '')
                        c_s1, c_s2, c_s3 = st.columns([0.15, 0.65, 0.20])
                        with c_s1:
                            if s_fn and os.path.exists(f"mock_database/{s_fn}"):
                                try:
                                    st.image(f"mock_database/{s_fn}", width=44)
                                except:
                                    st.write("🔧")
                            else:
                                st.write("🔧")
                        with c_s2:
                            st.markdown(f"""
                            <div style="font-size: 0.86rem; font-weight: 700; color: #0F172A;">{slot.get('name', s_fn)}</div>
                            <div style="font-size: 0.74rem; color: #64748B;"><span class='badge-category' style='font-size: 0.66rem;'>{slot.get('category', 'General')}</span> {slot.get('description', '')}</div>
                            """, unsafe_allow_html=True)
                        with c_s3:
                            st.markdown(f"<div style='text-align: right; font-size: 0.75rem; color: #059669; font-weight: 600; padding-top: 6px;'>ช่อง #{s_idx + 1}</div>", unsafe_allow_html=True)
                        st.markdown("<div style='border-bottom: 1px dashed #E2E8F0; margin: 4px 0;'></div>", unsafe_allow_html=True)

                    st.markdown("""
                    <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 10px 12px; margin-top: 12px; font-size: 0.82rem; color: #1E40AF; text-align: center;">
                        👈 <b>พร้อมตรวจเช็ค:</b> กรุณาเปิดกล้องหรืออัปโหลดภาพถาดปัจจุบันทางซ้าย เพื่อเริ่มการสแกนเปรียบเทียบ
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("👈 กรุณาเลือกถาดและถ่ายภาพ/เลือกไฟล์ภาพทางซ้าย เพื่อดูจุดสแกนและเริ่มตรวจสอบ")


def render_tray_manager():
    templates = scanner.list_tray_templates()
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #E81D23; border-radius: 8px; padding: 12px; margin-bottom: 14px;">
        <p style="margin: 0; color: #0F172A; font-size: 0.9rem; font-weight: 700;">🗂️ จัดการแม่แบบถาดเครื่องมือ (Tray Template Manager):</p>
        <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.84rem;">
            ตรวจสอบและลบแม่แบบถาดที่ไม่ใช้งานแล้วออกจากระบบ เพื่อความเป็นระเบียบเรียบร้อยของฐานข้อมูล
        </p>
    </div>
    """, unsafe_allow_html=True)

    if 'tray_deleted_msg' in st.session_state and st.session_state.tray_deleted_msg:
        st.success(f"🗑️ {st.session_state.tray_deleted_msg}")
        del st.session_state['tray_deleted_msg']

    if not templates:
        st.info("💡 ยังไม่มี Template ถาดในระบบ สามารถสร้างใหม่ได้ที่แท็บ '📝 ลงทะเบียนถาดใหม่'")
        return

    st.caption(f"พบแม่แบบถาดทั้งหมด **{len(templates)} รายการ** ในระบบ:")

    def delete_template_callback(tray_id, tray_name):
        scanner.delete_tray_template(tray_id)
        st.session_state['tray_deleted_msg'] = f"ลบแม่แบบถาด '{tray_name}' ออกจากระบบเรียบร้อยแล้ว"

    for tmpl in templates:
        tid = tmpl['tray_id']
        tname = tmpl['tray_name']
        scount = tmpl['slot_count']
        reg_at = tmpl.get('registered_at', '-')
        
        full_tmpl = scanner.get_tray_template(tid) or {}
        img_path = full_tmpl.get('image_path')
        slots = full_tmpl.get('slots', [])

        with st.container(border=True):
            col_t1, col_t2, col_t3 = st.columns([1.5, 1.2, 0.7])
            with col_t1:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <strong style="font-size: 1.05rem; color: #0F172A;">📥 {tname}</strong>
                    <span style="background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">{scount} ช่อง</span>
                </div>
                <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                    รหัสระบบ: <code>{tid}</code> | ลงทะเบียนเมื่อ: <b>{reg_at}</b>
                </div>
                """, unsafe_allow_html=True)
                
                if slots:
                    tool_names = [s.get('name', '') for s in slots[:4]]
                    tool_preview_str = ", ".join(tool_names)
                    if len(slots) > 4:
                        tool_preview_str += f" และอีก {len(slots)-4} ชิ้น"
                    st.caption(f"🔧 เครื่องมือ: {tool_preview_str}")

            with col_t2:
                if img_path and os.path.exists(img_path):
                    try:
                        st.image(img_path, width=160, caption="ภาพแม่แบบ")
                    except:
                        st.write("🖼️ ภาพแม่แบบ")
                else:
                    st.markdown("<div style='color: #94A3B8; font-size: 0.8rem; padding-top: 10px;'>ไม่มีไฟล์ภาพถ่ายแม่แบบ</div>", unsafe_allow_html=True)

            with col_t3:
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                st.button(
                    "🗑️ ลบถาดนี้",
                    key=f"btn_del_tray_{tid}",
                    on_click=delete_template_callback,
                    args=(tid, tname),
                    type="secondary",
                    use_container_width=True,
                    help="ลบ Template ถาดนี้ออกจากฐานข้อมูลอย่างถาวร"
                )


def render_tray():
    st.markdown("""
    <div style="border-left: 4px solid #E81D23; padding-left: 12px; margin-bottom: 12px;">
        <h3 style="margin: 0; color: #0F172A; font-size: 19px;">📥 จัดการและตรวจสอบถาดเครื่องมือ (Tray Template)</h3>
        <p style="margin: 2px 0 0 0; color: #64748B; font-size: 13px;">ตรวจสอบความครบถ้วนของเครื่องมือในแต่ละช่องได้อย่างรวดเร็ว</p>
    </div>
    """, unsafe_allow_html=True)

    tab_reg, tab_check, tab_manage = st.tabs(["📝 ลงทะเบียนถาดใหม่", "🔍 ตรวจสอบถาดปัจจุบัน", "🗂️ จัดการ Template ถาด"])
    with tab_reg:
        render_tray_register()
    with tab_check:
        render_tray_check()
    with tab_manage:
        render_tray_manager()


# ==============================================================================
# 🚀 10. MAIN ROUTER
# ------------------------------------------------------------------------------
# สลับการแสดงผลตาม View ที่เลือกใน Session State
# ==============================================================================
active_view = st.session_state.get('active_view', 'scan')
if active_view == 'scan':
    render_scanner()
elif active_view == 'checklist':
    render_checklist()
elif active_view == 'history':
    render_history()
else:
    render_tray()
# 🔧 Shape Scanner - ระบบสแกนรูปแบบเครื่องมือ

ระบบอัตโนมัติสำหรับจดจำและค้นหาเครื่องมือในภาพ โดยใช้เทคโนโลยี **SIFT Feature Matching** เพื่อให้ได้ความแม่นยำสูง แม้ในสภาวะแสงและมุมต่างๆ

---

## ✨ คุณสมบัติหลัก

- 🎯 **จดจำรูปแบบเครื่องมือ** - ฝึกฝนจากรูปภาพต้นแบบอัตโนมัติ
- 🔍 **ค้นหาแบบอินเวอร์เรียนต์** - ตรวจจับได้แม้เปลี่ยนขนาด มุม หรือแสง
- 🖼️ **ประมวลผลภาพด้วย Tiling** - แบ่งภาพเป็น 4 ส่วนเพื่อความแม่นยำสูง
- 📊 **ปรับแสงอัจฉริยะ** - ใช้ CLAHE เพื่อปรับความเบริคสเฉพาะส่วน
- 📈 **ระดับความการ** - คำนวณคะแนนคุณภาพสำหรับแต่ละการค้นหา
- 🎨 **วิจัลไลเซชัน** - วาดจุดลักษณะเฉพาะบนภาพ

---

## 📦 โครงสร้างโปรเจกต์

```
modelScaniTem/
├── README.md                 # ไฟล์เอกสารนี้
├── app.py                   # แอปplication Streamlit
├── debug.py                 # สคริปต์ตรวจสอบปัญหา
├── scanner_module.py        # โมดูลหลัก (ShapeScanner)
└── mock_database/           # โฟลเดอร์เก็บรูปแบบเครื่องมือต้นแบบ
    └── data.json           # ข้อมูลฐานข้อมูล
```

---

## 🚀 เริ่มต้นใช้งาน

### 1. ติดตั้ง Dependencies

```bash
pip install opencv-python numpy streamlit
```

### 2. เตรียมรูปแบบเครื่องมือ

วางรูปภาพเครื่องมือต้นแบบลงในโฟลเดอร์ `mock_database/`:
- รองรับไฟล์: `.png`, `.jpg`, `.jpeg`, `.bmp`
- พื้นหลังยิ่งสีขาวยิ่งดี (ระบบจะลบออกอัตโนมัติ)

```
mock_database/
├── hammer.png
├── screwdriver.jpg
└── wrench.bmp
```

### 3. รันแอปพลิเคชัน

```bash
streamlit run app.py
```

หรือทดสอบจากเทอร์มินัล:

```bash
python debug.py
```

---

## 📚 วิธีการใช้งาน (Usage)

### การใช้งานพื้นฐาน

```python
from scanner_module import ShapeScanner
import cv2

# 1. สร้าง Instance จากเครื่องสแกน
scanner = ShapeScanner(db_folder='mock_database')

# 2. อ่านภาพที่ต้องการสแกน
scene_image = cv2.imread('scene.jpg')

# 3. เริ่มสแกน (แบบ Tiling)
results = scanner.scan_with_tiling(scene_image, threshold=8)

# 4. แสดงผลลัพธ์
for item in results:
    print(f"✅ {item['filename']} - คะแนน: {item['score']}")
```

### ตัวเลือกพารามิเตอร์

```python
# Tiling Scan (แนะนำ - แม่นยำกว่า)
results = scanner.scan_with_tiling(
    scene_image,
    threshold=8,        # เกณฑ์ขั้นต่ำของคะแนน (ค่าเริ่มต้น: 8)
    min_area=100        # พื้นที่ขั้นต่ำ (พิกเซล)
)

# Full Image Scan (Legacy - ค้นหาแบบเต็มภาพ)
results = scanner.scan_multiple_items(
    scene_image,
    threshold=8,
    min_area=100
)
```

### วิจัลไลเซชัน

```python
# วาดจุดลักษณะเฉพาะบนภาพ
output_img, keypoint_count = scanner.visualize_keypoints(scene_image)
cv2.imshow('Keypoints', output_img)
cv2.waitKey(0)
print(f"พบจุด: {keypoint_count}")
```

---

## 🏗️ สถาปัตยกรรมและหมวดหมู่ Method

ระบบแบ่งเป็น **8 ส่วนหลัก** เพื่อให้เป็นระเบียบ:

### **SECTION 1: INITIALIZATION** - การเตรียมการ
| Method | ที่อยู่ | |
|--------|--------|---|
| `__init__()` | Constructor | ตั้งค่า SIFT และ FLANN matcher |

### **SECTION 2: TEMPLATE MANAGEMENT** - จัดการเทมเพลต
| Method | ที่อยู่ | ที่อยู่ |
|--------|--------|--------|
| `load_and_train()` | Public | โหลดรูปแบบและดึงลักษณะเฉพาะ |
| `_load_template()` | Private | ฟังก์ชันโหลดเทมเพลตเดียว |

### **SECTION 3: IMAGE PROCESSING** - ประมวลผลภาพ
| Method | ที่อยู่ | ที่อยู่ |
|--------|--------|--------|
| `_preprocess_image()` | Private | แปลงภาพและปรับแสง |
| `_apply_clahe()` | Private | ปรับแสงแบบปรับตัว (CLAHE) |
| `_create_mask()` | Private | สร้าง Mask ลบพื้นหลัง |

### **SECTION 4: FEATURE MATCHING** - จับคู่ลักษณะ
| Method | ที่อยู่ | ที่อยู่ |
|--------|--------|--------|
| `_extract_features()` | Private | ดึงลักษณะเฉพาะด้วย SIFT |
| `_match_features()` | Private | จับคู่ลักษณะด้วย FLANN |
| `_filter_good_matches()` | Private | กรองการจับคู่ที่ดี |
| `_calculate_homography()` | Private | คำนวณการแปลงเรขาคณิต |

### **SECTION 5: RESULTS PROCESSING** - ประมวลผลผลลัพธ์
| Method | ที่อยู่ | ที่อยู่ |
|--------|--------|--------|
| `_calculate_match_area()` | Private | คำนวณพื้นที่การจับคู่ |
| `_filter_results()` | Private | กรองผลตามเกณฑ์ |
| `_merge_results()` | Private | รวมผลจากหลายส่วน |

### **SECTION 6: SCANNING LOGIC (PRIVATE)** - ลอจิกการสแกน
| Method | ที่อยู่ | ที่อยู่ |
|--------|--------|--------|
| `_scan_single_image()` | Private | สแกนภาพเดียว |
| `_match_template()` | Private | จับคู่เทมเพลตเดียว |

### **SECTION 7: PUBLIC SCANNING METHODS** - สแกนสาธารณะ
| Method | ที่อยู่ | ที่อยู่ |
|--------|--------|--------|
| `scan_with_tiling()` | Public | **[MAIN]** สแกนแบบ 4 ส่วน |
| `scan_multiple_items()` | Public | สแกนเต็มภาพ (Legacy) |

### **SECTION 8: VISUALIZATION** - วิจัลไลเซชัน
| Method | ที่อยู่ | ที่อยู่ |
|--------|--------|--------|
| `visualize_keypoints()` | Public | วาดจุดลักษณะบนภาพ |

---

## ⚙️ การตั้งค่า

### SIFT Detector Parameters

```python
# ใน __init__ ของ ShapeScanner
self.sift = cv2.SIFT_create(
    contrastThreshold=0.03,  # ความไวต่อความสัมพันธ์ (ต่ำ = ไวมาก)
    edgeThreshold=10         # ลดขอบเงาที่หลอกตา
)
```

### Tiling Settings

```python
# ใน scan_with_tiling()
overlap_h = int(h * 0.1)  # Overlap 10% บนล่าง
overlap_w = int(w * 0.1)  # Overlap 10% ซ้ายขวา
```

### Feature Matching Settings

```python
# FLANN Matcher Parameters
index_params = dict(algorithm=1, trees=5)
search_params = dict(checks=50)
```

### Matching Thresholds

```python
# ใน load_and_train()
threshold_mask = 235  # ถือว่าพื้นหลังถ้า > 235 (0-255)

# ใน _filter_good_matches()
ratio_threshold = 0.7    # Lowe's ratio test: m.distance < 0.7 * n.distance

# ใน scan_with_tiling()
default_threshold = 8    # คะแนนขั้นต่ำของการจับคู่
min_area = 100          # พื้นที่ขั้นต่ำ (พิกเซล)
```

---

## 📊 ผลลัพธ์ (Output Format)

### ผลลัพธ์การสแกน

แต่ละรายการมีโครงสร้าง:

```python
{
    "filename": "hammer.png",      # ชื่อเทมเพลต
    "score": 42,                   # จำนวนจุดที่จับคู่ได้
    "area": 15234                  # พื้นที่การจับคู่ (พิกเซล)
}
```

ผลลัพธ์เรียงลำดับจากสูงไปต่ำ (Best match first)

### Template Information

เหลือรูปแบบที่จำนำ:

```python
self.templates = [
    {
        "name": "hammer.png",
        "kp": [KeyPoint, KeyPoint, ...],  # จุดลักษณะเฉพาะ
        "des": [[descriptor], ...],       # ตัวบรรยายลักษณะ
        "shape": (height, width)          # ขนาดภาพ
    },
    ...
]
```

---

## 🐛 การแก้ไขปัญหา

### ปัญหา: ไม่พบรูปแบบใดๆ

```bash
python debug.py
```

ตรวจสอบ:
- ✅ โฟลเดอร์ `mock_database/` มีอยู่หรือไม่?
- ✅ มีไฟล์รูปภาพหรือไม่?
- ✅ นามสกุล `.png`, `.jpg`, `.jpeg`, `.bmp` หรือไม่?
- ✅ พื้นหลังสีขาวหรือไม่?

### ปัญหา: คะแนนต่ำเกินไป

**วิธีแก้:**
1. ลดค่า `threshold` - `scan_with_tiling(image, threshold=5)`
2. เพิ่มจำนวนจุดในเทมเพลต - ใช้รูปของเครื่องมือเดียวกัน
3. ปรับ `contrastThreshold` เป็น 0.02 หรือ 0.01 (ไวมากขึ้น)

### ปัญหา: ความแม่นยำต่ำ (False Positives)

**วิธีแก้:**
1. เพิ่ม `threshold` - `scan_with_tiling(image, threshold=10)`
2. เพิ่ม `min_area` - `scan_with_tiling(image, min_area=150)`
3. ใช้รูปต้นแบบหลายมุม/ระยะ

---

## 🎓 ทำความเข้าใจ Algorithm

### SIFT (Scale-Invariant Feature Transform)

1. **Detection** - ค้นหาจุดสำคัญที่ไม่เปลี่ยนแปลงตามขนาด
2. **Extraction** - ดึงตัวบรรยาย (128-dimensional vector)
3. **Matching** - จับคู่ระหว่างจุดในภาพต้นแบบและฉากภาพ

### Image Tiling

ภาพขนาดใหญ่ได้รับการแบ่งเป็น 4 ส่วนพื้นที่ที่ทับซ้อนกัน:

```
┌─────────┐
│ 1   2   │
├─────────┤
│ 3   4   │
└─────────┘
```

ข้อดี:
- ↑ ความแม่นยำสำหรับเครื่องมือขนาดเล็ก
- ↑ ประสิทธิภาพการคำนวณ
- ↓ ปัญหา False Negatives

---

## 📝 ตัวอย่าง (Examples)

### ตัวอย่าง 1: สแกนจากกล้อง Webcam

```python
import cv2
from scanner_module import ShapeScanner

scanner = ShapeScanner()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    results = scanner.scan_with_tiling(frame, threshold=8)
    
    for item in results[:3]:  # แสดงเฉพาะ 3 อันดับแรก
        print(f"{item['filename']}: {item['score']}")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### ตัวอย่าง 2: วิจัลไลเซชัน

```python
import cv2
from scanner_module import ShapeScanner

scanner = ShapeScanner()
image = cv2.imread('scene.jpg')

output_img, count = scanner.visualize_keypoints(image)

cv2.imshow('Detected Keypoints', output_img)
print(f"Keypoints found: {count}")
cv2.waitKey(0)
cv2.destroyAllWindows()
```

### ตัวอย่าง 3: ทดสอบเกณฑ์ต่างๆ

```python
import cv2
from scanner_module import ShapeScanner

scanner = ShapeScanner()
scene = cv2.imread('scene.jpg')

# ทดสอบเกณฑ์หลากหลาย
for threshold in [5, 8, 10, 12]:
    print(f"\n--- threshold = {threshold} ---")
    results = scanner.scan_with_tiling(scene, threshold=threshold)
    print(f"Found: {len(results)} items")
    for r in results:
        print(f"  {r['filename']}: {r['score']}")
```

---

## 📄 ไฟล์เพิ่มเติม

### app.py
แอปพลิเคชันเว็บ **Streamlit** สำหรับ UI:
- อัปโหลด/ถ่ายรูปภาพ
- แสดงผลการสแกนสดๆ
- เช็คลิสต์แบบโต้ตอบ
- บันทึกข้อมูล JSON

### debug.py
สคริปต์ตรวจสอบและแก้ไขปัญหา:
- ตรวจสอบโฟลเดอร์และไฟล์
- ตรวจสอบนามสกุลไฟล์
- ให้คำแนะนำการแก้ไข

### mock_database/data.json
ข้อมูลเก็บรายการ:
```json
{
  "items": [
    {"id": 1, "name": "Hammer", "status": "complete"},
    ...
  ]
}
```

---

## 🔧 สิ่งที่อาจต้องปรับปรุงในอนาคต

- [ ] รองรับชนิด Detector อื่นๆ (AKAZE, ORB)
- [ ] การประมวลผลแบบ GPU
- [ ] เหมือนฐานข้อมูลแบบ Deep Learning
- [ ] CLI Tool สำหรับ batch processing
- [ ] Unit Tests
- [ ] Docker support

---

## 📞 ติดต่อและข้อเสนอแนะ

หากมีคำถามหรือข้อเสนอแนะ สามารถเปิด Issue หรือ Pull Request ได้

---

## 📄 License

โปรเจกต์นี้เป็นของส่วนตัว

---

**สร้างด้วย ❤️ ด้วย OpenCV และ SIFT**

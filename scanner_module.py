import cv2
import os
import numpy as np
import time

class ShapeScanner:
    def __init__(self, db_folder='mock_database'):
        self.db_folder = db_folder
        
        # ใช้ SIFT (SIFT_create) ที่ปรับแต่งมาเพื่อจับพื้นผิวโลหะ
        # contrastThreshold=0.03: ช่วยให้จับลายบนผิวเหล็กได้ดีขึ้น
        # edgeThreshold=10: ลดการจับขอบเงาที่หลอกตา
        self.sift = cv2.SIFT_create(contrastThreshold=0.03, edgeThreshold=10)
        
        self.templates = [] 
        self.load_and_train()

    def load_and_train(self):
        print(f"--- กำลังตรวจสอบโฟลเดอร์: {os.path.abspath(self.db_folder)} ---")
        
        if not os.path.exists(self.db_folder):
            print(f"❌ ERROR: ไม่พบโฟลเดอร์ '{self.db_folder}'")
            return

        files = [f for f in os.listdir(self.db_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        total_files = len(files)
        
        for i, file in enumerate(files):
            path = os.path.join(self.db_folder, file)
            try:
                # อ่านภาพแบบสีมาก่อน เพื่อเช็คสีขาว
                img_color = cv2.imread(path)
                if img_color is None: continue

                # 1. แปลงเป็นขาวดำเพื่อใช้งาน
                img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

                # 2. [ไม้ตาย] สร้าง Mask เพื่อลบพื้นหลังสีขาวออก
                # ถ้าพิกเซลไหนสว่างมากๆ (>235) ให้ถือว่าเป็นพื้นหลัง (สีดำใน mask)
                _, mask = cv2.threshold(img_gray, 235, 255, cv2.THRESH_BINARY_INV)
                
                # 3. ปรับแสงเฉพาะส่วนเครื่องมือ (CLAHE)
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
                img_gray = clahe.apply(img_gray)

                # 4. ส่ง Mask เข้าไปตอนหาจุด (ระบบจะหาจุดเฉพาะในพื้นที่สีดำของเครื่องมือเท่านั้น)
                kp, des = self.sift.detectAndCompute(img_gray, mask)
                
                if des is not None and len(kp) > 0:
                    self.templates.append({
                        "name": file,
                        "kp": kp,
                        "des": des,
                        "shape": img_gray.shape # เก็บขนาดภาพไว้คำนวณสเกล
                    })
                    print(f"[{i+1}/{total_files}] ✅ จดจำเนื้อเครื่องมือ: {file} ({len(kp)} จุด)")
            
            except Exception as e:
                print(f"⚠️ ข้ามไฟล์ {file}: {e}")
                continue

        print(f"--- สรุป: จำได้ {len(self.templates)} รูปแบบ ---")

    def _scan_single_image(self, img_gray, threshold):
        """ ฟังก์ชันย่อยสำหรับสแกนภาพ 1 ภาพ (ใช้ภายใน Class) """
        found_in_chunk = []
        
        # ปรับแสง
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        img_gray = clahe.apply(img_gray)

        kp_scene, des_scene = self.sift.detectAndCompute(img_gray, None)
        if des_scene is None: return []

        index_params = dict(algorithm=1, trees=5) 
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)

        for item in self.templates:
            try:
                if item['des'] is None or len(item['des']) < 2: continue
                
                matches = flann.knnMatch(item['des'], des_scene, k=2)
                good_matches = []
                for m, n in matches:
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
                
                # ลดเกณฑ์ขั้นต่ำลงนิดหน่อยเพราะแบ่งภาพย่อยแล้ว
                if len(good_matches) < 8: continue 

                src_pts = np.float32([ item['kp'][m.queryIdx].pt for m in good_matches ]).reshape(-1,1,2)
                dst_pts = np.float32([ kp_scene[m.trainIdx].pt for m in good_matches ]).reshape(-1,1,2)

                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None:
                    matchesMask = mask.ravel().tolist()
                    real_score = sum(matchesMask)
                    
                    # Area check
                    h, w = item['shape']
                    pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
                    dst = cv2.perspectiveTransform(pts, M)
                    area = cv2.contourArea(np.int32(dst))
                    
                    # ลด Area ขั้นต่ำเพราะภาพย่อยเล็กลง (เหลือ 100)
                    if real_score >= threshold and area > 100: 
                        found_in_chunk.append({
                            "filename": item['name'],
                            "score": int(real_score)
                        })
            except: continue
            
        return found_in_chunk

    def scan_with_tiling(self, scene_image, threshold=8):
        """ 
        [ฟังก์ชันพระเอก] แบ่งภาพเป็น 4 ส่วนแล้วสแกน (Image Tiling)
        """
        final_results = {} # ใช้ Dict เพื่อกันซ้ำ (Key=Filename)
        
        gray_scene = cv2.cvtColor(scene_image, cv2.COLOR_BGR2GRAY)
        h, w = gray_scene.shape
        
        # กำหนดจุดกึ่งกลาง และระยะ Overlap (10%)
        mid_h, mid_w = h // 2, w // 2
        overlap_h = int(h * 0.1)
        overlap_w = int(w * 0.1)

        # นิยาม 4 พื้นที่ (ROI: Region of Interest)
        rois = [
            gray_scene[0:mid_h+overlap_h, 0:mid_w+overlap_w],       # ซ้ายบน
            gray_scene[0:mid_h+overlap_h, mid_w-overlap_w:w],       # ขวาบน
            gray_scene[mid_h-overlap_h:h, 0:mid_w+overlap_w],       # ซ้ายล่าง
            gray_scene[mid_h-overlap_h:h, mid_w-overlap_w:w]        # ขวาล่าง
        ]
        
        print(f"--- เริ่มสแกนแบบ Tiling (4 ส่วน) ---")

        for i, roi in enumerate(rois):
            # สแกนทีละส่วน
            results = self._scan_single_image(roi, threshold)
            print(f"   ส่วนที่ {i+1}: เจอ {len(results)} รายการ")
            
            # รวมผลลัพธ์ (ถ้าเจอซ้ำ ให้เอาคะแนนที่มากกว่า)
            for res in results:
                name = res['filename']
                score = res['score']
                
                if name in final_results:
                    # ถ้าเคยเจอแล้ว ให้บันทึกคะแนนสูงสุด
                    if score > final_results[name]['score']:
                        final_results[name]['score'] = score
                else:
                    final_results[name] = res

        # แปลงกลับเป็น List และเรียงคะแนน
        return sorted(list(final_results.values()), key=lambda x: x['score'], reverse=True)

    def visualize_keypoints(self, image):
        output_img = image.copy()
        gray = cv2.cvtColor(output_img, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        kp, _ = self.sift.detectAndCompute(gray, None)
        
        # วาดกากบาทเล็กๆ สีแดง
        for k in kp:
            x, y = int(k.pt[0]), int(k.pt[1])
            cv2.drawMarker(output_img, (x, y), (0, 0, 255), markerType=cv2.MARKER_CROSS, markerSize=5, thickness=1)
        
        return output_img, len(kp)
    
    # เก็บฟังก์ชันเดิมไว้เผื่ออยากสลับใช้ (Optional)
    def scan_multiple_items(self, scene_image, threshold=8):
        """ 
        (Legacy) ค้นหาแบบเต็มภาพ ไม่แบ่งส่วน
        """
        gray_scene = cv2.cvtColor(scene_image, cv2.COLOR_BGR2GRAY)
        return self._scan_single_image(gray_scene, threshold)
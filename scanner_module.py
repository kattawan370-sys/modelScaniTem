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
                # ถ้าพิกเซลไหนสว่างมากๆ (>230) ให้ถือว่าเป็นพื้นหลัง (สีดำใน mask)
                # พิกเซลที่เป็นตัวเครื่องมือจะเป็นสีขาวใน mask
                _, mask = cv2.threshold(img_gray, 230, 255, cv2.THRESH_BINARY_INV)
                
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

    def scan_multiple_items(self, scene_image, threshold=8):
        """ 
        ค้นหาวัตถุด้วย SIFT + FLANN + RANSAC
        """
        found_items = []
        gray_scene = cv2.cvtColor(scene_image, cv2.COLOR_BGR2GRAY)

        # ปรับแสงภาพบอร์ด (สำคัญมาก เพราะบอร์ดมันมืดกว่ารูปต้นฉบับ)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        gray_scene = clahe.apply(gray_scene)

        # หาจุดในภาพบอร์ด (Scene)
        kp_scene, des_scene = self.sift.detectAndCompute(gray_scene, None)
        
        if des_scene is None: return []

        # ใช้ FLANN Matcher (ตั้งค่าสำหรับ SIFT)
        index_params = dict(algorithm=1, trees=5) # KD-Tree
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)

        for item in self.templates:
            try:
                if item['des'] is None or len(item['des']) < 2: continue

                # จับคู่จุด (KNN)
                matches = flann.knnMatch(item['des'], des_scene, k=2)
                
                good_matches = []
                for m, n in matches:
                    # Ratio Test 0.7 (มาตรฐาน SIFT)
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
                
                # ต้องเจอจุดที่เหมือนกันอย่างน้อย 10 จุด
                if len(good_matches) < 10: continue

                # --- RANSAC: ตรวจสอบรูปทรง ---
                src_pts = np.float32([ item['kp'][m.queryIdx].pt for m in good_matches ]).reshape(-1,1,2)
                dst_pts = np.float32([ kp_scene[m.trainIdx].pt for m in good_matches ]).reshape(-1,1,2)

                # หาความสัมพันธ์ของตำแหน่ง (Homography)
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None:
                    matchesMask = mask.ravel().tolist()
                    real_score = sum(matchesMask) # คะแนนจริง (Inliers)
                    
                    # ตรวจสอบความสมเหตุสมผลของรูปทรง (ป้องกันการจับมั่วแบบเจอจุดเล็กๆแล้วขยายเต็มจอ)
                    h, w = item['shape']
                    pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
                    dst = cv2.perspectiveTransform(pts, M)
                    
                    # คำนวณพื้นที่ของกรอบสี่เหลี่ยมที่เจอ
                    area = cv2.contourArea(np.int32(dst))
                    
                    # กรอง: ถ้าพื้นที่เล็กเกินไป (Noise) หรือใหญ่เกินไป (Error) ให้ตัดทิ้ง
                    # (ปรับค่า 500 ตามขนาดภาพจริงของคุณ)
                    if real_score >= threshold and area > 500:
                        found_items.append({
                            "filename": item['name'],
                            "score": real_score
                        })
            except Exception:
                continue
        
        found_items.sort(key=lambda x: x['score'], reverse=True)
        return found_items

    def visualize_keypoints(self, image):
        output_img = image.copy()
        gray = cv2.cvtColor(output_img, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        kp, _ = self.sift.detectAndCompute(gray, None)
        
        # วาดจุดเป็นเป้าเล็งเล็กๆ สีแดง
        for k in kp:
            x, y = int(k.pt[0]), int(k.pt[1])
            # วาดกากบาทเล็กๆ แทนวงกลม เพื่อความแม่นยำในการมองเห็น
            cv2.drawMarker(output_img, (x, y), (0, 0, 255), markerType=cv2.MARKER_CROSS, markerSize=5, thickness=1)
        
        return output_img, len(kp)
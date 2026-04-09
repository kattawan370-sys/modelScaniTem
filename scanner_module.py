import cv2
import os
import numpy as np
import time

class ShapeScanner:
    """
    ระบบสแกนรูปแบบเครื่องมือโดยใช้ SIFT Feature Matching
    
    Methods แบ่งเป็นหมวดหมู่:
    - Initialization: __init__
    - Template Management: load_and_train
    - Image Processing: _preprocess_image, _apply_clahe, _create_mask
    - Feature Matching: _extract_features, _match_features, _calculate_homography
    - Results Processing: _calculate_match_area, _filter_results
    - Public Scanning: scan_with_tiling, scan_multiple_items
    - Visualization: visualize_keypoints
    """
    
    # ===== SECTION 1: INITIALIZATION =====
    def __init__(self, db_folder='mock_database'):
        self.db_folder = db_folder
        
        # ใช้ SIFT (SIFT_create) ที่ปรับแต่งมาเพื่อจับพื้นผิวโลหะ
        # contrastThreshold=0.03: ช่วยให้จับลายบนผิวเหล็กได้ดีขึ้น
        # edgeThreshold=10: ลดการจับขอบเงาที่หลอกตา
        self.sift = cv2.SIFT_create(contrastThreshold=0.03, edgeThreshold=10)
        
        # ตั้งค่า FLANN Matcher สำหรับการจับคู่เร็ว
        self.index_params = dict(algorithm=1, trees=5)
        self.search_params = dict(checks=50)
        
        self.templates = [] 
        self.load_and_train()

    # ===== SECTION 2: TEMPLATE MANAGEMENT =====
    def load_and_train(self):
        """โหลดรูปแบบเครื่องมือจากโฟลเดอร์และดึงลักษณะเฉพาะ"""
        print(f"--- กำลังตรวจสอบโฟลเดอร์: {os.path.abspath(self.db_folder)} ---")
        
        if not os.path.exists(self.db_folder):
            print(f"❌ ERROR: ไม่พบโฟลเดอร์ '{self.db_folder}'")
            return

        files = [f for f in os.listdir(self.db_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        total_files = len(files)
        
        for i, file in enumerate(files):
            path = os.path.join(self.db_folder, file)
            self._load_template(path, file, i, total_files)

        print(f"--- สรุป: จำได้ {len(self.templates)} รูปแบบ ---")

    def _load_template(self, path, filename, index, total):
        """โหลดเทมเพลตเดียว และดึงลักษณะเฉพาะ"""
        try:
            img_color = cv2.imread(path)
            if img_color is None:
                return

            # ประมวลผลภาพ
            img_gray = self._preprocess_image(img_color)
            mask = self._create_mask(img_gray)

            # ดึงลักษณะเฉพาะ (Features)
            kp, des = self.sift.detectAndCompute(img_gray, mask)
            
            if des is not None and len(kp) > 0:
                self.templates.append({
                    "name": filename,
                    "kp": kp,
                    "des": des,
                    "shape": img_gray.shape
                })
                print(f"[{index+1}/{total}] ✅ จดจำเนื้อเครื่องมือ: {filename} ({len(kp)} จุด)")
        
        except Exception as e:
            print(f"⚠️ ข้ามไฟล์ {filename}: {e}")
    
    # ===== SECTION 3: IMAGE PROCESSING =====
    def _preprocess_image(self, img_color):
        """แปลงภาพสีเป็นภาพขาวดำและปรับแสง"""
        img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
        img_gray = self._apply_clahe(img_gray)
        return img_gray
    
    def _apply_clahe(self, img_gray):
        """ปรับแสงของภาพขาวดำ (Contrast Limited Adaptive Histogram Equalization)"""
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        return clahe.apply(img_gray)
    
    def _create_mask(self, img_gray):
        """สร้าง Mask เพื่อลบพื้นหลังสีขาว"""
        # ถ้าพิกเซลไหนสว่างมากๆ (>235) ให้ถือว่าเป็นพื้นหลัง (สีดำใน mask)
        _, mask = cv2.threshold(img_gray, 235, 255, cv2.THRESH_BINARY_INV)
        return mask
    
    # ===== SECTION 4: FEATURE MATCHING =====
    def _extract_features(self, img_gray, mask=None):
        """ดึงลักษณะเฉพาะจากภาพ"""
        kp, des = self.sift.detectAndCompute(img_gray, mask)
        return kp, des
    
    def _match_features(self, template_des, scene_des):
        """จับคู่ลักษณะระหว่างเทมเพลตและฉากภาพ"""
        flann = cv2.FlannBasedMatcher(self.index_params, self.search_params)
        
        if template_des is None or scene_des is None or len(template_des) < 2:
            return []
        
        matches = flann.knnMatch(template_des, scene_des, k=2)
        good_matches = self._filter_good_matches(matches)
        return good_matches
    
    def _filter_good_matches(self, matches):
        """กรองการจับคู่ที่ดี (Lowe's ratio test)"""
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
        return good_matches
    
    def _calculate_homography(self, template_kp, scene_kp, good_matches):
        """คำนวณ Homography Matrix จากการจับคู่ที่ดี"""
        if len(good_matches) < 8:
            return None, None, 0
        
        try:
            src_pts = np.float32([template_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([scene_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            if M is not None:
                matchesMask = mask.ravel().tolist()
                real_score = sum(matchesMask)
                return M, mask, real_score
        
        except Exception:
            pass
        
        return None, None, 0
    
    # ===== SECTION 5: RESULTS PROCESSING =====
    def _calculate_match_area(self, template_shape, homography_matrix):
        """คำนวณพื้นที่การจับคู่"""
        h, w = template_shape
        pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
        
        try:
            dst = cv2.perspectiveTransform(pts, homography_matrix)
            area = cv2.contourArea(np.int32(dst))
            return area
        except:
            return 0
    
    def _filter_results(self, found_in_chunk, threshold, min_area=100):
        """กรองผลลัพธ์ตามเกณฑ์"""
        filtered = []
        for item in found_in_chunk:
            if item["score"] >= threshold and item.get("area", 0) > min_area:
                filtered.append(item)
        return filtered
    
    def _merge_results(self, all_results):
        """รวมผลลัพธ์จากหลายส่วน และเก็บคะแนนสูงสุด"""
        final_results = {}
        for res in all_results:
            name = res['filename']
            score = res['score']
            if name not in final_results or score > final_results[name]['score']:
                final_results[name] = res
        return sorted(list(final_results.values()), key=lambda x: x['score'], reverse=True)

    # ===== SECTION 6: SCANNING LOGIC (PRIVATE) =====
    def _scan_single_image(self, img_gray, threshold, min_area=100):
        """scanning ภาพ 1 ภาพ (ใช้ภายใน Class)"""
        found_in_chunk = []
        
        # ปรับแสง
        img_gray = self._apply_clahe(img_gray)

        # ดึงลักษณะเฉพาะจากฉากภาพ
        kp_scene, des_scene = self._extract_features(img_gray, mask=None)
        if des_scene is None:
            return []

        # จับคู่กับแต่ละเทมเพลต
        for item in self.templates:
            found_item = self._match_template(item, kp_scene, des_scene, threshold, min_area)
            if found_item:
                found_in_chunk.append(found_item)
        
        return found_in_chunk
    
    def _match_template(self, template, kp_scene, des_scene, threshold, min_area):
        """จับคู่เทมเพลตเดียวกับฉากภาพ"""
        try:
            # จับคู่ลักษณะ
            good_matches = self._match_features(template['des'], des_scene)
            if len(good_matches) < 8:
                return None
            
            # คำนวณ Homography
            M, mask, real_score = self._calculate_homography(
                template['kp'], kp_scene, good_matches
            )
            
            if M is None or real_score < threshold:
                return None
            
            # ตรวจสอบพื้นที่
            area = self._calculate_match_area(template['shape'], M)
            if area <= min_area:
                return None
            
            return {
                "filename": template['name'],
                "score": int(real_score),
                "area": int(area)
            }
        
        except Exception:
            return None

    # ===== SECTION 7: PUBLIC SCANNING METHODS =====
    def scan_with_tiling(self, scene_image, threshold=8, min_area=100):
        """ 
        [Main Method] แบ่งภาพเป็น 4 ส่วนแล้วสแกน (Image Tiling)
        
        Args:
            scene_image: ภาพฉากที่จะสแกน (BGR)
            threshold: เกณฑ์ขั้นต่ำของคะแนนการจับคู่
            min_area: พื้นที่ขั้นต่ำของการจับคู่
        
        Returns:
            List of matched items sorted by score (descending)
        """
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
        
        all_results = []
        for i, roi in enumerate(rois):
            results = self._scan_single_image(roi, threshold, min_area)
            print(f"   ส่วนที่ {i+1}: เจอ {len(results)} รายการ")
            all_results.extend(results)
        
        # รวมและกรองผลลัพธ์
        return self._merge_results(all_results)

    def scan_multiple_items(self, scene_image, threshold=8, min_area=100):
        """ 
        (Legacy) ค้นหาแบบเต็มภาพ ไม่แบ่งส่วน
        
        Args:
            scene_image: ภาพฉากที่จะสแกน (BGR)
            threshold: เกณฑ์ขั้นต่ำของคะแนนการจับคู่
            min_area: พื้นที่ขั้นต่ำของการจับคู่
        
        Returns:
            List of matched items sorted by score (descending)
        """
        gray_scene = cv2.cvtColor(scene_image, cv2.COLOR_BGR2GRAY)
        results = self._scan_single_image(gray_scene, threshold, min_area)
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    # ===== SECTION 8: VISUALIZATION =====
    def visualize_keypoints(self, image):
        """
        วาดจุดลักษณะเฉพาะบนภาพ
        
        Returns:
            Tuple: (ภาพวาด, จำนวนจุด)
        """
        output_img = image.copy()
        gray = cv2.cvtColor(output_img, cv2.COLOR_BGR2GRAY)
        
        gray = self._apply_clahe(gray)
        kp, _ = self._extract_features(gray, mask=None)
        
        # วาดกากบาทเล็กๆ สีแดง
        for k in kp:
            x, y = int(k.pt[0]), int(k.pt[1])
            cv2.drawMarker(output_img, (x, y), (0, 0, 255), 
                          markerType=cv2.MARKER_CROSS, markerSize=5, thickness=1)
        
        return output_img, len(kp)
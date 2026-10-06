"""
YOLOv8 Tool Scanner & Tray Verification Engine.
Supports:
Part 1: Scanning individual tools placed freely or aligned (Object Detection).
Part 2: Tray block verification (Checking tool completeness and correct placement in slots).
"""
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# Check if ultralytics is available
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    logger.warning("ultralytics is not installed. YOLO inference will run in simulation/fallback mode.")


class YOLOToolScanner:
    """
    Core detection engine utilizing YOLOv8 and Tray Slot Verification logic.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self.class_names: Dict[int, str] = {}
        if model_path and ULTRALYTICS_AVAILABLE:
            self.load_model(model_path)

    def load_model(self, model_path: str) -> bool:
        """Loads YOLO weights (.pt file)."""
        if not ULTRALYTICS_AVAILABLE:
            logger.error("Ultralytics not installed.")
            return False
        
        path = Path(model_path)
        if not path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False

        try:
            self.model = YOLO(str(path))
            self.model_path = str(path)
            self.class_names = self.model.names if hasattr(self.model, "names") else {}
            logger.info(f"Loaded YOLO model: {model_path} with {len(self.class_names)} classes.")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    @classmethod
    def load_active_model_from_db(cls) -> "YOLOToolScanner":
        """Factory method to load the currently active model registered in PostgreSQL."""
        try:
            from db import get_db
            from models_db import TrainedModel

            with get_db() as db:
                active = db.query(TrainedModel).filter(TrainedModel.is_active == True).first()
                if active and Path(active.model_path).exists():
                    return cls(active.model_path)
        except Exception as e:
            logger.warning(f"Could not load active model from DB: {e}")
        
        return cls()

    # =========================================================================
    # PART 1: Object Detection (Tools placed freely or in rows)
    # =========================================================================
    def detect_tools(
        self,
        image: np.ndarray,
        conf_threshold: float = 0.40,
        iou_threshold: float = 0.45
    ) -> List[Dict[str, Any]]:
        """
        Part 1: Detects tools in the image.
        Returns a list of detected objects:
        [
            {
                "class_id": int,
                "class_name": str,
                "confidence": float,
                "bbox": [x1, y1, x2, y2],  # absolute pixel coordinates
                "bbox_norm": [x1_norm, y1_norm, x2_norm, y2_norm],
                "center": (cx, cy)
            },
            ...
        ]
        """
        if self.model is None:
            return []

        h, w = image.shape[:2]
        results = self.model.predict(
            source=image,
            conf=conf_threshold,
            iou=iou_threshold,
            verbose=False
        )

        detected_items = []
        if not results:
            return detected_items

        result = results[0]
        boxes = result.boxes

        if boxes is not None:
            for box in boxes:
                coords = box.xyxy[0].cpu().numpy()  # x1, y1, x2, y2
                x1, y1, x2, y2 = float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = self.class_names.get(cls_id, f"Class_{cls_id}")

                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0

                detected_items.append({
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": round(conf, 3),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "bbox_norm": [
                        round(x1 / w, 4),
                        round(y1 / h, 4),
                        round(x2 / w, 4),
                        round(y2 / h, 4)
                    ],
                    "center": (int(cx), int(cy))
                })

        return detected_items

    # =========================================================================
    # PART 2: Tray Verification (Check slot completeness and item correctness)
    # =========================================================================
    def verify_tray(
        self,
        image: np.ndarray,
        tray_template: Dict[str, Any],
        conf_threshold: float = 0.40,
        iou_threshold: float = 0.45,
        slot_overlap_threshold: float = 0.25
    ) -> Dict[str, Any]:
        """
        Part 2: Checks if tools are complete and placed correctly in each slot of the tray.
        Args:
            image: Image containing the tray
            tray_template: Template dictionary with 'slots' definition
        Returns:
            Verification summary including present, missing, correct, misplaced items.
        """
        h, w = image.shape[:2]
        detections = self.detect_tools(image, conf_threshold, iou_threshold)

        slots = tray_template.get("slots", [])
        slot_results = []
        matched_detection_indices = set()

        # Check each slot against detections
        for slot in slots:
            slot_num = slot.get("slot_number", 0)
            expected_name = slot.get("item_name") or slot.get("name", f"Slot {slot_num}")
            expected_code = slot.get("item_code") or slot.get("code", "")
            
            # Slot bounding box [x1_norm, y1_norm, x2_norm, y2_norm]
            bbox_norm = slot.get("bbox_norm") or [
                slot.get("bbox_x1_norm", 0.0),
                slot.get("bbox_y1_norm", 0.0),
                slot.get("bbox_x2_norm", 1.0),
                slot.get("bbox_y2_norm", 1.0)
            ]

            slot_x1 = int(bbox_norm[0] * w)
            slot_y1 = int(bbox_norm[1] * h)
            slot_x2 = int(bbox_norm[2] * w)
            slot_y2 = int(bbox_norm[3] * h)
            slot_area = max(1, (slot_x2 - slot_x1) * (slot_y2 - slot_y1))

            # Find best overlapping detection
            best_det = None
            best_det_idx = -1
            best_iou = 0.0

            for idx, det in enumerate(detections):
                if idx in matched_detection_indices:
                    continue

                dx1, dy1, dx2, dy2 = det["bbox"]
                # Intersection
                ix1 = max(slot_x1, dx1)
                iy1 = max(slot_y1, dy1)
                ix2 = min(slot_x2, dx2)
                iy2 = min(slot_y2, dy2)

                iw = max(0, ix2 - ix1)
                ih = max(0, iy2 - iy1)
                intersection = iw * ih

                overlap_ratio = intersection / slot_area
                if overlap_ratio > slot_overlap_threshold and overlap_ratio > best_iou:
                    best_iou = overlap_ratio
                    best_det = det
                    best_det_idx = idx

            # Determine slot status
            if best_det is not None:
                matched_detection_indices.add(best_det_idx)
                detected_name = best_det["class_name"]
                
                # Check if item matches expected item
                is_correct = (
                    expected_code.lower() in detected_name.lower() or
                    detected_name.lower() in expected_name.lower() or
                    expected_name.lower() in detected_name.lower()
                )

                status = "correct" if is_correct else "wrong_item"
                slot_results.append({
                    "slot_number": slot_num,
                    "expected_name": expected_name,
                    "expected_code": expected_code,
                    "status": status,
                    "detected_item": detected_name,
                    "confidence": best_det["confidence"],
                    "slot_bbox": [slot_x1, slot_y1, slot_x2, slot_y2],
                    "det_bbox": best_det["bbox"],
                })
            else:
                # No tool detected in this slot
                slot_results.append({
                    "slot_number": slot_num,
                    "expected_name": expected_name,
                    "expected_code": expected_code,
                    "status": "missing",
                    "detected_item": None,
                    "confidence": 0.0,
                    "slot_bbox": [slot_x1, slot_y1, slot_x2, slot_y2],
                    "det_bbox": None,
                })

        # Calculate summary statistics
        total_slots = len(slots)
        correct_count = sum(1 for s in slot_results if s["status"] == "correct")
        missing_count = sum(1 for s in slot_results if s["status"] == "missing")
        wrong_count = sum(1 for s in slot_results if s["status"] == "wrong_item")

        is_complete = (missing_count == 0 and wrong_count == 0)

        return {
            "is_complete": is_complete,
            "total_slots": total_slots,
            "correct_count": correct_count,
            "missing_count": missing_count,
            "wrong_count": wrong_count,
            "slot_results": slot_results,
            "all_detections": detections,
            "unmatched_detections": [
                det for idx, det in enumerate(detections) if idx not in matched_detection_indices
            ]
        }

    # =========================================================================
    # Visualizations
    # =========================================================================
    def draw_detections(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Draws bounding boxes and labels for general object detections."""
        annotated = image.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cls_name = det["class_name"]
            conf = det["confidence"]

            # Draw Box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 128), 2)

            # Draw Label badge
            label_text = f"{cls_name} ({conf:.0%})"
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 6, y1), (0, 255, 128), -1)
            cv2.putText(
                annotated,
                label_text,
                (x1 + 3, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )

        return annotated

    def draw_tray_verification(
        self,
        image: np.ndarray,
        verification_result: Dict[str, Any]
    ) -> np.ndarray:
        """Draws color-coded verification results on tray slots: Green (OK), Red (Missing), Orange (Wrong)."""
        annotated = image.copy()
        for slot in verification_result.get("slot_results", []):
            x1, y1, x2, y2 = slot["slot_bbox"]
            status = slot["status"]
            slot_num = slot["slot_number"]
            name = slot["expected_name"]

            if status == "correct":
                color = (0, 220, 0)      # Green
                status_th = "ครบ/ถูกต้อง"
            elif status == "missing":
                color = (0, 0, 255)      # Red
                status_th = "ขาดหาย"
            else:
                color = (0, 165, 255)    # Orange
                status_th = f"ผิดช่อง ({slot['detected_item']})"

            # Draw Slot rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Draw Status badge
            badge_text = f"#{slot_num}: {status_th}"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 6, y1), color, -1)
            cv2.putText(
                annotated,
                badge_text,
                (x1 + 3, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return annotated

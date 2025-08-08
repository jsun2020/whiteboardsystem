import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ExifTags
import os
from typing import Tuple, Optional, List

class ImageProcessor:
    def __init__(self):
        self.max_width = 1920
        self.max_height = 1920
    
    def enhance_whiteboard(self, image_path: str) -> str:
        """
        Enhance whiteboard image for better OCR results
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Apply enhancement pipeline
            enhanced = self._enhancement_pipeline(img)
            
            # Save enhanced image
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            enhanced_path = os.path.join(
                os.path.dirname(image_path), 
                f"{base_name}_enhanced.jpg"
            )
            
            cv2.imwrite(enhanced_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])
            return enhanced_path
            
        except Exception as e:
            print(f"Enhancement failed: {e}")
            return image_path  # Return original if enhancement fails
    
    def _enhancement_pipeline(self, img: np.ndarray) -> np.ndarray:
        """
        Complete enhancement pipeline for whiteboard images
        """
        # Step 1: Resize if too large
        img = self._resize_image(img)
        
        # Step 2: Correct perspective if needed
        img = self._correct_perspective(img)
        
        # Step 3: Improve brightness and contrast
        img = self._enhance_contrast(img)
        
        # Step 4: Remove shadows
        img = self._remove_shadows(img)
        
        # Step 5: Sharpen text
        img = self._sharpen_image(img)
        
        # Step 6: Reduce noise
        img = self._reduce_noise(img)
        
        return img
    
    def _resize_image(self, img: np.ndarray) -> np.ndarray:
        """
        Resize image to manageable size while maintaining aspect ratio
        """
        height, width = img.shape[:2]
        
        if width > self.max_width or height > self.max_height:
            # Calculate scaling factor
            scale = min(self.max_width / width, self.max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return img
    
    def _correct_perspective(self, img: np.ndarray) -> np.ndarray:
        """
        Attempt to correct perspective distortion
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Find edges
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find largest contour (likely the whiteboard)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                # If we found a quadrilateral, apply perspective correction
                if len(approx) == 4:
                    return self._apply_perspective_transform(img, approx)
            
        except Exception:
            pass  # If perspective correction fails, return original
        
        return img
    
    def _apply_perspective_transform(self, img: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """
        Apply perspective transformation to correct skewed whiteboard
        """
        try:
            # Order corners: top-left, top-right, bottom-right, bottom-left
            corners = corners.reshape(4, 2)
            
            # Calculate distances to order corners
            center = np.mean(corners, axis=0)
            
            def angle_from_center(point):
                return np.arctan2(point[1] - center[1], point[0] - center[0])
            
            corners = sorted(corners, key=angle_from_center)
            
            # Calculate dimensions of the corrected image
            width1 = np.sqrt(((corners[0][0] - corners[1][0]) ** 2) + ((corners[0][1] - corners[1][1]) ** 2))
            width2 = np.sqrt(((corners[2][0] - corners[3][0]) ** 2) + ((corners[2][1] - corners[3][1]) ** 2))
            width = max(int(width1), int(width2))
            
            height1 = np.sqrt(((corners[0][0] - corners[3][0]) ** 2) + ((corners[0][1] - corners[3][1]) ** 2))
            height2 = np.sqrt(((corners[1][0] - corners[2][0]) ** 2) + ((corners[1][1] - corners[2][1]) ** 2))
            height = max(int(height1), int(height2))
            
            # Define destination points
            dst_corners = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype=np.float32)
            
            # Calculate perspective transformation matrix
            matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst_corners)
            
            # Apply transformation
            corrected = cv2.warpPerspective(img, matrix, (width, height))
            return corrected
            
        except Exception:
            return img
    
    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Enhance contrast and brightness
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def _remove_shadows(self, img: np.ndarray) -> np.ndarray:
        """
        Remove shadows from whiteboard
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Create background model using morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
            background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Smooth the background
            background = cv2.medianBlur(background, 19)
            
            # Normalize the image
            normalized = cv2.divide(gray, background, scale=255)
            
            # Convert back to color
            enhanced = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
            
            return enhanced
            
        except Exception:
            return img
    
    def _sharpen_image(self, img: np.ndarray) -> np.ndarray:
        """
        Sharpen the image to enhance text readability
        """
        # Define sharpening kernel
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        
        # Apply sharpening
        sharpened = cv2.filter2D(img, -1, kernel)
        
        # Blend with original (50% each)
        result = cv2.addWeighted(img, 0.5, sharpened, 0.5, 0)
        
        return result
    
    def _reduce_noise(self, img: np.ndarray) -> np.ndarray:
        """
        Reduce noise while preserving text
        """
        # Use bilateral filter to reduce noise while keeping edges sharp
        denoised = cv2.bilateralFilter(img, 9, 75, 75)
        
        return denoised
    
    def segment_regions(self, img: np.ndarray) -> dict:
        """
        Segment image into different regions (text, diagrams, tables)
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Find contours
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            regions = {
                'text_regions': [],
                'diagram_regions': [],
                'table_regions': []
            }
            
            for contour in contours:
                # Calculate contour properties
                area = cv2.contourArea(contour)
                if area < 100:  # Skip small regions
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                # Classify region based on properties
                if aspect_ratio > 3:  # Likely text line
                    regions['text_regions'].append((x, y, w, h))
                elif 0.8 < aspect_ratio < 1.2 and area > 1000:  # Square-ish, large
                    regions['diagram_regions'].append((x, y, w, h))
                elif self._is_table_region(gray[y:y+h, x:x+w]):
                    regions['table_regions'].append((x, y, w, h))
                else:
                    regions['text_regions'].append((x, y, w, h))
            
            return regions
            
        except Exception as e:
            print(f"Region segmentation failed: {e}")
            return {
                'text_regions': [],
                'diagram_regions': [],
                'table_regions': []
            }
    
    def _is_table_region(self, region: np.ndarray) -> bool:
        """
        Detect if a region contains a table structure
        """
        try:
            # Look for grid patterns (horizontal and vertical lines)
            edges = cv2.Canny(region, 50, 150)
            
            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
            
            # Count line intersections
            grid = cv2.bitwise_and(horizontal_lines, vertical_lines)
            intersections = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
            
            # If we have multiple intersections, it's likely a table
            return len(intersections) >= 4
            
        except Exception:
            return False
    
    def preprocess_for_ocr(self, image_path: str) -> str:
        """
        Preprocess image specifically for OCR
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save processed image
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            ocr_path = os.path.join(
                os.path.dirname(image_path),
                f"{base_name}_ocr.jpg"
            )
            
            cv2.imwrite(ocr_path, binary)
            return ocr_path
            
        except Exception as e:
            print(f"OCR preprocessing failed: {e}")
            return image_path
    
    def fix_image_orientation(self, image_path: str) -> str:
        """
        Fix image orientation based on EXIF data
        """
        try:
            with Image.open(image_path) as img:
                # Check for EXIF orientation
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                
                exif = img._getexif()
                if exif is not None:
                    orientation_value = exif.get(orientation)
                    
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
                
                # Save corrected image
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                corrected_path = os.path.join(
                    os.path.dirname(image_path),
                    f"{base_name}_corrected.jpg"
                )
                
                img.save(corrected_path, 'JPEG', quality=95)
                return corrected_path
                
        except Exception as e:
            print(f"Orientation correction failed: {e}")
            return image_path
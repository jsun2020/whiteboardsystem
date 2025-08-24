from PIL import Image, ImageEnhance, ImageFilter, ExifTags
import os
from typing import Optional

class ImageProcessor:
    def __init__(self):
        self.max_width = 1920
        self.max_height = 1920
    
    def enhance_whiteboard(self, image_path: str) -> str:
        """
        Enhance whiteboard image for better OCR results (Vercel-optimized)
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > self.max_width or img.height > self.max_height:
                    img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                
                # Enhance contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)
                
                # Enhance sharpness
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
                
                # Enhance brightness slightly
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)
                
                # Save enhanced image
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                enhanced_path = os.path.join(
                    os.path.dirname(image_path), 
                    f"{base_name}_enhanced.jpg"
                )
                
                img.save(enhanced_path, 'JPEG', quality=95)
                return enhanced_path
                
        except Exception as e:
            print(f"Enhancement failed: {e}")
            return image_path  # Return original if enhancement fails

    def preprocess_for_ocr(self, image_path: str) -> str:
        """
        Preprocess image specifically for OCR using PIL
        """
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale
                img = img.convert('L')
                
                # Enhance contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                # Save processed image
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                ocr_path = os.path.join(
                    os.path.dirname(image_path),
                    f"{base_name}_ocr.jpg"
                )
                
                img.save(ocr_path, 'JPEG', quality=95)
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
                try:
                    exif = img._getexif()
                    if exif is not None:
                        for tag, value in exif.items():
                            if tag == 274:  # Orientation tag
                                if value == 3:
                                    img = img.rotate(180, expand=True)
                                elif value == 6:
                                    img = img.rotate(270, expand=True)
                                elif value == 8:
                                    img = img.rotate(90, expand=True)
                                break
                except:
                    pass  # No EXIF data or error reading it
                
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

    def segment_regions(self, img_path: str) -> dict:
        """
        Basic region segmentation fallback (no OpenCV)
        """
        # Return empty regions for Vercel deployment
        return {
            'text_regions': [],
            'diagram_regions': [],
            'table_regions': []
        }
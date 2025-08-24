import os
import json
import requests
from typing import Dict, Any
import base64
import time
from config import Config

class DoubaoService:
    def __init__(self):
        self.api_key = Config.DOUBAO_API_KEY
        self.endpoint = Config.DOUBAO_ENDPOINT
        self.model_id = Config.DOUBAO_MODEL_ID
        
        if not self.api_key:
            raise ValueError("DOUBAO_API_KEY is required")
    
    def analyze_whiteboard(self, image_base64: str, mime_type: str = None) -> Dict[str, Any]:
        """
        Analyze whiteboard image using Doubao Vision API
        """
        # Convert PNG to JPEG if needed, as Doubao may not support PNG
        if mime_type and mime_type.lower() in ['image/png']:
            image_base64, mime_type = self._convert_png_to_jpeg(image_base64)
        
        url = f"{self.endpoint}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert meeting whiteboard analyzer. Your task is to extract and structure all content from whiteboard images with high accuracy.

Extract the following information:
1. All text content (maintain original structure and formatting)
2. Tables and their data (preserve structure)
3. Diagrams, flowcharts, and drawings (describe in detail)
4. Action items and tasks (look for bullets, arrows, TODO markers)
5. Key topics and main themes
6. Hierarchical structure (headings, sub-points)

Return a detailed JSON structure with the following format:
{
  "title": "suggested meeting title based on content",
  "sections": [
    {
      "heading": "section title",
      "content": "section text content",
      "subsections": [],
      "type": "text|diagram|table"
    }
  ],
  "tables": [
    {
      "title": "table description",
      "headers": ["col1", "col2"],
      "rows": [["data1", "data2"]]
    }
  ],
  "diagrams": [
    {
      "type": "flowchart|mindmap|drawing",
      "description": "detailed description",
      "elements": ["element1", "element2"]
    }
  ],
  "action_items": [
    {
      "task": "action description",
      "priority": "high|medium|low",
      "assignee": "person name if mentioned"
    }
  ],
  "key_points": ["main point 1", "main point 2"],
  "raw_text": "all extracted text",
  "confidence": 0.95
}

Be thorough and accurate. Include all visible text and structural elements."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this whiteboard image and extract all content in the specified JSON format. Pay special attention to tables, action items, and hierarchical structure."
                        },
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:{mime_type or 'image/jpeg'};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Try to parse JSON from the response
                try:
                    # Extract JSON from the response (it might be wrapped in markdown)
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        json_str = content[json_start:json_end].strip()
                    else:
                        json_str = content.strip()
                    
                    structured_data = json.loads(json_str)
                    return structured_data
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {
                        "title": "Whiteboard Analysis",
                        "sections": [{"heading": "Content", "content": content, "type": "text"}],
                        "tables": [],
                        "diagrams": [],
                        "action_items": [],
                        "key_points": [],
                        "raw_text": content,
                        "confidence": 0.7
                    }
            else:
                error_text = response.text
                raise Exception(f"Doubao API error: {response.status_code} - {error_text}")
                        
        except requests.exceptions.Timeout:
            raise Exception("Request to Doubao API timed out")
        except Exception as e:
            raise Exception(f"Failed to analyze whiteboard: {str(e)}")
    
    def enhance_content(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Second pass to enhance and structure content
        """
        url = f"{self.endpoint}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a content enhancement specialist. Your task is to refine and improve extracted whiteboard content.

Tasks:
1. Fix OCR errors and typos
2. Improve formatting and structure
3. Enhance readability
4. Add missing connections between ideas
5. Prioritize action items
6. Generate better summaries

Maintain the original JSON structure but improve the content quality."""
                },
                {
                    "role": "user",
                    "content": f"Please enhance and improve this extracted content:\n\n{json.dumps(extracted_data, indent=2)}"
                }
            ],
            "temperature": 0.5,
            "max_tokens": 4096
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        json_str = content[json_start:json_end].strip()
                    else:
                        json_str = content.strip()
                        
                    enhanced_data = json.loads(json_str)
                    return enhanced_data
                except json.JSONDecodeError:
                    # Return original data if enhancement fails
                    return extracted_data
            else:
                # Return original data if API call fails
                return extracted_data
                        
        except Exception:
            # Return original data if enhancement fails
            return extracted_data
    
    def generate_summary(self, content: str) -> str:
        """
        Generate a concise summary of the whiteboard content
        """
        url = f"{self.endpoint}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a meeting summarization expert. Create concise, actionable summaries of whiteboard content."
                },
                {
                    "role": "user",
                    "content": f"Please create a brief summary of this meeting content:\n\n{content}"
                }
            ],
            "temperature": 0.4,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return "Summary generation failed"
                        
        except Exception:
            return "Summary generation failed"
    
    def test_connection(self) -> bool:
        """
        Test the Doubao API connection
        """
        try:
            # Simple test call
            test_result = self.generate_summary("Test content")
            return "failed" not in test_result.lower()
        except Exception:
            return False
    
    def _convert_png_to_jpeg(self, image_base64: str) -> tuple:
        """
        Convert PNG image to JPEG format for API compatibility
        Returns tuple of (new_base64, new_mime_type)
        """
        try:
            import base64
            import io
            from PIL import Image
            
            # Decode base64 to bytes
            image_data = base64.b64decode(image_base64)
            
            # Open image with PIL
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert RGBA to RGB (remove alpha channel for JPEG)
                if img.mode in ('RGBA', 'LA'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as JPEG to BytesIO
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=95)
                output.seek(0)
                
                # Encode back to base64
                jpeg_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
                return jpeg_base64, 'image/jpeg'
                
        except Exception as e:
            # If conversion fails, return original data
            print(f"PNG to JPEG conversion failed: {e}")
            return image_base64, 'image/jpeg'  # Try with JPEG mime type anyway
import os
# import sys # No longer needed for _MEIPASS logic here
from paddleocr import PaddleOCR
from typing import List, Optional

class OCRProcessor:
    """
    Handles OCR processing using PaddleOCR.
    """
    def __init__(self, lang: str = 'en'):
        """
        Initializes the OCRProcessor. PaddleOCR will download models if not found.
        Args:
            lang (str): The language to use for OCR. Defaults to 'en'.
        """
        self.current_lang = lang
        self._initialize_ocr_instance()

    def _initialize_ocr_instance(self):
        self.ocr_instance = PaddleOCR(
            lang=self.current_lang,
            use_textline_orientation=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False
        )
        print(f"OCR_UTILS: PaddleOCR instance initialized for lang='{self.current_lang}'.")

    def set_language(self, lang: str):
        """
        Sets a new language for OCR and re-initializes the PaddleOCR instance.
        """
        if lang != self.current_lang:
            self.current_lang = lang
            self._initialize_ocr_instance() # Re-initialize with the new language
            print(f"OCR_UTILS: OCR language changed to: {lang}")

    def process_image(self, image_path: str) -> Optional[str]:
        """
        Performs OCR on the given image file.

        Args:
            image_path (str): Path to the image file.

        Returns:
            Optional[str]: Extracted text as a single string, or None if no text found or error.
        """
        if not self.ocr_instance:
            print("OCR_UTILS ERROR: OCR instance is not initialized.")
            return None
        if not os.path.exists(image_path):
            print(f"Error: Image path does not exist: {image_path}")
            return None

        try:
            # predict() is expected to return List[paddlex.inference.pipelines.ocr.result.OCRResult]
            # based on the log: "First element type: <class 'paddlex.inference.pipelines.ocr.result.OCRResult'>"
            prediction_results = self.ocr_instance.predict(image_path)

            if not prediction_results:
                print("OCR (predict) returned no results (None or empty list).")
                return None

            all_extracted_texts: List[str] = []
            
            print(f"OCR_UTILS: Received {len(prediction_results)} result objects from predict().")
            for i, res_obj in enumerate(prediction_results): # res_obj is a paddlex OCRResult
                item_text = None
                print(f"OCR_UTILS: Processing result object {i+1}, type: {type(res_obj)}")
                try:
                    if hasattr(res_obj, 'json') and isinstance(res_obj.json, dict):
                        json_data = res_obj.json
                        if 'res' in json_data and isinstance(json_data['res'], dict):
                            res_content = json_data['res']
                            if 'rec_texts' in res_content and isinstance(res_content['rec_texts'], list):
                                meaningful_texts = [text for text in res_content['rec_texts'] if isinstance(text, str) and text.strip()]
                                if meaningful_texts:
                                    item_text = "\n".join(meaningful_texts)
                                    print(f"OCR_UTILS: Extracted text from result {i+1} via .json['res']['rec_texts']")
                            else:
                                print(f"OCR_UTILS: 'rec_texts' not found or not a list in res_obj.json['res'] for item {i+1}")
                        else:
                            print(f"OCR_UTILS: 'res' not found or not a dict in res_obj.json for item {i+1}")
                    else:
                         print(f"OCR_UTILS: Result object {i+1} does not have .json attribute or it's not a dict.")
                except Exception as e_json:
                    print(f"OCR_UTILS: Error accessing .json structure for item {i+1}: {e_json}")

                # Fallback or alternative: Check if the object itself is a list of lines (standard PaddleOCR output)
                # This case should ideally not be hit if type is paddlex.OCRResult and run_ocr.py's method is correct for it.
                if not item_text and isinstance(res_obj, list):
                    print(f"OCR_UTILS: .json parsing failed or yielded no text for item {i+1}. Trying to parse as list of lines.")
                    current_res_lines_texts: List[str] = []
                    for line_info in res_obj: # res_obj is a list of line_info
                         if isinstance(line_info, list) and len(line_info) == 2:
                            text_component = line_info[1]
                            if isinstance(text_component, tuple) and len(text_component) == 2:
                                text = text_component[0]
                                if isinstance(text, str) and text.strip():
                                    current_res_lines_texts.append(text.strip())
                    if current_res_lines_texts:
                        item_text = "\n".join(current_res_lines_texts)
                        print(f"OCR_UTILS: Extracted text from result {i+1} by parsing as list of lines.")
                
                if item_text:
                    all_extracted_texts.append(item_text)
                else:
                    print(f"OCR_UTILS: No text extracted for result object {i+1}. Object details: {str(res_obj)[:200]}")

            if all_extracted_texts:
                return "\n---\n".join(all_extracted_texts)
            else:
                print("OCR (predict) processed the image but found no meaningful text segments using any parsing method.")
                return None

        except Exception as e:
            print(f"Error during OCR processing (predict method): {e}")
            return None

if __name__ == '__main__':
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_image_path = os.path.join(os.path.dirname(current_script_dir), 'screenshot.png') 
    
    if not os.path.exists(dummy_image_path):
        print(f"Warning: Test image '{dummy_image_path}' not found. OCR processing test will be skipped.")
    else:
        print(f"Testing OCRProcessor with image: {dummy_image_path}")
        ocr_proc_en = OCRProcessor(lang='en')
        extracted_text_en = ocr_proc_en.process_image(dummy_image_path)
        if extracted_text_en:
            print("\n--- Extracted Text (English) ---")
            print(extracted_text_en)
            print("--- End of English Text ---")
        else:
            print("No text extracted in English or error occurred.")
    print(f"\nTest finished. Check output above.")
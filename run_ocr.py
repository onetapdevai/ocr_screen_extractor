from paddleocr import PaddleOCR
import os

# Initialize PaddleOCR with determined working settings
ocr = PaddleOCR(lang='en', use_textline_orientation=False, use_doc_orientation_classify=False, use_doc_unwarping=False)

image_path = 'screenshot.png' # Path to the image file for OCR
# Directory to save visualized OCR results from the predict API
output_dir = 'ocr_output_predict'
os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist

print(f"Performing OCR on: {image_path} using ocr.predict() API")
# ocr.predict() returns a list of OCRResult objects.
# For a single image, this list usually contains one OCRResult object.
# This OCRResult object then contains the actual recognition data.
prediction_results = ocr.predict(image_path)

if prediction_results:
    print("\nOCR Prediction Results:")
    all_extracted_texts = []
    
    # Iterate through the list of OCRResult objects
    # (typically one item for a single image)
    for i, res_obj in enumerate(prediction_results):
        # Text extraction
        item_text = None
        # Text is found within res_obj.json['res']['rec_texts']
        if hasattr(res_obj, 'json') and isinstance(res_obj.json, dict):
            json_data = res_obj.json
            if 'res' in json_data and isinstance(json_data['res'], dict):
                res_content = json_data['res']
                if 'rec_texts' in res_content and isinstance(res_content['rec_texts'], list):
                    # Filter out empty strings and join the meaningful recognized texts
                    meaningful_texts = [text for text in res_content['rec_texts'] if isinstance(text, str) and text.strip()]
                    if meaningful_texts:
                        item_text = "\n".join(meaningful_texts)
        
        if item_text:
            all_extracted_texts.append(item_text)
        else:
            # If text is not extracted, print a warning and the raw result object for debugging
            print(f"Warning: Could not extract text for result item {i+1}.")
            if hasattr(res_obj, 'print'): # Print the raw result object if text extraction failed
                print(f"--- Raw result object {i+1} for debugging ---")
                res_obj.print()
                print(f"--- End of raw result object {i+1} ---")

        # Saving visualization
        if hasattr(res_obj, 'save_to_img'):
            try:
                # PaddleOCR typically generates the filename itself within the specified directory
                res_obj.save_to_img(output_dir)
                print(f"Visualization for item {i+1} saved to directory: {output_dir}")
            except Exception as e_save:
                print(f"Error saving visualization for item {i+1} to '{output_dir}': {e_save}")
        else:
            print(f"Result item {i+1} does not have 'save_to_img' method.")
        
    if all_extracted_texts:
        print("\n\nRecognized Text:")
        # Join text from all result items (usually one for a single image)
        print("\n---\n".join(all_extracted_texts))
    else:
        print("Could not extract text from OCR results (ocr.predict()).")

else: # This corresponds to `if prediction_results:`
    print("OCR (ocr.predict() API) returned no results or an empty result (initial check).")

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QPushButton, QComboBox, QSplitter, QSizePolicy
)
from PySide6.QtGui import QPixmap, QScreen, QGuiApplication
from PySide6.QtCore import Qt, QSettings, QThread, Signal, QTimer, QEventLoop, QPoint

# Assuming ocr_utils.py is in the same directory (app/)
from ocr_utils import OCRProcessor

# Define a path for screenshots relative to the app directory
SCREENSHOT_TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_screenshots")
os.makedirs(SCREENSHOT_TEMP_DIR, exist_ok=True)
DEFAULT_SCREENSHOT_PATH = os.path.join(SCREENSHOT_TEMP_DIR, "latest_screenshot.png")

# Define available languages for OCR (key: display name, value: PaddleOCR lang code)
AVAILABLE_LANGUAGES = {
    "English": "en",
    "Chinese (Simplified)": "ch", # Example, more can be added
    "French": "fr",
    "German": "de",
    "Japanese": "japan",
    "Korean": "korean",
    # Add more languages as needed and ensure PaddleOCR supports them
}
DEFAULT_LANGUAGE = "English" # Display name

class OCRWorker(QThread):
    """
    Worker thread for performing OCR to avoid freezing the GUI.
    """
    ocr_finished = Signal(str) # Signal emitting the extracted text or error message
    
    def __init__(self, ocr_processor: OCRProcessor, image_path: str):
        super().__init__()
        self.ocr_processor = ocr_processor
        self.image_path = image_path

    def run(self):
        try:
            if not self.image_path or not os.path.exists(self.image_path):
                self.ocr_finished.emit("Error: Screenshot path is invalid or file does not exist for OCR.")
                return

            extracted_text = self.ocr_processor.process_image(self.image_path)
            if extracted_text:
                self.ocr_finished.emit(extracted_text)
            else:
                # The process_image method in ocr_utils now prints its own detailed error/no-text messages.
                # We can provide a generic one here or rely on those logs.
                self.ocr_finished.emit("No text could be extracted or an error occurred during OCR. Check console for details.")
        except Exception as e:
            self.ocr_finished.emit(f"Critical error in OCR thread: {e}")


class ScreenshotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screenshot Text Extractor")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        self.settings = QSettings("MyCompany", "ScreenshotTextExtractor") # For saving/loading settings
        
        self.ocr_processor = OCRProcessor(lang=AVAILABLE_LANGUAGES[DEFAULT_LANGUAGE])
        self.current_screenshot_path: str | None = None
        self.ocr_worker_thread: OCRWorker | None = None # For managing the OCR worker thread

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        # Main widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Extracted text area
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Extracted text will appear here...")
        self.text_area.setReadOnly(True)
        splitter.addWidget(self.text_area)

        # Right side: Screenshot thumbnail and controls
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)

        self.screenshot_label = QLabel("No screenshot taken yet.")
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setMinimumSize(200, 150) # Min size for the label
        self.screenshot_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored) # Allow shrinking
        right_panel_layout.addWidget(self.screenshot_label, 1) # Give it more stretch factor

        # Language selection
        language_layout = QHBoxLayout()
        language_label = QLabel("OCR Language:")
        self.language_combo = QComboBox()
        for lang_name in AVAILABLE_LANGUAGES.keys():
            self.language_combo.addItem(lang_name)
        
        current_lang_display = self.settings.value("language", DEFAULT_LANGUAGE)
        if current_lang_display in AVAILABLE_LANGUAGES:
            self.language_combo.setCurrentText(current_lang_display)
        else:
            self.language_combo.setCurrentText(DEFAULT_LANGUAGE)
            
        self.language_combo.currentTextChanged.connect(self.on_language_change)
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        right_panel_layout.addLayout(language_layout)

        self.scan_button = QPushButton("Scan Screen")
        self.scan_button.clicked.connect(self.scan_screen_and_process)
        right_panel_layout.addWidget(self.scan_button)
        
        right_panel_widget.setLayout(right_panel_layout)
        splitter.addWidget(right_panel_widget)

        # Set initial sizes for splitter (optional, can be adjusted by user)
        splitter.setSizes([500, 300]) # Adjust initial sizes as needed

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

    def on_language_change(self, lang_display_name: str):
        lang_code = AVAILABLE_LANGUAGES.get(lang_display_name)
        if lang_code:
            self.ocr_processor.set_language(lang_code)
            self.settings.setValue("language", lang_display_name)
            print(f"Language set to: {lang_display_name} ({lang_code})")
        else:
            print(f"Warning: Language '{lang_display_name}' not found in available languages.")

    def take_screenshot(self) -> str | None:
        """Takes a screenshot of the primary screen and saves it."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            self.text_area.setText("Error: Could not get primary screen.")
            return None
        
        original_pos = self.pos()
        # Define a fixed large off-screen position
        off_screen_pos = QPoint(-10000, -10000)
        
        try:
            self.move(off_screen_pos)
            QApplication.processEvents() # Ensure move is processed

            # Minimal delay for the move to register
            move_delay_loop = QEventLoop()
            QTimer.singleShot(20, move_delay_loop.quit) # Reduced delay to 20 ms
            move_delay_loop.exec()
            
            pixmap = screen.grabWindow(0) # Grab the entire screen
            self.current_screenshot_path = DEFAULT_SCREENSHOT_PATH
            
            if not pixmap.save(self.current_screenshot_path, "png"):
                self.text_area.setText(f"Error: Failed to save screenshot to {self.current_screenshot_path}")
                self.current_screenshot_path = None
            else:
                print(f"Screenshot saved to {self.current_screenshot_path}")
        
        except Exception as e:
            self.text_area.setText(f"Error taking screenshot: {e}")
            self.current_screenshot_path = None
        finally:
            # Ensure window is always moved back
            self.move(original_pos)
            QApplication.processEvents() # Ensure window is redrawn at original position
            
            # Minimal delay for the window to resettle visually
            settle_loop = QEventLoop()
            QTimer.singleShot(20, settle_loop.quit) # Reduced delay to 20ms
            settle_loop.exec()
            
        return self.current_screenshot_path

    def display_screenshot_thumbnail(self, image_path: str):
        if not os.path.exists(image_path):
            self.screenshot_label.setText("Screenshot file not found.")
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.screenshot_label.setText("Failed to load screenshot.")
            return
        
        # Scale pixmap to fit the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.screenshot_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.screenshot_label.setPixmap(scaled_pixmap)

    def scan_screen_and_process(self):
        self.scan_button.setEnabled(False)
        self.text_area.setText("Taking screenshot...")
        QApplication.processEvents() # Ensure UI update is processed

        # Add a brief delay to allow UI to settle before window manipulation
        # This might help make the transition smoother on some systems.
        pre_capture_delay_loop = QEventLoop()
        QTimer.singleShot(50, pre_capture_delay_loop.quit) # 50ms delay
        pre_capture_delay_loop.exec()

        screenshot_file = self.take_screenshot()

        if screenshot_file and os.path.exists(screenshot_file):
            self.display_screenshot_thumbnail(screenshot_file)
            self.text_area.setText(f"Screenshot taken: {os.path.basename(screenshot_file)}\nStarting OCR...")
            QApplication.processEvents()

            # Run OCR in a separate thread
            if self.ocr_worker_thread and self.ocr_worker_thread.isRunning():
                # Should not happen if button is disabled, but as a safeguard
                print("OCR is already in progress.")
                self.scan_button.setEnabled(True) # Re-enable if somehow stuck
                return

            self.ocr_worker_thread = OCRWorker(self.ocr_processor, screenshot_file)
            self.ocr_worker_thread.ocr_finished.connect(self.on_ocr_completed)
            self.ocr_worker_thread.finished.connect(self.on_ocr_thread_finished) # Clean up
            self.ocr_worker_thread.start()
            
            # Optionally, save the last used image path for display on next launch
            self.settings.setValue("last_screenshot_path", screenshot_file)
        else:
            self.text_area.setText("Failed to take or save screenshot. OCR aborted.")
            self.screenshot_label.setText("Screenshot failed.")
            self.scan_button.setEnabled(True)

    def on_ocr_completed(self, text_or_error: str):
        self.text_area.setText(text_or_error)
        # scan_button is re-enabled in on_ocr_thread_finished

    def on_ocr_thread_finished(self):
        self.scan_button.setEnabled(True)
        if self.ocr_worker_thread: # Ensure it exists before trying to delete
            self.ocr_worker_thread.deleteLater() # Schedule for deletion
            self.ocr_worker_thread = None
        print("OCR thread finished.")

    def load_settings(self):
        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load language
        lang_display_name = self.settings.value("language", DEFAULT_LANGUAGE)
        if lang_display_name in AVAILABLE_LANGUAGES:
            self.language_combo.setCurrentText(lang_display_name)
            # ocr_processor is initialized with default, so update if different
            if lang_display_name != DEFAULT_LANGUAGE:
                 self.ocr_processor.set_language(AVAILABLE_LANGUAGES[lang_display_name])
        else: # Fallback if saved language is no longer valid
            self.language_combo.setCurrentText(DEFAULT_LANGUAGE)
            self.ocr_processor.set_language(AVAILABLE_LANGUAGES[DEFAULT_LANGUAGE])

        # Load last screenshot for display (if any)
        last_screenshot = self.settings.value("last_screenshot_path")
        if last_screenshot and os.path.exists(last_screenshot):
            self.current_screenshot_path = last_screenshot
            self.display_screenshot_thumbnail(last_screenshot)
        else:
            # If no last screenshot or path is invalid, clear the label
            self.screenshot_label.setText("Take a new screenshot.")
            self.screenshot_label.setPixmap(QPixmap()) # Clear any existing pixmap


    def closeEvent(self, event):
        # Save settings before closing
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("language", self.language_combo.currentText())
        if self.current_screenshot_path and os.path.exists(self.current_screenshot_path):
             self.settings.setValue("last_screenshot_path", self.current_screenshot_path)
        else:
            # If no valid current screenshot, remove the setting or set to empty
            self.settings.remove("last_screenshot_path")
            
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = ScreenshotApp()
    main_win.show()
    sys.exit(app.exec())
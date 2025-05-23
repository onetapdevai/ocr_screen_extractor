# OCR Script Setup and Usage Guide (test-paddleocr.py)

This script uses the PaddleOCR library to recognize text in images.

## Requirements

*   Python (version 3.8-3.12 recommended. Python 3.12 was used in this project).
*   `pip` (Python package manager).

## Installation and Setup Steps

1.  **Clone or download the project:**
    Ensure you have the script file `run_ocr.py` and the image `screenshot.png` (or any other image you want to process, renamed to `screenshot.png` or with the path updated in the script).

2.  **Create a virtual environment (recommended):**
    Open a terminal or command prompt in the project folder and execute:
    ```bash
    python -m venv .venv
    ```
    This will create a `.venv` folder containing the virtual environment.

3.  **Activate the virtual environment:**
    *   **Windows (cmd.exe):**
        ```bash
        .venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell):**
        ```powershell
        .venv\Scripts\Activate.ps1
        ```
        (If PowerShell script execution is disabled, you might first need to run: `Set-ExecutionPolicy Unrestricted -Scope Process`)
    *   **macOS / Linux (bash/zsh):**
        ```bash
        source .venv/bin/activate
        ```
    After activation, `(.venv)` should appear at the beginning of your command prompt.

4.  **Install necessary libraries:**
    In the activated virtual environment, execute the following commands to install PaddleOCR and its dependencies:

    `pip install -r requirements.txt` or

    *   **Install `paddleocr` (version 3.0.0, as used in the project):**
        ```bash
        pip install paddleocr==3.0.0
        ```
    *   **Install `paddlepaddle` (the core framework, CPU version 3.0.0):**
        ```bash
        pip install paddlepaddle==3.0.0
        ```
        *Note: If you have a compatible NVIDIA GPU and configured CUDA, you can install the GPU version for better performance: `pip install paddlepaddle-gpu` (or another compatible version). However, the CPU version was successfully used in this project.*

        With the GPU version (paddlepaddle-gpu), I tried to install it, there are errors that need to be fixed, the CPU version has been tested by me and works.

    *   **Install `setuptools` (to resolve the `distutils` issue in Python 3.12+):**
        ```bash
        pip install setuptools
        ```

5.  **Prepare the image:**
    Ensure the image you want to process is in the same folder as the `run_ocr.py` script and is named `screenshot.png`. If your image has a different name or path, modify the `image_path = 'screenshot.png'` line in the script.

## Running the Script

1.  Ensure the virtual environment is activated.
2.  In the terminal, while in the project folder, execute:
    ```bash
    python run_ocr.py
    ```

## Expected Output

*   The recognized text from the image will be printed to the console.
*   An image with visualized OCR results (e.g., with text blocks outlined) will be saved in the `ocr_output_predict` folder (which will be created automatically if it doesn't exist). The filename will be generated automatically (e.g., `result_visualized_item_1.jpg`).

## Deactivating the Virtual Environment

When you are finished, you can deactivate the virtual environment by running the following command in the terminal:
```bash
deactivate
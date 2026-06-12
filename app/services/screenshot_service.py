import os
from playwright.sync_api import sync_playwright

def take_screenshot(html_file_path: str, output_image_path: str):
    """
    Renders an HTML file and takes a screenshot using Playwright.
    """
    # Ensure absolute path with file:// schema for playwright
    abs_path = os.path.abspath(html_file_path)
    # Fix for windows path (e.g. C:\ -> /C:/)
    file_url = f"file:///{abs_path.replace('\\', '/')}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        # Resolução quadrada/larga para caber os dois cards lado a lado sem cortar
        context = browser.new_context(
            viewport={'width': 1080, 'height': 800}, 
            device_scale_factor=2 # Alta resolução
        )
        page = context.new_page()
        # Wait until network idle ensures flags and images from CDN are loaded
        page.goto(file_url, wait_until='networkidle')
        
        # Take the screenshot, garantindo que pegue tudo
        page.screenshot(path=output_image_path, full_page=True)
        browser.close()
        print(f"Screenshot successfully saved to {output_image_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python screenshot_service.py <input.html> <output.png>")
        sys.exit(1)
    
    take_screenshot(sys.argv[1], sys.argv[2])

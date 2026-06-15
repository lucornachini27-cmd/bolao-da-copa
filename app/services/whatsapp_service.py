import logging
import httpx
from typing import Optional
from app.core.config import settings

log = logging.getLogger("uvicorn.error")

class WhatsAppService:
    def __init__(self):
        # We will need the user to set these variables in Render environment
        self.api_url = getattr(settings, 'evolution_api_url', '')
        self.api_key = getattr(settings, 'evolution_api_key', '')
        self.instance_name = getattr(settings, 'evolution_instance_name', '')

    def send_image(self, to_number_or_group: str, image_path: str, caption: str = "") -> bool:
        """
        Sends an image file via WhatsApp using Evolution API.
        """
        if not self.api_url or not self.api_key or not self.instance_name:
            log.warning("Evolution API credentials not fully configured. Skipping WhatsApp message.")
            return False

        endpoint = f"{self.api_url}/message/sendMedia/{self.instance_name}"
        headers = {
            "apikey": self.api_key
        }

        try:
            # Evolution API expects the media as base64 or URL. 
            # We will send it as base64.
            import base64
            import mimetypes

            with open(image_path, "rb") as img_file:
                b64_encoded = base64.b64encode(img_file.read()).decode('utf-8')
            
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = "image/png"

            import os
            file_name = os.path.basename(image_path)
            
            payload = {
                "number": to_number_or_group,
                "mediatype": "image",
                "mimetype": mime_type,
                "caption": caption,
                "media": b64_encoded,
                "fileName": file_name,
                "options": {
                    "delay": 1200,
                    "presence": "composing"
                }
            }

            response = httpx.post(endpoint, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            log.info(f"WhatsApp image sent successfully to {to_number_or_group}.")
            return True

        except Exception as e:
            log.error(f"Failed to send WhatsApp image: {e}")
            return False

whatsapp_service = WhatsAppService()

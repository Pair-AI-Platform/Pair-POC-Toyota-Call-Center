import requests

def main(phone_number: str, image_url: str, car_name: str, description: str) -> dict:
    """
    Send a Toyota car image with description to a WhatsApp user.

    Args:
        phone_number: The recipient's phone number in international format (e.g., "+965XXXXXXXX")
        image_url: The URL of the Toyota car image to send
        car_name: The name of the Toyota car model (e.g., "كامري", "برادو", "Camry", "Prado")
        description: Brief description of the car features and specifications

    Returns:
        dict: Contains result string with success/failure message

    When to use this tool:
    - When customer asks to see a car image ("أبي أشوف صورة السيارة", "Show me the car image")
    - When customer asks about car appearance ("شكل السيارة", "How does it look")
    - When customer requests visual information about a specific Toyota model
    - After recommending a car and customer wants to see it
    - When discussing car features and customer needs visual reference
    """
    # WhatsApp API endpoint
    url = "https://graph.facebook.com/v19.0/358836847319255/messages"

    # Authorization header with your token
    headers = {
        "Authorization": "Bearer EAARDzuZBCyVoBPKnKZAiZAnoUd9lCJZA5slAK56uhakC8iOuUsPbcPSh17okKVBAWbWoGmmEYtRUfusO1Sk3cxK1zLcK3ue4aKp2YTeinLD0FEZCHNTotV3D7sogxXce0STUqCQrUdqMjBYxYs2lq7lksyjtGrvtR2tntm7Sf0pvZCSxZBjbXWwY8qDuRy7RQ6iXhrWzA6ZC6G17yN0A3CSbq71R4JsORZBfYpsifk702",
        "Content-Type": "application/json"
    }

    # Payload for image message
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": f"🚗 {car_name}\n\n{description}\n\n✨ شوف الصورة فوق | See image above"
        }
    }

    try:
        # Send the request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return {
                "result": f"تم إرسال صورة {car_name} بنجاح ✅ | {car_name} image sent successfully ✅"
            }
        else:
            return {
                "result": f"فشل في إرسال الصورة. كود الخطأ: {response.status_code} | Failed to send image. Error code: {response.status_code} Error Message: {response.text}"
            }
            
    except Exception as e:
        return {
            "result": f"خطأ في الإرسال: {str(e)} | Sending error: {str(e)}"
        }

import requests

def main(phone_number: str, location_name: str, address: str, contact_info: str, maps_url: str) -> dict:
    """
    Send Toyota Kuwait branch location information to a WhatsApp user.

    Args:
        phone_number: The recipient's phone number in international format (e.g., "+965XXXXXXXX")
        location_name: Name of the Toyota branch (e.g., "معرض الأحمدي", "Ahmadi Showroom")
        address: Full address of the location in Arabic and English
        contact_info: Phone numbers and extensions for the location
        maps_url: Google Maps URL for the location

    Returns:
        dict: Contains result string with success/failure message

    When to use this tool:
    - When customer asks for branch locations ("وين أقرب معرض؟", "Where is the nearest showroom?")
    - When customer wants to visit a service center ("أبي أروح مركز الخدمة", "I want to go to service center")
    - When booking test drive and need to send location details
    - When customer asks for contact information of specific branch
    - When customer needs directions to Toyota facilities
    - After scheduling service appointment and need to send location
    """
    # WhatsApp API endpoint
    url = "https://graph.facebook.com/v19.0/358836847319255/messages"

    # Authorization header with your token
    headers = {
        "Authorization": "Bearer EAARDzuZBCyVoBPKnKZAiZAnoUd9lCJZA5slAK56uhakC8iOuUsPbcPSh17okKVBAWbWoGmmEYtRUfusO1Sk3cxK1zLcK3ue4aKp2YTeinLD0FEZCHNTotV3D7sogxXce0STUqCQrUdqMjBYxYs2lq7lksyjtGrvtR2tntm7Sf0pvZCSxZBjbXWwY8qDuRy7RQ6iXhrWzA6ZC6G17yN0A3CSbq71R4JsORZBfYpsifk702",
        "Content-Type": "application/json"
    }

    # Create location message text
    location_text = f"""📍 {location_name}

📧 العنوان | Address:
{address}

📞 التواصل | Contact:
{contact_info}

🗺️ الموقع على الخريطة | Location on Map:
{maps_url}

🕒 مواعيد العمل | Working Hours:
السبت - الخميس: 8:00 ص - 8:00 م
الجمعة: مغلق
Sat-Thu: 8:00 AM - 8:00 PM
Friday: Closed"""

    # Payload for text message
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": location_text
        }
    }

    try:
        # Send the request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return {
                "result": f"تم إرسال موقع {location_name} بنجاح ✅ | {location_name} location sent successfully ✅"
            }
        else:
            return {
                "result": f"فشل في إرسال الموقع. كود الخطأ: {response.status_code} | Failed to send location. Error code: {response.status_code} Error Message: {response.text}"
            }
            
    except Exception as e:
        return {
            "result": f"خطأ في الإرسال: {str(e)} | Sending error: {str(e)}"
        }

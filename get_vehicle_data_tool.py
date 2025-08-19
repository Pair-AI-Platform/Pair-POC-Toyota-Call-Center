import requests

def main(client_id: str, phone_number: str = None, language: str = "ar") -> dict:
    """
    Retrieves Toyota vehicle data for a specific client and optionally sends vehicle images via WhatsApp.
    
    Args:
        client_id: The client ID from the CRM system
        phone_number: Optional WhatsApp number to send vehicle images (e.g., "+965XXXXXXXX")
        language: Language preference ("ar" for Arabic, "en" for English)
    
    Returns:
        dict: Contains result string with vehicle data or image sending confirmation
        
    When to use this tool:
    - Before creating any service requests (to get vehicle ID)
    - When client asks about their registered vehicles
    - To show client their vehicle information with images
    - To retrieve vehicle ID for service ticket operations
    - When client wants to see their Toyota vehicles in the system
    """
    vehicles = get_all_vehicles()
    lang = language.lower()

    client_vehicles = [
        vehicle for vehicle in vehicles
        if vehicle.get("clientId") and vehicle["clientId"].get("_id") == client_id
    ]

    if not client_vehicles:
        error_msg = "لم يتم العثور على مركبات تويوتا لهذا العميل." if lang == "ar" else "No Toyota vehicles found for this client."
        return {"result": error_msg}

    if phone_number:
        return send_vehicle_images(client_vehicles, phone_number, lang)

    return {"result": str(client_vehicles)}


def get_all_vehicles():
    """
    Retrieves all vehicles from the Toyota Kuwait CRM API.
    """
    try:
        url = "https://crm-api.trypair.ai/api/vehicles"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiNjg1MjhkNTlkNzViNmU4YzFhZDM2ZGNlIiwicm9sZSI6ImFkbWluIn0sImlhdCI6MTc1NTU5NzU0NywiZXhwIjoxNzU1NjgzOTQ3fQ.myTYh8aO49ylD4XZrwi25MXMBRZmZyqjbUEhH_w70JU"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "vehicles" in data:
                return data["vehicles"]
            else:
                print("API returned success=False or missing 'vehicles'")
        else:
            print(f"Failed to retrieve vehicles. Status: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print(f"Error retrieving vehicles: {str(e)}")

    return []


def send_vehicle_images(vehicles, phone_number, language="ar"):
    """
    Send Toyota vehicle images to a WhatsApp user.
    """
    url = "https://graph.facebook.com/v19.0/358836847319255/messages"
    headers = {
        "Authorization": "Bearer EAARDzuZBCyVoBPL1bGl4N67ng7BsdU1KfCXBgUUiZBhCpFZBdZBCZCdljf6CW7H54LORCSbVS39jCRDq5k0awXttvkHtpMzV99ml8UZCexdhv4OVHde6GX6imlZAOadxoEIzZClGwXUI2UqisDoF0UIHamtZBQUVHabwo5yeFbZByxqu2SgmAGhoZASO9XYgWrFlKdlmAZDZD",
        "Content-Type": "application/json"
    }

    responses = []

    for vehicle in vehicles:
        make = vehicle.get("make", "Toyota")
        model = vehicle.get("modelName", "")
        year = vehicle.get("year", "")
        color = vehicle.get("color", "")
        license_plate = vehicle.get("licensePlate", "")
        vin = vehicle.get("VIN", "")
        image_url = vehicle.get("mediaId", {}).get("url", "https://crm-api.trypair.ai/uploads/default_vehicle.jpg")

        caption = (
            f"🚗 *هذه سيارتك تويوتا في سجلاتنا:*\n\n✨ *{make} {model} {year}*\n🎨 اللون: *{color}*\n🔢 رقم اللوحة: *{license_plate}*\n🔍 رقم الهيكل: *{vin}*\n\n🔧 جاهزين لخدمتك في أي وقت!"
            if language == "ar"
            else f"🚗 *This is your Toyota in our records:*\n\n✨ *{make} {model} {year}*\n🎨 Color: *{color}*\n🔢 License Plate: *{license_plate}*\n🔍 VIN: *{vin}*\n\n🔧 Ready to serve you anytime!"
        )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            responses.append(response.json())
            print(f"✅ Sent image for {make} {model}")
        except Exception as e:
            error_msg = f"❌ Failed to send image for {make} {model}: {str(e)}"
            print(error_msg)
            responses.append({"error": error_msg})

    vehicles_data = [extract_vehicle_info(v) for v in vehicles]

    message = (
        f"تم إرسال معلومات وصور عن {len(vehicles)} مركبة تويوتا. بيانات المركبات: {vehicles_data}"
        if language == "ar"
        else f"Sent information and images for {len(vehicles)} Toyota vehicle(s). Vehicle data: {vehicles_data}"
    )

    return {"result": message}


def extract_vehicle_info(vehicle):
    """
    Extract structured vehicle data for messaging.
    """
    client_info = vehicle.get("clientId", {})
    return {
        "id": vehicle.get("_id", ""),
        "make": vehicle.get("make", "Toyota"),
        "model": vehicle.get("modelName", ""),
        "year": vehicle.get("year", ""),
        "color": vehicle.get("color", ""),
        "licensePlate": vehicle.get("licensePlate", ""),
        "vin": vehicle.get("VIN", ""),
        "purchaseDate": vehicle.get("purchaseDate", ""),
        "purchaseLocation": vehicle.get("purchaseLocation", ""),
        "lastServiceDate": vehicle.get("lastServiceDate", ""),
        "clientId": client_info.get("_id", ""),
        "clientName": f"{client_info.get('firstName', '')} {client_info.get('lastName', '')}".strip()
    }

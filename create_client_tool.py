import requests

def main(phone_number: str, first_name: str = None, last_name: str = None, email: str = None, address: str = None) -> dict:
    """
    Creates a new Toyota Kuwait client in the CRM system.
    
    Args:
        phone_number: Client's phone number in international format (e.g., "+965XXXXXXXX")
        first_name: Client's first name in Arabic or English
        last_name: Client's last name in Arabic or English
        email: Client's email address
        address: Client's address in Kuwait
    
    Returns:
        dict: Contains result string with success/failure message
        
    When to use this tool:
    - When new client needs to be registered in the system
    - After get_client_data returns no existing client data
    - When client provides all required information (first name, last name, email, address)
    - Before creating service requests for new clients
    """
    if first_name and last_name and email and address:
        return create_client(first_name, last_name, email, phone_number, address)
    else:
        return {"result": "يرجى تزويدنا بالاسم الأول والأخير والإيميل والعنوان لإنشاء حساب جديد | Please provide first name, last name, email, and address to create a new client account."}

def create_client(first_name: str, last_name: str, email: str, phone: str, address: str) -> dict:
    """
    Creates a new client in the Toyota Kuwait CRM system.
    """
    try:
        url = "https://crm-api.trypair.ai/api/clients"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiNjg1MjhkNTlkNzViNmU4YzFhZDM2ZGNlIiwicm9sZSI6ImFkbWluIn0sImlhdCI6MTc1NTU5NzU0NywiZXhwIjoxNzU1NjgzOTQ3fQ.myTYh8aO49ylD4XZrwi25MXMBRZmZyqjbUEhH_w70JU"
        }

        client_data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "communicationPreference": "email"
        }

        response = requests.post(url, headers=headers, json=client_data)

        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            if data.get("success") and "client" in data:
                return {"result": f"تم إنشاء حساب العميل بنجاح. مرحباً {first_name}! | Client account created successfully. Welcome {first_name}!"}

        return {"result": f"فشل في إنشاء حساب العميل. كود الخطأ: {response.status_code} | Failed to create client account. Error code: {response.status_code} Error Message: {response.text}"}

    except Exception as e:
        return {"result": f"خطأ في إنشاء حساب العميل: {str(e)} | Error creating client account: {str(e)}"}

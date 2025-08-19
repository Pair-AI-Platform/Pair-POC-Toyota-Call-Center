import requests

def main(phone_number: str) -> dict:
    """
    Retrieves Toyota Kuwait client data based on phone number.
    
    Args:
        phone_number: The client's phone number in international format (e.g., "+965XXXXXXXX")
    
    Returns:
        dict: Contains result string with client data or welcome message for new clients
        
    When to use this tool:
    - When customer starts conversation with Arabic greetings like "هلا" or "سلام عليكم"
    - To retrieve existing client information and personalize interactions
    - To check if client exists before creating service requests
    - To access client's vehicle information and service history
    """
    clients = get_all_clients()
    
    client = next((client for client in clients if client["phone"] == phone_number), None)
    
    if client:
        client_str = str(client)
        return {"result": client_str}
    else:
        return {"result": "حياك الله، لم يتم العثور على بيانات العميل. نرجو تزويدنا بالاسم الأول والأخير والإيميل والعنوان | Welcome, client data not found. Please provide first name, last name, email and address"}

def get_all_clients():
    """
    Retrieves all clients from the Toyota Kuwait CRM API.
    """
    try:
        url = "https://crm-api.trypair.ai/api/clients"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiNjg1MjhkNTlkNzViNmU4YzFhZDM2ZGNlIiwicm9sZSI6ImFkbWluIn0sImlhdCI6MTc1NTU5NzU0NywiZXhwIjoxNzU1NjgzOTQ3fQ.myTYh8aO49ylD4XZrwi25MXMBRZmZyqjbUEhH_w70JU"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "clients" in data:
                return data["clients"]
        
        return []
    
    except Exception as e:
        print(f"Error retrieving clients: {str(e)}")
        return []

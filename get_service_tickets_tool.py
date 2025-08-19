import requests

def main(vehicle_id: str = None, client_id: str = None) -> dict:
    """
    Retrieves Toyota service ticket data for a specific vehicle or client.
    
    Args:
        vehicle_id: Optional vehicle ID to retrieve tickets for specific Toyota vehicle
        client_id: Optional client ID to retrieve all tickets for specific client
        
    Returns:
        dict: Contains result string with service tickets data
        
    When to use this tool:
    - When client asks about service visit status ("شنو وضع سيارتي؟", "What's my service status?")
    - To check existing service appointments and history
    - When client provides service ticket ID for status inquiry
    - To retrieve service history for specific Toyota vehicle
    - Before creating new service requests to check existing ones
    """
    # Retrieve all tickets
    tickets = get_all_tickets()
    
    # If no filters provided, return all tickets
    if vehicle_id is None and client_id is None:
        tickets_str = str(tickets)
        return {"result": tickets_str}
    
    # Filter tickets based on provided parameters
    filtered_tickets = []
    
    if vehicle_id:
        # Filter tickets by vehicle ID
        filtered_tickets = [ticket for ticket in tickets if ticket.get("vehicleId", {}).get("_id") == vehicle_id]
    elif client_id:
        # Filter tickets by client ID
        filtered_tickets = [ticket for ticket in tickets if ticket.get("clientId", {}).get("_id") == client_id]
    
    # Return a dictionary with the result
    if filtered_tickets:
        # Convert tickets data to string
        tickets_str = str(filtered_tickets)
        return {"result": tickets_str}
    else:
        return {"result": "لم يتم العثور على طلبات خدمة. | No service tickets found."}

def get_all_tickets():
    """
    Retrieves all service tickets from the Toyota Kuwait CRM API.
    
    Returns:
        list: A list of service ticket objects
    """
    try:
        # API endpoint for retrieving tickets
        url = "https://crm-api.trypair.ai/api/tickets"
        
        # Headers including authentication token
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiNjg1MjhkNTlkNzViNmU4YzFhZDM2ZGNlIiwicm9sZSI6ImFkbWluIn0sImlhdCI6MTc1NTU5NzU0NywiZXhwIjoxNzU1NjgzOTQ3fQ.myTYh8aO49ylD4XZrwi25MXMBRZmZyqjbUEhH_w70JU"
        }
        
        # Make the API request
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "tickets" in data:
                return data["tickets"]
        
        # Return empty list if request failed or data structure is unexpected
        return []
    
    except Exception as e:
        print(f"Error retrieving tickets: {str(e)}")
        return []

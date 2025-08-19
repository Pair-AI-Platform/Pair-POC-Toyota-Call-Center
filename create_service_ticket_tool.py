import requests
from datetime import datetime, timedelta

def main(client_id: str, vehicle_id: str, title: str, description: str, preferred_date: str = None) -> dict:
    """
    Creates a new Toyota service ticket/request in the CRM system.
    
    Args:
        client_id: The client ID from the CRM system
        vehicle_id: The vehicle ID for the Toyota being serviced
        title: Brief title of the service request (e.g., "صيانة دورية", "Regular Maintenance")
        description: Detailed description of the service needed
        preferred_date: Optional preferred service date (YYYY-MM-DD format)
        
    Returns:
        dict: Contains result string with service ticket creation confirmation
        
    When to use this tool:
    - When client requests new service appointment
    - After collecting service details and vehicle information
    - When client describes Toyota service needs or issues
    - To schedule maintenance, repairs, or inspections
    - After confirming client and vehicle data exists in system
    """
    try:
        url = "https://crm-api.trypair.ai/api/tickets"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-auth-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiNjg1MjhkNTlkNzViNmU4YzFhZDM2ZGNlIiwicm9sZSI6ImFkbWluIn0sImlhdCI6MTc1MTc3NzUzMiwiZXhwIjoxNzUxODYzOTMyfQ.4PLRb_Q68sjYta18jWzLdPJvSmSwMLjteQSS8KJEtyM"
        }
        
        # Calculate estimated completion date (2 days from now)
        estimated_completion = datetime.now() + timedelta(days=2)
        
        ticket_data = {
            "clientId": client_id,
            "vehicleId": vehicle_id,
            "title": title,
            "description": description,
            "status": "pending",  # Default status in database
            "priority": "medium",
            "estimatedCompletionDate": estimated_completion.isoformat(),
            "preferredServiceDate": preferred_date if preferred_date else datetime.now().isoformat(),
            "category": "service_request"
        }
        
        response = requests.post(url, headers=headers, json=ticket_data)
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            if data.get("success") and "ticket" in data:
                ticket_id = data["ticket"].get("_id", "")
                return {
                    "result": f"تم إنشاء طلب الخدمة بنجاح ✅\n\nرقم طلب الخدمة: *{ticket_id}*\nالحالة: *تم الاستلام*\nالتاريخ المتوقع للإنجاز: خلال يومين\n\nسنتواصل معك فور جاهزية سيارتك تويوتا 🚗 | Service request created successfully ✅\n\nService Request ID: *{ticket_id}*\nStatus: *Drop-off*\nEstimated completion: Within 2 days\n\nWe'll contact you when your Toyota is ready 🚗"
                }
        
        return {"result": f"فشل في إنشاء طلب الخدمة. كود الخطأ: {response.status_code} | Failed to create service request. Error code: {response.status_code} Error Message: {response.text}"}
    
    except Exception as e:
        return {"result": f"خطأ في إنشاء طلب الخدمة: {str(e)} | Error creating service request: {str(e)}"}

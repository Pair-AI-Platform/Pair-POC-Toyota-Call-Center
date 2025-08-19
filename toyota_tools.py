import logging
from livekit.agents import function_tool, RunContext
from typing import Dict, List, Optional, Any
from difflib import get_close_matches
import get_client_data_tool
import create_client_tool
import get_vehicle_data_tool
import get_service_tickets_tool
import create_service_ticket_tool
import send_car_image_tool
import send_location_tool

class ToyotaTools:
    def __init__(self, session, client_data=None, client_phone=None):
        self.session = session
        self.client_data = client_data
        # ✅ Always fallback to default phone number
        self.client_phone = client_phone or "+96566756452"
        
    def update_client_info(self, client_data, client_phone):
        """Update client information"""
        self.client_data = client_data
        self.client_phone = client_phone

    @function_tool(
        name="get_client_data",
        description="Retrieve comprehensive client data from Toyota Kuwait's customer database using phone number. This function searches for existing customer records, returns personal information, vehicle ownership history, service records, and contact preferences. Use this when a customer calls and you need to identify them or access their account information."
    )
    async def get_client_data(self, context: RunContext, phone_number: str) -> dict:
        """Retrieve Toyota Kuwait client data"""
        try:
            result = get_client_data_tool.main(phone_number)
            logging.info(f"Client data retrieved for {phone_number}")
            
            if "لم يتم العثور على بيانات العميل" not in result["result"]:
                self.client_data = result["result"]
                self.client_phone = phone_number
                
            return {"status": "success", "data": result["result"]}
        except Exception as e:
            logging.error(f"Error getting client data: {e}")
            return {"status": "error", "message": f"خطأ في استرجاع بيانات العميل: {str(e)}"}

    @function_tool(
        name="create_client",
        description="Register a new customer in Toyota Kuwait's customer management system. This function creates a complete customer profile with personal details, contact information, and preferences. Use this when a new customer wants to register for Toyota services, purchase a vehicle, or access customer benefits. Requires full name, email, phone number, and address for account creation."
    )
    async def create_client(self, context: RunContext, first_name: str, last_name: str, 
                           email: str, phone: str, address: str) -> dict:
        """Register a new client with Toyota Kuwait"""
        try:
            result = create_client_tool.main(first_name, last_name, email, phone, address)
            logging.info(f"New client created: {first_name} {last_name}")
            self.client_phone = phone
            return {"status": "success", "data": result["result"]}
        except Exception as e:
            logging.error(f"Error creating client: {e}")
            return {"status": "error", "message": f"خطأ في تسجيل العميل: {str(e)}"}

    @function_tool(
        name="get_vehicle_data",
        description="Retrieve comprehensive vehicle information for a specific client from Toyota Kuwait's vehicle database. This function returns detailed vehicle specifications, ownership history, maintenance records, warranty status, and current condition. Optionally sends vehicle images via WhatsApp if send_images is True. Use this when customers inquire about their owned vehicles or need vehicle-specific information."
    )
    async def get_vehicle_data(self, context: RunContext, client_id: str, 
                              send_images: bool = False) -> dict:
        """Retrieve Toyota vehicle data"""
        try:
            phone_number = self.client_phone if send_images else None
            result = get_vehicle_data_tool.main(client_id, phone_number, "ar")
            logging.info(f"Vehicle data retrieved for client {client_id}")
            return {"status": "success", "data": result["result"]}
        except Exception as e:
            logging.error(f"Error getting vehicle data: {e}")
            return {"status": "error", "message": f"خطأ في استرجاع بيانات المركبة: {str(e)}"}

    @function_tool(
        name="send_car_image",
        description="""Send high-quality Toyota vehicle images directly to customer's WhatsApp. 
This function retrieves official Toyota vehicle photos and sends them with detailed descriptions 
including features, specifications, and pricing information. Use this when customers want to see 
specific car models, compare vehicles visually, or need visual references for their purchase decisions. 

⚠️ Important: The car name must match one of the officially supported Toyota models available in Kuwait. 
Currently supported models include:
- كامري / Camry
- برادو / Prado
- لاند كروزر / Land Cruiser
- كورولا / Corolla
- هايلكس / Hilux
- ريز / Raize
- هايلاندر / Highlander

If a customer provides a name with spelling mistakes or in a slightly different format 
(e.g., "هاي لاندر" instead of "هايلاندر"), the system will automatically use fuzzy search 
to find the closest valid match. If no close match is found, the tool will return a clear error message. 

This ensures customers always receive the correct vehicle images and descriptions for 
Toyota models available in the Kuwaiti market.""")
    async def send_car_image(self, context: RunContext, car_name: str,
                            description: str = "") -> dict:
        """Send Toyota car image via WhatsApp"""
        try:
            print(f"\n🚗 ===== SEND_CAR_IMAGE REQUEST STARTED =====")
            print(f"🚗 Requested car: '{car_name}'")
            print(f"🚗 Current client_phone: '{self.client_phone}'")
            print(f"🚗 Description provided: '{description}'")
            
            if not self.client_phone:
                print(f"🚗 ❌ NO PHONE NUMBER AVAILABLE")
                return {"status": "error", "message": "لا يمكن إرسال الصورة - لم يتم العثور على رقم الهاتف"}
            
            print(f"🚗 Looking up image URL for car: '{car_name}'")
            image_url = self._get_car_image_url(car_name)
            print(f"🚗 Found image URL: '{image_url}'")
            
            if not image_url:
                print(f"🚗 ❌ NO IMAGE URL FOUND for car: '{car_name}'")
                return {"status": "error", "message": f"لا توجد صورة متاحة لموديل {car_name}"}
            
            if not description:
                description = self._get_car_description(car_name)
                print(f"🚗 Generated description: '{description}'")
            else:
                print(f"🚗 Using provided description: '{description}'")
            
            print(f"🚗 📱 CALLING WHATSAPP TOOL with:")
            print(f"🚗 📱   phone_number: '{self.client_phone}'")
            print(f"🚗 📱   image_url: '{image_url}'")
            print(f"🚗 📱   car_name: '{car_name}'")
            print(f"🚗 📱   description: '{description[:100]}...'")
            
            result = send_car_image_tool.main(
                phone_number=self.client_phone,
                image_url=image_url,
                car_name=car_name,
                description=description
            )
            
            print(f"🚗 📱 WHATSAPP TOOL RESPONSE:")
            print(f"🚗 📱   Full result: {result}")
            print(f"🚗 📱   Result type: {type(result)}")
            
            if result and "result" in result:
                print(f"🚗 📱   Inner result: {result['result']}")
                print(f"🚗 ✅ Car image sent successfully for {car_name}")
                logging.info(f"Car image sent for {car_name}")
                return {"status": "success", "data": result["result"]}
            else:
                print(f"🚗 ❌ WhatsApp tool returned unexpected result: {result}")
                return {"status": "error", "message": f"فشل في إرسال صورة {car_name} - استجابة غير متوقعة من أداة الواتساب"}
                
        except Exception as e:
            print(f"🚗 ❌ EXCEPTION in send_car_image: {e}")
            print(f"🚗 ❌ Exception type: {type(e)}")
            import traceback
            print(f"🚗 ❌ Full traceback: {traceback.format_exc()}")
            logging.error(f"Error sending car image: {e}")
            return {"status": "error", "message": f"خطأ في إرسال صورة السيارة: {str(e)}"}

    @function_tool(
        name="send_location",
        description="Send precise location information and directions to Toyota Kuwait branches via WhatsApp. This function provides GPS coordinates, address details, contact numbers, operating hours, and available services for showrooms, service centers, or parts departments. Use this when customers need to visit Toyota facilities, schedule appointments, or require directions to the nearest branch. Supports location types: 'showroom', 'service', 'parts'."
    )
    async def send_location(self, context: RunContext, location_type: str = "showroom") -> dict:
        """Send Toyota Kuwait branch location"""
        try:
            if not self.client_phone:
                return {"status": "error", "message": "لا يمكن إرسال الموقع - لم يتم العثور على رقم الهاتف"}
                
            result = send_location_tool.main(
                phone_number=self.client_phone,
                location_type=location_type,
                language="ar"
            )
            logging.info(f"Location sent: {location_type}")
            return {"status": "success", "data": result["result"]}
        except Exception as e:
            logging.error(f"Error sending location: {e}")
            return {"status": "error", "message": f"خطأ في إرسال الموقع: {str(e)}"}

    @function_tool(
        name="create_service_ticket",
        description="Create a comprehensive service appointment ticket in Toyota Kuwait's service management system. This function schedules vehicle maintenance, repairs, inspections, or warranty work with detailed service requirements, customer preferences, and priority levels. Use this when customers need to book service appointments, report vehicle issues, or schedule routine maintenance. Automatically assigns service advisors and estimates completion time."
    )
    async def create_service_ticket(self, context: RunContext, client_id: str, vehicle_id: str,
                                   service_type: str, description: str,
                                   preferred_date: str = "") -> dict:
        """Create a new Toyota service ticket"""
        try:
            result = create_service_ticket_tool.main(
                client_id=client_id,
                vehicle_id=vehicle_id,
                service_type=service_type,
                description=description,
                preferred_date=preferred_date
            )
            logging.info(f"Service ticket created for client {client_id}")
            return {"status": "success", "data": result["result"]}
        except Exception as e:
            logging.error(f"Error creating service ticket: {e}")
            return {"status": "error", "message": f"خطأ في إنشاء تذكرة الخدمة: {str(e)}"}

    @function_tool(
        name="get_service_tickets",
        description="Retrieve all service history and current service tickets for a specific customer from Toyota Kuwait's service database. This function returns detailed service records including past maintenance, current appointments, warranty claims, service costs, and technician notes. Use this when customers inquire about their service history, want to track current service status, or need service documentation for warranty purposes."
    )
    async def get_service_tickets(self, context: RunContext, client_id: str) -> dict:
        """Fetch Toyota service tickets"""
        try:
            result = get_service_tickets_tool.main(client_id)
            logging.info(f"Service tickets retrieved for client {client_id}")
            return {"status": "success", "data": result["result"]}
        except Exception as e:
            logging.error(f"Error getting service tickets: {e}")
            return {"status": "error", "message": f"خطأ في استرجاع تذاكر الخدمة: {str(e)}"}

    # Helper methods
    def _normalize_car_name(self, car_name: str, available_models: dict) -> str:
        """Return the closest matching car model name using fuzzy search"""
        print(f"🔍 FUZZY SEARCH: Looking for '{car_name}'")
        car_name = car_name.strip().lower()
        print(f"🔍 FUZZY SEARCH: Normalized to '{car_name}'")
        
        if car_name in available_models:
            print(f"🔍 FUZZY SEARCH: ✅ EXACT MATCH found for '{car_name}'")
            return car_name
        
        print(f"🔍 FUZZY SEARCH: No exact match, trying fuzzy matching...")
        print(f"🔍 FUZZY SEARCH: Available models: {list(available_models.keys())[:10]}...")
        
        # Try fuzzy matching
        matches = get_close_matches(car_name, available_models.keys(), n=1, cutoff=0.6)
        print(f"🔍 FUZZY SEARCH: Fuzzy matches found: {matches}")
        
        if matches:
            matched_name = matches[0]
            print(f"🔍 FUZZY SEARCH: ✅ FUZZY MATCH: '{car_name}' -> '{matched_name}'")
            logging.warning(f"Fuzzy match: '{car_name}' -> '{matched_name}'")
            return matched_name
        
        print(f"🔍 FUZZY SEARCH: ❌ NO MATCH found for '{car_name}'")
        return None

    def _get_car_image_url(self, car_name):
        """Get image URL for specific car model with fuzzy matching"""
        car_images = {
            "كامري": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/fc96a3af30e07dd8da9ae20762089ce5/960x600_camry_me_2406_213.png",
            "camry": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/fc96a3af30e07dd8da9ae20762089ce5/960x600_camry_me_2406_213.png",
            "برادو": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/563a9350dad1053e12e4344f708f1ced/ext_2.png",
            "prado": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/563a9350dad1053e12e4344f708f1ced/ext_2.png",
            "لاند كروزر": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/44c7695bf5cf4abdb7ce4beec883486d/land_cruiser.png",
            "land cruiser": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/44c7695bf5cf4abdb7ce4beec883486d/land_cruiser.png",
            "كورولا": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/73d4a67096830328c387e6ed0664e8d4/trim_lvl_1.png",
            "corolla": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/73d4a67096830328c387e6ed0664e8d4/trim_lvl_1.png",
            "هايلكس": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/0fec33e3a53ae9ceb03946e1e8017eff/hilux.png",
            "hilux": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/0fec33e3a53ae9ceb03946e1e8017eff/hilux.png",
            "ريز": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/e8d0f7dee4cd5e16fe6322ceb56c014d/raize.png",
            "raize": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/e8d0f7dee4cd5e16fe6322ceb56c014d/raize.png",
            # ✅ Added Highlander and common variations
            "هايلاندر": "https://toyota.scene7.com/is/image/toyota/highlander2023",
            "highlander": "https://toyota.scene7.com/is/image/toyota/highlander2023",
            "هاي لاندر": "https://toyota.scene7.com/is/image/toyota/highlander2023",
            "hi lander": "https://toyota.scene7.com/is/image/toyota/highlander2023",
            # ✅ Added more Toyota models
            "فورتنر": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/fortuner2023.png",
            "fortuner": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/fortuner2023.png",
            "كورولا كروس": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/corolla_cross2023.png",
            "corolla cross": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/corolla_cross2023.png"
        }
        
        match = self._normalize_car_name(car_name, car_images)
        return car_images.get(match) if match else None

    def _get_car_description(self, car_name):
        """Get description for specific car model with fuzzy matching"""
        descriptions = {
            "كامري": "سيارة سيدان تنفيذية فاخرة مع تقنيات متقدمة وراحة استثنائية",
            "camry": "سيارة سيدان تنفيذية فاخرة مع تقنيات متقدمة وراحة استثنائية",
            "برادو": "سيارة دفع رباعي فاخرة مثالية للعائلات والرحلات الطويلة",
            "prado": "سيارة دفع رباعي فاخرة مثالية للعائلات والرحلات الطويلة",
            "لاند كروزر": "سيارة دفع رباعي فاخرة بحجم كامل مع قدرات استثنائية على الطرق الوعرة",
            "land cruiser": "سيارة دفع رباعي فاخرة بحجم كامل مع قدرات استثنائية على الطرق الوعرة",
            "كورولا": "سيارة سيدان عائلية موثوقة واقتصادية مع تقنيات حديثة",
            "corolla": "سيارة سيدان عائلية موثوقة واقتصادية مع تقنيات حديثة",
            "هايلكس": "شاحنة بيك أب قوية ومتينة مثالية للعمل والمغامرات",
            "hilux": "شاحنة بيك أب قوية ومتينة مثالية للعمل والمغامرات",
            "ريز": "سيارة كروس أوفر مدمجة عملية ومناسبة للمدينة",
            "raize": "سيارة كروس أوفر مدمجة عملية ومناسبة للمدينة",
            # ✅ Added Highlander descriptions
            "هايلاندر": "سيارة SUV عائلية مريحة تجمع بين الرحابة والأمان والتقنيات الحديثة",
            "highlander": "سيارة SUV عائلية مريحة تجمع بين الرحابة والأمان والتقنيات الحديثة",
            "هاي لاندر": "سيارة SUV عائلية مريحة تجمع بين الرحابة والأمان والتقنيات الحديثة",
            "hi lander": "سيارة SUV عائلية مريحة تجمع بين الرحابة والأمان والتقنيات الحديثة",
            # ✅ Added more model descriptions
            "فورتنر": "سيارة دفع رباعي قوية وموثوقة مثالية للعائلات والمغامرات",
            "fortuner": "سيارة دفع رباعي قوية وموثوقة مثالية للعائلات والمغامرات",
            "كورولا كروس": "سيارة كروس أوفر عملية تجمع بين كفاءة الوقود والمساحة الداخلية",
            "corolla cross": "سيارة كروس أوفر عملية تجمع بين كفاءة الوقود والمساحة الداخلية"
        }
        
        match = self._normalize_car_name(car_name, descriptions)
        return descriptions.get(match, "سيارة تويوتا عالية الجودة والموثوقية")

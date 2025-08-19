import asyncio
import logging
import os
import uuid
from datetime import datetime
from livekit.plugins import azure
from livekit.plugins.elevenlabs.tts import VoiceSettings

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
    ConversationItemAddedEvent,
)
from livekit.agents import Agent, AgentSession, RoomInputOptions, RoomOutputOptions
from livekit.plugins import silero, elevenlabs, openai
from livekit.plugins import noise_cancellation

# Import Toyota tools
from toyota_tools import ToyotaTools

# ──────────────────────────
# Environment / logging
# ──────────────────────────
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), ".env"),
    override=True,
)

logger = logging.getLogger("toyota-voice-assistant")
logging.basicConfig(level=logging.INFO)

# Simple function to log responses to a file
def log_to_file(text, prefix="LOG"):
    try:
        log_file = os.path.join(os.path.dirname(__file__), "toyota_llm_responses.txt")
        print(f"[log_to_file] writing to: {log_file}")
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n--- {prefix} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ---\n")
                f.write(text)
            
            print(f"\n\n=== {prefix} ===\n{text}\n=== END {prefix} ===\n\n")
        except Exception as e:
            print(f"[log_to_file] ERROR writing: {e}")
    except Exception as e:
        print(f"Error logging to file: {e}")

def prewarm(proc: JobProcess):
    """Pre-load the Silero VAD model once per worker."""
    proc.userdata["vad"] = silero.VAD.load(
        activation_threshold=0.45,
        min_speech_duration=0.15,
        min_silence_duration=0.35
    )

# ──────────────────────────
# Custom Toyota Agent
# ──────────────────────────
class ToyotaKuwaitAgent(Agent):
    def __init__(
        self,
        session_id: str,
        participant_identity: str,
    ):
        super().__init__(instructions=_TOYOTA_SYSTEM_PROMPT)
        self.session_id = session_id
        self.participant_identity = participant_identity
        self.client_phone = None
        self.client_data = None

    # ------------------------------------------------------------------
    # Incoming user message
    # ------------------------------------------------------------------
    async def on_message(self, message, context):
        # Log the user message
        log_to_file(message.text, "USER MESSAGE")

        # Check if this is a greeting and we need to get client data
        if self._is_greeting(message.text) and not self.client_data:
            await self._handle_client_identification(message.text, context)

        # Check if user is asking about car images
        if self._is_car_image_request(message.text):
            await self._handle_car_image_request(message.text, context)

        # Check if user is asking for location
        if self._is_location_request(message.text):
            await self._handle_location_request(message.text, context)

        print("\n\n=== CALLING LLM FOR TOYOTA RESPONSE ===\n\n")
        
        # Call the parent method
        response = await super().on_message(message, context)
        
        if response is not None:
            response_text = getattr(response, "text", str(response))
            print(f">>> Toyota LLM response: {response_text!r}", flush=True)
        else:
            print(">>> super().on_message returned None", flush=True)
            
        return response

    # ------------------------------------------------------------------
    # Outgoing assistant response
    # ------------------------------------------------------------------
    async def on_response(self, response, context):
        log_to_file(response.text, "TOYOTA ASSISTANT RESPONSE")
        return await super().on_response(response, context)

    # ------------------------------------------------------------------
    # Helper methods for Toyota-specific functionality
    # ------------------------------------------------------------------
    def _is_greeting(self, text):
        """Check if the message is an Arabic greeting"""
        greetings = ["هلا", "سلام عليكم", "السلام عليكم", "مرحبا", "أهلا"]
        return any(greeting in text for greeting in greetings)

    def _is_car_image_request(self, text):
        """Check if user is requesting car images"""
        image_keywords = ["أبي أشوف صورة", "صورة السيارة", "شكل السيارة", "show me", "image", "picture"]
        return any(keyword in text.lower() for keyword in image_keywords)

    def _is_location_request(self, text):
        """Check if user is requesting location information"""
        location_keywords = ["وين", "أقرب معرض", "مركز الخدمة", "موقع", "عنوان", "where", "location", "address"]
        return any(keyword in text.lower() for keyword in location_keywords)

    async def _handle_client_identification(self, message_text, context):
        """Handle client identification using phone number"""
        try:
            # Extract phone number from participant identity or room metadata
            phone_number = self._extract_phone_from_call_system()
            
            if not phone_number:
                context.add_system_message("Phone number not available from call system")
                return "wwwwwwwww"

            # ✅ invoke tool via RunContext (following BurgerKing pattern)
            result = await context.run_tool("get_client_data", phone_number=phone_number)

            # ✅ check structured result
            if result and result.get("status") == "success":
                data = result.get("data")
                if data and "لم يتم العثور على بيانات العميل" not in str(data):
                    self.client_data = data
                    self.client_phone = phone_number
                    context.add_system_message(f"Client data found for {phone_number}")
                else:
                    context.add_system_message("New client - need to collect registration data")
            else:
                context.add_system_message("Failed to fetch client data")

        except Exception as e:
            print(f"Error handling client identification: {e}")

    def _extract_phone_from_call_system(self):
        """Extract phone number from caller identity (participant identity)"""
        try:
            if not self.participant_identity:
                print("No participant identity available")
                return "EEEEEEEEEEEE"
            
            print(f"Extracting phone from participant identity: {self.participant_identity}")
            
            # Method 1: Direct phone number as participant identity
            if self.participant_identity.startswith('+965'):
                print(f"Found Kuwait phone number: {self.participant_identity}")
                return self.participant_identity
            
            # Method 2: Look for Kuwait phone number pattern in identity string
            import re
            phone_pattern = r'\+965\d{8}'
            match = re.search(phone_pattern, self.participant_identity)
            if match:
                phone_number = match.group()
                print(f"Extracted phone number from identity: {phone_number}")
                return phone_number
            
            # Method 3: Handle cases where identity might be just the number without +965
            # Check if identity is 8 digits (Kuwait mobile number without country code)
            if re.match(r'^\d{8}$', self.participant_identity):
                phone_number = f"+965{self.participant_identity}"
                print(f"Added country code to number: {phone_number}")
                return phone_number
            
            # Method 4: Handle cases with different formatting
            # Remove any non-digit characters and check if it's a valid Kuwait number
            digits_only = re.sub(r'\D', '', self.participant_identity)
            if digits_only.startswith('965') and len(digits_only) == 11:
                phone_number = f"+{digits_only}"
                print(f"Formatted phone number: {phone_number}")
                return phone_number
            elif len(digits_only) == 8:
                phone_number = f"+965{digits_only}"
                print(f"Added country code to digits: {phone_number}")
                return phone_number
            
            print(f"Could not extract valid Kuwait phone number from: {self.participant_identity}")
            return "WEX"
            
        except Exception as e:
            print(f"Error extracting phone from caller identity: {e}")
            return "EEWE"

    async def _handle_car_image_request(self, message_text, context):
        """Handle car image requests"""
        try:
            if not self.client_phone:
                return "EEEEEEEE"
            car_name = self._extract_car_name(message_text)
            description = self._get_car_description(car_name)
            # ✅ invoke tool via context (following BurgerKing pattern)
            result = await context.run_tool(
                "send_car_image",
                car_name=car_name,
                description=description or ""  # ✅ ensure str, never None
            )
            context.add_system_message(f"Car image sent: {result}")
        except Exception as e:
            print(f"Error handling car image request: {e}")

    async def _handle_location_request(self, message_text, context):
        """Handle location requests"""
        try:
            if not self.client_phone:
                return
            location_type = self._determine_location_type(message_text)
            # ✅ invoke tool via context (following BurgerKing pattern)
            result = await context.run_tool(
                "send_location",
                location_type=location_type
            )
            context.add_system_message(f"Location sent: {result}")
        except Exception as e:
            print(f"Error handling location request: {e}")

    def _extract_car_name(self, text):
        """Extract car name from user message"""
        car_models = {
            "كورولا": "Corolla",
            "كامري": "Camry", 
            "برادو": "Prado",
            "لاند كروزر": "Land Cruiser",
            "هايلكس": "Hilux",
            "ريز": "Raize",
            "فورتنر": "Fortuner"
        }
        
        for arabic_name, english_name in car_models.items():
            if arabic_name in text or english_name.lower() in text.lower():
                return arabic_name
        
        return "كامري"  # Default

    def _get_car_image_url(self, car_name):
        """Get image URL for specific car model"""
        car_images = {
            "كامري": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/fc96a3af30e07dd8da9ae20762089ce5/960x600_camry_me_2406_213.png",
            "برادو": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/563a9350dad1053e12e4344f708f1ced/ext_2.png",
            "لاند كروزر": "https://images.netdirector.co.uk/gforces-auto/image/upload/w_329,h_219,q_auto,c_fill,f_auto,fl_lossy/auto-client/44c7695bf5cf4abdb7ce4beec883486d/land_cruiser.png"
        }
        
        return car_images.get(car_name, car_images["كامري"])

    def _get_car_description(self, car_name):
        """Get description for specific car model"""
        descriptions = {
            "كامري": "سيارة سيدان تنفيذية فاخرة مع تقنيات متقدمة وراحة استثنائية",
            "برادو": "سيارة دفع رباعي فاخرة مثالية للعائلات والرحلات الطويلة",
            "لاند كروزر": "سيارة دفع رباعي فاخرة بحجم كامل مع قدرات استثنائية على الطرق الوعرة"
        }
        
        return descriptions.get(car_name, "سيارة تويوتا عالية الجودة والموثوقية")

    def _determine_location_type(self, text):
        """Determine what type of location user is asking for"""
        if "معرض" in text or "showroom" in text.lower():
            return "showroom"
        elif "خدمة" in text or "service" in text.lower():
            return "service"
        else:
            return "showroom"  # Default

# ──────────────────────────
# Entrypoint
# ──────────────────────────
async def entrypoint(ctx: JobContext):
    session = None
    try:
        session_id = str(uuid.uuid4())
        print(f"\n\n=== TOYOTA SESSION STARTING: {session_id} ===\n\n")

        # LLM client
        llm_client = openai.LLM(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            temperature=0.2,
        )

        # Connect to the room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        participant = await ctx.wait_for_participant()
        print(f"\n\n=== PARTICIPANT CONNECTED: {participant.identity} ===\n\n")

        # Handle disconnects
        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(p):
            print(f"\n\n=== PARTICIPANT DISCONNECTED: {p.identity} ===\n\n")
            async def _cleanup_and_shutdown():
                if session:
                    await session.aclose()
                ctx.shutdown(reason="participant_disconnected")

            asyncio.create_task(_cleanup_and_shutdown())

        
        

        # Build session
        session = AgentSession(
            vad=ctx.proc.userdata["vad"],
            stt=azure.STT(
                speech_key=os.getenv("AZURE_SPEECH_KEY"),
                speech_region=os.getenv("AZURE_SPEECH_REGION"),
                language="ar-KW",
                # sample_rate=16000,
                # segmentation_silence_timeout_ms=300,
            ),
            llm=llm_client,
            tts=elevenlabs.TTS(
                api_key=os.getenv("ELEVEN_API_KEY"),
                model="eleven_multilingual_v2",
                voice_id="nU39tgunJTx5rQiBJfzc",  # Arabic voice
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.6,
                    speed=1,
                ),
            ),
        )

        # Tools + agent
        toyota_tools = ToyotaTools(session=session)
        agent = ToyotaKuwaitAgent(
            session_id=session_id,
            participant_identity=participant.identity,
        )
        await agent.update_tools([
            toyota_tools.get_client_data,
            toyota_tools.create_client,
            toyota_tools.get_vehicle_data,
            toyota_tools.send_car_image,
            toyota_tools.send_location,
            toyota_tools.create_service_ticket,
            toyota_tools.get_service_tickets,
        ])

        # Start session
        await session.start(
            room=ctx.room,
            agent=agent,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
                close_on_disconnect=False,
            ),
            room_output_options=RoomOutputOptions(
                # transcription_enabled=True,
            ),
        )
        print("Toyota session started successfully")

        # Greeting
        greeting = "السلام عليكم ورحمة الله وبركاته، حياك الله في تويوتا الكويت، معك فاطمة، كيف أقدر أخدمك اليوم؟"
        log_to_file(greeting, "INITIAL GREETING")
        await session.say(greeting, allow_interruptions=False)

        # ⬇️ Keep session alive until shutdown
        await asyncio.Event().wait()

    except Exception as e:
        print(f"Unexpected error in Toyota entrypoint: {e}")
        logger.error(f"Unexpected error in Toyota entrypoint: {e}", exc_info=True)
        await ctx.shutdown("unexpected_error")

    # ✅ Cleanup hook
    async def _log_usage():
        print("\n\n=== TOYOTA SESSION ENDING ===\n\n")
        if session:
            try:
                await session.aclose()
                print("Toyota session stopped successfully")
            except Exception as e:
                print(f"Error stopping Toyota session: {e}")
        import gc
        gc.collect()
        print("Garbage collection performed")

    ctx.add_shutdown_callback(_log_usage)



# ──────────────────────────
# Toyota System prompt
# ──────────────────────────
_TOYOTA_SYSTEM_PROMPT = """
أنت فاطمة، مساعدة افتراضية ماهرة لتويوتا الكويت (محمد ناصر الساير وأولاده). أنت مساعدة صوتية ذكية تعمل عبر المكالمات الهاتفية لخدمة العملاء. دورك هو تقديم ردود موجزة وفعالة للعملاء خلال رحلة مبيعات وخدمة السيارات بضيافة كويتية أصيلة.

## 🎯 قواعد المكالمات الصوتية - VOICE CALL OPTIMIZATION 🎯

### 🔴 قواعد الردود الصوتية الإجبارية:
- **احتفظ بالردود قصيرة جداً - بحد أقصى 2-3 أسطر**
- **تكلم بوضوح ومباشرة للنقطة**
- **تجنب القوائم الطويلة أو التفاصيل المعقدة**
- **استخدم جمل بسيطة وواضحة**
- **قدم معلومة واحدة رئيسية في كل رد**

## ⚠️ قواعد اللغة الإجبارية - CRITICAL LANGUAGE RULES ⚠️

### 🔴 القاعدة الذهبية الأولى: مطابقة لغة المستخدم بدقة 100%
**إذا تكلم المستخدم بالعربية → رد بالعربية فقط**
**إذا تكلم المستخدم بالإنجليزية → رد بالإنجليزية فقط**
**لا تخلط اللغات أبداً في رد واحد - هذا ممنوع منعاً باتاً**

### 🔴 أمثلة إجبارية للمطابقة اللغوية:

**مثال 1 - المستخدم يتكلم عربي:**
المستخدم: "السلام عليكم، أبي أشوف سيارة كامري"
فاطمة: "وعليكم السلام ورحمة الله وبركاته، حياك الله! الكامري سيارة ممتازة. شرايك نحجزلك موعد لتشوفها؟"

**مثال 2 - المستخدم يتكلم إنجليزي:**
المستخدم: "Hello, I want to see the Camry"
فاطمة: "Hello! Welcome to Toyota Kuwait. The Camry is an excellent choice. Would you like to schedule a test drive?"

**مثال 3 - المستخدم يغير اللغة:**
المستخدم: "شكراً، بس أبي أسأل عن السعر" (عربي)
فاطمة: "على الرحب والسعة! سعر الكامري يبدأ من 7,500 دينار. تبي تفاصيل أكثر؟" (عربي)

المستخدم: "Can you send me the brochure?" (إنجليزي)
فاطمة: "Of course! I'll send you the Camry brochure right away. What's your WhatsApp number?" (إنجليزي)

### 🔴 قواعد كشف اللغة الصارمة:

**العربية - مؤشرات:**
- أحرف عربية: ا، ب، ت، ث، ج، ح، خ، د، ذ، ر، ز، س، ش، ص، ض، ط، ظ، ع، غ، ف، ق، ك، ل، م، ن، ه، و، ي
- كلمات عربية: السلام، مرحبا، أبي، شلون، شرايك، إنشالله، يعطيك العافية
- أرقام عربية: ١، ٢، ٣، ٤، ٥، ٦، ٧، ٨، ٩، ٠

**الإنجليزية - مؤشرات:**
- أحرف لاتينية: A-Z, a-z
- كلمات إنجليزية: Hello, Hi, Thank you, Please, Can you, I want, How much
- أرقام إنجليزية: 1, 2, 3, 4, 5, 6, 7, 8, 9, 0

### 🔴 أمثلة ممنوعة (لا تفعل هذا أبداً):
❌ المستخدم: "أبي أشوف الكامري"
❌ فاطمة: "حياك الله! The Camry is available for viewing" (خلط اللغات)

❌ المستخدم: "Hello, I want the Camry"
❌ فاطمة: "Welcome! الكامري متوفرة للمشاهدة" (خلط اللغات)

### 🔴 حالات خاصة:
- **أسماء السيارات**: استخدم الاسم المناسب للغة
  - عربي: "كامري، كورولا، برادو، لاند كروزر"
  - إنجليزي: "Camry, Corolla, Prado, Land Cruiser"

- **الأرقام والأسعار**: 
  - عربي: "سبعة آلاف وخمسمائة دينار"
  - إنجليزي: "Seven thousand five hundred dinars"

### 🔴 اختبار سريع للمطابقة:
قبل كل رد، اسأل نفسك:
1. ما هي لغة رسالة المستخدم؟
2. هل ردي بنفس اللغة 100%؟
3. هل يوجد أي خلط في اللغات؟

## الهوية الأساسية والسلوك
- مهنية ودافئة، تعكس الضيافة الكويتية الحقيقية
- خبيرة مبيعات سيارات مع معرفة عميقة بمنتجات تويوتا
- خبيرة خدمة عملاء مع قدرات تكامل CRM
- حلالة مشاكل تتحمل مسؤولية قضايا العملاء
- موجهة نحو الحلول مع نهج خيارات متعددة
- مركزة على الاحتفاظ بالعملاء مع بناء علاقات طويلة المدى

## قواعد اللغة والتواصل الصوتي
- **احتفظ بجميع الردود قصيرة جداً - بحد أقصى 2-3 أسطر للمكالمات**
- **تكلم بوضوح ومباشرة، تجنب التفاصيل المعقدة**
- **استخدم جملة واحدة رئيسية لكل رد**
- **تجنب القوائم الطويلة في المكالمات الصوتية**
- **قدم الخيارات بشكل مبسط ومختصر**
- **طابق لغة المستخدم بدقة 100% - هذا إجباري**

## تعبيرات كويتية ثقافية
**التحيات والمجاملات العربية:**
- "حياك الله" (أهلاً وسهلاً)
- "وعليكم السلام ورحمة الله وبركاته"
- "يعطيك العافية" (شكراً/أحسنت)
- "الله يعافيك" (رد على يعطيك العافية)
- "جزاكم الله خير" (جزاك الله خيراً)
- "على الرحب والسعة" (أهلاً وسهلاً)
- "تسلم" (شكراً/بارك الله فيك)
- "معنا ما راح تعاني" (معنا لن تعاني)

**تعبيرات الأعمال الكويتية:**
- "شرايك؟" (ما رأيك؟)
- "شلونك؟" (كيف حالك؟)
- "شنو رايك؟" (ما رأيك؟)
- "إنشالله" (إن شاء الله)
- "توكل على الله" (توكل على الله)
- "الله يوفقك" (وفقك الله)

## مجموعة سيارات تويوتا مع الصور
### سيدان
- **كورولا (Corolla)**: سيدان عائلية، موثوقة
- **كامري (Camry)**: سيدان تنفيذية
- **كراون (Crown)**: سيدان هجين فاخر

### سيارات رياضية
- **GR86**: كوبيه رياضية
- **سوبرا (Supra)**: سيارة رياضية فاخرة

### SUVs وكروس أوفر
- **ريز (Raize)**: كروس أوفر مدمج
- **كورولا كروس (Corolla Cross)**: كروس أوفر هجين
- **برادو (Prado)**: دفع رباعي فاخر
- **لاند كروزر (Land Cruiser)**: دفع رباعي فاخر بحجم كامل
- **فورتنر (Fortuner)**: SUV قوي

### MPVs
- **فيلوز (Veloz)**: MPV مدمج 7 مقاعد
- **إينوفا (Innova)**: MPV واسع 8 مقاعد

### المركبات التجارية
- **هايلكس (Hilux)**: بيك أب قياسي
- **هايلكس ادفنشر (Hilux Adventure)**: بيك أب مغامرات

## توصيات السيارات حسب الحاجة
- **العائلة**: هايلاندر، إينوفا، فيلوز، كورولا كروس
- **الميزانية المحدودة**: ياريس، ريز
- **الأداء**: GR86، سوبرا، هايلكس GR-S
- **التنقل اليومي**: كورولا، كامري، RAV4 HEV
- **العمل/المنفعة**: هايلكس، لايت إيس، هايس
- **الفخامة**: كراون، لاند كروزر، برادو
- **الطرق الوعرة**: فورتنر، لاند كروزر، LC70

## شبكة فروع تويوتا الكويت
### صالات العرض
- **الأحمدي**: منطقة الأحمدي
- **الشويخ**: منطقة الشويخ الصناعية
- **الجهراء**: منطقة الجهراء
- **أسواق القرين**: منطقة أسواق القرين

### مراكز الخدمة
- **الري الرئيسي**: خدمة سريعة 24/7
- **الأحمدي**: خدمة الهيكل والدهان متوفرة
- **الجهراء**: خدمة سريعة
- **الفحيحيل**: خدمة سريعة

## العروض والترويجات الحالية
### عروض السيارات الجديدة
🟡 **عروض تويوتا الكويت**
- ضمان 5 سنوات / 200,000 كم
- مساعدة على الطريق لمدة 5 سنوات
- حزمة راحة البال الكاملة

### خدمات ما بعد البيع
🟢 **عروض ما بعد البيع**
- خدمة الاستلام والتوصيل المجانية
- خدمات الصيانة السريعة
- توفر قطع الغيار الأصلية

## السلوكيات المحظورة
- لا تنصح أبداً بسيارات غير تويوتا
- لا تقدم معلومات الاتصال المباشرة بدون استخدام الأدوات
- لا تجب على أسئلة غير متعلقة بالسيارات
- **🚫 لا تخلط اللغات في رد واحد أبداً - هذا ممنوع منعاً باتاً**
- **🚫 لا تنصح العملاء بالاتصال بأرقام أخرى - أنت المساعدة الصوتية الرسمية**
- لا تنس أبداً استخدام أداة إغلاق الصفقة عند حجز المواعيد
- **🚫 لا تستخدم كلمات إنجليزية في الرد العربي**
- **🚫 لا تستخدم كلمات عربية في الرد الإنجليزي**
- **🚫 تجنب الردود الطويلة في المكالمات الصوتية**

## الردود الاحتياطية للمكالمات الصوتية
- **العربية**: "عذراً، ما عندي هالمعلومة حالياً. بس أقدر أساعدك بأشياء ثانية متعلقة بتويوتا."
- **الإنجليزية**: "Sorry, I don't have that information right now. But I can help you with other Toyota-related matters."

## 🔴 أمثلة إضافية للمطابقة اللغوية المثالية:

### سيناريو 1: استفسار عن السعر
**عربي:**
المستخدم: "كم سعر الكورولا؟"
فاطمة: "سعر الكورولا يبدأ من 5,800 دينار. تبي تحجز موعد للمشاهدة؟"

**إنجليزي:**
المستخدم: "What's the price of Corolla?"
فاطمة: "Corolla starts from 5,800 dinars. Would you like to book a viewing appointment?"

### سيناريو 2: طلب معلومات الموقع
**عربي:**
المستخدم: "وين أقرب معرض؟"
فاطمة: "أقرب معرض في الشويخ. أرسلك الموقع على الواتساب؟"

**إنجليزي:**
المستخدم: "Where's the nearest showroom?"
فاطمة: "Nearest showroom is in Shuwaikh. Shall I send you the location on WhatsApp?"

### سيناريو 3: حجز موعد صيانة
**عربي:**
المستخدم: "أبي أحجز موعد صيانة"
فاطمة: "إنشالله! أي يوم يناسبك؟ عندنا مواعيد متاحة الأسبوع الجاي."

**إنجليزي:**
المستخدم: "I want to book a service appointment"
فاطمة: "Sure! Which day works for you? We have slots available next week."

### سيناريو 4: شكوى أو مشكلة
**عربي:**
المستخدم: "عندي مشكلة بالسيارة"
فاطمة: "معذرة على الإزعاج. شنو المشكلة بالضبط؟ راح أساعدك أحلها."

**إنجليزي:**
المستخدم: "I have a problem with my car"
فاطمة: "Sorry for the inconvenience. What exactly is the problem? I'll help you resolve it."

## 🎯 أمثلة إضافية للمكالمات الصوتية - VOICE CALL EXAMPLES 🎯

### مثال 1: رد مختصر للاستفسار العام
**عربي:**
المستخدم: "أبي أعرف عن سيارات تويوتا"
فاطمة: "حياك الله! عندنا مجموعة واسعة. شنو نوع السيارة اللي تدورها؟"

**إنجليزي:**
المستخدم: "Tell me about Toyota cars"
فاطمة: "Welcome! We have a wide range. What type of car are you looking for?"

### مثال 2: تبسيط المعلومات المعقدة
**عربي:**
المستخدم: "شنو الفرق بين الكامري والكورولا؟"
فاطمة: "الكامري أكبر وأفخم، والكورولا اقتصادية أكثر. أي وحدة تناسب احتياجاتك؟"

**إنجليزي:**
المستخدم: "What's the difference between Camry and Corolla?"
فاطمة: "Camry is larger and more luxurious, Corolla is more economical. Which suits your needs?"

### مثال 3: توجيه سريع للعمل
**عربي:**
المستخدم: "أبي أحجز تست درايف"
فاطمة: "ممتاز! أي سيارة تبي تجربها؟ وأي يوم يناسبك؟"

**إنجليزي:**
المستخدم: "I want to book a test drive"
فاطمة: "Excellent! Which car would you like to try? And which day works for you?"

## التذكيرات النهائية للمكالمات الصوتية
- **احتفظ بالردود قصيرة جداً - بحد أقصى 2-3 أسطر للمكالمات**
- **تكلم بوضوح ومباشرة، تجنب التعقيد**
- **استخدم التعبيرات الكويتية بطبيعية (في الردود العربية فقط)**
- **قدم حلول مبسطة ومباشرة**
- **🔴 طابق لغة المستخدم بدقة 100% - هذا الأهم**
- **اجمع تفاصيل العميل بشكل مختصر وفعال**
- **استخدم أداة إغلاق الصفقة عند الحجز**
- **ابن العلاقات من خلال الاتصال الثقافي الأصيل**
- **🎯 تذكر: أنت مساعدة صوتية - اجعل كل رد واضح ومفيد للمكالمة**

### 🔴 تذكير أخير - قواعد اللغة الحديدية:
1. **اقرأ رسالة المستخدم بعناية**
2. **حدد اللغة (عربي أم إنجليزي)**
3. **رد بنفس اللغة 100%**
4. **لا تخلط اللغات أبداً**
5. **تأكد من ردك قبل الإرسال**

عندما يطلب العميل رؤية صور السيارات، استخدم أداة إرسال صور السيارات لإرسال الصور عبر الواتساب.
عندما يطلب العميل معلومات الموقع، استخدم أداة إرسال الموقع لإرسال تفاصيل الفروع.
"""

# ──────────────────────────
# Main
# ──────────────────────────
if __name__ == "__main__":
    # print(f"Using ElevenLabs TTS with API key: {os.getenv('ELEVEN_API_KEY')}")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )

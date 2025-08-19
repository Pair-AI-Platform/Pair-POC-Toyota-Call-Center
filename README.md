# Toyota Kuwait LiveKit Voice Assistant

A sophisticated voice assistant for Toyota Kuwait built with LiveKit that integrates with CRM systems and can send car images via WhatsApp.

## Features

- **Voice Interaction**: Arabic (Kuwaiti dialect) speech-to-text and text-to-speech
- **CRM Integration**: Connects to Toyota Kuwait CRM for client and vehicle data
- **WhatsApp Integration**: Sends car images and location information via WhatsApp
- **RAG Support**: Vector database for Toyota knowledge base
- **Real-time Communication**: Built on LiveKit for low-latency voice interactions

## Architecture

The agent is built using:
- **LiveKit Agents Framework**: For real-time voice communication
- **Azure Speech Services**: For Arabic STT (Speech-to-Text)
- **ElevenLabs**: For Arabic TTS (Text-to-Speech) 
- **OpenAI GPT-4**: For natural language understanding and generation
- **Vector Database**: For Toyota knowledge base retrieval
- **WhatsApp Business API**: For sending images and locations

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required credentials:
- **LiveKit**: URL, API Key, and Secret from your LiveKit project
- **Azure Speech**: Key and Region from Azure portal
- **ElevenLabs**: API Key and Voice ID for Arabic voice
- **OpenAI**: API Key for GPT-4 access

### 3. Toyota Tools

The following tools are already configured:
- `get_client_data_tool.py`: Retrieve client information from CRM
- `create_client_tool.py`: Register new clients
- `get_vehicle_data_tool.py`: Get vehicle information and send images
- `send_car_image_tool.py`: Send car images via WhatsApp
- `send_location_tool.py`: Send branch locations via WhatsApp
- `create_service_ticket_tool.py`: Create service appointments
- `get_service_tickets_tool.py`: Check service status

## Usage

### Running the Agent

```bash
python toyota_livekit_agent.py
```

The agent will:
1. Connect to your LiveKit room
2. Wait for participants to join
3. Greet users in Arabic: "السلام عليكم ورحمة الله وبركاته، حياك الله في تويوتا الكويت"
4. Handle voice interactions with Toyota-specific functionality

### Key Capabilities

#### Client Identification
- Automatically identifies returning clients using phone numbers
- Registers new clients when needed
- Personalizes interactions based on client data

#### Car Image Sharing
When users ask to see car images:
```
User: "أبي أشوف صورة الكامري"
Agent: Sends Camry image via WhatsApp with description
```

#### Location Sharing
When users ask for locations:
```
User: "وين أقرب معرض؟"
Agent: Sends nearest showroom location via WhatsApp
```

#### Service Management
- Create service appointments
- Check service status
- Access vehicle history

## Toyota Vehicle Lineup

The agent knows about all Toyota models:

### Sedans
- كورولا (Corolla)
- كامري (Camry) 
- كراون (Crown)

### SUVs
- ريز (Raize)
- كورولا كروس (Corolla Cross)
- برادو (Prado)
- لاند كروزر (Land Cruiser)
- فورتنر (Fortuner)

### Commercial
- هايلكس (Hilux)
- هايلكس ادفنشر (Hilux Adventure)

### MPVs
- فيلوز (Veloz)
- إينوفا (Innova)

## Configuration

### Voice Settings
- **Language**: Arabic (Kuwaiti - ar-KW)
- **TTS Model**: ElevenLabs Flash v2.5
- **Voice Stability**: 0.5
- **Similarity Boost**: 0.6

### VAD (Voice Activity Detection)
- **Activation Threshold**: 0.45
- **Min Speech Duration**: 0.15s
- **Min Silence Duration**: 0.35s

## Logging

The agent logs all interactions to:
- `toyota_llm_responses.txt`: Complete conversation logs
- Console output with structured logging

## Error Handling

- Graceful participant disconnection handling
- Automatic session cleanup
- Fallback responses for unknown queries
- WhatsApp API error handling

## Customization

### Adding New Car Models
Update the car mappings in `toyota_livekit_agent.py`:

```python
car_models = {
    "نموذج جديد": "New Model",
    # Add more models
}

car_images = {
    "نموذج جديد": "https://image-url.com/new-model.png",
    # Add more image URLs
}
```

### Modifying System Prompt
Edit `_TOYOTA_SYSTEM_PROMPT` in `toyota_livekit_agent.py` to adjust:
- Personality and tone
- Business rules
- Response formats
- Cultural expressions

## Troubleshooting

### Common Issues

1. **Audio Quality**: Check VAD settings and network connection
2. **TTS Errors**: Verify ElevenLabs API key and voice ID
3. **STT Issues**: Confirm Azure Speech credentials and region
4. **WhatsApp Failures**: Check access token and phone number ID

### Debug Mode
Enable detailed logging by setting log level to DEBUG:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Security

- Environment variables for all sensitive credentials
- No hardcoded API keys in source code
- Secure token handling for CRM and WhatsApp APIs

## Support

For issues or questions:
- Check logs in `toyota_llm_responses.txt`
- Verify all environment variables are set
- Ensure LiveKit room is accessible
- Test individual tools separately

## License

This project is proprietary to Toyota Kuwait (Mohamed Naser Al-Sayer & Sons).

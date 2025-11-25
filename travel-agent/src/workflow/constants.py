# LLM Agentic Goal shared across all workflows
AGENTIC_GOAL = (
    "You are a travel planning assistant. Your goal is to help users plan their trips by searching for flights, booking accommodations, and creating personalized itineraries. "
    "You should ask clarifying questions if information is missing, suggest optimal travel options, and provide detailed, actionable recommendations. "
    "Always respond in a helpful, friendly, and proactive manner, aiming to make the user's travel experience smooth and enjoyable."
)

# Shared workflow configuration
DEFAULT_LLM_MODEL = "gpt-4-1106-preview"
DEFAULT_TEMPERATURE = 0.7
MAX_RETRIES = 3

# Default values for fallback scenarios
DEFAULT_AIRLINE = "LLM-Air"
DEFAULT_FLIGHT_NUMBER = "LLM123"
DEFAULT_FLIGHT_PRICE = 500
DEFAULT_HOTEL_NAME = "Echo Hotel"
DEFAULT_HOTEL_PRICE_PER_NIGHT = 100
DEFAULT_HOTEL_TOTAL_PRICE = 400

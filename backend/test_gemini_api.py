import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Load API key from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("[ERROR] No GOOGLE_API_KEY found in .env file.")
    exit(1)

print("Testing Gemini API...")
try:
    # Initialize the LLM with the model used in config.py
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro", # The model configured in your app
        google_api_key=api_key,
        temperature=0.1
    )
    
    # Send a simple test message
    response = llm.invoke([HumanMessage(content="Hello! Are you working? Please reply with a short 'Yes, I am working!'.")])
    
    print("\n[SUCCESS] The Gemini API is working perfectly!")
    print(f"API Response: {response.content}")

except Exception as e:
    print("\n[FAILED] There was an error connecting to the Gemini API.")
    print(f"Error details: {str(e)}")

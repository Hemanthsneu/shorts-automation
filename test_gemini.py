
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {api_key[:5]}...{api_key[-5:]}" if api_key else "No API Key found")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash") # Using a more standard model for test

try:
    response = model.generate_content("Say hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

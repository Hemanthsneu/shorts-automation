import sys
from pathlib import Path

# Important: make sure we can import config
sys.path.insert(0, str(Path(__file__).parent))
import config

from google import genai
from google.genai import types

def generate_logo():
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    prompt = "Generate a sleek, high-contrast minimal profile picture logo featuring a glowing neon cyan and purple stylized geometric eye on a pitch-black background. Cyberpunk aesthetic, clean vector style, perfect circle composition, no text. Square aspect ratio."
    print("🎨 Generating Logo...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        ),
    )
    
    logo_path = Path("output/assets/channel_logo.jpg")
    logo_path.parent.mkdir(parents=True, exist_ok=True)
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            logo_path.write_bytes(part.inline_data.data)
            break
    print(f"✅ Logo generated: {logo_path}")

def generate_banner():
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    prompt = "Generate a dark cinematic abstract art background with glowing neon circuitry, data streams, and geometric shapes in deep space black, neon cyan, and purple colors. Cyberpunk aesthetic, 16:9 aspect ratio, high resolution, no text. YouTube banner style."
    print("🎨 Generating Banner...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        ),
    )
    
    banner_path = Path("output/assets/channel_banner.jpg")
    banner_path.parent.mkdir(parents=True, exist_ok=True)
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            banner_path.write_bytes(part.inline_data.data)
            break
    print(f"✅ Banner generated: {banner_path}")

if __name__ == "__main__":
    generate_logo()
    generate_banner()

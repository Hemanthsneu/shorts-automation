import sys
import subprocess
from pathlib import Path

# Important: make sure we can import config
sys.path.insert(0, str(Path(__file__).parent))
import config

from google import genai
from google.genai import types

def generate_banner():
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    # Updated prompt to specifically ask for the text rendering
    prompt = (
        "A cinematic YouTube channel banner. In the center, bright, bold, large clear neon text that reads exactly: 'THE UNSEEN FILES'. "
        "Just below it, slightly smaller clear text that reads: 'MIND-BLOWING FACTS IN 60 SECONDS'. "
        "The background should be dark cinematic abstract art with glowing neon circuitry, data streams, "
        "and geometric shapes in deep space black, neon cyan, and purple colors. Cyberpunk aesthetic, 16:9 aspect ratio."
    )
    
    print("🎨 Generating Banner with text via Gemini...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        ),
    )
    
    banner_raw_path = Path("output/assets/channel_banner_raw.jpg")
    banner_path = Path("output/assets/channel_banner.jpg")
    banner_path.parent.mkdir(parents=True, exist_ok=True)
    
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            banner_raw_path.write_bytes(part.inline_data.data)
            break
            
    if not banner_raw_path.exists():
        print("❌ Failed to extract image data from response.")
        return

    print(f"✅ Raw Banner generated: {banner_raw_path}")
    print("📏 Resizing to exactly 1024x576 using FFmpeg...")
    
    # Use FFmpeg to rigidly scale the image to the exact 1024x576 requirement
    cmd = [
        "ffmpeg", "-y", 
        "-i", str(banner_raw_path), 
        "-vf", "scale=1024:576", 
        str(banner_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Clean up the raw file
    banner_raw_path.unlink()
    
    print(f"✅ Final Banner (1024x576) ready: {banner_path}")

if __name__ == "__main__":
    generate_banner()

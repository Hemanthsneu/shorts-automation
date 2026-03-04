import json
import os
from pathlib import Path
import config
import google.generativeai as genai

genai.configure(api_key=config.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")

print("🎨 Generating Logo...")
logo_res = model.generate_content(
    "A sleek, high-contrast minimal profile picture logo featuring a glowing neon cyan and purple stylized geometric eye on a pitch-black background. Cyberpunk aesthetic, clean vector style, perfect circle composition, no text.",
    generation_config=genai.GenerationConfig(
        response_mime_type="image/jpeg",
        aspect_ratio="1:1"
    )
)
logo_path = Path("output/assets/channel_logo.jpg")
logo_path.parent.mkdir(parents=True, exist_ok=True)
with open(logo_path, "wb") as f:
    f.write(logo_res.candidates[0].content.parts[0].inline_data.data)
print(f"✅ Logo generated: {logo_path}")

print("🎨 Generating Banner...")
banner_res = model.generate_content(
    "A dark cinematic abstract art background with glowing neon circuitry, data streams, and geometric shapes in deep space black, neon cyan, and purple colors. Cyberpunk aesthetic, high resolution, no text.",
    generation_config=genai.GenerationConfig(
        response_mime_type="image/jpeg",
        aspect_ratio="16:9"
    )
)
banner_path = Path("output/assets/channel_banner.jpg")
with open(banner_path, "wb") as f:
    f.write(banner_res.candidates[0].content.parts[0].inline_data.data)
print(f"✅ Banner generated: {banner_path}")

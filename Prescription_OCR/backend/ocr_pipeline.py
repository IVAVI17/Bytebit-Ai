
import os
import io
import base64
import requests
import json
from PIL import Image

def process_image(image_bytes):


    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    # Add a white background
    white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white_bg.paste(image, (0, 0), image)
    rgb_image = white_bg.convert("RGB")
    # Save the image being sent to the LLM for inspection
    rgb_image.save("sent_to_llm.png")
    buffered = io.BytesIO()
    rgb_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    prompt = (
        "Extract and return only the exact text that appears in the image. "
        "Do not add, interpret, or format anything. Output only the raw recognized text, exactly as it is written in the image, in the LLM output I dont want any extra things or text just what is mentioned in the text"
    )

    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    payload = {
        "model": "accounts/fireworks/models/kimi-k2p5",
        "max_tokens": 4096,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.6,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}]}
        ]
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('FIREWORKS_API_KEY', 'fw_WUbj2iSi6bqasaKG92Et8n')}"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    try:
        result = response.json()
        llm_output = result["choices"][0]["message"]["content"]
    except Exception:
        llm_output = response.text
    print("LLM Output:\n", llm_output)
    return {
        "llm_output": llm_output
    }
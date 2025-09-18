
import os
import io
import time
import uuid
import base64
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ====== Configuration ======
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Hugging Face Inference API token
# Recommended text-to-image model (fast and reliable on Inference API)
HF_MODEL = os.getenv("HF_MODEL", "stabilityai/stable-diffusion-2-1")  

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
GEN_DIR = BASE_DIR / "generated"

app = Flask(__name__, static_folder="static", template_folder="templates")

# Ensure folders exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GEN_DIR.mkdir(parents=True, exist_ok=True)

def save_image_bytes(img_bytes: bytes, prefix: str = "gen") -> str:
    """Save image bytes to the generated folder and return filename."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{prefix}_{ts}_{uuid.uuid4().hex[:8]}.png"
    outpath = GEN_DIR / filename
    with open(outpath, "wb") as f:
        f.write(img_bytes)
    return filename

def call_hf_txt2img(prompt: str, guidance: float = 7.5, num_inference_steps: int = 30, width: int = 768, height: int = 960):
    """Call Hugging Face Inference API for text-to-image. Returns image bytes or raises Exception."""
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is missing. Set it in your .env file.")

    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Accept": "image/png",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "guidance_scale": guidance,
            "num_inference_steps": num_inference_steps,
            "width": width,
            "height": height
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    if resp.status_code != 200:
        try:
            raise RuntimeError(f"HF API error {resp.status_code}: {resp.json()}")
        except Exception:
            raise RuntimeError(f"HF API error {resp.status_code}: {resp.text}")
    return resp.content

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generated/<path:filename>")
def serve_generated(filename):
    return send_from_directory(GEN_DIR, filename, as_attachment=False)

@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)

@app.route("/api/images", methods=["GET"])
def list_images():
    imgs = []
    for p in sorted(GEN_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True):
        imgs.append({
            "filename": p.name,
            "url": f"/generated/{p.name}",
            "mtime": int(p.stat().st_mtime)
        })
    return jsonify({"images": imgs})

@app.route("/api/upload", methods=["POST"])
def upload_image():
    """Save uploaded image (for preview/reference only in MVP)."""
    if "image" not in request.files:
        return jsonify({"error": "No file part named 'image'"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    ext = os.path.splitext(file.filename)[1].lower() or ".png"
    fname = f"upload_{datetime.now().strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    save_path = UPLOAD_DIR / fname
    file.save(save_path)
    return jsonify({"ok": True, "filename": fname, "url": f"/uploads/{fname}"})

@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Generate a profile image from style + composition.
    MVP: text-to-image via HF Inference API (does NOT copy identity from uploaded photo).
    """
    data = request.form or request.json or {}
    style = data.get("style", "clean")
    composition = data.get("composition", "half")
    seed_prompt = data.get("prompt", "").strip()

    # Optional uploaded file (not used for generation in MVP, just stored)
    up_url = None
    if "image" in request.files:
        f = request.files["image"]
        if f.filename:
            ext = os.path.splitext(f.filename)[1].lower() or ".png"
            fname = f"ref_{datetime.now().strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
            dest = UPLOAD_DIR / fname
            f.save(dest)
            up_url = f"/uploads/{fname}"

    STYLE_PRESETS = {
        "clean": "studio headshot, natural soft light, 50mm lens, neutral background, realistic skin texture, subtle makeup, professional portrait photography",
        "film": "cinematic portrait, Kodak Portra 400 film look, soft grain, rim light, shallow depth of field, realistic",
        "corporate": "professional business headshot, blazer, plain background, soft key light, linkedin profile style, realistic",
        "modern": "minimal studio headshot, gradient background, soft rim lighting, high-end magazine style, realistic",
        "colorpop": "vibrant colored backdrop, beauty lighting, studio portrait, realistic",
        "bw": "black and white portrait, high contrast, studio lighting, realistic"
    }

    COMP_PRESETS = {
        "half": "from waist up, centered composition, looking at camera",
        "full": "full-length portrait, balanced composition, standing pose"
    }

    # Build prompt
    composition_text = COMP_PRESETS.get(composition, COMP_PRESETS["half"])
    style_text = STYLE_PRESETS.get(style, STYLE_PRESETS["clean"])

    base_prompt = f"{style_text}, {composition_text}, photorealistic, detailed eyes, natural skin tones, 8k, masterpiece"
    if seed_prompt:
        base_prompt = f"{seed_prompt}, {base_prompt}"

    try:
        img_bytes = call_hf_txt2img(base_prompt)
        filename = save_image_bytes(img_bytes)
        return jsonify({
            "ok": True,
            "image_url": f"/generated/{filename}",
            "prompt_used": base_prompt,
            "ref_image_url": up_url
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    # For local dev
    app.run(host="0.0.0.0", port=5000, debug=True)

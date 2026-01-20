import os
import io
import base64
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from PIL import Image
import urllib.parse

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Style presets with prompt enhancements
STYLES = {
    'fun': {
        'prefix': 'vibrant, playful, colorful, whimsical, cheerful,',
        'suffix': ', trending on artstation, highly detailed, sharp focus'
    },
    'artistic': {
        'prefix': 'artistic masterpiece, elegant composition, professional photography,',
        'suffix': ', award winning, dramatic lighting, 8k uhd, studio quality'
    },
    'realistic': {
        'prefix': 'photorealistic, hyperrealistic, ultra detailed, cinematic,',
        'suffix': ', professional photography, natural lighting, high resolution, dslr'
    }
}

def enhance_prompt(prompt, style='fun'):
    """Enhance user prompt with style-specific improvements"""
    style_data = STYLES.get(style, STYLES['fun'])
    enhanced = f"{style_data['prefix']} {prompt.strip()} {style_data['suffix']}"
    return enhanced.strip()

def generate_image(prompt, model='sdxl'):
    """Generate image using Pollinations.ai (completely free, no API key)"""
    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true"
    
    try:
        response = requests.get(api_url, timeout=120)
        
        if response.status_code == 200:
            # Convert image to base64
            image = Image.open(io.BytesIO(response.content))
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {'success': True, 'image': f'data:image/png;base64,{img_str}'}
        else:
            return {'success': False, 'error': 'Failed to generate image. Please try again.'}
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout - please try again'}
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}

@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('.', 'index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Handle image generation requests"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'Prompt is required'}), 400
        
        user_prompt = data['prompt'].strip()
        if not user_prompt:
            return jsonify({'success': False, 'error': 'Prompt cannot be empty'}), 400
        
        style = data.get('style', 'fun')
        
        # Enhance the prompt
        enhanced_prompt = enhance_prompt(user_prompt, style)
        
        # Generate image
        result = generate_image(enhanced_prompt)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'generator': 'Pollinations.ai (Free & No API Key)'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
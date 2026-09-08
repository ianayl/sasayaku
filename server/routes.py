from flask import Blueprint, request, jsonify
from flask_cors import CORS
from utils import gen_diag

# Define a blueprint for API routes
api_bp = Blueprint('api', __name__)
diag = gen_diag("routes")

@api_bp.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"status": "pong"}), 200

# TODO: Consider making /api/health as a health check instead of ping

@api_bp.route('/api/process-youtube', methods=['POST'])
def process_youtube():
    data = request.get_json()
    youtube_url = data.get('youtube_url')
    # TODO filter links out to make sure they're for youtube
    if not youtube_url:
        diag.warning("Missing youtube_url in request body")
        return jsonify({"status": "error", "message": "Missing youtube_url in request body"}), 400

    diag.info(f"Received YouTube URL: {youtube_url}")
    return jsonify({
        "status": "success",
        "message": "URL received and queued for processing"
    }), 200


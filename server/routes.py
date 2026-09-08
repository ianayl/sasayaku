from flask import Blueprint, request, jsonify
from flask_cors import CORS

import utils
import videos 
from videos import VideoSource

# Define a blueprint for API routes
api_bp = Blueprint('api', __name__)
diag = utils.gen_diag("routes")

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

    youtube_id = utils.extract_youtube_id(youtube_url)
    if youtube_id is None:
        diag.warning("Couldn't extract youtube video id from url")
        return jsonify({"status": "error", "message": "Malformed youtube url"}), 400
    diag.info(f"Received YouTube video {youtube_id} ({youtube_url})")

    videos.init_db()
    # TODO make this API accept tab id
    videos.register_video(youtube_id, VideoSource.YOUTUBE, 7)

    return jsonify({
        "status": "success",
        "message": "URL received and queued for processing"
    }), 200


@api_bp.route('/api/get-video-count', methods=['GET'])
def process_video_count():
    count = videos.get_video_count()
    diag.info(f"Received request for video count: {count}")
    return jsonify({
        "status": "success",
        "count": count
    }), 200


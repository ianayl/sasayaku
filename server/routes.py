from flask import Blueprint, request, jsonify
from flask_cors import CORS
from pathlib import Path

import utils
from utils.config import CONFIG
import videos 
import videos.whisper as whisper
from videos import VideoSource
from workers.taskmaster import taskmaster

# Define a blueprint for API routes
api_bp = Blueprint('api', __name__)
diag = utils.gen_diag("routes")

# TODO: Consider making /api/health as a health check instead of ping

@api_bp.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"status": "pong"}), 200

@api_bp.route('/api/process-youtube', methods=['POST'])
def process_youtube():
    data = request.get_json()
    # TODO filter links out to make sure they're for youtube
    youtube_url = data.get('youtube_url')
    if not youtube_url:
        diag.warning("Missing youtube_url in request body")
        return jsonify({"status": "error", "message": "Missing youtube_url in request body"}), 400

    youtube_id = utils.extract_youtube_id(youtube_url)
    if youtube_id is None:
        diag.warning("Couldn't extract youtube video id from url")
        return jsonify({"status": "error", "message": "Malformed youtube url"}), 400
    diag.info(f"Received YouTube video {youtube_id} ({youtube_url})")

    youtube = VideoSource.YOUTUBE
    db_id = videos.register_video(youtube_id, youtube, 7)

    # Submit to the taskmaster for background processing
    taskmaster.submit_download_task(db_id=db_id, video_id=youtube_id, video_source=youtube)

     # TODO catch RuntimeError and CUDA failures
     # TODO probably return the failure to the client

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


@api_bp.route('/api/get-all-videos', methods=['GET'])
def get_all_videos():
    limit = request.args.get('limit', default=20, type=int)
    offset = request.args.get('offset', default=0, type=int)
    videos_list = videos.get_all_videos(limit=limit, offset=offset)

    # Convert Video objects to dictionaries using their to_dict methods
    results = [v.to_dict() for v in videos_list]

    diag.info(f"Received request for all videos (limit={limit}, offset={offset}): {len(results)}")
    return jsonify({
        "status": "success",
        "count": len(results),
        "videos": results
    }), 200



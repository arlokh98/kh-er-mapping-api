from flask import Blueprint, jsonify
from priority_cache_manager import get_priority_cache
priority_cache = get_priority_cache()
import logging

logger = logging.getLogger(__name__)
status_bp = Blueprint("status", __name__)

@status_bp.route('/status', methods=['GET'])
def status():
    status = priority_cache.get_cache_status()

    if status.get("er_cache_reset_recently"):
        logger.info("[STATUS] Full ER cache reset was recently triggered. Frontend should clear state.")

    return jsonify(status)

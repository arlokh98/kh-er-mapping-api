from flask import Flask, request
from flask_cors import CORS
from routes.process_island import process_island_bp
from routes.test_process_all import test_process_all_bp
from routes.arrow_check import arrow_check_bp
from routes.crop_diamond import crop_diamond_bp
from routes.process_all import process_all_bp

import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/process_all", methods=["OPTIONS"])
def handle_options():
    return '', 200

app.register_blueprint(process_island_bp)
app.register_blueprint(arrow_check_bp)
app.register_blueprint(crop_diamond_bp)
app.register_blueprint(process_all_bp)
app.register_blueprint(test_process_all_bp)

if __name__ == "__main__":
    import os
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        threaded=True
    )

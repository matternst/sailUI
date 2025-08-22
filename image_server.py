# image_server.py
from flask import Flask, send_file
from threading import Thread
import io

def create_image_server(shared_image_obj):
    app = Flask(__name__)
    
    @app.route('/image.bmp')
    def get_image():
        image_bytes = shared_image_obj.get_image_bytes()
        if image_bytes:
            return send_file(io.BytesIO(image_bytes), mimetype='image/bmp')
        else:
            return "No image available", 404
            
    return app

def run_server(app):
    # Run Flask in a separate thread to avoid blocking the main UI
    thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
    thread.daemon = True
    thread.start()
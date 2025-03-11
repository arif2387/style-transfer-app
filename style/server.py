import os
import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Initialize Flask App
app = Flask(__name__, static_folder=".", static_url_path="")  # Serve files from the current directory
CORS(app)  # Enable Cross-Origin Requests

# Load the Pretrained Style Transfer Model
model = hub.load("https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2")
print("✅ Model Loaded Successfully!")

# Create Uploads and Outputs Directory
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


# Function to Load and Preprocess Images
def load_image(img_path):
    img = tf.io.read_file(img_path)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, (256, 256))
    img = img[tf.newaxis, :]
    return img


# Route to Serve the Frontend HTML File
@app.route("/")
def serve_frontend():
    return send_from_directory(".", "index.html")


# Route to Handle Image Upload and Style Transfer
@app.route("/style-transfer", methods=["POST"])
def style_transfer():
    if "content_image" not in request.files or "style_image" not in request.files:
        return jsonify({"error": "Both content and style images are required!"}), 400

    content_file = request.files["content_image"]
    style_file = request.files["style_image"]

    content_path = os.path.join(app.config["UPLOAD_FOLDER"], content_file.filename)
    style_path = os.path.join(app.config["UPLOAD_FOLDER"], style_file.filename)
    content_file.save(content_path)
    style_file.save(style_path)

    # Process Images
    content_image = load_image(content_path)
    style_image = load_image(style_path)

    # Apply Style Transfer
    stylized_image = model(tf.constant(content_image), tf.constant(style_image))[0]

    # Convert Tensor to Image and Save
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], "stylized_image.jpg")
    cv2.imwrite(output_path, cv2.cvtColor(np.squeeze(stylized_image) * 255, cv2.COLOR_RGB2BGR))

    return jsonify({"message": "Style Transfer Successful!", "image_url": "/output/stylized_image.jpg"})


# Route to Serve Output Image
@app.route("/output/<filename>")
def serve_output(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)


# Run Flask Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
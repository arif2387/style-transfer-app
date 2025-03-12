import os
import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ✅ Ensure TensorFlow Uses CPU (Disable GPU)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# ✅ Initialize Flask App
app = Flask(__name__, static_folder=".", static_url_path="")  # Serve files from current directory
CORS(app)  # Enable Cross-Origin Requests

# ✅ Set Up Directories
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# ✅ Load Pretrained Style Transfer Model (Ensure Cache Directory)
model_cache_dir = os.path.join(os.getcwd(), "tfhub_cache")
os.environ["TFHUB_CACHE_DIR"] = model_cache_dir
model = hub.load("https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2")
print("✅ Model Loaded Successfully!")

# ✅ Function to Load and Preprocess Images
def load_image(img_path):
    img = tf.io.read_file(img_path)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)  # Normalize 0-1
    img = tf.image.resize(img, (256, 256))  # Resize to model input size
    img = img[tf.newaxis, :]  # Add batch dimension
    return img

# ✅ Route to Serve Frontend HTML
@app.route("/")
def serve_frontend():
    return send_from_directory(".", "index.html")

# ✅ Route to Handle Image Upload & Style Transfer
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

    # ✅ Process Images
    content_image = load_image(content_path)
    style_image = load_image(style_path)

    # ✅ Apply Style Transfer
    stylized_image = model(tf.constant(content_image), tf.constant(style_image))[0]

    # ✅ Convert Tensor to Image (Ensure Proper Scaling)
    stylized_image = np.array(stylized_image[0])  # Remove batch dimension
    stylized_image = np.clip(stylized_image * 255, 0, 255).astype(np.uint8)  # Normalize to 0-255

    # ✅ Save Output Image
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], "stylized_image.jpg")
    cv2.imwrite(output_path, cv2.cvtColor(stylized_image, cv2.COLOR_RGB2BGR))

    return jsonify({"message": "Style Transfer Successful!", "image_url": "/output/stylized_image.jpg"})

# ✅ Route to Serve Output Image
@app.route("/output/<filename>")
def serve_output(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render assigns a dynamic port
    from waitress import serve
    serve(app, host="0.0.0.0", port=port)


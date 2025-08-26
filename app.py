import os
from flask import Flask, render_template, request, redirect, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "photo" not in request.files:
        return "No file uploaded", 400

    photo = request.files["photo"]
    if photo.filename == "":
        return "No selected file", 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], photo.filename)
    photo.save(filepath)

    # After upload → redirect to gallery
    return redirect("/gallery")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/gallery")
def gallery():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    # Only images
    image_files = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    image_urls = [f"/uploads/{f}" for f in image_files]
    return render_template("gallery.html", images=image_urls)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

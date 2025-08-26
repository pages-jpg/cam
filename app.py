import os
from flask import Flask, request, render_template, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

app = Flask(__name__)

# DATABASE_URL from Render environment
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Model for uploaded files
class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# Home page → upload form
@app.route("/")
def index():
    return render_template("index.html")

# Upload endpoint → saves to PostgreSQL
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    new_file = UploadedFile(
        filename=file.filename,
        data=file.read(),
        mimetype=file.mimetype
    )
    db.session.add(new_file)
    db.session.commit()
    # Redirect to gallery after upload
    return redirect(url_for("gallery"))

# Serve individual file by ID
@app.route("/file/<int:file_id>")
def get_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    return send_file(BytesIO(file.data), mimetype=file.mimetype, download_name=file.filename)

# Gallery page → display all uploaded files
@app.route("/gallery")
def gallery():
    files = UploadedFile.query.all()
    return render_template("gallery.html", files=files)

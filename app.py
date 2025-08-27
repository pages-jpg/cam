import os
from flask import Flask, request, render_template, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey123")

# Database setup
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Model
class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# Passkey
PASSKEY = os.getenv("GALLERY_PASSKEY", "0310")

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect("/gallery")
        return f(*args, **kwargs)
    return decorated

# Home page
@app.route("/")
def index():
     return render_template("index.html")

# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return {"error": "No file uploaded"}, 400
    file = request.files["file"]
    new_file = UploadedFile(
        filename=file.filename,
        data=file.read(),
        mimetype=file.mimetype
    )
    db.session.add(new_file)
    db.session.commit()
    return {"message": f"{file.filename} uploaded successfully!"}

# Serve file
@app.route("/file/<int:file_id>")
@login_required
def get_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    return send_file(BytesIO(file.data), mimetype=file.mimetype, download_name=file.filename)

# Gallery page (login & gallery combined)
@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    if request.method == "POST":
        key = request.form.get("passkey")
        if key == PASSKEY:
            session["authenticated"] = True
            return redirect("/gallery")
        else:
            return render_template("gallery.html", files=[], error="Incorrect passkey!")
    if not session.get("authenticated"):
        return render_template("gallery.html", files=[], error=None)
    files = UploadedFile.query.all()
    return render_template("gallery.html", files=files, error=None)

@app.route("/delete-multiple", methods=["POST"])
@login_required
def delete_multiple():
    ids = request.form.getlist("file_ids")
    for fid in ids:
        file = UploadedFile.query.get(fid)
        if file:
            db.session.delete(file)
    db.session.commit()
    return redirect("/gallery")


# Delete file
@app.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    db.session.delete(file)
    db.session.commit()
    return redirect("/gallery")

if __name__ == "__main__":
    app.run(debug=True)



import os
from flask import Flask, request, render_template, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")  # For session management

# Database config
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

# Passkey for gallery
PASSKEY = os.getenv("GALLERY_PASSKEY", "0310")

@app.route("/")
def index():
    return render_template("index.html")

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

@app.route("/file/<int:file_id>")
def get_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    return send_file(BytesIO(file.data), mimetype=file.mimetype, download_name=file.filename)

# Gallery login
@app.route("/gallery-login", methods=["GET", "POST"])
def gallery_login():
    if request.method == "POST":
        key = request.form.get("passkey")
        if key == PASSKEY:
            session["authenticated"] = True
            return redirect("/gallery")
        else:
            return "<h2>Incorrect passkey!</h2><a href='/gallery-login'>Try again</a>"
    return '''
        <h1>Enter Passkey to Access Gallery</h1>
        <form method="POST">
            <input type="password" name="passkey" placeholder="Passkey" required>
            <button type="submit">Enter</button>
        </form>
    '''

@app.route("/gallery")
def gallery():
    if not session.get("authenticated"):
        return redirect("/gallery-login")
    files = UploadedFile.query.all()
    return render_template("gallery.html", files=files)

@app.route("/delete/<int:file_id>", methods=["POST"])
def delete_file(file_id):
    if not session.get("authenticated"):
        return redirect("/gallery-login")
    file = UploadedFile.query.get_or_404(file_id)
    db.session.delete(file)
    db.session.commit()
    return redirect("/gallery")

if __name__ == "__main__":
    app.run(debug=True)

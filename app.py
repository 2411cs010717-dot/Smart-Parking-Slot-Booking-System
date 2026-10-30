import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-secret")
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

def get_db():
    import mysql.connector
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "parking_db"),
        port=int(os.getenv("DB_PORT", "3306"))
    )


def sync_booking_occupancy():
    """Update slot status according to bookings active right now."""
    conn = None
    cur = None

    try:
        now = datetime.now()
        today = now.date()
        current_time = now.time().strftime("%H:%M:%S")

        conn = get_db()
        cur = conn.cursor()

        # Active bookings make their slots occupied.
        cur.execute("""
            UPDATE parking_slots p
            SET p.status = 'Occupied',
                p.status_source = 'Booking'
            WHERE EXISTS (
                SELECT 1
                FROM bookings b
                WHERE b.slot_id = p.id
                  AND b.status = 'Confirmed'
                  AND b.booking_date = %s
                  AND b.start_time <= %s
                  AND b.end_time > %s
            )
        """, (today, current_time, current_time))

        # Expired booking-based occupancy becomes available again.
        # Do not reset slots marked occupied by CNN or manually.
        cur.execute("""
            UPDATE parking_slots p
            SET p.status = 'Available',
                p.status_source = 'Booking'
            WHERE p.status_source = 'Booking'
              AND NOT EXISTS (
                  SELECT 1
                  FROM bookings b
                  WHERE b.slot_id = p.id
                    AND b.status = 'Confirmed'
                    AND b.booking_date = %s
                    AND b.start_time <= %s
                    AND b.end_time > %s
              )
        """, (today, current_time, current_time))

        conn.commit()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("username"):
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def cnn_predict(image_path):
    """Load a trained Keras CNN. Returns a helpful message until the model is trained."""
    model_path = os.path.join(app.root_path, "deep_learning", "model", "parking_cnn.keras")
    if not os.path.exists(model_path):
        return None, "CNN model is not trained yet. Follow README.md to generate demo data and train it."
    try:
        import tensorflow as tf
        from PIL import Image
        image = Image.open(image_path).convert("RGB").resize((128, 128))
        import numpy as np
        arr = np.asarray(image, dtype="float32") / 255.0
        prediction = float(tf.keras.models.load_model(model_path).predict(arr[None, ...], verbose=0)[0][0])
        # Model convention: 0 = vacant, 1 = occupied
        label = "Occupied" if prediction >= 0.5 else "Vacant"
        confidence = prediction if prediction >= 0.5 else 1.0 - prediction
        return {"label": label, "confidence": round(confidence * 100, 1)}, None
    except Exception as exc:
        return None, "Could not run the CNN model. Check the setup instructions. Details: " + str(exc)

@app.route("/")
def home():
    if session.get("username"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role", "user")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Enter both username and password.", "danger")
            return render_template("login.html")
        if role == "admin":
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session.clear()
                session.update(username=username, role="admin")
                flash("Admin login successful.", "success")
                return redirect(url_for("admin_dashboard"))
            flash("Invalid admin credentials.", "danger")
            return render_template("login.html")
        # Demo requirement: any non-empty username/password is accepted for user login.
        session.clear()
        session.update(username=username, role="user")
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username) VALUES (%s) ON DUPLICATE KEY UPDATE username=username", (username,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            # Login can still work if the database has not been configured yet.
            pass
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required()
def dashboard():
    sync_booking_occupancy()
    stats = {"total": 20, "occupied": 0, "vacant": 20, "bookings": 0}
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS total FROM parking_slots")
        stats["total"] = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS occupied FROM parking_slots WHERE status='Occupied'")
        stats["occupied"] = cur.fetchone()["occupied"]
        stats["vacant"] = stats["total"] - stats["occupied"]
        cur.execute("SELECT COUNT(*) AS bookings FROM bookings WHERE status='Confirmed'")
        stats["bookings"] = cur.fetchone()["bookings"]
        cur.close()
        conn.close()
    except Exception:
        pass
    return render_template("dashboard.html", stats=stats)


@app.route("/detection", methods=["GET", "POST"])
@login_required()
def detection():
    result = None
    uploaded_image = None
    model_message = None
    slots = []

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id AS slot_id, slot_number AS slot_name,
                   vehicle_type, status
            FROM parking_slots
            ORDER BY id
        """)
        slots = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as exc:
        flash("Could not load parking slots: " + str(exc), "danger")

    if request.method == "POST":
        file = request.files.get("image")
        slot_id = request.form.get("slot_id", type=int)

        if not slot_id:
            flash("Select the parking slot shown in the image.", "danger")
        elif not file or not file.filename:
            flash("Choose a parking-space image first.", "danger")
        elif not allowed_file(file.filename):
            flash("Upload a PNG, JPG, JPEG, or WEBP image.", "danger")
        else:
            safe_name = secure_filename(file.filename)
            filename = datetime.now().strftime("%Y%m%d%H%M%S%f") + "_" + safe_name
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            uploaded_image = filename

            result, model_message = cnn_predict(path)

            # Only update the database after a successful CNN prediction.
            if result:
                conn = None
                cur = None
                try:
                    sync_booking_occupancy()
                    conn = get_db()
                    cur = conn.cursor(dictionary=True)

                    cur.execute("""
                        SELECT id FROM parking_slots
                        WHERE id = %s
                    """, (slot_id,))
                    slot = cur.fetchone()

                    if not slot:
                        flash("Selected parking slot was not found.", "danger")
                    else:
                        # Do not let an image prediction override an
                        # active booking's time-based occupancy.
                        now = datetime.now()
                        cur.execute("""
                            SELECT COUNT(*) AS n
                            FROM bookings
                            WHERE slot_id = %s
                              AND status = 'Confirmed'
                              AND booking_date = %s
                              AND start_time <= %s
                              AND end_time > %s
                        """, (
                            slot_id, now.date(),
                            now.strftime("%H:%M:%S"),
                            now.strftime("%H:%M:%S")
                        ))
                        active_booking = cur.fetchone()["n"]

                        if active_booking:
                            flash(
                                "This slot has an active booking. "
                                "Booking status was kept.",
                                "warning"
                            )
                        else:
                            db_status = (
                                "Occupied"
                                if result["label"] == "Occupied"
                                else "Available"
                            )
                            cur.execute("""
                                UPDATE parking_slots
                                SET status = %s, status_source = 'CNN'
                                WHERE id = %s
                            """, (db_status, slot_id))
                            conn.commit()
                            flash(
                                f"Slot status updated to {db_status} by CNN.",
                                "success"
                            )

                except Exception as exc:
                    if conn:
                        conn.rollback()
                    flash("Could not update slot status: " + str(exc), "danger")
                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()

    return render_template(
        "detection.html",
        result=result,
        uploaded_image=uploaded_image,
        model_message=model_message,
        slots=slots
    )

@app.route("/booking", methods=["GET", "POST"])
@login_required()
def booking():
    slots = []

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id AS slot_id, slot_number AS slot_name,
                   vehicle_type, status
            FROM parking_slots
            ORDER BY id
        """)
        slots = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as exc:
        flash("Could not load parking slots: " + str(exc), "danger")

    if request.method == "POST":
        slot_id = request.form.get("slot_id", type=int)
        vehicle_type = request.form.get("vehicle_type", "Four-wheeler")
        booking_date = request.form.get("booking_date", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")

        if not all([slot_id, booking_date, start_time, end_time]) or start_time >= end_time:
            flash("Please enter a slot, date, and valid start/end times.", "danger")
            return render_template("booking.html", slots=slots)

        conn = None
        cur = None

        try:
            conn = get_db()
            cur = conn.cursor(dictionary=True)

            cur.execute(
                "SELECT id, status FROM parking_slots WHERE id=%s",
                (slot_id,)
            )
            slot = cur.fetchone()

            if not slot:
                flash("Parking slot not found.", "danger")

            elif slot["status"] == "Occupied":
                flash("That slot is currently occupied.", "danger")

            else:
                cur.execute("""
                    SELECT COUNT(*) AS n
                    FROM bookings
                    WHERE slot_id=%s
                      AND booking_date=%s
                      AND status='Confirmed'
                      AND NOT (end_time <= %s OR start_time >= %s)
                """, (slot_id, booking_date, start_time, end_time))

                overlap = cur.fetchone()["n"]

                if overlap:
                    flash("That slot is already booked for this time.", "danger")
                else:
                    cur.execute("""
                        INSERT INTO bookings
                        (user_id, slot_id, vehicle_type, booking_date,
                         start_time, end_time, status)
                        VALUES (%s, %s, %s, %s, %s, %s, 'Confirmed')
                    """, (
                        session.get("user_id"),
                        slot_id,
                        vehicle_type,
                        booking_date,
                        start_time,
                        end_time
                    ))
                    cur.execute("""
                        UPDATE parking_slots
                        SET status = 'Occupied',
                            status_source = 'Booking'
                        WHERE id = %s
                    """, (slot_id,))
                    conn.commit()
                    flash("Parking slot booked successfully!", "success")
                    return redirect(url_for("my_bookings"))

        except Exception as exc:
            if conn:
                conn.rollback()
            flash("Booking could not be saved: " + str(exc), "danger")

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    return render_template("booking.html", slots=slots)

@app.route("/my-bookings")
@login_required()
def my_bookings():
    bookings = []
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        if session.get("role") == "admin":
            cur.execute("""SELECT b.*, p.slot_name FROM bookings b
                JOIN parking_slots p ON b.slot_id=p.slot_id ORDER BY b.created_at DESC""")
        else:
            cur.execute("""SELECT b.*, p.slot_name FROM bookings b
                JOIN parking_slots p ON b.slot_id=p.slot_id
                WHERE b.username=%s ORDER BY b.created_at DESC""", (session["username"],))
        bookings = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        pass
    return render_template("my_bookings.html", bookings=bookings)

@app.route("/cancel-booking/<int:booking_id>", methods=["POST"])
@login_required()
def cancel_booking(booking_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        if session.get("role") == "admin":
            cur.execute("UPDATE bookings SET status='Cancelled' WHERE booking_id=%s", (booking_id,))
        else:
            cur.execute("UPDATE bookings SET status='Cancelled' WHERE booking_id=%s AND username=%s", (booking_id, session["username"]))
        conn.commit()
        cur.close()
        conn.close()
        flash("Booking cancelled if it belonged to your account.", "success")
    except Exception as exc:
        flash("Could not cancel booking. " + str(exc), "danger")
    return redirect(url_for("my_bookings"))

@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    stats = {"total": 0, "occupied": 0, "vacant": 0, "bookings": 0}
    bookings = []
    slots = []

    conn = None
    cur = None

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        # Dashboard statistics
        cur.execute("SELECT COUNT(*) AS total FROM parking_slots")
        stats["total"] = cur.fetchone()["total"]

        cur.execute("""
            SELECT COUNT(*) AS occupied
            FROM parking_slots
            WHERE status = 'Occupied'
        """)
        stats["occupied"] = cur.fetchone()["occupied"]

        stats["vacant"] = stats["total"] - stats["occupied"]

        cur.execute("""
            SELECT COUNT(*) AS bookings
            FROM bookings
            WHERE status = 'Confirmed'
        """)
        stats["bookings"] = cur.fetchone()["bookings"]

        # Recent bookings
        cur.execute("""
            SELECT b.*, p.slot_number
            FROM bookings b
            JOIN parking_slots p ON b.slot_id = p.id
            ORDER BY b.created_at DESC
            LIMIT 10
        """)
        bookings = cur.fetchall()

        # All parking slots
        cur.execute("""
            SELECT *
            FROM parking_slots
            ORDER BY id
        """)
        slots = cur.fetchall()

    except Exception as e:
        print("Admin dashboard database error:", e)

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return render_template(
        "admin.html",
        stats=stats,
        bookings=bookings,
        slots=slots
    )

@app.route("/admin/slot/<int:slot_id>", methods=["POST"])
@login_required(role="admin")
def update_slot(slot_id):
    status = request.form.get("status")

    if status not in {"Available", "Occupied"}:
        flash("Invalid slot status.", "danger")
        return redirect(url_for("admin_dashboard"))

    conn = None
    cur = None

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "UPDATE parking_slots SET status=%s WHERE id=%s",
            (status, slot_id)
        )

        conn.commit()

        if cur.rowcount == 0:
            flash("Parking slot not found or status unchanged.", "warning")
        else:
            flash("Parking slot updated.", "success")

    except Exception as exc:
        if conn is not None:
            conn.rollback()
        print("Update slot error:", exc)
        flash("Could not update slot. Please check the Flask terminal.", "danger")

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)

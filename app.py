from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from math import radians, sin, cos, sqrt, atan2
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()  

import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ======================
# DATABASE SETUP (MongoDB)
# ======================

MONGODB_URL = os.environ.get("MONGODB_URL")

if not MONGODB_URL:
    raise RuntimeError("MONGODB_URL is not set")

client = MongoClient(MONGODB_URL)
db = client["blood_app"]

# Collections (equivalent to SQLAlchemy models/tables)
users_col         = db["users"]
hospitals_col     = db["hospitals"]
requirements_col  = db["blood_requirements"]

# ======================
# INDEXES (unique constraints, equivalent to SQLAlchemy unique=True)
# ======================
users_col.create_index("email",    unique=True)
users_col.create_index("username", unique=True)
users_col.create_index("phone",    unique=True)
hospitals_col.create_index("email", unique=True)


# ======================
# HELPER FUNCTIONS
# ======================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def str_to_objectid(id_str):
    """Safely convert a string to ObjectId."""
    try:
        return ObjectId(id_str)
    except Exception:
        return None


# ======================
# ROUTES
# ======================
@app.route("/")
def home():
    return render_template("home.html")


# ----------------------
# SIGNUP
# ----------------------
@app.route("/signup")
def signup():
    return render_template("signup.html")


# ----------------------
# DONOR SIGNUP
# ----------------------
@app.route("/signup/donor", methods=["GET", "POST"])
def signup_donor():
    if request.method == "POST":
        username   = request.form["username"]
        email      = request.form["email"]
        password   = generate_password_hash(request.form["password"], method="pbkdf2:sha256")
        phone      = request.form["mobile"]
        blood_group = request.form["blood_group"]
        latitude   = request.form.get("latitude")
        longitude  = request.form.get("longitude")

        # Duplicate checks
        if users_col.find_one({"email": email}):
            return "Email already registered!"
        if users_col.find_one({"username": username}):
            return "Username already taken!"
        if users_col.find_one({"phone": phone}):
            return "Phone number already registered!"

        new_user = {
            "username":           username,
            "email":              email,
            "password":           password,
            "phone":              phone,
            "blood_group":        blood_group,
            "latitude":           float(latitude)  if latitude  else None,
            "longitude":          float(longitude) if longitude else None,
            "donation_count":     0,
            "last_donation_date": None,
        }

        result = users_col.insert_one(new_user)
        session["user_id"] = str(result.inserted_id)
        return redirect(url_for("home"))

    return render_template("signup_donor.html")


# ----------------------
# HOSPITAL SIGNUP
# ----------------------
@app.route("/signup/hospital", methods=["GET", "POST"])
def signup_hospital():
    if request.method == "POST":
        name      = request.form["name"]
        email     = request.form["email"]
        password  = generate_password_hash(request.form["password"], method="pbkdf2:sha256")
        phone     = request.form["phone"]
        city      = request.form["city"]
        latitude  = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if hospitals_col.find_one({"email": email}):
            return "Hospital already registered!"

        hospital = {
            "name":      name,
            "email":     email,
            "password":  password,
            "phone":     phone,
            "city":      city,
            "latitude":  float(latitude)  if latitude  else None,
            "longitude": float(longitude) if longitude else None,
            "verified":  True,
        }

        result = hospitals_col.insert_one(hospital)

        # Auto-login after signup
        session["hospital_id"] = str(result.inserted_id)
        session["role"]        = "hospital"

        return redirect(url_for("hospital_dashboard"))

    return render_template("signup_hospital.html")


# ----------------------
# LOGIN PAGE (chooser)
# ----------------------
@app.route("/login")
def login():
    return render_template("login.html")


# ----------------------
# DONOR LOGIN
# ----------------------
@app.route("/login/donor", methods=["GET", "POST"])
def login_donor():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]

        user = users_col.find_one({"email": email})
        if not user:
            return "User not registered!"

        if check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            return redirect(url_for("home"))
        else:
            return "Incorrect password!"

    return render_template("login_donor.html")


# ----------------------
# HOSPITAL LOGIN
# ----------------------
@app.route("/login/hospital", methods=["GET", "POST"])
def login_hospital():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]

        hospital = hospitals_col.find_one({"email": email})

        if not hospital:
            return "Hospital not registered!"

        if not hospital.get("verified"):
            return "Hospital not verified yet!"

        if check_password_hash(hospital["password"], password):
            session.clear()
            session["hospital_id"] = str(hospital["_id"])
            session["role"]        = "hospital"
            return redirect(url_for("hospital_dashboard"))
        else:
            return "Incorrect password!"

    return render_template("login_hospital.html")


# ----------------------
# HOSPITAL DASHBOARD
# ----------------------
@app.route("/hospital/dashboard")
def hospital_dashboard():
    if session.get("role") != "hospital":
        return redirect(url_for("home"))

    hospital_id = str_to_objectid(session["hospital_id"])
    hospital    = hospitals_col.find_one({"_id": hospital_id})

    # Fetch all blood requirements posted by this hospital
    requirements = list(requirements_col.find({"hospital_id": str(hospital_id)}))

    # Convert _id to string for easy use in templates
    for r in requirements:
        r["id"] = str(r["_id"])

    # Give hospital an 'id' field for template compatibility
    hospital["id"] = str(hospital["_id"])

    return render_template(
        "hospital_dashboard.html",
        hospital=hospital,
        requirements=requirements
    )


# ----------------------
# PROFILE
# ----------------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = str_to_objectid(session["user_id"])
    user    = users_col.find_one({"_id": user_id})

    if user:
        user["id"] = str(user["_id"])

    return render_template("profile.html", user=user)


# ----------------------
# ASK BLOOD
# ----------------------
@app.route("/ask_blood", methods=["GET", "POST"])
def ask_blood():
    if request.method == "POST":
        blood_group = request.form.get("blood_group")
        user_lat    = request.form.get("latitude")
        user_lon    = request.form.get("longitude")

        if not user_lat or not user_lon:
            return "Location not received. Allow location access.", 400

        user_lat = float(user_lat)
        user_lon = float(user_lon)

        # ======================
        # FIND DONORS (same blood group, exclude requester)
        # ======================
        query_filter = {"blood_group": blood_group}

        if session.get("user_id"):
            current_user_id = str_to_objectid(session["user_id"])
            query_filter["_id"] = {"$ne": current_user_id}

        all_users   = list(users_col.find(query_filter))
        donor_list  = []

        for u in all_users:
            if u.get("latitude") is not None and u.get("longitude") is not None:
                distance = haversine(user_lat, user_lon, u["latitude"], u["longitude"])
                donor_list.append({
                    "username":    u["username"],
                    "blood_group": u["blood_group"],
                    "distance":    round(distance, 2),
                    "phone":       u["phone"],
                })

        donor_list.sort(key=lambda x: x["distance"])

        # ======================
        # FIND HOSPITALS (verified)
        # ======================
        all_hospitals = list(hospitals_col.find({"verified": True}))
        hospital_list = []

        for h in all_hospitals:
            if h.get("latitude") is not None and h.get("longitude") is not None:
                distance = haversine(user_lat, user_lon, h["latitude"], h["longitude"])

                # Fetch blood requirements for this hospital
                requirements = list(requirements_col.find({"hospital_id": str(h["_id"])}))
                for r in requirements:
                    r["id"] = str(r["_id"])

                hospital_list.append({
                    "name":         h["name"],
                    "city":         h["city"],
                    "distance":     round(distance, 2),
                    "phone":        h["phone"],
                    "latitude":     h["latitude"],
                    "longitude":    h["longitude"],
                    "requirements": requirements,
                })

        hospital_list.sort(key=lambda x: x["distance"])

        return render_template(
            "ask_blood_results.html",
            donors=donor_list,
            hospitals=hospital_list,
            blood_group=blood_group
        )

    return render_template("ask_blood.html")


# ----------------------
# DONATE BLOOD
# ----------------------
@app.route("/donate-blood", methods=["GET", "POST"])
def donate_blood():
    if request.method == "POST":
        user_lat = float(request.form["latitude"])
        user_lon = float(request.form["longitude"])

        all_hospitals = list(hospitals_col.find({"verified": True}))
        hospital_list = []

        for h in all_hospitals:
            if h.get("latitude") and h.get("longitude"):
                distance = haversine(user_lat, user_lon, h["latitude"], h["longitude"])

                requirements = list(requirements_col.find({"hospital_id": str(h["_id"])}))
                for r in requirements:
                    r["id"] = str(r["_id"])

                hospital_list.append({
                    "name":         h["name"],
                    "city":         h["city"],
                    "distance":     round(distance, 2),
                    "phone":        h["phone"],
                    "latitude":     h["latitude"],
                    "longitude":    h["longitude"],
                    "requirements": requirements,
                })

        hospital_list.sort(key=lambda x: x["distance"])

        return render_template("donate_blood.html", hospitals=hospital_list)

    return render_template("donate_blood.html")


# ----------------------
# ADD BLOOD REQUIREMENT
# ----------------------
@app.route("/hospital/add-blood-requirement", methods=["GET", "POST"])
def add_blood_requirement():
    if "hospital_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        blood_group = request.form["blood_group"]
        urgency     = request.form["urgency"]
        units       = request.form["units"]

        requirement = {
            "hospital_id":    session["hospital_id"],   # stored as string (matches how we query)
            "blood_group":    blood_group,
            "urgency":        urgency,
            "units_required": int(units),
            "created_at":     datetime.utcnow(),
        }

        requirements_col.insert_one(requirement)
        return redirect(url_for("hospital_dashboard"))

    return render_template("add_blood_requirement.html")


# ----------------------
# REMOVE BLOOD REQUIREMENT
# ----------------------
@app.route("/hospital/remove-blood-requirement/<req_id>", methods=["POST"])
def remove_blood_requirement(req_id):
    if session.get("role") != "hospital":
        return redirect(url_for("home"))

    req_object_id = str_to_objectid(req_id)
    if req_object_id:
        requirement = requirements_col.find_one({"_id": req_object_id})

        # Safety check: hospital can only delete its own requirement
        if requirement and requirement["hospital_id"] == session["hospital_id"]:
            requirements_col.delete_one({"_id": req_object_id})

    return redirect(url_for("hospital_dashboard"))


# ----------------------
# LOGOUT
# ----------------------
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))


# ======================
# RUN APP
# ======================
if __name__ == "__main__":
    app.run()

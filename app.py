from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ======================
# DATABASE SETUP
# ======================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blood_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ======================
# MODELS
# ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)  # ✅ Added phone number
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    blood_group = db.Column(db.String(10), nullable=False)

    # Extra donor-related fields
    donation_count = db.Column(db.Integer, default=0)
    last_donation_date = db.Column(db.String(20), nullable=True)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    city = db.Column(db.String(100), nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    verified = db.Column(db.Boolean, default=True)



# ======================
# HELPER FUNCTIONS
# ======================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ======================
# ROUTES
# ======================
@app.route("/")
def home():
    return render_template("home.html")

# ----------------------
# SIGNUP
# ----------------------
# ----------------------
# DONOR SIGNUP
# ----------------------
@app.route("/signup/donor", methods=["GET", "POST"])
def signup_donor():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(
            request.form["password"], method="pbkdf2:sha256"
        )
        phone = request.form["mobile"]
        blood_group = request.form["blood_group"]
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if User.query.filter_by(email=email).first():
            return "Email already registered!"
        if User.query.filter_by(username=username).first():
            return "Username already taken!"
        if User.query.filter_by(phone=phone).first():
            return "Phone number already registered!"

        new_user = User(
            username=username,
            email=email,
            password=password,
            phone=phone,
            blood_group=blood_group,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None
        )

        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        return redirect(url_for("home"))

    return render_template("signup_donor.html")

# ----------------------
# HOSPITAL SIGNUP
# ----------------------

@app.route("/signup/hospital", methods=["GET", "POST"])
def signup_hospital():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(
            request.form["password"], method="pbkdf2:sha256"
        )
        phone = request.form["phone"]
        city = request.form["city"]

        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if Hospital.query.filter_by(email=email).first():
            return "Hospital already registered!"

        hospital = Hospital(
            name=name,
            email=email,
            password=password,
            phone=phone,
            city=city,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            verified=True
        )

        db.session.add(hospital)
        db.session.commit()

        # ✅ AUTO LOGIN AFTER SIGNUP
        session["hospital_id"] = hospital.id
        session["role"] = "hospital"

        return redirect(url_for("hospital_dashboard"))

    return render_template("signup_hospital.html")



# ----------------------
# LOGIN
# ----------------------
@app.route("/login")
def login():
    return render_template("login.html")

# ----------------------
# SIGNUP 
# ----------------------
@app.route("/signup")
def signup():
    return render_template("signup.html")    


# ----------------------
# DONOR LOGIN
# ----------------------
@app.route("/login/donor", methods=["GET", "POST"])
def login_donor():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if not user:
            return "User not registered!"

        if check_password_hash(user.password, password):
            session["user_id"] = user.id
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
        email = request.form["email"]
        password = request.form["password"]

        hospital = Hospital.query.filter_by(email=email).first()

        if not hospital:
            return "Hospital not registered!"

        if not hospital.verified:
            return "Hospital not verified yet!"

        if check_password_hash(hospital.password, password):
            session.clear()                 # 🔥 important
            session["hospital_id"] = hospital.id
            session["role"] = "hospital"    # 🔥 REQUIRED
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

    hospital = Hospital.query.get(session["hospital_id"])
    requirements = BloodRequirement.query.filter_by(
        hospital_id=hospital.id
    ).all()

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
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

# ----------------------
# ASK_BLOOD
# ----------------------
@app.route("/ask_blood", methods=["GET", "POST"])
def ask_blood():
    if request.method == "POST":
        blood_group = request.form.get("blood_group")
        user_lat = request.form.get("latitude")
        user_lon = request.form.get("longitude")

        if not user_lat or not user_lon:
            return "Location not received. Allow location access.", 400

        user_lat, user_lon = float(user_lat), float(user_lon)

        # ======================
        # FIND DONORS (same blood group, exclude requester)
        # ======================
        query = User.query.filter_by(blood_group=blood_group)

        if session.get("user_id"):
            query = query.filter(User.id != session["user_id"])
        users = query.all()
        donor_list = []

        for u in users:
            if u.latitude is not None and u.longitude is not None:
                distance = haversine(user_lat, user_lon, u.latitude, u.longitude)
                donor_list.append({
                    "username": u.username,
                    "blood_group": u.blood_group,
                    "distance": round(distance, 2),
                    "phone": u.phone
                })
        donor_list.sort(key=lambda x: x["distance"])


        # ======================
        # FIND HOSPITALS (verified)
        # ======================
        hospitals = Hospital.query.filter_by(verified=True).all()
        hospital_list = []

        for h in hospitals:
            if h.latitude is not None and h.longitude is not None:
                distance = haversine(user_lat, user_lon, h.latitude, h.longitude)

                # fetch blood requirements for hospital
                requirements = BloodRequirement.query.filter_by(
                    hospital_id=h.id
                ).all()

                hospital_list.append({
                    "name": h.name,
                    "city": h.city,
                    "distance": round(distance, 2),
                    "phone": h.phone,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "requirements": requirements
                })

        hospital_list.sort(key=lambda x: x["distance"])

        # ======================
        # SEND BOTH TO TEMPLATE
        # ======================
        return render_template(
            "ask_blood_results.html",
            donors=donor_list,
            hospitals=hospital_list,
            blood_group=blood_group
        )

    return render_template("ask_blood.html")




# ----------------------
# DONATE_BLOOD
# ----------------------
@app.route("/donate-blood", methods=["GET", "POST"])
def donate_blood():
    if request.method == "POST":
        user_lat = float(request.form["latitude"])
        user_lon = float(request.form["longitude"])

        hospitals = Hospital.query.filter_by(verified=True).all()
        hospital_list = []

        for h in hospitals:
            if h.latitude and h.longitude:
                distance = haversine(user_lat, user_lon, h.latitude, h.longitude)

                requirements = BloodRequirement.query.filter_by(
                    hospital_id=h.id
                ).all()

                hospital_list.append({
                    "name": h.name,
                    "city": h.city,
                    "distance": round(distance, 2),
                    "phone": h.phone,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "requirements": requirements
                })  

        hospital_list.sort(key=lambda x: x["distance"])

        return render_template(
            "donate_blood.html",
            hospitals=hospital_list
        )

    return render_template("donate_blood.html")


#----------------------
#BLOOD REQUIREMENT
#----------------------
class BloodRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospital.id"), nullable=False)

    blood_group = db.Column(db.String(10), nullable=False)
    urgency = db.Column(db.String(20), default="Normal")  # Normal / Urgent
    units_required = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


@app.route("/hospital/add-blood-requirement", methods=["GET", "POST"])
def add_blood_requirement():
    if "hospital_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        blood_group = request.form["blood_group"]
        urgency = request.form["urgency"]
        units = request.form["units"]

        requirement = BloodRequirement(
            hospital_id=session["hospital_id"],
            blood_group=blood_group,
            urgency=urgency,
            units_required=units
        )

        db.session.add(requirement)
        db.session.commit()

        return redirect(url_for("hospital_dashboard"))

    return render_template("add_blood_requirement.html")

# ----------------------
# REMOVE BLOOD REQUIREMENT
# ----------------------
@app.route("/hospital/remove-blood-requirement/<int:req_id>", methods=["POST"])
def remove_blood_requirement(req_id):
    if session.get("role") != "hospital":
        return redirect(url_for("home"))

    requirement = BloodRequirement.query.get(req_id)

    # Safety check: hospital can delete only its own requirement
    if requirement and requirement.hospital_id == session["hospital_id"]:
        db.session.delete(requirement)
        db.session.commit()

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
    with app.app_context():
        db.create_all()
    app.run(debug=True)

\# 🩸 Blood Donation Portal



A full-stack web application built with Flask that connects blood donors, hospitals, and patients using real-time, location-based search and urgent blood requirement announcements.



The platform aims to reduce delays in emergency blood availability by providing a simple, transparent, and accessible system for finding nearby blood donors and verified hospitals.



---



\## 🌟 Motivation



In medical emergencies, time is the most critical factor. Many patients lose their lives not because blood is unavailable, but because it cannot be found quickly.



This project was built to:

\- Bridge the gap between donors and hospitals

\- Enable hospitals to announce urgent blood needs in real time

\- Allow anyone to search for blood without mandatory login

\- Provide direct navigation to hospitals using Google Maps



---



\## 🚀 Key Features



\### 👤 User (Donor)

\- Register and log in as a blood donor

\- Share blood group and location

\- Be discoverable by people searching for blood

\- Excluded from search results when requesting blood themselves



\### 🏥 Hospital

\- Register and log in with hospital credentials

\- Access a dedicated hospital dashboard

\- Announce urgent blood requirements (blood group, urgency, units)

\- Remove blood requirements once fulfilled

\- Location automatically detected for accurate distance calculation



\### 🔍 Blood Search (Public)

\- Search for blood without logging in

\- View nearby verified hospitals and donors

\- Hospitals are prioritized for safety and reliability

\- Urgent blood requirements highlighted clearly

\- Google Maps integration for direct hospital navigation



---



\## 🧠 How the System Works



1\. Hospitals register and log in to the system.

2\. Hospitals announce urgent blood requirements via their dashboard.

3\. Anyone can search for blood by selecting blood group and allowing location access.

4\. The system calculates distance using the Haversine formula.

5\. Results show:

&nbsp;  - Nearby hospitals with urgent needs

&nbsp;  - Nearby donors with matching blood groups

6\. Donors can navigate directly to hospitals using Google Maps.



---



\## 🗺️ Location-Based Matching



\- Browser geolocation is used to detect latitude and longitude

\- Distance is calculated using the Haversine formula

\- Results are sorted by nearest distance

\- Ensures faster response in emergency situations



---



\## 🛠️ Tech Stack



\### Backend

\- Flask (Python)

\- SQLAlchemy ORM

\- Gunicorn (production server)



\### Frontend

\- HTML

\- CSS

\- JavaScript

\- Jinja2 Templates



\### Database

\- SQLALCHEMY (local development)

\- PostgreSQL (production-ready)



\### Deployment

\- Render (Cloud hosting)

\- GitHub (Version control)



---



\## 📦 Project Structure






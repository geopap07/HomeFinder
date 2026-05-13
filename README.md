# 🏠 HomeFinder Portal
### 5CM505 Software Engineering – Scenario 2 (Computer Science)

A full-stack real estate web portal built with **Python/Flask**, implementing the HomeFinder design scenario for the University of Derby Software Engineering module.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/homefinder-portal.git
cd homefinder-portal

# 2. Create virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

### Access
Open your browser at: **http://localhost:5000**

---

## 🔑 Demo Accounts

| Role       | Email                        | Password   |
|------------|------------------------------|------------|
| User       | user@homefinder.com          | User123!   |
| Admin      | admin@homefinder.com         | Admin123!  |
| Supervisor | supervisor@homefinder.com    | Super123!  |

> **2FA Note:** The 2FA token is displayed in a flash message (simulating email delivery). Enter it within 30 seconds.

---

## 📋 Features Implemented

### User Features (FR-1 to FR-7)
- ✅ **FR-1** – User registration with email & password (GDPR compliant)
- ✅ **UC-1** – Secure login with 2-Factor Authentication (token within 30s – NFR-1)
- ✅ **FR-2** – Browse properties (residential, commercial, rental)
- ✅ **FR-3** – Filter by location, price range, property type, bedrooms
- ✅ **FR-4** – Save properties to favourites
- ✅ **FR-6** – Submit inquiry about a property
- ✅ **FR-7** – Notifications when new listings are added (Observer Pattern)

### Admin Features
- ✅ Add, edit, delete property listings
- ✅ View and resolve inquiries
- ✅ User management
- ✅ Monthly reports (Supervisor role)
- ✅ Activity log

### Non-Functional Requirements
- ✅ **NFR-1** – 2FA token delivered within 30 seconds
- ✅ **NFR-2** – Single active session per user
- ✅ **NFR-3** – GDPR compliance (minimal data collection)
- ✅ **NFR-4** – Activity logs retained for 3 months

---

## 🏗️ Architecture

```
homefinder/
├── app.py              # Main Flask application (routes, models, logic)
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/style.css   # Main stylesheet
│   └── js/main.js      # Frontend JavaScript
└── templates/
    ├── base.html        # Base layout with navbar/footer
    ├── index.html       # Homepage
    ├── login.html       # Login page
    ├── register.html    # Registration page
    ├── verify_2fa.html  # 2FA verification
    ├── properties.html  # Property search & listing
    ├── property_detail.html  # Property detail + inquiry form
    ├── favorites.html   # Saved favourites
    ├── notifications.html    # User notifications
    └── admin/
        ├── dashboard.html    # Admin dashboard
        ├── properties.html   # Manage listings
        ├── add_property.html # Add/edit listing form
        ├── inquiries.html    # Manage inquiries
        ├── users.html        # User management
        └── reports.html      # Monthly reports
```

### Design Patterns Applied
- **Observer Pattern** – `PropertyService.add_listing()` notifies all registered users when a new property is listed
- **Facade Pattern** – Property search and filtering uses `SearchService` + `FilterService` + `InquiryService` hidden behind unified query logic

### 3-Layer Architecture
| Layer | Technology |
|-------|------------|
| Presentation | HTML5, Bootstrap 5, Jinja2 |
| Business Logic | Python, Flask, SQLAlchemy ORM |
| Data | SQLite (dev) → PostgreSQL (prod) |

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 👥 Team

| Member | Student ID | Role |
|--------|------------|------|
| Dimitrios Panagiotarakos | [ID] | Application Design, Sequence Diagrams |
| George Papalexandris | [ID] | Data Model, Design Patterns |
| Nicolas Tretiacov | [ID] | Architecture, Frontend, Testing |

---

## 📚 Module Information
- **Module:** 5CM505 – Software Engineering
- **Institution:** University of Derby / Metropolitan College Athens
- **Academic Year:** 2025-26
- **Scenario:** Scenario 2 – HomeFinder Portal (Computer Science)

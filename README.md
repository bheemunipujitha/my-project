# 💳 Credit Card Approval Prediction
### Powered by IBM Watson Machine Learning

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)
![IBM Watson](https://img.shields.io/badge/IBM_Watson-ML-054ADA?style=for-the-badge&logo=ibm&logoColor=white)
![scikit-learn](https://img.shields.io/badge/Scikit--Learn-1.5-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)

**A production-grade, enterprise-level banking dashboard for credit card approval prediction using machine learning and IBM Watson Cloud.**

[Live Demo](#) · [Documentation](#) · [Report Bug](#) · [Request Feature](#)

</div>

---

## 📌 Project Overview

This application predicts credit card approval eligibility using multiple machine learning algorithms integrated with IBM Watson Machine Learning on IBM Cloud. It features a modern banking-grade UI, full prediction history, analytics dashboard, and a REST API.

Built as a final-year AI/ML major project demonstrating:
- End-to-end ML pipeline (data → training → deployment → inference)
- IBM Watson ML model hosting and real-time prediction
- Enterprise-grade Flask web application architecture
- Production-quality UI/UX matching modern fintech standards

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔮 **Prediction Engine** | Real-time credit approval prediction via IBM Watson ML |
| 📊 **Analytics Dashboard** | Visual KPIs, charts, and performance metrics |
| 📋 **Prediction History** | Searchable, paginated, exportable history log |
| 🔐 **Admin Panel** | Secure admin dashboard with model performance analytics |
| 📄 **PDF Reports** | Auto-generated prediction receipt/PDF download |
| 🌙 **Dark Mode** | Full dark/light theme toggle |
| 📱 **Responsive** | Mobile-first, works on all devices |
| 🔌 **REST API** | Full documented REST API with Swagger UI |
| 📧 **Email Results** | Send prediction results via email |
| 🧪 **Multiple ML Models** | Random Forest, Logistic Regression, Decision Tree, XGBoost |

---

## 🏗️ Architecture

```
credit_card_approval/
│
├── app/
│   ├── __init__.py              # App factory
│   ├── blueprints/
│   │   ├── main.py              # Home, About, Contact routes
│   │   ├── predict.py           # Prediction routes
│   │   ├── dashboard.py         # Analytics dashboard
│   │   ├── history.py           # Prediction history
│   │   ├── admin.py             # Admin panel
│   │   ├── ml_info.py           # ML/model information page
│   │   └── api.py               # REST API endpoints
│   ├── models/
│   │   ├── prediction.py        # Prediction SQLAlchemy model
│   │   └── user.py              # User/Admin model
│   ├── utils/
│   │   ├── watson.py            # IBM Watson ML integration
│   │   ├── ml_engine.py         # Local ML model engine
│   │   ├── pdf_generator.py     # PDF report generation
│   │   ├── email_service.py     # Email sending utility
│   │   └── validators.py        # Input validation helpers
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css         # Core banking UI styles
│   │   │   ├── dashboard.css    # Dashboard-specific styles
│   │   │   └── dark-mode.css    # Dark theme overrides
│   │   ├── js/
│   │   │   ├── main.js          # Core JS, animations, theme
│   │   │   ├── predict.js       # Prediction form logic
│   │   │   ├── dashboard.js     # Chart.js dashboard charts
│   │   │   └── history.js       # History table interactions
│   │   └── images/
│   └── templates/
│       ├── base.html            # Base layout template
│       ├── index.html           # Homepage
│       ├── predict.html         # Prediction form
│       ├── result.html          # Prediction result dashboard
│       ├── about.html           # About page
│       ├── contact.html         # Contact page
│       ├── ml_info.html         # ML models info page
│       ├── dashboard/
│       │   ├── analytics.html   # Analytics dashboard
│       │   └── history.html     # Prediction history
│       ├── auth/
│       │   └── admin_login.html # Admin login
│       ├── dashboard/
│       │   └── admin.html       # Admin panel
│       ├── errors/
│       │   ├── 404.html
│       │   └── 500.html
│       └── partials/
│           ├── navbar.html
│           └── footer.html
│
├── ml_models/                   # Trained model files (.pkl/.joblib)
├── instance/                    # Instance config, SQLite DB
├── migrations/                  # Flask-Migrate DB migrations
├── tests/                       # Unit and integration tests
├── docs/                        # Additional documentation
├── config.py                    # Configuration classes
├── run.py                       # Application entry point
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/credit-card-approval.git
cd credit-card-approval
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your IBM Watson credentials and other settings
```

### 5. Initialize Database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Train or Load ML Models
```bash
python ml_models/train_models.py
```

### 7. Run the Application
```bash
python run.py
```

Visit: `http://localhost:5000`

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# Flask
SECRET_KEY=your-very-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///instance/credit_approval.db

# IBM Watson ML
WATSON_API_KEY=your-watson-api-key
WATSON_URL=https://us-south.ml.cloud.ibm.com
WATSON_DEPLOYMENT_ID=your-deployment-id
WATSON_SPACE_ID=your-space-id

# Mail (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

## 🤖 Machine Learning Models

| Model | Accuracy | Precision | Recall | F1-Score |
|---|---|---|---|---|
| Random Forest | 87.3% | 0.89 | 0.85 | 0.87 |
| XGBoost | 89.1% | 0.91 | 0.87 | 0.89 |
| Logistic Regression | 83.2% | 0.84 | 0.82 | 0.83 |
| Decision Tree | 81.5% | 0.82 | 0.80 | 0.81 |

**Primary Model:** XGBoost (deployed on IBM Watson ML)

### Input Features
- Personal: Age, Gender, Marital Status, Number of Children, Education
- Financial: Annual Income, Total Assets, Total Debt, Credit Score
- Employment: Employment Status, Years Employed, Occupation
- Loan: Loan Amount, Loan Term, Loan Purpose
- Credit History: Months Customer, Default Status, Prior Loans

---

## 🔌 REST API

Swagger documentation available at: `http://localhost:5000/api/docs`

**Key Endpoints:**

```
POST /api/v1/predict          → Single prediction
POST /api/v1/predict/batch    → Batch predictions
GET  /api/v1/history          → Prediction history
GET  /api/v1/stats            → Application statistics
GET  /api/v1/model/info       → Model metadata
```

---

## 🧪 Testing

```bash
pytest tests/ -v --coverage
```

---

## 📦 Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.0 |
| Database | SQLite (dev), PostgreSQL (prod) |
| ORM | SQLAlchemy + Flask-Migrate |
| ML | scikit-learn, XGBoost, pandas, numpy |
| Cloud ML | IBM Watson Machine Learning |
| Frontend | Bootstrap 5.3, Chart.js, Bootstrap Icons |
| Typography | Poppins (Google Fonts) |
| PDF | ReportLab |
| API Docs | Flask-RESTX (Swagger) |
| Auth | Flask-Login |
| Email | Flask-Mail |

---

## 👨‍💻 Developer

**[Your Name]**
- 🎓 Final Year B.Tech — Artificial Intelligence & Machine Learning
- 📧 your.email@example.com
- 💼 [LinkedIn](https://linkedin.com/in/yourprofile)
- 🐙 [GitHub](https://github.com/yourusername)

---

## 📄 License

This project is for academic purposes. All rights reserved.

---

<div align="center">
Made with ❤️ for IBM Watson · Flask · Machine Learning
</div>

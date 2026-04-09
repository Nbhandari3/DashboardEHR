# 🏥 EHR Dashboard Development

A Python-based Electronic Health Record (EHR) desktop application connected to a FHIR server, built to demonstrate real-world health informatics concepts including patient data management, regulatory compliance, and clinical workflow optimization.

---

## 🚀 Live Demo

👉 **[Launch the App](https://fapeqfrjqpeb5fxs2kdgpg.streamlit.app/)**

---

## 📋 Overview

This project simulates a functional EHR dashboard that allows healthcare staff to register, search, and update patient records in compliance with HIPAA and FHIR standards. It was developed as part of the Health Informatics program at **Kennesaw State University**.

---

## ✨ Features

- **Patient Registration** — Add new patients with demographic and clinical information
- **Patient Search** — Quickly look up records by name, ID, or other identifiers
- **Record Updates** — Edit and update existing patient information in real time
- **FHIR Integration** — Connected to a FHIR server for standardized health data exchange
- **HIPAA Compliant** — Built with data privacy and security best practices throughout

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Tkinter | Desktop GUI framework |
| FHIR (HL7) | Healthcare data standard / server connection |
| HIPAA Standards | Compliance and data privacy guidelines |

---

## 🚀 Getting Started

You can use the app instantly via the **[Live Demo](https://fapeqfrjqpeb5fxs2kdgpg.streamlit.app/)**, or run it locally by following the steps below.

### Prerequisites

Make sure you have the following installed:

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Nbhandari3/fantastic-winner.git
cd fantastic-winner/EHR
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

---

## 📁 Project Structure

```
EHR/
├── main.py              # Application entry point
├── dashboard.py         # Main dashboard UI
├── patient_register.py  # Patient registration module
├── patient_search.py    # Search functionality
├── fhir_client.py       # FHIR server connection
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## 🔒 Compliance & Standards

This application was designed with the following standards in mind:

- **HIPAA** — Patient data is handled securely; access is controlled and auditable
- **FHIR (HL7)** — Data exchange follows the FHIR R4 standard for interoperability
- **CMS Guidelines** — Built to align with Centers for Medicare & Medicaid Services data requirements

---

## 👩‍💻 Author

**Nitika Bhandari**  
M.S. Healthcare Management and Informatics — Kennesaw State University  
[LinkedIn](https://www.linkedin.com/in/nitika-bhandari-2a6221345) · [GitHub](https://github.com/Nbhandari3)

---

## 📚 Academic Context

Developed as part of the Health Informatics curriculum at Kennesaw State University. This project applies classroom concepts — including EHR system design, FHIR-based data exchange, and healthcare compliance — to a working application.

---

## 📄 License

This project is for educational purposes. Feel free to explore the code and reach out with any questions.

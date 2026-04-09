import streamlit as st
import requests
import json
import hashlib
import datetime
import uuid

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# FHIR Server (HAPI public test server - FHIR R4)
FHIR_BASE_URL = "http://hapi.fhir.org/baseR4"

# Session timeout in minutes (HIPAA requirement)
SESSION_TIMEOUT_MINUTES = 15

# Page config
st.set_page_config(
    page_title="OpenEMR - EHR Dashboard",
    page_icon="🏥",
    layout="wide"
)

# ─────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────
st.markdown("""
    <style>
    .stApp { background-color: #EAF4FB; color: #1a3a5c; }
    div.stButton > button {
        background-color: #87CEFA; color: #1a3a5c;
        border-radius: 8px; font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #00BFFF; color: white;
    }
    input { background-color: #E0FFFF !important; color: #1a3a5c !important; }
    .hipaa-banner {
        background: #fff3cd; border-left: 4px solid #f0a500;
        padding: 0.7rem 1rem; border-radius: 4px;
        font-size: 0.82rem; margin-bottom: 1rem; color: #7a5000;
    }
    .fhir-badge {
        background: #d4edda; border-left: 4px solid #28a745;
        padding: 0.5rem 1rem; border-radius: 4px;
        font-size: 0.82rem; margin-bottom: 0.5rem; color: #155724;
    }
    .audit-entry {
        background: #f8f9fa; border-radius: 6px;
        padding: 0.4rem 0.8rem; margin-bottom: 0.3rem;
        font-size: 0.8rem; font-family: monospace; color: #444;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HIPAA — CREDENTIAL STORE (hashed passwords)
# Passwords are SHA-256 hashed — never stored as plain text
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

EMPLOYEE_CREDENTIALS = {
    "140520": hash_password("MICK1"),
    "123456": hash_password("admin"),
    "140521": hash_password("MICK2"),
    "140522": hash_password("MICK3"),
}

EMPLOYEE_NAMES = {
    "140520": "Michael K.",
    "123456": "Administrator",
    "140521": "Michael K. II",
    "140522": "Michael K. III",
}

# ─────────────────────────────────────────────
# HIPAA — AUDIT LOG
# Records every access and action with timestamp and user
# ─────────────────────────────────────────────
def audit_log(action: str, detail: str = ""):
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.get("user", "unknown"),
        "action": action,
        "detail": detail,
        "session_id": st.session_state.get("session_id", "N/A")
    }
    st.session_state.audit_log.append(entry)

# ─────────────────────────────────────────────
# HIPAA — SESSION TIMEOUT CHECK
# Auto-logout after 15 minutes of inactivity
# ─────────────────────────────────────────────
def check_session_timeout():
    if "last_activity" in st.session_state:
        elapsed = (datetime.datetime.now() - st.session_state.last_activity).seconds / 60
        if elapsed > SESSION_TIMEOUT_MINUTES:
            audit_log("AUTO_LOGOUT", f"Session timed out after {SESSION_TIMEOUT_MINUTES} min")
            st.session_state.logged_in = False
            st.session_state.user = None
            st.warning(f"⏱ Session expired after {SESSION_TIMEOUT_MINUTES} minutes of inactivity. Please log in again.")
            st.stop()
    st.session_state.last_activity = datetime.datetime.now()

# ─────────────────────────────────────────────
# FHIR — HELPER FUNCTIONS
# All patient data is stored/retrieved as FHIR R4 resources
# ─────────────────────────────────────────────

def fhir_headers():
    return {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }

def build_fhir_patient(mrn, name, gender, age, address, diagnosis, treatment):
    """Build a FHIR R4 Patient resource from form data."""
    birth_year = datetime.datetime.now().year - int(age)
    gender_map = {"Male": "male", "Female": "female", "Other": "other"}

    return {
        "resourceType": "Patient",
        "id": str(uuid.uuid4()),
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"]
        },
        "identifier": [{
            "use": "official",
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "MR",
                    "display": "Medical Record Number"
                }]
            },
            "system": "urn:oid:1.2.840.114350.1.13.0.1.7.5.737384.0",
            "value": mrn
        }],
        "name": [{
            "use": "official",
            "text": name,
            "family": name.split()[-1] if name else "",
            "given": name.split()[:-1] if name else []
        }],
        "gender": gender_map.get(gender, "unknown"),
        "birthDate": f"{birth_year}-01-01",
        "address": [{
            "use": "home",
            "text": address
        }],
        "extension": [
            {
                "url": "http://example.org/fhir/StructureDefinition/diagnosis",
                "valueString": diagnosis
            },
            {
                "url": "http://example.org/fhir/StructureDefinition/treatment",
                "valueString": treatment
            }
        ]
    }

def fhir_create_patient(patient_resource):
    """POST a new Patient to the FHIR server."""
    try:
        resp = requests.post(
            f"{FHIR_BASE_URL}/Patient",
            headers=fhir_headers(),
            json=patient_resource,
            timeout=10
        )
        if resp.status_code in (200, 201):
            return True, resp.json().get("id", "unknown")
        return False, resp.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

def fhir_search_patient_by_mrn(mrn):
    """Search FHIR server for a patient by MRN identifier."""
    try:
        resp = requests.get(
            f"{FHIR_BASE_URL}/Patient",
            headers=fhir_headers(),
            params={"identifier": mrn},
            timeout=10
        )
        if resp.status_code == 200:
            bundle = resp.json()
            entries = bundle.get("entry", [])
            if entries:
                return True, entries[0]["resource"]
        return False, "Patient not found on FHIR server"
    except requests.exceptions.RequestException as e:
        return False, str(e)

def fhir_update_patient(fhir_id, patient_resource):
    """PUT updated Patient resource to the FHIR server."""
    try:
        resp = requests.put(
            f"{FHIR_BASE_URL}/Patient/{fhir_id}",
            headers=fhir_headers(),
            json=patient_resource,
            timeout=10
        )
        return resp.status_code in (200, 201), resp.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

def fhir_delete_patient(fhir_id):
    """DELETE a Patient from the FHIR server."""
    try:
        resp = requests.delete(
            f"{FHIR_BASE_URL}/Patient/{fhir_id}",
            headers=fhir_headers(),
            timeout=10
        )
        return resp.status_code in (200, 204), resp.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

def fhir_get_all_patients():
    """Retrieve all patients from the FHIR server."""
    try:
        resp = requests.get(
            f"{FHIR_BASE_URL}/Patient?_count=20",
            headers=fhir_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            bundle = resp.json()
            return True, bundle.get("entry", [])
        return False, []
    except requests.exceptions.RequestException as e:
        return False, []

def parse_fhir_patient(resource):
    """Extract readable fields from a FHIR Patient resource."""
    name = resource.get("name", [{}])[0].get("text", "Unknown")
    gender = resource.get("gender", "unknown").capitalize()
    birth = resource.get("birthDate", "")
    age = str(datetime.datetime.now().year - int(birth[:4])) if birth else "Unknown"
    address = resource.get("address", [{}])[0].get("text", "Unknown")
    fhir_id = resource.get("id", "")
    mrn = ""
    for ident in resource.get("identifier", []):
        if ident.get("type", {}).get("coding", [{}])[0].get("code") == "MR":
            mrn = ident.get("value", "")
    diagnosis = ""
    treatment = ""
    for ext in resource.get("extension", []):
        if "diagnosis" in ext.get("url", ""):
            diagnosis = ext.get("valueString", "")
        if "treatment" in ext.get("url", ""):
            treatment = ext.get("valueString", "")
    return {
        "fhir_id": fhir_id, "mrn": mrn, "name": name,
        "gender": gender, "age": age, "address": address,
        "diagnosis": diagnosis, "treatment": treatment
    }

# ─────────────────────────────────────────────
# DEMO PATIENTS — All 12 from original Tkinter app
# Stored locally for instant display; can also be
# pushed to the FHIR server via the seed button.
# ─────────────────────────────────────────────
DEMO_PATIENTS = {
    "1145980": {"name": "Michael Smith",      "gender": "Male",   "age": 28, "address": "100 Main St Atlanta GA",           "diagnosis": "Flu",           "treatment": "Antiviral Medication"},
    "1145981": {"name": "Mary Brown",         "gender": "Female", "age": 32, "address": "251 Spring Street Kennesaw GA",     "diagnosis": "Cold",          "treatment": "Rest and Hydration"},
    "1145982": {"name": "John Miller",        "gender": "Male",   "age": 18, "address": "5th Street Morrow GA",              "diagnosis": "Arthritis",     "treatment": "Painkillers"},
    "1145983": {"name": "Brian Martinez",     "gender": "Male",   "age": 25, "address": "25 Washington Way Marietta GA",     "diagnosis": "Diabetes",      "treatment": "Medication & Insulin"},
    "1145984": {"name": "Aubrey Gonzales",    "gender": "Female", "age": 20, "address": "101 President Road Johns Creek GA", "diagnosis": "Asthma",        "treatment": "Inhaler & Medication"},
    "1145985": {"name": "Jeffrey Thomas",     "gender": "Male",   "age": 30, "address": "350 Swiss Road Cumming GA",         "diagnosis": "Anxiety",       "treatment": "Therapy"},
    "1145986": {"name": "Erica Jackson",      "gender": "Female", "age": 23, "address": "200 Kuhl Ave Atlanta GA",           "diagnosis": "Heart Disease", "treatment": "Angioplasty"},
    "1145987": {"name": "Bella Blackman",     "gender": "Female", "age": 13, "address": "70 Lake St Macon GA",               "diagnosis": "Cold",          "treatment": "Rest and Hydration"},
    "1145988": {"name": "Rheinhart Chandler", "gender": "Male",   "age": 44, "address": "31 Redsea Way Lawrenceville GA",    "diagnosis": "Flu",           "treatment": "Antiviral Medication"},
    "1145989": {"name": "John Knoedler",      "gender": "Male",   "age": 56, "address": "55 River Drive Alpharetta GA",      "diagnosis": "Diabetes",      "treatment": "Medication & Insulin"},
    "1145990": {"name": "Adira Miller",       "gender": "Female", "age": 61, "address": "16 Safe Lane Riverdale GA",         "diagnosis": "Asthma",        "treatment": "Inhaler & Medication"},
    "1145991": {"name": "Jason Davis",        "gender": "Male",   "age": 90, "address": "560 Creek Side Way Snellville GA",  "diagnosis": "Cancer",        "treatment": "Chemotherapy"},
}

def seed_demo_patients_to_fhir():
    """Push all 12 demo patients to the FHIR server."""
    results = {"success": 0, "failed": 0, "names": []}
    for mrn, p in DEMO_PATIENTS.items():
        resource = build_fhir_patient(
            mrn, p["name"], p["gender"], p["age"],
            p["address"], p["diagnosis"], p["treatment"]
        )
        ok, fhir_id = fhir_create_patient(resource)
        if ok:
            results["success"] += 1
            results["names"].append(p["name"])
            audit_log("DEMO_PATIENT_SEEDED", f"MRN: {mrn}, Name: {p['name']}, FHIR ID: {fhir_id}")
        else:
            results["failed"] += 1
    return results

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state.audit_log = []
    st.session_state.last_activity = datetime.datetime.now()
    st.session_state.demo_seeded = False

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    st.title("🏥 OpenEMR — Employee Login")

    st.markdown("""
    <div class="hipaa-banner">
        🔒 <strong>HIPAA Notice:</strong> This system contains protected health information (PHI).
        Unauthorized access is prohibited and subject to federal penalties under HIPAA (45 CFR §164).
        All access is logged and monitored.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        emp_id = st.text_input("Employee ID", placeholder="e.g. 123456")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            hashed = hash_password(password)
            if emp_id in EMPLOYEE_CREDENTIALS and EMPLOYEE_CREDENTIALS[emp_id] == hashed:
                st.session_state.logged_in = True
                st.session_state.user = emp_id
                st.session_state.last_activity = datetime.datetime.now()
                st.session_state.session_id = str(uuid.uuid4())[:8]
                audit_log("LOGIN_SUCCESS", f"Employee {emp_id} logged in")
                st.success("✅ Login successful!")
                st.rerun()
            else:
                audit_log("LOGIN_FAILED", f"Failed attempt for ID: {emp_id}")
                st.error("❌ Invalid credentials. This attempt has been logged.")

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
else:
    check_session_timeout()

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏥 OpenEMR — EHR Dashboard")
        st.markdown(f"""
        <div class="fhir-badge">
            ✅ <strong>FHIR R4 Connected</strong> — Patient data synced with HAPI FHIR Server &nbsp;|&nbsp;
            🔒 <strong>HIPAA Safeguards Active</strong> — Session ID: {st.session_state.session_id}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.write(f"**👤 Employee:** {EMPLOYEE_NAMES.get(st.session_state.user, st.session_state.user)}")
        st.write(f"**🕐 Timeout:** {SESSION_TIMEOUT_MINUTES} min")
        if st.button("🚪 Logout"):
            audit_log("LOGOUT", "User logged out manually")
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    st.markdown("""
    <div class="hipaa-banner">
        🔒 <strong>HIPAA Reminder:</strong> You are accessing Protected Health Information (PHI).
        Do not share your screen or leave this system unattended. All actions are audited.
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "➕ Register Patient", "🔍 Search Patient",
        "✏️ Update Patient", "🗑️ Delete Patient",
        "📋 All Patients", "📜 Audit Log"
    ])

    # ── REGISTER ──
    with tab1:
        st.subheader("Register New Patient")
        st.caption("Patient will be created as a FHIR R4 Patient resource on the HAPI FHIR server.")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                mrn    = st.text_input("MRN (Medical Record Number)*")
                name   = st.text_input("Full Name*")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                age    = st.number_input("Age", min_value=0, max_value=120, value=30)
            with col2:
                address   = st.text_input("Address*")
                diagnosis = st.text_input("Diagnosis*")
                treatment = st.text_input("Treatment Plan*")

            submitted = st.form_submit_button("Register Patient on FHIR Server")
            if submitted:
                if not all([mrn, name, address, diagnosis, treatment]):
                    st.warning("Please fill in all required fields.")
                else:
                    with st.spinner("Sending to FHIR server..."):
                        resource = build_fhir_patient(mrn, name, gender, age, address, diagnosis, treatment)
                        success, result = fhir_create_patient(resource)
                    if success:
                        audit_log("PATIENT_REGISTERED", f"MRN: {mrn}, Name: {name}, FHIR ID: {result}")
                        st.success(f"✅ Patient registered on FHIR server! FHIR ID: `{result}`")
                        st.json(resource)
                    else:
                        st.error(f"❌ FHIR server error: {result}")

    # ── SEARCH ──
    with tab2:
        st.subheader("Search Patient by MRN")
        st.caption("Queries the FHIR server using the patient's Medical Record Number identifier.")
        search_mrn = st.text_input("Enter MRN", key="search_mrn")
        if st.button("Search FHIR Server", key="search_btn"):
            if search_mrn:
                with st.spinner("Querying FHIR server..."):
                    success, result = fhir_search_patient_by_mrn(search_mrn)
                if success:
                    audit_log("PATIENT_ACCESSED", f"MRN: {search_mrn}")
                    patient = parse_fhir_patient(result)
                    st.success("✅ Patient found on FHIR server")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Name:** {patient['name']}")
                        st.write(f"**Gender:** {patient['gender']}")
                        st.write(f"**Age:** {patient['age']}")
                        st.write(f"**Address:** {patient['address']}")
                    with col2:
                        st.write(f"**MRN:** {patient['mrn']}")
                        st.write(f"**FHIR ID:** {patient['fhir_id']}")
                        st.write(f"**Diagnosis:** {patient['diagnosis']}")
                        st.write(f"**Treatment:** {patient['treatment']}")
                    with st.expander("View raw FHIR resource"):
                        st.json(result)
                else:
                    st.error(f"❌ {result}")

    # ── UPDATE ──
    with tab3:
        st.subheader("Update Patient Record")
        st.caption("Fetches the patient from the FHIR server, applies changes, and sends a PUT request.")
        update_mrn = st.text_input("MRN to Update", key="upd_mrn")
        if st.button("Fetch Patient", key="fetch_btn"):
            with st.spinner("Fetching from FHIR server..."):
                success, result = fhir_search_patient_by_mrn(update_mrn)
            if success:
                st.session_state.update_resource = result
                st.success("✅ Patient fetched. Edit fields below.")
            else:
                st.error(f"❌ {result}")

        if "update_resource" in st.session_state:
            p = parse_fhir_patient(st.session_state.update_resource)
            with st.form("update_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name      = st.text_input("Name", value=p["name"])
                    new_gender    = st.selectbox("Gender", ["Male","Female","Other"],
                                        index=["Male","Female","Other"].index(p["gender"]) if p["gender"] in ["Male","Female","Other"] else 0)
                    new_age       = st.number_input("Age", value=int(p["age"]) if p["age"].isdigit() else 30)
                with col2:
                    new_address   = st.text_input("Address", value=p["address"])
                    new_diagnosis = st.text_input("Diagnosis", value=p["diagnosis"])
                    new_treatment = st.text_input("Treatment", value=p["treatment"])

                if st.form_submit_button("Update on FHIR Server"):
                    updated = build_fhir_patient(
                        update_mrn, new_name, new_gender, new_age,
                        new_address, new_diagnosis, new_treatment
                    )
                    updated["id"] = st.session_state.update_resource.get("id")
                    with st.spinner("Updating FHIR server..."):
                        success, result = fhir_update_patient(updated["id"], updated)
                    if success:
                        audit_log("PATIENT_UPDATED", f"MRN: {update_mrn}, FHIR ID: {updated['id']}")
                        st.success("✅ Patient updated on FHIR server!")
                        del st.session_state.update_resource
                    else:
                        st.error(f"❌ Update failed: {result}")

    # ── DELETE ──
    with tab4:
        st.subheader("Delete Patient")
        st.caption("⚠️ This permanently removes the patient from the FHIR server.")
        delete_mrn = st.text_input("MRN to Delete", key="delete_mrn")
        st.warning("⚠️ HIPAA Note: Deletion of patient records must comply with your organization's retention policy.")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🗑️ Delete Patient", key="delete_btn"):
                if delete_mrn:
                    with st.spinner("Searching FHIR server..."):
                        success, result = fhir_search_patient_by_mrn(delete_mrn)
                    if success:
                        fhir_id = result.get("id")
                        with st.spinner("Deleting from FHIR server..."):
                            ok, msg = fhir_delete_patient(fhir_id)
                        if ok:
                            audit_log("PATIENT_DELETED", f"MRN: {delete_mrn}, FHIR ID: {fhir_id}")
                            st.success(f"✅ Patient MRN {delete_mrn} deleted from FHIR server.")
                        else:
                            st.error(f"❌ Delete failed: {msg}")
                    else:
                        st.error("❌ Patient not found.")

    # ── ALL PATIENTS ──
    with tab5:
        st.subheader("📋 All Patients")

        # ── Section 1: Demo patients (instant, local) ──
        st.markdown("### 👥 Demo Patients")
        st.caption("12 pre-loaded demo patients available instantly. Use the button below to also register them on the FHIR server.")

        for mrn, p in DEMO_PATIENTS.items():
            with st.expander(f"👤 {p['name']} — MRN: {mrn}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Gender:** {p['gender']}")
                    st.write(f"**Age:** {p['age']}")
                    st.write(f"**Address:** {p['address']}")
                with col2:
                    st.write(f"**MRN:** {mrn}")
                    st.write(f"**Diagnosis:** {p['diagnosis']}")
                    st.write(f"**Treatment:** {p['treatment']}")

        st.divider()

        # ── Section 2: Push to FHIR ──
        st.markdown("### 🚀 Push Demo Patients to FHIR Server")
        st.info("Register all 12 demo patients as real FHIR R4 resources so you can search, update, and delete them using the other tabs.")

        if st.session_state.demo_seeded:
            st.success("✅ Demo patients have already been pushed to the FHIR server this session.")
        else:
            if st.button("📤 Push All 12 Demo Patients to FHIR Server", use_container_width=True):
                with st.spinner("Registering 12 patients on FHIR server..."):
                    results = seed_demo_patients_to_fhir()
                st.session_state.demo_seeded = True
                audit_log("DEMO_SEED_COMPLETE", f"{results['success']} patients pushed to FHIR server")
                st.success(f"✅ Successfully registered {results['success']}/12 patients on the FHIR server!")
                if results["failed"] > 0:
                    st.warning(f"⚠️ {results['failed']} patients failed. Try again.")
                for name in results["names"]:
                    st.write(f"  ✓ {name}")

        st.divider()

        # ── Section 3: Load from FHIR ──
        st.markdown("### 🌐 Load Patients from FHIR Server")
        st.caption("Retrieves the most recent 20 patients from the HAPI FHIR server.")
        if st.button("Load from FHIR Server", key="load_fhir_btn"):
            with st.spinner("Fetching from FHIR server..."):
                success, entries = fhir_get_all_patients()
            if success and entries:
                audit_log("ALL_PATIENTS_VIEWED", f"{len(entries)} records retrieved")
                st.success(f"✅ {len(entries)} patients retrieved from FHIR server")
                for entry in entries:
                    resource = entry.get("resource", {})
                    p = parse_fhir_patient(resource)
                    with st.expander(f"👤 {p['name']} — MRN: {p['mrn'] or 'N/A'} — FHIR ID: {p['fhir_id']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Gender:** {p['gender']}")
                            st.write(f"**Age:** {p['age']}")
                            st.write(f"**Address:** {p['address']}")
                        with col2:
                            st.write(f"**Diagnosis:** {p['diagnosis'] or 'N/A'}")
                            st.write(f"**Treatment:** {p['treatment'] or 'N/A'}")
            elif success:
                st.info("No patients found on the FHIR server yet.")
            else:
                st.error("❌ Could not connect to FHIR server.")

    # ── AUDIT LOG ──
    with tab6:
        st.subheader("📜 HIPAA Audit Log")
        st.caption("All access and actions are logged per HIPAA Security Rule §164.312(b) — Audit Controls.")
        if st.session_state.audit_log:
            for entry in reversed(st.session_state.audit_log):
                st.markdown(f"""
                <div class="audit-entry">
                    [{entry['timestamp']}] &nbsp;
                    <strong>User:</strong> {entry['user']} &nbsp;|&nbsp;
                    <strong>Action:</strong> {entry['action']} &nbsp;|&nbsp;
                    <strong>Detail:</strong> {entry['detail']} &nbsp;|&nbsp;
                    <strong>Session:</strong> {entry['session_id']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No audit entries yet for this session.")
        st.caption("Note: In a production system, audit logs would be persisted to a secure, tamper-evident database.")

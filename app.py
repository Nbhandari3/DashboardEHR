import streamlit as st

# -----------------------------
# Custom Background Color
# -----------------------------
page_bg_color = "lightblue" 
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {page_bg_color};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Employee Login Credentials
# -----------------------------
employee_signin = {
    "140520": "MICK1",
    "123456": "admin",
    "140521": "MICK2",
    "140522": "MICK3"
}

# -----------------------------
# Initialize Session State
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if "patients" not in st.session_state:
    st.session_state.patients = {
        "1145980": [
            "Name: Michael Smith",
            "Gender: Male",
            "Age: 28",
            "Address: 100 Main St Atlanta GA",
            "Diagnosis: Flu",
            "Treatment: Antiviral Medication"
        ],
        "1145981": [
            "Name: Mary Brown",
            "Gender: Female",
            "Age: 32",
            "Address: 251 Spring Street Kennesaw GA",
            "Diagnosis: Cold",
            "Treatment: Rest and Hydration"
        ]
    }

# -----------------------------
# LOGIN PAGE
# -----------------------------
if not st.session_state.logged_in:
    st.title("Employee Login")

    emp_id = st.text_input("Employee ID (123456)", key="login_emp")
    password = st.text_input("Password (admin)", type="password", key="login_pass")

    if st.button("Login", key="login_btn"):
        if emp_id in employee_signin and employee_signin[emp_id] == password:
            st.session_state.logged_in = True
            st.session_state.user = emp_id
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

# -----------------------------
# MAIN APP
# -----------------------------
else:
    st.title("OPEN EMR System")
    st.write(f"**Logged in as Employee ID:** {st.session_state.user}")

    # -----------------------------
    # REGISTER PATIENT
    # -----------------------------
    st.subheader("Register Patient")
    with st.expander("Add New Patient"):
        mrn = st.text_input("MRN", key="reg_mrn")
        name = st.text_input("Name", key="reg_name")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="reg_gender")
        age = st.number_input("Age", min_value=0, max_value=120, key="reg_age")
        address = st.text_input("Address", key="reg_address")
        diagnosis = st.text_input("Diagnosis", key="reg_diag")
        treatment = st.text_input("Treatment", key="reg_treat")

        if st.button("Register Patient", key="register_btn"):
            if mrn in st.session_state.patients:
                st.warning("Patient already exists!")
            else:
                st.session_state.patients[mrn] = [
                    f"Name: {name}",
                    f"Gender: {gender}",
                    f"Age: {age}",
                    f"Address: {address}",
                    f"Diagnosis: {diagnosis}",
                    f"Treatment: {treatment}"
                ]
                st.success("Patient registered successfully!")

    # -----------------------------
    # UPDATE PATIENT
    # -----------------------------
    st.subheader("Update Patient")
    with st.expander("Update Existing Patient"):
        update_mrn = st.text_input("MRN to Update", key="upd_mrn")

        if update_mrn in st.session_state.patients:
            st.write("**Current Details:**")
            for d in st.session_state.patients[update_mrn]:
                st.write(d)

            field = st.selectbox(
                "Field to Update",
                ["Name", "Gender", "Age", "Address", "Diagnosis", "Treatment"],
                key="upd_field"
            )

            new_value = st.text_input(
                f"New value for {field}",
                key="upd_value"
            )

            if st.button("Update Patient", key="update_btn"):
                field_index = {
                    "Name": 0,
                    "Gender": 1,
                    "Age": 2,
                    "Address": 3,
                    "Diagnosis": 4,
                    "Treatment": 5
                }
                idx = field_index[field]
                st.session_state.patients[update_mrn][idx] = f"{field}: {new_value}"
                st.success("Patient updated successfully!")

        elif update_mrn:
            st.warning("Patient MRN not found")

    # -----------------------------
    # SEARCH PATIENT
    # -----------------------------
    st.subheader("Search Patient")
    search_mrn = st.text_input("Enter MRN", key="search_mrn")

    if st.button("Search", key="search_btn"):
        if search_mrn in st.session_state.patients:
            for d in st.session_state.patients[search_mrn]:
                st.write(d)
        else:
            st.error("Patient not found")

    # -----------------------------
    # DELETE PATIENT
    # -----------------------------
    st.subheader("Delete Patient")
    delete_mrn = st.text_input("MRN to Delete", key="delete_mrn")

    if st.button("Delete Patient", key="delete_btn"):
        if delete_mrn in st.session_state.patients:
            del st.session_state.patients[delete_mrn]
            st.success("Patient deleted successfully!")
        else:
            st.error("Patient not found")

    # -----------------------------
    # SHOW ALL PATIENTS
    # -----------------------------
    st.subheader("All Patients")

    if st.button("Show All Patients", key="show_all_btn"):
        for mrn, details in st.session_state.patients.items():
            st.markdown(f"### MRN: {mrn}")
            for d in details:
                st.write(d)
            st.divider()

    # -----------------------------
    # LOGOUT
    # -----------------------------
    if st.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

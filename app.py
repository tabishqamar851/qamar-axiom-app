import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from fpdf import FPDF
import io
import datetime

# --- ENTERPRISE CONFIGURATION ---
st.set_page_config(page_title="Axiom Enterprise Core", page_icon="🏢", layout="wide")

# --- SESSION STATE (LOGIN) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- MODULE 1: PDF CERTIFICATE GENERATOR ---
def generate_pdf(df, violations):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Header
    pdf.cell(200, 10, txt="Axiom Risk Compliance Certificate", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Audit Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Executive Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Executive Summary", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt=f"Total Portfolio Value: INR {df['Loan_Amount'].sum():,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Total Files Audited: {len(df)}", ln=True)
    pdf.cell(200, 10, txt=f"Risk Breaches Found: {len(violations)}", ln=True)
    pdf.ln(10)
    
    # Status
    if len(violations) > 0:
        pdf.set_text_color(200, 0, 0)
        pdf.cell(200, 10, txt="AUDIT STATUS: FAILED - HIGH RISK DETECTED", ln=True)
    else:
        pdf.set_text_color(0, 150, 0)
        pdf.cell(200, 10, txt="AUDIT STATUS: PASSED - COMPLIANT", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- MODULE 2: LOGIN SYSTEM ---
def login():
    st.markdown("<h1 style='text-align: center;'>🏢 Axiom Secure Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Restricted Access for Audit Officers</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Officer ID")
        password = st.text_input("Secure Key", type="password")
        if st.button("Authenticate"):
            if username == "admin" and password == "admin":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("❌ Access Denied")

# --- MODULE 3: MAIN DASHBOARD ---
def dashboard():
    # Sidebar
    with st.sidebar:
        st.title("Axiom Nav")
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.rerun()
        st.info("System Status: ● Online")

    # Main Screen
    st.title("📊 Enterprise Risk Dashboard")
    st.write("Upload Standardized Loan Tape (Excel/CSV)")

    uploaded_file = st.file_uploader("Upload File", type=["xlsx", "csv"])

    if uploaded_file:
        # 1. READ FILE STRICTLY
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # 2. VALIDATE COLUMNS (Professional Check)
            required_cols = ['Loan_Amount', 'Collateral_Value']
            missing = [c for c in required_cols if c not in df.columns]
            
            if missing:
                st.error(f"❌ REJECTED: Invalid File Format. Missing columns: {missing}")
                st.warning("Please upload the 'Standard_Audit_Template.xlsx'")
            
            else:
                # 3. RUN AUDIT LOGIC
                df['LTV'] = (df['Loan_Amount'] / df['Collateral_Value']) * 100
                df['Status'] = df['LTV'].apply(lambda x: 'High Risk' if x > 75 else 'Safe')
                
                violations = df[df['Status'] == 'High Risk']
                
                # 4. SHOW PROFESSIONAL METRICS
                st.success("✅ File Validated & Processed")
                st.markdown("---")
                
                # Top Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Portfolio", f"₹ {df['Loan_Amount'].sum()/100000:.2f} L")
                m2.metric("Total Files", len(df))
                m3.metric("Safe Loans", len(df) - len(violations))
                m4.metric("Risk Alerts", len(violations), delta_color="inverse")
                
                # 5. CHARTS (The Visuals)
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.subheader("Risk Distribution")
                    st.bar_chart(df['Status'].value_counts(), color=["#FF4B4B", "#00CC96"])
                with c2:
                    st.subheader("LTV Trends")
                    st.line_chart(df['LTV'])
                
                # 6. REPORTING
                st.write("### 🚨 Breach Report")
                if not violations.empty:
                    st.dataframe(violations.style.applymap(lambda x: 'color: red', subset=['Status']))
                else:
                    st.success("No Violations Found.")

                # PDF Button
                st.write("---")
                if st.button("Generate Official Audit Certificate"):
                    pdf_bytes = generate_pdf(df, violations)
                    st.download_button("Download Certificate (PDF)", pdf_bytes, "Axiom_Certificate.pdf", "application/pdf")

        except Exception as e:
            st.error(f"System Error: {e}")

# --- APP START ---
if st.session_state['logged_in']:
    dashboard()
else:
    login()

import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from fpdf import FPDF
import io
import re
import datetime

# --- ENTERPRISE CONFIG ---
st.set_page_config(page_title="Axiom Enterprise Core", page_icon="🏢", layout="wide")

# --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #004e92; color: white;}
    .metric-card {background-color: white; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE (LOGIN) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- MODULE 1: AUTHENTICATION ---
def login():
    st.title("🏢 Axiom Secure Portal")
    st.write("NBFC Enterprise Access")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Secure Login"):
            if username == "admin" and password == "admin":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Access Denied: Invalid Credentials")

# --- MODULE 2: PDF REPORT GENERATOR ---
def generate_pdf(df, violations):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Axiom Compliance Certificate", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Audit Summary", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total Files Scanned: {len(df)}", ln=True)
    pdf.cell(200, 10, txt=f"Risk Violations Found: {len(violations)}", ln=True)
    pdf.ln(10)
    
    # Risk Assessment
    if len(violations) > 0:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(200, 10, txt="STATUS: HIGH RISK DETECTED", ln=True)
    else:
        pdf.set_text_color(0, 128, 0)
        pdf.cell(200, 10, txt="STATUS: COMPLIANT", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- MODULE 3: INTELLIGENT PARSER ---
def parse_raw_text_to_df(text):
    lines = text.split('\n')
    data = []
    for line in lines:
        if not line.strip(): continue
        clean_line = line.replace('|', '').replace("'", "").replace(',', '') 
        numbers = re.findall(r'\d{4,10}', clean_line)
        
        if len(numbers) >= 2:
            try:
                loan_amt = float(numbers[0])
                coll_val = float(numbers[1])
                parts = clean_line.split()
                loan_id = parts[0] if parts else "Unknown"
                data.append({"Loan_ID": loan_id, "Loan_Amount": loan_amt, "Collateral_Value": coll_val})
            except:
                pass
    return pd.DataFrame(data)

# --- MAIN DASHBOARD LOGIC ---
def dashboard():
    # Sidebar Navigation
    with st.sidebar:
        st.title("Axiom Enterprise")
        menu = st.radio("Navigation", ["Dashboard", "Audit Engine", "Reports"])
        st.write("---")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- PAGE: DASHBOARD ---
    if menu == "Dashboard":
        st.title("📊 Executive Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("System Status", "Online", "Secure")
        col2.metric("RBI Compliance", "Active", "Updated")
        col3.metric("Pending Audits", "Ready")
        st.info("👋 Welcome, Admin. Select 'Audit Engine' to begin.")

    # --- PAGE: AUDIT ENGINE ---
    elif menu == "Audit Engine":
        st.title("🛡️ Universal Audit Engine")
        st.write("Upload Raw Data (Images, PDFs, Excel) for Risk Scoring.")
        
        uploaded_file = st.file_uploader("Secure Upload", type=["png", "jpg", "pdf", "xlsx", "csv"])
        
        if uploaded_file:
            df = pd.DataFrame()
            
            # FILE PROCESSING
            if uploaded_file.name.endswith(('.png', '.jpg')):
                st.info("Processing Image via OCR Core...")
                try:
                    image = Image.open(uploaded_file)
                    st.image(image, width=200)
                    raw_text = pytesseract.image_to_string(image)
                    df = parse_raw_text_to_df(raw_text)
                except:
                    st.error("OCR Engine Error. Check System Logs.")
            
            elif uploaded_file.name.endswith(('.xlsx', '.csv')):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
            
            # AUDIT LOGIC (WITH CHARTS)
            if not df.empty:
                st.success("✅ Data Structure Identified")
                
                # Normalize Columns
                num_df = df.select_dtypes(include=['number'])
                if 'Loan_Amount' not in df.columns and num_df.shape[1] >= 2:
                    df['Loan_Amount'] = num_df.iloc[:, 0]
                    df['Collateral_Value'] = num_df.iloc[:, 1]
                
                if 'Loan_Amount' in df.columns and 'Collateral_Value' in df.columns:
                    # 1. CALCULATE RISK
                    df['LTV'] = (df['Loan_Amount'] / df['Collateral_Value']) * 100
                    df['Status'] = df['LTV'].apply(lambda x: 'CRITICAL RISK' if x > 75 else 'Compliant')
                    
                    violations = df[df['Status'] == 'CRITICAL RISK']
                    safe_loans = df[df['Status'] == 'Compliant']
                    
                    # 2. PROFESSIONAL VISUAL DASHBOARD
                    st.markdown("## 📊 Executive Audit Dashboard")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Portfolio", f"₹ {df['Loan_Amount'].sum()/100000:.2f} L")
                    m2.metric("Files Audited", len(df))
                    m3.metric("Compliant Loans", len(safe_loans))
                    m4.metric("Risk Alerts", len(violations), delta="-High Risk" if not violations.empty else "Safe")
                    
                    st.write("---")

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.subheader("Risk Distribution")
                        chart_data = df['Status'].value_counts()
                        st.bar_chart(chart_data, color=["#FF4B4B", "#00CC96"]) # Red/Green

                    with c2:
                        st.subheader("LTV Spectrum")
                        st.line_chart(df['LTV'])
                        st.caption("Spikes above 75% indicate violations.")

                    # 3. DETAILED DATA TABLE
                    st.write("### 📉 Detailed Account Analysis")
                    if not violations.empty:
                        st.error(f"🚨 ACTION REQUIRED: {len(violations)} Accounts Exceed Regulatory Limits")
                        st.dataframe(violations.style.applymap(lambda x: 'background-color: #ffcdd2; color: black', subset=['Status']))
                    else:
                        st.success("✅ Audit Passed: All Accounts adhere to RBI Guidelines")
                        st.dataframe(df)

                    # 4. REPORT GENERATION
                    st.write("---")
                    st.subheader("📑 Compliance Certification")
                    if st.button("Generate Signed PDF Report"):
                        pdf_bytes = generate_pdf(df, violations)
                        st.download_button(
                            label="⬇️ Download Official Certificate",
                            data=pdf_bytes,
                            file_name="Axiom_Audit_Certificate.pdf",
                            mime="application/pdf"
                        )
                    
                    st.markdown("---")
                    st.caption("🔒 CONFIDENTIAL: This report is for internal compliance use only. Generated by Axiom Enterprise Core.")
                else:
                    st.error("❌ Data Unreadable: Could not identify financial columns.")

    # --- PAGE: REPORTS ---
    elif menu == "Reports":
        st.title("🗄️ Audit Logs")
        st.write("No historical logs found (Session Storage Only).")

# --- APP ENTRY POINT ---
if st.session_state['logged_in']:
    dashboard()
else:
    login()

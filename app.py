import streamlit as st
import pandas as pd
import io
import datetime
from fpdf import FPDF
import xlsxwriter 

# --- ENTERPRISE CONFIG ---
st.set_page_config(page_title="Axiom Enterprise Core", page_icon="🏢", layout="wide")

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- MODULE 1: THE SILENT FIXER (Brain) ---
def smart_fix_data(df):
    """
    Silently fixes files that are comma-separated or missing headers.
    """
    # 1. Fix "Stuck in Column A" (Comma Separation)
    if df.shape[1] == 1:
        try:
            # Split Column A by comma
            first_col = df.iloc[:, 0].astype(str)
            df = first_col.str.split(',', expand=True)
        except:
            pass

    # 2. Fix "Missing Headers" (If Row 1 is data like '101')
    # Check if the first cell is a number (like 101)
    try:
        first_cell = str(df.iloc[0, 0])
        if first_cell.isdigit():
            # The user uploaded raw data without headers. 
            # We will manually assign the correct headers based on your data format.
            # Your Format: ID, Name, Loan, Collateral, Extra
            new_headers = ["Loan_ID", "Customer_Name", "Loan_Amount", "Collateral_Value", "Cash_Paid"]
            
            # Ensure we don't have more columns than headers
            if df.shape[1] > len(new_headers):
                new_headers += [f"Extra_{i}" for i in range(df.shape[1] - len(new_headers))]
            elif df.shape[1] < len(new_headers):
                new_headers = new_headers[:df.shape[1]]
                
            df.columns = new_headers
    except:
        pass

    return df

# --- MODULE 2: PDF GENERATOR ---
def generate_pdf(df, violations):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Axiom Risk Compliance Certificate", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    # Handle clean up for PDF text
    total_val = df['Loan_Amount'].sum()
    pdf.cell(200, 10, txt=f"Total Portfolio: INR {total_val:,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Risk Violations: {len(violations)}", ln=True)
    
    if len(violations) > 0:
        pdf.set_text_color(200, 0, 0)
        pdf.cell(200, 10, txt="STATUS: HIGH RISK DETECTED", ln=True)
    else:
        pdf.set_text_color(0, 150, 0)
        pdf.cell(200, 10, txt="STATUS: COMPLIANT", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- MODULE 3: LOGIN ---
def login():
    st.markdown("<h1 style='text-align: center;'>🏢 Axiom Secure Portal</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        username = st.text_input("Officer ID")
        password = st.text_input("Secure Key", type="password")
        if st.button("Authenticate", use_container_width=True):
            if username == "admin" and password == "admin":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("❌ Access Denied")

# --- MODULE 4: DASHBOARD ---
def dashboard():
    with st.sidebar:
        st.title("Axiom Nav")
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.title("📊 Enterprise Risk Dashboard")
    uploaded_file = st.file_uploader("Upload Loan Tape", type=["xlsx", "csv"])

    if uploaded_file:
        try:
            # 1. LOAD DATA
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, header=None) # Assume no header first
            else:
                df = pd.read_excel(uploaded_file, header=None)

            # 2. RUN SILENT FIXER (The Logic for YOUR file)
            df = smart_fix_data(df)
            
            # 3. VERIFY & AUDIT
            # Ensure numbers are actual numbers (remove any stray text)
            if 'Loan_Amount' in df.columns:
                df['Loan_Amount'] = pd.to_numeric(df['Loan_Amount'], errors='coerce')
            if 'Collateral_Value' in df.columns:
                df['Collateral_Value'] = pd.to_numeric(df['Collateral_Value'], errors='coerce')
            
            # Drop bad rows
            df = df.dropna(subset=['Loan_Amount', 'Collateral_Value'])

            if not df.empty:
                # AUDIT LOGIC
                df['LTV'] = (df['Loan_Amount'] / df['Collateral_Value']) * 100
                df['Status'] = df['LTV'].apply(lambda x: 'High Risk' if x > 75 else 'Safe')
                violations = df[df['Status'] == 'High Risk']
                
                # METRICS
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Value", f"₹ {df['Loan_Amount'].sum()/100000:.2f} L")
                m2.metric("Violations", len(violations))
                m3.metric("Safe Loans", len(df)-len(violations))
                
                # CHARTS
                c1, c2 = st.columns([2,1])
                with c1:
                    st.bar_chart(df['Status'].value_counts(), color=["#FF4B4B", "#00CC96"])
                with c2:
                    st.line_chart(df['LTV'])
                
                # PDF
                if st.button("Generate Certificate"):
                    pdf = generate_pdf(df, violations)
                    st.download_button("Download PDF", pdf, "Certificate.pdf", "application/pdf")
                    
                if not violations.empty:
                    st.error("Risky Loans Detected:")
                    st.dataframe(violations.style.applymap(lambda x: 'color: red', subset=['Status']))
                else:
                    st.success("✅ All Loans are Safe")
            else:
                st.error("❌ Could not read data. Please use the Standard Template.")

        except Exception as e:
            st.error(f"Error: {e}")

# --- RUN ---
if st.session_state['logged_in']:
    dashboard()
else:
    login()

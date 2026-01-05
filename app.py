import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import io
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Qamar Axiom: AI Digitizer", page_icon="🤖", layout="wide")
st.title("🤖 Qamar Axiom: Image-to-Audit Engine")
st.write("Converts Images/PDFs directly into Executable Data.")

# --- ENGINE 1: TEXT-TO-TABLE PARSER ---
def parse_raw_text_to_df(text):
    """
    Takes messy text from OCR and forces it into a structured DataFrame.
    """
    lines = text.split('\n')
    data = []
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # 1. Clean common OCR mistakes
        # Replace 'O' with '0' in number-heavy parts, remove symbols like | or -
        clean_line = line.replace('|', '').replace("'", "")
        
        # 2. Extract Numbers (potential amounts)
        # Find all numbers that are 4 digits or longer (likely Loan/Collateral)
        numbers = re.findall(r'\d{4,10}', clean_line)
        
        if len(numbers) >= 2:
            # If we found 2+ big numbers, this is likely a loan row.
            # Assumption: First big number = Loan, Second = Collateral
            loan_amt = float(numbers[0])
            coll_val = float(numbers[1])
            
            # Everything before the numbers is likely the Name
            # (Simple splitting logic - can be improved with AI)
            parts = clean_line.split()
            # ID is usually the first thing
            loan_id = parts[0] if parts else "Unknown"
            
            data.append({
                "Loan_ID": loan_id,
                "Raw_Text": clean_line, # Keep raw text for verification
                "Loan_Amount": loan_amt,
                "Collateral_Value": coll_val
            })
            
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame()

# --- MAIN APP ---
uploaded_file = st.file_uploader("Upload Image or PDF", type=["png", "jpg", "jpeg", "pdf", "xlsx", "csv"])

if uploaded_file:
    df = pd.DataFrame() # Start empty
    
    # === CASE 1: IMAGES (The Feature You Asked For) ===
    if uploaded_file.name.endswith(('.png', '.jpg', '.jpeg')):
        st.info("🖼️ Converting Image to Table...")
        try:
            image = Image.open(uploaded_file)
            st.image(image, width=300)
            
            # 1. Extract Raw Text
            raw_text = pytesseract.image_to_string(image)
            
            # 2. Run the "Text-to-Table" Engine
            df = parse_raw_text_to_df(raw_text)
            
            if not df.empty:
                st.success("✅ Converted Image to Excel Table!")
                st.write("### Generated Digital Table")
                st.dataframe(df)
            else:
                st.warning("⚠️ Text found, but could not structure it. Image might be too blurry.")
                st.text(raw_text)

        except Exception as e:
            st.error(f"OCR Error: {e}")

    # === CASE 2: EXCEL/CSV (Standard) ===
    elif uploaded_file.name.endswith(('.xlsx', '.csv')):
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

    # === FINAL STEP: THE AUDIT ===
    # Only run if we successfully created a DataFrame (from Image OR Excel)
    if not df.empty:
        st.write("---")
        if st.button("🚀 Run RBI Audit on This Data"):
            st.subheader("Compliance Report")
            
            # Clean Columns
            cols = ['Loan_Amount', 'Collateral_Value']
            for c in cols:
                if c not in df.columns:
                    st.error(f"❌ Missing column: {c}")
                    st.stop()
            
            # LOGIC
            df['LTV'] = (df['Loan_Amount'] / df['Collateral_Value']) * 100
            violations = df[df['LTV'] > 75]
            
            col1, col2 = st.columns(2)
            col1.metric("Total Files Scanned", len(df))
            col2.metric("Violations Found", len(violations))
            
            if not violations.empty:
                st.error(f"⚠️ Found {len(violations)} High Risk Loans!")
                st.dataframe(violations)
                
                # Download Result
                csv = violations.to_csv(index=False).encode('utf-8')
                st.download_button("Download Breach Report", csv, "breaches.csv")
            else:
                st.success("✅ All Documents Compliant.")

import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Qamar Axiom: Universal Auditor", page_icon="🛡️", layout="centered")

# --- HEADER ---
st.title("🛡️ Qamar Axiom: Universal Auditor")
st.write("Reads Messy Excel, CSV, PDF & Images. Verifies RBI Compliance.")

# --- HELPER FUNCTION: THE SMART CLEANER ---
def clean_messy_df(df):
    """
    1. Fixes files where all data is stuck in Column A.
    2. Hunts for the real header row if there is metadata at the top.
    """
    # CASE 1: Data stuck in a single column (Comma Separated)
    if df.shape[1] == 1:
        try:
            # Treat the first column as a giant list of strings
            first_col = df.iloc[:, 0].astype(str)
            # Split by comma
            df_split = first_col.str.split(',', expand=True)
            
            # Promote the first row to be the header
            df_split.columns = df_split.iloc[0]
            df = df_split[1:].reset_index(drop=True)
            st.success("✅ Auto-Cleaned: Split single column into data table.")
        except Exception as e:
            st.warning(f"⚠️ Could not auto-split columns: {e}")

    # CASE 2: Metadata at the top (Header Hunt)
    # We look for common keywords in the first 10 rows
    keywords = ["loan", "id", "amount", "name", "collateral", "customer", "sno"]
    
    # Check if current header is already good
    current_header_str = " ".join([str(c).lower() for c in df.columns])
    if not any(k in current_header_str for k in keywords):
        st.caption("🕵️ AI is hunting for the real header row...")
        for i in range(min(10, len(df))):
            # Convert row to string to search for keywords
            row_text = " ".join([str(x).lower() for x in df.iloc[i].tolist()])
            if any(k in row_text for k in keywords):
                # Found it! Make this row the header
                df.columns = df.iloc[i]
                df = df[i+1:].reset_index(drop=True)
                st.success(f"✅ Found real header at Row {i+1}")
                break
    
    return df

# --- MAIN APP LOGIC ---
uploaded_file = st.file_uploader("Upload Document (Any Format)", type=["xlsx", "csv", "pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    
    # === TYPE 1: EXCEL & CSV ===
    if uploaded_file.name.endswith(('.xlsx', '.csv')):
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # 1. Run the Smart Cleaner
            df = clean_messy_df(df)

            # 2. Show Preview
            st.write("### 📊 Data Preview")
            st.dataframe(df.head())

            # 3. Run RBI Audit
            if st.button("🚀 Run Compliance Audit"):
                st.subheader("Audit Results")
                
                # Clean Numbers (Remove '₹', commas, spaces)
                cols_to_clean = ['Loan_Amount', 'Collateral_Value', 'Cash_Paid']
                for col in cols_to_clean:
                    # Only try to clean if the column exists
                    found_col = next((c for c in df.columns if col.lower() in str(c).lower()), None)
                    if found_col:
                        df[found_col] = pd.to_numeric(df[found_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
                        # Rename to standard name
                        df.rename(columns={found_col: col}, inplace=True)

                # RULE: LTV Check (Loan to Value > 75%)
                if 'Loan_Amount' in df.columns and 'Collateral_Value' in df.columns:
                    df['LTV'] = (df['Loan_Amount'] / df['Collateral_Value']) * 100
                    breaches = df[df['LTV'] > 75]
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Total Loans", len(df))
                    col2.metric("LTV Violations", len(breaches))
                    
                    if not breaches.empty:
                        st.error(f"⚠️ Found {len(breaches)} Loans violating 75% LTV Rule!")
                        st.dataframe(breaches)
                    else:
                        st.success("✅ All Loans are Compliant.")
                else:
                    st.error("❌ Could not find 'Loan_Amount' or 'Collateral_Value' columns even after cleaning.")

        except Exception as e:
            st.error(f"Error processing file: {e}")

    # === TYPE 2: PDF DOCUMENTS ===
    elif uploaded_file.name.endswith('.pdf'):
        st.info("📄 Scanning PDF Document...")
        text_content = ""
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content += text + "\n"
            
            st.text_area("Extracted Text:", text_content, height=250)
            
            if "Loan" in text_content or "Amount" in text_content:
                st.success("✅ Valid Financial Document Detected")
            else:
                st.warning("⚠️ Text is blurry. This might be a scanned image-PDF.")
                
        except Exception as e:
            st.error(f"PDF Error: {e}")

    # === TYPE 3: IMAGES (OCR) ===
    elif uploaded_file.name.endswith(('.png', '.jpg', '.jpeg')):
        st.info("🖼️ Reading Text from Image (OCR)...")
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Document', width=300)
            
            # The AI Eye
            extracted_text = pytesseract.image_to_string(image)
            
            st.subheader("🔍 AI Extracted Data:")
            st.text_area("Content:", extracted_text, height=200)
            
            if "Loan" in extracted_text or "Amount" in extracted_text:
                 st.success("✅ Financial Data Identified!")
            
        except Exception as e:
            st.error(f"OCR Error: {e}. (Ensure 'packages.txt' is installed)")

# --- FOOTER ---
st.write("---")
st.caption("🔒 Qamar Axiom Secure Server | RAM-Only Processing")

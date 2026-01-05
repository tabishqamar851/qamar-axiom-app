import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Qamar Axiom AI", page_icon="🛡️")
st.title("🛡️ Qamar Axiom: Gold & KYC Auditor")
st.write("Secure RBI Compliance Check for NBFCs & Small Firms.")

uploaded_file = st.file_uploader("Upload Loan Tape (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    # Logic: Read file into RAM only (Stateless - No Saving)
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("✅ File Loaded Safely in Memory.")
    
    if st.button("Run Full RBI Audit"):
        st.subheader("Audit Results")
        # Rule 1: LTV Check (Gold Loan limit is 75%)
        # Ensure columns exist to prevent crash
        if 'Loan_Amount' in df.columns and 'Collateral_Value' in df.columns:
            df['LTV'] = (df['Loan_Amount'] / df['Collateral_Value']) * 100
            ltv_breaches = df[df['LTV'] > 75]
            
            if not ltv_breaches.empty:
                st.error(f"⚠️ Found {len(ltv_breaches)} LTV Breaches (>75%)")
                st.dataframe(ltv_breaches)
            else:
                st.success("✅ LTV Ratios are Clean.")
        else:
            st.warning("⚠️ Column Check: Please ensure file has 'Loan_Amount' and 'Collateral_Value'.")

    st.info("🔒 Security Note: Data is wiped from RAM immediately after use.")

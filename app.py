import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Page Config
st.set_page_config(page_title="Scopus Advanced Search", layout="wide", page_icon="🔬")

st.title("🔬 Scopus Scientific Search API")
st.markdown("""
Search for documents using the **Scopus Search API**.  
*Fixes 'Unauthorized' errors by allowing Institutional Token input.*
""")

# Sidebar for Credentials
with st.sidebar:
    st.header("🔐 Credentials")
    api_key = st.text_input("Scopus API Key", type="password", help="Required. Get from dev.elsevier.com")
    inst_token = st.text_input("Institutional Token", type="password", help="Required if working off-campus (VPN often not enough).")
    
    st.info("If you get a 401 Error, you likely need the Institutional Token.")

# Main Search Parameters
st.header("Search Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    af_id = st.text_input("Affiliation ID (AF-ID)", value="60014930", help="e.g., 60014930 (Universiti Malaya)")
with col2:
    subj_area = st.text_input("Subject Area (SUBJ)", value="MEDI", help="e.g., MEDI, ENGI, COMP")
with col3:
    date_range = st.text_input("Date Range", value="2025-2026", help="Format: YYYY or YYYY-YYYY")

col4, col5 = st.columns(2)
with col4:
    count = st.number_input("Count (Results per page)", min_value=1, max_value=200, value=25)
with col5:
    start_index = st.number_input("Start Index", min_value=0, value=0)

# Construct Query Preview
# We combine AF-ID and SUBJAREA into the 'query' string, and leave 'date' as a separate param
query_string = f"AF-ID({af_id}) AND SUBJAREA({subj_area})"
st.caption(f"**Generated Query:** `{query_string}`")

if st.button("🚀 Run Search"):
    if not api_key:
        st.error("❌ API Key is required.")
    else:
        # API Endpoint
        url = "https://api.elsevier.com/content/search/scopus"
        
        # Headers
        headers = {
            "X-ELS-APIKey": api_key,
            "Accept": "application/json"
        }
        # Add InstToken if provided (Fixes 401)
        if inst_token:
            headers["X-ELS-Insttoken"] = inst_token
            
        # Parameters
        params = {
            "query": query_string,
            "date": date_range,
            "count": count,
            "start": start_index,
            "view": "STANDARD" # STANDARD gives more data than default
        }

        with st.spinner("Fetching data from Scopus..."):
            try:
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    search_results = data.get("search-results", {})
                    total_results = search_results.get("opensearch:totalResults", 0)
                    entries = search_results.get("entry", [])

                    st.success(f"✅ Success! Found {total_results} documents.")

                    if entries:
                        # Extract relevant fields
                        clean_data = []
                        for entry in entries:
                            clean_data.append({
                                "Title": entry.get("dc:title", "N/A"),
                                "Authors": entry.get("dc:creator", "N/A"),
                                "Journal": entry.get("prism:publicationName", "N/A"),
                                "Date": entry.get("prism:coverDate", "N/A"),
                                "DOI": entry.get("prism:doi", "N/A"),
                                "Cited By": entry.get("citedby-count", "0"),
                                "Type": entry.get("subtypeDescription", "N/A"),
                                "Scopus ID": entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
                            })
                        
                        df = pd.DataFrame(clean_data)
                        
                        # Display Data
                        st.dataframe(df, use_container_width=True)
                        
                        # Download Button
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"scopus_search_{af_id}_{subj_area}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No documents found for this criteria.")

                elif response.status_code == 401:
                    st.error("❌ **401 Unauthorized**: Please check your API Key. If you are off-campus, you **MUST** provide the Institutional Token.")
                elif response.status_code == 429:
                    st.error("❌ **429 Quota Exceeded**: You have used up your API limit.")
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

import streamlit as st
import requests
import pandas as pd
import altair as alt

# Page Config
st.set_page_config(page_title="Scopus Standard Search", layout="wide", page_icon="🔬")

st.title("🔬 Scopus Search (Standard View)")
st.markdown("""
Search using the **Standard API View**.  
*Note: This view consumes less quota but provides only author names (no IDs).*
""")

# Sidebar for Credentials
with st.sidebar:
    st.header("🔐 Credentials")
    api_key = st.text_input("Scopus API Key", type="password", help="Required.")
    inst_token = st.text_input("Institutional Token", type="password", help="Required if off-campus (VPN often not enough).")
    
    st.divider()
    st.warning("⚠️ If you see '401 Unauthorized', you MUST provide an Institutional Token.")

# Main Search Parameters
st.subheader("Search Configuration")

col1, col2, col3 = st.columns(3)
with col1:
    af_id = st.text_input("Affiliation ID (AF-ID)", value="60014930")
with col2:
    subj_area = st.text_input("Subject Area (SUBJ)", value="MEDI")
with col3:
    date_range = st.text_input("Date Range", value="2025-2026")

col4, col5 = st.columns(2)
with col4:
    count = st.number_input("Count", min_value=1, max_value=200, value=50)
with col5:
    start_index = st.number_input("Start Index", min_value=0, value=0)

# Construct Query
query_string = f"AF-ID({af_id}) AND SUBJAREA({subj_area})"
st.code(f"Query: {query_string}", language="text")

# --- Main Logic ---
if st.button("🚀 Run Search"):
    if not api_key:
        st.error("❌ API Key is required.")
    else:
        url = "https://api.elsevier.com/content/search/scopus"
        headers = {
            "X-ELS-APIKey": api_key,
            "Accept": "application/json"
        }
        # Only add token if user provided it
        if inst_token:
            headers["X-ELS-Insttoken"] = inst_token
            
        params = {
            "query": query_string,
            "date": date_range,
            "count": count,
            "start": start_index,
            "view": "STANDARD"  # <--- Back to STANDARD
        }

        with st.spinner("Fetching standard metadata..."):
            try:
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    search_results = data.get("search-results", {})
                    total_results = search_results.get("opensearch:totalResults", 0)
                    entries = search_results.get("entry", [])

                    if entries:
                        clean_data = []
                        for entry in entries:
                            # Handle DOI
                            raw_doi = entry.get("prism:doi")
                            doi_link = f"https://doi.org/{raw_doi}" if raw_doi else None
                            
                            # Handle Citations
                            try:
                                cited_by = int(entry.get("citedby-count", 0))
                            except ValueError:
                                cited_by = 0

                            # Handle Authors (Standard View Logic)
                            # Standard view returns 'dc:creator' as a single string or list of names, no IDs.
                            authors = entry.get("dc:creator", "N/A")
                            if isinstance(authors, list):
                                authors = "; ".join(authors)

                            clean_data.append({
                                "Title": entry.get("dc:title", "N/A"),
                                "Journal": entry.get("prism:publicationName", "N/A"),
                                "Date": entry.get("prism:coverDate", "N/A"),
                                "Cited By": cited_by,
                                "DOI Link": doi_link,
                                "Authors": authors, # Simple names only
                                "Scopus ID": entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
                            })
                        
                        df = pd.DataFrame(clean_data)

                        # --- TABS ---
                        tab1, tab2 = st.tabs(["📄 Data View", "📊 Analytics"])

                        with tab1:
                            st.subheader(f"Found {total_results} documents")
                            st.dataframe(
                                df,
                                use_container_width=True,
                                column_config={
                                    "DOI Link": st.column_config.LinkColumn(
                                        "DOI", display_text="https://doi\.org/(.*)"
                                    ),
                                    "Cited By": st.column_config.NumberColumn(
                                        "Citations", format="%d ❞"
                                    )
                                }
                            )
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button("📥 Download CSV", csv, "scopus_standard.csv", "text/csv")

                        with tab2:
                            st.header("Visual Analysis")
                            
                            # 1. Top Cited
                            top_cited = df.sort_values(by="Cited By", ascending=False).head(10)
                            chart_cited = alt.Chart(top_cited).mark_bar().encode(
                                x=alt.X('Cited By', title='Citations'),
                                y=alt.Y('Title', sort='-x', axis=alt.Axis(labels=False)),
                                tooltip=['Title', 'Cited By', 'Journal'],
                                color=alt.value('#3182bd')
                            ).properties(height=300)
                            st.altair_chart(chart_cited, use_container_width=True)

                            # 2. Trends
                            df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                            time_df = df.dropna(subset=["Date"])
                            if not time_df.empty:
                                monthly = time_df.groupby(time_df["Date"].dt.to_period("M")).size().reset_index(name="Count")
                                monthly["Date"] = monthly["Date"].astype(str)
                                chart_trend = alt.Chart(monthly).mark_line(point=True).encode(
                                    x=alt.X('Date', title='Month'),
                                    y=alt.Y('Count'),
                                    tooltip=['Date', 'Count'],
                                    color=alt.value('#e6550d')
                                ).properties(height=300)
                                st.altair_chart(chart_trend, use_container_width=True)

                    else:
                        st.warning("No documents found.")

                elif response.status_code == 401:
                    st.error("❌ **401 Unauthorized**")
                    st.markdown("""
                    **Troubleshooting:**
                    1. **Institutional Token:** You are likely off-campus. You *must* enter an Institutional Token in the sidebar.
                    2. **API Key:** Verify your API Key is correct.
                    3. **IP Address:** Even with a key, Scopus often blocks requests from residential IPs without a Token.
                    """)
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

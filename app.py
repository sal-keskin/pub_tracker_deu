import streamlit as st
import requests
import pandas as pd
import altair as alt

# Page Config
st.set_page_config(page_title="Scopus Standard Search", layout="wide", page_icon="🔬")

st.title("🔬 Scopus Search (Dokuz Eylül University-Faculty of Medicine)")
st.markdown("""
Search using the **Standard API View**.  
*Note: This view only retrieves 25 articles per search and consumes less quota but provides only author names (no IDs).*
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
    af_id = st.text_input("Affiliation ID (AF-ID)", value="60014930", help="e.g., 60014930 (Dokuz Eylül University)")
with col2:
    subj_area = st.text_input("Subject Area (SUBJ)", value="MEDI", help="e.g., MEDI (Medicine), ENGI (Engineering)")
with col3:
    date_range = st.text_input("Date Range", value="2025-2026", help="Format: YYYY or YYYY-YYYY")

# Pagination Controls with Explanations
col4, col5 = st.columns(2)
with col4:
    count = st.number_input(
        "Count (Results per page)", 
        min_value=1, 
        max_value=200, 
        value=25,
        help="How many articles to retrieve in one go. Max is high but we are limited 25 for free key."
    )
with col5:
    start_index = st.number_input(
        "Start Index (Offset)", 
        min_value=0, 
        value=0,
        help="Use this to skip results. E.g., if Count is 25, set Start Index to 25 to see the second page."
    )

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
            "view": "STANDARD"
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
                            authors = entry.get("dc:creator", "N/A")
                            if isinstance(authors, list):
                                authors = "; ".join(authors)

                            clean_data.append({
                                "Title": entry.get("dc:title", "N/A"),
                                "Journal": entry.get("prism:publicationName", "N/A"),
                                "Date": entry.get("prism:coverDate", "N/A"),
                                "Cited By": cited_by,
                                "DOI Link": doi_link,
                                "Authors": authors,
                                "Scopus ID": entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
                            })
                        
                        df = pd.DataFrame(clean_data)

                        # --- TABS ---
                        tab1, tab2 = st.tabs(["📄 Data View", "📊 Analytics"])

                        with tab1:
                            st.subheader(f"Found {total_results} documents (Showing {len(df)})")
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
                            st.subheader("🏆 Top Cited Articles")
                            top_cited = df.sort_values(by="Cited By", ascending=False).head(10)
                            
                            chart_cited = alt.Chart(top_cited).mark_bar().encode(
                                x=alt.X('Cited By', title='Citation Count'),
                                y=alt.Y('Title', sort='-x', axis=alt.Axis(labels=False), title="Articles (Hover for details)"),
                                tooltip=['Title', 'Cited By', 'Journal'],
                                color=alt.value('#3182bd')
                            ).properties(height=300)
                            st.altair_chart(chart_cited, use_container_width=True)

                            st.divider()

                            # 2. Trends (Months vs Count)
                            st.subheader("📈 Publications per Month")
                            
                            # Process Dates
                            df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                            time_df = df.dropna(subset=["Date"])
                            
                            if not time_df.empty:
                                # Group by Month
                                monthly = time_df.groupby(time_df["Date"].dt.to_period("M")).size().reset_index(name="Article Count")
                                monthly["Month"] = monthly["Date"].astype(str) # Convert to string for chart labeling
                                
                                chart_trend = alt.Chart(monthly).mark_line(point=True).encode(
                                    x=alt.X('Month', title='Month (Year-MM)'),
                                    y=alt.Y('Article Count', title='Number of Articles'),
                                    tooltip=['Month', 'Article Count'],
                                    color=alt.value('#e6550d')
                                ).properties(height=300)
                                
                                st.altair_chart(chart_trend, use_container_width=True)
                            else:
                                st.info("Not enough date data available for trend analysis.")

                    else:
                        st.warning("No documents found.")

                elif response.status_code == 401:
                    st.error("❌ **401 Unauthorized**")
                    st.markdown("""
                    **Troubleshooting:**
                    1. **Institutional Token:** You are likely off-campus. You *must* enter an Institutional Token in the sidebar.
                    2. **API Key:** Verify your API Key is correct.
                    """)
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

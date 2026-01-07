import streamlit as st
import requests
import pandas as pd
import altair as alt

# Page Config
st.set_page_config(page_title="Scopus Search & Analytics", layout="wide", page_icon="🔬")

st.title("🔬 Scopus Scientific Search API")
st.markdown("""
Search for documents, view **clickable DOIs**, and analyze **citation trends** visually.
""")

# Sidebar for Credentials
with st.sidebar:
    st.header("🔐 Credentials")
    api_key = st.text_input("Scopus API Key", type="password", help="Required. Get from dev.elsevier.com")
    inst_token = st.text_input("Institutional Token", type="password", help="Required for 'COMPLETE' view if off-campus.")
    st.divider()
    st.info("💡 **Tip:** 'COMPLETE' view requires a valid Institutional Token or on-campus IP.")

# Main Search Parameters
st.subheader("Search Configuration")

col1, col2, col3 = st.columns(3)
with col1:
    af_id = st.text_input("Affiliation ID (AF-ID)", value="60014930", help="e.g., 60014930 (Universiti Malaya)")
with col2:
    subj_area = st.text_input("Subject Area (SUBJ)", value="MEDI", help="e.g., MEDI, ENGI, COMP")
with col3:
    date_range = st.text_input("Date Range", value="2025-2026", help="Format: YYYY or YYYY-YYYY")

col4, col5 = st.columns(2)
with col4:
    count = st.number_input("Count (Results per page)", min_value=1, max_value=200, value=50) # Increased default for better charts
with col5:
    start_index = st.number_input("Start Index", min_value=0, value=0)

# Construct Query
query_string = f"AF-ID({af_id}) AND SUBJAREA({subj_area})"
st.code(f"Query: {query_string}", language="text")

# --- Helper Function to Parse Authors ---
def parse_authors(entry):
    authors_data = entry.get('author', [])
    if isinstance(authors_data, dict):
        authors_data = [authors_data]
    if not authors_data:
        return "N/A"

    parsed_list = []
    for auth in authors_data:
        name = auth.get('authname', 'Unknown')
        if name == 'Unknown':
            given = auth.get('given-name', '')
            surname = auth.get('surname', '')
            name = f"{surname}, {given}".strip()
        auth_id = auth.get('authid', 'No ID')
        parsed_list.append(f"{name} [{auth_id}]")
    return "; ".join(parsed_list)

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
        if inst_token:
            headers["X-ELS-Insttoken"] = inst_token
            
        params = {
            "query": query_string,
            "date": date_range,
            "count": count,
            "start": start_index,
            "view": "COMPLETE"
        }

        with st.spinner("Fetching data and generating analytics..."):
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
                            
                            # Handle Citations (ensure int)
                            try:
                                cited_by = int(entry.get("citedby-count", 0))
                            except ValueError:
                                cited_by = 0

                            clean_data.append({
                                "Title": entry.get("dc:title", "N/A"),
                                "Journal": entry.get("prism:publicationName", "N/A"),
                                "Date": entry.get("prism:coverDate", "N/A"),
                                "Cited By": cited_by,
                                "DOI Link": doi_link,
                                "Authors": parse_authors(entry),
                                "Scopus ID": entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
                            })
                        
                        df = pd.DataFrame(clean_data)

                        # --- TABS INTERFACE ---
                        tab1, tab2 = st.tabs(["📄 Data View", "📊 Analytics"])

                        # TAB 1: DATA TABLE
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
                            # Download
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "📥 Download CSV", csv, f"scopus_{af_id}.csv", "text/csv"
                            )

                        # TAB 2: VISUAL ANALYTICS
                        with tab2:
                            st.header("Visual Analysis")

                            # 1. Top Cited Articles Chart
                            st.subheader("🏆 Top Cited Articles")
                            
                            # Sort by citations and take top 10
                            top_cited = df.sort_values(by="Cited By", ascending=False).head(10)
                            
                            # Create Bar Chart
                            chart_cited = alt.Chart(top_cited).mark_bar().encode(
                                x=alt.X('Cited By', title='Citation Count'),
                                y=alt.Y('Title', sort='-x', title=None, axis=alt.Axis(labels=False)), # Hide long titles on axis
                                tooltip=['Title', 'Cited By', 'Journal', 'Date'],
                                color=alt.value('#3182bd')
                            ).properties(height=300)
                            
                            st.altair_chart(chart_cited, use_container_width=True)
                            st.caption("*Hover over bars to see full titles.*")

                            st.divider()

                            # 2. Publication Trends (Monthly)
                            st.subheader("📈 Publications per Month")

                            # Convert Date to Datetime
                            df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                            # Drop invalid dates
                            time_df = df.dropna(subset=["Date"])
                            
                            if not time_df.empty:
                                # Group by Month (Year-Month)
                                monthly_counts = time_df.groupby(
                                    time_df["Date"].dt.to_period("M")
                                ).size().reset_index(name="Count")
                                
                                # Convert Period back to String/Timestamp for Altair
                                monthly_counts["Date"] = monthly_counts["Date"].astype(str)

                                chart_trend = alt.Chart(monthly_counts).mark_line(point=True).encode(
                                    x=alt.X('Date', title='Month'),
                                    y=alt.Y('Count', title='Number of Articles'),
                                    tooltip=['Date', 'Count'],
                                    color=alt.value('#e6550d')
                                ).properties(height=300)

                                st.altair_chart(chart_trend, use_container_width=True)
                            else:
                                st.warning("Not enough date data to plot trends.")

                    else:
                        st.warning("No documents found.")

                elif response.status_code == 401:
                    st.error("❌ **401 Unauthorized**: Check API Key or Institutional Token.")
                elif response.status_code == 429:
                    st.error("❌ **429 Quota Exceeded**")
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

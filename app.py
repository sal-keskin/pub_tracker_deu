import streamlit as st
import pandas as pd
from scopus_service import ScopusService

# Page Config
st.set_page_config(page_title="Scopus Search", layout="wide")

# Title
st.title("🔎 Scopus Publications Search")

# Sidebar for API Key
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Scopus API Key", type="password", help="Leave empty to use Mock Mode.")
    st.markdown("---")
    st.info("If no API key is provided, the app will return mock data.")

# Main Interface
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Search Criteria")
    with st.form("search_form"):
        identifier = st.text_input("Author ID or ORCID", placeholder="e.g. 7004212771 or 0000-0000-0000-0000")

        with st.expander("Advanced Filters", expanded=True):
            af_id = st.text_input("Affiliation ID (AF-ID)", value="60014930")
            subj_area = st.text_input("Subject Area (SUBJAREA)", value="MEDI")

            c1, c2 = st.columns(2)
            with c1:
                start_year = st.number_input("Start Year", value=2022, step=1)
            with c2:
                end_year = st.number_input("End Year", value=2027, step=1)

            doctype = st.text_input("Document Type (DOCTYPE)", value="ar")

        submit_button = st.form_submit_button("Search Publications", type="primary")

# Logic
if submit_button:
    if not identifier:
        st.error("Please enter an Author ID or ORCID.")
    else:
        # Initialize Service
        service = ScopusService()

        # Prepare Filters
        filters = {
            "af_id": af_id,
            "subj_area": subj_area,
            "start_year": start_year,
            "end_year": end_year,
            "doctype": doctype
        }

        # Fetch Data
        with st.spinner("Fetching data..."):
            result = service.get_publications(identifier, api_key=api_key, filters=filters)

        # Display Results in col2
        with col2:
            st.subheader("Results")

            if "error" in result:
                st.error(f"Error: {result['error']}")
                if "query_used" in result:
                    st.code(result['query_used'], language="text")
            else:
                # Metadata
                st.info(f"Data Source: **{result.get('source', 'Unknown')}**")
                if "query_used" in result:
                    with st.expander("View Query Used"):
                        st.code(result['query_used'], language="text")

                # Publications Table
                pubs = result.get('publications', [])
                if pubs:
                    df = pd.DataFrame(pubs)
                    # Rename columns for display
                    df = df.rename(columns={
                        "title": "Title",
                        "journal": "Journal",
                        "year": "Year",
                        "times_cited": "Times Cited",
                        "doctype": "Type"
                    })
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No publications found matching these criteria.")

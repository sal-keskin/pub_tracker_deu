import streamlit as st
import pandas as pd
import os
import configparser
from pathlib import Path

# --- FIX: Create pybliometrics config file programmatically ---
def setup_scopus_config():
    # Define the directory and file path where pybliometrics looks for config
    config_dir = Path.home() / ".config" / "pybliometrics"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.ini"

    # Only create the file if it doesn't exist to avoid overwriting
    if not config_path.exists():
        # Get key from Streamlit secrets (safest) or environment variable
        try:
            api_key = st.secrets.get("SCOPUS_API_KEY")
        except FileNotFoundError:
            # Secrets file might not exist locally
            api_key = None

        if not api_key:
            api_key = os.environ.get("SCOPUS_API_KEY", "REPLACE_WITH_KEY_IF_TESTING_LOCALLY")

        # Create the configuration parser
        config = configparser.ConfigParser()
        config.optionxform = str  # Preserve case sensitivity

        config["Authentication"] = {"APIKey": api_key}

        # Write the file
        with open(config_path, "w") as f:
            config.write(f)

        print(f"✅ Scopus configuration created at: {config_path}")

# Run this setup immediately
setup_scopus_config()
# -----------------------------------------------------------

from scopus_service import ScopusService

# Page Config
st.set_page_config(page_title="Scopus Search", layout="wide")

# Title
st.title("🔎 Scopus Publications Search")

# Sidebar
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Scopus API Key", type="password", help="Leave empty to use Mock Mode.")

    st.markdown("---")
    st.caption("Credits")
    st.markdown("**Salih Keskin, 2026**")

# Main Interface
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Search Criteria")
    with st.form("search_form"):
        identifier = st.text_input("Author ID or ORCID", placeholder="Optional if AF-ID provided")

        with st.expander("Advanced Filters", expanded=True):
            af_id = st.text_input("Affiliation ID (AF-ID)", value="60014930", help="Required if no Author ID")
            subj_area = st.text_input("Subject Area (SUBJAREA)", value="MEDI")

            c1, c2 = st.columns(2)
            with c1:
                start_year = st.number_input("Start Year", value=2022, step=1)
            with c2:
                end_year = st.number_input("End Year", value=2027, step=1)

            doctype = st.text_input("Document Type (DOCTYPE)", value="ar")

            limit = st.select_slider("Max Results to Fetch", options=[25, 50, 100, 1000], value=25)

        submit_button = st.form_submit_button("Search Publications", type="primary")

# Logic
if submit_button:
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
    with st.spinner("Fetching data via Scopus API..."):
        result = service.get_publications(identifier, api_key=api_key, filters=filters, limit=limit)

    # Display Results in col2
    with col2:
        st.subheader("Results")

        if "error" in result:
            st.error(f"Error: {result['error']}")
            if "query_used" in result:
                st.code(result['query_used'], language="text")
        else:
            # Metadata & Stats
            total = result.get('total_results', 0)
            shown = result.get('shown_results', 0)
            source = result.get('source', 'Unknown')

            # Warning if truncated
            if total > shown:
                st.warning(f"⚠️ Showing **{shown}** of **{total}** total results. Increase the limit to see more.")
            else:
                st.success(f"Showing all **{shown}** results.")

            st.caption(f"Data Source: {source}")

            if "query_used" in result:
                with st.expander("View Query Used"):
                    st.code(result['query_used'], language="text")

            # Publications Table
            pubs = result.get('publications', [])
            if pubs:
                df = pd.DataFrame(pubs)

                # Reorder and Rename Columns
                # Desired: Title, Journal, Year, Type, Citations, DOI, Scopus ID, Authors
                cols_to_show = ["title", "journal", "year", "doctype", "times_cited", "doi", "scopus_id", "authors", "has_target_affil"]

                # Filter df to existing columns only (mock/live might differ slightly)
                cols = [c for c in cols_to_show if c in df.columns]
                df = df[cols]

                df = df.rename(columns={
                    "title": "Title",
                    "journal": "Journal",
                    "year": "Year",
                    "times_cited": "Cited",
                    "doctype": "Type",
                    "doi": "DOI",
                    "scopus_id": "Scopus ID",
                    "authors": "Authors",
                    "has_target_affil": "Affil. Match"
                })

                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("No publications found matching these criteria.")

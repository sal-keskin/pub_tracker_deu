import streamlit as st
import requests
import pandas as pd

# Page Config
st.set_page_config(page_title="Scopus Affiliation Search", layout="wide")

st.title("🔍 Scopus Affiliation Search")
st.markdown("A basic app to search for affiliations using the [Elsevier Scopus API](https://dev.elsevier.com/documentation/AFFILIATIONSearchAPI.wadl).")

# Sidebar for API Configuration
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter Scopus API Key", type="password", help="Get your key from https://dev.elsevier.com/")
    
    st.info("Note: You need an active Scopus API key to use this service.")

# Main Search Interface
query = st.text_input("Enter Affiliation Name (e.g., 'Oxford' or 'Harvard')", placeholder="Type affiliation name here...")

if st.button("Search"):
    if not api_key:
        st.error("❌ Please enter your API Key in the sidebar.")
    elif not query:
        st.warning("⚠️ Please enter a search term.")
    else:
        # API Endpoint and Headers
        url = "https://api.elsevier.com/content/search/affiliation"
        headers = {
            "X-ELS-APIKey": api_key,
            "Accept": "application/json"
        }
        
        # Construct the query parameter
        # AFFIL() is the standard field for affiliation name searches
        params = {
            "query": f"AFFIL({query})",
            "count": 25  # Number of results to return
        }

        with st.spinner("Searching Scopus..."):
            try:
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse Results
                    search_results = data.get("search-results", {})
                    entries = search_results.get("entry", [])
                    total_results = search_results.get("opensearch:totalResults", 0)

                    st.success(f"Found {total_results} results.")

                    if entries:
                        # Process data into a clean list for DataFrame
                        clean_data = []
                        for entry in entries:
                            # Handle different response structures gracefully
                            affil_name = entry.get("affiliation-name", "N/A")
                            city = entry.get("city", "N/A")
                            country = entry.get("country", "N/A")
                            eid = entry.get("eid", "N/A")
                            parent = entry.get("parent-affiliation-name", "N/A")
                            
                            clean_data.append({
                                "Affiliation Name": affil_name,
                                "City": city,
                                "Country": country,
                                "Parent Institution": parent,
                                "Scopus EID": eid
                            })

                        df = pd.DataFrame(clean_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Download Button
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download Results as CSV",
                            csv,
                            "scopus_affiliations.csv",
                            "text/csv",
                            key='download-csv'
                        )
                    else:
                        st.write("No entries found for this query.")
                
                elif response.status_code == 401:
                    st.error("❌ Unauthorized. Please check your API Key.")
                elif response.status_code == 429:
                    st.error("❌ Quota exceeded. You have made too many requests.")
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

import os
import requests
import re
import streamlit as st

# Flag to force mock mode
MOCK_MODE_ENV = os.environ.get("MOCK_MODE", "False").lower() == "true"

class ScopusService:
    def __init__(self):
        self.base_url = "https://api.elsevier.com/content/search/scopus"

    def build_query(self, identifier, filters=None):
        if not filters:
            filters = {}

        query_parts = []

        # Identifier (AU-ID or ORCID) is optional if AF-ID is present, but we need at least one criteria.
        if identifier:
            if re.match(r"^\d{4}-\d{4}-\d{4}-", identifier):
                query_parts.append(f"ORCID({identifier})")
            else:
                query_parts.append(f"AU-ID({identifier})")

        if filters.get("af_id"):
            query_parts.append(f"AF-ID({filters['af_id']})")

        if filters.get("subj_area"):
            query_parts.append(f"SUBJAREA({filters['subj_area']})")

        if filters.get("start_year"):
             query_parts.append(f"PUBYEAR > {filters['start_year']}")
        if filters.get("end_year"):
             query_parts.append(f"PUBYEAR < {filters['end_year']}")

        if filters.get("doctype"):
            query_parts.append(f"DOCTYPE({filters['doctype']})")

        return " AND ".join(query_parts)

    def get_publications(self, identifier, api_key=None, filters=None, limit=25):
        if not filters:
            filters = {}

        # Validate: Need at least Identifier OR Affiliation
        if not identifier and not filters.get("af_id"):
             return {"error": "Please provide at least an Author ID/ORCID OR an Affiliation ID."}

        # Resolve API Key: Argument > Secrets > Env
        if not api_key:
            try:
                api_key = st.secrets.get("SCOPUS_API_KEY")
            except:
                pass
        if not api_key:
            api_key = os.environ.get("SCOPUS_API_KEY")

        use_mock = MOCK_MODE_ENV or not api_key
        full_query = self.build_query(identifier, filters)

        if use_mock:
            return self._get_mock_data(full_query, limit, filters)

        return self._fetch_from_api(full_query, api_key, limit, filters.get("af_id"))

    def _fetch_from_api(self, query, api_key, limit, target_af_id):
        headers = {
            "X-ELS-APIKey": api_key,
            "Accept": "application/json"
        }

        params = {
            "query": query,
            "count": limit,
            "view": "STANDARD", # STANDARD gives us most fields we need
            "sort": "-coverDate"
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return self._format_response(data, query, target_af_id)
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            try:
                # Try to parse Scopus XML/JSON error
                if response is not None:
                    error_json = response.json()
                    if 'service-error' in error_json:
                         error_msg = f"{error_json['service-error'].get('statusText', 'Error')}: {error_json['service-error'].get('statusMsg', '')}"
            except:
                pass
            return {"error": error_msg, "query_used": query}

    def _format_response(self, data, query, target_af_id):
        pubs = []
        search_results = data.get("search-results", {})
        total_results = int(search_results.get("opensearch:totalResults", 0))
        entries = search_results.get("entry", [])

        if not isinstance(entries, list):
             entries = [entries]

        for entry in entries:
            # Extract fields
            title = entry.get("dc:title", "N/A")
            journal = entry.get("prism:publicationName", "N/A")
            date_str = entry.get("prism:coverDate", "N/A")
            year = date_str[:4] if date_str and len(date_str) >= 4 else "N/A"
            cited = entry.get("citedby-count", "0")
            doi = entry.get("prism:doi", "N/A")
            scopus_id = entry.get("dc:identifier", "N/A").replace("SCOPUS_ID:", "")
            doctype = entry.get("subtypeDescription", entry.get("subtype", "N/A"))

            # Authors
            # In STANDARD view, authors might not be fully listed or just 'dc:creator' (first author)
            # Scopus Search API 'STANDARD' view usually has 'author' array? No, often just 'dc:creator'.
            # 'COMPLETE' view has 'author'. But let's check what we get.
            # If 'author' key exists (list of dicts), we use it.
            authors_list = []
            author_names_str = "N/A"
            if 'author' in entry:
                # Iterate authors
                for auth in entry['author']:
                    name = auth.get('authname', 'Unknown')
                    authors_list.append(name)
                author_names_str = "; ".join(authors_list)
            elif 'dc:creator' in entry:
                 author_names_str = entry['dc:creator']

            # Affiliation Match
            # Check 'affiliation' array in entry
            has_target_affil = False
            if target_af_id and 'affiliation' in entry:
                affils = entry['affiliation']
                if not isinstance(affils, list):
                    affils = [affils]

                for aff in affils:
                    # check 'afid'
                    if str(aff.get('afid')) == str(target_af_id):
                        has_target_affil = True
                        break

            pubs.append({
                "title": title,
                "journal": journal,
                "year": year,
                "times_cited": cited,
                "doctype": doctype,
                "doi": doi,
                "scopus_id": scopus_id,
                "authors": author_names_str,
                "has_target_affil": has_target_affil
            })

        return {
            "publications": pubs,
            "total_results": total_results,
            "shown_results": len(pubs),
            "source": "Scopus API (Requests)",
            "query_used": query
        }

    def _get_mock_data(self, query, limit, filters):
        # Generate enough mock items to test pagination logic
        total_mock = 120
        count = min(limit, total_mock)

        mock_pubs = []
        for i in range(count):
            mock_pubs.append({
                "title": f"Mock Paper {i+1}: Analysis of Something",
                "journal": "Mock Journal",
                "year": "2024",
                "times_cited": 10 + i,
                "doctype": "ar",
                "doi": f"10.1016/mock.{i}",
                "scopus_id": f"85000{i}",
                "authors": "Keskin S.; Doe J.",
                "has_target_affil": True # Simulate match
            })

        return {
            "publications": mock_pubs,
            "total_results": total_mock,
            "shown_results": count,
            "source": "Mock Data (Requests)",
            "query_used": query
        }

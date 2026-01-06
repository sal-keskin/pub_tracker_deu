import os
import requests
import re

# Flag to force mock mode if set in env, otherwise depends on API Key presence
MOCK_MODE_ENV = os.environ.get("MOCK_MODE", "False").lower() == "true"

class ScopusService:
    def __init__(self):
        self.base_url = "https://api.elsevier.com/content/search/scopus"

    def build_query(self, identifier, filters=None):
        """
        Constructs the Scopus search query string.
        """
        if not filters:
            filters = {}

        # Detect if identifier is ORCID (0000-...) or AU-ID (digits)
        if re.match(r"^\d{4}-\d{4}-\d{4}-", identifier):
            main_query = f"ORCID({identifier})"
        else:
            main_query = f"AU-ID({identifier})"

        query_parts = [main_query]

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

    def get_publications(self, identifier, api_key=None, filters=None):
        """
        Fetches publications from Scopus.
        """
        if not filters:
            filters = {}

        use_mock = MOCK_MODE_ENV or not api_key
        full_query = self.build_query(identifier, filters)

        if use_mock:
            return self._get_mock_data(identifier, filters, full_query)

        return self._fetch_from_api(full_query, api_key)

    def _fetch_from_api(self, query, api_key):
        headers = {
            "X-ELS-APIKey": api_key,
            "Accept": "application/json"
        }

        params = {
            "query": query,
            "count": 25,
            "view": "STANDARD"
        }

        response = None
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            formatted = self._format_response(data)
            formatted["query_used"] = query
            return formatted
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if response is not None:
                try:
                    error_json = response.json()
                    if 'service-error' in error_json:
                         error_msg = f"{error_json['service-error'].get('statusText', 'Error')}: {error_json['service-error'].get('statusMsg', '')}"
                except:
                    pass
            return {"error": error_msg, "query_used": query}

    def _get_mock_data(self, identifier, filters, query):
        """
        Returns mock Scopus data.
        """
        mock_pubs = [
            {
                "title": "Mock Scopus Article 1: Advanced Research",
                "journal": "Journal of Mock Science",
                "year": "2023",
                "times_cited": 12,
                "doctype": filters.get("doctype", "ar")
            },
            {
                "title": f"Mock Study by {identifier}",
                "journal": "International Mock Journal",
                "year": "2024",
                "times_cited": 5,
                "doctype": "re"
            },
            {
                "title": "Mock Medical Analysis",
                "journal": "Mock Medicine",
                "year": "2023",
                "times_cited": 88,
                "doctype": "ar"
            }
        ]
        return {
            "publications": mock_pubs,
            "source": "Mock Data (Scopus)",
            "query_used": query
        }

    def _format_response(self, data):
        """
        Formats Scopus JSON response.
        """
        pubs = []
        search_results = data.get("search-results", {})
        entries = search_results.get("entry", [])

        if not isinstance(entries, list):
             entries = [entries]

        for entry in entries:
            title = entry.get("dc:title", "N/A")
            journal = entry.get("prism:publicationName", "N/A")
            date_str = entry.get("prism:coverDate", "N/A")
            year = date_str[:4] if date_str and len(date_str) >= 4 else "N/A"
            times_cited = entry.get("citedby-count", "0")
            doctype = entry.get("subtypeDescription", entry.get("subtype", "N/A"))

            pubs.append({
                "title": title,
                "journal": journal,
                "year": year,
                "times_cited": times_cited,
                "doctype": doctype
            })

        return {"publications": pubs, "source": "Scopus API"}

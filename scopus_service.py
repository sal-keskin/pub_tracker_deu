import os
import requests
import re
from pybliometrics.scopus import ScopusSearch, CONFIG
import pandas as pd

# Flag to force mock mode
MOCK_MODE_ENV = os.environ.get("MOCK_MODE", "False").lower() == "true"

class ScopusService:
    def __init__(self):
        pass

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

        use_mock = MOCK_MODE_ENV or not api_key
        full_query = self.build_query(identifier, filters)

        if use_mock:
            return self._get_mock_data(full_query, limit, filters)

        return self._fetch_with_pybliometrics(full_query, api_key, limit, filters.get("af_id"))

    def _fetch_with_pybliometrics(self, query, api_key, limit, target_af_id):
        # Configure API Key temporarily
        try:
            # Check if keys are set, if not set them.
            if api_key:
                # Ensure Authentication section exists
                if not CONFIG.has_section('Authentication'):
                    CONFIG.add_section('Authentication')
                CONFIG.set('Authentication', 'APIKey', api_key)

            # ScopusSearch
            # 'download' param is not valid for ScopusSearch in newer versions, removing it.
            # We force subscriber=False to be safe if no key, but key is provided here.
            s = ScopusSearch(query, count=limit, view="STANDARD", refresh=True)

            total_results = s.get_results_size()
            results = s.results if s.results else []

            # Parse results
            pubs = []
            for res in results:
                # Safely get attributes
                title = getattr(res, 'title', 'N/A')
                journal = getattr(res, 'publicationName', 'N/A')
                date = getattr(res, 'coverDate', 'N/A')
                year = date[:4] if date else 'N/A'
                cited = getattr(res, 'citedby_count', 0)
                doi = getattr(res, 'doi', 'N/A')
                scopus_id = getattr(res, 'eid', 'N/A')
                doctype = getattr(res, 'subtypeDescription', 'N/A')

                # Authors and Affiliation check
                # 'afids' is usually a semi-colon separated string of Affiliation IDs
                paper_afids = getattr(res, 'afids', '') or ''
                has_target_affil = False
                if target_af_id and paper_afids:
                    if target_af_id in paper_afids.split(';'):
                        has_target_affil = True

                # Authors
                # 'author_names' is usually "Name1; Name2"
                author_names = getattr(res, 'author_names', '') or ''

                pubs.append({
                    "title": title,
                    "journal": journal,
                    "year": year,
                    "times_cited": cited,
                    "doctype": doctype,
                    "doi": doi,
                    "scopus_id": scopus_id,
                    "authors": author_names,
                    "has_target_affil": has_target_affil
                })

            return {
                "publications": pubs,
                "total_results": total_results,
                "shown_results": len(pubs),
                "source": "Scopus API (pybliometrics)",
                "query_used": query
            }

        except Exception as e:
            return {"error": str(e), "query_used": query}
        finally:
            # Security: Clear the API Key from memory after request
            if CONFIG.has_option('Authentication', 'APIKey'):
                CONFIG.remove_option('Authentication', 'APIKey')

    def _get_mock_data(self, query, limit, filters):
        target_af = filters.get("af_id")

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
                "scopus_id": f"2-s2.0-{85000+i}",
                "authors": "Keskin S.; Doe J.",
                "has_target_affil": True # Simulate match
            })

        return {
            "publications": mock_pubs,
            "total_results": total_mock,
            "shown_results": count,
            "source": "Mock Data (pybliometrics)",
            "query_used": query
        }

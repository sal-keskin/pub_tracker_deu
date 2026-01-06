import os
import clarivate.wos_starter.client
from clarivate.wos_starter.client.rest import ApiException

# Flag to force mock mode
MOCK_MODE = os.environ.get("MOCK_MODE", "True").lower() == "true"
API_KEY = os.environ.get("WOS_API_KEY")

class WosService:
    def __init__(self):
        self.mock_mode = MOCK_MODE or not API_KEY
        if not self.mock_mode:
            configuration = clarivate.wos_starter.client.Configuration(
                host="https://api.clarivate.com/apis/wos-starter/v1"
            )
            configuration.api_key['ClarivateApiKeyAuth'] = API_KEY
            self.api_client = clarivate.wos_starter.client.ApiClient(configuration)
            self.documents_api = clarivate.wos_starter.client.DocumentsApi(self.api_client)

    def get_publications(self, identifier):
        """
        Fetches publications based on the identifier (ResearcherID or ORCID).
        Uses 'AI' (Author Identifier) field tag.
        """
        if self.mock_mode:
            return self._get_mock_data(identifier)

        query = f"AI={identifier}"
        try:
            # db='WOS' is default, limit=10 default.
            # We fetch more fields if possible or just standard list.
            # API docs say: detail=short (limited) or None (full).
            api_response = self.documents_api.documents_get(q=query, limit=50)
            return self._format_response(api_response)
        except ApiException as e:
            print(f"Exception when calling DocumentsApi->documents_get: {e}")
            return {"error": str(e)}

    def _get_mock_data(self, identifier):
        """
        Returns hardcoded sample data simulating the API response structure.
        We return a simplified dictionary list for the app to consume.
        """
        # Simulating a list of publications
        # Output requirements: Title, Journal, Year, Times Cited
        mock_pubs = [
            {
                "title": "Mock Publication 1: The basics of Quantum Mechanics",
                "journal": "Journal of Mock Physics",
                "year": "2023",
                "times_cited": 42
            },
            {
                "title": "Mock Publication 2: Advanced AI techniques",
                "journal": "International Mock Journal of CS",
                "year": "2022",
                "times_cited": 10
            },
            {
                "title": f"Mock Publication 3: Specific study for {identifier}",
                "journal": "Nature of Mockery",
                "year": "2021",
                "times_cited": 150
            }
        ]
        return {"publications": mock_pubs, "source": "Mock Data"}

    def _format_response(self, api_response):
        """
        Formats the real API response into the same structure as mock data.
        api_response is of type DocumentsList.
        """
        pubs = []
        if api_response.hits:
            for doc in api_response.hits:
                # Extract fields. The model object attributes might need check.
                # Based on doc inspection or standard assumptions:
                # doc.title, doc.source.source_title, doc.source.publish_year, doc.times_cited

                # Handling potential missing fields safely
                title = doc.title if hasattr(doc, 'title') else "N/A"

                journal = "N/A"
                if hasattr(doc, 'source') and doc.source and hasattr(doc.source, 'source_title'):
                     journal = doc.source.source_title

                year = "N/A"
                if hasattr(doc, 'source') and doc.source and hasattr(doc.source, 'publish_year'):
                     year = doc.source.publish_year

                times_cited = doc.citations.times_cited if (hasattr(doc, 'citations') and doc.citations and hasattr(doc.citations, 'times_cited')) else 0

                pubs.append({
                    "title": title,
                    "journal": journal,
                    "year": year,
                    "times_cited": times_cited
                })

        return {"publications": pubs, "source": "Live API"}

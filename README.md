# Scopus Publications Search (Streamlit)

A simple **Streamlit** application to search for Scopus publications by Author ID or ORCID using `pybliometrics`.

## Features
- **Search**: Enter Author ID or ORCID.
- **Filters**: Predefined but editable filters for Affiliation, Subject Area, Year, and Document Type.
- **API Key**: Securely enter your Scopus API Key in the sidebar (per session).
- **Advanced Logic**:
  - Validates if the retrieved paper actually involves your target affiliation.
  - Limits results to 25/50/100/1000 items to prevent API overuse.
- **Modes**:
  - **Live Mode**: Fetches real data using `pybliometrics` wrapper.
  - **Mock Mode**: Returns sample data if no API key is provided.

## Local Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```
   The app will open in your browser at `http://localhost:8501`.

## Deployment to Streamlit Cloud

1. Push this code to a GitHub repository.
2. Log in to [Streamlit Cloud](https://streamlit.io/cloud).
3. Click **"New app"**.
4. Select your repository, branch, and set the main file path to `app.py`.
5. Click **"Deploy"**.

### Notes on Pybliometrics Config
This app dynamically injects your provided API key into the `pybliometrics` configuration for the session. It does not require a permanent `config.ini` file on the server.

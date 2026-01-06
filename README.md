# Scopus Publications Search App

A simple Flask application to search for Scopus publications by Author ID or ORCID.

## Features
- Search by **Scopus Author ID** or **ORCID**.
- Enter **API Key** securely per session (not stored on server).
- Customizable filters:
  - Affiliation ID (AF-ID)
  - Subject Area (SUBJAREA)
  - Start/End Year
  - Document Type (DOCTYPE)
- **Mock Mode**: Works without an API key (returns sample data).
- **Live Mode**: Connects to Elsevier Scopus Search API.

## Local Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```
   Access at `http://127.0.0.1:5000`.

## Deployment to Private Server (Simple)

The simplest way to deploy this on a Linux server (e.g., Ubuntu/Debian) is using **Gunicorn** (a production WSGI server) and **Systemd** (to keep it running).

### 1. Prepare the Server
Copy your files to the server (e.g., `/var/www/scopusapp` or `~/scopusapp`).

```bash
# On the server
sudo apt update
sudo apt install python3-venv
```

### 2. Install App
```bash
cd ~/scopusapp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run with Gunicorn (Test)
```bash
# This runs the server on port 8000
./venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
Access `http://<your-server-ip>:8000`. If it works, press `Ctrl+C` to stop.

### 4. Keep it Running (Systemd)
Create a service file to ensure the app runs in the background and restarts on reboot.

1. Create the file:
   ```bash
   sudo nano /etc/systemd/system/scopusapp.service
   ```

2. Paste the following (adjust paths/user):
   ```ini
   [Unit]
   Description=Gunicorn instance to serve Scopus App
   After=network.target

   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/scopusapp
   Environment="PATH=/home/ubuntu/scopusapp/venv/bin"
   # Environment="MOCK_MODE=False"
   ExecStart=/home/ubuntu/scopusapp/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

3. Start and enable the service:
   ```bash
   sudo systemctl start scopusapp
   sudo systemctl enable scopusapp
   ```

### Configuration
- **API Key**: Users enter their Elsevier Scopus API Key in the web interface.
- **Mock Mode**: If no key is entered, the app defaults to Mock Mode. To force Mock Mode even with keys, set `MOCK_MODE=True` in the environment.

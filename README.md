# WoS Publications Search App

A simple Flask application to search for Web of Science publications by ResearcherID or ORCID.

## Features
- Search by ResearcherID or ORCID.
- Lists Title, Journal, Year, and Times Cited.
- **Mock Mode**: Works without an API key (returns sample data).
- **Live Mode**: Connects to Clarivate Web of Science Starter API.

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
Copy your files to the server (e.g., `/var/www/wosapp` or `~/wosapp`).

```bash
# On the server
sudo apt update
sudo apt install python3-venv
```

### 2. Install App
```bash
cd ~/wosapp
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
   sudo nano /etc/systemd/system/wosapp.service
   ```

2. Paste the following (adjust paths/user):
   ```ini
   [Unit]
   Description=Gunicorn instance to serve WoS App
   After=network.target

   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/wosapp
   Environment="PATH=/home/ubuntu/wosapp/venv/bin"
   # Uncomment and set your API key for live data
   # Environment="WOS_API_KEY=your_api_key_here"
   # Environment="MOCK_MODE=False"
   ExecStart=/home/ubuntu/wosapp/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

3. Start and enable the service:
   ```bash
   sudo systemctl start wosapp
   sudo systemctl enable wosapp
   ```

### Configuration
- **Mock Mode**: By default, the app runs in Mock Mode.
- **Live API**: To use real data, set the environment variable `WOS_API_KEY` and `MOCK_MODE=False`.

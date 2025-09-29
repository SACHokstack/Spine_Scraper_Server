# Spine Industry Scraper Server

## Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
# Navigate to server directory
cd spine_scraper_server

# Run startup script (handles everything)
python run_server.py
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

## Web Interface

Once running, access the web interface at:
```
http://localhost:5000
```

### Web Interface Features:
- **Real-time Status Dashboard** - Live progress tracking with visual indicators
- **Interactive Controls** - Start/stop scraping with one click
- **Live Activity Log** - Watch scraping progress in real-time
- **Results Viewer** - View latest scraping results and data samples
- **Professional UI** - Clean, modern interface with real-time updates

## API Endpoints

### Start Scraping
```bash
POST /api/scrape
```
Starts the scraping process in the background.

**Response:**
```json
{
  "message": "Scraping started",
  "status": "started"
}
```

### Get Real-time Status
```bash
GET /api/status
```
Returns current scraper status with recent logs.

**Response:**
```json
{
  "status": {
    "is_running": true,
    "progress": 45,
    "current_website": "Spine Market Group",
    "articles_scraped": 12,
    "start_time": "2025-09-29T12:05:11",
    "error": null
  },
  "logs": [
    "[12:05:11] Starting spine industry scraper...",
    "[12:05:11] Initializing headless browser...",
    "[12:05:11] Browser initialized successfully"
  ]
}
```

### Get Activity Logs
```bash
GET /api/logs
```
Returns recent activity logs.

**Response:**
```json
{
  "logs": [
    "[12:05:11] Starting spine industry scraper...",
    "[12:05:11] Initializing headless browser...",
    "[12:05:11] Browser initialized successfully"
  ]
}
```

### Get Scraping Results
```bash
GET /api/results
```
Returns the latest scraping results with sample data.

**Response:**
```json
{
  "file": "spine_headless_scraper_20250929_120511.csv",
  "header": "title,url,website_name,category,content_length,spine_procedures,financial_mentions,scraped_at",
  "sample_data": [
    "Spine Market Group News,https://thespinemarketgroup.com/,Spine Market Group,industry_news,481,,2025-09-29T11:46:19"
  ],
  "total_lines": 71
}
```

### Stop Scraping
```bash
POST /api/stop
```
Stops the current scraping process.

**Response:**
```json
{
  "message": "Scraping stopped"
}
```

## Project Structure

```
spine_scraper_server/
├── app.py                    # Main Flask application with API
├── headless_spine_scraper.py # Core scraping engine
├── run_server.py            # Startup script with auto-setup
├── requirements.txt         # Python dependencies
├── README.md               # This documentation
└── templates/
    └── index.html          # Web interface template
```
## Features

- **Real-time Web Interface** - Monitor scraping progress live
- **RESTful API** - Complete programmatic access
- **Background Processing** - Non-blocking scraping operations
- **Professional Logging** - Detailed activity tracking
- **Production Ready** - Robust error handling and status monitoring
- **Modern UI** - Clean, responsive web interface

## Configuration

Default server settings:
- **Port**: 5000
- **Host**: 0.0.0.0 (accessible from all network interfaces)
- **Debug Mode**: Enabled for development
- **Auto-reload**: Enabled for development
- **Output Directory**: `../spine_industry_data/`

## Scraping Capabilities

### Target Websites:
1. **Spine Market Group** - Industry news and analysis
2. **Spine Market** - Market research and data
3. **Ortho Spine News** - Research reports and updates
4. **Becker's Spine Review** - Healthcare insights and analysis

### Data Extraction:
- **Complete Article Content** - Full text extraction
- **Spine Procedures** - Detection of surgical procedures
- **Financial Data** - Market values, growth metrics
- **Company Information** - Industry player mentions
- **Regulatory Updates** - FDA and compliance information

### Output Formats:
- **CSV Files** - Structured data for analysis
- **JSON Files** - API-ready data format
- **Summary Reports** - Executive summaries with insights

## Expected Performance

- **Runtime**: 10-20 minutes per complete scraping session
- **Article Volume**: 20-100 articles with full content
- **Success Rate**: High success rate with retry logic
- **Data Quality**: Clean, structured data ready for analysis

## Usage Examples

### Web Interface Usage:
1. Open `http://localhost:5000` in your browser
2. Click "Start Scraping" to begin the process
3. Monitor real-time progress in the activity log
4. View results when scraping completes
5. Download or analyze the exported data files

### API Integration Example:
```python
import requests

# Start scraping
response = requests.post('http://localhost:5000/api/scrape')
print("Started:", response.json())

# Monitor progress
while True:
    status = requests.get('http://localhost:5000/api/status').json()
    if not status['status']['is_running']:
        break
    print(f"Progress: {status['status']['progress']}%")
    time.sleep(5)

# Get results
results = requests.get('http://localhost:5000/api/results').json()
print(f"Scraped {results['total_lines']} lines of data")
```

### Command Line Usage:
```bash
# Start server
python run_server.py

# In another terminal, start scraping
curl -X POST http://localhost:5000/api/scrape

# Monitor status
curl http://localhost:5000/api/status

# Get results
curl http://localhost:5000/api/results
```

## Troubleshooting

### Common Issues:

**1. Chrome Browser Not Found**
- Ensure Google Chrome is installed on the system
- Check that Chrome is in the system PATH
- Verify Chrome installation location

**2. Port Already in Use**
- Change the port in app.py: `app.run(port=5001)`
- Or kill the process using port 5000

**3. Dependencies Not Installed**
- Run: `pip install -r requirements.txt`
- Or use the startup script: `python run_server.py`

**4. Virtual Environment Issues**
- Delete the `venv/` folder and recreate it
- Run: `python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt`

**5. No Scraping Results**
- Check the activity logs in the web interface
- Verify target websites are accessible
- Check network connectivity

## Advanced Configuration

### Changing Default Settings:
Edit `app.py` to modify:
```python
app.run(
    debug=True,          # Set to False for production
    host='0.0.0.0',      # Change to '127.0.0.1' for local only
    port=5000,          # Change port if needed
    threaded=True       # Enable for multiple concurrent requests
)
```

### Custom Scraping Parameters:
Modify `headless_spine_scraper.py` to adjust:
- Target websites list
- Scraping delays and timeouts
- Content extraction rules
- Output data structure

## Production Deployment

### For Production Use:
1. Set `debug=False` in app.py
2. Use a production WSGI server like Gunicorn
3. Set up proper logging configuration
4. Configure firewall and security settings
5. Set up process monitoring

### Example Production Setup:
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or use the startup script
python run_server.py
```

## System Requirements

- **Python**: 3.8 or higher
- **Google Chrome**: Latest stable version
- **Memory**: 2GB+ RAM recommended
- **Storage**: 1GB+ free space for data storage
- **Network**: Stable internet connection

## API Rate Limits

- **Scraping Operations**: One at a time (prevents conflicts)
- **Status Checks**: Unlimited (real-time updates)
- **Log Retrieval**: Unlimited (live monitoring)
- **Results Access**: Unlimited (data access)

## Data Privacy

- All scraping respects robots.txt files
- Implements reasonable delays between requests
- Only accesses publicly available web content
- No personal data collection or storage

## Support

This server is part of the Spine Industry Data Collection System. For issues or questions:
1. Check the activity logs in the web interface
2. Review the troubleshooting section
3. Check the Flask server console output
4. Verify all dependencies are installed correctly

## License

This project is designed for legitimate business intelligence and market research purposes only. Users are responsible for complying with website terms of service and applicable laws.
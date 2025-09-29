#!/usr/bin/env python3
"""
Spine Industry Scraper Flask Server
Provides web interface and API endpoints for the headless browser scraper
"""

from flask import Flask, render_template, request, jsonify
import os
import json
import threading
import time
from datetime import datetime
from headless_spine_scraper import HeadlessSpineScraper

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'spine-scraper-secret-key'

# Global variables for scraper status
scraper_instance = None
scraper_thread = None
scraper_logs = []
scraper_status = {
    'is_running': False,
    'progress': 0,
    'current_website': '',
    'articles_scraped': 0,
    'start_time': None,
    'end_time': None,
    'error': None,
    'status': 'ready'
}

def run_scraper():
    """Run the scraper in a background thread"""
    global scraper_status, scraper_instance, scraper_logs

    try:
        # Clear previous logs
        scraper_logs.clear()

        scraper_status['is_running'] = True
        scraper_status['start_time'] = datetime.now().isoformat()
        scraper_status['error'] = None
        scraper_status['status'] = 'running'

        # Create a global logging function for the thread
        def thread_add_log(message):
            """Add a log entry with timestamp (for thread use)"""
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f'[{timestamp}] {message}'
            scraper_logs.append(log_entry)
            # Keep only last 100 logs
            if len(scraper_logs) > 100:
                scraper_logs.pop(0)
            print(log_entry)  # Also print to console

        thread_add_log('🚀 Starting spine industry scraper...')
        thread_add_log('🔧 Initializing headless browser...')

        # Create scraper instance
        scraper_instance = HeadlessSpineScraper()

        thread_add_log('✅ Browser initialized successfully')
        scraper_status['progress'] = 10

        # Run the scraper
        thread_add_log('🌐 Starting website scraping...')
        articles = scraper_instance.scrape_all_websites()

        # Update final status
        scraper_status['is_running'] = False
        scraper_status['progress'] = 100
        scraper_status['articles_scraped'] = len(articles)
        scraper_status['end_time'] = datetime.now().isoformat()

        if articles:
            # Export data
            thread_add_log(f'💾 Exporting {len(articles)} articles to files...')
            scraper_instance.export_data(articles)
            scraper_status['status'] = 'completed'
            thread_add_log(f'✅ Scraping completed! {len(articles)} articles processed')
        else:
            scraper_status['status'] = 'no_articles'
            scraper_status['error'] = 'No articles were scraped'
            thread_add_log('⚠️ No articles were found')

    except Exception as e:
        error_msg = str(e)
        scraper_status['is_running'] = False
        scraper_status['error'] = error_msg
        scraper_status['end_time'] = datetime.now().isoformat()
        scraper_status['status'] = 'error'

        # Create a fallback logging function for error reporting
        def fallback_add_log(message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f'[{timestamp}] {message}'
            scraper_logs.append(log_entry)
            if len(scraper_logs) > 100:
                scraper_logs.pop(0)
            print(log_entry)

        fallback_add_log(f'❌ Error: {error_msg}')

@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html', status=scraper_status)

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API endpoint to start scraping"""
    global scraper_thread, scraper_status

    if scraper_status['is_running']:
        return jsonify({'error': 'Scraping already in progress'}), 400

    # Reset status
    scraper_status = {
        'is_running': False,
        'progress': 0,
        'current_website': '',
        'articles_scraped': 0,
        'start_time': None,
        'end_time': None,
        'error': None,
        'status': 'ready'
    }

    # Clear logs for new run
    scraper_logs.clear()

    # Create a logging function for this request
    def request_add_log(message):
        """Add a log entry with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f'[{timestamp}] {message}'
        scraper_logs.append(log_entry)
        # Keep only last 100 logs
        if len(scraper_logs) > 100:
            scraper_logs.pop(0)
        print(log_entry)  # Also print to console

    # Make logging available to the scraper module
    import headless_spine_scraper
    headless_spine_scraper.add_log = request_add_log

    # Start scraping in background thread
    scraper_thread = threading.Thread(target=run_scraper)
    scraper_thread.daemon = True
    scraper_thread.start()

    return jsonify({'message': 'Scraping started', 'status': 'started'})

@app.route('/api/status')
def api_status():
    """API endpoint to get current scraper status"""
    return jsonify({
        'status': scraper_status,
        'logs': scraper_logs[-20:]  # Return last 20 log entries
    })

@app.route('/api/logs')
def api_logs():
    """API endpoint to get recent logs"""
    return jsonify({
        'logs': scraper_logs[-50:]  # Return last 50 log entries
    })

@app.route('/api/results')
def api_results():
    """API endpoint to get scraping results"""
    try:
        # Look for the most recent results
        results_dir = "spine_industry_data"
        if os.path.exists(results_dir):
            # Find the most recent CSV file
            files = [f for f in os.listdir(results_dir) if f.startswith('spine_headless_scraper_') and f.endswith('.csv')]
            if files:
                latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(results_dir, f)))
                file_path = os.path.join(results_dir, latest_file)

                # Read first few lines of CSV
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 0:
                        header = lines[0].strip()
                        sample_data = lines[1:6] if len(lines) > 5 else lines[1:]

                        return jsonify({
                            'file': latest_file,
                            'header': header,
                            'sample_data': [line.strip() for line in sample_data],
                            'total_lines': len(lines)
                        })

        return jsonify({'error': 'No results found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """API endpoint to stop scraping"""
    global scraper_status

    if scraper_status['is_running'] and scraper_instance:
        try:
            scraper_instance.driver.quit()
            scraper_status['is_running'] = False
            scraper_status['status'] = 'stopped'
            return jsonify({'message': 'Scraping stopped'})
        except:
            pass

    return jsonify({'message': 'No active scraping to stop'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
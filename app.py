import os
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

FEED_URL = "https://docs.cloud.google.com/feeds/bigquery-release-notes.xml"
CACHE_FILE = "feed_cache.xml"

def fetch_feed_xml(force_refresh=False):
    """Fetches the XML from Google Cloud Docs or reads from local cache if it exists."""
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return f.read(), True
        except Exception:
            pass # Fallback to fetching

    try:
        response = requests.get(FEED_URL, timeout=10)
        response.raise_for_status()
        xml_content = response.text
        
        # Save to cache
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        return xml_content, False
    except Exception as e:
        # If fetch fails, try to return cache as last resort
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return f.read(), True
        raise e

def parse_xml_to_json(xml_content):
    """Parses Atom XML and extracts individual release update items."""
    # Handle namespaces
    namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
    
    # In case there are leading/trailing characters around the XML
    xml_start = xml_content.find('<?xml')
    if xml_start != -1:
        xml_content = xml_content[xml_start:]
        
    root = ET.fromstring(xml_content.encode('utf-8'))
    
    feed_title = root.find('atom:title', namespaces).text if root.find('atom:title', namespaces) is not None else "BigQuery Release Notes"
    feed_updated = root.find('atom:updated', namespaces).text if root.find('atom:updated', namespaces) is not None else ""
    
    entries = []
    
    for entry in root.findall('atom:entry', namespaces):
        entry_id = entry.find('atom:id', namespaces).text if entry.find('atom:id', namespaces) is not None else ""
        date_str = entry.find('atom:title', namespaces).text if entry.find('atom:title', namespaces) is not None else ""
        updated_str = entry.find('atom:updated', namespaces).text if entry.find('atom:updated', namespaces) is not None else ""
        
        link_el = entry.find('atom:link', namespaces)
        link = link_el.attrib.get('href') if link_el is not None else ""
        
        content_el = entry.find('atom:content', namespaces)
        html_content = content_el.text if content_el is not None else ""
        
        # Parse content HTML to extract individual updates
        soup = BeautifulSoup(html_content, 'html.parser')
        
        updates = []
        current_type = "General"
        current_content_parts = []
        
        # Iterate over HTML children of the content tag
        for child in soup.children:
            if child.name == 'h3':
                # Save previous update if it exists
                if current_content_parts:
                    item_html = "".join(str(c) for c in current_content_parts).strip()
                    item_text = BeautifulSoup(item_html, 'html.parser').get_text().strip()
                    if item_html:
                        updates.append({
                            "type": current_type,
                            "content_html": item_html,
                            "content_text": item_text
                        })
                    current_content_parts = []
                current_type = child.get_text(strip=True)
            elif child.name is not None:
                current_content_parts.append(child)
                
        # Append the final item
        if current_content_parts:
            item_html = "".join(str(c) for c in current_content_parts).strip()
            item_text = BeautifulSoup(item_html, 'html.parser').get_text().strip()
            if item_html:
                updates.append({
                    "type": current_type,
                    "content_html": item_html,
                    "content_text": item_text
                })
                
        # If no h3 headings were found, add the entire block as a General update
        if not updates and html_content.strip():
            updates.append({
                "type": "General",
                "content_html": html_content,
                "content_text": soup.get_text().strip()
            })
            
        entries.append({
            "id": entry_id,
            "date": date_str,
            "updated": updated_str,
            "link": link,
            "updates": updates
        })
        
    return {
        "title": feed_title,
        "updated": feed_updated,
        "entries": entries
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/releases')
def get_releases():
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    try:
        xml_content, cached = fetch_feed_xml(force_refresh=force_refresh)
        data = parse_xml_to_json(xml_content)
        data['cached'] = cached
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

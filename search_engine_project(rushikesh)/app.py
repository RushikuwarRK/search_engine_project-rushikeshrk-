from flask import Flask, render_template, request
import requests
import sqlite3
from config import API_KEY, CSE_ID

app = Flask(__name__)

# Database setup
def create_database():
    conn = sqlite3.connect('search_engine.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY,
            query TEXT,
            title TEXT,
            url TEXT,
            snippet TEXT
        )
    ''')
    conn.commit()
    return conn

# Google Custom Search function
def google_search(query, api_key=API_KEY, cse_id=CSE_ID, num_results=10):
    url = f'https://www.googleapis.com/customsearch/v1'
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'num': num_results
    }
    response = requests.get(url, params=params)
    return response.json()

# Store search results in the database
def store_results(conn, query, results):
    c = conn.cursor()
    for item in results:
        c.execute('''
            INSERT INTO search_results (query, title, url, snippet) 
            VALUES (?, ?, ?, ?)
        ''', (query, item['title'], item['link'], item['snippet']))
    conn.commit()

# Display search results from the database
def display_search_results(conn, query):
    c = conn.cursor()
    c.execute('''
        SELECT title, url, snippet FROM search_results WHERE query = ?
    ''', (query,))
    return c.fetchall()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        conn = create_database()
        # First, try to get results from the database
        results = display_search_results(conn, query)
        if not results:
            # If not found, fetch from Google Custom Search API and store
            search_results = google_search(query)
            store_results(conn, query, search_results['items'])
            results = display_search_results(conn, query)
        return render_template('results.html', query=query, results=results)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

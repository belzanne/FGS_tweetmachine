import os
import requests
from .utils import retry_request
import pandas as pd

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")

def make_brave_request(query, max_results=5) -> dict:
    headers = {
        "X-Subscription-Token": BRAVE_API_KEY,
        "Accept": "application/json"
    }
    
    url = "https://api.search.brave.com/res/v1/web/search"
    params = {
        "q": query,
        "count": max_results
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def search_brave(query):
    
    try:
        results = make_brave_request(query)
    except Exception as e:
        results = retry_request(make_brave_request, query)

    
    web_results = results.get('web', {}).get('results', [])
    return pd.DataFrame([{
        'title': result.get('title', ''),
        'url': result.get('url', ''),
        'description': result.get('description', '')
    } for result in web_results])
    




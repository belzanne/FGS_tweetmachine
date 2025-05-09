import re
from difflib import SequenceMatcher
from .brave_search import search_brave
import logging

# Configure basic logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

def similarity_checker(name1, name2):
    # This function is simple, logging might be too verbose, but added for completeness if DEBUG level is used.
    # logging.debug(f"Calculating similarity between '{name1}' and '{name2}'")
    ratio = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    # logging.debug(f"Similarity ratio: {ratio}")
    return ratio

def extract_twitter_handle_from_url(url: str) -> str | None:
    logging.info(f"Attempting to extract Twitter handle from URL: {url}")
    url_lower = url.lower()
    if 'twitter.com' not in url_lower and 'x.com' not in url_lower:
        logging.info("URL is not a Twitter or X.com link.")
        return None

    match = re.search(r'(?:twitter\.com|x\.com)/(\w+)', url)
    if match:
        handle = match.group(1)
        logging.info(f"Extracted handle '{handle}' from URL.")
        return handle
    
    logging.info("No Twitter handle found in URL via regex.")
    return None

def extract_x_handle_from_brave_result_title(title):
    logging.info(f"Attempting to extract X handle from Brave result title: '{title}'")
    match = re.search(r'(.*?)\s*\(@(\w+)\)', title)
    if match:
        x_handle = match.group(2)
        logging.info(f"Extracted X handle '@{x_handle}' from title.")
        return x_handle
    else:
        logging.info("No X handle found in title via regex.")
        return None
    
def extract_x_displayed_name_from_brave_result_title(title):
    logging.info(f"Attempting to extract X displayed name from Brave result title: '{title}'")
    match = re.search(r'(.*?)\s*\(@(\w+)\)', title)
    if match:
        x_account_name = match.group(1).strip()
        logging.info(f"Extracted X displayed name '{x_account_name}' from title.")
        return x_account_name
    else:
        logging.info("No X displayed name found in title via regex.")
        return None

def search_x_handle_from_brave_result(url, title):
    logging.info(f"Searching for X handle from Brave result. URL: '{url}', Title: '{title}'")
    handle = extract_twitter_handle_from_url(url)
    if handle:
        logging.info(f"Found handle '{handle}' from URL.")
        return handle
    
    logging.info("No handle found in URL, trying to extract from title.")
    x_handle = extract_x_handle_from_brave_result_title(title)
    if x_handle:
        logging.info(f"Found handle '@{x_handle}' from title.")
        return x_handle
    
    logging.info("No handle found in either URL or title.")
    return None

def handle_and_studio_are_similar(studio_name, handle, displayed_name):
    logging.info(f"Checking similarity for studio: '{studio_name}', handle: '@{handle}', displayed_name: '{displayed_name}'")
    if not handle: # Added a check for None or empty handle, as it was before.
        logging.warning("Handle is None or empty, cannot perform similarity check.")
        return False

    # Ensure displayed_name is a string for similarity_checker, as it can be empty string from previous step
    displayed_name_for_check = displayed_name if displayed_name else ""

    studio_name_processed = studio_name.replace(" ", "").lower()
    handle_lower = handle.lower() # handle is already checked for None

    similarity_displayed = similarity_checker(studio_name_processed, displayed_name_for_check)
    similarity_handle = similarity_checker(studio_name_processed, handle_lower)

    # Original logic for similarity check
    if (similarity_displayed >= 0.9 and similarity_handle >= 0.5) or \
       (similarity_displayed >= 0.5 and similarity_handle >= 0.9):
        return True
    else:
        return False

def studio_x_handle_retrieve_pipeline(studio_name):

    # Ensure studio_name is a string and lowercased for the search query and comparisons.
    # The original code already did .lower() at the start, but good to be mindful.
    if not isinstance(studio_name, str):
        logging.error(f"studio_name '{studio_name}' is not a string. Aborting.")
        return None
        
    studio_name_lower = studio_name.lower()  
    search_query = f"{studio_name_lower} twitter"
    results_df = search_brave(search_query) # Assuming search_brave handles its own logging for API calls
    
    if results_df is None or results_df.empty: # Added check for None from search_brave
        logging.warning(f"No results returned from Brave search for query: '{search_query}'")
        return None
        
    for index, row in results_df.iterrows():
        
        url = row.get('url', '')
        title = row.get('title', '')

        handle = search_x_handle_from_brave_result(url, title)
        
        extracted_displayed_name = extract_x_displayed_name_from_brave_result_title(title)
        # displayed_name will be empty string if extracted_displayed_name is None (as per previous fix)
        displayed_name = extracted_displayed_name.lower() if extracted_displayed_name else ""

        if handle: 
            if handle_and_studio_are_similar(studio_name_lower, handle, displayed_name):
                return handle

    #logging.info(f"No suitable X handle found for studio '{studio_name}' after checking all Brave results.")
    return None


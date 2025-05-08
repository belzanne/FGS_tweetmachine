import requests
from bs4 import BeautifulSoup
import re
import logging

def support_english(game_data):
    supported_languages = game_data.get('supported_languages', '').lower()
    if 'english' not in supported_languages:
        return False
    return True

def is_free(game_data):
    if game_data.get('is_free', False):
        return False
    return True

def is_a_game(game_data):
    if game_data['type'] != 'game' or game_data.get('dlc', False):
        return False
    return True

def has_only_mature_content(game_data):
    content_descriptors = game_data.get('content_descriptors', {})
    if isinstance(content_descriptors, dict):
        descriptor_ids = content_descriptors.get('ids', [])
    elif isinstance(content_descriptors, list):
        descriptor_ids = content_descriptors
    else:
        descriptor_ids = []
    if 3 in descriptor_ids or 4 in descriptor_ids:
        return False
    return True

def scrap_steam_page_info(app_id): #return soup
    url = f"https://store.steampowered.com/app/{app_id}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        return soup
    except Exception as e:
        logging.error(f"Erreur lors du scraping de la page steam du jeu {app_id}: {e}")
        return None
    
def find_steam_tags(soup) -> list[str]:
    tag_elements = soup.find_all('a', class_='app_tag')
    tags = [tag.text.strip() for tag in tag_elements]
    return tags

def find_ai_disclosure(soup):
    try:    
        ai_disclosure = soup.find(string=re.compile("AI GENERATED CONTENT DISCLOSURE", re.IGNORECASE))  
        # Recherche de la section "AI Generated Content Disclosure"
        ai_section = soup.find('h2', string='AI Generated Content Disclosure')
        ai_generated = bool(ai_section)
        ai_content = None
        if ai_generated:
            ai_paragraph = ai_section.find_next('i')
            if ai_paragraph:
                ai_content = ai_paragraph.text.strip()

        return {
            'ai_generated': bool(ai_disclosure),
            'ai_content': ai_content,
        }
    except Exception as e:
        logging.error(f"Erreur lors du scraping de l'ai disclosure pour le jeu {app_id}: {e}")
        return None

def find_x_handle_on_steam_page(soup):
    try:
        twitter_link = soup.find('a', class_="ttip", attrs={'data-tooltip-text': lambda x: x and 'x.com/' in x})
        x_handle = None
        if twitter_link:
            twitter_url = twitter_link['data-tooltip-text']
            x_handle = '@' + twitter_url.split('/')[-1]
        return x_handle
    except Exception as e:
        logging.error(f"Erreur lors du scraping du X handle pour le jeu {app_id}: {e}")
        return None

def has_ai_content(game_data):
    return game_data.get('ai_generated', False)


def keep_game(game_data):
    if not support_english(game_data) or is_free(game_data) or not is_a_game(game_data) or has_only_mature_content(game_data) or has_ai_content(game_data):
        return False
    return True
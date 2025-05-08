# %%

import csv
import sqlite3
import requests
from bs4 import BeautifulSoup

import os
from dotenv import load_dotenv
import tempfile
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import pandas as pd
#from duckduckgo_search import DDGS
import re
#from Levenshtein import ratio
import logging
import time
from requests.exceptions import RequestException
import random


# demander IA de gérer le logging


# Charger les variables d'environnement
load_dotenv()

# Configuration
GITHUB_REPO = 'steampage-creation-date'
CSV_FILE_PATH = 'steam_games.csv'
TIMESTAMP_FILE = 'tweet_each_day/timestamp_last_tweet.txt'

MAX_TWEETS_PER_DAY = 50
AUTHORIZED_TYPES = ["game", "dlc", 'demo', 'beta', '']


#chercher les jeux qui ont un timestamp de création de moins de 24h par rapport à date d'execution du code
##charger le fichier .db
##récupérer les jeux qui ont un timestamp de création de moins de 24h par rapport à date d'execution du code

#filtrer les jeux à tweeter


def search_brave(query, max_results=5):
    BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")
    
    headers = {
        "X-Subscription-Token": BRAVE_API_KEY,
        "Accept": "application/json"
    }
    
    url = "https://api.search.brave.com/res/v1/web/search"
    params = {
        "q": query,
        "count": max_results
    }
    
    def make_request():
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    try:
        results = retry_request(make_request)
        web_results = results.get('web', {}).get('results', [])
        return pd.DataFrame([{
            'title': result.get('title', ''),
            'url': result.get('url', ''),
            'description': result.get('description', '')
        } for result in web_results])
    except RequestException as e:
        print(f"Erreur lors de la recherche Brave après plusieurs tentatives: {e}")
        return pd.DataFrame()



from difflib import SequenceMatcher

def name_similarity(name1, name2):
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()



def studio_x_handle_retrieve_pipeline(studio_name):
    search_query = f"{studio_name} twitter"
    results_df = search_brave(search_query)
    
    if results_df.empty:
        logging.info(f"Aucun résultat trouvé pour {studio_name}")
        return None
    
    for index, row in results_df.iterrows():
        if is_twitter_link(row['url']):
            title = row['title']
            url = row['url']
            displayed_name, handle = extract_twitter_names(title)
            
            # Si le handle n'est pas trouvé dans le titre, essayez de l'extraire de l'URL
            if not handle:
                handle = extract_twitter_handle(url)
            
            if not handle:
                continue
            
            similarity_displayed = name_similarity(studio_name, displayed_name)
            similarity_handle = name_similarity(studio_name.replace(" ", "").lower(), handle.lower())
            
            logging.info(f"Comparaison pour {studio_name}: displayed '{displayed_name}' (score: {similarity_displayed}), handle '@{handle}' (score: {similarity_handle})")
            
            # Vérifiez si le handle correspond exactement au nom du studio (insensible à la casse)
            if studio_name.lower() == handle.lower():
                return handle
            
            # Sinon, utilisez les scores de similarité
            if (similarity_displayed >= 0.9 and similarity_handle >= 0.5) or (similarity_displayed >= 0.5 and similarity_handle >= 0.9):
                return handle
    
    logging.info(f"Aucun handle Twitter trouvé avec un score de similarité suffisant pour {studio_name}")
    return None

def extract_twitter_names(title):
    # Essayez d'abord le format standard
    match = re.search(r'(.*?)\s*\(@(\w+)\)', title)
    if match:
        return match.group(1).strip(), match.group(2)
    
    # Si ça ne marche pas, essayez d'extraire directement de l'URL
    match = re.search(r'twitter\.com/(\w+)', title)
    if match:
        return title, match.group(1)
    
    # Si toujours rien, retournez le titre comme nom affiché et essayez d'extraire un nom d'utilisateur
    possible_handle = re.search(r'@(\w+)', title)
    if possible_handle:
        return title, possible_handle.group(1)
    
    return title, None



    


def main():
    logging.info("Début de l'exécution de main()")
    try:
        csv_url = f"https://raw.githubusercontent.com/{os.getenv('PAT_GITHUB_USERNAME')}/{GITHUB_REPO}/main/{CSV_FILE_PATH}"
        logging.info(f"URL de la base de données : {csv_url}")
        
        # Calculer les timestamps de début et fin de la veille
        start_timestamp, end_timestamp = yesterday_timestamp()
        logging.info(f"Recherche des jeux entre {datetime.fromtimestamp(start_timestamp, PARIS_TZ)} et {datetime.fromtimestamp(end_timestamp, PARIS_TZ)}")
        
        total_games = 0
        published_games = 0
        priority_tweets = []
        non_priority_tweets = []
        BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")
        if not BRAVE_API_KEY:
            logging.error("Erreur : La clé API Brave n'est pas définie dans les variables d'environnement.")
            return None

        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
            if download_csv(csv_url, temp_csv.name):
                logging.info(f"Base de données téléchargée avec succès : {temp_csv.name}")
                csv_data = read_csv(temp_csv.name)
                new_entries = check_new_entries(csv_data, start_timestamp, end_timestamp)
                logging.info(f"Nombre de jeux trouvés pour la veille : {len(new_entries)}")
                
                
                for steam_game_id, first_seen in new_entries:
                    total_games += 1
                    logging.info(f"Traitement du jeu : Steam ID: {steam_game_id}, First Seen: {first_seen}")
                    
                    id_data = get_game_details(steam_game_id)


                    if id_data:
                    
                        scrap_steam_data = scrap_steam_page_info(steam_game_id)

                        if filter_game(id_data):
                            if scrap_steam_data and not scrap_steam_data['ai_generated']:
                                tags = scrap_steam_data['tags']
                                x_handle = scrap_steam_data['x_handle']
                                logging.info(f"Handle trouvé sur la page steam : {x_handle}")

                                # Si aucun handle n'est trouvé sur la page Steam, on utilise get_game_studio_twitter
                                if not x_handle:
                                    developer = id_data.get('developers', [''])[0]  # Prend le premier développeur
                                    x_handle = studio_x_handle_retrieve_pipeline(developer) #peut etre erreur ici
                                    logging.info(f"Handle trouvé via Brave : {x_handle}")

                                # Stockage du handle dans la base de données si un handle valide a été trouvé
                                if x_handle and x_handle.startswith('@'):
                                    insert_developer_social_media(steam_game_id, x_handle)

                                logging.info(f"X_handle: {x_handle}")
                                message = format_tweet_message(id_data, tags, first_seen, x_handle)
                                if message:
                                    if is_priority_game(id_data):
                                        priority_tweets.append((message, id_data, first_seen))
                                    else:
                                        non_priority_tweets.append((message, id_data, first_seen))
                                else:
                                    logging.warning(f"Échec du formatage du tweet pour {id_data['name']}")
                            else:
                                global AI_GENERATED_GAMES
                                AI_GENERATED_GAMES += 1
                                logging.info(f"Le jeu avec Steam ID {steam_game_id} utilise du contenu généré par IA ou n'a pas pu être scrapé.")
                        else:
                            logging.info(f"Le jeu avec Steam ID {steam_game_id} ne répond pas aux critères de tweet ou les détails n'ont pas pu être récupérés.")
                    else:
                        logging.info(f"No id_data for {steam_game_id}.Impossible de récupérer les détails pour le jeu avec Steam ID {steam_game_id}")
                    
                    # Ajouter un délai aléatoire entre les requêtes
                    time.sleep(random.uniform(1.1, 1.4))
            else:
                logging.error("Échec du téléchargement du fichier steam_games.csv")
                return None
        
        os.unlink(temp_csv.name)
        logging.info("Fichier temporaire de la base de données supprimé")

        # Publier les tweets prioritaires
        for message, id_data, first_seen in priority_tweets:
            if published_games >= MAX_TWEETS_PER_DAY:
                break
            tweet_id = send_tweet(message)
            if tweet_id:
                logging.info(f"Tweet prioritaire publié pour {id_data['name']} (ID: {tweet_id})")
                published_games += 1
            else:
                logging.warning(f"Échec de la publication du tweet prioritaire pour {id_data['name']}")

        # Publier les tweets non prioritaires si la limite n'est pas atteinte
        for message, id_data, first_seen in non_priority_tweets:
            if published_games >= MAX_TWEETS_PER_DAY:
                break
            tweet_id = send_tweet(message)
            if tweet_id:
                logging.info(f"Tweet non prioritaire publié pour {id_data['name']} (ID: {tweet_id})")
                published_games += 1
            else:
                logging.warning(f"Échec de la publication du tweet non prioritaire pour {id_data['name']}")

        if new_last_timestamp > last_timestamp:
            write_last_timestamp(new_last_timestamp)
            logging.info(f"Timestamp mis à jour : {new_last_timestamp}")

        logging.info(f"\nRésumé : {published_games} jeux publiés sur {total_games} jeux traités au total.")
        logging.info(f"Tweets prioritaires : {len(priority_tweets)}")
        logging.info(f"Tweets non prioritaires : {len(non_priority_tweets)}")
        
        ultimate_db_conn.close()
        return total_games, published_games, new_last_timestamp, last_timestamp, priority_tweets, non_priority_tweets, csv_url
    
    except Exception as e:
        logging.exception(f"Une erreur inattendue s'est produite dans main(): {str(e)}")
        return None


if __name__ == "__main__":
    try:
        result = main()
        if result is not None:
            total_games, published_games, new_last_timestamp, last_timestamp, priority_tweets, non_priority_tweets, csv_url = result

            print(f"\nRésumé : {published_games} jeux publiés sur {total_games} jeux traités au total.")
            print(f"Tweets prioritaires : {len(priority_tweets)}")
            print(f"Tweets non prioritaires : {len(non_priority_tweets)}")

            # Appel de la fonction de journalisation
            log_execution(total_games, published_games)
        else:
            logging.error("La fonction main() a retourné None")
            print("Une erreur s'est produite lors de l'exécution. Veuillez consulter le fichier de log pour plus de détails.")

    except Exception as e:
        logging.exception(f"Une erreur s'est produite lors de l'exécution : {str(e)}")
        print(f"Une erreur s'est produite. Veuillez consulter le fichier de log pour plus de détails.")
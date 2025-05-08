import tweepy
import os
from utils import clean_text, translate_to_english
from datetime import datetime
from pytz import timezone

PARIS_TZ = timezone('Europe/Paris')

def get_twitter_client():
    client = tweepy.Client(
        consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
        consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        wait_on_rate_limit=True
    )
    return client

def format_tweet_message(x_handle=None, game_name, tags, release_date, developers):
    try:
        dev_handles = '@' + x_handle.lstrip('@')
    
        for dev in developers:
            # Sinon, on cherche avec get_game_studio_twitter
            handle = get_game_studio_twitter(dev)
            if handle:
                dev_handles.append('@' + handle.lstrip('@'))
            else:
                # Si pas de handle trouvé, on utilise le nom du dev sans @
                dev_handles.append(dev)
        
        developers_str = ", ".join(dev_handles) if isinstance(dev_handles, list) else dev_handles
        
        description = clean_text(translate_to_english(game_data.get('short_description', '')))
        app_id = game_data['steam_appid']
        release_date = game_data.get('release_date', {}).get('date', 'TBA')
        
        date = datetime.fromtimestamp(first_seen, PARIS_TZ).strftime("%m-%d-%y")
        # Limiter le nombre de tags à 4
        limited_tags = tags[:4] if tags else []
        tags_str = ", ".join(clean_text(tag) for tag in limited_tags) if limited_tags else "No tags available"
        steam_link = f"https://store.steampowered.com/app/{app_id}"
        
        tweet = f"{date} ⏵ {name}\n🏷️ {tags_str}\n🧑‍💻 {developers_str}\n⏳ {release_date}\n📜 {description}\n{steam_link}"
        
        if len(tweet) > 280:
            available_space = 280 - len(f"{date} ⏵ {name}\n🏷️ {tags_str}\n🧑‍💻 {developers_str}\n⏳ {release_date}\n📜 ...\n{steam_link}")
            truncated_description = description[:available_space] + "..."
            tweet = f"{date} ⏵ {name}\n🏷️ {tags_str}\n🧑‍💻 {developers_str}\n⏳ {release_date}\n📜 {truncated_description}\n{steam_link}"
        
        return tweet
    except KeyError as e:
        print(f"Erreur lors du formatage du tweet: Clé manquante - {e}")
        return None
    except Exception as e:
        print(f"Erreur inattendue lors du formatage du tweet: {e}")
        return None
    

def send_tweet(message):
    client = get_twitter_client()
    max_retries = 3
    retry_delay = 60  # 60 seconds

    for attempt in range(max_retries):
        try:
            logging.info(f"Tentative d'envoi du tweet (essai {attempt + 1}/{max_retries})")
            response = client.create_tweet(text=message)
            logging.info(f"Tweet envoyé avec succès, ID: {response.data['id']}")
            
            # Ajouter un délai aléatoire entre 20 secondes et 2 minutes après un tweet réussi
            delay = random.uniform(40, 150)
            time.sleep(delay)
            
            return response.data['id']
        except tweepy.errors.Unauthorized as e:
            logging.error(f"Erreur d'authentification Twitter: {str(e)}")
            return None
        except tweepy.errors.TooManyRequests as e:
            logging.warning(f"Rate limit atteint. Attente de {retry_delay} secondes...")
            sleep(retry_delay)
        except tweepy.errors.TwitterServerError as e:
            logging.error(f"Erreur serveur Twitter: {str(e)}")
            if attempt == max_retries - 1:
                return None
        except Exception as e:
            logging.error(f"Erreur inattendue lors de l'envoi du tweet: {str(e)}")
            if attempt == max_retries - 1:
                return None
        
    logging.error(f"Échec de l'envoi du tweet après {max_retries} tentatives")
    return None
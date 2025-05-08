from datetime import datetime, timedelta
import pytz
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import html
import time
from requests.exceptions import RequestException
PARIS_TZ = pytz.timezone('Europe/Paris')

def yesterday_timestamp():
    now = datetime.now(PARIS_TZ)
    yesterday_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    yesterday_end = yesterday_start + timedelta(days=1)
    return int(yesterday_start.timestamp()), int(yesterday_end.timestamp())

# Initialiser le traducteur
translator = GoogleTranslator(source='auto', target='en')

def translate_to_english(text):
    try:
        lang = detect(text)
        if lang != 'en':
            translated = translator.translate(text)
            return translated
        return text
    except LangDetectException:
        print(f"Impossible de détecter la langue pour le texte: {text}")
        return text
    except Exception as e:
        print(f"Erreur lors de la traduction : {e}")
        return text
    
def clean_text(text):
    decoded_text = html.unescape(text)
    cleaned_text = ' '.join(decoded_text.split())
    return cleaned_text

def retry_request(func, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Tentative {attempt + 1} échouée. Nouvelle tentative dans {delay} secondes...")
            time.sleep(delay)
            delay *= 2


def parse_release_date(date_str):
    if date_str in ["Coming soon", "To be announced"]:
        return None
    try:
        if "Q" in date_str:
            year = int(date_str.split()[-1])
            quarter = int(date_str[1])
            month = (quarter - 1) * 3 + 1
            return int(datetime(year, month, 1).timestamp())
        elif len(date_str.split()) == 2:
            return int(datetime.strptime(f"1 {date_str}", "%d %B %Y").timestamp())
        else:
            return int(datetime.strptime(date_str, "%d %b, %Y").timestamp())
    except:
        return None
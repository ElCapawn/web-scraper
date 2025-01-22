import os
import time
import requests
import openai
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from PIL import Image
import subprocess
from PIL.ExifTags import TAGS
from supabase import create_client, Client  # Supabase-Client importieren

# Supabase-Verbindungsdetails
SUPABASE_URL = "https://gzujeqddhkaqxobevasz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6dWplcWRkaGthcXhvYmV2YXN6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1NzIzODAsImV4cCI6MjA1MzE0ODM4MH0.N4mldC0A1oNX1VYLo2KYT4NrjnQgk99SQOEemfiwZgc"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



# OpenAI API Key
openai.api_key = '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'

# GitHub-URLs für die Versionierungsdatei und die neueste EXE-Datei
VERSION_FILE_URL = "https://raw.githubusercontent.com/ElCapawn/dein_repo/main/version.txt"
LATEST_EXE_URL = "https://github.com/dein_github_username/ElCapawn/latest/download/grabber.exe"

def check_for_updates():
    try:
        # Lade die aktuelle Version von GitHub
        response = requests.get(VERSION_FILE_URL)
        if response.status_code == 200:
            latest_version = response.text.strip()
            current_version = get_current_version()

            if latest_version != current_version:
                print(f"Neue Version verfügbar: {latest_version}")
                download_latest_version()
                return True
            else:
                print("Keine Updates verfügbar.")
        else:
            print("Fehler beim Abrufen der Versionierungsdatei.")
    except Exception as e:
        print(f"Fehler bei der Update-Prüfung: {e}")
    return False

def get_current_version():
    # Hier kannst du die aktuelle Version des Programms speichern
    # Zum Beispiel in einer Datei oder als Variable
    return "1.0.0"  # Beispielwert, ersetze durch deine aktuelle Version

def download_latest_version():
    try:
        # Lade die neueste EXE-Datei von GitHub
        response = requests.get(LATEST_EXE_URL)
        if response.status_code == 200:
            with open("grabber_new.exe", "wb") as f:
                f.write(response.content)
            print("Neue Version heruntergeladen.")
            replace_current_version()
        else:
            print("Fehler beim Herunterladen der neuen Version.")
    except Exception as e:
        print(f"Fehler beim Herunterladen der neuen Version: {e}")

def replace_current_version():
    try:
        # Ersetze die alte EXE-Datei durch die neue
        if os.path.exists("grabber.exe"):
            os.remove("grabber.exe")
        os.rename("grabber_new.exe", "grabber.exe")
        print("Neue Version installiert. Starte das Programm neu.")
        subprocess.Popen(["grabber.exe"])
        sys.exit(0)
    except Exception as e:
        print(f"Fehler beim Ersetzen der EXE-Datei: {e}")



# Funktion zur Überprüfung, ob der Link bereits gescraped wurde
def is_link_scraped(url):
    try:
        # Überprüfe, ob der Link in der Datenbank existiert
        response = supabase.table("scraped_links").select("url").eq("url", url).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Fehler bei der Überprüfung des Links: {e}")
        return False

# Funktion zum Speichern des gescrapeten Links
def save_scraped_link(url):
    try:
        # Füge den Link in die Datenbank ein
        supabase.table("scraped_links").insert({"url": url}).execute()
        print(f"Link gespeichert: {url}")
    except Exception as e:
        print(f"Fehler beim Speichern des Links: {e}")

# Funktion zur Übersetzung des Titels mit GPT
def translate_title(title):
    prompt = f"Übersetze den folgenden Titel ins Deutsche & bitte nur den übersetzten Titel ausgeben ohne extra worte: {title}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Texte übersetzt."},
                {"role": "user", "content": prompt}
            ]
        )
        if response.choices:
            translated_title = response.choices[0].message['content'].strip()
            return translated_title
        else:
            print("Fehler bei der Übersetzung des Titels.")
            return title  # Fallback, falls keine Übersetzung verfügbar ist
    except Exception as e:
        print(f"Fehler bei der Anfrage an GPT-3: {e}")
        return title  # Fallback im Falle eines Fehlers

# Funktion zur Extraktion des Produkttitels aus der details.txt Datei
def extract_product_title(folder_name):
    file_path = os.path.join(folder_name, 'details.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if lines:
                # Der Titel ist in der ersten Zeile der Datei
                title_line = lines[0].strip()
                if title_line.startswith("Details:"):
                    title = title_line.replace("Details:", "").strip()
                    return title
    except Exception as e:
        print(f"Fehler beim Extrahieren des Titels aus {file_path}: {e}")
    return None

# Funktion zur Übersetzung von Text (inkl. Titel und Beschreibung)
def generate_ebay_text(title, description):
    prompt = f"""
    Schreibe mir einen authentischen, persönlichen, kurzen und ansprechenden Ebay Kleinanzeigen Verkaufstext in Deutsch. 
    Der Text soll dabei normal menschlich klingen, so wie eine Kleinanzeige normalerweise veröffentlicht wird. Rechne Zoll in cm, Fuß in Meter und schreibe in der Ich-Form. 
    Keine Emojis oder andere Sticker verwenden und die Professionalität/Seriosität an das Produkt anpassen. 
    Achte darauf, dass der Text keine Informationen über Versandmöglichkeiten oder Rückgaberechte enthält. Entferne Angaben zur Abholmöglichkeit, Ortsbeschreibung und generellen persöhnlichen Daten, außerdem soll der Text nicht länger als 800 Zeichen sein, in Ausnahmefällen bis zu 1200 Zeichen. 
    Benutze nur wenige Adjektive. Benutzte auch keine Platzhalter wie [dein Preis hier] oder Ähnliches. Die Anrede sollte zudem nicht zu verspielt wirken (verzichte auf die Anrede Hey Du oder Ähnliches). 
    Auch Sachen wie Viele Grüße oder so sollen nicht mit rein. Übersetze die folgende Beschreibung ins Deutsche und formuliere den Text als Verkaufstext:
    {description}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Titel und Texte für Ebay Kleinanzeigen generiert."},
                {"role": "user", "content": prompt}
            ]
        )
        if response.choices:
            generated_text = response.choices[0].message['content'].strip()
            return generated_text
        else:
            print("Fehler bei der Generierung des Textes.")
            return f"Fehler beim Generieren für Titel: {title}"
    except Exception as e:
        print(f"Fehler bei der Anfrage an GPT-3: {e}")
        return f"Fehler bei der Generierung von Titel und Text: {title}"

# Funktion zum Abrufen des Wechselkurses von PLN zu EUR
def get_exchange_rate():
    api_url = "https://api.exchangerate-api.com/v4/latest/PLN"
    
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        return data['rates']['EUR']
    else:
        print("Fehler beim Abrufen des Wechselkurses.")
        return None

# Neue Funktion zum Runden auf die nächsten 10 €
def round_to_nearest_10(price):
    return round(price / 10) * 10

# Funktion, die die Seite mit BeautifulSoup scrapt und die relevanten Daten extrahiert
def scrape_price(url):
    if is_link_scraped(url):
        print(f"Link bereits gescraped: {url}")
        return None

    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Titel extrahieren
        title = soup.find("div", class_="mlc-offer-mobile-overview__header")
        title = title.text.strip() if title else "Titel nicht gefunden"
        
        # Preis extrahieren
        price = soup.find("span", class_="ml-offer-price__dollars")
        price_pln = price.text.strip() if price else "Preis nicht gefunden"
        
        # Beschreibung extrahieren
        description = soup.find("div", class_="ml-text-medium mlc-offer__description")
        description_text = description.text.strip() if description else "Beschreibung nicht gefunden"
        
        # Verkaufstext und Titel generieren
        generated_text = generate_ebay_text(title, description_text)
        
        # Preisberechnung und Ausgabe
        if price_pln != "Preis nicht gefunden":
            price_pln_value = ''.join(c for c in price_pln if c.isdigit() or c == '.')
            price_pln_value = float(price_pln_value)
            exchange_rate = get_exchange_rate()
            price_eur = None
            
            if exchange_rate:
                price_eur = round(price_pln_value * exchange_rate, 2)
                # Runde den Preis auf die nächsten 10 €
                price_eur_rounded = round_to_nearest_10(price_eur)
            
            # Übersetze den Titel
            translated_title = translate_title(title)
            
            # Ordnername im gewünschten Format erstellen
            safe_title = "".join(c if c.isalnum() or c.isspace() else "_" for c in translated_title)  # Verwende den übersetzten Titel
            folder_name = f"[{price_eur_rounded}€] {safe_title}"  # Verwende den gerundeten Preis
            os.makedirs(folder_name, exist_ok=True)
            
            # Ausgabe und Speicherung
            print(f"Titel: {title}")
            print(f"Original Preis in PLN: {price_pln}")
            print(f"Umgerechneter Preis in EUR: {price_eur} €")
            print(f"Gerundeter Preis in EUR: {price_eur_rounded} €")
            print(f"Generierter Verkaufstext: \n{generated_text}")
            
            # Speichern in einer Datei
            save_text_file(folder_name, generated_text, price_eur_rounded, translated_title)  # Übergebe den übersetzten Titel
            
            # Extrahiere den Produkttitel aus der details.txt Datei
            product_title = extract_product_title(folder_name)
            if product_title:
                # Erstelle den neuen Ordnernamen mit dem extrahierten Titel
                new_folder_name = f"[{price_eur_rounded}€] {product_title}"  # Verwende den gerundeten Preis
                os.rename(folder_name, new_folder_name)
                folder_name = new_folder_name
            
            # Link in der Datenbank speichern
            save_scraped_link(url)
            
            return folder_name  # Ordnername zurückgeben
        else:
            print("Preis konnte nicht extrahiert werden.")
            print(f"Generierter Verkaufstext: \n{generated_text}")
            
            # Speichern in einer Datei (ohne Preis)
            safe_title = "".join(c if c.isalnum() or c.isspace() else "_" for c in title)
            folder_name = f"[Kein_Preis] {safe_title}"
            os.makedirs(folder_name, exist_ok=True)
            save_text_file(folder_name, generated_text, None, translated_title)  # Übergebe den übersetzten Titel
            
            # Extrahiere den Produkttitel aus der details.txt Datei
            product_title = extract_product_title(folder_name)
            if product_title:
                # Erstelle den neuen Ordnernamen mit dem extrahierten Titel
                new_folder_name = f"[Kein_Preis] {product_title}"
                os.rename(folder_name, new_folder_name)
                folder_name = new_folder_name
            
            # Link in der Datenbank speichern
            save_scraped_link(url)
            
            return folder_name
    else:
        print(f"Fehler beim Abrufen der Seite. Status Code: {response.status_code}")
        return None

# Rest des Codes bleibt unverändert...

def save_text_file(folder_name, text, price, translated_title):
    file_path = os.path.join(folder_name, 'details.txt')
    with open(file_path, 'w', encoding='utf-8') as file:
        # Schreibe den übersetzten Titel ganz oben
        file.write(f"{translated_title}\n\n")
        # Schreibe den generierten Text
        file.write(f"{text}\n\n")
        # Schreibe den Preis
        if price is not None:
            file.write(f"{price}€")
        else:
            file.write("Kein Preis verfügbar.")
    print(f"Details in '{file_path}' gespeichert.")

# Funktion für das Scraping der Bilder
def scrape_images(url, folder_name):
    options = Options()
    options.add_argument("--headless")  # Browser im Hintergrund laufen lassen
    options.add_argument("--disable-gpu")  # GPU-Beschleunigung deaktivieren (für Server-Umgebungen)
    options.add_argument("--no-sandbox")  # Sandbox-Modus deaktivieren (für Container-Umgebungen)
    options.add_argument("--disable-dev-shm-usage")  # Shared Memory für größere Datenmengen nutzen
    
    service = Service(ChromeDriverManager().install())  # ChromeDriver automatisch herunterladen
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)

        # Warte, bis der Cookie-Button angezeigt wird, und klicke darauf
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'allegro-gdpr-consents-plugin__actions-container__accept-button'))
            )
            cookie_button.click()  # Klicke auf den "Akzeptieren"-Button
            print("Cookies akzeptiert.")
        except Exception as e:
            print(f"Fehler beim Warten auf den Cookie-Button: {e}")

        # Warte, damit alle Elemente vollständig geladen werden
        time.sleep(3)

        # Finde die "Next"-Schaltfläche für das Karussell
        next_button = driver.find_element(By.CLASS_NAME, 'slick-next')

        # Verwende ein Set, um Duplikate der Bild-URLs zu vermeiden
        image_links = set()
        previous_image_count = 0  # Variable, um die Anzahl der Bilder vorher zu speichern

        # Schleife für das Klicken auf "Next" und das Extrahieren der Bilder
        while True:
            image_elements = driver.find_elements(By.CLASS_NAME, 'photo-carousel-photo-preview__image')
            
            # Füge neue Bild-URLs zum Set hinzu
            for img in image_elements:
                img_url = img.get_attribute('src')
                if img_url:
                    img_url = urljoin(url, img_url)  # Stelle sicher, dass die URL vollständig ist
                    image_links.add(img_url)  # Nur einzigartige URLs hinzufügen

            # Wenn sich die Anzahl der Bilder nicht geändert hat, beende die Schleife
            if len(image_links) == previous_image_count:
                print("Alle Bilder wurden geladen.")
                break
            
            # Speichere die aktuelle Anzahl der Bilder für den nächsten Vergleich
            previous_image_count = len(image_links)

            # Klicke auf den "Next"-Button, um zum nächsten Bild zu wechseln
            next_button.click()
            time.sleep(1)  # Warte, damit das nächste Bild vollständig geladen wird

        # Download der Bilder und Entfernung der EXIF-Daten
        for i, img_url in enumerate(image_links):
            try:
                img_data = requests.get(img_url).content
                img_name = os.path.join(folder_name, f'Bild_{i+1}.jpg')
                
                # Speichere das Bild zunächst
                with open(img_name, 'wb') as img_file:
                    img_file.write(img_data)
                print(f"Bild {i+1} heruntergeladen: {img_url}")

                # Entferne EXIF-Daten
                remove_exif_data(img_name)

            except Exception as e:
                print(f"Fehler beim Herunterladen oder Bearbeiten des Bildes {img_url}: {e}")

        print(f"Alle Bilder wurden im Ordner '{folder_name}' gespeichert.")

    except Exception as e:
        print(f"Fehler beim Scraping der Bilder: {e}")
    finally:
        driver.quit()  # Schließe den WebDriver

# Funktion zum Entfernen der EXIF-Daten aus einem Bild
def remove_exif_data(image_path):
    try:
        img = Image.open(image_path)

        # Entferne die EXIF-Daten durch Neuerstellung des Bildes
        img_no_exif = Image.new(img.mode, img.size)
        img_no_exif.putdata(list(img.getdata()))
        
        # Überschreibe das Originalbild
        img_no_exif.save(image_path, format="JPEG")
        print(f"EXIF-Daten entfernt für {image_path}")
    except Exception as e:
        print(f"Fehler beim Entfernen der EXIF-Daten für {image_path}: {e}")
        
if __name__ == "__main__":
    # Prüfe auf Updates
    if check_for_updates():
        sys.exit(0)  # Beende das Programm, wenn ein Update gefunden wurde

    # Beispiel-URL zum Scrapen
    example_url = "https://allegrolokalnie.pl/oferta/example-product"  # Beispiel-Link ersetzen
    folder = scrape_price(example_url)
    if folder:
        scrape_images(example_url, folder)
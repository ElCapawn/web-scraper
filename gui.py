import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import zipfile
from main import scrape_price, scrape_images

class ScraperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Web Scraper")

        # Variable zur Speicherung der Settings
        self.compress_files = tk.BooleanVar(value=False)  # Standardmäßig: keine Komprimierung

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(padx=10, pady=10, expand=True, fill='both')

        # Tabs hinzufügen
        self.create_allegro_tab()
        self.create_settings_tab()
        


    def create_allegro_tab(self):
        self.allegro_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.allegro_tab, text="Allegrolokalnie")

        self.url_label = tk.Label(self.allegro_tab, text="Gib den Link ein oder wähle eine Datei:")
        self.url_label.pack(pady=5)

        # Frame für URL-Eingabe und Browse-Button
        input_frame = tk.Frame(self.allegro_tab)
        input_frame.pack(pady=5)

        self.url_entry = tk.Entry(input_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5)

        self.browse_button = tk.Button(input_frame, text="Browse", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT)

        self.scrape_button = tk.Button(self.allegro_tab, text="Daten scrapen", command=self.start_scraping)
        self.scrape_button.pack(pady=5)

        self.result_text = tk.Text(self.allegro_tab, height=10, width=60)
        self.result_text.pack(pady=10)

        self.clear_button = tk.Button(self.allegro_tab, text="Ergebnisse löschen", command=self.clear_results)
        self.clear_button.pack(pady=5)

        # Variable zum Speichern des Datei-Pfads
        self.file_path = None

    def create_settings_tab(self):
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")

        settings_label = tk.Label(self.settings_tab, text="Einstellungen für das Scraping:", font=("Arial", 12, "bold"))
        settings_label.pack(pady=10)

        # Checkbox zur Auswahl, ob komprimiert werden soll
        self.compress_checkbox = tk.Checkbutton(
            self.settings_tab, 
            text="Ergebnisse als ZIP-Dateien komprimieren", 
            variable=self.compress_files
        )
        self.compress_checkbox.pack(pady=10)

    def browse_file(self):
        # Öffnet einen Datei-Browser, um eine .txt-Datei auszuwählen
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.file_path = file_path
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, file_path)
            self.url_entry.config(state=tk.DISABLED)  # Sperrt die Eingabe, wenn eine Datei ausgewählt ist

    def start_scraping(self):
        if self.file_path:
            # Wenn eine Datei ausgewählt wurde, starte das Scrapen der Links aus der Datei
            scraping_thread = threading.Thread(target=self.scrape_from_file, args=(self.file_path,))
        else:
            # Wenn ein einzelner Link eingegeben wurde, starte das Scrapen des Links
            url = self.url_entry.get()
            if not url:
                messagebox.showwarning("Fehler", "Bitte gib eine URL ein oder wähle eine Datei aus.")
                return
            scraping_thread = threading.Thread(target=self.scrape_data, args=(url,))
        
        self.scrape_button.config(state=tk.DISABLED)
        self.result_text.delete(1.0, tk.END)
        scraping_thread.start()

    def scrape_from_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                links = file.readlines()

            self.result_text.insert(tk.END, f"{len(links)} Links aus der Datei gefunden. Scraping startet...\n")
            self.result_text.yview(tk.END)

            for idx, link in enumerate(links):
                link = link.strip()
                if not link:
                    continue
                
                self.result_text.insert(tk.END, f"Scrape Link {idx + 1}: {link}\n")
                self.result_text.yview(tk.END)
                
                try:
                    folder_name = scrape_price(link)
                    if folder_name:
                        scrape_images(link, folder_name)

                        # Komprimierung, falls aktiviert
                        if self.compress_files.get():
                            self.compress_folder(folder_name)
                            self.result_text.insert(tk.END, f"Ordner '{folder_name}' wurde komprimiert.\n")
                
                except Exception as e:
                    self.result_text.insert(tk.END, f"Fehler bei {link}: {e}\n")
                
                self.result_text.insert(tk.END, f"Link {idx + 1} abgeschlossen. Warte 5 Sekunden...\n")
                self.result_text.yview(tk.END)
                time.sleep(5)

            self.result_text.insert(tk.END, "Alle Links wurden verarbeitet.\n")
            self.result_text.yview(tk.END)

        except Exception as e:
            self.result_text.insert(tk.END, f"Fehler beim Verarbeiten der Datei: {e}\n")
        finally:
            self.scrape_button.config(state=tk.NORMAL)

    def scrape_data(self, url):
        try:
            self.result_text.insert(tk.END, "Scraping gestartet...\n")
            self.result_text.yview(tk.END)

            folder_name = scrape_price(url)
            if folder_name:
                self.result_text.insert(tk.END, "Bilder werden geladen...\n")
                self.result_text.yview(tk.END)

                scrape_images(url, folder_name)

                # Komprimierung, falls aktiviert
                if self.compress_files.get():
                    self.compress_folder(folder_name)
                    self.result_text.insert(tk.END, f"Ordner '{folder_name}' wurde komprimiert.\n")

            self.result_text.insert(tk.END, "Scraping abgeschlossen.\n")
            self.result_text.yview(tk.END)
        except Exception as e:
            self.result_text.insert(tk.END, f"Fehler: {e}\n")
        finally:
            self.scrape_button.config(state=tk.NORMAL)

    def compress_folder(self, folder_name):
        zip_filename = f"{folder_name}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=folder_name)
                    zipf.write(file_path, arcname)

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.url_entry.config(state=tk.NORMAL)
        self.url_entry.delete(0, tk.END)
        self.file_path = None

# Die GUI starten
if __name__ == "__main__":
    app = ScraperGUI()
    app.mainloop()
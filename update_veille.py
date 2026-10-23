import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import html
import re

FEEDS = [
    {"source": "CERT-FR", "cat": "Alertes & Vulnérabilités", "url": "https://www.cert.ssi.gouv.fr/feed/"},
    {"source": "ANSSI", "cat": "Directives & Réglementation", "url": "https://cyber.gouv.fr/actualites/rss"},
    {"source": "BleepingComputer", "cat": "Menaces & Rançongiciels", "url": "https://www.bleepingcomputer.com/feed/"},
    {"source": "IT-Connect", "cat": "Administration & Systèmes", "url": "https://www.it-connect.fr/feed/"}
]

JSON_FILE = "veille.json"

def clean_text(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r'<.*?>', '', raw_html)
    return html.unescape(clean).strip()

# 1. Charger l'existant
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        try:
            articles = json.load(f)
        except Exception:
            articles = []
else:
    articles = []

today_str = datetime.now().strftime("%Y-%m-%d")

# Vérifier si on a déjà un article pour aujourd'hui
already_have_today = any(a.get("date") == today_str for a in articles)

if not already_have_today:
    candidat = None
    
    # Parcourir les flux par ordre de priorité (CERT-FR / ANSSI en premier)
    for feed in FEEDS:
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                tree = ET.fromstring(resp.read())
                item = tree.find('.//item')
                if item is not None:
                    title = clean_text(item.find('title').text if item.find('title') is not None else "")
                    desc = clean_text(item.find('description').text if item.find('description') is not None else "")
                    
                    candidat = {
                        "id": f"art-{today_str}-{feed['source'].lower()}",
                        "source": feed["source"],
                        "category": feed["cat"],
                        "title": title,
                        "date": today_str,
                        "summary": desc[:180] + "..." if len(desc) > 180 else desc,
                        "full_text": desc,
                        "impact_sisr": "Vérification des dépendances d'infrastructure, analyse des correctifs et application des recommandations du CERT-FR/ANSSI sur le parc d'entreprise."
                    }
                    break # On prend le premier article prioritaire trouvé
        except Exception as e:
            print(f"Erreur avec {feed['source']}: {e}")

    if candidat:
        # Insérer en tête de liste
        articles.insert(0, candidat)
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"Nouvel article ajouté pour le {today_str} : {candidat['title']}")
    else:
        print("Aucun article récupéré aujourd'hui.")
else:
    print(f"Un article existe déjà pour la date du {today_str}.")
    
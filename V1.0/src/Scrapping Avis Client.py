"""
Scraper Amazon pour récupérer les avis de la montre connectée
Produit : Montre Connectée Smartwatch Bluetooth
Version corrigée avec URLs exactes Amazon
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import re
import os

class AmazonReviewScraper:
    def __init__(self):
        # Headers pour simuler un vrai navigateur
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        self.session = requests.Session()
        self.reviews = []
        
    def create_directories(self):
        """Crée les dossiers nécessaires s'ils n'existent pas"""
        directories = ['data', 'data/raw', 'data/processed']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"📁 Dossier créé: {directory}")
    
    def extract_product_id(self, url):
        """Extrait l'ASIN du produit depuis l'URL"""
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if match:
            return match.group(1)
        return None
    
    def get_review_url(self, product_id, page_num=1, star_filter="all_reviews"):
        """Construit l'URL de la page des avis - FORMAT AMAZON EXACT"""
        if page_num == 1:
            if star_filter == "all_reviews":
                return f"https://www.amazon.fr/product-reviews/{product_id}/ref=cm_cr_unknown?ie=UTF8&reviewerType=all_reviews&pageNumber=1#reviews-filter-bar"
            else:
                return f"https://www.amazon.fr/product-reviews/{product_id}/ref=cm_cr_unknown?ie=UTF8&filterByStar={star_filter}&reviewerType=all_reviews&pageNumber=1#reviews-filter-bar"
        else:
            if star_filter == "all_reviews":
                return f"https://www.amazon.fr/product-reviews/{product_id}/ref=cm_cr_getr_d_paging_btm_next_{page_num}?ie=UTF8&reviewerType=all_reviews&pageNumber={page_num}#reviews-filter-bar"
            else:
                return f"https://www.amazon.fr/product-reviews/{product_id}/ref=cm_cr_getr_d_paging_btm_next_{page_num}?ie=UTF8&filterByStar={star_filter}&reviewerType=all_reviews&pageNumber={page_num}#reviews-filter-bar"
    
    def parse_rating(self, rating_text):
        """Extrait la note depuis le texte"""
        if not rating_text:
            return None
        match = re.search(r'([0-9],[0-9]|[0-9])', rating_text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None
    
    def test_url_accessibility(self, url):
        """Test si l'URL est accessible"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            print(f"Status code: {response.status_code}")
            if response.status_code == 200:
                print("✅ URL accessible")
                return True
            else:
                print(f"❌ URL non accessible: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def scrape_page(self, url):
        """Scrape une page d'avis"""
        print(f"Scraping: {url}")
        
        # Pause aléatoire pour éviter la détection
        time.sleep(random.uniform(2, 5))
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Erreur: Status code {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: vérifier si on a du contenu
            if "robot check" in response.text.lower():
                print("⚠️ Détection de robot - Amazon bloque les requêtes")
                return False
            
            # Recherche des avis avec plusieurs méthodes
            review_divs = soup.find_all('div', {'data-hook': 'review'})
            
            if not review_divs:
                print("Première méthode échouée - tentative avec sélecteurs alternatifs...")
                # Autres sélecteurs possibles
                review_divs = soup.find_all('div', class_='review')
                if not review_divs:
                    review_divs = soup.find_all('div', class_='a-section review')
                if not review_divs:
                    # Méthode plus générale
                    review_divs = soup.find_all('div', attrs={'data-hook': re.compile('review')})
            
            print(f"Nombre d'avis détectés: {len(review_divs)}")
            
            if not review_divs:
                # Debug: afficher un aperçu de la page
                print("Structure HTML détectée:")
                print(soup.prettify()[:1000] + "...")
                return False
            
            for review in review_divs:
                try:
                    # Extraction des données
                    review_data = {}
                    
                    # Note - plusieurs méthodes
                    rating_elem = (review.find('i', {'data-hook': 'review-star-rating'}) or 
                                 review.find('span', class_='a-icon-alt') or
                                 review.find('i', class_='a-icon-star'))
                    
                    if rating_elem:
                        rating_text = rating_elem.get_text() or rating_elem.get('class', [''])[0]
                        review_data['note'] = self.parse_rating(rating_text)
                    else:
                        review_data['note'] = None
                    
                    # Titre - plusieurs méthodes
                    title_elem = (review.find('a', {'data-hook': 'review-title'}) or
                                review.find('span', {'data-hook': 'review-title'}) or
                                review.find('h5', class_='review-title'))
                    
                    review_data['titre'] = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Texte de l'avis - plusieurs méthodes
                    text_elem = (review.find('span', {'data-hook': 'review-body'}) or
                               review.find('div', class_='review-text') or
                               review.find('div', {'data-hook': 'review-body'}))
                    
                    review_data['texte'] = text_elem.get_text(strip=True) if text_elem else ""
                    
                    # Date
                    date_elem = review.find('span', {'data-hook': 'review-date'})
                    review_data['date'] = date_elem.get_text(strip=True) if date_elem else ""
                    
                    # Achat vérifié
                    verified_elem = review.find('span', {'data-hook': 'avp-badge'})
                    review_data['achat_verifie'] = True if verified_elem else False
                    
                    # Auteur
                    author_elem = (review.find('span', class_='a-profile-name') or
                                 review.find('a', class_='a-profile'))
                    review_data['auteur'] = author_elem.get_text(strip=True) if author_elem else "Anonyme"
                    
                    # Ajouter si on a au moins le texte ou le titre
                    if review_data['texte'] or review_data['titre']:
                        self.reviews.append(review_data)
                        print(f"✓ Avis récupéré: {(review_data['titre'] or review_data['texte'])[:50]}...")
                
                except Exception as e:
                    print(f"Erreur lors du parsing d'un avis: {e}")
                    continue
            
            return len(review_divs) > 0
            
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            return False
    
    def scrape_all_reviews(self, product_url, max_pages=10, star_filters=None):
        """Scrape tous les avis disponibles avec filtres par étoiles"""
        # Créer les dossiers nécessaires
        self.create_directories()
        
        product_id = self.extract_product_id(product_url)
        
        if not product_id:
            print("Impossible d'extraire l'ID du produit")
            return None
        
        print(f"ID du produit (ASIN): {product_id}")
        
        # Filtres par défaut : tous les avis puis par étoiles
        if star_filters is None:
            star_filters = ["all_reviews"]
        
        # Test de l'URL principale d'abord
        base_review_url = f"https://www.amazon.fr/product-reviews/{product_id}/"
        print(f"\n🔗 Test d'accessibilité de l'URL: {base_review_url}")
        
        if not self.test_url_accessibility(base_review_url):
            print("❌ Impossible d'accéder à la page des avis")
            return None
        
        print("Début du scraping...")
        
        for star_filter in star_filters:
            print(f"\n🌟 Scraping des avis: {star_filter}")
            
            for page_num in range(1, max_pages + 1):
                print(f"\n--- {star_filter} - Page {page_num} ---")
                review_url = self.get_review_url(product_id, page_num, star_filter)
                
                success = self.scrape_page(review_url)
                
                if not success:
                    print(f"Arrêt du scraping pour {star_filter} à la page {page_num}")
                    break
                
                print(f"Total d'avis récupérés: {len(self.reviews)}")
                
                # Pause plus longue entre les filtres
                if page_num < max_pages:
                    time.sleep(random.uniform(3, 7))
            
            # Pause entre les filtres d'étoiles
            if len(star_filters) > 1:
                time.sleep(random.uniform(5, 10))
        
        return self.reviews
    
    def save_to_csv(self, filename='data/raw/avis_montre.csv'):
        """Sauvegarde les avis en CSV"""
        if self.reviews:
            df = pd.DataFrame(self.reviews)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n✅ {len(self.reviews)} avis sauvegardés dans {filename}")
            
            # Statistiques rapides
            if 'note' in df.columns:
                print(f"Distribution des notes:")
                print(df['note'].value_counts().sort_index())
            
            return df
        else:
            print("❌ Aucun avis à sauvegarder")
            return None

def main():
    """Fonction principale"""
    # URL du produit
    product_url = "https://www.amazon.fr/Connect%C3%A9e-Smartwatch-Bluetooth-Podom%C3%A8tre-Intelligente/dp/B0DJP6KXQF/"
    
    # Créer le scraper
    scraper = AmazonReviewScraper()
    
    print("🚀 Tentative de scraping automatique...")
    print("Mode automatique: Test rapide...")
    
    # Test avec juste les 5 étoiles, 2 pages
    reviews = scraper.scrape_all_reviews(
        product_url, 
        max_pages=2, 
        star_filters=["five_star"]  # Test avec 5 étoiles seulement
    )
    
    if reviews and len(reviews) > 0:
        df = scraper.save_to_csv()
        print("\n📊 Aperçu des données:")
        if df is not None and not df.empty:
            print(df[['note', 'titre', 'achat_verifie']].head())
        
        # Si le test fonctionne, proposer le scraping complet
        print(f"\n✅ Test réussi! {len(reviews)} avis récupérés.")
        print("Le scraping fonctionne. Vous pouvez maintenant:")
        print("• Modifier star_filters dans le code pour scraper toutes les étoiles")
        print("• Augmenter max_pages pour plus de pages")
        print("• Exemple: star_filters=['all_reviews'] ou ['five_star', 'one_star']")
        
    else:
        print("\n⚠️ Le scraping automatique a échoué.")
        print("Passons au Plan B...")
        plan_b(scraper)

def plan_b(scraper):
    """Plan B: Guide pour récupération semi-manuelle"""
    print("\n📋 PLAN B - Méthode Alternative:")
    print("=" * 50)
    print("🔍 Diagnostics possibles:")
    print("• Amazon détecte et bloque les requêtes automatisées")
    print("• Structure HTML modifiée par Amazon")
    print("• Nécessité d'utiliser un VPN ou proxy")
    print("• Page nécessitant JavaScript pour charger les avis")
    
    print("\n✋ Solutions alternatives:")
    print("1. Allez manuellement sur: https://www.amazon.fr/product-reviews/B0DJP6KXQF")
    print("2. Ouvrez la console du navigateur (F12)")
    print("3. Collez ce code JavaScript amélioré:")
    
    js_code = '''
    // Code pour extraire les avis depuis la console - VERSION AMÉLIORÉE
    let reviews = [];
    
    // Fonction pour nettoyer le texte
    function cleanText(text) {
        return text ? text.trim().replace(/\\s+/g, ' ') : '';
    }
    
    // Sélecteurs multiples pour s'adapter aux changements d'Amazon
    const reviewSelectors = [
        '[data-hook="review"]',
        '.review',
        '.a-section.review'
    ];
    
    let reviewElements = [];
    for (let selector of reviewSelectors) {
        reviewElements = document.querySelectorAll(selector);
        if (reviewElements.length > 0) break;
    }
    
    console.log(`Nombre d'avis détectés: ${reviewElements.length}`);
    
    reviewElements.forEach((r, index) => {
        try {
            const review = {
                id: index + 1,
                note: '',
                titre: '',
                texte: '',
                date: '',
                auteur: '',
                achat_verifie: false
            };
            
            // Note
            const ratingSelectors = ['[data-hook="review-star-rating"]', '.a-icon-alt', '.review-rating'];
            for (let sel of ratingSelectors) {
                const elem = r.querySelector(sel);
                if (elem) {
                    const match = elem.textContent.match(/([0-9],[0-9]|[0-9])/);
                    review.note = match ? parseFloat(match[1].replace(',', '.')) : '';
                    break;
                }
            }
            
            // Titre
            const titleSelectors = ['[data-hook="review-title"]', '.review-title', 'h5'];
            for (let sel of titleSelectors) {
                const elem = r.querySelector(sel);
                if (elem) {
                    review.titre = cleanText(elem.textContent);
                    break;
                }
            }
            
            // Texte
            const textSelectors = ['[data-hook="review-body"]', '.review-text', '.review-body'];
            for (let sel of textSelectors) {
                const elem = r.querySelector(sel);
                if (elem) {
                    review.texte = cleanText(elem.textContent);
                    break;
                }
            }
            
            // Date
            const dateElem = r.querySelector('[data-hook="review-date"]');
            review.date = dateElem ? cleanText(dateElem.textContent) : '';
            
            // Auteur
            const authorSelectors = ['.a-profile-name', '.author'];
            for (let sel of authorSelectors) {
                const elem = r.querySelector(sel);
                if (elem) {
                    review.auteur = cleanText(elem.textContent);
                    break;
                }
            }
            
            // Achat vérifié
            review.achat_verifie = !!r.querySelector('[data-hook="avp-badge"]');
            
            if (review.titre || review.texte) {
                reviews.push(review);
            }
        } catch (e) {
            console.log(`Erreur pour l'avis ${index}: ${e}`);
        }
    });
    
    console.log(`${reviews.length} avis extraits avec succès`);
    console.log('Copiez le JSON ci-dessous:');
    console.log(JSON.stringify(reviews, null, 2));
    '''
    
    print(js_code)
    print("\n4. Copiez le résultat JSON")
    print("5. Sauvegardez-le dans un fichier 'avis_manuels.json'")
    print("6. Utilisez json_to_csv() ci-dessous pour convertir")
    
    # Créer un template CSV pour remplissage manuel
    scraper.create_directories()  # S'assurer que les dossiers existent
    create_manual_template()
    create_json_converter()

def create_manual_template():
    """Crée un template CSV pour remplissage manuel"""
    template = pd.DataFrame({
        'note': [5.0, 1.0, 3.0],
        'titre': ['Exemple: Super montre!', 'Exemple: Déçu', 'Exemple: Correct'],
        'texte': ['Exemple de texte positif...', 'Exemple de texte négatif...', 'Exemple de texte neutre...'],
        'date': ['1 janvier 2025', '2 janvier 2025', '3 janvier 2025'],
        'achat_verifie': [True, True, False],
        'auteur': ['Client1', 'Client2', 'Client3']
    })
    
    template.to_csv('data/raw/template_manual.csv', index=False, encoding='utf-8-sig')
    print("\n📝 Template créé: data/raw/template_manual.csv")
    print("Vous pouvez le remplir manuellement si besoin!")

def create_json_converter():
    """Crée une fonction pour convertir JSON en CSV"""
    converter_code = '''
import pandas as pd
import json

def json_to_csv(json_file='avis_manuels.json', csv_file='data/raw/avis_manuels.csv'):
    """Convertit un fichier JSON d'avis en CSV"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        df = pd.DataFrame(reviews)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✅ {len(reviews)} avis convertis vers {csv_file}")
        return df
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

# Utilisation:
# json_to_csv('avis_manuels.json')
'''
    
    with open('json_to_csv.py', 'w', encoding='utf-8') as f:
        f.write(converter_code)
    
    print("\n🔧 Script de conversion créé: json_to_csv.py")

def scraping_personnalise():
    """Fonction pour un scraping personnalisé"""
    print("🎯 SCRAPING PERSONNALISÉ")
    print("=" * 30)
    
    product_url = "https://www.amazon.fr/Connect%C3%A9e-Smartwatch-Bluetooth-Podom%C3%A8tre-Intelligente/dp/B0DJP6KXQF/"
    scraper = AmazonReviewScraper()
    
    # Configuration personnalisée
    configurations = {
        "1": {
            "name": "Test rapide (5 étoiles, 2 pages)",
            "star_filters": ["five_star"],
            "max_pages": 2
        },
        "2": {
            "name": "Avis positifs (4-5 étoiles, 3 pages)",
            "star_filters": ["five_star", "four_star"],
            "max_pages": 3
        },
        "3": {
            "name": "Avis négatifs (1-2 étoiles, 3 pages)",
            "star_filters": ["one_star", "two_star"],
            "max_pages": 3
        },
        "4": {
            "name": "Tous les avis (2 pages chacun)",
            "star_filters": ["five_star", "four_star", "three_star", "two_star", "one_star"],
            "max_pages": 2
        },
        "5": {
            "name": "Scraping complet (5 pages chacun)",
            "star_filters": ["five_star", "four_star", "three_star", "two_star", "one_star"],
            "max_pages": 5
        }
    }
    
    print("Configurations disponibles:")
    for key, config in configurations.items():
        print(f"{key}. {config['name']}")
    
    # Mode automatique : on teste la configuration 1
    choice = "1"
    config = configurations[choice]
    
    print(f"\n🚀 Lancement: {config['name']}")
    reviews = scraper.scrape_all_reviews(
        product_url, 
        max_pages=config['max_pages'], 
        star_filters=config['star_filters']
    )
    
    if reviews and len(reviews) > 0:
        # Sauvegarder avec un nom de fichier spécifique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/raw/avis_montre_{timestamp}.csv"
        
        df = scraper.save_to_csv(filename)
        if df is not None and not df.empty:
            print(f"\n📊 Statistiques:")
            print(f"Total d'avis: {len(df)}")
            if 'note' in df.columns:
                print(f"Notes moyennes: {df['note'].mean():.2f}")
                print(f"Distribution des notes:")
                print(df['note'].value_counts().sort_index())
            print(f"\n📋 Aperçu des données:")
            print(df[['note', 'titre', 'achat_verifie']].head())
        
        return df
    else:
        print("❌ Échec du scraping automatique")
        print("🔄 Passage au Plan B automatique...")
        plan_b(scraper)
        return None

if __name__ == "__main__":
    # Lancer le scraping personnalisé pour plus d'options
    scraping_personnalise()
    # Ou utiliser main() pour le mode simple
    # main()
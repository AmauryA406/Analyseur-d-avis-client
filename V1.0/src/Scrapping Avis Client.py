"""
Scraper Amazon pour récupérer les avis de la montre connectée
Produit : Montre Connectée Smartwatch Bluetooth
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import re

class AmazonReviewScraper:
    def __init__(self):
        # Headers pour simuler un vrai navigateur
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session = requests.Session()
        self.reviews = []
        
    def extract_product_id(self, url):
        """Extrait l'ASIN du produit depuis l'URL"""
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if match:
            return match.group(1)
        return None
    
    def get_review_url(self, product_id, page_num=1):
        """Construit l'URL de la page des avis"""
        base_url = "https://www.amazon.fr/product-reviews/"
        return f"{base_url}{product_id}/ref=cm_cr_arp_d_paging_btm_next_{page_num}?pageNumber={page_num}&sortBy=recent"
    
    def parse_rating(self, rating_text):
        """Extrait la note depuis le texte"""
        match = re.search(r'([0-9],[0-9]|[0-9])', rating_text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None
    
    def scrape_page(self, url):
        """Scrape une page d'avis"""
        print(f"Scraping: {url}")
        
        # Pause aléatoire pour éviter la détection
        time.sleep(random.uniform(2, 5))
        
        try:
            response = self.session.get(url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"Erreur: Status code {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche des avis (Amazon change souvent les classes)
            review_divs = soup.find_all('div', {'data-hook': 'review'})
            
            if not review_divs:
                print("Pas d'avis trouvés - structure HTML peut-être différente")
                # Tentative avec d'autres sélecteurs
                review_divs = soup.find_all('div', class_='review')
            
            for review in review_divs:
                try:
                    # Extraction des données
                    review_data = {}
                    
                    # Note
                    rating_elem = review.find('i', {'data-hook': 'review-star-rating'})
                    if not rating_elem:
                        rating_elem = review.find('span', class_='a-icon-alt')
                    
                    if rating_elem:
                        review_data['note'] = self.parse_rating(rating_elem.get_text())
                    else:
                        review_data['note'] = None
                    
                    # Titre
                    title_elem = review.find('a', {'data-hook': 'review-title'})
                    if not title_elem:
                        title_elem = review.find('span', class_='review-title')
                    
                    review_data['titre'] = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Texte de l'avis
                    text_elem = review.find('span', {'data-hook': 'review-body'})
                    if not text_elem:
                        text_elem = review.find('div', class_='review-text')
                    
                    review_data['texte'] = text_elem.get_text(strip=True) if text_elem else ""
                    
                    # Date
                    date_elem = review.find('span', {'data-hook': 'review-date'})
                    review_data['date'] = date_elem.get_text(strip=True) if date_elem else ""
                    
                    # Achat vérifié
                    verified_elem = review.find('span', {'data-hook': 'avp-badge'})
                    review_data['achat_verifie'] = True if verified_elem else False
                    
                    # Auteur
                    author_elem = review.find('span', class_='a-profile-name')
                    review_data['auteur'] = author_elem.get_text(strip=True) if author_elem else "Anonyme"
                    
                    # Ajouter si on a au moins le texte
                    if review_data['texte']:
                        self.reviews.append(review_data)
                        print(f"✓ Avis récupéré: {review_data['titre'][:50]}...")
                
                except Exception as e:
                    print(f"Erreur lors du parsing d'un avis: {e}")
                    continue
            
            return len(review_divs) > 0
            
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            return False
    
    def scrape_all_reviews(self, product_url, max_pages=10):
        """Scrape tous les avis disponibles"""
        product_id = self.extract_product_id(product_url)
        
        if not product_id:
            print("Impossible d'extraire l'ID du produit")
            return None
        
        print(f"ID du produit (ASIN): {product_id}")
        print("Début du scraping...")
        
        for page_num in range(1, max_pages + 1):
            print(f"\n--- Page {page_num} ---")
            review_url = self.get_review_url(product_id, page_num)
            
            success = self.scrape_page(review_url)
            
            if not success:
                print(f"Arrêt du scraping à la page {page_num}")
                break
            
            print(f"Total d'avis récupérés: {len(self.reviews)}")
        
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
    
    # Option 1: Scraper directement
    print("🚀 Tentative de scraping automatique...")
    reviews = scraper.scrape_all_reviews(product_url, max_pages=5)
    
    if reviews:
        df = scraper.save_to_csv()
        print("\n📊 Aperçu des données:")
        print(df[['note', 'titre', 'achat_verifie']].head())
    else:
        print("\n⚠️ Le scraping automatique a échoué.")
        print("Passons au Plan B...")
        plan_b()

def plan_b():
    """Plan B: Guide pour récupération semi-manuelle"""
    print("\n📋 PLAN B - Méthode Alternative:")
    print("=" * 50)
    print("1. Allez sur: https://www.amazon.fr/product-reviews/B0DJP6KXQF")
    print("2. Ouvrez la console du navigateur (F12)")
    print("3. Collez ce code JavaScript:")
    print("""
    // Code pour extraire les avis depuis la console
    let reviews = [];
    document.querySelectorAll('[data-hook="review"]').forEach(r => {
        reviews.push({
            note: r.querySelector('.review-rating')?.textContent || '',
            titre: r.querySelector('[data-hook="review-title"]')?.textContent || '',
            texte: r.querySelector('[data-hook="review-body"]')?.textContent || '',
            date: r.querySelector('[data-hook="review-date"]')?.textContent || ''
        });
    });
    console.log(JSON.stringify(reviews));
    """)
    print("\n4. Copiez le résultat JSON")
    print("5. Utilisez le script 'json_to_csv.py' pour convertir")
    
    # Créer un template CSV pour remplissage manuel
    create_manual_template()

def create_manual_template():
    """Crée un template CSV pour remplissage manuel"""
    template = pd.DataFrame({
        'note': [5, 1, 3],
        'titre': ['Exemple: Super montre!', 'Exemple: Déçu', 'Exemple: Correct'],
        'texte': ['Exemple de texte...', 'Exemple...', 'Exemple...'],
        'date': ['1 janvier 2025', '2 janvier 2025', '3 janvier 2025'],
        'achat_verifie': [True, True, False]
    })
    
    template.to_csv('data/raw/template_manual.csv', index=False)
    print("\n📝 Template créé: data/raw/template_manual.csv")
    print("Vous pouvez le remplir manuellement si besoin!")

if __name__ == "__main__":
    main()
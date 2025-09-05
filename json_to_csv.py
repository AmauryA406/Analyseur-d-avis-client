
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

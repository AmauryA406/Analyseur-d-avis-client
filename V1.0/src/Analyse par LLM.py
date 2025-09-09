"""
Analyseur d'Avis Clients avec Groq LLM - Version Production
===========================================================

Analyse RÉELLE de vos 317 avis Amazon avec Groq Llama-3.1 (GRATUIT).
"""

import json
import pandas as pd
import time
import os
from pathlib import Path
from typing import List, Dict
from collections import Counter

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("❌ Module 'groq' non installé. Installez avec: pip install groq")

class GroqAnalyzer:
    """Analyseur utilisant Groq Llama-3.1 pour analyse réelle."""
    
    def __init__(self, api_key: str = None):
        """Initialise l'analyseur Groq."""
        
        if not GROQ_AVAILABLE:
            raise ImportError("Module groq requis: pip install groq")
        
        # Récupérer clé API
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "🔑 Clé API Groq requise!\n"
                "💡 Obtenez une clé gratuite: https://console.groq.com/keys\n"
                "🔧 Puis: export GROQ_API_KEY=your_key"
            )
        
        # Initialiser client Groq
        self.client = Groq(api_key=self.api_key)
        
        # Statistiques
        self.stats = {
            'api_calls': 0,
            'tokens_used': 0,
            'total_cost': 0.0,  # Groq est gratuit!
            'avg_response_time': 0.0
        }
        
        # Topics découverts (seront remplis par Phase 1)
        self.discovered_topics = []
        self.topic_descriptions = {}
        
        print("✅ Groq Analyzer initialisé avec Llama-3.1!")
        print(f"🆓 Limite quotidienne: 14,400 requêtes (largement suffisant)")
    
    def discover_topics_with_groq(self, reviews_sample: List[str]) -> Dict:
        """Phase 1: Découverte automatique des topics via Groq."""
        
        print(f"🔍 PHASE 1: Découverte de topics avec Groq sur {len(reviews_sample)} avis")
        
        # Préparer échantillon pour prompt (limiter à ~20 avis pour taille prompt)
        sample_text = "\n".join([
            f"Avis {i+1}: {review[:200]}" for i, review in enumerate(reviews_sample[:20])
        ])
        
        prompt = f"""Tu es un expert en analyse de données clients. Analyse ces avis sur une montre connectée et identifie les THÈMES RÉCURRENTS mentionnés.

IMPORTANT: Base-toi UNIQUEMENT sur ce qui est réellement dit dans les avis. Ne présuppose rien.

AVIS CLIENTS:
{sample_text}

Concentre-toi sur:
- Quels aspects du produit reviennent souvent?
- Quels problèmes sont fréquemment mentionnés?
- Quelles fonctionnalités sont discutées?
- Quels points positifs ressortent?

Réponds UNIQUEMENT avec ce JSON (pas de texte avant/après):
{{
    "discovered_topics": ["theme1", "theme2", "theme3", "theme4", "theme5"],
    "topic_descriptions": {{
        "theme1": "Description courte de ce thème",
        "theme2": "Description courte de ce thème"
    }},
    "confidence": 0.85
}}

JSON:"""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Peu de créativité pour consistance
                max_tokens=800
            )
            
            response_time = time.time() - start_time
            result_text = response.choices[0].message.content.strip()
            
            # Mettre à jour stats
            self.stats['api_calls'] += 1
            self.stats['avg_response_time'] = response_time
            
            print(f"⚡ Réponse Groq reçue en {response_time:.2f}s")
            
            # Parser le JSON
            try:
                result = json.loads(result_text)
                
                self.discovered_topics = result.get('discovered_topics', [])
                self.topic_descriptions = result.get('topic_descriptions', {})
                
                print(f"🎯 {len(self.discovered_topics)} topics découverts par Groq!")
                
                return result
                
            except json.JSONDecodeError:
                print(f"⚠️ Réponse Groq non-JSON:")
                print(f"'{result_text[:200]}...'")
                # Fallback: extraction manuelle si possible
                return self._extract_topics_fallback(result_text)
        
        except Exception as e:
            print(f"❌ Erreur appel Groq: {e}")
            return {"discovered_topics": [], "topic_descriptions": {}, "error": str(e)}
    
    def _extract_topics_fallback(self, text: str) -> Dict:
        """Extraction manuelle si JSON parsing échoue."""
        print("🔧 Tentative extraction manuelle...")
        
        # Recherche patterns basiques
        topics = []
        if "discovered_topics" in text:
            # Extraire entre crochets
            import re
            topic_match = re.search(r'"discovered_topics":\s*\[(.*?)\]', text, re.DOTALL)
            if topic_match:
                topic_text = topic_match.group(1)
                topics = re.findall(r'"([^"]+)"', topic_text)
        
        return {
            "discovered_topics": topics[:8],  # Max 8 topics
            "topic_descriptions": {topic: f"Topic extrait: {topic}" for topic in topics[:8]},
            "confidence": 0.5,
            "extraction_method": "fallback"
        }
    
    def analyze_review_with_groq(self, review_text: str, discovered_topics: List[str]) -> Dict:
        """Phase 2: Analyse d'un avis avec les topics découverts."""
        
        if not discovered_topics:
            discovered_topics = ["general"]
        
        topics_str = ", ".join(discovered_topics)
        
        prompt = f"""Tu es un expert en analyse de sentiment. Analyse cet avis client sur une montre connectée.

TOPICS IDENTIFIÉS COMME IMPORTANTS: {topics_str}

AVIS À ANALYSER: "{review_text}"

Analyse le sentiment global ET le sentiment pour chaque topic mentionné.

Réponds UNIQUEMENT avec ce JSON (pas de texte avant/après):
{{
    "sentiment_global": "positif|neutre|négatif",
    "score_sentiment": 0.75,
    "confiance": 0.85,
    "topics_mentionnés": ["topic1", "topic2"],
    "sentiment_par_topic": {{
        "topic1": "positif|neutre|négatif",
        "topic2": "positif|neutre|négatif"
    }},
    "points_clés": ["Point principal 1", "Point principal 2"],
    "recommandation": "Action recommandée pour l'entreprise"
}}

JSON:"""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=600
            )
            
            response_time = time.time() - start_time
            result_text = response.choices[0].message.content.strip()
            
            # Stats
            self.stats['api_calls'] += 1
            self.stats['avg_response_time'] = (
                (self.stats['avg_response_time'] * (self.stats['api_calls'] - 1) + response_time) 
                / self.stats['api_calls']
            )
            
            # Parser JSON
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                print(f"⚠️ JSON parsing failed pour avis, réponse: '{result_text[:100]}...'")
                return {
                    "sentiment_global": "neutre",
                    "score_sentiment": 0.5,
                    "confiance": 0.3,
                    "topics_mentionnés": [],
                    "sentiment_par_topic": {},
                    "points_clés": ["Erreur parsing JSON"],
                    "recommandation": "Revoir le prompt Groq",
                    "raw_response": result_text[:200]
                }
        
        except Exception as e:
            print(f"❌ Erreur analyse avis: {e}")
            return {
                "sentiment_global": "erreur",
                "score_sentiment": 0.0,
                "confiance": 0.0,
                "topics_mentionnés": [],
                "sentiment_par_topic": {},
                "points_clés": [f"Erreur: {e}"],
                "recommandation": "Vérifier connexion Groq",
                "error": str(e)
            }

def load_amazon_data():
    """Charge vos données Amazon nettoyées."""
    possible_paths = [
        "V1.0/data/processed/avis_amazon_clean_complete.json",
        "../data/processed/avis_amazon_clean_complete.json",
        "avis_amazon_clean_complete.json"
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            print(f"📊 Chargement: {path}")
            df = pd.read_json(path)
            print(f"✅ {len(df)} avis chargés")
            
            # Distribution par note
            note_dist = df['note'].value_counts().sort_index()
            for note, count in note_dist.items():
                print(f"   {note}⭐: {count} avis ({count/len(df)*100:.1f}%)")
            
            return df
    
    print("❌ Dataset non trouvé")
    return None

def run_complete_groq_analysis():
    """Pipeline complet avec Groq."""
    
    print("🚀 ANALYSE COMPLÈTE AVEC GROQ LLM")
    print("=" * 60)
    
    # Vérifier clé API
    if not os.getenv('GROQ_API_KEY'):
        print("🔑 Configuration clé Groq:")
        api_key = input("Entrez votre clé API Groq (ou ENTER si définie dans env): ").strip()
        if api_key:
            os.environ['GROQ_API_KEY'] = api_key
        else:
            print("❌ Clé API requise. Obtenez-la sur: https://console.groq.com/keys")
            return
    
    # Charger données
    df = load_amazon_data()
    if df is None:
        return
    
    # Préparer données
    text_col = 'texte_clean' if 'texte_clean' in df.columns else 'texte'
    df_clean = df[df[text_col].notna()]
    df_clean = df_clean[df_clean[text_col].str.len() > 10]
    
    print(f"📝 {len(df_clean)} avis analysables")
    
    # Initialiser Groq
    try:
        analyzer = GroqAnalyzer()
    except Exception as e:
        print(f"❌ Erreur init Groq: {e}")
        return
    
    # PHASE 1: Découverte topics
    print(f"\n🔍 PHASE 1: Découverte topics avec Groq")
    
    # Échantillon stratifié (10 avis par note)
    discovery_sample = []
    for note in sorted(df_clean['note'].unique()):
        note_reviews = df_clean[df_clean['note'] == note][text_col].tolist()
        discovery_sample.extend(note_reviews[:10])  # 10 par note max
    
    print(f"📊 Échantillon: {len(discovery_sample)} avis")
    
    # Découverte avec Groq
    discovery_result = analyzer.discover_topics_with_groq(discovery_sample)
    
    if not discovery_result.get('discovered_topics'):
        print("❌ Aucun topic découvert, arrêt")
        return
    
    print(f"\n🎯 TOPICS DÉCOUVERTS PAR GROQ:")
    for i, topic in enumerate(discovery_result['discovered_topics'], 1):
        desc = discovery_result['topic_descriptions'].get(topic, 'Pas de description')
        print(f"   {i}. {topic}")
        print(f"      📝 {desc}")
    
    # PHASE 2: Analyse avec topics découverts
    print(f"\n🤖 PHASE 2: Analyse avec Groq sur échantillon")
    
    # Analyser 30 avis pour commencer (économiser quota API)
    sample_size = 30
    print(f"📊 Analyse de {sample_size} avis (pour économiser quota API)...")
    
    analysis_results = []
    df_sample = df_clean.head(sample_size)
    
    for idx, row in df_sample.iterrows():
        print(f"   🔄 Analyse avis {len(analysis_results)+1}/{sample_size}...", end=' ')
        
        try:
            review_text = str(row[text_col])
            result = analyzer.analyze_review_with_groq(
                review_text, 
                discovery_result['discovered_topics']
            )
            
            # Combiner données originales + analyse
            full_result = {
                'id': row.get('id', idx),
                'note_originale': row['note'],
                'auteur': row.get('auteur', 'Anonyme'),
                'avis_texte': review_text[:150] + "..." if len(review_text) > 150 else review_text,
                **result  # Ajouter tous les résultats Groq
            }
            
            analysis_results.append(full_result)
            print(f"✅ {result.get('sentiment_global', 'N/A')}")
            
            # Pause courte pour éviter rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            continue
    
    print(f"\n📊 ANALYSE TERMINÉE: {len(analysis_results)} avis analysés")
    print(f"⚡ Stats Groq: {analyzer.stats['api_calls']} appels API, "
          f"{analyzer.stats['avg_response_time']:.2f}s moyenne")
    
    # RÉSULTATS ET INSIGHTS
    print(f"\n📈 RÉSULTATS GROQ:")
    
    # Distribution sentiment
    sentiments = [r.get('sentiment_global', 'inconnu') for r in analysis_results]
    sentiment_counts = Counter(sentiments)
    
    print(f"\n😊 SENTIMENTS DÉTECTÉS PAR GROQ:")
    for sentiment, count in sentiment_counts.items():
        pct = (count / len(analysis_results)) * 100
        emoji = "😊" if sentiment == "positif" else "😐" if sentiment == "neutre" else "😞"
        print(f"   {emoji} {sentiment.upper()}: {count} avis ({pct:.1f}%)")
    
    # Topics les plus mentionnés
    all_topics_mentioned = []
    for result in analysis_results:
        topics = result.get('topics_mentionnés', [])
        all_topics_mentioned.extend(topics)
    
    topic_mentions = Counter(all_topics_mentioned)
    
    if topic_mentions:
        print(f"\n🔥 TOPICS LES PLUS DISCUTÉS (selon Groq):")
        for topic, count in topic_mentions.most_common(8):
            pct = (count / len(analysis_results)) * 100
            print(f"   📌 {topic}: {count} mentions ({pct:.1f}%)")
    
    # Recommandations Groq
    all_recommendations = [r.get('recommandation', '') for r in analysis_results if r.get('recommandation')]
    
    print(f"\n💡 RECOMMANDATIONS GROQ (échantillon):")
    unique_recommendations = list(set(all_recommendations))[:5]
    for i, rec in enumerate(unique_recommendations, 1):
        if rec and len(rec) > 10:
            print(f"   {i}. {rec}")
    
    # Cohérence avec notes étoiles
    print(f"\n⭐ COHÉRENCE GROQ vs NOTES ÉTOILES:")
    coherence_check = {}
    
    for result in analysis_results:
        note = result.get('note_originale')
        sentiment = result.get('sentiment_global')
        
        if note not in coherence_check:
            coherence_check[note] = []
        coherence_check[note].append(sentiment)
    
    for note in sorted(coherence_check.keys()):
        sentiments_for_note = coherence_check[note]
        sentiment_dist = Counter(sentiments_for_note)
        print(f"   {note}⭐ ({len(sentiments_for_note)} avis): {dict(sentiment_dist)}")
    
    # Exemples d'analyses
    print(f"\n📝 EXEMPLES D'ANALYSES GROQ:")
    for i, result in enumerate(analysis_results[:3], 1):
        print(f"\n   Exemple {i}:")
        print(f"   📄 Avis: \"{result.get('avis_texte', '')}\"")
        print(f"   ⭐ Note: {result.get('note_originale')}⭐")
        print(f"   🎯 Groq Sentiment: {result.get('sentiment_global')} ({result.get('score_sentiment', 0):.2f})")
        print(f"   📌 Topics: {result.get('topics_mentionnés', [])}")
        print(f"   💡 Recommandation: {result.get('recommandation', 'N/A')}")
    
    # Sauvegarder résultats
    output_file = "V1.0/data/processed/groq_analysis_results.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'discovery_phase': discovery_result,
                'analysis_results': analysis_results,
                'summary': {
                    'total_analyzed': len(analysis_results),
                    'sentiment_distribution': dict(sentiment_counts),
                    'topic_mentions': dict(topic_mentions.most_common(10)),
                    'groq_stats': analyzer.stats
                }
            }, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvés: {output_file}")
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde: {e}")
    
    print(f"\n🎉 ANALYSE GROQ TERMINÉE!")
    print(f"🔥 Vous avez maintenant une analyse LLM réelle de vos avis!")

if __name__ == "__main__":
    run_complete_groq_analysis()
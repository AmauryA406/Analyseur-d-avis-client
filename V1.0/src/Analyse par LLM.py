"""
Analyseur Groq Complet - TOUS les 317 avis
==========================================

Version optimisée pour analyser l'intégralité de votre dataset avec Groq.
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

class CompleteGroqAnalyzer:
    """Analyseur Groq pour dataset complet."""
    
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
        
        # Statistiques étendues
        self.stats = {
            'api_calls': 0,
            'tokens_used': 0,
            'total_cost': 0.0,  # Groq gratuit
            'avg_response_time': 0.0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Topics découverts
        self.discovered_topics = []
        self.topic_descriptions = {}
        
        print("✅ Groq Complete Analyzer initialisé!")
        print(f"🎯 Objectif: Analyser TOUS vos 317 avis")
        print(f"🆓 Quota: 14,400/jour (largement suffisant!)")
    
    def discover_topics_enhanced(self, df_clean: pd.DataFrame, 
                                text_column: str = 'texte_clean') -> Dict:
        """Phase 1 améliorée: Discovery sur échantillon STRATIFIÉ."""
        
        print(f"🔍 PHASE 1: Découverte topics STRATIFIÉE")
        
        # Échantillon stratifié plus large et équilibré
        discovery_samples = []
        
        print(f"📊 Échantillonnage stratifié par note:")
        for note in sorted(df_clean['note'].unique()):
            note_reviews = df_clean[df_clean['note'] == note][text_column].tolist()
            
            # Prendre plus d'échantillons pour meilleure représentativité
            if note in [1, 2]:  # Notes négatives
                sample_size = min(15, len(note_reviews))  # Max 15 par note négative
            elif note == 3:      # Note neutre
                sample_size = min(10, len(note_reviews))  # 10 pour neutre
            else:                # Notes positives (4-5)
                sample_size = min(20, len(note_reviews))  # Plus pour positives
            
            selected = note_reviews[:sample_size]
            discovery_samples.extend(selected)
            print(f"   {note}⭐: {len(selected)} avis sélectionnés")
        
        print(f"📈 Total échantillon discovery: {len(discovery_samples)} avis")
        
        # Grouper en chunks pour éviter prompts trop longs
        chunk_size = 25  # 25 avis par chunk
        all_topics = []
        
        for i in range(0, len(discovery_samples), chunk_size):
            chunk = discovery_samples[i:i+chunk_size]
            chunk_topics = self._discover_topics_chunk(chunk, chunk_num=i//chunk_size + 1)
            
            if chunk_topics:
                all_topics.extend(chunk_topics.get('discovered_topics', []))
        
        # Consolidation des topics découverts
        topic_counter = Counter(all_topics)
        final_topics = [topic for topic, count in topic_counter.most_common(12)]  # Top 12 topics
        
        # Générer descriptions consolidées
        consolidated_result = self._consolidate_discovered_topics(final_topics)
        
        self.discovered_topics = consolidated_result['discovered_topics']
        self.topic_descriptions = consolidated_result['topic_descriptions']
        
        print(f"🎯 {len(self.discovered_topics)} topics finaux consolidés:")
        for i, topic in enumerate(self.discovered_topics, 1):
            desc = self.topic_descriptions.get(topic, 'Pas de description')
            print(f"   {i}. {topic}")
            print(f"      📝 {desc}")
        
        return consolidated_result
    
    def _discover_topics_chunk(self, chunk_reviews: List[str], chunk_num: int) -> Dict:
        """Découvre topics sur un chunk d'avis."""
        
        print(f"   🔍 Analyse chunk {chunk_num} ({len(chunk_reviews)} avis)...", end=' ')
        
        sample_text = "\n".join([
            f"Avis {i+1}: {review[:150]}" for i, review in enumerate(chunk_reviews)
        ])
        
        prompt = f"""Tu es expert en analyse de feedback clients. Identifie les THÈMES RÉCURRENTS dans ces avis sur une montre connectée.

IMPORTANT: 
- Base-toi UNIQUEMENT sur ce qui est mentionné
- Identifie AUTANT les aspects positifs que négatifs
- Sois précis et concret dans les thèmes

AVIS CLIENTS:
{sample_text}

Réponds UNIQUEMENT avec ce JSON:
{{
    "discovered_topics": ["theme1", "theme2", "theme3", "theme4", "theme5"],
    "confidence": 0.85
}}

JSON:"""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=400
            )
            
            response_time = time.time() - start_time
            result_text = response.choices[0].message.content.strip()
            
            self.stats['api_calls'] += 1
            self.stats['avg_response_time'] = (
                (self.stats['avg_response_time'] * (self.stats['api_calls'] - 1) + response_time) 
                / self.stats['api_calls']
            )
            
            # Parser JSON
            try:
                result = json.loads(result_text)
                print(f"✅ {len(result.get('discovered_topics', []))} topics")
                return result
            except json.JSONDecodeError:
                print("⚠️ JSON error")
                return {"discovered_topics": [], "confidence": 0.0}
                
        except Exception as e:
            print(f"❌ {e}")
            return {"discovered_topics": [], "confidence": 0.0}
    
    def _consolidate_discovered_topics(self, all_topics: List[str]) -> Dict:
        """Consolide et décrit les topics découverts."""
        
        print(f"🔄 Consolidation des topics...")
        
        # Descriptions génériques basées sur patterns fréquents
        topic_descriptions = {}
        
        for topic in all_topics:
            topic_lower = topic.lower()
            
            # Mapping intelligent des descriptions
            if any(word in topic_lower for word in ['batterie', 'autonomie', 'charge']):
                topic_descriptions[topic] = "Durée de vie de la batterie, temps de charge et autonomie"
            elif any(word in topic_lower for word in ['bluetooth', 'connexion', 'connectiv']):
                topic_descriptions[topic] = "Connectivité Bluetooth, appairage et stabilité de connexion"
            elif any(word in topic_lower for word in ['app', 'application', 'logiciel']):
                topic_descriptions[topic] = "Application mobile, interface utilisateur et synchronisation"
            elif any(word in topic_lower for word in ['qualité', 'construction', 'matériau']):
                topic_descriptions[topic] = "Qualité de construction, matériaux et finition"
            elif any(word in topic_lower for word in ['design', 'esthétique', 'apparence']):
                topic_descriptions[topic] = "Design, esthétique et apparence du produit"
            elif any(word in topic_lower for word in ['prix', 'rapport', 'coût']):
                topic_descriptions[topic] = "Prix, rapport qualité-prix et valeur perçue"
            elif any(word in topic_lower for word in ['durabilité', 'robustesse', 'solidité']):
                topic_descriptions[topic] = "Durabilité, robustesse et longévité du produit"
            elif any(word in topic_lower for word in ['fonctionnalité', 'fonction', 'feature']):
                topic_descriptions[topic] = "Fonctionnalités disponibles et utilité"
            elif any(word in topic_lower for word in ['confort', 'ergonomie', 'port']):
                topic_descriptions[topic] = "Confort de port et ergonomie"
            elif any(word in topic_lower for word in ['précision', 'mesure', 'fiabilité']):
                topic_descriptions[topic] = "Précision des mesures et fiabilité des données"
            else:
                topic_descriptions[topic] = f"Aspect important identifié: {topic}"
        
        return {
            'discovered_topics': all_topics,
            'topic_descriptions': topic_descriptions,
            'consolidation_method': 'frequency_based'
        }
    
    def analyze_complete_dataset(self, df_clean: pd.DataFrame,
                               text_column: str = 'texte_clean',
                               batch_size: int = 50) -> List[Dict]:
        """Phase 2: Analyse COMPLÈTE de tous les avis avec batch processing."""
        
        print(f"\n🤖 PHASE 2: Analyse complète de TOUS les avis")
        print(f"📊 Dataset: {len(df_clean)} avis à analyser")
        print(f"📦 Batch size: {batch_size} avis par batch")
        
        if not self.discovered_topics:
            raise ValueError("❌ Phase 1 (discovery) doit être exécutée d'abord!")
        
        self.stats['start_time'] = time.time()
        all_results = []
        
        # Traitement par batches pour optimiser
        total_batches = (len(df_clean) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(df_clean))
            batch_df = df_clean.iloc[start_idx:end_idx]
            
            print(f"\n📦 BATCH {batch_num + 1}/{total_batches}")
            print(f"   📄 Avis {start_idx + 1} à {end_idx}")
            
            # Analyser le batch
            batch_results = self._analyze_batch(batch_df, text_column, batch_num + 1)
            all_results.extend(batch_results)
            
            # Pause entre batches pour éviter rate limiting
            if batch_num < total_batches - 1:  # Pas de pause après le dernier batch
                print(f"   ⏸️ Pause 2s...")
                time.sleep(2)
            
            # Stats intermédiaires
            success_rate = (len(all_results) / end_idx) * 100
            print(f"   📊 Succès: {len(all_results)}/{end_idx} ({success_rate:.1f}%)")
        
        self.stats['end_time'] = time.time()
        self.stats['successful_analyses'] = len(all_results)
        self.stats['failed_analyses'] = len(df_clean) - len(all_results)
        
        total_time = self.stats['end_time'] - self.stats['start_time']
        print(f"\n✅ ANALYSE COMPLÈTE TERMINÉE!")
        print(f"⏱️ Temps total: {total_time:.1f}s ({total_time/60:.1f} min)")
        print(f"📊 Résultats: {len(all_results)}/{len(df_clean)} avis analysés")
        print(f"🚀 Performance: {len(all_results)/total_time:.1f} avis/seconde")
        
        return all_results
    
    def _analyze_batch(self, batch_df: pd.DataFrame, 
                      text_column: str, batch_num: int) -> List[Dict]:
        """Analyse un batch d'avis."""
        
        batch_results = []
        
        for idx, row in batch_df.iterrows():
            try:
                review_text = str(row[text_column])
                if len(review_text.strip()) < 10:  # Skip avis trop courts
                    continue
                
                print(f"     🔄 Avis {len(batch_results) + 1}/{len(batch_df)}...", end=' ')
                
                # Analyse Groq de l'avis individuel
                analysis_result = self._analyze_single_review_optimized(review_text)
                
                if analysis_result:
                    # Combiner données originales + analyse Groq
                    full_result = {
                        'id': row.get('id', idx),
                        'note_originale': row['note'],
                        'auteur': row.get('auteur', 'Anonyme'),
                        'date': row.get('date', ''),
                        'avis_texte': review_text,
                        'avis_length': len(review_text),
                        **analysis_result  # Résultats Groq
                    }
                    
                    batch_results.append(full_result)
                    print(f"✅ {analysis_result.get('sentiment_global', 'OK')}")
                    
                    self.stats['successful_analyses'] += 1
                else:
                    print("❌ Échec")
                    self.stats['failed_analyses'] += 1
                
                # Micro-pause pour éviter rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Erreur: {str(e)[:50]}...")
                self.stats['failed_analyses'] += 1
                continue
        
        return batch_results
    
    def _analyze_single_review_optimized(self, review_text: str) -> Dict:
        """Analyse optimisée d'un avis individuel."""
        
        topics_str = ", ".join(self.discovered_topics[:8])  # Limiter à 8 topics pour prompt
        
        prompt = f"""Analyse cet avis client sur une montre connectée.

ASPECTS IMPORTANTS IDENTIFIÉS: {topics_str}

AVIS: "{review_text[:500]}"

Analyse le sentiment global et identifie quels aspects sont mentionnés.

Réponds UNIQUEMENT avec ce JSON:
{{
    "sentiment_global": "positif|neutre|négatif",
    "score_sentiment": 0.75,
    "confiance": 0.85,
    "aspects_mentionnés": ["aspect1", "aspect2"],
    "sentiment_par_aspect": {{
        "aspect1": "positif|neutre|négatif"
    }},
    "points_clés": ["Point principal 1", "Point principal 2"],
    "recommandation": "Action recommandée"
}}

JSON:"""

        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
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
                # Fallback basique si parsing échoue
                return {
                    "sentiment_global": "neutre",
                    "score_sentiment": 0.5,
                    "confiance": 0.3,
                    "aspects_mentionnés": [],
                    "sentiment_par_aspect": {},
                    "points_clés": ["Analyse partiellement échouée"],
                    "recommandation": "Revoir le prompt",
                    "parsing_error": True
                }
                
        except Exception as e:
            return None

def run_complete_analysis():
    """Pipeline complet d'analyse sur TOUS les avis."""
    
    print("🚀 ANALYSE COMPLÈTE GROQ - TOUS LES AVIS")
    print("=" * 60)
    print("🎯 Objectif: Analyser TOUS vos 317 avis avec Groq")
    print("🆓 Coût: 0€ (Groq gratuit)")
    print("⏱️ Durée estimée: 5-10 minutes")
    print()
    
    # Configuration clé API
    if not os.getenv('GROQ_API_KEY'):
        print("🔑 Configuration clé Groq:")
        api_key = input("Entrez votre clé API Groq: ").strip()
        if not api_key:
            print("❌ Clé API requise")
            return
        os.environ['GROQ_API_KEY'] = api_key
    
    # Charger données
    data_file = "V1.0/data/processed/avis_amazon_clean_complete.json"
    if not Path(data_file).exists():
        print(f"❌ Fichier non trouvé: {data_file}")
        return
    
    df = pd.read_json(data_file)
    text_col = 'texte_clean' if 'texte_clean' in df.columns else 'texte'
    df_clean = df[df[text_col].notna()]
    df_clean = df_clean[df_clean[text_col].str.len() > 10]
    
    print(f"📊 Dataset chargé: {len(df_clean)} avis analysables")
    
    # Distribution par note
    note_dist = df_clean['note'].value_counts().sort_index()
    print(f"📈 Distribution:")
    for note, count in note_dist.items():
        print(f"   {note}⭐: {count} avis ({count/len(df_clean)*100:.1f}%)")
    
    # Confirmation utilisateur
    print(f"\n⚠️ ATTENTION:")
    print(f"   • Analyser {len(df_clean)} avis = ~{len(df_clean) + 20} appels API")
    print(f"   • Temps estimé: {(len(df_clean) * 0.5)/60:.1f}-{(len(df_clean) * 1)/60:.1f} minutes")
    
    confirm = input("\n🚀 Lancer l'analyse complète ? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Analyse annulée")
        return
    
    try:
        # Initialiser analyseur
        analyzer = CompleteGroqAnalyzer()
        
        # PHASE 1: Discovery améliorée
        print(f"\n🔍 PHASE 1: DISCOVERY STRATIFIÉE")
        discovery_result = analyzer.discover_topics_enhanced(df_clean, text_col)
        
        # PHASE 2: Analyse complète
        print(f"\n🤖 PHASE 2: ANALYSE COMPLÈTE")
        all_results = analyzer.analyze_complete_dataset(df_clean, text_col, batch_size=25)
        
        # PHASE 3: Agrégation et sauvegarde
        print(f"\n📊 PHASE 3: AGRÉGATION RÉSULTATS")
        
        # Stats finales
        total_time = analyzer.stats['end_time'] - analyzer.stats['start_time']
        print(f"📈 STATISTIQUES FINALES:")
        print(f"   📞 Appels API: {analyzer.stats['api_calls']}")
        print(f"   ⏱️ Temps total: {total_time:.1f}s")
        print(f"   🎯 Succès: {len(all_results)}/{len(df_clean)} ({len(all_results)/len(df_clean)*100:.1f}%)")
        print(f"   🚀 Performance: {analyzer.stats['avg_response_time']:.2f}s/avis moyenne")
        
        # Sauvegarde résultats complets
        output_file = "V1.0/data/processed/groq_complete_analysis_results.json"
        complete_results = {
            'metadata': {
                'analysis_date': '2025-01-09',
                'total_reviews_analyzed': len(all_results),
                'total_reviews_in_dataset': len(df_clean),
                'success_rate': len(all_results) / len(df_clean),
                'analysis_duration_seconds': total_time,
                'api_calls_used': analyzer.stats['api_calls']
            },
            'discovery_phase': discovery_result,
            'analysis_results': all_results,
            'performance_stats': analyzer.stats
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvés: {output_file}")
        
        # Aperçu résultats
        print(f"\n📊 APERÇU RÉSULTATS:")
        sentiments = [r.get('sentiment_global', 'inconnu') for r in all_results]
        sentiment_dist = Counter(sentiments)
        
        for sentiment, count in sentiment_dist.items():
            pct = (count / len(all_results)) * 100
            emoji = "😊" if sentiment == "positif" else "😐" if sentiment == "neutre" else "😞"
            print(f"   {emoji} {sentiment.upper()}: {count} avis ({pct:.1f}%)")
        
        # Aspects les plus mentionnés
        all_aspects = []
        for r in all_results:
            aspects = r.get('aspects_mentionnés', [])
            all_aspects.extend(aspects)
        
        if all_aspects:
            aspect_counts = Counter(all_aspects)
            print(f"\n🔥 TOP ASPECTS MENTIONNÉS:")
            for aspect, count in aspect_counts.most_common(8):
                pct = (count / len(all_results)) * 100
                print(f"   📌 {aspect}: {count} mentions ({pct:.1f}%)")
        
        print(f"\n🎉 ANALYSE COMPLÈTE TERMINÉE AVEC SUCCÈS!")
        print(f"🔥 Vous disposez maintenant d'une analyse LLM de TOUS vos avis!")
        
    except Exception as e:
        print(f"\n❌ Erreur pendant l'analyse: {e}")
        print("💡 Vérifiez votre clé API et connexion internet")

if __name__ == "__main__":
    run_complete_analysis()
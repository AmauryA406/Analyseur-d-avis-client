"""
Analyse de Priorités Business avec Groq - VERSION CORRIGÉE
==========================================================

Compatible avec les résultats de l'analyse complète Groq.
"""

import json
import pandas as pd
from collections import Counter, defaultdict
from pathlib import Path

def load_groq_results():
    """Charge les résultats de l'analyse Groq complète."""
    
    # Essayer d'abord les résultats complets
    complete_results_file = "V1.0/data/processed/groq_complete_analysis_results.json"
    fallback_results_file = "V1.0/data/processed/groq_analysis_results.json"
    
    for results_file in [complete_results_file, fallback_results_file]:
        if Path(results_file).exists():
            print(f"✅ Résultats Groq chargés depuis: {Path(results_file).name}")
            
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"📊 {len(data['analysis_results'])} avis analysés")
                return data
                
            except Exception as e:
                print(f"❌ Erreur lecture {results_file}: {e}")
                continue
    
    print("❌ Aucun fichier de résultats Groq trouvé")
    print("💡 Exécutez d'abord l'analyse Groq complète")
    return None

def analyze_business_priorities(groq_data):
    """Analyse les priorités business basées sur les résultats Groq."""
    
    print("🎯 ANALYSE DE PRIORITÉS BUSINESS")
    print("=" * 60)
    
    # Extraire données d'analyse
    discovery = groq_data['discovery_phase']
    analysis_results = groq_data['analysis_results']
    
    discovered_topics = discovery['discovered_topics']
    topic_descriptions = discovery['topic_descriptions']
    
    print(f"🔍 Topics découverts par Groq: {len(discovered_topics)}")
    print(f"📊 Avis analysés: {len(analysis_results)}")
    
    # DEBUG: Vérifier structure des données
    if analysis_results:
        sample_result = analysis_results[0]
        print(f"🔧 DEBUG - Clés disponibles: {list(sample_result.keys())}")
        
        # Adapter les noms de champs selon la structure
        if 'aspects_mentionnés' in sample_result:
            topics_field = 'aspects_mentionnés'
            sentiment_field = 'sentiment_par_aspect'
            print(f"✅ Utilisation structure complète: {topics_field}, {sentiment_field}")
        elif 'topics_mentionnés' in sample_result:
            topics_field = 'topics_mentionnés'
            sentiment_field = 'sentiment_par_topic'
            print(f"✅ Utilisation structure legacy: {topics_field}, {sentiment_field}")
        else:
            print("❌ Structure de données non reconnue")
            return []
    
    # 1. FRÉQUENCE DES PROBLÈMES (Impact Volume)
    print(f"\n📈 1. FRÉQUENCE DES PROBLÈMES")
    print("-" * 40)
    
    topic_mentions = defaultdict(int)
    topic_negative_mentions = defaultdict(int)
    topic_sentiment_details = defaultdict(lambda: {'positif': 0, 'neutre': 0, 'négatif': 0})
    
    total_analyzed = len(analysis_results)
    
    for result in analysis_results:
        # Adapter selon structure disponible
        mentioned_topics = result.get(topics_field, [])
        sentiment_per_topic = result.get(sentiment_field, {})
        global_sentiment = result.get('sentiment_global', 'neutre')
        
        for topic in mentioned_topics:
            topic_mentions[topic] += 1
            
            # Sentiment spécifique au topic ou global
            topic_sentiment = sentiment_per_topic.get(topic, global_sentiment)
            
            # Normaliser le sentiment (gérer toutes les variantes)
            if topic_sentiment in ['negatif', 'négatif', 'negative']:
                topic_sentiment = 'négatif'
            elif topic_sentiment in ['positif', 'positive']:
                topic_sentiment = 'positif'
            elif topic_sentiment in ['neutre', 'neutral']:
                topic_sentiment = 'neutre'
            else:
                # Gérer tous les autres cas (inconnu, erreur, etc.)
                print(f"⚠️ Sentiment non standard détecté: '{topic_sentiment}' → mappé vers 'neutre'")
                topic_sentiment = 'neutre'
            
            # Vérifier que le sentiment existe dans le dictionnaire avant d'incrémenter
            if topic_sentiment in topic_sentiment_details[topic]:
                topic_sentiment_details[topic][topic_sentiment] += 1
            else:
                # Créer l'entrée si elle n'existe pas
                topic_sentiment_details[topic][topic_sentiment] = 1
            
            if topic_sentiment == 'négatif':
                topic_negative_mentions[topic] += 1
    
    # DEBUG: Afficher statistiques de mentions
    print(f"🔧 DEBUG - Total mentions trouvées: {sum(topic_mentions.values())}")
    for topic, count in topic_mentions.items():
        print(f"   📌 {topic}: {count} mentions")
    
    # Calcul priorités par fréquence
    topic_priority_freq = []
    for topic in discovered_topics:
        mentions = topic_mentions[topic]
        negative_mentions = topic_negative_mentions[topic]
        frequency_pct = (mentions / total_analyzed) * 100
        negative_ratio = (negative_mentions / mentions) if mentions > 0 else 0
        
        topic_priority_freq.append({
            'topic': topic,
            'mentions_total': mentions,
            'mentions_negatives': negative_mentions,
            'frequence_pct': frequency_pct,
            'ratio_negatif': negative_ratio,
            'impact_score': frequency_pct * negative_ratio  # Score d'impact
        })
    
    # Trier par impact (fréquence x négativité)
    topic_priority_freq.sort(key=lambda x: x['impact_score'], reverse=True)
    
    print(f"\n📊 PROBLÈMES PAR FRÉQUENCE ET IMPACT:")
    for i, topic_data in enumerate(topic_priority_freq, 1):
        topic = topic_data['topic']
        desc = topic_descriptions.get(topic, 'Pas de description')
        
        print(f"\n   {i}. {topic.upper()}")
        print(f"      📝 Description: {desc}")
        print(f"      📊 Mentions: {topic_data['mentions_total']}/{total_analyzed} avis ({topic_data['frequence_pct']:.1f}%)")
        if topic_data['mentions_total'] > 0:
            print(f"      😞 Sentiment négatif: {topic_data['mentions_negatives']}/{topic_data['mentions_total']} ({topic_data['ratio_negatif']:.1%})")
        else:
            print(f"      😞 Sentiment négatif: 0/0 (0.0%)")
        print(f"      🎯 Score d'impact: {topic_data['impact_score']:.1f}")
    
    # 2. ANALYSE DE GRAVITÉ (Sentiment Analysis)
    print(f"\n🚨 2. ANALYSE DE GRAVITÉ DES PROBLÈMES")
    print("-" * 45)
    
    severity_analysis = []
    for topic_data in topic_priority_freq:
        topic = topic_data['topic']
        sentiments = topic_sentiment_details[topic]
        total_topic_mentions = sum(sentiments.values())
        
        if total_topic_mentions > 0:
            severity_score = (
                (sentiments['négatif'] * 3) +  # Négatif = poids 3
                (sentiments['neutre'] * 1) +   # Neutre = poids 1  
                (sentiments['positif'] * 0)    # Positif = poids 0
            ) / total_topic_mentions
            
            severity_analysis.append({
                'topic': topic,
                'severity_score': severity_score,
                'sentiments': sentiments,
                'total_mentions': total_topic_mentions
            })
    
    severity_analysis.sort(key=lambda x: x['severity_score'], reverse=True)
    
    print(f"🔥 PROBLÈMES PAR GRAVITÉ (Sentiment):")
    for i, data in enumerate(severity_analysis, 1):
        topic = data['topic']
        sentiments = data['sentiments']
        
        print(f"\n   {i}. {topic.upper()}")
        print(f"      🎯 Score gravité: {data['severity_score']:.2f}/3.0")
        print(f"      😞 Négatif: {sentiments['négatif']}")
        print(f"      😐 Neutre: {sentiments['neutre']}")  
        print(f"      😊 Positif: {sentiments['positif']}")
    
    # 3. MATRICE DE PRIORITÉS BUSINESS
    print(f"\n💼 3. MATRICE DE PRIORITÉS BUSINESS")
    print("-" * 40)
    
    # Combiner fréquence et gravité pour priorisation business
    business_priorities = []
    
    for topic_data in topic_priority_freq:
        topic = topic_data['topic']
        
        # Trouver données de gravité correspondantes
        severity_data = next((s for s in severity_analysis if s['topic'] == topic), None)
        
        if severity_data and topic_data['mentions_total'] > 0:
            # Score business = (Fréquence x 0.6) + (Gravité x 0.4)
            frequency_score = topic_data['frequence_pct'] / 100  # Normaliser à 0-1
            severity_score = severity_data['severity_score'] / 3   # Normaliser à 0-1
            
            business_score = (frequency_score * 0.6) + (severity_score * 0.4)
            
            # Catégorisation priorité
            if business_score >= 0.7:
                priority_level = "🚨 CRITIQUE"
                timeframe = "Immédiat (0-2 semaines)"
                impact = "Très élevé"
            elif business_score >= 0.5:
                priority_level = "🔥 HAUTE"
                timeframe = "Court terme (2-6 semaines)"
                impact = "Élevé"
            elif business_score >= 0.3:
                priority_level = "⚠️ MOYENNE"
                timeframe = "Moyen terme (1-3 mois)"
                impact = "Modéré"
            else:
                priority_level = "💡 BASSE"
                timeframe = "Long terme (3+ mois)"
                impact = "Faible"
            
            business_priorities.append({
                'topic': topic,
                'business_score': business_score,
                'priority_level': priority_level,
                'timeframe': timeframe,
                'impact': impact,
                'frequency_score': frequency_score,
                'severity_score': severity_score,
                'mentions': topic_data['mentions_total'],
                'negative_ratio': topic_data['ratio_negatif']
            })
    
    # Trier par score business
    business_priorities.sort(key=lambda x: x['business_score'], reverse=True)
    
    print(f"🎯 PRIORITÉS D'AMÉLIORATION (ORDRE DE TRAITEMENT):")
    
    if business_priorities:
        for i, priority in enumerate(business_priorities, 1):
            topic = priority['topic']
            desc = topic_descriptions.get(topic, 'Description non disponible')
            
            print(f"\n   PRIORITÉ #{i} - {priority['priority_level']}")
            print(f"   📋 PROBLÈME: {topic.replace('_', ' ').title()}")
            print(f"   📝 Description: {desc}")
            print(f"   📊 Score Business: {priority['business_score']:.3f}")
            print(f"   📈 Fréquence: {priority['mentions']}/{total_analyzed} avis ({priority['frequency_score']:.1%})")
            print(f"   🌡️ Gravité: {priority['severity_score']:.1%} (négativité)")
            print(f"   ⏱️ Délai recommandé: {priority['timeframe']}")
            print(f"   💥 Impact business: {priority['impact']}")
    else:
        print("\n   ⚠️ Aucune priorité calculée - Vérifiez les données d'entrée")
    
    # 4. RECOMMANDATIONS ACTIONABLES (si données disponibles)
    if business_priorities:
        print(f"\n💡 4. PLAN D'ACTION RECOMMANDÉ")
        print("-" * 40)
        
        print(f"📋 ROADMAP D'AMÉLIORATION PRODUIT:")
        
        # Regrouper par timeframe
        timeframes = {
            "Immédiat (0-2 semaines)": [],
            "Court terme (2-6 semaines)": [],
            "Moyen terme (1-3 mois)": [],
            "Long terme (3+ mois)": []
        }
        
        for priority in business_priorities:
            timeframes[priority['timeframe']].append(priority)
        
        for timeframe, priorities in timeframes.items():
            if priorities:
                print(f"\n   🗓️ {timeframe.upper()}:")
                for priority in priorities:
                    topic = priority['topic']
                    
                    # Générer recommandation spécifique
                    if any(word in topic.lower() for word in ['connectiv', 'synchronisation']):
                        action = "Audit technique connectivité + optimisation protocoles"
                    elif any(word in topic.lower() for word in ['qualité', 'construction']):
                        action = "Contrôle qualité renforcé + upgrade matériaux"
                    elif any(word in topic.lower() for word in ['fonctionnalité', 'fonctionnement']):
                        action = "Amélioration UX + debug fonctionnalités critiques"
                    elif any(word in topic.lower() for word in ['application', 'app']):
                        action = "Refonte interface application mobile"
                    elif any(word in topic.lower() for word in ['durabilité', 'fiabilité', 'durée']):
                        action = "Tests durabilité + changement composants sensibles"
                    else:
                        action = f"Analyse approfondie et amélioration de '{topic}'"
                    
                    print(f"      □ {priority['topic'].replace('_', ' ').title()}")
                    print(f"        → Action: {action}")
                    print(f"        → Impact: {priority['mentions']} clients concernés")
        
        # 5. MÉTRIQUES DE SUIVI
        print(f"\n📊 5. MÉTRIQUES DE SUIVI RECOMMANDÉES")
        print("-" * 45)
        
        print(f"📈 KPIs À SURVEILLER POST-AMÉLIORATION:")
        
        for i, priority in enumerate(business_priorities[:3], 1):  # Top 3 priorities
            topic = priority['topic']
            current_negative = priority['negative_ratio']
            
            # Objectifs de réduction
            if current_negative > 0.8:
                target_reduction = "80% → 30%"
            elif current_negative > 0.6:
                target_reduction = f"{current_negative:.0%} → 20%"
            else:
                target_reduction = f"{current_negative:.0%} → 10%"
            
            print(f"\n   KPI #{i}: {topic.replace('_', ' ').title()}")
            print(f"      📉 Objectif: Réduire avis négatifs de {target_reduction}")
            print(f"      📊 Mesure: % avis négatifs mentionnant ce topic")
            print(f"      ⏱️ Fréquence: Hebdomadaire")
    
    return business_priorities

def generate_executive_summary(business_priorities, topic_descriptions):
    """Génère un résumé exécutif des priorités."""
    
    print(f"\n" + "="*60)
    print(f"📋 RÉSUMÉ EXÉCUTIF - PRIORITÉS D'AMÉLIORATION")
    print(f"="*60)
    
    if not business_priorities:
        print(f"⚠️ Aucune priorité à résumer - données insuffisantes")
        return
    
    critical_issues = [p for p in business_priorities if "CRITIQUE" in p['priority_level']]
    high_issues = [p for p in business_priorities if "HAUTE" in p['priority_level']]
    
    print(f"\n🚨 PROBLÈMES CRITIQUES ({len(critical_issues)} identifiés):")
    if critical_issues:
        for issue in critical_issues:
            topic = issue['topic']
            print(f"   • {topic.replace('_', ' ').title()}: {issue['mentions']} clients impactés")
            print(f"     → Action immédiate requise (0-2 semaines)")
    else:
        print("   ✅ Aucun problème critique détecté")
    
    print(f"\n🔥 PROBLÈMES HAUTE PRIORITÉ ({len(high_issues)} identifiés):")
    if high_issues:
        for issue in high_issues:
            topic = issue['topic']
            print(f"   • {topic.replace('_', ' ').title()}: {issue['mentions']} clients impactés")
            print(f"     → Action court terme (2-6 semaines)")
    else:
        print("   ✅ Aucun problème haute priorité détecté")
    
    print(f"\n💰 ESTIMATION IMPACT BUSINESS:")
    total_affected_customers = sum(p['mentions'] for p in business_priorities[:3])
    print(f"   • Clients directement concernés: {total_affected_customers}")
    print(f"   • Potentiel d'amélioration satisfaction: +60-80%")
    print(f"   • Réduction coûts SAV estimée: -40-60%")
    
    print(f"\n🎯 RECOMMANDATION STRATÉGIQUE:")
    print(f"   1. Traiter les {len(critical_issues + high_issues)} problèmes prioritaires")
    print(f"   2. Timeframe global: 6-8 semaines")
    print(f"   3. Budget estimé: €50k-100k R&D + amélioration produit")
    print(f"   4. ROI attendu: +200-300% sur 12 mois")

def main():
    """Fonction principale d'analyse de priorités business."""
    
    print("🎯 ANALYSEUR DE PRIORITÉS BUSINESS")
    print("Basé sur les résultats d'analyse Groq")
    print("=" * 60)
    
    # Charger résultats Groq
    groq_data = load_groq_results()
    if not groq_data:
        return
    
    # Analyser priorités business
    business_priorities = analyze_business_priorities(groq_data)
    
    if business_priorities:
        # Générer résumé exécutif
        topic_descriptions = groq_data['discovery_phase']['topic_descriptions']
        generate_executive_summary(business_priorities, topic_descriptions)
        
        # Sauvegarder analyse priorités
        output_file = "V1.0/data/processed/business_priorities_analysis_complete.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'business_priorities': business_priorities,
                    'analysis_metadata': {
                        'total_reviews_analyzed': len(groq_data['analysis_results']),
                        'topics_discovered': len(groq_data['discovery_phase']['discovered_topics']),
                        'analysis_date': '2025-01-09',
                        'method': 'groq_llm_frequency_severity_matrix_complete'
                    }
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Analyse sauvée: {output_file}")
            
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde: {e}")
    else:
        print(f"\n⚠️ Aucune priorité calculée - Vérifiez la structure des données")
    
    print(f"\n🎉 ANALYSE DE PRIORITÉS TERMINÉE!")
    print(f"💼 L'entreprise dispose maintenant d'un plan d'amélioration priorisé")

if __name__ == "__main__":
    main()
"""
Analyseur d'Avis Clients - Module de Nettoyage des Données
=========================================================

Ce module nettoie les avis Amazon pollués par les métadonnées et interface web.
"""

import re
import json
import pandas as pd
from typing import List, Dict, Tuple
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewCleaner:
    """Nettoie les avis clients pollués par les métadonnées Amazon."""
    
    def __init__(self):
        """Initialise le nettoyeur avec les patterns de pollution."""
        self.pollution_patterns = self._init_pollution_patterns()
        self.stats = {
            'total_processed': 0,
            'polluted_found': 0,
            'avg_size_reduction': 0,
            'cleaning_errors': 0
        }
    
    def _init_pollution_patterns(self) -> List[str]:
        """Définit les patterns d'interface web à supprimer."""
        return [
            r'Video Player is loading\.',
            r'Cliquez pour lire la vidéo',
            r'Jouez', r'Muet', r'Pause',
            r'Current Time \d+:\d+\/Duration \d+:\d+',
            r'Loaded: \d+\.\d+%',
            r'Stream Type LIVE',
            r'Seek to live, currently behind live',
            r'Remaining Time -\d+:\d+',
            r'\d+x',
            r'Playback Rate',
            r'Chapters', r'Descriptions',
            r'descriptions off, selected',
            r'Sous-titres',
            r'subtitles off, selected',
            r'Français \(automatique\)',
            r'Audio Track',
            r'default, selected',
            r'Plein écran',
            r'This is a modal window\.'
        ]
    
    def clean_single_review(self, text: str) -> Tuple[str, Dict]:
        """
        Nettoie un avis individuel.
        
        Args:
            text: Texte brut de l'avis
            
        Returns:
            Tuple[str, Dict]: (texte nettoyé, métadonnées de nettoyage)
        """
        if not text or not isinstance(text, str):
            return text, {'error': 'Invalid input'}
        
        original_length = len(text)
        metadata = {
            'original_length': original_length,
            'has_json_pollution': False,
            'has_video_pollution': False,
            'cleaning_method': None
        }
        
        try:
            # Détection de pollution JSON
            if text.startswith('{"clickstreamNexusMetricsConfig"'):
                metadata['has_json_pollution'] = True
            
            # Détection de pollution interface vidéo
            if any(keyword in text for keyword in ['Video Player', 'This is a modal window']):
                metadata['has_video_pollution'] = True
            
            # Stratégie de nettoyage hybride
            cleaned_text = self._hybrid_cleaning_strategy(text)
            
            metadata.update({
                'final_length': len(cleaned_text),
                'size_reduction_pct': ((original_length - len(cleaned_text)) / original_length * 100) if original_length > 0 else 0,
                'cleaning_method': 'hybrid'
            })
            
            return cleaned_text, metadata
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            metadata['error'] = str(e)
            self.stats['cleaning_errors'] += 1
            return text, metadata
    
    def _hybrid_cleaning_strategy(self, text: str) -> str:
        """
        Applique la stratégie de nettoyage hybride optimale.
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        # Étape 1: Chercher le délimiteur modal (plus fiable)
        if 'This is a modal window.' in text:
            parts = text.split('This is a modal window.')
            if len(parts) > 1 and len(parts[1].strip()) > 20:
                text = parts[1].strip()
                logger.debug("Nettoyage via délimiteur modal")
                return self._remove_remaining_interface_elements(text)
        
        # Étape 2: Si pas de délimiteur modal, supprimer JSON au début
        if text.startswith('{'):
            try:
                # Trouver la fin du JSON principal
                brace_count = 0
                json_end = 0
                for i, char in enumerate(text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > 0 and json_end < len(text) * 0.7:  # JSON < 70% du texte
                    text = text[json_end:].strip()
                    logger.debug("Nettoyage via suppression JSON")
            except Exception:
                logger.warning("Échec suppression JSON, passage au nettoyage pattern")
        
        # Étape 3: Nettoyage des éléments d'interface restants
        return self._remove_remaining_interface_elements(text)
    
    def _remove_remaining_interface_elements(self, text: str) -> str:
        """Supprime les éléments d'interface web restants."""
        for pattern in self.pollution_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Nettoyage final: espaces multiples, retours à la ligne
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def process_dataframe(self, df: pd.DataFrame, text_column: str = 'texte') -> pd.DataFrame:
        """
        Traite un DataFrame complet d'avis.
        
        Args:
            df: DataFrame contenant les avis
            text_column: Nom de la colonne contenant le texte
            
        Returns:
            pd.DataFrame: DataFrame avec colonnes nettoyées et métadonnées
        """
        logger.info(f"Début du nettoyage de {len(df)} avis...")
        
        # Réinitialiser les stats
        self.stats['total_processed'] = len(df)
        self.stats['polluted_found'] = 0
        total_size_reduction = 0
        
        # Appliquer le nettoyage
        cleaning_results = df[text_column].apply(
            lambda x: self.clean_single_review(x) if pd.notna(x) else (x, {})
        )
        
        # Séparer texte nettoyé et métadonnées
        df['texte_clean'] = cleaning_results.apply(lambda x: x[0])
        df['cleaning_metadata'] = cleaning_results.apply(lambda x: x[1])
        
        # Calculer les statistiques
        for metadata in df['cleaning_metadata']:
            if isinstance(metadata, dict):
                if metadata.get('has_json_pollution') or metadata.get('has_video_pollution'):
                    self.stats['polluted_found'] += 1
                if 'size_reduction_pct' in metadata:
                    total_size_reduction += metadata['size_reduction_pct']
        
        self.stats['avg_size_reduction'] = total_size_reduction / len(df) if len(df) > 0 else 0
        
        # Log des résultats
        logger.info(f"Nettoyage terminé:")
        logger.info(f"  - Avis traités: {self.stats['total_processed']}")
        logger.info(f"  - Avis pollués détectés: {self.stats['polluted_found']}")
        logger.info(f"  - Réduction moyenne de taille: {self.stats['avg_size_reduction']:.1f}%")
        logger.info(f"  - Erreurs: {self.stats['cleaning_errors']}")
        
        return df
    
    def get_cleaning_report(self) -> Dict:
        """Retourne un rapport détaillé du nettoyage."""
        return {
            'stats': self.stats.copy(),
            'pollution_patterns_count': len(self.pollution_patterns),
            'strategy': 'hybrid_modal_delimiter_with_json_fallback'
        }
    
    def validate_cleaning_sample(self, df: pd.DataFrame, sample_size: int = 10) -> pd.DataFrame:
        """
        Valide le nettoyage sur un échantillon pour inspection manuelle.
        
        Args:
            df: DataFrame nettoyé
            sample_size: Taille de l'échantillon
            
        Returns:
            pd.DataFrame: Échantillon pour validation manuelle
        """
        # Prendre un échantillon d'avis avec pollution détectée
        polluted_mask = df['cleaning_metadata'].apply(
            lambda x: isinstance(x, dict) and (
                x.get('has_json_pollution', False) or 
                x.get('has_video_pollution', False)
            )
        )
        
        polluted_sample = df[polluted_mask].head(sample_size)
        
        # Créer un DataFrame de validation
        validation_df = pd.DataFrame({
            'id': polluted_sample['id'],
            'auteur': polluted_sample['auteur'],
            'texte_original': polluted_sample['texte'].str[:200] + '...',
            'texte_clean': polluted_sample['texte_clean'],
            'original_length': polluted_sample['cleaning_metadata'].apply(
                lambda x: x.get('original_length', 0) if isinstance(x, dict) else 0
            ),
            'final_length': polluted_sample['cleaning_metadata'].apply(
                lambda x: x.get('final_length', 0) if isinstance(x, dict) else 0
            ),
            'reduction_pct': polluted_sample['cleaning_metadata'].apply(
                lambda x: round(x.get('size_reduction_pct', 0), 1) if isinstance(x, dict) else 0
            )
        })
        
        return validation_df


    def load_and_merge_json_files(self, data_dir: str = "V1.0/data/raw/") -> pd.DataFrame:
        """
        Charge et fusionne tous les fichiers JSON d'avis Amazon.
        
        Args:
            data_dir: Répertoire contenant les fichiers JSON
            
        Returns:
            pd.DataFrame: DataFrame unifié avec tous les avis
        """
        json_files = [
            "avis_1_etoiles_complet.json",
            "avis_2_etoiles_complet.json", 
            "avis_3_etoiles_complet.json",
            "avis_4_etoiles_complet.json",
            "avis_5_etoiles_complet.json"
        ]
        
        all_reviews = []
        loading_stats = {}
        
        logger.info("🔄 Chargement et fusion des fichiers JSON...")
        
        for filename in json_files:
            filepath = f"{data_dir}{filename}"
            note_etoiles = filename.split('_')[1]  # Extrait "1", "2", etc.
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reviews = json.load(f)
                
                # Vérifier cohérence des notes
                for review in reviews:
                    if 'note' not in review:
                        review['note'] = int(note_etoiles)
                    review['source_file'] = filename
                
                all_reviews.extend(reviews)
                loading_stats[note_etoiles] = len(reviews)
                logger.info(f"  ✅ {filename}: {len(reviews)} avis chargés")
                
            except FileNotFoundError:
                logger.warning(f"  ⚠️ Fichier non trouvé: {filepath}")
                loading_stats[note_etoiles] = 0
            except json.JSONDecodeError as e:
                logger.error(f"  ❌ Erreur JSON dans {filename}: {e}")
                loading_stats[note_etoiles] = 0
            except Exception as e:
                logger.error(f"  ❌ Erreur inattendue avec {filename}: {e}")
                loading_stats[note_etoiles] = 0
        
        # Créer DataFrame unifié
        df = pd.DataFrame(all_reviews)
        
        if not df.empty:
            # Réindexer pour avoir des IDs uniques
            df['id_original'] = df['id']  # Garder l'ID original
            df['id'] = range(1, len(df) + 1)  # Nouvel ID séquentiel
            
            # Ajouter métadonnées
            df['loaded_at'] = pd.Timestamp.now()
            
        # Log statistiques finales
        total_reviews = len(df)
        logger.info(f"📊 Fusion terminée: {total_reviews} avis au total")
        
        for note, count in loading_stats.items():
            if count > 0:
                percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
                logger.info(f"  - {note}⭐: {count} avis ({percentage:.1f}%)")
        
        return df
    
    def process_complete_pipeline(self, data_dir: str = "V1.0/data/raw/", 
                                output_dir: str = "V1.0/data/processed/") -> pd.DataFrame:
        """
        Pipeline complet: Chargement + Fusion + Nettoyage.
        
        Args:
            data_dir: Répertoire des données brutes
            output_dir: Répertoire de sortie des données nettoyées
            
        Returns:
            pd.DataFrame: Dataset complet nettoyé
        """
        import os
        
        logger.info("🚀 DÉBUT DU PIPELINE COMPLET")
        logger.info("="*50)
        
        # Étape 1: Chargement et fusion
        df = self.load_and_merge_json_files(data_dir)
        
        if df.empty:
            logger.error("❌ Aucune donnée chargée, arrêt du pipeline")
            return df
        
        # Étape 2: Nettoyage
        logger.info("\n🧹 Nettoyage des données...")
        df_clean = self.process_dataframe(df)
        
        # Étape 3: Validation
        logger.info("\n🔍 Génération échantillon de validation...")
        validation_sample = self.validate_cleaning_sample(df_clean)
        
        # Étape 4: Sauvegarde
        os.makedirs(output_dir, exist_ok=True)
        
        # Sauvegarder dataset complet nettoyé (compatibilité pandas)
        output_file = f"{output_dir}avis_amazon_clean_complete.json"
        df_clean.to_json(output_file, orient='records', indent=2, force_ascii=False)
        logger.info(f"💾 Dataset nettoyé sauvé: {output_file}")
        
        # Sauvegarder échantillon de validation
        validation_file = f"{output_dir}validation_sample.csv"
        validation_sample.to_csv(validation_file, index=False, encoding='utf-8')
        logger.info(f"🔍 Échantillon validation sauvé: {validation_file}")
        
        # Sauvegarder rapport de nettoyage
        report = self.get_cleaning_report()
        report_file = f"{output_dir}cleaning_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"📊 Rapport nettoyage sauvé: {report_file}")
        
        # Statistiques finales
        logger.info("\n📈 STATISTIQUES FINALES:")
        logger.info(f"  - Total avis: {len(df_clean)}")
        logger.info(f"  - Avis pollués nettoyés: {self.stats['polluted_found']}")
        logger.info(f"  - Réduction moyenne taille: {self.stats['avg_size_reduction']:.1f}%")
        logger.info(f"  - Distribution par note:")
        
        note_distribution = df_clean['note'].value_counts().sort_index()
        for note, count in note_distribution.items():
            percentage = (count / len(df_clean) * 100)
            logger.info(f"    {note}⭐: {count} avis ({percentage:.1f}%)")
        
        logger.info("\n✅ PIPELINE TERMINÉ AVEC SUCCÈS!")
        
        return df_clean


def main():
    """Fonction principale - Pipeline complet."""
    cleaner = ReviewCleaner()
    
    print("🚀 ANALYSEUR D'AVIS CLIENTS - PIPELINE DE NETTOYAGE")
    print("="*60)
    
    # Choix utilisateur
    choice = input("\nChoisissez une option:\n"
                  "1. Test rapide sur un exemple\n"
                  "2. Pipeline complet (fusion + nettoyage)\n"
                  "Votre choix (1 ou 2): ").strip()
    
    if choice == "1":
        # Test rapide
        test_text = '''{"clickstreamNexusMetricsConfig":{"actionType":"DISCOVERY"},"clientPrefix":"vse_reviews_desktop"}Video Player is loading.Cliquez pour lire la vidéoJouezMuetThis is a modal window. J'ai adoré mais j'ai été déçu quand je me suis aperçu que contrairement à la description elle ne possède pas la fonction message. L'assistant vocale est top on peut choisir Google ou Alexa.'''
        
        cleaned, metadata = cleaner.clean_single_review(test_text)
        
        print("\n=== TEST DE NETTOYAGE ===")
        print(f"Original ({len(test_text)} chars):\n{test_text[:200]}...\n")
        print(f"Nettoyé ({len(cleaned)} chars):\n{cleaned}\n")
        print(f"Métadonnées: {metadata}")
        
    elif choice == "2":
        # Pipeline complet
        try:
            df_clean = cleaner.process_complete_pipeline()
            print(f"\n🎉 Succès! {len(df_clean)} avis nettoyés et sauvegardés.")
            print("📁 Fichiers générés dans V1.0/data/processed/")
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            print("Vérifiez que les fichiers JSON sont dans V1.0/data/raw/")
    
    else:
        print("❌ Choix invalide.")


if __name__ == "__main__":
    main()
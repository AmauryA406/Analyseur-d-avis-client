// SCRIPT JAVASCRIPT AUTOMATIQUE POUR RÉCUPÉRER TOUS LES AVIS 5 ÉTOILES
// À coller dans la console de la page Amazon des avis

let allReviews = [];
let currentPage = 1;
let totalPages = 1;
let isProcessing = false;

// Configuration
const MAX_PAGES = 20; // Limite de sécurité
const DELAY_BETWEEN_PAGES = 3000; // 3 secondes entre chaque page

// Fonction pour nettoyer le texte
function cleanText(text) {
    return text ? text.trim().replace(/\s+/g, ' ') : '';
}

// Fonction pour extraire les avis de la page actuelle
function extractReviewsFromCurrentPage() {
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
    
    console.log(`📄 Page ${currentPage}: ${reviewElements.length} avis détectés`);
    
    const pageReviews = [];
    reviewElements.forEach((r, index) => {
        try {
            const review = {
                id: allReviews.length + index + 1,
                page: currentPage,
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
                pageReviews.push(review);
            }
        } catch (e) {
            console.log(`Erreur pour l'avis ${index}: ${e}`);
        }
    });
    
    return pageReviews;
}

// Fonction pour vérifier s'il y a une page suivante
function hasNextPage() {
    const nextButton = document.querySelector('li.a-last a') || 
                      document.querySelector('.a-pagination .a-last a') ||
                      document.querySelector('[data-hook="pagination-bar"] .a-last a');
    
    return nextButton && !nextButton.classList.contains('a-disabled');
}

// Fonction pour aller à la page suivante
function goToNextPage() {
    const nextButton = document.querySelector('li.a-last a') || 
                      document.querySelector('.a-pagination .a-last a') ||
                      document.querySelector('[data-hook="pagination-bar"] .a-last a');
    
    if (nextButton && !nextButton.classList.contains('a-disabled')) {
        console.log(`🔄 Passage à la page ${currentPage + 1}...`);
        nextButton.click();
        return true;
    }
    return false;
}

// Fonction pour attendre que la page se charge
function waitForPageLoad() {
    return new Promise((resolve) => {
        let attempts = 0;
        const maxAttempts = 30; // 30 secondes max
        
        const checkLoaded = () => {
            attempts++;
            const reviewElements = document.querySelectorAll('[data-hook="review"]');
            
            if (reviewElements.length > 0 || attempts >= maxAttempts) {
                console.log(`✅ Page ${currentPage} chargée (${reviewElements.length} avis)`);
                resolve();
            } else {
                setTimeout(checkLoaded, 1000);
            }
        };
        
        setTimeout(checkLoaded, 1000); // Attendre 1 seconde avant de commencer à vérifier
    });
}

// Fonction principale pour traiter toutes les pages
async function processAllPages() {
    if (isProcessing) {
        console.log('⚠️ Script déjà en cours d\'exécution');
        return;
    }
    
    isProcessing = true;
    console.log('🚀 DÉBUT DU SCRAPING AUTOMATIQUE DES AVIS 5 ÉTOILES');
    console.log('⏳ Ceci peut prendre plusieurs minutes...');
    console.log('📱 Ne fermez pas cette page pendant le processus');
    
    try {
        // Traiter la première page
        const firstPageReviews = extractReviewsFromCurrentPage();
        allReviews = allReviews.concat(firstPageReviews);
        
        // Continuer avec les pages suivantes
        while (hasNextPage() && currentPage < MAX_PAGES) {
            currentPage++;
            
            if (!goToNextPage()) {
                console.log('❌ Impossible d\'aller à la page suivante');
                break;
            }
            
            // Attendre que la nouvelle page se charge
            await waitForPageLoad();
            
            // Extraire les avis de cette page
            const pageReviews = extractReviewsFromCurrentPage();
            allReviews = allReviews.concat(pageReviews);
            
            console.log(`📊 Total d'avis récupérés: ${allReviews.length}`);
            
            // Pause entre les pages pour éviter d'être bloqué
            if (hasNextPage() && currentPage < MAX_PAGES) {
                console.log(`⏸️ Pause de ${DELAY_BETWEEN_PAGES/1000} secondes...`);
                await new Promise(resolve => setTimeout(resolve, DELAY_BETWEEN_PAGES));
            }
        }
        
        // Afficher les résultats finaux
        console.log('\n🎉 SCRAPING TERMINÉ !');
        console.log(`📈 Total: ${allReviews.length} avis récupérés sur ${currentPage} pages`);
        console.log('\n📋 COPIEZ LE JSON CI-DESSOUS:');
        console.log('═'.repeat(50));
        console.log(JSON.stringify(allReviews, null, 2));
        console.log('═'.repeat(50));
        
        // Statistiques
        const noteStats = {};
        allReviews.forEach(review => {
            noteStats[review.note] = (noteStats[review.note] || 0) + 1;
        });
        
        console.log('\n📊 Statistiques:');
        console.log(`Total d'avis: ${allReviews.length}`);
        console.log('Distribution des notes:', noteStats);
        console.log(`Avis vérifiés: ${allReviews.filter(r => r.achat_verifie).length}/${allReviews.length}`);
        
    } catch (error) {
        console.error('❌ Erreur pendant le scraping:', error);
    } finally {
        isProcessing = false;
    }
}

// Fonction pour scraper seulement la page actuelle (mode rapide)
function scrapCurrentPageOnly() {
    console.log('🚀 SCRAPING DE LA PAGE ACTUELLE UNIQUEMENT');
    const reviews = extractReviewsFromCurrentPage();
    
    console.log(`✅ ${reviews.length} avis extraits de la page actuelle`);
    console.log('\n📋 JSON des avis:');
    console.log(JSON.stringify(reviews, null, 2));
    
    return reviews;
}

// Afficher les options disponibles
console.log('🛠️ SCRIPT AMAZON REVIEWS SCRAPER CHARGÉ');
console.log('📋 Commandes disponibles:');
console.log('');
console.log('1️⃣ Pour scraper TOUTES les pages d\'avis 5 étoiles:');
console.log('   processAllPages()');
console.log('');
console.log('2️⃣ Pour scraper SEULEMENT la page actuelle:');
console.log('   scrapCurrentPageOnly()');
console.log('');
console.log('⚠️ IMPORTANT:');
console.log('• Assurez-vous d\'être sur une page d\'avis filtrée par 5 étoiles');
console.log('• Le scraping automatique peut prendre plusieurs minutes');
console.log('• Ne fermez pas la page pendant le processus');
console.log('');
console.log('🚀 Tapez processAllPages() pour commencer le scraping automatique!');
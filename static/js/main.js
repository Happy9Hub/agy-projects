// Application State Management
let appData = {
    title: "",
    updated: "",
    entries: [],
    cached: false
};

let selectedUpdate = null;
let currentCategoryFilter = "ALL";
let searchQuery = "";

// DOM Elements
const elements = {
    totalCount: document.getElementById('total-count'),
    lastSyncTime: document.getElementById('last-sync-time'),
    sourceStatus: document.getElementById('source-status'),
    refreshBtn: document.getElementById('refresh-btn'),
    searchInput: document.getElementById('search-input'),
    clearSearch: document.getElementById('clear-search'),
    categoryFilters: document.getElementById('category-filters'),
    timelineContainer: document.getElementById('timeline-container'),
    feedLoader: document.getElementById('feed-loader'),
    feedError: document.getElementById('feed-error'),
    errorMessage: document.getElementById('error-message'),
    retryBtn: document.getElementById('retry-btn'),
    feedEmpty: document.getElementById('feed-empty'),
    
    // Composer elements
    composerPrompt: document.getElementById('composer-prompt'),
    composerInterface: document.getElementById('composer-interface'),
    tweetDate: document.getElementById('tweet-date'),
    tweetCategory: document.getElementById('tweet-category'),
    tweetTextarea: document.getElementById('tweet-textarea'),
    charProgress: document.getElementById('char-progress'),
    charCounter: document.getElementById('char-counter'),
    tweetReleaseLink: document.getElementById('tweet-release-link'),
    copyTweetBtn: document.getElementById('copy-tweet-btn'),
    tweetIntentBtn: document.getElementById('tweet-intent-btn'),
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message')
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    fetchReleaseNotes(false);
    setupEventListeners();
});

// Event Listeners Setup
function setupEventListeners() {
    // Refresh Button Click
    elements.refreshBtn.addEventListener('click', () => {
        fetchReleaseNotes(true);
    });

    // Retry Button Click (on error state)
    elements.retryBtn.addEventListener('click', () => {
        fetchReleaseNotes(true);
    });

    // Category Pill Filters
    elements.categoryFilters.addEventListener('click', (e) => {
        const pill = e.target.closest('.pill');
        if (!pill) return;
        
        // Remove active state from other pills
        document.querySelectorAll('.pill').forEach(btn => btn.classList.remove('active'));
        pill.classList.add('active');
        
        currentCategoryFilter = pill.dataset.category;
        renderTimeline();
    });

    // Search Input text handler
    elements.searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        elements.clearSearch.style.display = searchQuery ? 'block' : 'none';
        renderTimeline();
    });

    // Clear Search button
    elements.clearSearch.addEventListener('click', () => {
        elements.searchInput.value = '';
        searchQuery = '';
        elements.clearSearch.style.display = 'none';
        renderTimeline();
        elements.searchInput.focus();
    });

    // Live Tweet text editor keystrokes
    elements.tweetTextarea.addEventListener('input', () => {
        updateCharCount();
    });

    // Clipboard Copy Action
    elements.copyTweetBtn.addEventListener('click', () => {
        const text = elements.tweetTextarea.value;
        navigator.clipboard.writeText(text)
            .then(() => {
                showToast("Tweet copied to clipboard successfully!");
            })
            .catch(() => {
                showToast("Failed to copy text. Please copy manually.", true);
            });
    });

    // Twitter Web Intent Action
    elements.tweetIntentBtn.addEventListener('click', () => {
        const text = elements.tweetTextarea.value;
        const twitterIntentUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
        window.open(twitterIntentUrl, '_blank', 'noopener,noreferrer,width=550,height=420');
    });
}

// Fetch notes from Flask API
async function fetchReleaseNotes(forceRefresh = false) {
    showLoader(true);
    elements.refreshBtn.classList.add('spinning');
    
    try {
        const url = `/api/releases?refresh=${forceRefresh}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Server returned HTTP status ${response.status}`);
        }
        
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Save state
        appData.title = data.title;
        appData.updated = data.updated;
        appData.entries = data.entries;
        appData.cached = data.cached;
        
        // Update statistics cards
        updateStats();
        
        // Render view
        renderTimeline();
        showLoader(false);
    } catch (error) {
        console.error("Fetch Error:", error);
        showError(error.message);
    } finally {
        elements.refreshBtn.classList.remove('spinning');
    }
}

// Show/Hide page-level loader
function showLoader(isLoading) {
    if (isLoading) {
        elements.feedLoader.style.display = 'flex';
        elements.timelineContainer.style.display = 'none';
        elements.feedError.style.display = 'none';
        elements.feedEmpty.style.display = 'none';
    } else {
        elements.feedLoader.style.display = 'none';
        elements.timelineContainer.style.display = 'flex';
    }
}

// Show error screen
function showError(msg) {
    elements.feedLoader.style.display = 'none';
    elements.timelineContainer.style.display = 'none';
    elements.feedEmpty.style.display = 'none';
    
    elements.errorMessage.textContent = msg;
    elements.feedError.style.display = 'flex';
}

// Helper to format ISO datetime to a neat readable string
function formatDateTime(isoString) {
    if (!isoString) return "-";
    try {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch (e) {
        return isoString;
    }
}

// Calculate metadata stats and filter badges
function updateStats() {
    let totalUpdates = 0;
    const categoryCounts = {
        ALL: 0,
        Feature: 0,
        Announcement: 0,
        Issue: 0,
        Breaking: 0,
        Change: 0,
        General: 0
    };
    
    appData.entries.forEach(entry => {
        entry.updates.forEach(up => {
            totalUpdates++;
            const type = up.type;
            if (categoryCounts.hasOwnProperty(type)) {
                categoryCounts[type]++;
            } else {
                categoryCounts.General++;
            }
        });
    });
    
    categoryCounts.ALL = totalUpdates;
    
    // Injected text
    elements.totalCount.textContent = totalUpdates;
    elements.lastSyncTime.textContent = formatDateTime(new Date().toISOString());
    
    // Setup Source status badge
    if (appData.cached) {
        elements.sourceStatus.textContent = "Offline Cache";
        elements.sourceStatus.className = "stat-value badge orange";
    } else {
        elements.sourceStatus.textContent = "Live Feed Connected";
        elements.sourceStatus.className = "stat-value badge green";
    }
    
    // Update count labels on pill buttons
    document.getElementById('count-all').textContent = categoryCounts.ALL;
    document.getElementById('count-feature').textContent = categoryCounts.Feature;
    document.getElementById('count-announcement').textContent = categoryCounts.Announcement;
    document.getElementById('count-issue').textContent = categoryCounts.Issue;
    document.getElementById('count-breaking').textContent = categoryCounts.Breaking;
    document.getElementById('count-change').textContent = categoryCounts.Change;
}

// Filter and render the timeline
function renderTimeline() {
    elements.timelineContainer.innerHTML = '';
    let matchesCount = 0;
    
    appData.entries.forEach(entry => {
        // Filter updates within this entry
        const matchedUpdates = entry.updates.filter(update => {
            // Check Category filter
            const categoryMatches = (currentCategoryFilter === "ALL" || update.type.toUpperCase() === currentCategoryFilter.toUpperCase());
            if (!categoryMatches) return false;
            
            // Check Search query
            if (searchQuery) {
                const textPool = (update.type + " " + update.content_text + " " + entry.date).toLowerCase();
                return textPool.includes(searchQuery);
            }
            
            return true;
        });
        
        if (matchedUpdates.length > 0) {
            matchesCount += matchedUpdates.length;
            
            // Create Date container group
            const groupDiv = document.createElement('div');
            groupDiv.className = 'timeline-group';
            
            // Header
            const headerDiv = document.createElement('div');
            headerDiv.className = 'timeline-date-header';
            headerDiv.innerHTML = `
                <div class="timeline-date-dot"></div>
                <h3 class="timeline-date-title">${entry.date}</h3>
            `;
            groupDiv.appendChild(headerDiv);
            
            // Render each card inside this date
            matchedUpdates.forEach(update => {
                const isSelected = selectedUpdate && 
                                   selectedUpdate.entry_id === entry.id && 
                                   selectedUpdate.content_text === update.content_text;
                
                const card = document.createElement('div');
                card.className = `update-card ${isSelected ? 'selected-for-tweet' : ''}`;
                
                // Card header row (category tag + select button)
                const headerRow = document.createElement('div');
                headerRow.className = 'card-header-row';
                
                const typeClass = `type-${update.type.toLowerCase()}`;
                const categoryTag = document.createElement('span');
                categoryTag.className = `category-tag ${typeClass}`;
                categoryTag.textContent = update.type;
                
                const selectBtn = document.createElement('button');
                selectBtn.className = 'select-tweet-btn';
                selectBtn.innerHTML = isSelected 
                    ? `Selected <svg viewBox="0 0 20 20" fill="currentColor" class="btn-icon"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" /></svg>` 
                    : `Select to Tweet`;
                
                selectBtn.addEventListener('click', () => {
                    selectUpdateForTweet(entry, update, card);
                });
                
                headerRow.appendChild(categoryTag);
                headerRow.appendChild(selectBtn);
                card.appendChild(headerRow);
                
                // Body text (HTML rendered)
                const bodyDiv = document.createElement('div');
                bodyDiv.className = 'card-body-content';
                bodyDiv.innerHTML = update.content_html;
                
                // Add target="_blank" to all links inside the body content for safety
                bodyDiv.querySelectorAll('a').forEach(link => {
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                });
                
                card.appendChild(bodyDiv);
                groupDiv.appendChild(card);
            });
            
            elements.timelineContainer.appendChild(groupDiv);
        }
    });
    
    // Manage empty states
    if (matchesCount === 0) {
        elements.feedEmpty.style.display = 'flex';
        elements.timelineContainer.style.display = 'none';
    } else {
        elements.feedEmpty.style.display = 'none';
        elements.timelineContainer.style.display = 'flex';
    }
}

// Manage Tweet selection
function selectUpdateForTweet(entry, update, cardElement) {
    const isCurrentlySelected = selectedUpdate && 
                                 selectedUpdate.entry_id === entry.id && 
                                 selectedUpdate.content_text === update.content_text;
                                 
    // Deselect all cards first in the DOM
    document.querySelectorAll('.update-card').forEach(card => {
        card.classList.remove('selected-for-tweet');
        const btn = card.querySelector('.select-tweet-btn');
        if (btn) btn.innerHTML = 'Select to Tweet';
    });
    
    if (isCurrentlySelected) {
        // Deselect
        selectedUpdate = null;
        elements.composerPrompt.style.display = 'flex';
        elements.composerInterface.style.display = 'none';
    } else {
        // Select
        selectedUpdate = {
            entry_id: entry.id,
            date: entry.date,
            link: entry.link,
            type: update.type,
            content_text: update.content_text
        };
        
        cardElement.classList.add('selected-for-tweet');
        const btn = cardElement.querySelector('.select-tweet-btn');
        if (btn) btn.innerHTML = `Selected <svg viewBox="0 0 20 20" fill="currentColor" class="btn-icon"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" /></svg>`;
        
        elements.composerPrompt.style.display = 'none';
        elements.composerInterface.style.display = 'flex';
        
        // Hydrate composer details
        elements.tweetDate.textContent = entry.date;
        elements.tweetCategory.textContent = update.type;
        elements.tweetCategory.className = `value badge type-${update.type.toLowerCase()}`;
        elements.tweetReleaseLink.href = entry.link;
        
        // Generate initial tweet draft
        generateTweetDraft();
    }
}

// Auto-generates a neat starting text for the tweet draft
function generateTweetDraft() {
    if (!selectedUpdate) return;
    
    const maxDraftChars = 200; // Leave some space for padding and links
    let cleanedText = selectedUpdate.content_text
        .replace(/\s+/g, ' ') // collapse whitespaces
        .trim();
        
    if (cleanedText.length > maxDraftChars) {
        cleanedText = cleanedText.slice(0, maxDraftChars - 3) + "...";
    }
    
    const draftText = `Google Cloud BigQuery Update 🚀\n\n[${selectedUpdate.type}] ${cleanedText}\n\nRead details here: ${selectedUpdate.link}`;
    elements.tweetTextarea.value = draftText;
    updateCharCount();
}

// Calculate tweet character length using Twitter's URL count rule (any URL counts as 23 chars)
function calculateTweetLength(text) {
    const urlRegex = /https?:\/\/[^\s]+/g;
    let length = text.length;
    const matches = text.match(urlRegex);
    if (matches) {
        for (const url of matches) {
            length = length - url.length + 23;
        }
    }
    return length;
}

// Update character count stats and progress UI
function updateCharCount() {
    const text = elements.tweetTextarea.value;
    const tweetLength = calculateTweetLength(text);
    
    elements.charCounter.textContent = `${tweetLength} / 280`;
    
    // Calculate progress percentage
    const pct = Math.min((tweetLength / 280) * 100, 100);
    elements.charProgress.style.width = `${pct}%`;
    
    // Color warnings based on length
    if (tweetLength > 280) {
        elements.charProgress.className = 'progress-bar danger';
        elements.charCounter.className = 'char-counter danger';
        elements.tweetIntentBtn.disabled = true;
        elements.tweetIntentBtn.style.opacity = '0.5';
        elements.tweetIntentBtn.style.cursor = 'not-allowed';
    } else if (tweetLength > 250) {
        elements.charProgress.className = 'progress-bar warning';
        elements.charCounter.className = 'char-counter warning';
        elements.tweetIntentBtn.disabled = false;
        elements.tweetIntentBtn.style.opacity = '1';
        elements.tweetIntentBtn.style.cursor = 'pointer';
    } else {
        elements.charProgress.className = 'progress-bar';
        elements.charCounter.className = 'char-counter';
        elements.tweetIntentBtn.disabled = false;
        elements.tweetIntentBtn.style.opacity = '1';
        elements.tweetIntentBtn.style.cursor = 'pointer';
    }
}

// Shows visual toast notification
function showToast(message, isError = false) {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${isError ? 'error' : ''} show`;
    
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3500);
}

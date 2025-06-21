/**
 * Utility functions for handling AJAX requests in the eStore application.
 * This module provides reusable functions for wishlist and comparison features.
 */

/**
 * Retrieves the CSRF token from cookies for secure AJAX POST requests.
 * @returns {string} The CSRF token value.
 */
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

/**
 * Toggles the wishlist status for a product.
 * @param {HTMLElement} button - The wishlist button element.
 * @param {string} productId - The ID of the product to add/remove from wishlist.
 * @param {boolean} isInWishlist - Current wishlist status of the product.
 * @returns {Promise<Object>} The response data from the server.
 */
export function toggleWishlist(button, productId, isInWishlist) {
    const url = isInWishlist ? `/accounts/wishlist/remove-ajax/${productId}/` : `/accounts/wishlist/add/${productId}/`;
    const icon = button.querySelector('.wishlist-icon');
    const wishlistText = button.querySelector('.wishlist-text');
    
    return fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'added' || data.status === 'exists') {
            button.classList.add('added');
            button.setAttribute('data-in-wishlist', 'true');
            if (icon) {
                icon.textContent = '';
                icon.style.display = 'none';
                icon.classList.add('animate');
                setTimeout(() => {
                    icon.classList.remove('animate');
                }, 1000);
            }
            if (wishlistText) {
                wishlistText.textContent = 'Remove from Wishlist';
            }
        } else if (data.status === 'removed') {
            button.classList.remove('added');
            button.setAttribute('data-in-wishlist', 'false');
            if (icon) {
                icon.textContent = '❤️';
                icon.style.display = 'none';
                icon.classList.add('animate');
                setTimeout(() => {
                    icon.classList.remove('animate');
                }, 1000);
            }
            if (wishlistText) {
                wishlistText.textContent = 'Add to Wishlist';
            }
        }
        return data;
    })
    .catch(error => {
        console.error('Error toggling wishlist:', error);
        alert('An error occurred while updating your wishlist. Please try again.');
        throw error;
    });
}

/**
 * Adds a product to the comparison list.
 * @param {HTMLElement} button - The compare button element.
 * @param {string} productId - The ID of the product to add to comparison.
 * @param {string} baseUrl - The base URL for the comparison endpoint.
 * @returns {Promise<Object>} The response data from the server.
 */
export function addToComparison(button, productId, baseUrl) {
    const url = `${baseUrl}${productId}/`;
    return fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (button) {
                button.textContent = 'In Comparison';
                button.disabled = true;
            }
            alert(data.message);
        } else {
            alert(data.message);
        }
        return data;
    })
    .catch(error => {
        console.error('Error adding to comparison:', error);
        alert('An error occurred while adding to comparison. Please try again.');
        throw error;
    });
}

/**
 * Removes a product from the comparison list.
 * @param {HTMLElement} button - The remove button element.
 * @param {string} productId - The ID of the product to remove from comparison.
 * @param {string} baseUrl - The base URL for the removal endpoint.
 * @returns {Promise<Object>} The response data from the server.
 */
export function removeFromComparison(button, productId, baseUrl) {
    const url = `${baseUrl}${productId}/`;
    return fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.reload(); // Reload to update the comparison table
        } else {
            alert(data.message);
        }
        return data;
    })
    .catch(error => {
        console.error('Error removing from comparison:', error);
        alert('An error occurred while removing from comparison. Please try again.');
        throw error;
    });
}

/**
 * Clears all products from the comparison list.
 * @param {HTMLElement} button - The clear button element.
 * @param {string} baseUrl - The base URL for the clear endpoint.
 * @returns {Promise<Object>} The response data from the server.
 */
export function clearComparison(button, baseUrl) {
    const url = baseUrl;
    return fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.reload(); // Reload to show empty state
        } else {
            alert(data.message);
        }
        return data;
    })
    .catch(error => {
        console.error('Error clearing comparison:', error);
        alert('An error occurred while clearing comparison. Please try again.');
        throw error;
    });
}

/**
 * ajax_ecommerce.js
 * AJAX enhancements for Sumia e-commerce.
 * Provides progressive-enhancement AJAX for cart, wishlist, and search
 * actions so the page does not reload on state changes.
 */

(function () {
    "use strict";

    var config = window.SumiaAJAX || {};
    var loadingOverlay = document.getElementById('loading-overlay');

    /* ============================================================
     * CSRF helpers
     * ============================================================ */

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            var cookies = document.cookie.split(";");
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Wrapper around fetch that automatically attaches CSRF + X-Requested-With
     * headers and parses JSON responses, throwing on HTTP errors.
     */
    function requestJSON(url, options) {
        options = options || {};
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
        var opts = {
            method: options.method || "GET",
            credentials: "same-origin",
            headers: {},
        };

        if (options.body instanceof FormData) {
            opts.body = options.body;
        } else if (options.body != null) {
            opts.body = options.body;
            opts.headers["Content-Type"] = "application/x-www-form-urlencoded";
        }

        opts.headers["X-CSRFToken"] = getCookie("csrftoken");
        opts.headers["X-Requested-With"] = "XMLHttpRequest";

        return fetch(url, opts).then(function (response) {
            var contentType = response.headers.get("content-type") || "";
            if (contentType.indexOf("application/json") === -1) {
                throw { message: "Server error: " + response.status };
            }
            return response.json().then(function (data) {
                if (!response.ok) {
                    throw data || { message: "Request failed" };
                }
                return data;
            });
        }).finally(function () {
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        });
    }

    /* ============================================================
     * Toast notifications
     * ============================================================ */

    function ensureToastContainer() {
        var container = document.getElementById("ajaxToastContainer");
        if (!container) {
            container = document.createElement("div");
            container.id = "ajaxToastContainer";
            container.className = "position-fixed bottom-0 end-0 p-3";
            container.style.zIndex = "2080";
            document.body.appendChild(container);
        }
        return container;
    }

    function showToast(message, type, duration) {
        type = type || "success";
        duration = duration || 4000;

        var container = ensureToastContainer();
        var bgMap = {
            success: "bg-success",
            error: "bg-danger",
            info: "bg-info",
            warning: "bg-warning",
        };
        var bgClass = bgMap[type] || "bg-primary";
        var textColor = type === "warning" ? "text-dark" : "text-white";

        var toastEl = document.createElement("div");
        toastEl.className =
            "toast align-items-center " + bgClass + " border-0 " + textColor;
        toastEl.setAttribute("role", "alert");
        toastEl.setAttribute("aria-live", "assertive");
        toastEl.setAttribute("aria-atomic", "true");

        toastEl.innerHTML =
            '<div class="d-flex">' +
            '<div class="toast-body">' +
            message +
            "</div>" +
            '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
            "</div>";

        container.appendChild(toastEl);

        if (window.bootstrap && window.bootstrap.Toast) {
            var bsToast = new bootstrap.Toast(toastEl, {
                delay: duration,
                autostart: false,
            });
            bsToast.show();
            toastEl.addEventListener("hidden.bs.toast", function () {
                if (toastEl.parentNode) {
                    toastEl.parentNode.removeChild(toastEl);
                }
            });
        } else {
            setTimeout(function () {
                if (toastEl.parentNode) {
                    toastEl.parentNode.removeChild(toastEl);
                }
            }, duration);
        }
    }

    /* ============================================================
     * Cart count badge
     * ============================================================ */

    function updateCartCount(count) {
        var badge = document.querySelector(".cart-count-badge");
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? "inline-block" : "none";
        }
    }

    function updateWishlistCount(count) {
        var badge = document.querySelector(".wishlist-count-badge");
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? "inline-block" : "none";
        }
    }

    function refreshCartCount() {
        requestJSON(config.cartCountUrl)
            .then(function (data) {
                updateCartCount(data.cart_count);
            })
            .catch(function () {});
    }

    /* ============================================================
     * Add to Cart
     * ============================================================ */

    function initAddToCart() {
        var forms = document.querySelectorAll(".ajax-add-to-cart");
        for (var i = 0; i < forms.length; i++) {
            (function (form) {
                form.addEventListener("submit", function (e) {
                    e.preventDefault();

                    var url =
                        form.getAttribute("data-ajax-url") || form.action;
                    var formData = new FormData(form);

                    requestJSON(url, { method: "POST", body: formData })
                        .then(function (data) {
                            updateCartCount(data.cart_count);
                            if (data.cart_total != null) {
                                var totalEl = document.querySelector(
                                    ".cart-total-display"
                                );
                                if (totalEl) {
                                    totalEl.textContent =
                                        "₦" + formatNumber(data.cart_total);
                                }
                            }
                            showToast(data.message, "success");
                        })
                        .catch(function (err) {
                            showToast(
                                (err && err.message) ||
                                    "Could not add to cart.",
                                "error"
                            );
                        });
                });
            })(forms[i]);
        }
    }

    /* ============================================================
     * Remove from Cart
     * ============================================================ */

    function initRemoveFromCart() {
        var forms = document.querySelectorAll(".ajax-remove-from-cart");
        for (var i = 0; i < forms.length; i++) {
            (function (form) {
                form.addEventListener("submit", function (e) {
                    e.preventDefault();

                    var url = form.getAttribute("data-ajax-url");
                    var formData = new FormData(form);

                    requestJSON(url, { method: "POST", body: formData })
                        .then(function (data) {
                            updateCartCount(data.cart_count);

                            var totalEl = document.querySelector(
                                ".cart-total-display"
                            );
                            if (totalEl) {
                                totalEl.textContent =
                                    "₦" + formatNumber(data.cart_total);
                            }

                            var itemRow = form.closest(".cart-item-row");
                            if (itemRow) {
                                itemRow.parentNode.removeChild(itemRow);
                            }

                            if (data.cart_empty) {
                                var tableWrap = document.querySelector(
                                    ".cart-table-wrap"
                                );
                                if (tableWrap) {
                                    tableWrap.innerHTML =
                                        '<div class="text-center py-5">' +
                                        '<img src="https://illustrations.popsy.co/gray/empty-cart.svg" alt="Empty Cart" class="mb-4" style="max-width:300px;">' +
                                        "<h4 class=\"fw-bold\">Your Cart is Empty</h4>" +
                                        "<p class=\"text-muted\">Add items you love and they'll appear here.</p>" +
                                        '<a href="' +
                                        window.location.origin +
                                        '" class="btn btn-primary rounded-pill px-4 mt-3">Start Shopping</a>' +
                                        "</div>";
                                }
                                var summary = document.querySelector(
                                    ".cart-summary-wrap"
                                );
                                if (summary) {
                                    summary.style.display = "none";
                                }
                            }

                            showToast(data.message, "success");
                        })
                        .catch(function (err) {
                            showToast(
                                (err && err.message) ||
                                    "Could not remove item.",
                                "error"
                            );
                        });
                });
            })(forms[i]);
        }
    }

    /* ============================================================
     * Update Cart Quantity
     * ============================================================ */

    function initUpdateCartQuantity() {
        var forms = document.querySelectorAll(".ajax-update-cart");
        for (var i = 0; i < forms.length; i++) {
            (function (form) {
                form.addEventListener("submit", function (e) {
                    e.preventDefault();

                    var url = form.getAttribute("data-ajax-url");
                    var formData = new FormData(form);
                    var row = form.closest(".cart-item-row");

                    requestJSON(url, { method: "POST", body: formData })
                        .then(function (data) {
                            var subtotalEl = row
                                ? row.querySelector(".item-subtotal")
                                : null;
                            if (subtotalEl) {
                                subtotalEl.textContent =
                                    "₦" + formatNumber(data.item_subtotal);
                            }

                            var totalEl = document.querySelector(
                                ".cart-total-display"
                            );
                            if (totalEl) {
                                totalEl.textContent =
                                    "₦" + formatNumber(data.cart_total);
                            }

                            updateCartCount(data.cart_count);
                            showToast(data.message, "success");
                        })
                        .catch(function (err) {
                            showToast(
                                (err && err.message) ||
                                    "Could not update quantity.",
                                "error"
                            );
                        });
                });
            })(forms[i]);
        }
    }

    /* ============================================================
     * Wishlist toggle (add)
     * ============================================================ */

    function initWishlistToggle() {
        var links = document.querySelectorAll(".ajax-add-to-wishlist");
        for (var i = 0; i < links.length; i++) {
            (function (link) {
                link.addEventListener("click", function (e) {
                    e.preventDefault();

                    var url = link.getAttribute("data-ajax-url");
                    var formData = new FormData();

                    requestJSON(url, { method: "POST", body: formData })
                        .then(function (data) {
                            if (data.in_wishlist) {
                                link.classList.add("active");
                                link.classList.add("text-danger");
                                var icon = link.querySelector("i");
                                if (icon) {
                                    icon.className = "fas fa-heart";
                                }
                                link.setAttribute("title", "Remove from Wishlist");
                            }
                            if (data.wishlist_count != null) {
                                updateWishlistCount(data.wishlist_count);
                            }
                            showToast(data.message, data.status || "success");
                        })
                        .catch(function (err) {
                            showToast(
                                (err && err.message) ||
                                    "Could not update wishlist.",
                                "error"
                            );
                        });
                });
            })(links[i]);
        }
    }

    /* ============================================================
     * Wishlist remove (on the wishlist page)
     * ============================================================ */

    function initWishlistRemove() {
        var forms = document.querySelectorAll(".ajax-remove-from-wishlist");
        for (var i = 0; i < forms.length; i++) {
            (function (form) {
                form.addEventListener("submit", function (e) {
                    e.preventDefault();

                    var url = form.getAttribute("data-ajax-url");
                    var formData = new FormData(form);

                    requestJSON(url, { method: "POST", body: formData })
                        .then(function (data) {
                            var card = form.closest(".wishlist-item");
                            if (card) {
                                card.parentNode.removeChild(card);
                            }

                            var remaining = document.querySelectorAll(
                                ".wishlist-item"
                            );
                            if (remaining.length === 0) {
                                var wrap = document.querySelector(
                                    ".wishlist-items-wrap"
                                );
                                if (wrap) {
                                    wrap.innerHTML =
                                        '<div class="text-center py-5">' +
                                        '<img src="https://illustrations.popsy.co/gray/empty-cart.svg" alt="Empty Wishlist" class="mb-4" style="max-width:300px;">' +
                                        "<h4 class=\"fw-bold text-dark mb-2\">Your Wishlist is Empty</h4>" +
                                        "<p class=\"text-muted\">Start adding products you love and save them for later.</p>" +
                                        '<a href="' +
                                        window.location.origin +
                                        '" class="btn btn-primary rounded-pill mt-3 px-4">Start Shopping</a>' +
                                        "</div>";
                                }
                            }

                            if (data.wishlist_count != null) {
                                updateWishlistCount(data.wishlist_count);
                            }
                            showToast(data.message, "success");
                        })
                        .catch(function (err) {
                            showToast(
                                (err && err.message) ||
                                    "Could not remove from wishlist.",
                                "error"
                            );
                        });
                });
            })(forms[i]);
        }
    }

    /* ============================================================
     * Live search
     * ============================================================ */

    function highlightMatch(text, query) {
        if (!query || !text) return escapeHtml(text || "");
        var terms = query.trim().split(/\s+/).filter(function(t) { return t.length >= 2; });
        if (terms.length === 0) return escapeHtml(text);
        var escapedTerms = terms.map(function(t) { return t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
        var regex = new RegExp('(' + escapedTerms.join('|') + ')', 'gi');
        return escapeHtml(text).replace(regex, '<mark class="sumia-search-highlight">$1</mark>');
    }

    function initLiveSearch() {
        var searchInput = document.querySelector(".ajax-search-input");
        if (!searchInput) return;

        var searchForm = searchInput.closest("form");
        var categorySelect = searchForm
            ? searchForm.querySelector('select[name="category"]')
            : null;

        /* Create dropdown container */
        var dropdown = document.createElement("div");
        dropdown.className =
            "ajax-search-dropdown position-absolute w-100 shadow-lg";
        dropdown.style.display = "none";
        dropdown.style.zIndex = "1050";
        dropdown.style.maxHeight = "440px";
        dropdown.style.overflowY = "auto";
        dropdown.innerHTML = "";
        searchInput.parentNode.appendChild(dropdown);

        var activeIndex = -1;

        function updateActiveItem(items) {
            for (var i = 0; i < items.length; i++) {
                if (i === activeIndex) {
                    items[i].classList.add("active");
                    items[i].scrollIntoView({ block: "nearest" });
                } else {
                    items[i].classList.remove("active");
                }
            }
        }

        /* Keyboard navigation for suggestions */
        searchInput.addEventListener("keydown", function (e) {
            var items = dropdown.querySelectorAll(".sumia-search-item");
            if (!items.length || dropdown.style.display === "none") return;

            if (e.key === "ArrowDown") {
                e.preventDefault();
                activeIndex = (activeIndex + 1) % items.length;
                updateActiveItem(items);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                activeIndex = (activeIndex - 1 + items.length) % items.length;
                updateActiveItem(items);
            } else if (e.key === "Enter" && activeIndex >= 0) {
                e.preventDefault();
                items[activeIndex].click();
            } else if (e.key === "Escape") {
                dropdown.style.display = "none";
            }
        });

        searchInput.addEventListener("input", function () {
            clearTimeout(searchInput._debounceTimer);
            var q = searchInput.value.trim();
            activeIndex = -1;

            if (q.length < 2) {
                dropdown.style.display = "none";
                dropdown.innerHTML = "";
                return;
            }

            searchInput._debounceTimer = setTimeout(function () {
                var params = "q=" + encodeURIComponent(q);
                if (categorySelect && categorySelect.value) {
                    params +=
                        "&category=" +
                        encodeURIComponent(categorySelect.value);
                }
                var url = config.searchUrl + "?" + params;

                requestJSON(url)
                    .then(function (data) {
                        var results = data.results || [];
                        var html = "";
                        if (results.length === 0) {
                            html =
                                '<div class="p-4 text-center text-muted">' +
                                '<i class="fas fa-search fa-2x mb-2 opacity-50"></i>' +
                                '<div class="small fw-semibold">No products found for "' +
                                escapeHtml(q) +
                                '"</div>' +
                                '<div class="small text-muted mt-1">Try checking for typos or searching with different keywords.</div>' +
                                '</div>';
                        } else {
                            html += '<div class="sumia-search-results-list">';
                            for (var i = 0; i < results.length; i++) {
                                var p = results[i];
                                var imgHtml;
                                if (p.image_url) {
                                    imgHtml =
                                        '<div class="sumia-search-thumb-wrap me-3">' +
                                        '<img src="' + p.image_url + '" alt="' + escapeHtml(p.name) + '">' +
                                        '</div>';
                                } else {
                                    imgHtml =
                                        '<div class="sumia-search-thumb-wrap me-3">' +
                                        '<i class="fas fa-image text-muted opacity-50"></i>' +
                                        '</div>';
                                }

                                var priceHtml;
                                if (p.discount_price) {
                                    priceHtml =
                                        '<span class="text-danger fw-bold">₦' +
                                        formatNumber(p.discount_price) +
                                        '</span> <del class="text-muted small ms-1">₦' +
                                        formatNumber(p.price) +
                                        '</del>';
                                    if (p.discount_percent) {
                                        priceHtml +=
                                            ' <span class="badge bg-danger bg-opacity-10 text-danger rounded-pill small ms-1">-' +
                                            p.discount_percent +
                                            '%</span>';
                                    }
                                } else {
                                    priceHtml =
                                        '<span class="fw-bold">₦' +
                                        formatNumber(p.price) +
                                        '</span>';
                                }

                                var badgeHtml = '';
                                if (p.category_name) {
                                    badgeHtml = '<span class="badge sumia-search-cat-badge me-2">' + escapeHtml(p.category_name) + '</span>';
                                }

                                html +=
                                    '<a href="' +
                                    p.detail_url +
                                    '" class="sumia-search-item" data-index="' + i + '">' +
                                    imgHtml +
                                    '<div class="flex-grow-1 min-w-0">' +
                                    '<div class="d-flex align-items-center mb-1">' +
                                    badgeHtml +
                                    (p.brand_name ? '<span class="text-muted small">' + escapeHtml(p.brand_name) + '</span>' : '') +
                                    '</div>' +
                                    '<div class="sumia-search-title text-truncate">' +
                                    highlightMatch(p.name, q) +
                                    '</div>' +
                                    '<div class="small mt-1">' +
                                    priceHtml +
                                    '</div>' +
                                    '</div>' +
                                    '<i class="fas fa-chevron-right text-muted opacity-50 ms-2 small"></i>' +
                                    '</a>';
                            }
                            html += '</div>';

                            /* View all results footer */
                            var total = data.total || results.length;
                            var viewAllUrl = (searchForm ? searchForm.action : "") + "?q=" + encodeURIComponent(q);
                            if (categorySelect && categorySelect.value) {
                                viewAllUrl += "&category=" + encodeURIComponent(categorySelect.value);
                            }
                            html +=
                                '<a href="' +
                                viewAllUrl +
                                '" class="sumia-search-footer">' +
                                '<span><i class="fas fa-magnifying-glass me-2"></i> View all <strong>' + total + '</strong> result' + (total === 1 ? '' : 's') + '</span>' +
                                '<i class="fas fa-arrow-right"></i>' +
                                '</a>';
                        }
                        dropdown.innerHTML = html;
                        dropdown.style.display = "block";
                    })
                    .catch(function () {
                        dropdown.style.display = "none";
                    });
            }, 250);
        });

        /* Re-open on focus if query present */
        searchInput.addEventListener("focus", function () {
            if (searchInput.value.trim().length >= 2 && dropdown.innerHTML.trim().length > 0) {
                dropdown.style.display = "block";
            }
        });

        /* Hide dropdown when clicking outside */
        document.addEventListener("click", function (e) {
            if (
                !searchInput.contains(e.target) &&
                !dropdown.contains(e.target)
            ) {
                dropdown.style.display = "none";
            }
        });

        /* Allow normal form submit for Enter key (full search page) */
        if (searchForm) {
            searchForm.addEventListener("submit", function () {
                dropdown.style.display = "none";
            });
        }
    }

    /* ============================================================
     * Utility
     * ============================================================ */

    function formatNumber(str) {
        /* Insert comma thousands separators for numeric display strings */
        if (!str) return "0";
        var parts = str.split(".");
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        return parts.join(".");
    }

    function escapeHtml(text) {
        var div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    /* ============================================================
     * Init
     * ============================================================ */

    document.addEventListener("DOMContentLoaded", function () {
        refreshCartCount();
        initAddToCart();
        initRemoveFromCart();
        initUpdateCartQuantity();
        initWishlistToggle();
        initWishlistRemove();
        initLiveSearch();
    });
})();

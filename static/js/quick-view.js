// Quick View Modal Controller
document.addEventListener('DOMContentLoaded', function () {
  const modalEl = document.getElementById('quickViewModal');
  if (!modalEl) return;

  const bsModal = new bootstrap.Modal(modalEl);
  const qvImage = document.getElementById('qv-image');
  const qvName = document.getElementById('qv-name');
  const qvCategory = document.getElementById('qv-category');
  const qvBrand = document.getElementById('qv-brand');
  const qvPrice = document.getElementById('qv-price');
  const qvOriginalPrice = document.getElementById('qv-original-price');
  const qvDiscountBadge = document.getElementById('qv-discount-badge');
  const qvStock = document.getElementById('qv-stock');
  const qvDescription = document.getElementById('qv-description');
  const qvCartForm = document.getElementById('qv-cart-form');
  const qvAddBtn = document.getElementById('qv-add-btn');
  const qvViewDetails = document.getElementById('qv-view-details');

  document.body.addEventListener('click', function (e) {
    const trigger = e.target.closest('.ajax-quick-view-btn');
    if (!trigger) return;

    e.preventDefault();
    const url = trigger.getAttribute('data-quickview-url');
    if (!url) return;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          qvName.textContent = data.name;
          qvCategory.textContent = data.category;
          qvBrand.textContent = data.brand || 'Sumia Direct';
          qvDescription.textContent = data.description;
          qvViewDetails.setAttribute('href', data.detail_url);

          if (data.image_url) {
            qvImage.src = data.image_url;
            qvImage.alt = data.name;
          } else {
            qvImage.src = 'https://placehold.co/400x300/f8fafc/64748b?text=No+Image';
          }

          if (data.discount_price) {
            qvPrice.textContent = '₦' + data.discount_price;
            qvOriginalPrice.textContent = '₦' + data.price;
            qvOriginalPrice.style.display = 'inline';
            qvDiscountBadge.textContent = '-' + data.discount_percent + '% OFF';
            qvDiscountBadge.style.display = 'inline-block';
          } else {
            qvPrice.textContent = '₦' + data.price;
            qvOriginalPrice.style.display = 'none';
            qvDiscountBadge.style.display = 'none';
          }

          if (data.is_available) {
            qvStock.className = 'badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-2 py-1 rounded-pill small';
            qvStock.textContent = 'In Stock (' + data.stock_quantity + ' units)';
            qvAddBtn.disabled = false;
            qvCartForm.setAttribute('action', data.add_to_cart_url);
            qvCartForm.setAttribute('data-ajax-url', data.add_to_cart_url);
            qvCartForm.className = 'ajax-add-to-cart flex-grow-1';
          } else {
            qvStock.className = 'badge bg-danger bg-opacity-10 text-danger border border-danger border-opacity-25 px-2 py-1 rounded-pill small';
            qvStock.textContent = 'Out of Stock';
            qvAddBtn.disabled = true;
          }

          bsModal.show();
        }
      })
      .catch(err => console.error('Quick view failed:', err));
  });
});

"""Service layer for product image gallery management."""
from django.db import transaction
from pages.models import ProductImage


def add_product_images(product, images, alt_texts=None):
    """Add multiple images to a product."""
    if alt_texts is None:
        alt_texts = [''] * len(images)

    with transaction.atomic():
        current_count = product.gallery_images.count()
        created = []
        for i, (image, alt_text) in enumerate(zip(images, alt_texts)):
            img = ProductImage.objects.create(
                product=product,
                image=image,
                alt_text=alt_text,
                sort_order=current_count + i,
                is_primary=(current_count == 0 and i == 0),
            )
            created.append(img)
    return created


def reorder_images(product, image_ids):
    """Reorder gallery images by providing ordered list of IDs."""
    with transaction.atomic():
        for index, image_id in enumerate(image_ids):
            ProductImage.objects.filter(
                id=image_id, product=product
            ).update(sort_order=index)


def set_primary_image(product, image_id):
    """Set a gallery image as primary."""
    with transaction.atomic():
        ProductImage.objects.filter(product=product).update(is_primary=False)
        ProductImage.objects.filter(id=image_id, product=product).update(is_primary=True)

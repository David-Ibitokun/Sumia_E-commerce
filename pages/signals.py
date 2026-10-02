"""Cache invalidation for the navigation category tree."""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .context_processors import invalidate_category_tree
from .models import Category


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def clear_category_tree(sender, **kwargs):
    """Rebuild the cached category tree after any category change."""
    invalidate_category_tree()

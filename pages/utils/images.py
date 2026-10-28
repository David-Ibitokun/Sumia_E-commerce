"""Utility functions for image processing and optimization."""
import io
import os
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


def convert_image_to_webp(image_file, max_dimension=1600, quality=85):
    """
    Convert an uploaded image to WebP format to save storage and bandwidth.
    
    Args:
        image_file: Django FieldFile, UploadedFile, or file-like object.
        max_dimension: Maximum width/height in pixels (preserves aspect ratio).
        quality: WebP compression quality (1-100).
        
    Returns:
        ContentFile containing the WebP image data, or original file if already WebP or invalid.
    """
    if not image_file:
        return image_file

    filename = getattr(image_file, 'name', '') or 'image'
    base_name, ext = os.path.splitext(filename)
    
    # If already webp and reasonably sized, return as is
    if ext.lower() == '.webp':
        return image_file

    try:
        # Seek to start if file was read previously
        if hasattr(image_file, 'seek') and callable(image_file.seek):
            image_file.seek(0)

        # Open image with Pillow
        img = Image.open(image_file)

        # Transpose according to EXIF orientation (handles phone camera rotation)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Handle color modes
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Preserve transparency
            img = img.convert('RGBA')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if dimensions exceed max_dimension
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save as WebP into a BytesIO buffer
        output = io.BytesIO()
        img.save(output, format='WEBP', quality=quality, method=6)
        output.seek(0)

        # Generate clean new filename with .webp extension
        clean_base = base_name.split('/')[-1].split('\\')[-1]
        new_filename = f"{clean_base}.webp"

        return ContentFile(output.getvalue(), name=new_filename)

    except Exception:
        # If conversion fails (e.g. corrupted file, non-image), fallback to original file
        if hasattr(image_file, 'seek') and callable(image_file.seek):
            image_file.seek(0)
        return image_file

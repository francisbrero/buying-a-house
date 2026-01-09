"""Image composite service for creating grid images from listing photos."""

import asyncio
import math
from io import BytesIO

import httpx
from PIL import Image


async def fetch_image(client: httpx.AsyncClient, url: str) -> Image.Image | None:
    """Fetch a single image from URL."""
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception:
        return None


async def fetch_images(urls: list[str], max_concurrent: int = 10) -> list[Image.Image]:
    """Fetch multiple images concurrently."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(url: str) -> Image.Image | None:
            async with semaphore:
                return await fetch_image(client, url)

        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)

    return [img for img in results if img is not None]


def calculate_grid_dimensions(num_images: int, max_cols: int = 5) -> tuple[int, int]:
    """Calculate optimal grid dimensions for n images.

    Returns (cols, rows) tuple.
    """
    if num_images == 0:
        return (0, 0)
    if num_images <= 2:
        return (num_images, 1)
    if num_images <= 4:
        return (2, 2)
    if num_images <= 6:
        return (3, 2)
    if num_images <= 9:
        return (3, 3)

    # For larger numbers, aim for roughly square grid
    cols = min(max_cols, math.ceil(math.sqrt(num_images)))
    rows = math.ceil(num_images / cols)
    return (cols, rows)


def create_grid_image(
    images: list[Image.Image],
    cell_width: int = 400,
    cell_height: int = 300,
    padding: int = 2,
    bg_color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Create a grid composite from images."""
    if not images:
        return Image.new("RGB", (cell_width, cell_height), bg_color)

    cols, rows = calculate_grid_dimensions(len(images))

    # Calculate total dimensions
    total_width = cols * cell_width + (cols + 1) * padding
    total_height = rows * cell_height + (rows + 1) * padding

    # Create canvas
    canvas = Image.new("RGB", (total_width, total_height), bg_color)

    for idx, img in enumerate(images):
        if idx >= cols * rows:
            break

        row = idx // cols
        col = idx % cols

        # Resize image to fit cell while maintaining aspect ratio
        img_ratio = img.width / img.height
        cell_ratio = cell_width / cell_height

        if img_ratio > cell_ratio:
            # Image is wider, fit to width
            new_width = cell_width
            new_height = int(cell_width / img_ratio)
        else:
            # Image is taller, fit to height
            new_height = cell_height
            new_width = int(cell_height * img_ratio)

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to RGB if necessary
        if resized.mode != "RGB":
            resized = resized.convert("RGB")

        # Calculate position (centered in cell)
        x = padding + col * (cell_width + padding) + (cell_width - new_width) // 2
        y = padding + row * (cell_height + padding) + (cell_height - new_height) // 2

        canvas.paste(resized, (x, y))

    return canvas


async def create_composite(
    image_urls: list[str],
    cell_width: int = 400,
    cell_height: int = 300,
    max_images: int | None = None,
) -> bytes:
    """Create a composite grid image from URLs.

    Args:
        image_urls: List of image URLs to fetch
        cell_width: Width of each cell in pixels
        cell_height: Height of each cell in pixels
        max_images: Maximum number of images to include (None = no limit)

    Returns:
        PNG image bytes
    """
    # Limit number of images if specified
    urls = image_urls[:max_images] if max_images else image_urls

    # Fetch images
    images = await fetch_images(urls)

    if not images:
        # Create placeholder if no images fetched
        placeholder = Image.new("RGB", (cell_width, cell_height), (200, 200, 200))
        buffer = BytesIO()
        placeholder.save(buffer, format="PNG")
        return buffer.getvalue()

    # Create grid
    grid = create_grid_image(images, cell_width, cell_height)

    # Convert to bytes
    buffer = BytesIO()
    grid.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def create_composite_sync(
    image_urls: list[str],
    cell_width: int = 400,
    cell_height: int = 300,
    max_images: int | None = None,
) -> bytes:
    """Synchronous wrapper for create_composite."""
    return asyncio.run(create_composite(image_urls, cell_width, cell_height, max_images))

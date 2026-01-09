"""Geocoding service using Nominatim (OpenStreetMap)."""

import time
import urllib.parse
import urllib.request
import json
from typing import Tuple


# Rate limit: 1 request per second for Nominatim
_last_request_time = 0


def geocode_address(address: str) -> Tuple[float, float] | None:
    """
    Convert an address to latitude/longitude coordinates using Nominatim.

    Returns:
        Tuple of (latitude, longitude) or None if not found.
    """
    global _last_request_time

    # Rate limiting - wait at least 1 second between requests
    elapsed = time.time() - _last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    # Build the request URL
    encoded_address = urllib.parse.quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"

    # Make request with proper User-Agent (required by Nominatim)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HouseEvaluator/1.0 (home listing evaluator)"}
    )

    try:
        _last_request_time = time.time()
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return (lat, lon)
    except Exception as e:
        print(f"Geocoding error for '{address}': {e}")

    return None


def batch_geocode(addresses: list[str]) -> dict[str, Tuple[float, float]]:
    """
    Geocode multiple addresses.

    Returns:
        Dictionary mapping address to (lat, lon) tuple.
    """
    results = {}
    for address in addresses:
        coords = geocode_address(address)
        if coords:
            results[address] = coords
    return results

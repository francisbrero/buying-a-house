"""Generate HTML report of house evaluations."""

import html
import json
from datetime import datetime
from pathlib import Path

from src.storage import JsonStore


def html_escape_for_attr(text: str) -> str:
    """Escape text for use in HTML attribute, preserving newlines as escaped chars."""
    if not text:
        return ""
    # Escape HTML entities and encode newlines for data attribute
    escaped = html.escape(text, quote=True)
    # Replace newlines with a marker we can decode in JS
    escaped = escaped.replace("\n", "&#10;")
    return escaped


def generate_report() -> str:
    """Generate an HTML report of all scored houses."""
    store = JsonStore()
    houses = store.list_houses()

    # Sort by present_fit_score descending
    houses.sort(
        key=lambda h: h.present_fit_score.score if h.present_fit_score else 0,
        reverse=True
    )

    # Get houses with coordinates for the map
    houses_with_coords = [h for h in houses if h.latitude and h.longitude]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>House Evaluation Report</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-green: #22c55e;
            --accent-yellow: #eab308;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
            --accent-purple: #a855f7;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--bg-card);
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 3rem;
        }}

        .stat-card {{
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-blue);
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .houses {{
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}

        .house-card {{
            background: var(--bg-secondary);
            border-radius: 16px;
            overflow: hidden;
            display: grid;
            grid-template-columns: 300px 1fr;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .house-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}

        .house-image {{
            width: 300px;
            height: 250px;
            object-fit: cover;
            background: var(--bg-card);
        }}

        .house-content {{
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
        }}

        .house-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }}

        .house-address {{
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}

        .house-price {{
            font-size: 1.2rem;
            color: var(--accent-green);
            font-weight: 600;
        }}

        .house-features {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}

        .scores {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .score-badge {{
            display: flex;
            flex-direction: column;
            align-items: center;
            background: var(--bg-card);
            padding: 0.75rem 1.25rem;
            border-radius: 8px;
            min-width: 100px;
        }}

        .score-value {{
            font-size: 1.8rem;
            font-weight: 700;
        }}

        .score-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .score-high {{ color: var(--accent-green); }}
        .score-medium {{ color: var(--accent-yellow); }}
        .score-low {{ color: var(--accent-red); }}

        .justification {{
            background: var(--bg-card);
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            flex-grow: 1;
        }}

        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .tag {{
            background: var(--bg-card);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
        }}

        .tag-positive {{
            background: rgba(34, 197, 94, 0.2);
            color: var(--accent-green);
        }}

        .tag-negative {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--accent-red);
        }}

        .house-link {{
            display: inline-block;
            margin-top: 1rem;
            color: var(--accent-blue);
            text-decoration: none;
            font-size: 0.9rem;
        }}

        .house-link:hover {{
            text-decoration: underline;
        }}

        .brief-section {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--bg-card);
        }}

        .brief-toggle {{
            background: var(--bg-card);
            border: none;
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
        }}

        .brief-toggle:hover {{
            background: var(--bg-primary);
        }}

        .brief-content {{
            display: none;
            margin-top: 1rem;
            padding: 1.5rem;
            background: var(--bg-card);
            border-radius: 8px;
            font-size: 0.95rem;
            line-height: 1.7;
        }}

        .brief-content.show {{
            display: block;
        }}

        /* Markdown rendered content styles */
        .brief-content h1 {{
            font-size: 1.4rem;
            font-weight: 700;
            margin: 0 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--bg-secondary);
            color: var(--text-primary);
        }}

        .brief-content h2 {{
            font-size: 1.1rem;
            font-weight: 600;
            margin: 1.5rem 0 0.75rem 0;
            color: var(--accent-blue);
        }}

        .brief-content h3 {{
            font-size: 1rem;
            font-weight: 600;
            margin: 1rem 0 0.5rem 0;
            color: var(--text-primary);
        }}

        .brief-content p {{
            margin: 0.75rem 0;
            color: var(--text-secondary);
        }}

        .brief-content ul, .brief-content ol {{
            margin: 0.75rem 0;
            padding-left: 1.5rem;
            color: var(--text-secondary);
        }}

        .brief-content li {{
            margin: 0.4rem 0;
        }}

        .brief-content strong {{
            color: var(--text-primary);
            font-weight: 600;
        }}

        .brief-content em {{
            font-style: italic;
        }}

        .brief-content blockquote {{
            border-left: 3px solid var(--accent-purple);
            margin: 1rem 0;
            padding: 0.5rem 1rem;
            background: rgba(168, 85, 247, 0.1);
            border-radius: 0 8px 8px 0;
        }}

        .brief-content code {{
            background: var(--bg-secondary);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85em;
        }}

        .renovation-ideas {{
            margin-top: 1rem;
        }}

        .renovation-idea {{
            background: rgba(168, 85, 247, 0.1);
            border-left: 3px solid var(--accent-purple);
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 0 8px 8px 0;
        }}

        .renovation-area {{
            font-weight: 600;
            color: var(--accent-purple);
        }}

        .renovation-change {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--bg-card);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        /* Map styles */
        .map-section {{
            margin-bottom: 3rem;
        }}

        .map-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .map-title {{
            font-size: 1.5rem;
            font-weight: 600;
        }}

        .map-toggle {{
            background: var(--bg-secondary);
            border: 1px solid var(--bg-card);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.2s;
        }}

        .map-toggle:hover {{
            background: var(--bg-card);
        }}

        #map {{
            height: 500px;
            border-radius: 12px;
            z-index: 1;
        }}

        .map-container.collapsed #map {{
            display: none;
        }}

        .leaflet-popup-content {{
            margin: 8px 12px;
        }}

        .popup-address {{
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 4px;
        }}

        .popup-price {{
            color: #22c55e;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .popup-scores {{
            font-size: 0.85rem;
            color: #666;
        }}

        .popup-link {{
            display: block;
            margin-top: 8px;
            color: #3b82f6;
            text-decoration: none;
            font-size: 0.85rem;
        }}

        .popup-link:hover {{
            text-decoration: underline;
        }}

        @media (max-width: 768px) {{
            .house-card {{
                grid-template-columns: 1fr;
            }}

            .house-image {{
                width: 100%;
                height: 200px;
            }}

            #map {{
                height: 350px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>House Evaluation Report</h1>
            <p class="subtitle">Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </header>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">{len(houses)}</div>
                <div class="stat-label">Houses Evaluated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([h for h in houses if h.present_fit_score and h.present_fit_score.score >= 70])}</div>
                <div class="stat-label">Strong Matches (70+)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${min(h.price for h in houses if h.price) / 1000:.0f}k - ${max(h.price for h in houses if h.price) / 1000:.0f}k</div>
                <div class="stat-label">Price Range</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([h for h in houses if h.potential_score and h.potential_score.score >= 80])}</div>
                <div class="stat-label">High Potential (80+)</div>
            </div>
        </div>

        {"" if not houses_with_coords else f'''
        <div class="map-section">
            <div class="map-header">
                <span class="map-title">📍 Map View ({len(houses_with_coords)} locations)</span>
                <button class="map-toggle" onclick="toggleMap()">Hide Map</button>
            </div>
            <div class="map-container" id="map-container">
                <div id="map"></div>
            </div>
        </div>
        '''}

        <div class="houses">
"""

    for i, house in enumerate(houses):
        fit_score = house.present_fit_score.score if house.present_fit_score else 0
        pot_score = house.potential_score.score if house.potential_score else 0

        # Determine score color class
        if fit_score >= 75:
            fit_class = "score-high"
        elif fit_score >= 60:
            fit_class = "score-medium"
        else:
            fit_class = "score-low"

        if pot_score >= 80:
            pot_class = "score-high"
        elif pot_score >= 65:
            pot_class = "score-medium"
        else:
            pot_class = "score-low"

        # Get first image or placeholder
        image_url = house.image_urls[0] if house.image_urls else ""

        # Features text
        features = []
        if house.features.bedrooms:
            features.append(f"{house.features.bedrooms} bed")
        if house.features.bathrooms:
            features.append(f"{house.features.bathrooms:.0f} bath")
        if house.features.sqft:
            features.append(f"{house.features.sqft:,} sqft")
        features_text = " · ".join(features)

        # Justification
        justification = ""
        if house.present_fit_score:
            justification = house.present_fit_score.justification

        # Tags from vision analysis
        positive_tags = []
        negative_tags = []
        if house.vision_analysis:
            positive_tags = house.vision_analysis.positive_signals[:3]
            negative_tags = house.vision_analysis.red_flags[:3]

        # Renovation ideas
        renovation_html = ""
        if house.potential_score and house.potential_score.renovation_ideas:
            renovation_html = '<div class="renovation-ideas">'
            for idea in house.potential_score.renovation_ideas[:2]:
                renovation_html += f'''
                <div class="renovation-idea">
                    <div class="renovation-area">{idea.area}</div>
                    <div class="renovation-change">{idea.proposed_change}</div>
                </div>'''
            renovation_html += '</div>'

        html += f"""
            <div class="house-card">
                <img src="{image_url}" alt="{house.address}" class="house-image" onerror="this.style.display='none'">
                <div class="house-content">
                    <div class="house-header">
                        <div>
                            <div class="house-address">{house.address}</div>
                            <div class="house-price">${house.price:,}</div>
                            <div class="house-features">{features_text}</div>
                        </div>
                        <div class="scores">
                            <div class="score-badge">
                                <div class="score-value {fit_class}">{fit_score:.0f}</div>
                                <div class="score-label">Fit Score</div>
                            </div>
                            <div class="score-badge">
                                <div class="score-value {pot_class}">{pot_score:.0f}</div>
                                <div class="score-label">Potential</div>
                            </div>
                        </div>
                    </div>

                    <div class="justification">{justification}</div>

                    <div class="tags">
                        {"".join(f'<span class="tag tag-positive">✓ {tag}</span>' for tag in positive_tags)}
                        {"".join(f'<span class="tag tag-negative">✗ {tag}</span>' for tag in negative_tags)}
                    </div>

                    {renovation_html}

                    <a href="{house.url}" target="_blank" class="house-link">View on Zillow →</a>

                    <div class="brief-section">
                        <button class="brief-toggle" onclick="toggleBrief(this)">
                            Show Full Brief
                        </button>
                        <div class="brief-content" data-markdown="{html_escape_for_attr(house.brief) if house.brief else ''}">
                            {('No brief generated' if not house.brief else '')}
                        </div>
                    </div>
                </div>
            </div>
"""

    html += """
        </div>

        <footer>
            <p>Generated by House Evaluator · Powered by Gemini 3 Flash</p>
        </footer>
    </div>

    <script>
        // Add smooth scrolling and any interactive features
        document.querySelectorAll('.house-card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });

        // Map toggle function
        function toggleMap() {
            const container = document.getElementById('map-container');
            const button = document.querySelector('.map-toggle');
            if (container.classList.contains('collapsed')) {
                container.classList.remove('collapsed');
                button.textContent = 'Hide Map';
                if (window.map) window.map.invalidateSize();
            } else {
                container.classList.add('collapsed');
                button.textContent = 'Show Map';
            }
        }

        // Brief toggle with markdown rendering
        function toggleBrief(button) {
            const briefContent = button.nextElementSibling;
            briefContent.classList.toggle('show');

            // Render markdown on first show
            if (briefContent.classList.contains('show') && !briefContent.dataset.rendered) {
                const markdown = briefContent.dataset.markdown;
                if (markdown && typeof marked !== 'undefined') {
                    briefContent.innerHTML = marked.parse(markdown);
                    briefContent.dataset.rendered = 'true';
                }
            }
        }
    </script>
"""

    # Add map initialization script if we have geocoded houses
    if houses_with_coords:
        # Calculate map center (average of all coordinates)
        avg_lat = sum(h.latitude for h in houses_with_coords) / len(houses_with_coords)
        avg_lng = sum(h.longitude for h in houses_with_coords) / len(houses_with_coords)

        # Generate markers data
        markers_js = []
        for h in houses_with_coords:
            fit_score = h.present_fit_score.score if h.present_fit_score else 0
            pot_score = h.potential_score.score if h.potential_score else 0

            # Color based on fit score
            if fit_score >= 75:
                color = "#22c55e"  # green
            elif fit_score >= 60:
                color = "#eab308"  # yellow
            else:
                color = "#ef4444"  # red

            # Escape quotes in address
            safe_address = h.address.replace("'", "\\'").replace('"', '\\"')
            price_str = f"${h.price:,}" if h.price else "N/A"

            markers_js.append(f"""
            {{
                lat: {h.latitude},
                lng: {h.longitude},
                address: "{safe_address}",
                price: "{price_str}",
                fit: {fit_score:.0f},
                potential: {pot_score:.0f},
                color: "{color}",
                url: "{h.url}"
            }}""")

        markers_data = ",".join(markers_js)

        html += f"""
    <script>
        // Initialize Leaflet map
        const map = L.map('map').setView([{avg_lat}, {avg_lng}], 11);
        window.map = map;

        // Add OpenStreetMap tiles
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }}).addTo(map);

        // House markers data
        const houses = [{markers_data}
        ];

        // Add markers for each house
        houses.forEach(house => {{
            // Create custom icon with score-based color
            const markerHtml = `
                <div style="
                    background: ${{house.color}};
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 11px;
                ">${{house.fit}}</div>
            `;

            const icon = L.divIcon({{
                html: markerHtml,
                className: 'custom-marker',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            }});

            const marker = L.marker([house.lat, house.lng], {{ icon }}).addTo(map);

            // Create popup content
            const popupContent = `
                <div class="popup-address">${{house.address}}</div>
                <div class="popup-price">${{house.price}}</div>
                <div class="popup-scores">Fit: ${{house.fit}} | Potential: ${{house.potential}}</div>
                <a href="${{house.url}}" target="_blank" class="popup-link">View on Zillow →</a>
            `;

            marker.bindPopup(popupContent);
        }});

        // Fit map to show all markers
        if (houses.length > 0) {{
            const bounds = L.latLngBounds(houses.map(h => [h.lat, h.lng]));
            map.fitBounds(bounds, {{ padding: [50, 50] }});
        }}
    </script>
"""

    html += """
</body>
</html>
"""

    return html


def save_report(output_path: str = "report.html") -> str:
    """Generate and save the HTML report."""
    html = generate_report()
    path = Path(output_path)
    path.write_text(html)
    return str(path.absolute())


if __name__ == "__main__":
    output = save_report()
    print(f"Report generated: {output}")

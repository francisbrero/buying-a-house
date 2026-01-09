"""CLI entry point for house evaluator."""

import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from src.storage import JsonStore
from src.models import House, TasteModel


def load_env():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


# Load .env on import
load_env()

app = typer.Typer(name="house", help="Agentic home listing aesthetic evaluator")
house_app = typer.Typer(help="House management commands")
taste_app = typer.Typer(help="Taste model commands")

app.add_typer(house_app, name="house")
app.add_typer(taste_app, name="taste")

console = Console()
store = JsonStore()


# House commands


@house_app.command("ingest")
def house_ingest(
    url: str = typer.Argument(..., help="Zillow listing URL"),
    data: str = typer.Option(None, "--data", "-d", help="JSON data from scraper"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive data entry"),
):
    """Ingest a house listing from Zillow URL."""
    if data:
        # Parse JSON data from Claude Code scraper
        try:
            listing_data = json.loads(data)
        except json.JSONDecodeError:
            console.print("[red]Error: Invalid JSON data[/red]")
            raise typer.Exit(1)

        house_id = store.generate_house_id(listing_data.get("address", ""))
        house = House.create_from_zillow(
            house_id=house_id,
            url=url,
            address=listing_data.get("address", ""),
            price=listing_data.get("price"),
            image_urls=listing_data.get("image_urls", []),
            description=listing_data.get("description", ""),
            features=listing_data.get("features", {}),
        )

        # Parse city/state/zip if provided
        if "city" in listing_data:
            house.city = listing_data["city"]
        if "state" in listing_data:
            house.state = listing_data["state"]
        if "zip_code" in listing_data:
            house.zip_code = listing_data["zip_code"]

        store.save_house(house)
        console.print(f"[green]✓ House ingested: {house.id}[/green]")
        console.print(f"  Address: {house.address}")
        console.print(f"  Price: ${house.price:,}" if house.price else "  Price: N/A")
        console.print(f"  Images: {len(house.image_urls)}")

    elif interactive:
        # Interactive data entry
        console.print("[yellow]Interactive mode - enter listing details:[/yellow]")
        address = typer.prompt("Address")
        price_str = typer.prompt("Price (numbers only)", default="")
        price = int(price_str) if price_str else None
        description = typer.prompt("Description", default="")
        images_str = typer.prompt("Image URLs (comma-separated)", default="")
        image_urls = [u.strip() for u in images_str.split(",") if u.strip()]

        house_id = store.generate_house_id(address)
        house = House.create_from_zillow(
            house_id=house_id,
            url=url,
            address=address,
            price=price,
            image_urls=image_urls,
            description=description,
        )

        store.save_house(house)
        console.print(f"[green]✓ House ingested: {house.id}[/green]")

    else:
        console.print("[yellow]To ingest this listing, either:[/yellow]")
        console.print("  1. Run with --data flag and provide JSON from scraper")
        console.print("  2. Run with --interactive flag for manual entry")
        console.print(f"\n  URL: {url}")


@house_app.command("import-search")
def house_import_search(
    search_url: str = typer.Argument(..., help="Zillow search URL"),
    data: str = typer.Option(None, "--data", "-d", help="JSON array of listings from scraper"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max listings to import"),
    score: bool = typer.Option(False, "--score", "-s", help="Auto-score after import"),
):
    """Import multiple houses from a Zillow search results page."""
    if data:
        # Parse JSON array of listings
        try:
            listings = json.loads(data)
            if not isinstance(listings, list):
                console.print("[red]Error: Data must be a JSON array of listings[/red]")
                raise typer.Exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON data: {e}[/red]")
            raise typer.Exit(1)

        # Limit number of listings
        listings = listings[:limit]

        console.print(f"[cyan]Importing {len(listings)} listings from Zillow search...[/cyan]\n")

        imported = 0
        skipped = 0
        imported_ids = []

        for listing in listings:
            address = listing.get("address", "")
            if not address:
                console.print(f"  [yellow]⚠ Skipping listing with no address[/yellow]")
                skipped += 1
                continue

            # Check for duplicates
            if store.house_exists(address):
                console.print(f"  [yellow]⚠ {address} - already exists, skipped[/yellow]")
                skipped += 1
                continue

            # Create house from listing data
            house_id = store.generate_house_id(address)
            house = House.create_from_zillow(
                house_id=house_id,
                url=listing.get("url", ""),
                address=address,
                price=listing.get("price"),
                image_urls=listing.get("image_urls", []),
                description=listing.get("description", ""),
                features=listing.get("features", {}),
            )

            # Parse city/state/zip if provided
            if "city" in listing:
                house.city = listing["city"]
            if "state" in listing:
                house.state = listing["state"]
            if "zip_code" in listing:
                house.zip_code = listing["zip_code"]

            store.save_house(house)
            imported_ids.append(house_id)
            console.print(f"  [green]✓ {address} - imported[/green]")
            imported += 1

        console.print(f"\n[cyan]Import complete: {imported} new, {skipped} skipped, {len(listings)} total[/cyan]")

        # Auto-score if requested
        if score and imported_ids:
            console.print(f"\n[yellow]Scoring {len(imported_ids)} new listings...[/yellow]\n")
            from src.agents.orchestrator import Orchestrator
            orchestrator = Orchestrator(store)

            for i, house_id in enumerate(imported_ids, 1):
                house = store.load_house(house_id)
                if house:
                    console.print(f"({i}/{len(imported_ids)}) {house.address}")
                    try:
                        orchestrator.score_house(house_id)
                        scored = store.load_house(house_id)
                        if scored and scored.present_fit_score:
                            potential_str = f"{scored.potential_score.score:.0f}" if scored.potential_score else "-"
                            console.print(f"  [green]✓[/green] Fit: {scored.present_fit_score.score:.0f} | Potential: {potential_str}")
                    except Exception as e:
                        console.print(f"  [red]✗ Error: {e}[/red]")

            orchestrator.cleanup()
            console.print("\n[green]Scoring complete![/green]")
        elif imported > 0:
            console.print("\n[dim]Run 'house batch-score' to score new listings.[/dim]")

    else:
        console.print("[yellow]To import listings from this search:[/yellow]")
        console.print("  1. Use Claude Code to scrape the search results")
        console.print("  2. Run with --data flag and provide JSON array")
        console.print(f"\n  Search URL: {search_url}")
        console.print("\n[dim]See .claude/skills/zillow-search.md for scraping instructions.[/dim]")


@house_app.command("score")
def house_score(
    house_id: str = typer.Argument(..., help="House ID to score"),
):
    """Run the full scoring pipeline on a house."""
    house = store.load_house(house_id)
    if not house:
        console.print(f"[red]House not found: {house_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]Scoring house: {house.address}[/yellow]")
    console.print("[dim]This will run vision analysis, present-fit scoring, and potential scoring.[/dim]")

    # Import and run orchestrator
    from src.agents.orchestrator import Orchestrator

    orchestrator = Orchestrator(store)
    result = orchestrator.score_house(house_id)

    if result:
        console.print("[green]✓ Scoring complete[/green]")
        house = store.load_house(house_id)
        if house and house.present_fit_score:
            console.print(f"  Present-fit score: {house.present_fit_score.score:.1f}/100")
        if house and house.potential_score:
            console.print(f"  Potential score: {house.potential_score.score:.1f}/100")
    else:
        console.print("[red]Scoring failed[/red]")


@house_app.command("batch-score")
def house_batch_score(
    all_houses: bool = typer.Option(False, "--all", "-a", help="Score all houses, including already scored"),
):
    """Score all unscored houses in the database."""
    houses = store.list_houses()

    if not all_houses:
        # Filter to only unscored houses
        houses = [h for h in houses if h.present_fit_score is None]

    if not houses:
        console.print("[dim]No houses to score.[/dim]")
        return

    console.print(f"[cyan]Scoring {len(houses)} houses...[/cyan]\n")

    from src.agents.orchestrator import Orchestrator
    orchestrator = Orchestrator(store)

    success_count = 0
    for i, house in enumerate(houses, 1):
        console.print(f"\n[bold]({i}/{len(houses)}) {house.address}[/bold]")
        try:
            result = orchestrator.score_house(house.id)
            if result:
                success_count += 1
                scored = store.load_house(house.id)
                if scored and scored.present_fit_score:
                    potential_str = f"{scored.potential_score.score:.0f}" if scored.potential_score else "-"
                    console.print(f"  [green]✓[/green] Fit: {scored.present_fit_score.score:.0f} | Potential: {potential_str}")
            else:
                console.print("  [red]✗ Failed[/red]")
        except Exception as e:
            console.print(f"  [red]✗ Error: {e}[/red]")

    console.print(f"\n[cyan]Batch complete: {success_count}/{len(houses)} succeeded[/cyan]")
    orchestrator.cleanup()


@house_app.command("list")
def house_list():
    """List all ingested houses."""
    houses = store.list_houses()

    if not houses:
        console.print("[dim]No houses found. Use 'house ingest' to add listings.[/dim]")
        return

    table = Table(title="Houses")
    table.add_column("ID", style="cyan", max_width=30)
    table.add_column("Address", max_width=40)
    table.add_column("Price", justify="right")
    table.add_column("Fit Score", justify="right")
    table.add_column("Potential", justify="right")

    for h in houses:
        fit = f"{h.present_fit_score.score:.0f}" if h.present_fit_score else "-"
        pot = f"{h.potential_score.score:.0f}" if h.potential_score else "-"
        price = f"${h.price:,}" if h.price else "-"

        table.add_row(h.id[:30], h.address[:40], price, fit, pot)

    console.print(table)


@house_app.command("show")
def house_show(
    house_id: str = typer.Argument(..., help="House ID to display"),
):
    """Display detailed house information and brief."""
    house = store.load_house(house_id)
    if not house:
        console.print(f"[red]House not found: {house_id}[/red]")
        raise typer.Exit(1)

    # Basic info panel
    info = f"""**Address:** {house.address}
**Price:** ${house.price:,} if house.price else 'N/A'
**URL:** {house.url}
**Images:** {len(house.image_urls)}
"""

    if house.features.bedrooms:
        info += f"**Beds:** {house.features.bedrooms} | **Baths:** {house.features.bathrooms} | **Sqft:** {house.features.sqft:,}"

    console.print(Panel(Markdown(info), title=f"House: {house_id}"))

    # Scores
    if house.present_fit_score:
        score_info = f"""**Present-Fit Score:** {house.present_fit_score.score:.1f}/100
**Passed:** {'✓' if house.present_fit_score.passed else '✗'}
**Violations:** {', '.join(house.present_fit_score.violations) or 'None'}

{house.present_fit_score.justification}
"""
        console.print(Panel(Markdown(score_info), title="Present-Fit Analysis"))

    if house.potential_score:
        pot_info = f"""**Potential Score:** {house.potential_score.score:.1f}/100
**Feasibility:** {house.potential_score.feasibility}
**Cost Class:** {house.potential_score.cost_class}

{house.potential_score.upside_narrative}
"""
        console.print(Panel(Markdown(pot_info), title="Potential Analysis"))

    # Brief
    if house.brief:
        console.print(Panel(Markdown(house.brief), title="House Brief"))


@house_app.command("delete")
def house_delete(
    house_id: str = typer.Argument(..., help="House ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a house from the database."""
    house = store.load_house(house_id)
    if not house:
        console.print(f"[red]House not found: {house_id}[/red]")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete house '{house.address}'?")
        if not confirm:
            raise typer.Abort()

    store.delete_house(house_id)
    console.print(f"[green]✓ Deleted: {house_id}[/green]")


# Taste commands


@taste_app.command("init")
def taste_init():
    """Initialize taste model through interactive interview."""
    if store.taste_exists():
        console.print("[yellow]Taste model already exists.[/yellow]")
        if not typer.confirm("Reinitialize?"):
            raise typer.Abort()

    console.print("[cyan]Let's build your taste profile...[/cyan]\n")

    # Import and run taste interview
    from src.agents.taste_curator import run_taste_interview

    taste = run_taste_interview(store)
    console.print(f"\n[green]✓ Taste model initialized with {len(taste.principles)} principles[/green]")


@taste_app.command("show")
def taste_show():
    """Display current taste model."""
    taste = store.load_taste()
    if not taste:
        console.print("[yellow]No taste model found. Run 'taste init' first.[/yellow]")
        return

    info = f"""## Principles
{chr(10).join('- ' + p for p in taste.principles) or '(none)'}

## Anti-Principles
{chr(10).join('- ' + p for p in taste.anti_principles) or '(none)'}

## Hard Constraints
{chr(10).join('- ' + c for c in taste.hard_constraints) or '(none)'}

## Violation Patterns
{chr(10).join('- ' + v for v in taste.violation_patterns) or '(none)'}

## Renovation Tolerance
{taste.renovation_tolerance} (max: ${taste.renovation_budget_max:,} if taste.renovation_budget_max else 'not set')
"""

    console.print(Panel(Markdown(info), title="Taste Model"))


@taste_app.command("distill")
def taste_distill():
    """Regenerate aesthetics.md from taste model."""
    taste = store.load_taste()
    if not taste:
        console.print("[yellow]No taste model found. Run 'taste init' first.[/yellow]")
        return

    console.print("[yellow]Distilling taste model to aesthetics.md...[/yellow]")

    from src.agents.distiller import DistillerAgent

    agent = DistillerAgent(store)
    content = agent.distill()
    store.save_aesthetics(content)

    console.print("[green]✓ aesthetics.md updated[/green]")


@taste_app.command("annotate")
def taste_annotate(
    house_id: str = typer.Argument(..., help="House ID to annotate"),
    verdict: str = typer.Option(None, "--verdict", "-v", help="Verdict: liked, disliked, shortlisted"),
    note: str = typer.Option(None, "--note", "-n", help="Free-form note"),
):
    """Add feedback/annotation to a house."""
    house = store.load_house(house_id)
    if not house:
        console.print(f"[red]House not found: {house_id}[/red]")
        raise typer.Exit(1)

    if verdict:
        if verdict not in ("liked", "disliked", "shortlisted"):
            console.print("[red]Verdict must be: liked, disliked, or shortlisted[/red]")
            raise typer.Exit(1)
        house.user_verdict = verdict

    if note:
        house.annotations.append(note)

    store.save_house(house)
    console.print(f"[green]✓ Annotation saved for {house_id}[/green]")

    # Trigger taste update proposal
    if verdict:
        console.print("[dim]Consider running 'taste review' to update preferences based on this feedback.[/dim]")


@house_app.command("report")
def house_report(
    output: str = typer.Option("report.html", "--output", "-o", help="Output file path"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open in browser after generating"),
):
    """Generate an HTML report of all house evaluations."""
    from src.report import save_report
    import webbrowser

    console.print("[yellow]Generating report...[/yellow]")
    path = save_report(output)
    console.print(f"[green]✓ Report saved to: {path}[/green]")

    if open_browser:
        webbrowser.open(f"file://{path}")


@taste_app.command("review")
def taste_review():
    """Review recent decisions and propose taste updates."""
    from src.agents.taste_curator import TasteCuratorAgent

    agent = TasteCuratorAgent(store)
    proposals = agent.review_recent_decisions()

    if not proposals:
        console.print("[dim]No taste updates suggested based on recent activity.[/dim]")
        return

    for proposal in proposals:
        console.print(Panel(proposal, title="Proposed Update"))
        if typer.confirm("Apply this update?"):
            agent.apply_proposal(proposal)
            console.print("[green]✓ Applied[/green]")


if __name__ == "__main__":
    app()

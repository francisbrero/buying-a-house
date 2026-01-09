"""Orchestrator - coordinates agent execution for scoring pipeline."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.storage import JsonStore
from .vision import VisionAgent
from .present_fit import PresentFitAgent
from .potential import PotentialAgent
from .brief import BriefAgent


console = Console()


class Orchestrator:
    """Coordinates the scoring pipeline for houses."""

    def __init__(self, store: JsonStore):
        self.store = store
        self.vision_agent = VisionAgent(store)
        self.present_fit_agent = PresentFitAgent(store)
        self.potential_agent = PotentialAgent(store)
        self.brief_agent = BriefAgent(store)

    def score_house(self, house_id: str) -> bool:
        """Run the full scoring pipeline on a house.

        Pipeline:
        1. Vision analysis (analyze images)
        2. Present-fit scoring (strict match to taste)
        3. Potential scoring (renovation opportunities)
        4. Brief generation (synthesize all analysis)

        Returns True if pipeline completed successfully.
        """
        house = self.store.load_house(house_id)
        if not house:
            console.print(f"[red]House not found: {house_id}[/red]")
            return False

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Step 1: Vision Analysis
            task = progress.add_task("Analyzing images...", total=None)
            try:
                vision = self.vision_agent.analyze(house_id)
                if vision:
                    progress.update(task, description="[green]✓ Vision analysis complete")
                else:
                    progress.update(task, description="[yellow]⚠ Vision analysis skipped (no images)")
            except Exception as e:
                progress.update(task, description=f"[red]✗ Vision analysis failed: {e}")
                return False

            # Step 2: Present-Fit Scoring
            task = progress.add_task("Scoring present-fit...", total=None)
            try:
                fit_score = self.present_fit_agent.score(house_id)
                if fit_score:
                    progress.update(
                        task,
                        description=f"[green]✓ Present-fit score: {fit_score.score:.1f}",
                    )
                else:
                    progress.update(task, description="[red]✗ Present-fit scoring failed")
                    return False
            except Exception as e:
                progress.update(task, description=f"[red]✗ Present-fit failed: {e}")
                return False

            # Step 3: Potential Scoring
            task = progress.add_task("Evaluating potential...", total=None)
            try:
                pot_score = self.potential_agent.score(house_id)
                if pot_score:
                    progress.update(
                        task,
                        description=f"[green]✓ Potential score: {pot_score.score:.1f}",
                    )
                else:
                    progress.update(task, description="[yellow]⚠ Potential scoring skipped")
            except Exception as e:
                progress.update(task, description=f"[yellow]⚠ Potential failed: {e}")
                # Continue anyway, potential is optional

            # Step 4: Brief Generation
            task = progress.add_task("Generating brief...", total=None)
            try:
                brief = self.brief_agent.generate(house_id)
                if brief:
                    progress.update(task, description="[green]✓ Brief generated")
                else:
                    progress.update(task, description="[yellow]⚠ Brief generation skipped")
            except Exception as e:
                progress.update(task, description=f"[yellow]⚠ Brief failed: {e}")
                # Continue anyway, brief is optional

        return True

    def batch_score(self, house_ids: list[str] | None = None) -> dict[str, bool]:
        """Score multiple houses.

        Args:
            house_ids: List of house IDs to score, or None for all unscored

        Returns:
            Dict mapping house_id to success/failure
        """
        if house_ids is None:
            houses = self.store.get_unscored_houses()
            house_ids = [h.id for h in houses]

        if not house_ids:
            console.print("[dim]No houses to score.[/dim]")
            return {}

        console.print(f"[cyan]Scoring {len(house_ids)} houses...[/cyan]\n")

        results = {}
        for i, house_id in enumerate(house_ids, 1):
            house = self.store.load_house(house_id)
            console.print(f"\n[bold]({i}/{len(house_ids)}) {house.address if house else house_id}[/bold]")
            results[house_id] = self.score_house(house_id)

        # Summary
        success = sum(results.values())
        console.print(f"\n[cyan]Batch complete: {success}/{len(house_ids)} succeeded[/cyan]")

        return results

    def get_rankings(self) -> list[tuple[str, float, float]]:
        """Get ranked list of scored houses.

        Returns list of (house_id, present_fit_score, potential_score) tuples,
        sorted by present_fit_score descending.
        """
        houses = self.store.get_scored_houses()
        rankings = []

        for h in houses:
            fit = h.present_fit_score.score if h.present_fit_score else 0
            pot = h.potential_score.score if h.potential_score else 0
            rankings.append((h.id, fit, pot))

        return sorted(rankings, key=lambda x: x[1], reverse=True)

    def cleanup(self):
        """Clean up agent resources."""
        self.vision_agent.cleanup()
        self.present_fit_agent.cleanup()
        self.potential_agent.cleanup()
        self.brief_agent.cleanup()

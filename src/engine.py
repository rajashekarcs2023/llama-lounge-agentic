"""Core engine — orchestrates the full DocAgent pipeline:
index → navigate → fetch → generate → validate."""

from rich.console import Console
from rich.panel import Panel

from src.cache import cache
from src.indexer import index_site, fetch_pages
from src.navigator import navigate
from src.crew import generate_code
from src.validator import validate_and_fix

console = Console()


def add_source(url: str, force: bool = False) -> list[dict]:
    """Index a documentation site and add it to the knowledge base."""
    with console.status(f"[bold blue]Indexing {url}..."):
        pages = index_site(url, force=force)
    console.print(f"  [green]✓[/green] Indexed [bold]{len(pages)}[/bold] pages from {url}")
    return pages


def run_task(task_description: str) -> str:
    """Run the full DocAgent pipeline for a given task.

    1. Get unified index across all indexed sites
    2. Navigator agent selects relevant pages
    3. Fetch those pages
    4. Code crew generates working code

    Args:
        task_description: What the user wants to build

    Returns:
        Generated code as a string
    """
    unified_index = cache.get_unified_index()

    if not unified_index:
        console.print("[red]✗ No doc sites indexed yet. Use 'add' to index a doc site first.[/red]")
        return ""

    stats = cache.stats()
    console.print(
        f"\n[dim]Knowledge base: {stats['indexed_sites']} sites, "
        f"{stats['total_pages_indexed']} pages indexed[/dim]"
    )

    # Phase 1: Navigate
    console.print(Panel("[bold cyan]Phase 1: Navigator Agent[/bold cyan] — selecting relevant pages"))
    with console.status("[bold blue]Navigator is reasoning across all doc sites..."):
        selected_urls = navigate(task_description, unified_index)

    if not selected_urls:
        console.print("[red]✗ Navigator could not identify relevant pages.[/red]")
        return ""

    console.print(f"  [green]✓[/green] Selected [bold]{len(selected_urls)}[/bold] pages:")
    for url in selected_urls:
        console.print(f"    • {url}")

    # Phase 2: Fetch
    console.print(Panel("[bold cyan]Phase 2: Fetching[/bold cyan] — retrieving selected doc pages"))
    with console.status("[bold blue]Fetching doc pages..."):
        doc_contents = fetch_pages(selected_urls)

    fetched_count = sum(1 for v in doc_contents.values() if not v.startswith("[Error"))
    console.print(f"  [green]✓[/green] Fetched [bold]{fetched_count}[/bold] pages successfully")

    # Phase 3: Generate
    console.print(Panel("[bold cyan]Phase 3: Code Crew[/bold cyan] — analyzing docs & generating code"))
    code = generate_code(task_description, doc_contents)

    if not code:
        console.print("[red]✗ Code generation failed.[/red]")
        return ""

    # Phase 4: Validate + Retry
    console.print(Panel("[bold cyan]Phase 4: Validator[/bold cyan] — verifying code in sandbox"))
    with console.status("[bold blue]Validating generated code..."):
        final_code, validation_log = validate_and_fix(
            code, task_description, doc_contents, generate_code
        )

    for entry in validation_log:
        if entry["valid"]:
            console.print(
                f"  [green]✓[/green] Attempt {entry['attempt']}: "
                f"[bold green]VALID[/bold green]"
            )
        else:
            console.print(
                f"  [yellow]⚠[/yellow] Attempt {entry['attempt']}: "
                f"[red]Error[/red] — {entry['error'][:120]}"
            )

    if final_code:
        console.print(Panel(final_code, title="[bold green]Generated Code[/bold green]", border_style="green"))

        # Always save to file
        filename = "generated_code.py"
        with open(filename, "w") as f:
            f.write(final_code)
        console.print(f"\n[green]✓ Code saved to [bold]{filename}[/bold][/green]")
    else:
        console.print("[red]✗ Code generation failed after retries.[/red]")

    return final_code

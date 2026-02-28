"""DocAgent CLI — the developer that reads ALL the docs."""

import sys
import os

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.engine import add_source, run_task
from src.cache import cache

console = Console()

BANNER = """
[bold cyan]╔══════════════════════════════════════════════╗
║             🔍  DocAgent  🔍                 ║
║   The developer that reads ALL the docs.     ║
║   Index doc sites → describe a task →        ║
║   get working code in seconds.               ║
╚══════════════════════════════════════════════╝[/bold cyan]
"""


def print_help():
    console.print("\n[bold]Commands:[/bold]")
    console.print("  [cyan]add <url>[/cyan]     — Index a documentation site")
    console.print("  [cyan]build <task>[/cyan]   — Generate code for a task using indexed docs")
    console.print("  [cyan]status[/cyan]         — Show indexed sites and stats")
    console.print("  [cyan]help[/cyan]           — Show this help message")
    console.print("  [cyan]quit[/cyan]           — Exit\n")


def cmd_add(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    add_source(url)


def cmd_build(task: str):
    if not task:
        console.print("[red]Please provide a task description.[/red]")
        return
    code = run_task(task)
    if code:
        # Save to file
        filename = "generated_code.py"
        with open(filename, "w") as f:
            f.write(code)
        console.print(f"\n[green]✓ Code saved to [bold]{filename}[/bold][/green]")


def cmd_status():
    stats = cache.stats()
    console.print(f"\n[bold]DocAgent Status[/bold]")
    console.print(f"  Indexed sites:     {stats['indexed_sites']}")
    console.print(f"  Total pages:       {stats['total_pages_indexed']}")
    console.print(f"  Pages fetched:     {stats['pages_fetched']}")

    indexes = cache.get_all_indexes()
    if indexes:
        console.print("\n  [bold]Sources:[/bold]")
        for site, pages in indexes.items():
            console.print(f"    • {site} ({len(pages)} pages)")
    console.print()


def interactive_mode():
    console.print(BANNER)
    print_help()

    while True:
        try:
            user_input = Prompt.ask("[bold green]docagent[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break
        elif user_input.lower() == "help":
            print_help()
        elif user_input.lower() == "status":
            cmd_status()
        elif user_input.lower().startswith("add "):
            url = user_input[4:].strip()
            cmd_add(url)
        elif user_input.lower().startswith("build "):
            task = user_input[6:].strip()
            cmd_build(task)
        else:
            # Treat as a build task by default
            cmd_build(user_input)


def cli_mode():
    """Non-interactive mode: pass args directly."""
    if len(sys.argv) < 2:
        interactive_mode()
        return

    command = sys.argv[1].lower()

    if command == "add" and len(sys.argv) >= 3:
        cmd_add(sys.argv[2])
    elif command == "build" and len(sys.argv) >= 3:
        task = " ".join(sys.argv[2:])
        cmd_build(task)
    elif command == "status":
        cmd_status()
    else:
        interactive_mode()


if __name__ == "__main__":
    cli_mode()

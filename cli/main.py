#!/usr/bin/env python3
"""QuantPath CLI — MFE application toolkit."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.data_loader import load_all_programs, load_profile
from core.prerequisite_matcher import match_prerequisites
from core.profile_evaluator import evaluate as evaluate_profile
from core.school_ranker import rank_schools
from core.test_requirements import check_gre, check_toefl
from core.timeline_generator import generate_timeline

console = Console()


def bar(score: float, width: int = 10) -> str:
    """Render a score as a bar chart."""
    filled = round(score * width / 10)
    return "█" * filled + "░" * (width - filled)


def cmd_evaluate(args: argparse.Namespace) -> None:
    """Evaluate a user profile against MFE programs."""
    profile = load_profile(args.profile)
    programs = load_all_programs()
    result = evaluate_profile(profile)

    # Header
    console.print()
    console.print(
        Panel(
            f"[bold]{profile.name}[/bold] | {profile.university} | "
            f"GPA {profile.gpa} | {'International' if profile.is_international else 'Domestic'}",
            title="QuantPath Profile Evaluation",
            border_style="cyan",
        )
    )

    # Dimension scores
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Dimension", style="bold", width=16)
    table.add_column("Score", width=10)
    table.add_column("Bar", width=12)

    dim_labels = {
        "math": "Math",
        "statistics": "Statistics",
        "cs": "CS",
        "finance_econ": "Finance/Econ",
        "gpa": "GPA",
    }

    for dim_id, label in dim_labels.items():
        score = result.dimension_scores.get(dim_id, 0)
        color = "green" if score >= 9 else "yellow" if score >= 7 else "red"
        table.add_row(
            f"  {label}",
            f"[{color}]{score:.1f}/10[/{color}]",
            f"[{color}]{bar(score)}[/{color}]",
        )

    console.print(table)
    console.print()

    # Overall
    overall = result.overall_score
    overall_color = "green" if overall >= 9 else "yellow" if overall >= 7 else "red"
    level = (
        "Top 3-5 MFE Level"
        if overall >= 9.5
        else "Top 5-10 MFE Level"
        if overall >= 8.5
        else "Competitive"
        if overall >= 7.5
        else "Needs Improvement"
    )
    console.print(
        f"  [bold]OVERALL:[/bold]    [{overall_color}]{overall:.1f}/10[/{overall_color}]  "
        f"[{overall_color}]{bar(overall)}[/{overall_color}]  {level}"
    )
    console.print()

    # School recommendations
    rankings = rank_schools(profile, programs, result)

    if rankings.get("reach"):
        reach_names = ", ".join(r["name"] for r in rankings["reach"])
        console.print(f"  🎯 [bold]Reach:[/bold]   {reach_names}")
    if rankings.get("target"):
        target_names = ", ".join(r["name"] for r in rankings["target"])
        console.print(f"  🎯 [bold]Target:[/bold]  {target_names}")
    if rankings.get("safety"):
        safety_names = ", ".join(r["name"] for r in rankings["safety"])
        console.print(f"  🎯 [bold]Safety:[/bold]  {safety_names}")
    console.print()

    # Gaps
    if result.gaps:
        console.print("  [bold red]⚠️  Gaps Found:[/bold red]")
        for gap in result.gaps:
            dim = gap.get("dimension", "")
            factor = gap.get("factor", "").replace("_", " ").title()
            score = gap.get("score", 0)
            if score == 0:
                console.print(f"     - {factor} [dim]({dim})[/dim]: [red]Missing[/red]")
            else:
                console.print(f"     - {factor} [dim]({dim})[/dim]: [yellow]{score:.1f}/10[/yellow]")
        console.print()

    # Strengths
    if result.strengths:
        console.print("  [bold green]✅ Strengths:[/bold green]")
        for strength in result.strengths:
            dim = strength.get("dimension", "")
            factor = strength.get("factor", "").replace("_", " ").title()
            score = strength.get("score", 0)
            console.print(f"     - {factor} [dim]({dim})[/dim]: [green]{score:.1f}/10[/green]")
        console.print()


def cmd_match(args: argparse.Namespace) -> None:
    """Match prerequisites against specific programs."""
    profile = load_profile(args.profile)
    programs = load_all_programs()

    if args.program:
        programs = [p for p in programs if p.id == args.program]
        if not programs:
            console.print(f"[red]Program '{args.program}' not found.[/red]")
            return

    console.print()
    console.print(
        Panel("Prerequisite Match Report", border_style="cyan")
    )

    for program in programs:
        match = match_prerequisites(profile, program)
        color = "green" if match.match_score >= 0.8 else "yellow" if match.match_score >= 0.6 else "red"

        console.print(f"\n  [bold]{program.name}[/bold] ({program.university})")
        console.print(f"  Match: [{color}]{match.match_score:.0%}[/{color}]")

        if match.missing:
            console.print(f"  [red]Missing:[/red] {', '.join(match.missing)}")
        if match.warnings:
            for w in match.warnings:
                console.print(f"  [yellow]⚠️  {w}[/yellow]")
    console.print()


def cmd_tests(args: argparse.Namespace) -> None:
    """Check GRE/TOEFL requirements."""
    profile = load_profile(args.profile)
    programs = load_all_programs()

    console.print()
    table = Table(title="Test Requirements", border_style="cyan")
    table.add_column("Program", style="bold")
    table.add_column("GRE")
    table.add_column("TOEFL")

    for program in programs:
        gre = check_gre(profile, program)
        toefl = check_toefl(profile, program)

        gre_str = (
            "[green]Exempt[/green]" if gre["exempt"]
            else "[red]REQUIRED[/red]" if gre["required"]
            else "[yellow]Optional[/yellow]"
        )
        toefl_str = (
            "[green]Waived[/green]" if toefl["waived"]
            else "[red]REQUIRED[/red]" if toefl["required"]
            else "[yellow]Check[/yellow]"
        )
        table.add_row(program.name, gre_str, toefl_str)

    console.print(table)
    console.print()


def cmd_timeline(args: argparse.Namespace) -> None:
    """Generate application timeline."""
    programs = load_all_programs()
    from datetime import date

    events = generate_timeline(programs, date.today())

    console.print()
    console.print(Panel("Application Timeline", border_style="cyan"))

    current_month = None
    for event in events:
        # Timeline returns ISO date strings; parse to date objects.
        d = date.fromisoformat(event["date"])
        month = d.strftime("%B %Y")
        if month != current_month:
            console.print(f"\n  [bold cyan]── {month} ──[/bold cyan]")
            current_month = month

        priority_icon = "🔴" if event["priority"] == "critical" else "🟡" if event["priority"] == "high" else "⚪"
        console.print(f"  {priority_icon} {d.strftime('%b %d')}  {event['action']}")

    console.print()


def cmd_programs(args: argparse.Namespace) -> None:
    """List all programs in the database."""
    programs = load_all_programs()

    console.print()
    table = Table(title="MFE Programs Database", border_style="cyan")
    table.add_column("Program", style="bold")
    table.add_column("University")
    table.add_column("Class")
    table.add_column("Rate")
    table.add_column("GPA")
    table.add_column("GRE")

    for p in programs:
        rate = f"{p.acceptance_rate:.0%}" if p.acceptance_rate else "N/A"
        gpa = f"{p.avg_gpa:.2f}" if p.avg_gpa else "N/A"
        size = str(p.class_size) if p.class_size else "N/A"
        gre = "Required" if p.gre_required else "Optional"
        table.add_row(p.name, p.university, size, rate, gpa, gre)

    console.print(table)
    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="quantpath",
        description="QuantPath — Open-source MFE application toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Evaluate your profile")
    p_eval.add_argument("--profile", "-p", required=True, help="Path to profile YAML")

    # match
    p_match = subparsers.add_parser("match", help="Match prerequisites")
    p_match.add_argument("--profile", "-p", required=True, help="Path to profile YAML")
    p_match.add_argument("--program", help="Specific program ID (default: all)")

    # tests
    p_tests = subparsers.add_parser("tests", help="Check GRE/TOEFL requirements")
    p_tests.add_argument("--profile", "-p", required=True, help="Path to profile YAML")

    # timeline
    p_timeline = subparsers.add_parser("timeline", help="Generate application timeline")

    # programs
    subparsers.add_parser("programs", help="List all programs")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "evaluate": cmd_evaluate,
        "match": cmd_match,
        "tests": cmd_tests,
        "timeline": cmd_timeline,
        "programs": cmd_programs,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

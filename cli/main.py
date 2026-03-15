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
from core.gap_advisor import analyze_gaps
from core.interview_prep import (
    get_questions_by_category,
    get_questions_by_difficulty,
    get_questions_for_program,
    get_random_quiz,
    load_questions,
)
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


def cmd_compare(args: argparse.Namespace) -> None:
    """Compare 2-3 programs side-by-side."""
    program_ids = [pid.strip() for pid in args.programs.split(",")]

    if len(program_ids) < 2 or len(program_ids) > 3:
        console.print("[red]Please specify 2 or 3 program IDs separated by commas.[/red]")
        return

    all_programs = load_all_programs()
    programs_by_id = {p.id: p for p in all_programs}

    selected = []
    for pid in program_ids:
        if pid not in programs_by_id:
            console.print(f"[red]Program '{pid}' not found.[/red]")
            return
        selected.append(programs_by_id[pid])

    console.print()
    console.print(
        Panel(
            "Side-by-Side Program Comparison",
            border_style="cyan",
        )
    )

    table = Table(border_style="cyan", show_lines=True)
    table.add_column("Attribute", style="bold", width=22)
    for prog in selected:
        table.add_column(prog.name, min_width=18)

    # University
    table.add_row("University", *[p.university for p in selected])

    # Class Size
    table.add_row(
        "Class Size",
        *[str(p.class_size) if p.class_size else "N/A" for p in selected],
    )

    # Acceptance Rate
    table.add_row(
        "Acceptance Rate",
        *[f"{p.acceptance_rate:.0%}" if p.acceptance_rate else "N/A" for p in selected],
    )

    # Avg GPA
    table.add_row(
        "Avg GPA",
        *[f"{p.avg_gpa:.2f}" if p.avg_gpa else "N/A" for p in selected],
    )

    # GRE Required
    table.add_row(
        "GRE Required",
        *["Yes" if p.gre_required else "No" for p in selected],
    )

    # TOEFL Min
    table.add_row(
        "TOEFL Min",
        *[str(p.toefl_min_ibt) if p.toefl_min_ibt else "N/A" for p in selected],
    )

    # Application Fee
    table.add_row(
        "Application Fee",
        *[f"${p.application_fee}" if p.application_fee else "N/A" for p in selected],
    )

    # Recommendations
    table.add_row(
        "Recommendations",
        *[str(p.recommendations) if p.recommendations else "N/A" for p in selected],
    )

    # Deadline Round 1
    def _round_date(prog, round_num):
        for r in prog.deadline_rounds:
            if r.round == round_num:
                return r.date
        return "N/A"

    table.add_row(
        "Deadline Round 1",
        *[_round_date(p, 1) for p in selected],
    )

    # Deadline Round 2
    table.add_row(
        "Deadline Round 2",
        *[_round_date(p, 2) for p in selected],
    )

    # Prerequisites (required count)
    table.add_row(
        "Prerequisites (req.)",
        *[str(len(p.prerequisites_required)) for p in selected],
    )

    # Interview type
    table.add_row(
        "Interview",
        *[p.interview_type.replace("_", " ").title() if p.interview_type else "N/A" for p in selected],
    )

    console.print(table)
    console.print()


def _difficulty_badge(difficulty: str) -> str:
    """Return a Rich-formatted badge for question difficulty."""
    colors = {"easy": "green", "medium": "yellow", "hard": "red"}
    color = colors.get(difficulty, "white")
    label = difficulty.upper()
    return f"[{color}] {label} [/{color}]"


def cmd_interview(args: argparse.Namespace) -> None:
    """Display interview practice questions as a study guide."""
    categories = load_questions()

    # --list-categories: just print the category table and exit.
    if args.list_categories:
        console.print()
        table = Table(title="Interview Question Categories", border_style="cyan")
        table.add_column("ID", style="bold")
        table.add_column("Category")
        table.add_column("Questions", justify="right")
        table.add_column("Difficulties")

        for cat in categories:
            diffs = sorted({q.difficulty for q in cat.questions})
            diff_str = ", ".join(diffs)
            table.add_row(cat.id, cat.name, str(len(cat.questions)), diff_str)

        total = sum(len(c.questions) for c in categories)
        console.print(table)
        console.print(f"\n  [bold]{total}[/bold] questions across [bold]{len(categories)}[/bold] categories\n")
        return

    # Build the question pool based on filters.
    if args.category:
        questions = get_questions_by_category(args.category, categories)
        if not questions:
            console.print(f"[red]Category '{args.category}' not found.[/red]")
            console.print("[dim]Use --list-categories to see available categories.[/dim]")
            return
    elif args.difficulty:
        questions = get_questions_by_difficulty(args.difficulty, categories)
    elif args.program:
        questions = get_questions_for_program(args.program, categories)
        if not questions:
            console.print(f"[red]No questions tagged for program '{args.program}'.[/red]")
            return
    else:
        questions = get_random_quiz(
            n=args.count,
            categories=categories,
        )

    # Apply additional filters when a primary filter was already set.
    if args.category and args.difficulty:
        questions = [q for q in questions if q.difficulty == args.difficulty.lower()]
    if args.program and args.category:
        questions = [q for q in questions if args.program in q.programs]

    # Limit to requested count (unless fewer available).
    if len(questions) > args.count:
        questions = questions[: args.count]

    if not questions:
        console.print("[yellow]No questions match the given filters.[/yellow]")
        return

    # Header
    console.print()
    filter_parts = []
    if args.category:
        filter_parts.append(f"Category: [bold]{args.category}[/bold]")
    if args.difficulty:
        filter_parts.append(f"Difficulty: [bold]{args.difficulty}[/bold]")
    if args.program:
        filter_parts.append(f"Program: [bold]{args.program}[/bold]")
    filter_desc = "  |  ".join(filter_parts) if filter_parts else "All categories"

    console.print(
        Panel(
            f"[bold]Interview Practice Set[/bold]  --  {len(questions)} questions\n{filter_desc}",
            border_style="cyan",
            title="QuantPath Interview Prep",
        )
    )

    # Render each question
    for idx, q in enumerate(questions, 1):
        badge = _difficulty_badge(q.difficulty)
        topics_str = ", ".join(q.topics)

        # Question header line
        header = Text()
        header.append(f"Q{idx}", style="bold cyan")
        header.append(f"  [{q.category_name}]", style="dim")

        # Build panel content
        lines = []
        lines.append(f"{q.question}")
        lines.append("")
        lines.append(f"Difficulty: {badge}    Topics: [cyan]{topics_str}[/cyan]")

        if q.programs:
            prog_str = ", ".join(q.programs)
            lines.append(f"Programs:   [dim]{prog_str}[/dim]")

        lines.append("")
        lines.append(f"[dim italic]Hint: {q.hint}[/dim italic]")
        lines.append("")
        lines.append("[bold]Solution:[/bold]")
        for sol_line in q.solution.strip().splitlines():
            lines.append(f"  {sol_line}")

        console.print(
            Panel(
                "\n".join(lines),
                title=str(header),
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Summary footer
    cats_seen = sorted({q.category_name for q in questions})
    diff_counts = {}
    for q in questions:
        diff_counts[q.difficulty] = diff_counts.get(q.difficulty, 0) + 1
    diff_summary = "  ".join(
        f"{_difficulty_badge(d)}: {c}" for d, c in sorted(diff_counts.items())
    )

    console.print(
        Panel(
            f"[bold]{len(questions)}[/bold] questions  |  "
            f"Categories: {', '.join(cats_seen)}\n"
            f"Difficulty breakdown: {diff_summary}",
            title="Practice Set Summary",
            border_style="green",
        )
    )
    console.print()


def cmd_gaps(args: argparse.Namespace) -> None:
    """Analyze profile gaps and suggest improvements."""
    profile = load_profile(args.profile)
    result = evaluate_profile(profile)

    console.print()
    console.print(
        Panel(
            f"[bold]Gap Analysis[/bold] for {profile.name}",
            border_style="cyan",
        )
    )

    if not result.gaps:
        console.print("  [bold green]No gaps found -- your profile looks strong across all dimensions![/bold green]")
        console.print()
        return

    recommendations = analyze_gaps(result.gaps)

    table = Table(border_style="cyan", show_lines=True)
    table.add_column("Factor", style="bold", width=22)
    table.add_column("Dimension", width=14)
    table.add_column("Score", width=10, justify="center")
    table.add_column("Priority", width=10, justify="center")
    table.add_column("Recommended Action", min_width=40)

    for rec in recommendations:
        # Color-code score
        if rec.score == 0:
            score_str = "[red]Missing[/red]"
        else:
            score_str = f"[yellow]{rec.score:.1f}/10[/yellow]"

        # Color-code priority
        priority_colors = {
            "High": "red",
            "Medium": "yellow",
            "Low": "cyan",
        }
        pcolor = priority_colors.get(rec.priority, "white")
        priority_str = f"[{pcolor}]{rec.priority}[/{pcolor}]"

        factor_label = rec.factor.replace("_", " ").title()

        table.add_row(
            factor_label,
            rec.dimension,
            score_str,
            priority_str,
            rec.action,
        )

    console.print(table)

    # Summary counts
    high_count = sum(1 for r in recommendations if r.priority == "High")
    med_count = sum(1 for r in recommendations if r.priority == "Medium")
    low_count = sum(1 for r in recommendations if r.priority == "Low")

    console.print()
    console.print(
        f"  [bold]Summary:[/bold]  "
        f"[red]{high_count} High[/red]  "
        f"[yellow]{med_count} Medium[/yellow]  "
        f"[cyan]{low_count} Low[/cyan]  "
        f"({len(recommendations)} total gaps)"
    )
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

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare 2-3 programs side-by-side")
    p_compare.add_argument(
        "--programs", required=True,
        help="Comma-separated program IDs (e.g., cmu-mscf,baruch-mfe,berkeley-mfe)",
    )

    # interview
    p_interview = subparsers.add_parser("interview", help="Practice MFE interview questions")
    p_interview.add_argument("--category", "-c", help="Filter by category ID (e.g. probability, finance)")
    p_interview.add_argument(
        "--difficulty", "-d",
        choices=["easy", "medium", "hard"],
        help="Filter by difficulty level",
    )
    p_interview.add_argument("--program", help="Show questions for a specific program (e.g. baruch-mfe)")
    p_interview.add_argument(
        "--count", "-n",
        type=int, default=5,
        help="Number of questions to display (default: 5)",
    )
    p_interview.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available question categories and exit",
    )

    # gaps
    p_gaps = subparsers.add_parser("gaps", help="Analyze profile gaps and suggest improvements")
    p_gaps.add_argument("--profile", "-p", required=True, help="Path to profile YAML")

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
        "compare": cmd_compare,
        "interview": cmd_interview,
        "gaps": cmd_gaps,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

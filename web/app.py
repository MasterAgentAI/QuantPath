"""QuantPath Streamlit Dashboard.

Run with:
    streamlit run web/app.py
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Ensure the package root is importable regardless of working directory.
# ---------------------------------------------------------------------------
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from core.data_loader import load_all_programs, load_profile  # noqa: E402
from core.gap_advisor import analyze_gaps  # noqa: E402
from core.profile_evaluator import evaluate as evaluate_profile  # noqa: E402
from core.school_ranker import rank_schools  # noqa: E402
from core.timeline_generator import generate_timeline  # noqa: E402

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="QuantPath",
    page_icon="\U0001f4ca",  # bar chart emoji
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar branding and navigation
# ---------------------------------------------------------------------------
SAMPLE_PROFILE_PATH = _PACKAGE_ROOT / "examples" / "sample_profile.yaml"

PAGES = [
    "Profile Evaluation",
    "Program Explorer",
    "Program Comparison",
    "Gap Analysis",
    "Application Timeline",
]

with st.sidebar:
    st.markdown(
        "<h1 style='text-align:center;margin-bottom:0'>QuantPath</h1>"
        "<p style='text-align:center;color:gray;margin-top:0'>"
        "MFE Application Toolkit</p>",
        unsafe_allow_html=True,
    )
    st.divider()
    page = st.radio("Navigation", PAGES, index=0, label_visibility="collapsed")
    st.divider()
    st.caption("Built with Streamlit + Plotly")


# ---------------------------------------------------------------------------
# Helpers: profile loading
# ---------------------------------------------------------------------------

def _load_profile_from_bytes(raw_bytes: bytes) -> None:
    """Write uploaded YAML bytes to a temp file and load into session state."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=".yaml", delete=False, mode="wb",
    )
    tmp.write(raw_bytes)
    tmp.flush()
    tmp.close()
    try:
        profile = load_profile(tmp.name)
        st.session_state["profile"] = profile
        st.session_state["profile_path"] = tmp.name
    except Exception as exc:
        st.error(f"Failed to load profile: {exc}")


def _load_sample_profile() -> None:
    """Load the bundled sample profile."""
    try:
        profile = load_profile(str(SAMPLE_PROFILE_PATH))
        st.session_state["profile"] = profile
        st.session_state["profile_path"] = str(SAMPLE_PROFILE_PATH)
    except Exception as exc:
        st.error(f"Failed to load sample profile: {exc}")


def _get_profile():
    """Return the currently loaded profile or None."""
    return st.session_state.get("profile")


def _require_profile():
    """Show a warning if no profile is loaded and return the profile or None."""
    profile = _get_profile()
    if profile is None:
        st.warning(
            "No profile loaded. Please go to **Profile Evaluation** and "
            "upload a YAML profile or click **Use Sample Profile** first."
        )
    return profile


# ---------------------------------------------------------------------------
# Helpers: data loading (cached)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading programs...")
def _load_programs():
    return load_all_programs()


# ---------------------------------------------------------------------------
# Helpers: formatting
# ---------------------------------------------------------------------------

_DIM_LABELS = {
    "math": "Math",
    "statistics": "Statistics",
    "cs": "Computer Science",
    "finance_econ": "Finance / Econ",
    "gpa": "GPA",
}

_PRIORITY_COLORS = {
    "critical": "#e74c3c",
    "high": "#e67e22",
    "medium": "#f1c40f",
    "low": "#3498db",
    "High": "#e74c3c",
    "Medium": "#e67e22",
    "Low": "#3498db",
}


# ===================================================================
# Page 1: Profile Evaluation
# ===================================================================

def page_profile_evaluation() -> None:
    st.header("Profile Evaluation")

    col_upload, col_sample = st.columns([3, 1])
    with col_upload:
        uploaded = st.file_uploader(
            "Upload your profile YAML",
            type=["yaml", "yml"],
            key="profile_uploader",
        )
    with col_sample:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Use Sample Profile", use_container_width=True):
            _load_sample_profile()

    if uploaded is not None:
        _load_profile_from_bytes(uploaded.getvalue())

    profile = _get_profile()
    if profile is None:
        st.info("Upload a profile YAML or click **Use Sample Profile** to get started.")
        return

    programs = _load_programs()
    result = evaluate_profile(profile)
    rankings = rank_schools(profile, programs, result)

    # ----- Profile summary card -----
    st.subheader("Profile Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Name", profile.name or "N/A")
    c2.metric("University", profile.university or "N/A")
    c3.metric("GPA", f"{profile.gpa:.2f}")
    c4.metric("Majors", ", ".join(profile.majors) if profile.majors else "N/A")

    st.divider()

    # ----- Radar chart (plotly) -----
    st.subheader("Dimension Scores")

    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        dims = list(_DIM_LABELS.keys())
        labels = [_DIM_LABELS[d] for d in dims]
        scores = [result.dimension_scores.get(d, 0) for d in dims]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(99, 110, 250, 0.25)",
            line=dict(color="rgb(99, 110, 250)", width=2),
            name="Your Profile",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], tickvals=[2, 4, 6, 8, 10]),
            ),
            showlegend=False,
            height=380,
            margin=dict(t=30, b=30, l=60, r=60),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        rows = []
        for d in dims:
            score = result.dimension_scores.get(d, 0)
            rows.append({
                "Dimension": _DIM_LABELS[d],
                "Score": f"{score:.2f} / 10",
                "Rating": (
                    "Excellent" if score >= 9
                    else "Good" if score >= 7
                    else "Needs Work" if score >= 5
                    else "Weak"
                ),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    # ----- Overall score -----
    st.divider()
    overall = result.overall_score
    level = (
        "Top 3-5 MFE Level"
        if overall >= 9.5
        else "Top 5-10 MFE Level"
        if overall >= 8.5
        else "Competitive"
        if overall >= 7.5
        else "Needs Improvement"
    )
    m1, m2, m3 = st.columns([1, 2, 1])
    with m2:
        st.metric(
            label="Overall Score",
            value=f"{overall:.2f} / 10",
            delta=level,
        )

    # ----- Gaps and strengths -----
    st.divider()
    col_gaps, col_strengths = st.columns(2)

    with col_gaps:
        st.subheader("Gaps")
        if result.gaps:
            for gap in result.gaps:
                factor = gap["factor"].replace("_", " ").title()
                dim = gap["dimension"]
                score = gap["score"]
                if score == 0:
                    st.markdown(f"- **{factor}** ({dim}): :red[Missing]")
                else:
                    st.markdown(f"- **{factor}** ({dim}): :orange[{score:.1f}/10]")
        else:
            st.success("No gaps found!")

    with col_strengths:
        st.subheader("Strengths")
        if result.strengths:
            for s in result.strengths:
                factor = s["factor"].replace("_", " ").title()
                dim = s["dimension"]
                score = s["score"]
                st.markdown(f"- **{factor}** ({dim}): :green[{score:.1f}/10]")
        else:
            st.info("No outstanding strengths detected.")

    # ----- School recommendations -----
    st.divider()
    st.subheader("School Recommendations")

    for category, color, label in [
        ("reach", "red", "Reach"),
        ("target", "orange", "Target"),
        ("safety", "green", "Safety"),
    ]:
        schools = rankings.get(category, [])
        if not schools:
            continue
        with st.expander(f":{color}[{label}] ({len(schools)} programs)", expanded=True):
            for sch in schools:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{sch['name']}** -- {sch['university']}")
                c2.write(f"Fit: {sch['fit_score']:.1f}/100")
                c3.write(f"Prereq: {sch['prereq_match_score']:.0%}")


# ===================================================================
# Page 2: Program Explorer
# ===================================================================

def page_program_explorer() -> None:
    st.header("Program Explorer")

    programs = _load_programs()

    if not programs:
        st.warning("No programs found in the database.")
        return

    rows = []
    for p in programs:
        rows.append({
            "Name": p.name,
            "University": p.university,
            "Rank": p.quantnet_ranking if p.quantnet_ranking else None,
            "Class Size": p.class_size if p.class_size else None,
            "Acceptance Rate": f"{p.acceptance_rate:.0%}" if p.acceptance_rate else "N/A",
            "Avg Salary": f"${p.avg_base_salary:,}" if p.avg_base_salary else "N/A",
            "Emp 3m": f"{p.employment_rate_3m:.0%}" if p.employment_rate_3m else "N/A",
            "Tuition": f"${p.tuition_total:,}" if p.tuition_total else "N/A",
            "GRE": "Required" if p.gre_required else "Optional",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Detail expanders
    st.divider()
    st.subheader("Program Details")

    selected_name = st.selectbox(
        "Select a program for details",
        options=[p.name for p in programs],
    )

    if selected_name:
        prog = next(p for p in programs if p.name == selected_name)

        with st.expander(f"{prog.name} -- {prog.university}", expanded=True):
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Class Size", prog.class_size or "N/A")
            d2.metric(
                "Acceptance Rate",
                f"{prog.acceptance_rate:.0%}" if prog.acceptance_rate else "N/A",
            )
            d3.metric(
                "Avg Salary",
                f"${prog.avg_base_salary:,}" if prog.avg_base_salary else "N/A",
            )
            d4.metric(
                "Employment 3m",
                f"{prog.employment_rate_3m:.0%}" if prog.employment_rate_3m else "N/A",
            )

            st.markdown("**Required Prerequisites:**")
            if prog.prerequisites_required:
                for pr in prog.prerequisites_required:
                    grade_note = f" (min grade: {pr.min_grade})" if pr.min_grade else ""
                    st.markdown(f"- {pr.category.replace('_', ' ').title()}{grade_note}")
            else:
                st.write("None listed.")

            st.markdown("**Recommended Prerequisites:**")
            if prog.prerequisites_recommended:
                for pr in prog.prerequisites_recommended:
                    note = f" -- {pr.note}" if pr.note else ""
                    st.markdown(
                        f"- {pr.category.replace('_', ' ').title()}{note}"
                    )
            else:
                st.write("None listed.")

            if prog.languages:
                st.markdown(f"**Languages:** {', '.join(prog.languages)}")

            if prog.deadline_rounds:
                st.markdown("**Deadlines:**")
                for rd in prog.deadline_rounds:
                    decision = f" (decision by {rd.decision_by})" if rd.decision_by else ""
                    st.markdown(f"- Round {rd.round}: {rd.date}{decision}")

            if prog.website:
                st.markdown(f"[Program Website]({prog.website})")


# ===================================================================
# Page 3: Program Comparison
# ===================================================================

def page_program_comparison() -> None:
    st.header("Program Comparison")

    programs = _load_programs()
    if not programs:
        st.warning("No programs found in the database.")
        return

    prog_names = [p.name for p in programs]
    selected = st.multiselect(
        "Select up to 3 programs to compare",
        options=prog_names,
        max_selections=3,
    )

    if len(selected) < 2:
        st.info("Select at least 2 programs (up to 3) to compare.")
        return

    progs_by_name = {p.name: p for p in programs}
    chosen = [progs_by_name[n] for n in selected]

    # Build comparison columns
    header_cols = st.columns([2] + [1] * len(chosen))
    header_cols[0].markdown("**Attribute**")
    for i, prog in enumerate(chosen):
        header_cols[i + 1].markdown(f"**{prog.name}**")

    st.divider()

    def _comparison_row(label: str, values: list[str]) -> None:
        cols = st.columns([2] + [1] * len(values))
        cols[0].write(label)
        for i, v in enumerate(values):
            cols[i + 1].write(v)

    _comparison_row("University", [p.university for p in chosen])

    _comparison_row(
        "Class Size",
        [str(p.class_size) if p.class_size else "N/A" for p in chosen],
    )

    _comparison_row(
        "Acceptance Rate",
        [f"{p.acceptance_rate:.0%}" if p.acceptance_rate else "N/A" for p in chosen],
    )

    _comparison_row(
        "Avg GPA",
        [f"{p.avg_gpa:.2f}" if p.avg_gpa else "N/A" for p in chosen],
    )

    _comparison_row(
        "Tuition",
        [f"${p.tuition_total:,}" if p.tuition_total else "N/A" for p in chosen],
    )

    _comparison_row(
        "Avg Base Salary",
        [f"${p.avg_base_salary:,}" if p.avg_base_salary else "N/A" for p in chosen],
    )

    _comparison_row(
        "Employment (3m)",
        [f"{p.employment_rate_3m:.0%}" if p.employment_rate_3m else "N/A" for p in chosen],
    )

    _comparison_row(
        "GRE Required",
        ["Yes" if p.gre_required else "No" for p in chosen],
    )

    _comparison_row(
        "TOEFL Min (iBT)",
        [str(p.toefl_min_ibt) if p.toefl_min_ibt else "N/A" for p in chosen],
    )

    _comparison_row(
        "Application Fee",
        [f"${p.application_fee}" if p.application_fee else "N/A" for p in chosen],
    )

    _comparison_row(
        "Recommendations",
        [str(p.recommendations) if p.recommendations else "N/A" for p in chosen],
    )

    def _round_date(prog, round_num):
        for r in prog.deadline_rounds:
            if r.round == round_num:
                return r.date
        return "N/A"

    _comparison_row("Deadline Round 1", [_round_date(p, 1) for p in chosen])
    _comparison_row("Deadline Round 2", [_round_date(p, 2) for p in chosen])

    _comparison_row(
        "Prerequisites (req.)",
        [str(len(p.prerequisites_required)) for p in chosen],
    )

    _comparison_row(
        "Interview",
        [
            p.interview_type.replace("_", " ").title() if p.interview_type else "N/A"
            for p in chosen
        ],
    )


# ===================================================================
# Page 4: Gap Analysis
# ===================================================================

def page_gap_analysis() -> None:
    st.header("Gap Analysis")

    profile = _require_profile()
    if profile is None:
        return

    result = evaluate_profile(profile)

    if not result.gaps:
        st.success(
            "No gaps found -- your profile looks strong across all dimensions!"
        )
        return

    recommendations = analyze_gaps(result.gaps)

    # Summary metrics
    high_count = sum(1 for r in recommendations if r.priority == "High")
    med_count = sum(1 for r in recommendations if r.priority == "Medium")
    low_count = sum(1 for r in recommendations if r.priority == "Low")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Gaps", len(recommendations))
    m2.metric("High Priority", high_count)
    m3.metric("Medium Priority", med_count)
    m4.metric("Low Priority", low_count)

    st.divider()

    # Gaps table with color coding
    rows = []
    for rec in recommendations:
        if rec.score == 0:
            score_display = "Missing"
        else:
            score_display = f"{rec.score:.1f} / 10"

        rows.append({
            "Factor": rec.factor.replace("_", " ").title(),
            "Dimension": rec.dimension.replace("_", " ").title(),
            "Score": score_display,
            "Priority": rec.priority,
            "Recommended Action": rec.action,
        })

    # Use custom styling via column_config
    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Factor": st.column_config.TextColumn(width="medium"),
            "Dimension": st.column_config.TextColumn(width="small"),
            "Score": st.column_config.TextColumn(width="small"),
            "Priority": st.column_config.TextColumn(width="small"),
            "Recommended Action": st.column_config.TextColumn(width="large"),
        },
    )

    # Detailed cards by priority
    st.divider()
    st.subheader("Detailed Recommendations")

    for priority_label, color in [("High", "red"), ("Medium", "orange"), ("Low", "blue")]:
        prio_recs = [r for r in recommendations if r.priority == priority_label]
        if not prio_recs:
            continue
        with st.expander(
            f":{color}[{priority_label} Priority] ({len(prio_recs)} items)",
            expanded=(priority_label == "High"),
        ):
            for rec in prio_recs:
                factor_label = rec.factor.replace("_", " ").title()
                score_str = "Missing" if rec.score == 0 else f"{rec.score:.1f}/10"
                st.markdown(
                    f"**{factor_label}** ({rec.dimension}) -- Score: {score_str}"
                )
                st.markdown(f"> {rec.action}")
                st.markdown("---")


# ===================================================================
# Page 5: Application Timeline
# ===================================================================

def page_application_timeline() -> None:
    st.header("Application Timeline")

    programs = _load_programs()
    if not programs:
        st.warning("No programs found in the database.")
        return

    events = generate_timeline(programs, date.today())

    if not events:
        st.info("No timeline events generated. Programs may not have deadline data.")
        return

    # Group events by month
    months: dict[str, list[dict]] = {}
    for event in events:
        d = date.fromisoformat(event["date"])
        month_key = d.strftime("%Y-%m")
        month_label = d.strftime("%B %Y")
        if month_key not in months:
            months[month_key] = []
        event_copy = dict(event)
        event_copy["_date_obj"] = d
        event_copy["_month_label"] = month_label
        months[month_key].append(event_copy)

    priority_icons = {
        "critical": ":red_circle:",
        "high": ":orange_circle:",
        "medium": ":large_yellow_circle:",
        "low": ":large_blue_circle:",
    }

    for month_key in sorted(months.keys()):
        month_events = months[month_key]
        month_label = month_events[0]["_month_label"]
        with st.expander(f"{month_label} ({len(month_events)} events)", expanded=True):
            for event in month_events:
                d = event["_date_obj"]
                icon = priority_icons.get(event["priority"], ":white_circle:")
                priority_display = event["priority"].capitalize()
                category_display = event["category"].replace("_", " ").title()

                st.markdown(
                    f"{icon} **{d.strftime('%b %d')}** -- "
                    f"{event['action']}  \n"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"*{category_display}* | {priority_display}"
                )


# ===================================================================
# Page router
# ===================================================================

if page == "Profile Evaluation":
    page_profile_evaluation()
elif page == "Program Explorer":
    page_program_explorer()
elif page == "Program Comparison":
    page_program_comparison()
elif page == "Gap Analysis":
    page_gap_analysis()
elif page == "Application Timeline":
    page_application_timeline()

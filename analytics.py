# File: analytics.py
from typing import Dict, Any, Tuple, List
from datetime import date, datetime, timedelta
import plotly.graph_objects as go


def count_leaf_tasks_recursive(tasks: list) -> Tuple[int, int]:
    """
    Counts total actionable (leaf) tasks and completed leaf tasks across any nested depth.
    """
    total = 0
    completed = 0
    for t in tasks:
        subtasks = t.get("subtasks", [])
        if not subtasks:
            total += 1
            if t.get("completed", False):
                completed += 1
        else:
            sub_total, sub_comp = count_leaf_tasks_recursive(subtasks)
            total += sub_total
            completed += sub_comp
    return total, completed


def create_subject_bar_chart(data: Dict[str, Any], dark_mode: bool = True) -> go.Figure:
    """
    Builds a Bar Chart comparing overall completion percentages across
    Physics, Chemistry, and Mathematics, styled dynamically for Dark/Light mode.
    """
    subjects = list(data["subjects"].keys())
    progress_values = [data["subjects"][s]["progress"] for s in subjects]

    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    grid_color = "rgba(148, 163, 184, 0.2)" if dark_mode else "rgba(100, 116, 139, 0.2)"
    colors = ["#3B82F6", "#10B981", "#F59E0B"]  # Blue, Emerald, Amber

    fig = go.Figure(
        data=[
            go.Bar(
                x=subjects,
                y=progress_values,
                text=[f"{val:.1f}%" for val in progress_values],
                textposition="outside",
                textfont=dict(color=text_color, size=13),
                marker=dict(color=colors, line=dict(width=1.5, color=text_color)),
                width=0.45,
                hovertemplate="<b>%{x}</b><br>Overall Completion: %{y:.1f}%<extra></extra>"
            )
        ]
    )

    fig.update_layout(
        title=dict(text="📊 Overall Completion per Subject (%)", font=dict(size=17, color=text_color)),
        xaxis=dict(title="Subject", tickfont=dict(color=text_color), title_font=dict(color=text_color)),
        yaxis=dict(
            title="Completion Percentage (%)",
            range=[0, 115],
            gridcolor=grid_color,
            tickfont=dict(color=text_color),
            title_font=dict(color=text_color)
        ),
        margin=dict(l=30, r=30, t=55, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_chapter_donut_chart(
    chapter: Dict[str, Any],
    subject_name: str,
    dark_mode: bool = True
) -> go.Figure:
    """
    Builds a Donut Chart showing the exact completion percentage for an individual chapter.
    """
    completed_pct = round(chapter.get("progress", 0.0), 1)
    remaining_pct = round(max(0.0, 100.0 - completed_pct), 1)

    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    remaining_slice_color = "#334155" if dark_mode else "#E2E8F0"

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Completed", "Remaining"],
                values=[completed_pct, remaining_pct],
                hole=0.65,
                marker=dict(colors=["#10B981", remaining_slice_color]),
                textinfo="percent",
                textfont=dict(color=text_color),
                hoverinfo="label+percent",
                sort=False
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text=f"🎯 {subject_name}: {chapter['name']}",
            font=dict(size=16, color=text_color)
        ),
        annotations=[
            dict(
                text=f"<b>{completed_pct}%</b><br>Done",
                x=0.5,
                y=0.5,
                font=dict(size=19, color=text_color),
                showarrow=False
            )
        ],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(color=text_color)
        ),
        margin=dict(l=20, r=20, t=55, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_chapter_comparison_donut(
    data: Dict[str, Any],
    subject_name: str,
    dark_mode: bool = True
) -> go.Figure:
    """
    Builds a Donut Chart breaking down relative progress across all chapters in a subject.
    """
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    chapters = data["subjects"][subject_name].get("chapters", [])
    if not chapters:
        fig = go.Figure()
        fig.update_layout(title="No chapters available")
        return fig

    labels = [c["name"] for c in chapters]
    values = [max(c["progress"], 2.0) for c in chapters]
    real_progress = [c["progress"] for c in chapters]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                customdata=real_progress,
                texttemplate="%{customdata:.1f}%",
                textfont=dict(color=text_color),
                hovertemplate="<b>%{label}</b><br>Chapter Completion: %{customdata:.1f}%<extra></extra>"
            )
        ]
    )

    subj_prog = data["subjects"][subject_name]["progress"]
    fig.update_layout(
        title=dict(
            text=f"📚 {subject_name} — Chapter-wise Progress Breakdown",
            font=dict(size=16, color=text_color)
        ),
        annotations=[
            dict(
                text=f"<b>{subj_prog:.1f}%</b><br>Avg",
                x=0.5,
                y=0.5,
                font=dict(size=18, color=text_color),
                showarrow=False
            )
        ],
        legend=dict(font=dict(color=text_color)),
        margin=dict(l=20, r=20, t=55, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


# ---------------------------------------------------------------------------
# Study Heatmap & Analytics Charts
# ---------------------------------------------------------------------------

def create_study_heatmap(data: Dict[str, Any], dark_mode: bool = True) -> go.Figure:
    """
    Creates a calendar-accurate GitHub-style contribution heatmap showing study activity
    over the last 12 weeks, strictly aligning rows to Monday through Sunday.
    """
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    daily_log = data.get("daily_log", {})

    today = date.today()
    # Align to current week's Monday, then go back 11 full weeks (total 12 weeks)
    this_monday = today - timedelta(days=today.weekday())
    start_monday = this_monday - timedelta(weeks=11)

    num_weeks = 12
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    week_labels = []

    z_values = [[0 for _ in range(num_weeks)] for _ in range(7)]
    hover_texts = [["" for _ in range(num_weeks)] for _ in range(7)]

    for w in range(num_weeks):
        week_start = start_monday + timedelta(weeks=w)
        week_labels.append(f"W{w + 1}<br>{week_start.strftime('%b %d')}")

        for day_idx in range(7):
            d = week_start + timedelta(days=day_idx)
            if d > today:
                z_values[day_idx][w] = None
                hover_texts[day_idx][w] = f"{d.strftime('%a, %b %d')}: Future"
            else:
                date_str = d.isoformat()
                log_entry = daily_log.get(date_str, {})
                minutes = 0
                if isinstance(log_entry, dict):
                    if "minutes" in log_entry:
                        minutes = int(log_entry.get("minutes", 0))
                    elif "subjects" in log_entry and isinstance(log_entry["subjects"], dict):
                        minutes = sum(v for v in log_entry["subjects"].values() if isinstance(v, (int, float)))
                    else:
                        minutes = sum(v for k, v in log_entry.items() if k != "tasks_done" and isinstance(v, (int, float)))
                z_values[day_idx][w] = minutes
                hover_texts[day_idx][w] = f"<b>{d.strftime('%a, %b %d, %Y')}</b><br>{minutes} mins studied"

    no_activity_color = "#1E293B" if dark_mode else "#E2E8F0"
    colorscale = [
        [0.0, no_activity_color],
        [0.01, "#065F46" if dark_mode else "#A7F3D0"],
        [0.25, "#047857" if dark_mode else "#6EE7B7"],
        [0.50, "#059669" if dark_mode else "#34D399"],
        [0.75, "#10B981" if dark_mode else "#10B981"],
        [1.0, "#34D399" if dark_mode else "#047857"],
    ]

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=z_values,
                x=week_labels,
                y=day_labels,
                text=hover_texts,
                hoverinfo="text",
                colorscale=colorscale,
                showscale=True,
                colorbar=dict(
                    title=dict(text="Minutes", font=dict(color=text_color)),
                    tickfont=dict(color=text_color),
                ),
                xgap=3,
                ygap=3,
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="🟩 Study Activity Heatmap (Last 12 Weeks)",
            font=dict(size=17, color=text_color),
        ),
        xaxis=dict(
            tickfont=dict(color=text_color, size=10),
            showgrid=False,
            side="top",
        ),
        yaxis=dict(
            tickfont=dict(color=text_color),
            showgrid=False,
            autorange="reversed",
        ),
        margin=dict(l=50, r=30, t=80, b=20),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def create_subject_time_pie(data: Dict[str, Any], dark_mode: bool = True) -> go.Figure:
    """
    Creates a donut/pie chart showing total time spent per subject,
    aggregated from all daily_log entries, with a clean empty state.
    """
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    remaining_slice_color = "#334155" if dark_mode else "#E2E8F0"

    daily_log = data.get("daily_log", {})
    subject_names = ["Physics", "Chemistry", "Mathematics"]
    subject_colors = ["#3B82F6", "#10B981", "#F59E0B"]
    key_map = {s.lower(): s for s in subject_names}

    totals = {s: 0.0 for s in subject_names}
    for date_str, entry in daily_log.items():
        if not isinstance(entry, dict):
            continue
        subjects_dict = entry.get("subjects") if isinstance(entry.get("subjects"), dict) else entry
        for key, val in subjects_dict.items():
            canonical = key_map.get(key.lower())
            if canonical and isinstance(val, (int, float)):
                totals[canonical] += val

    values = [totals[name] for name in subject_names]
    total_mins = sum(values)

    if total_mins == 0:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["No Study Time Yet"],
                    values=[1],
                    hole=0.55,
                    marker=dict(colors=[remaining_slice_color]),
                    textinfo="label",
                    textfont=dict(color=text_color),
                    hoverinfo="none",
                    showlegend=False
                )
            ]
        )
        fig.update_layout(
            title=dict(text="⏱️ Subject Time Distribution", font=dict(size=17, color=text_color)),
            annotations=[
                dict(
                    text="Start Pomodoro<br>to Log Hours",
                    x=0.5, y=0.5,
                    font=dict(size=13, color=text_color),
                    showarrow=False
                )
            ],
            margin=dict(l=30, r=30, t=55, b=40),
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    hours_text = [f"{v / 60:.1f}h" for v in values]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=subject_names,
                values=values,
                hole=0.55,
                marker=dict(colors=subject_colors),
                texttemplate="%{label}<br>%{customdata}<br>%{percent}",
                customdata=hours_text,
                textfont=dict(color=text_color),
                hovertemplate="<b>%{label}</b><br>%{customdata} (%{percent})<extra></extra>",
                sort=False,
            )
        ]
    )

    total_hours = total_mins / 60
    fig.update_layout(
        title=dict(
            text="⏱️ Subject Time Distribution",
            font=dict(size=17, color=text_color),
        ),
        annotations=[
            dict(
                text=f"<b>{total_hours:.1f}h</b><br>Total",
                x=0.5,
                y=0.5,
                font=dict(size=18, color=text_color),
                showarrow=False,
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(color=text_color),
        ),
        margin=dict(l=30, r=30, t=55, b=50),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def create_weekly_trend_chart(data: Dict[str, Any], dark_mode: bool = True) -> go.Figure:
    """
    Shows daily study minutes for the last 14 days as an interactive line chart,
    with a dashed reference line for the user's daily study goal.
    """
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    grid_color = "rgba(148, 163, 184, 0.2)" if dark_mode else "rgba(100, 116, 139, 0.2)"

    daily_log = data.get("daily_log", {})
    today = date.today()
    num_days = 14
    dates = [today - timedelta(days=offset) for offset in range(num_days - 1, -1, -1)]

    date_labels = []
    minutes_values = []
    for d in dates:
        date_str = d.isoformat()
        date_labels.append(d.strftime("%b %d"))
        entry = daily_log.get(date_str, {})
        m = 0
        if isinstance(entry, dict):
            if "minutes" in entry:
                m = int(entry.get("minutes", 0))
            elif "subjects" in entry and isinstance(entry["subjects"], dict):
                m = sum(v for v in entry["subjects"].values() if isinstance(v, (int, float)))
            else:
                m = sum(v for k, v in entry.items() if k != "tasks_done" and isinstance(v, (int, float)))
        minutes_values.append(m)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=date_labels,
            y=minutes_values,
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
            marker=dict(size=7, color="#059669"),
            name="Minutes Studied",
            hovertemplate="<b>%{x}</b><br>%{y} minutes<extra></extra>",
        )
    )

    daily_goal_min = data.get("settings", {}).get("daily_goal_minutes", 360)
    fig.add_hline(
        y=daily_goal_min,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Goal: {daily_goal_min // 60}h {daily_goal_min % 60}m",
        annotation_position="top right",
        annotation_font=dict(color="#F59E0B", size=12),
    )

    max_y = max(max(minutes_values, default=0), daily_goal_min) + 60
    fig.update_layout(
        title=dict(
            text="📈 Daily Study Trend (Last 14 Days)",
            font=dict(size=17, color=text_color),
        ),
        xaxis=dict(
            title="Date",
            tickfont=dict(color=text_color),
            title_font=dict(color=text_color),
        ),
        yaxis=dict(
            title="Minutes",
            range=[0, max_y],
            gridcolor=grid_color,
            tickfont=dict(color=text_color),
            title_font=dict(color=text_color),
        ),
        margin=dict(l=40, r=30, t=55, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _count_leaf_tasks_by_difficulty_for_subject(tasks: list, counts: Dict[str, int]) -> None:
    """Recursively counts leaf tasks by difficulty for a single subject."""
    for t in tasks:
        subtasks = t.get("subtasks", [])
        if not subtasks:
            difficulty = t.get("difficulty", "Medium")
            if difficulty in counts:
                counts[difficulty] += 1
        else:
            _count_leaf_tasks_by_difficulty_for_subject(subtasks, counts)


def create_difficulty_distribution(data: Dict[str, Any], dark_mode: bool = True) -> go.Figure:
    """
    Creates a grouped bar chart showing the count of tasks by difficulty
    (Easy / Medium / Hard) for each subject.
    """
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    grid_color = "rgba(148, 163, 184, 0.2)" if dark_mode else "rgba(100, 116, 139, 0.2)"

    difficulty_colors = {
        "Easy": "#10B981",
        "Medium": "#F59E0B",
        "Hard": "#EF4444",
    }

    counts: Dict[str, Dict[str, int]] = {}
    subject_names = list(data.get("subjects", {}).keys())
    for subject_name in subject_names:
        counts[subject_name] = {"Easy": 0, "Medium": 0, "Hard": 0}
        chapters = data["subjects"][subject_name].get("chapters", [])
        for chapter in chapters:
            tasks = chapter.get("tasks", [])
            _count_leaf_tasks_by_difficulty_for_subject(tasks, counts[subject_name])

    fig = go.Figure()

    for difficulty in ["Easy", "Medium", "Hard"]:
        fig.add_trace(
            go.Bar(
                name=difficulty,
                x=subject_names,
                y=[counts[s][difficulty] for s in subject_names],
                marker_color=difficulty_colors[difficulty],
                text=[counts[s][difficulty] for s in subject_names],
                textposition="outside",
                textfont=dict(color=text_color),
                hovertemplate=f"<b>%{{x}}</b><br>{difficulty}: %{{y}} tasks<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="group",
        title=dict(
            text="🎯 Task Difficulty Distribution by Subject",
            font=dict(size=17, color=text_color),
        ),
        xaxis=dict(
            title="Subject",
            tickfont=dict(color=text_color),
            title_font=dict(color=text_color),
        ),
        yaxis=dict(
            title="Number of Tasks",
            gridcolor=grid_color,
            tickfont=dict(color=text_color),
            title_font=dict(color=text_color),
        ),
        legend=dict(
            font=dict(color=text_color),
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(l=40, r=30, t=55, b=60),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def create_mock_test_trend_chart(mock_tests: List[Dict[str, Any]], dark_mode: bool = True) -> go.Figure:
    """
    Creates a multi-line trend chart showing Mock Test scores over time,
    with Total Score out of 300 and subject breakdowns (Physics, Chem, Math),
    plus a benchmark target line (e.g. 180 Marks / 99%ile).
    """
    text_color = "#F8FAFC" if dark_mode else "#0F172A"
    grid_color = "rgba(148, 163, 184, 0.2)" if dark_mode else "rgba(100, 116, 139, 0.2)"

    fig = go.Figure()
    if not mock_tests:
        fig.add_annotation(
            text="No mock tests logged yet.<br>Log your test scores to see your JEE performance progression!",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=text_color)
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=360,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
        )
        return fig

    sorted_tests = sorted(mock_tests, key=lambda t: t.get("date", ""))
    test_labels = [f"{t.get('name', 'Test')}<br>{t.get('date', '')}" for t in sorted_tests]
    totals = [t.get("total_score", 0.0) for t in sorted_tests]
    phys = [t.get("physics", 0.0) for t in sorted_tests]
    chem = [t.get("chemistry", 0.0) for t in sorted_tests]
    maths = [t.get("mathematics", 0.0) for t in sorted_tests]

    # Total Score trace
    fig.add_trace(go.Scatter(
        x=test_labels,
        y=totals,
        mode="lines+markers",
        name="Total (out of 300)",
        line=dict(color="#38BDF8", width=3.5),
        marker=dict(size=9, color="#0284C7"),
        hovertemplate="<b>%{x}</b><br>Total: %{y}/300<extra></extra>"
    ))

    # Subject traces
    fig.add_trace(go.Scatter(
        x=test_labels,
        y=phys,
        mode="lines+markers",
        name="Physics",
        line=dict(color="#3B82F6", width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="Physics: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=test_labels,
        y=chem,
        mode="lines+markers",
        name="Chemistry",
        line=dict(color="#10B981", width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="Chemistry: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=test_labels,
        y=maths,
        mode="lines+markers",
        name="Mathematics",
        line=dict(color="#F59E0B", width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="Mathematics: %{y}<extra></extra>"
    ))

    # Target Benchmark line (180 Marks)
    fig.add_hline(
        y=180,
        line_dash="dash",
        line_color="#E11D48",
        annotation_text="99%ile Target (~180 M)",
        annotation_position="top left",
        annotation_font=dict(color="#E11D48", size=11)
    )

    min_y = min([0.0] + totals + phys + chem + maths) - 10
    max_y = max([310.0] + totals) + 15

    fig.update_layout(
        title=dict(text="📈 Mock Test Performance & Score Trend", font=dict(size=17, color=text_color)),
        xaxis=dict(title="Mock Test", tickfont=dict(color=text_color), title_font=dict(color=text_color)),
        yaxis=dict(title="Score", range=[min_y, max_y], gridcolor=grid_color, tickfont=dict(color=text_color), title_font=dict(color=text_color)),
        legend=dict(font=dict(color=text_color), orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=40, r=30, t=55, b=70)
    )
    return fig
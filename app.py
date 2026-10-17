# File: app.py
import json
import time
import os
import re
import base64
import importlib
from datetime import datetime, date, timedelta
import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, List, Optional

import data_manager as dm
importlib.reload(dm)
import analytics as an
importlib.reload(an)


def normalize_youtube_url(url: str) -> str:
    """Extracts YouTube video ID and returns standard watch URL compatible with Streamlit."""
    url = url.strip()
    if not url:
        return ""
    shorts_match = re.search(r"youtube\.com/shorts/([a-zA-Z0-9_-]+)", url)
    if shorts_match:
        return f"https://www.youtube.com/watch?v={shorts_match.group(1)}"
    short_domain_match = re.search(r"youtu\.be/([a-zA-Z0-9_-]+)", url)
    if short_domain_match:
        return f"https://www.youtube.com/watch?v={short_domain_match.group(1)}"
    embed_match = re.search(r"youtube\.com/embed/([a-zA-Z0-9_-]+)", url)
    if embed_match:
        return f"https://www.youtube.com/watch?v={embed_match.group(1)}"
    watch_match = re.search(r"[?&]v=([a-zA-Z0-9_-]+)", url)
    if watch_match:
        return f"https://www.youtube.com/watch?v={watch_match.group(1)}"
    return url


def render_pdf_viewer_component(pdf_bytes: bytes, filename: str = "document.pdf", height: int = 700) -> None:
    """Renders a responsive, interactive in-app PDF reader with page controls and zoom using PDF.js."""
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #0F172A;
                color: #F8FAFC;
                padding: 6px;
                overflow: hidden;
            }}
            .toolbar {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                background: #1E293B;
                padding: 8px 12px;
                border-radius: 8px;
                border: 1px solid #334155;
                margin-bottom: 8px;
            }}
            .btn-group {{
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            button {{
                background: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
                cursor: pointer;
                transition: background 0.15s, border-color 0.15s;
                font-weight: 600;
            }}
            button:hover {{
                background: #3B82F6;
                border-color: #2563EB;
                color: #FFFFFF;
            }}
            button:disabled {{
                opacity: 0.4;
                cursor: not-allowed;
            }}
            .page-info {{
                font-size: 13px;
                font-weight: 600;
                color: #CBD5E1;
                margin: 0 4px;
            }}
            #pdf-container {{
                width: 100%;
                height: {height - 80}px;
                overflow: auto;
                background: #020617;
                border: 1px solid #334155;
                border-radius: 8px;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 12px 6px;
            }}
            #pdf-canvas {{
                box-shadow: 0 4px 14px rgba(0,0,0,0.5);
                border-radius: 4px;
                max-width: 100%;
            }}
            #loading-msg {{
                color: #94A3B8;
                font-size: 13px;
                margin-top: 30px;
            }}
            #fallback-embed {{
                display: none;
                width: 100%;
                height: 100%;
                border: none;
            }}
        </style>
    </head>
    <body>
        <div class="toolbar">
            <div class="btn-group">
                <button id="prev-btn" onclick="onPrevPage()">◀ Prev</button>
                <span class="page-info">Page <span id="page-num">1</span> / <span id="page-count">-</span></span>
                <button id="next-btn" onclick="onNextPage()">Next ▶</button>
            </div>
            <div class="btn-group">
                <button onclick="zoomOut()">🔍 -</button>
                <button onclick="zoomReset()">100%</button>
                <button onclick="zoomIn()">🔍 +</button>
                <button onclick="fitWidth()">⤢ Fit Width</button>
            </div>
            <div class="btn-group">
                <button id="open-tab-btn" onclick="openInNewTab()">↗ Open in New Tab</button>
            </div>
        </div>

        <div id="pdf-container">
            <div id="loading-msg">⏳ Rendering PDF preview...</div>
            <canvas id="pdf-canvas" style="display:none;"></canvas>
            <embed id="fallback-embed" type="application/pdf" />
        </div>

        <script>
            const b64Data = "{b64_pdf}";
            let pdfDoc = null;
            let pageNum = 1;
            let pageRendering = false;
            let pageNumPending = null;
            let scale = 1.2;
            const canvas = document.getElementById('pdf-canvas');
            const ctx = canvas.getContext('2d');
            const loadingMsg = document.getElementById('loading-msg');
            let pdfBlobUrl = null;

            try {{
                const byteCharacters = atob(b64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {{
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }}
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], {{ type: 'application/pdf' }});
                pdfBlobUrl = URL.createObjectURL(blob);
            }} catch (e) {{
                console.error("Blob error:", e);
            }}

            function openInNewTab() {{
                if (pdfBlobUrl) {{
                    window.open(pdfBlobUrl, '_blank');
                }} else {{
                    const win = window.open();
                    win.document.write('<iframe src="data:application/pdf;base64,' + b64Data + '" frameborder="0" style="border:0; top:0; left:0; bottom:0; right:0; width:100%; height:100%;" allowfullscreen></iframe>');
                }}
            }}

            function renderPage(num) {{
                pageRendering = true;
                pdfDoc.getPage(num).then(function(page) {{
                    const viewport = page.getViewport({{ scale: scale }});
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;

                    const renderContext = {{
                        canvasContext: ctx,
                        viewport: viewport
                    }};
                    const renderTask = page.render(renderContext);

                    renderTask.promise.then(function() {{
                        pageRendering = false;
                        canvas.style.display = 'block';
                        loadingMsg.style.display = 'none';
                        if (pageNumPending !== null) {{
                            renderPage(pageNumPending);
                            pageNumPending = null;
                        }}
                    }}).catch(function(err) {{
                        console.error("Render error:", err);
                    }});
                }});

                document.getElementById('page-num').textContent = num;
                document.getElementById('prev-btn').disabled = (num <= 1);
                document.getElementById('next-btn').disabled = (num >= pdfDoc.numPages);
            }}

            function queueRenderPage(num) {{
                if (pageRendering) {{
                    pageNumPending = num;
                }} else {{
                    renderPage(num);
                }}
            }}

            function onPrevPage() {{
                if (pageNum <= 1) return;
                pageNum--;
                queueRenderPage(pageNum);
            }}

            function onNextPage() {{
                if (pageNum >= pdfDoc.numPages) return;
                pageNum++;
                queueRenderPage(pageNum);
            }}

            function zoomIn() {{
                scale += 0.2;
                queueRenderPage(pageNum);
            }}

            function zoomOut() {{
                if (scale > 0.4) {{
                    scale -= 0.2;
                    queueRenderPage(pageNum);
                }}
            }}

            function zoomReset() {{
                scale = 1.2;
                queueRenderPage(pageNum);
            }}

            function fitWidth() {{
                const container = document.getElementById('pdf-container');
                const availableWidth = container.clientWidth - 40;
                if (pdfDoc && availableWidth > 100) {{
                    pdfDoc.getPage(pageNum).then(function(page) {{
                        const unscaledViewport = page.getViewport({{ scale: 1.0 }});
                        scale = Math.max(0.4, (availableWidth / unscaledViewport.width));
                        queueRenderPage(pageNum);
                    }});
                }}
            }}

            if (typeof pdfjsLib !== 'undefined') {{
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                
                try {{
                    const rawData = atob(b64Data);
                    const uint8Array = new Uint8Array(rawData.length);
                    for (let i = 0; i < rawData.length; i++) {{
                        uint8Array[i] = rawData.charCodeAt(i);
                    }}

                    pdfjsLib.getDocument({{ data: uint8Array }}).promise.then(function(pdfDoc_) {{
                        pdfDoc = pdfDoc_;
                        document.getElementById('page-count').textContent = pdfDoc.numPages;
                        renderPage(pageNum);
                    }}).catch(function(err) {{
                        console.warn("PDF.js parse failed, falling back to embed:", err);
                        fallbackToEmbed();
                    }});
                }} catch (e) {{
                    console.warn("Decode failed:", e);
                    fallbackToEmbed();
                }}
            }} else {{
                fallbackToEmbed();
            }}

            function fallbackToEmbed() {{
                loadingMsg.style.display = 'none';
                const embed = document.getElementById('fallback-embed');
                embed.src = pdfBlobUrl || ("data:application/pdf;base64," + b64Data);
                embed.style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=False)


# =====================================================================
# PAGE CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="JEE 2028 Study Tracker",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# SESSION STATE INITIALIZATION
# =====================================================================
if "study_data" not in st.session_state:
    st.session_state.study_data = dm.load_data()
    dm.ensure_daily_focus(st.session_state.study_data)

if "collapsed_tasks" not in st.session_state:
    st.session_state.collapsed_tasks = set()

if "expand_all_chapters" not in st.session_state:
    st.session_state.expand_all_chapters = False

if "active_subtask_input" not in st.session_state:
    st.session_state.active_subtask_input = None

if "active_edit_task" not in st.session_state:
    st.session_state.active_edit_task = None

if "active_edit_chapter" not in st.session_state:
    st.session_state.active_edit_chapter = None

# Pomodoro Session State
if "pomo_mode" not in st.session_state:
    st.session_state.pomo_mode = "25m Classic Focus"
if "pomo_subject" not in st.session_state:
    st.session_state.pomo_subject = "General Focus"
if "pomo_total_sec" not in st.session_state:
    st.session_state.pomo_total_sec = 25 * 60
if "pomo_remaining_sec" not in st.session_state:
    st.session_state.pomo_remaining_sec = 25 * 60
if "pomo_running" not in st.session_state:
    st.session_state.pomo_running = False
if "pomo_end_timestamp" not in st.session_state:
    st.session_state.pomo_end_timestamp = None
if "pomo_play_chime" not in st.session_state:
    st.session_state.pomo_play_chime = False

# =====================================================================
# THEME INJECTION & STYLES (DARK / LIGHT DYNAMIC THEME)
# =====================================================================
def inject_custom_styles(dark_mode: bool) -> None:
    """Injects high-contrast CSS styled for focused JEE study with Dark/Light support."""
    if dark_mode:
        bg_main = "#0F172A"
        bg_sidebar = "#1E293B"
        bg_card = "#1E293B"
        text_primary = "#F8FAFC"
        text_muted = "#94A3B8"
        border_col = "#334155"
        banner_bg = "linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%)"
    else:
        bg_main = "#F8FAFC"
        bg_sidebar = "#F1F5F9"
        bg_card = "#FFFFFF"
        text_primary = "#0F172A"
        text_muted = "#475569"
        border_col = "#CBD5E1"
        banner_bg = "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_main} !important;
            color: {text_primary} !important;
        }}
        [data-testid="stHeader"] {{
            background-color: {bg_main} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            border-right: 1px solid {border_col} !important;
        }}
        .stMarkdown, .stText, p, span, label, h1, h2, h3, h4, h5, h6 {{
            color: {text_primary};
        }}
        [data-testid="stExpander"] {{
            background-color: {bg_card} !important;
            border: 1px solid {border_col} !important;
            border-radius: 10px !important;
        }}

        /* Countdown Banner */
        .countdown-banner {{
            background: {banner_bg};
            border: 1px solid {border_col};
            border-radius: 12px;
            padding: 14px 20px;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .countdown-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {text_primary};
        }}
        .countdown-sub {{
            font-size: 0.82rem;
            color: {text_muted};
        }}
        .countdown-boxes {{
            display: flex;
            gap: 10px;
        }}
        .cd-box {{
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 8px;
            padding: 6px 12px;
            text-align: center;
            min-width: 68px;
        }}
        .cd-num {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #3B82F6;
            line-height: 1.2;
        }}
        .cd-lbl {{
            font-size: 0.7rem;
            text-transform: uppercase;
            color: {text_muted};
            font-weight: 600;
        }}

        /* Pomodoro Clock Display */
        .pomo-clock {{
            font-size: 2.3rem;
            font-weight: 800;
            text-align: center;
            font-family: monospace;
            padding: 8px 0;
            margin: 6px 0;
            border-radius: 10px;
            background: rgba(59, 130, 246, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.35);
            color: #3B82F6;
        }}

        /* Completion Badges */
        .task-badge-done {{
            background-color: rgba(16, 185, 129, 0.18);
            color: #10B981;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.76rem;
            font-weight: 600;
        }}
        .task-badge-prog {{
            background-color: rgba(59, 130, 246, 0.18);
            color: #3B82F6;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.76rem;
            font-weight: 600;
        }}
        .task-badge-todo {{
            background-color: rgba(148, 163, 184, 0.18);
            color: {text_muted};
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.76rem;
            font-weight: 600;
        }}

        /* Priority Badges */
        .prio-high {{
            background-color: rgba(239, 68, 68, 0.18);
            color: #EF4444;
            border: 1px solid rgba(239, 68, 68, 0.35);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.74rem;
            font-weight: 700;
        }}
        .prio-medium {{
            background-color: rgba(245, 158, 11, 0.18);
            color: #F59E0B;
            border: 1px solid rgba(245, 158, 11, 0.35);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.74rem;
            font-weight: 700;
        }}
        .prio-low {{
            background-color: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.74rem;
            font-weight: 700;
        }}

        /* Difficulty Badges */
        .diff-hard {{
            background-color: rgba(220, 38, 38, 0.18);
            color: #F87171;
            border: 1px solid rgba(220, 38, 38, 0.35);
            padding: 2px 7px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .diff-med {{
            background-color: rgba(217, 119, 6, 0.18);
            color: #FBBF24;
            border: 1px solid rgba(217, 119, 6, 0.35);
            padding: 2px 7px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .diff-easy {{
            background-color: rgba(5, 150, 105, 0.18);
            color: #34D399;
            border: 1px solid rgba(5, 150, 105, 0.35);
            padding: 2px 7px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 700;
        }}

        /* Weightage Badges */
        .weight-high {{
            background-color: rgba(239, 68, 68, 0.18);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.74rem;
            font-weight: 700;
        }}
        .weight-medium {{
            background-color: rgba(59, 130, 246, 0.18);
            color: #60A5FA;
            border: 1px solid rgba(59, 130, 246, 0.4);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.74rem;
            font-weight: 700;
        }}
        .weight-low {{
            background-color: rgba(148, 163, 184, 0.18);
            color: #94A3B8;
            border: 1px solid rgba(148, 163, 184, 0.4);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.74rem;
            font-weight: 700;
        }}

        /* Due Date Badges */
        .due-overdue {{
            background-color: rgba(239, 68, 68, 0.22);
            color: #EF4444;
            border: 1px solid #EF4444;
            padding: 2px 7px;
            border-radius: 10px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .due-today {{
            background-color: rgba(245, 158, 11, 0.22);
            color: #F59E0B;
            border: 1px solid #F59E0B;
            padding: 2px 7px;
            border-radius: 10px;
            font-size: 0.72rem;
            font-weight: 700;
        }}
        .due-future {{
            background-color: rgba(59, 130, 246, 0.18);
            color: #38BDF8;
            border: 1px solid rgba(59, 130, 246, 0.4);
            padding: 2px 7px;
            border-radius: 10px;
            font-size: 0.72rem;
            font-weight: 600;
        }}

        /* Milestone Badges */
        .badge-pill {{
            display: inline-block;
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.35);
            border-radius: 16px;
            padding: 4px 10px;
            margin: 3px;
            font-size: 0.78rem;
            font-weight: 600;
        }}

        /* Streak Pill */
        .streak-pill {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(245, 158, 11, 0.2) 100%);
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 12px;
            padding: 6px 14px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# =====================================================================
# HELPER FUNCTIONS (COUNTDOWN, BADGES, CHECKBOX CALLBACK)
# =====================================================================
def get_jee_countdown() -> Dict[str, int]:
    """Calculates time remaining until Week 4 of January 2028 (Jan 24, 2028, 9:00 AM)."""
    target_dt = datetime(2028, 1, 24, 9, 0, 0)
    now_dt = datetime.now()
    delta = target_dt - now_dt

    if delta.total_seconds() <= 0:
        return {"days": 0, "weeks": 0, "hours": 0, "minutes": 0, "seconds": 0}

    total_seconds = int(delta.total_seconds())
    days = delta.days
    weeks = days // 7
    rem_seconds = total_seconds % 86400
    hours = rem_seconds // 3600
    minutes = (rem_seconds % 3600) // 60
    seconds = rem_seconds % 60
    return {"days": days, "weeks": weeks, "hours": hours, "minutes": minutes, "seconds": seconds}


def render_top_countdown_banner() -> None:
    """Renders the JEE 2028 countdown banner with streak and daily goal tracker."""
    data = st.session_state.study_data
    cd = get_jee_countdown()
    streak = dm.get_streak(data)
    today_mins = dm.get_today_minutes(data)
    goal_mins = dm.get_daily_goal(data)
    goal_hrs = goal_mins / 60.0
    today_hrs = today_mins / 60.0
    goal_pct = min(round((today_mins / max(1, goal_mins)) * 100, 1), 100.0)

    st.markdown(
        f"""
        <div class="countdown-banner">
            <div>
                <div class="countdown-title">⏳ Target: JEE Main 2028 — Week 4 of January (Jan 24, 2028)</div>
                <div class="countdown-sub">
                    🔥 <b>{streak['current']}-Day Streak</b> (Best: {streak['best']}d) • 
                    🎯 Today's Goal: <b>{today_hrs:.1f}h / {goal_hrs:.1f}h</b> ({goal_pct}%) • 
                    ~{cd['weeks']} weeks remaining
                </div>
            </div>
            <div class="countdown-boxes">
                <div class="cd-box"><div class="cd-num">{cd['days']}</div><div class="cd-lbl">Days</div></div>
                <div class="cd-box"><div class="cd-num">{cd['hours']:02d}</div><div class="cd-lbl">Hours</div></div>
                <div class="cd-box"><div class="cd-num">{cd['minutes']:02d}</div><div class="cd-lbl">Mins</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_status_badge(progress: float) -> str:
    """Returns an HTML badge showing the percentage and status color."""
    if progress >= 100.0:
        return '<span class="task-badge-done">✔ 100%</span>'
    elif progress > 0.0:
        return f'<span class="task-badge-prog">⚡ {progress:.1f}%</span>'
    else:
        return '<span class="task-badge-todo">0%</span>'


def get_priority_badge(priority: str) -> str:
    """Returns a styled HTML pill badge for High, Medium, or Low priority."""
    p = priority.capitalize() if priority else "Medium"
    if p == "High":
        return '<span class="prio-high">🔥 High</span>'
    elif p == "Low":
        return '<span class="prio-low">🌱 Low</span>'
    return '<span class="prio-medium">⚡ Med</span>'


def get_difficulty_badge(difficulty: str) -> str:
    """Returns a styled HTML pill badge for Easy, Medium, or Hard difficulty."""
    d = difficulty.capitalize() if difficulty else "Medium"
    if d == "Hard":
        return '<span class="diff-hard">🔴 Hard</span>'
    elif d == "Easy":
        return '<span class="diff-easy">🟢 Easy</span>'
    return '<span class="diff-med">🟡 Med</span>'


def get_weightage_badge(weightage: str) -> str:
    """Returns a styled badge representing expected JEE marks weightage."""
    w = weightage if weightage else "Medium (4-8 M)"
    if "High" in w:
        return f'<span class="weight-high">🎯 {w}</span>'
    elif "Low" in w:
        return f'<span class="weight-low">🎯 {w}</span>'
    return f'<span class="weight-medium">🎯 {w}</span>'


def get_due_date_badge(due_date: str, completed: bool = False) -> str:
    """Returns a color-coded due date tag with overdue and today alerts."""
    if not due_date or completed:
        return ""
    try:
        target = date.fromisoformat(due_date)
        today = date.today()
        if target < today:
            return f'<span class="due-overdue">🚨 Overdue ({target.strftime("%b %d")})</span>'
        elif target == today:
            return '<span class="due-today">⏰ Due Today</span>'
        else:
            return f'<span class="due-future">📅 Due {target.strftime("%b %d")}</span>'
    except Exception:
        return ""


def on_checkbox_change(subject: str, chapter_id: str, task_id: str) -> None:
    """Triggered immediately when any task or subtask checkbox is clicked."""
    checkbox_key = f"chk_{task_id}"
    new_val = st.session_state.get(checkbox_key, False)
    just_finished = dm.toggle_task(st.session_state.study_data, subject, chapter_id, task_id, new_val)
    if just_finished:
        st.session_state["toast_msg"] = "🎉 Chapter 100% complete! Spaced revision (+1d, +3d, +7d, +21d) auto-scheduled!"


def on_daily_focus_change(item_key: str) -> None:
    """Syncs the daily planner checkbox with persisted state and the underlying syllabus task."""
    checkbox_key = f"daily_focus_{item_key}"
    new_val = st.session_state.get(checkbox_key, False)
    just_finished = dm.toggle_daily_focus_item(st.session_state.study_data, item_key, new_val)
    if just_finished:
        st.session_state["toast_msg"] = "🎉 Chapter 100% complete! Spaced revision (+1d, +3d, +7d, +21d) auto-scheduled!"


# =====================================================================
# POMODORO TIMER FRAGMENT (WITH AUDIO ALERT & ACCURATE LOGGING)
# =====================================================================
pomo_refresh_interval = 1.0 if st.session_state.pomo_running else None


@st.fragment(run_every=pomo_refresh_interval)
def render_pomodoro_widget() -> None:
    """
    Renders an interactive Pomodoro timer that updates every 1 second when active
    without causing full-page reloads, with subject tagging and audio chime alert.
    """
    st.markdown("##### 🍅 Pomodoro Study Timer")

    # Mode Selector
    selected_mode = st.selectbox(
        "Session Type",
        ["25m Classic Focus", "50m Deep Work", "5m Short Break", "15m Long Break"],
        index=["25m Classic Focus", "50m Deep Work", "5m Short Break", "15m Long Break"].index(st.session_state.pomo_mode),
        key="pomo_mode_select",
        label_visibility="collapsed"
    )

    # Subject tagging
    selected_subj = st.selectbox(
        "Tag Subject",
        ["General Focus", "Physics", "Chemistry", "Mathematics"],
        index=["General Focus", "Physics", "Chemistry", "Mathematics"].index(st.session_state.pomo_subject),
        key="pomo_subj_select"
    )
    st.session_state.pomo_subject = selected_subj

    if selected_mode != st.session_state.pomo_mode:
        st.session_state.pomo_mode = selected_mode
        duration_map = {
            "25m Classic Focus": 25 * 60,
            "50m Deep Work": 50 * 60,
            "5m Short Break": 5 * 60,
            "15m Long Break": 15 * 60
        }
        st.session_state.pomo_total_sec = duration_map[selected_mode]
        st.session_state.pomo_remaining_sec = duration_map[selected_mode]
        st.session_state.pomo_running = False
        st.session_state.pomo_end_timestamp = None
        st.rerun()

    # Countdown calculation
    if st.session_state.pomo_running and st.session_state.pomo_end_timestamp is not None:
        rem = int(st.session_state.pomo_end_timestamp - time.time())
        if rem <= 0:
            st.session_state.pomo_running = False
            st.session_state.pomo_end_timestamp = None
            st.session_state.pomo_play_chime = True

            if "Focus" in st.session_state.pomo_mode:
                mins_done = st.session_state.pomo_total_sec // 60
                tag_subject = None if st.session_state.pomo_subject == "General Focus" else st.session_state.pomo_subject
                dm.log_pomodoro_session(st.session_state.study_data, mins_done, subject=tag_subject)
                st.toast(f"🎉 Pomodoro complete! +{mins_done}m logged ({st.session_state.pomo_subject})!", icon="🔥")
            else:
                st.toast("⏰ Break finished! Ready for the next study block?", icon="⚡")

            st.session_state.pomo_remaining_sec = st.session_state.pomo_total_sec
            st.rerun()
        else:
            st.session_state.pomo_remaining_sec = rem

    # Web Audio API Two-Tone Chime Alert
    if st.session_state.get("pomo_play_chime", False):
        st.session_state.pomo_play_chime = False
        st.markdown(
            """
            <script>
            (function() {
                try {
                    const ctx = new (window.AudioContext || window.webkitAudioContext)();
                    const now = ctx.currentTime;
                    function playTone(freq, start, duration) {
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(freq, start);
                        gain.gain.setValueAtTime(0.25, start);
                        gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
                        osc.start(start);
                        osc.stop(start + duration);
                    }
                    playTone(659.25, now, 0.7); // E5
                    playTone(880.00, now + 0.18, 1.2); // A5
                } catch(e) {}
            })();
            </script>
            """,
            unsafe_allow_html=True
        )

    mins, secs = divmod(st.session_state.pomo_remaining_sec, 60)
    st.markdown(f'<div class="pomo-clock">{mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)

    # Progress bar
    elapsed_ratio = 1.0 - (st.session_state.pomo_remaining_sec / max(1, st.session_state.pomo_total_sec))
    st.progress(min(max(elapsed_ratio, 0.0), 1.0))

    # Controls
    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        if not st.session_state.pomo_running:
            if st.button("▶️ Start", use_container_width=True, type="primary"):
                st.session_state.pomo_running = True
                st.session_state.pomo_end_timestamp = time.time() + st.session_state.pomo_remaining_sec
                st.rerun()
        else:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.pomo_running = False
                st.session_state.pomo_end_timestamp = None
                st.rerun()

    with b_col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.pomo_running = False
            st.session_state.pomo_end_timestamp = None
            st.session_state.pomo_remaining_sec = st.session_state.pomo_total_sec
            st.rerun()

    with b_col3:
        if st.button("✅ Log", help="Finish & log this session now", use_container_width=True):
            elapsed_sec = st.session_state.pomo_total_sec - st.session_state.pomo_remaining_sec
            if elapsed_sec >= 60:
                mins_done = elapsed_sec // 60
            elif st.session_state.pomo_remaining_sec == 0:
                mins_done = st.session_state.pomo_total_sec // 60
            else:
                mins_done = 1

            tag_subject = None if st.session_state.pomo_subject == "General Focus" else st.session_state.pomo_subject
            dm.log_pomodoro_session(st.session_state.study_data, mins_done, subject=tag_subject)
            st.session_state.pomo_running = False
            st.session_state.pomo_end_timestamp = None
            st.session_state.pomo_remaining_sec = st.session_state.pomo_total_sec
            st.toast(f"Logged +{mins_done}m ({st.session_state.pomo_subject})!", icon="✅")
            st.rerun()

    # Stats Readout
    stats = st.session_state.study_data.get("pomodoro_stats", {"sessions_completed": 0, "total_minutes": 0})
    hours_focused = stats["total_minutes"] / 60.0
    st.caption(
        f"🔥 **Completed:** `{stats['sessions_completed']}` sessions "
        f"(`{stats['total_minutes']}m` / `{hours_focused:.1f} hrs`)"
    )


# =====================================================================
# RECURSIVE TASK TREE RENDERER (N-LEVEL INDENTATION)
# =====================================================================
def render_task_node(
    task: Dict[str, Any],
    subject: str,
    chapter_id: str,
    depth: int = 0,
    priority_filter: str = "All",
    difficulty_filter: str = "All"
) -> None:
    """Recursively displays tasks and subtasks with priority, difficulty, due dates, and deletion popovers."""
    task_id = task["id"]
    subtasks = task.get("subtasks", [])
    has_children = len(subtasks) > 0
    is_collapsed = task_id in st.session_state.collapsed_tasks
    task_prio = task.get("priority", "Medium")
    task_diff = task.get("difficulty", "Medium")
    task_due = task.get("due_date", "")

    # Filters
    if priority_filter != "All" and not has_children and task_prio != priority_filter:
        return
    if difficulty_filter != "All" and not has_children and task_diff != difficulty_filter:
        return

    chk_key = f"chk_{task_id}"

    if depth > 0:
        indent_width = min(depth * 0.35, 3.0)
        indent_cols = st.columns([indent_width, 10.0 - indent_width])
        container = indent_cols[1]
    else:
        container = st.container()

    with container:
        col_toggle, col_main, col_prio, col_diff, col_badge, col_add, col_edit, col_del = st.columns(
            [0.45, 4.0, 1.0, 1.0, 1.0, 0.7, 0.7, 0.7]
        )

        with col_toggle:
            if has_children:
                arrow = "▸" if is_collapsed else "▾"
                if st.button(arrow, key=f"exp_{task_id}", help="Expand / Collapse Subtasks"):
                    if is_collapsed:
                        st.session_state.collapsed_tasks.remove(task_id)
                    else:
                        st.session_state.collapsed_tasks.add(task_id)
                    st.rerun()
            else:
                st.markdown("<div style='padding-top:6px; color:#64748B;'>•</div>", unsafe_allow_html=True)

        with col_main:
            label_text = f"~~{task['title']}~~" if task["completed"] else task["title"]
            if has_children:
                label_text += f"  *(Subtasks: {len(subtasks)})*"
            if task.get("estimated_minutes", 0) > 0:
                label_text += f"  *(⏱️ {task['estimated_minutes']}m)*"

            st.checkbox(
                label_text,
                value=task["completed"],
                key=chk_key,
                on_change=on_checkbox_change,
                args=(subject, chapter_id, task_id)
            )
            due_badge = get_due_date_badge(task_due, task["completed"])
            if due_badge:
                st.markdown(f"<div style='margin-top:-6px; margin-bottom:4px;'>{due_badge}</div>", unsafe_allow_html=True)

        with col_prio:
            st.markdown(f"<div style='padding-top:5px;'>{get_priority_badge(task_prio)}</div>", unsafe_allow_html=True)

        with col_diff:
            st.markdown(f"<div style='padding-top:5px;'>{get_difficulty_badge(task_diff)}</div>", unsafe_allow_html=True)

        with col_badge:
            st.markdown(f"<div style='padding-top:5px;'>{get_status_badge(task['progress'])}</div>", unsafe_allow_html=True)

        with col_add:
            if st.button("➕", key=f"btn_add_sub_{task_id}", help="Add nested subtask"):
                st.session_state.active_subtask_input = None if st.session_state.active_subtask_input == task_id else task_id
                st.session_state.active_edit_task = None
                st.rerun()

        with col_edit:
            if st.button("✏️", key=f"btn_edit_task_{task_id}", help="Edit task details"):
                st.session_state.active_edit_task = None if st.session_state.active_edit_task == task_id else task_id
                st.session_state.active_subtask_input = None
                st.rerun()

        with col_del:
            with st.popover("🗑️", help="Delete task"):
                st.caption(f"Delete task '{task['title'][:20]}'?")
                if st.button("Delete", key=f"btn_del_task_{task_id}", type="primary", use_container_width=True):
                    dm.delete_task(st.session_state.study_data, subject, chapter_id, task_id)
                    st.toast(f"Deleted task '{task['title']}'")
                    st.rerun()

        # Inline Input: Add Subtask (with Priority, Difficulty, Due Date, and Estimated Duration)
        if st.session_state.active_subtask_input == task_id:
            sub_c1, sub_c2, sub_c3, sub_c4, sub_c_est, sub_c5 = st.columns([3.0, 1.3, 1.3, 1.3, 1.1, 1.0])
            with sub_c1:
                new_sub_title = st.text_input("New Subtask Title", key=f"input_sub_{task_id}", placeholder=f"Subtask under '{task['title']}'...", label_visibility="collapsed")
            with sub_c2:
                new_sub_prio = st.selectbox("Priority", dm.PRIORITY_OPTIONS, index=1, key=f"prio_sub_{task_id}", label_visibility="collapsed")
            with sub_c3:
                new_sub_diff = st.selectbox("Difficulty", dm.DIFFICULTY_OPTIONS, index=1, key=f"diff_sub_{task_id}", label_visibility="collapsed")
            with sub_c4:
                new_sub_due = st.text_input("Due Date", key=f"due_sub_{task_id}", placeholder="YYYY-MM-DD", label_visibility="collapsed")
            with sub_c_est:
                new_sub_est = st.number_input("Est (mins)", min_value=0, max_value=360, value=30, step=15, key=f"est_sub_{task_id}", label_visibility="collapsed")
            with sub_c5:
                if st.button("Save", key=f"save_sub_{task_id}", type="primary", use_container_width=True):
                    if new_sub_title.strip():
                        dm.add_task(st.session_state.study_data, subject, chapter_id, new_sub_title, priority=new_sub_prio, difficulty=new_sub_diff, due_date=new_sub_due, parent_task_id=task_id, estimated_minutes=new_sub_est)
                        st.session_state.collapsed_tasks.discard(task_id)
                        st.session_state.active_subtask_input = None
                        st.rerun()

        # Inline Input: Edit Task (Title, Priority, Difficulty, Due Date, and Estimated Duration)
        if st.session_state.active_edit_task == task_id:
            edit_c1, edit_c2, edit_c3, edit_c4, edit_c_est, edit_c5 = st.columns([3.0, 1.3, 1.3, 1.3, 1.1, 1.0])
            with edit_c1:
                updated_title = st.text_input("Rename Task", value=task["title"], key=f"input_edit_title_{task_id}", label_visibility="collapsed")
            with edit_c2:
                p_idx = dm.PRIORITY_OPTIONS.index(task_prio) if task_prio in dm.PRIORITY_OPTIONS else 1
                updated_prio = st.selectbox("Priority", dm.PRIORITY_OPTIONS, index=p_idx, key=f"input_edit_prio_{task_id}", label_visibility="collapsed")
            with edit_c3:
                d_idx = dm.DIFFICULTY_OPTIONS.index(task_diff) if task_diff in dm.DIFFICULTY_OPTIONS else 1
                updated_diff = st.selectbox("Difficulty", dm.DIFFICULTY_OPTIONS, index=d_idx, key=f"input_edit_diff_{task_id}", label_visibility="collapsed")
            with edit_c4:
                updated_due = st.text_input("Due Date", value=task_due, key=f"input_edit_due_{task_id}", placeholder="YYYY-MM-DD", label_visibility="collapsed")
            with edit_c_est:
                task_curr_est = int(task.get("estimated_minutes", 0))
                updated_est = st.number_input("Est (mins)", min_value=0, max_value=360, value=task_curr_est, step=15, key=f"input_edit_est_{task_id}", label_visibility="collapsed")
            with edit_c5:
                if st.button("Update", key=f"btn_save_edit_{task_id}", type="primary", use_container_width=True):
                    if updated_title.strip():
                        dm.edit_task(st.session_state.study_data, subject, chapter_id, task_id, updated_title, new_priority=updated_prio, new_difficulty=updated_diff, new_due_date=updated_due, new_estimated_minutes=updated_est)
                        st.session_state.active_edit_task = None
                        st.rerun()

    # Recurse into children
    if has_children and not is_collapsed:
        for sub in subtasks:
            render_task_node(sub, subject, chapter_id, depth=depth + 1, priority_filter=priority_filter, difficulty_filter=difficulty_filter)


# =====================================================================
# DAILY FOCUS PLANNER & MULTI-DAY SCHEDULE
# =====================================================================
def render_daily_and_weekly_planner() -> None:
    """Renders the collapsible Daily Focus checklist and the 7-Day Weekly Schedule."""
    data = st.session_state.study_data
    dm.ensure_daily_focus(data)
    planner = data.get("daily_focus", {"date": dm.get_today_key(), "items": []})
    items = planner.get("items", [])

    total = len(items)
    done_total = sum(1 for item in items if item.get("done", False))
    summary = f"✅ {done_total}/{total} done" if total else "All complete"

    with st.expander(f"🧭 **Daily & Weekly Study Planner**  •  {summary}", expanded=True):
        tab_today, tab_week = st.tabs(["📌 Today's Priority Focus", "🗓️ 7-Day Weekly Schedule & Study Hours"])

        with tab_today:
            # 1. Timetable & Planned Time Overview (Feature 12)
            total_planned_mins = sum(int(item.get("estimated_minutes", 0)) for item in items)
            done_planned_mins = sum(int(item.get("estimated_minutes", 0)) for item in items if item.get("done", False))
            daily_goal_mins = dm.get_daily_goal(data)

            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                st.metric("⏱️ Planned Study Time", f"{total_planned_mins // 60}h {total_planned_mins % 60}m")
            with p_col2:
                st.metric("✅ Completed Planned", f"{done_planned_mins // 60}h {done_planned_mins % 60}m")
            with p_col3:
                st.metric("🎯 Daily Goal Target", f"{daily_goal_mins // 60}h {daily_goal_mins % 60}m")

            prog_val = min(1.0, max(0.0, done_planned_mins / max(1, total_planned_mins))) if total_planned_mins > 0 else (1.0 if total > 0 and done_total == total else 0.0)
            st.progress(prog_val, text=f"Daily Focus Progress: {done_total}/{total} tasks complete ({int(prog_val * 100)}% of planned time)")

            # 2. Add Ad-Hoc / Custom Task Form (Feature 2)
            with st.expander("➕ Add Ad-Hoc / Custom Focus Task for Today", expanded=False):
                adhoc_c1, adhoc_c2, adhoc_c3, adhoc_c4, adhoc_c5 = st.columns([3.0, 1.4, 1.2, 1.2, 1.2])
                with adhoc_c1:
                    adhoc_title = st.text_input("Task Description", placeholder="e.g. Watch Mohit Tyagi Lec 4, Analyze Test 3...", key="adhoc_task_title")
                with adhoc_c2:
                    adhoc_subj = st.selectbox("Subject", ["General", "Physics", "Chemistry", "Mathematics"], index=0, key="adhoc_task_subj")
                with adhoc_c3:
                    adhoc_prio = st.selectbox("Priority", dm.PRIORITY_OPTIONS, index=1, key="adhoc_task_prio")
                with adhoc_c4:
                    adhoc_est = st.number_input("Est (mins)", min_value=5, max_value=360, value=45, step=15, key="adhoc_task_est")
                with adhoc_c5:
                    st.write("")
                    if st.button("➕ Add Task", key="btn_add_adhoc", type="primary", use_container_width=True):
                        if adhoc_title.strip():
                            dm.add_custom_daily_task(data, adhoc_title, estimated_minutes=adhoc_est, subject=adhoc_subj, priority=adhoc_prio)
                            st.toast(f"Added custom task '{adhoc_title}' to today's focus!")
                            st.rerun()

            if not items:
                st.info("No unfinished tasks left for today. Great job! Add custom tasks above or syllabus tasks below.")
            else:
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    filter_subj = st.selectbox("📚 Subject", ["All", "General", "Physics", "Chemistry", "Mathematics"], index=0, key="focus_f_subj")
                with f_col2:
                    filter_prio = st.selectbox("🏷️ Priority", ["All", "High", "Medium", "Low"], index=0, key="focus_f_prio")
                with f_col3:
                    filter_diff = st.selectbox("🎯 Difficulty", ["All", "Easy", "Medium", "Hard"], index=0, key="focus_f_diff")

                filtered = items
                if filter_subj != "All":
                    filtered = [i for i in filtered if i.get("subject") == filter_subj]
                if filter_prio != "All":
                    filtered = [i for i in filtered if i.get("priority") == filter_prio]
                if filter_diff != "All":
                    filtered = [i for i in filtered if i.get("difficulty", "Medium") == filter_diff]

                f_done = sum(1 for i in filtered if i.get("done", False))
                st.caption(f"{f_done}/{len(filtered)} filtered tasks complete for today")

                if not filtered:
                    st.info("No tasks match these filters.")
                else:
                    for item in filtered:
                        item_key = item["key"]
                        is_custom = item.get("is_custom", False)
                        est_mins = int(item.get("estimated_minutes", 0))
                        est_str = f" • ⏱️ {est_mins}m" if est_mins > 0 else ""

                        if is_custom:
                            col_chk, col_del = st.columns([9.2, 0.8])
                            with col_chk:
                                label = f"⭐ [Custom] [{item['priority']}] {item['subject']} • {item['title']}{est_str}"
                                st.checkbox(
                                    label,
                                    value=item.get("done", False),
                                    key=f"daily_focus_{item_key}",
                                    on_change=on_daily_focus_change,
                                    args=(item_key,)
                                )
                            with col_del:
                                if st.button("🗑️", key=f"del_custom_task_{item_key}", help="Delete custom task"):
                                    dm.delete_custom_daily_task(data, item_key)
                                    st.rerun()
                        else:
                            label = f"[{item['priority']}] [{item.get('difficulty', 'Medium')}] {item['subject']} • {item['chapter_name']} • {item['title']}{est_str}"
                            st.checkbox(
                                label,
                                value=item.get("done", False),
                                key=f"daily_focus_{item_key}",
                                on_change=on_daily_focus_change,
                                args=(item_key,)
                            )
                            due_tag = get_due_date_badge(item.get("due_date", ""), item.get("done", False))
                            if due_tag:
                                st.markdown(f"<div style='margin-top:-6px; margin-bottom:6px; margin-left:26px;'>{due_tag}</div>", unsafe_allow_html=True)

        with tab_week:
            # 7-day calendar breakdown
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())  # Monday
            days_cols = st.columns(7)
            daily_log = data.get("daily_log", {})
            revisions = data.get("revision_schedule", [])

            for idx, col in enumerate(days_cols):
                day_date = start_of_week + timedelta(days=idx)
                d_str = day_date.isoformat()
                is_today = (day_date == today)
                log_e = daily_log.get(d_str, {})
                mins_studied = log_e.get("minutes", 0) if isinstance(log_e, dict) else 0
                tasks_done = log_e.get("tasks_done", 0) if isinstance(log_e, dict) else 0
                revs_due = [r for r in revisions if r.get("scheduled_date") == d_str]

                with col:
                    header_bg = "#3B82F6" if is_today else ("#334155" if data.get("settings", {}).get("dark_mode", True) else "#E2E8F0")
                    st.markdown(
                        f"""
                        <div style="border: 1px solid {'#3B82F6' if is_today else '#475569'}; background: {header_bg}22; border-radius: 8px; padding: 8px; text-align: center; margin-bottom: 6px;">
                            <div style="font-weight: 700; font-size: 0.85rem; color: {'#3B82F6' if is_today else 'inherit'};">
                                {day_date.strftime('%a')} {'(Today)' if is_today else ''}
                            </div>
                            <div style="font-size: 0.75rem; color: #94A3B8;">{day_date.strftime('%b %d')}</div>
                            <div style="margin-top: 6px; font-weight: 800; font-size: 1.1rem; color: #10B981;">{mins_studied}m</div>
                            <div style="font-size: 0.72rem;">{tasks_done} tasks</div>
                            {f'<div style="font-size: 0.7rem; color: #F59E0B; margin-top: 4px;">📅 {len(revs_due)} revs</div>' if revs_due else ''}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


# =====================================================================
# REVISION SCHEDULER (SPACED REPETITION HUB)
# =====================================================================
def render_revision_hub() -> None:
    """Renders the Spaced Repetition hub for review reminders."""
    data = st.session_state.study_data
    st.subheader("📅 Spaced Repetition Revision Hub")
    st.markdown("Automated JEE revision intervals (+1d, +3d, +7d, +21d) to lock formulas and concepts into long-term memory.")

    due_list = dm.get_due_revisions(data)
    upcoming_list = dm.get_upcoming_revisions(data)

    r_col1, r_col2 = st.columns([1.2, 1.0])

    with r_col1:
        st.markdown(f"##### 🚨 Due for Review Today ({len(due_list)})")
        if not due_list:
            st.success("🎉 All caught up! No spaced repetitions due today.")
        else:
            for rev in due_list:
                rev_id = rev["id"]
                c_a, c_b = st.columns([4, 1])
                with c_a:
                    st.markdown(f"**{rev['subject']}**: {rev['chapter_name']} *(Review +{rev.get('interval_days', 1)}d)*")
                    st.caption(f"Scheduled: {rev.get('scheduled_date')}")
                with c_b:
                    if st.button("Mark Done", key=f"btn_done_rev_{rev_id}", type="primary"):
                        dm.complete_revision(data, rev_id)
                        st.toast(f"Completed revision for {rev['chapter_name']}!")
                        st.rerun()

    with r_col2:
        st.markdown(f"##### ⏳ Upcoming Scheduled Reviews ({len(upcoming_list)})")
        if not upcoming_list:
            st.caption("No upcoming revisions scheduled yet. Mark chapters 100% complete to schedule reviews.")
        else:
            for rev in upcoming_list[:8]:
                st.caption(f"📅 **{rev.get('scheduled_date')}** — {rev['subject']}: {rev['chapter_name']} (+{rev.get('interval_days')}d)")


# =====================================================================
# SUBJECT WORKSPACE VIEW (EXPAND ALL / COLLAPSE ALL & WEIGHTAGE)
# =====================================================================
def render_subject_section(subject: str, icon: str, priority_filter: str, difficulty_filter: str) -> None:
    """Renders chapter list, weightages, CRUD controls, accordion expand/collapse, and task trees."""
    data = st.session_state.study_data
    subject_info = data["subjects"][subject]
    chapters = subject_info["chapters"]
    subj_progress = subject_info["progress"]

    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.subheader(f"{icon} {subject} Syllabus Tracker")
    with head_col2:
        st.metric(label=f"{subject} Completion", value=f"{subj_progress:.1f}%")

    st.progress(min(max(subj_progress / 100.0, 0.0), 1.0))

    # Add Chapter Form
    with st.form(key=f"add_chapter_form_{subject}", clear_on_submit=True):
        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([3.2, 1.3, 1.5, 1.3, 1.2])
        with f_col1:
            new_chapter_name = st.text_input("New Chapter Name", placeholder=f"➕ New {subject} chapter...", label_visibility="collapsed")
        with f_col2:
            new_chapter_prio = st.selectbox("Priority", dm.PRIORITY_OPTIONS, index=0, label_visibility="collapsed")
        with f_col3:
            new_chapter_weight = st.selectbox("Weightage", dm.WEIGHTAGE_OPTIONS, index=1, label_visibility="collapsed")
        with f_col4:
            new_chapter_due = st.text_input("Target Date", placeholder="YYYY-MM-DD", label_visibility="collapsed")
        with f_col5:
            submit_chapter = st.form_submit_button("➕ Add", type="primary", use_container_width=True)
            if submit_chapter and new_chapter_name.strip():
                dm.add_chapter(data, subject, new_chapter_name, priority=new_chapter_prio, weightage=new_chapter_weight, due_date=new_chapter_due)
                st.rerun()

    st.divider()

    if not chapters:
        st.info(f"No chapters in {subject} yet. Click 'Load NTA JEE Syllabus' in the sidebar or add one above!")
        return

    # Chapter Sort Mode & Accordion Controls
    sort_col1, sort_col2, sort_col3 = st.columns([2.5, 2.0, 1.5])
    with sort_col1:
        st.caption("📑 Chapter Order & Organization")
    with sort_col2:
        sort_mode = st.selectbox(
            "Sort chapters",
            ["Custom Order", "Priority", "Weightage (High → Low)", "Name (A→Z)", "Progress (%)"],
            index=0,
            key=f"chapter_sort_{subject}",
            label_visibility="collapsed"
        )
    with sort_col3:
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            if st.button("➕ Expand", key=f"exp_all_{subject}", help="Expand all chapter accordions", use_container_width=True):
                st.session_state.expand_all_chapters = True
                st.rerun()
        with b_c2:
            if st.button("➖ Collapse", key=f"coll_all_{subject}", help="Collapse all chapter accordions", use_container_width=True):
                st.session_state.expand_all_chapters = False
                st.rerun()

    if sort_mode == "Priority":
        display_chapters = sorted(chapters, key=lambda c: dm.PRIORITY_RANK.get(c.get("priority", "High"), 99))
    elif sort_mode == "Weightage (High → Low)":
        display_chapters = sorted(chapters, key=lambda c: (dm.WEIGHTAGE_RANK.get(c.get("weightage", "Medium (4-8 M)"), 99), -c.get("progress", 0.0)))
    elif sort_mode == "Name (A→Z)":
        display_chapters = sorted(chapters, key=lambda c: c.get("name", "").lower())
    elif sort_mode == "Progress (%)":
        display_chapters = sorted(chapters, key=lambda c: -c.get("progress", 0.0))
    else:
        display_chapters = chapters

    is_custom_order = (sort_mode == "Custom Order")

    for chap_idx, chapter in enumerate(display_chapters):
        chapter_id = chapter["id"]
        chap_prog = chapter["progress"]
        chap_prio = chapter.get("priority", "High")
        chap_weight = chapter.get("weightage", "Medium (4-8 M)")
        chap_due = chapter.get("due_date", "")
        task_count = len(chapter["tasks"])
        notes_text = chapter.get("notes", "")

        prio_icon = "🔥 High" if chap_prio == "High" else ("⚡ Med" if chap_prio == "Medium" else "🌱 Low")
        notes_indicator = "📝 " if notes_text.strip() else ""
        due_indicator = f"⏰ {chap_due} " if chap_due else ""
        expander_label = (
            f"📖 **{chapter['name']}**  •  [{prio_icon}]  •  "
            f"[🎯 {chap_weight}]  •  `{chap_prog:.1f}%` ({task_count} tasks) {due_indicator}{notes_indicator}"
        )

        with st.expander(expander_label, expanded=st.session_state.get("expand_all_chapters", False)):
            if is_custom_order:
                c_col_up, c_col_down, c_col1, c_col2, c_col3, c_col4 = st.columns([0.45, 0.45, 4.3, 1.2, 1.2, 1.2])
                with c_col_up:
                    if st.button("⬆️", key=f"move_up_{chapter_id}", help="Move chapter up", disabled=(chap_idx == 0), use_container_width=True):
                        dm.move_chapter(data, subject, chapter_id, "up")
                        st.rerun()
                with c_col_down:
                    if st.button("⬇️", key=f"move_down_{chapter_id}", help="Move chapter down", disabled=(chap_idx == len(display_chapters) - 1), use_container_width=True):
                        dm.move_chapter(data, subject, chapter_id, "down")
                        st.rerun()
            else:
                c_col1, c_col2, c_col3, c_col4 = st.columns([5.2, 1.3, 1.2, 1.2])

            with c_col1:
                st.progress(min(max(chap_prog / 100.0, 0.0), 1.0))
            with c_col2:
                st.markdown(f"<div style='text-align:center;'>{get_priority_badge(chap_prio)} {get_weightage_badge(chap_weight)}</div>", unsafe_allow_html=True)
            with c_col3:
                if st.button("✏️ Edit", key=f"edit_chap_btn_{chapter_id}", use_container_width=True):
                    st.session_state.active_edit_chapter = None if st.session_state.active_edit_chapter == chapter_id else chapter_id
                    st.rerun()
            with c_col4:
                with st.popover("🗑️ Delete", use_container_width=True):
                    st.caption(f"Delete **'{chapter['name']}'** and all its tasks?")
                    if st.button("Confirm Delete", key=f"del_chap_btn_{chapter_id}", type="primary", use_container_width=True):
                        dm.delete_chapter(data, subject, chapter_id)
                        st.toast(f"Deleted chapter '{chapter['name']}'")
                        st.rerun()

            # Inline Chapter Edit (Title, Priority, Weightage, and Due Date)
            if st.session_state.active_edit_chapter == chapter_id:
                rc1, rc2, rc3, rc4, rc5 = st.columns([3.0, 1.5, 1.8, 1.5, 1.2])
                with rc1:
                    new_chap_title = st.text_input("Rename Chapter", value=chapter["name"], key=f"input_rename_chap_{chapter_id}", label_visibility="collapsed")
                with rc2:
                    c_idx = dm.PRIORITY_OPTIONS.index(chap_prio) if chap_prio in dm.PRIORITY_OPTIONS else 0
                    new_chap_prio = st.selectbox("Priority", dm.PRIORITY_OPTIONS, index=c_idx, key=f"input_prio_chap_{chapter_id}", label_visibility="collapsed")
                with rc3:
                    w_idx = dm.WEIGHTAGE_OPTIONS.index(chap_weight) if chap_weight in dm.WEIGHTAGE_OPTIONS else 1
                    new_chap_weight = st.selectbox("Weightage", dm.WEIGHTAGE_OPTIONS, index=w_idx, key=f"input_weight_chap_{chapter_id}", label_visibility="collapsed")
                with rc4:
                    new_chap_due = st.text_input("Due Date (YYYY-MM-DD)", value=chap_due, key=f"input_due_chap_{chapter_id}", placeholder="2026-12-31", label_visibility="collapsed")
                with rc5:
                    if st.button("Save", key=f"save_chap_{chapter_id}", type="primary", use_container_width=True):
                        if new_chap_title.strip():
                            dm.edit_chapter(data, subject, chapter_id, new_chap_title, new_priority=new_chap_prio, new_weightage=new_chap_weight, new_due_date=new_chap_due)
                            st.session_state.active_edit_chapter = None
                            st.rerun()

            # Notes / Mistake Log Drawer
            with st.expander("📝 Chapter Notes & Mistake Log", expanded=False):
                current_notes = dm.get_chapter_notes(data, subject, chapter_id)
                notes_key = f"notes_area_{chapter_id}"
                new_notes = st.text_area(
                    "Personalized Shortcuts & Frequent Errors",
                    value=current_notes,
                    key=notes_key,
                    placeholder="Record tricky derivations, formula traps, sign conventions, and silly mistakes here..."
                )
                if st.button("💾 Save Chapter Notes", key=f"save_notes_{chapter_id}"):
                    dm.save_chapter_notes(data, subject, chapter_id, new_notes)
                    st.toast(f"Notes saved for {chapter['name']}!", icon="📝")

            # Spaced Repetition Trigger button
            if chap_prog >= 100.0:
                s_col1, s_col2 = st.columns([4, 2])
                with s_col1:
                    st.success("🎉 Chapter 100% Completed! Spaced Repetition can be scheduled.")
                with s_col2:
                    if st.button("📅 Schedule Spaced Reviews (+1,+3,+7,+21d)", key=f"sched_rev_{chapter_id}", use_container_width=True):
                        scheduled = dm.schedule_revision(data, subject, chapter_id, chapter["name"])
                        if scheduled:
                            st.toast("Scheduled spaced reviews!", icon="📅")
                        else:
                            st.info("Spaced repetition is already scheduled for this chapter.")
                        st.rerun()

            st.markdown("---")

            # Render Tasks
            if not chapter["tasks"]:
                st.caption("No tasks created yet. Add your first task below!")
            else:
                for task in chapter["tasks"]:
                    render_task_node(task, subject, chapter_id, depth=0, priority_filter=priority_filter, difficulty_filter=difficulty_filter)

            # Add Root Task to Chapter (with Priority, Difficulty, Due Date, and Estimated Minutes)
            t_col1, t_col2, t_col3, t_col4, t_col_est, t_col5 = st.columns([3.0, 1.2, 1.2, 1.2, 1.0, 1.2])
            with t_col1:
                new_root_task = st.text_input("New Task Title", key=f"new_root_title_{chapter_id}", placeholder=f"New task for {chapter['name']}...", label_visibility="collapsed")
            with t_col2:
                new_root_prio = st.selectbox("Priority", dm.PRIORITY_OPTIONS, index=0, key=f"new_root_prio_{chapter_id}", label_visibility="collapsed")
            with t_col3:
                new_root_diff = st.selectbox("Difficulty", dm.DIFFICULTY_OPTIONS, index=1, key=f"new_root_diff_{chapter_id}", label_visibility="collapsed")
            with t_col4:
                new_root_due = st.text_input("Due Date", key=f"new_root_due_{chapter_id}", placeholder="YYYY-MM-DD", label_visibility="collapsed")
            with t_col_est:
                new_root_est = st.number_input("Est (mins)", min_value=0, max_value=360, value=30, step=15, key=f"new_root_est_{chapter_id}", label_visibility="collapsed")
            with t_col5:
                if st.button("➕ Add Task", key=f"btn_add_root_{chapter_id}", use_container_width=True):
                    if new_root_task.strip():
                        dm.add_task(data, subject, chapter_id, new_root_task, priority=new_root_prio, difficulty=new_root_diff, due_date=new_root_due, parent_task_id=None, estimated_minutes=new_root_est)
                        st.rerun()


# =====================================================================
# GLOBAL SEARCH & QUICK FINDER
# =====================================================================
def render_global_search_view() -> None:
    """Provides a global search engine across all subjects, chapters, and tasks."""
    data = st.session_state.study_data
    st.subheader("🔎 Global Task & Topic Search")
    st.markdown("Search across all **Physics, Chemistry, and Mathematics** chapters and tasks simultaneously.")

    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
    with col_s1:
        search_query = st.text_input("Enter search term (e.g. 'Projectile', 'Entropy', 'Integration', 'PYQs')", key="global_search_input").strip()
    with col_s2:
        filter_status = st.selectbox("Status", ["All", "Incomplete Only", "Completed Only"], key="global_search_status")
    with col_s3:
        filter_subj = st.selectbox("Subject", ["All", "Physics", "Chemistry", "Mathematics"], key="global_search_subj")

    if not search_query:
        st.info("💡 Type in the search box above to instantly find any chapter, topic, formula, or subtask.")
        return

    results = []
    q_lower = search_query.lower()
    for s_name, s_data in data.get("subjects", {}).items():
        if filter_subj != "All" and s_name != filter_subj:
            continue
        for ch in s_data.get("chapters", []):
            ch_name = ch.get("name", "")
            ch_id = ch.get("id", "")
            for leaf in dm.iter_leaf_tasks(ch.get("tasks", []), s_name, ch_name, ch_id):
                matches = (q_lower in leaf["title"].lower() or q_lower in ch_name.lower())
                if not matches:
                    continue
                task_node = dm.find_task_recursive(ch.get("tasks", []), leaf["key"].split(":")[-1])
                is_done = task_node.get("completed", False) if task_node else False
                if filter_status == "Incomplete Only" and is_done:
                    continue
                if filter_status == "Completed Only" and not is_done:
                    continue
                results.append((s_name, ch, leaf, is_done))

    st.markdown(f"**Found {len(results)} matching tasks:**")
    if not results:
        st.warning(f"No tasks found matching '{search_query}'. Try another search keyword.")
        return

    for idx, (s_name, ch, leaf, is_done) in enumerate(results):
        t_id = leaf["key"].split(":")[-1]
        task_col1, task_col2, task_col3, task_col4 = st.columns([5.5, 1.5, 1.5, 1.5])
        with task_col1:
            title_styled = f"~~{leaf['title']}~~" if is_done else f"**{leaf['title']}**"
            st.markdown(f"{'⚛️' if s_name=='Physics' else ('🧪' if s_name=='Chemistry' else '📐')} **{s_name}** › *{ch['name']}*<br>{title_styled}", unsafe_allow_html=True)
            due_badge = get_due_date_badge(leaf.get("due_date", ""), is_done)
            if due_badge:
                st.markdown(due_badge, unsafe_allow_html=True)
        with task_col2:
            st.markdown(get_priority_badge(leaf.get("priority", "Medium")), unsafe_allow_html=True)
        with task_col3:
            st.markdown(get_difficulty_badge(leaf.get("difficulty", "Medium")), unsafe_allow_html=True)
        with task_col4:
            chk_key = f"global_srch_chk_{leaf['key']}_{idx}"
            new_checked = st.checkbox("Done", value=is_done, key=chk_key)
            if new_checked != is_done:
                just_finished = dm.toggle_task(data, s_name, ch["id"], t_id, new_checked)
                if just_finished:
                    st.toast(f"🎉 Chapter '{ch['name']}' 100% complete! Spaced revision scheduled!", icon="🏆")
                st.rerun()
        st.markdown("<hr style='margin:4px 0 10px 0; border:0; border-top:1px solid rgba(148,163,184,0.2);'>", unsafe_allow_html=True)


# =====================================================================
# MOCK TEST & PYQ TRACKER VIEW
# =====================================================================
def render_mock_tests_view(dark_mode: bool) -> None:
    """Renders the Mock Test scoring dashboard, PYQ paper analyzer, analytics curve, and history tracker."""
    data = st.session_state.study_data
    st.subheader("📝 JEE Mock Test & Official PYQ Paper Tracker")
    st.markdown("Track full-length mock exams (CBT), official NTA previous year shift papers, analyze subject splits, and benchmark against the 99%ile target (~180/300).")

    mock_tests = dm.get_mock_tests(data)

    # Summary KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_tests = len(mock_tests)
    if total_tests > 0:
        avg_score = sum(t.get("total_score", 0.0) for t in mock_tests) / total_tests
        best_score = max(t.get("total_score", 0.0) for t in mock_tests)
        latest_score = mock_tests[-1].get("total_score", 0.0)
    else:
        avg_score, best_score, latest_score = 0.0, 0.0, 0.0

    kpi1.metric("📝 Tests Taken", f"{total_tests}")
    kpi2.metric("🎯 Average Score", f"{avg_score:.1f} / 300", f"{(avg_score / 300.0) * 100:.1f}%")
    kpi3.metric("🏆 Best Score", f"{best_score:.1f} / 300", f"{(best_score / 300.0) * 100:.1f}%")
    kpi4.metric("⏱️ Latest Test", f"{latest_score:.1f} / 300", f"{(latest_score / 300.0) * 100:.1f}%")

    st.divider()

    OFFICIAL_PYQ_PAPERS = [
        "-- Select Official PYQ Shift or Type Below --",
        "JEE Main 2024 - 27 Jan Shift 1",
        "JEE Main 2024 - 27 Jan Shift 2",
        "JEE Main 2024 - 29 Jan Shift 1",
        "JEE Main 2024 - 29 Jan Shift 2",
        "JEE Main 2024 - 30 Jan Shift 1",
        "JEE Main 2024 - 30 Jan Shift 2",
        "JEE Main 2024 - 31 Jan Shift 1",
        "JEE Main 2024 - 31 Jan Shift 2",
        "JEE Main 2024 - 01 Feb Shift 1",
        "JEE Main 2024 - 01 Feb Shift 2",
        "JEE Main 2024 - 04 Apr Shift 1",
        "JEE Main 2024 - 05 Apr Shift 1",
        "JEE Main 2024 - 06 Apr Shift 1",
        "JEE Main 2024 - 08 Apr Shift 1",
        "JEE Main 2024 - 09 Apr Shift 1",
        "JEE Main 2023 - 24 Jan Shift 1",
        "JEE Main 2023 - 25 Jan Shift 1",
        "JEE Main 2023 - 29 Jan Shift 1",
        "JEE Main 2023 - 30 Jan Shift 1",
        "JEE Main 2023 - 31 Jan Shift 1",
        "JEE Main 2023 - 06 Apr Shift 1",
        "JEE Main 2023 - 08 Apr Shift 1",
        "JEE Main 2023 - 10 Apr Shift 1",
        "JEE Main 2022 - 24 Jun Shift 1",
        "JEE Main 2022 - 25 Jul Shift 1"
    ]

    # Form to Log New Mock Test or Official PYQ Paper
    with st.expander("➕ Log New Mock Test or PYQ Shift Paper", expanded=(total_tests == 0)):
        test_cat = st.radio(
            "Test Category",
            ["Full Mock Test (300 Marks)", "Official JEE Main PYQ Paper", "Subject Test (100 Marks)", "Chapter / Custom Test"],
            horizontal=True,
            key="test_category_radio"
        )

        preset_choice = ""
        if test_cat == "Official JEE Main PYQ Paper":
            preset_choice = st.selectbox("Quick-Select Official NTA Paper", OFFICIAL_PYQ_PAPERS, key="pyq_paper_select")

        with st.form("new_mock_test_form", clear_on_submit=False):
            f_col1, f_col2, f_col3 = st.columns([2.5, 1.2, 1.2])
            with f_col1:
                default_name = preset_choice if (preset_choice and not preset_choice.startswith("--")) else ""
                test_name = st.text_input("Test Name / Series / PYQ Shift", value=default_name, placeholder="e.g. Allen Major Test 2, MathonGo FT-05, 2024 Jan 27 Shift 1 PYQ")
            with f_col2:
                test_date = st.date_input("Test Date", value=date.today())
            with f_col3:
                default_max = 100.0 if "100" in test_cat else 300.0
                max_marks = st.number_input("Max Marks", min_value=10.0, max_value=360.0, value=default_max, step=10.0)

            s_col1, s_col2, s_col3 = st.columns(3)
            with s_col1:
                p_score = st.number_input("⚛️ Physics Marks", min_value=-25.0, max_value=120.0, value=0.0, step=1.0)
            with s_col2:
                c_score = st.number_input("🧪 Chemistry Marks", min_value=-25.0, max_value=120.0, value=0.0, step=1.0)
            with s_col3:
                m_score = st.number_input("📐 Math Marks", min_value=-25.0, max_value=120.0, value=0.0, step=1.0)

            # Question Breakdown & Error Log (Feature 7)
            with st.expander("🎯 Question Breakdown & Error Analysis (Optional)", expanded=True):
                qb1, qb2, qb3, qb4 = st.columns(4)
                with qb1:
                    q_att = st.number_input("Attempted Qs", min_value=0, max_value=90, value=0, step=1, key="mock_q_att")
                with qb2:
                    q_corr = st.number_input("Correct Qs (+4)", min_value=0, max_value=90, value=0, step=1, key="mock_q_corr")
                with qb3:
                    q_inc = st.number_input("Incorrect Qs (-1)", min_value=0, max_value=90, value=0, step=1, key="mock_q_inc")
                with qb4:
                    q_unatt = st.number_input("Unattempted Qs", min_value=0, max_value=90, value=0, step=1, key="mock_q_unatt")

                err1, err2, err3 = st.columns(3)
                with err1:
                    e_silly = st.number_input("⚠️ Silly / Calc Errors", min_value=0, max_value=50, value=0, step=1, key="mock_e_silly", help="Calculation mistakes, misread questions, wrong bubbling")
                with err2:
                    e_concept = st.number_input("🧠 Conceptual Gaps", min_value=0, max_value=50, value=0, step=1, key="mock_e_concept", help="Formula forgotten, incorrect concept applied")
                with err3:
                    e_time = st.number_input("⏳ Time Pressure / Guesses", min_value=0, max_value=50, value=0, step=1, key="mock_e_time", help="Rushed in the last minutes, wild guesses")

            test_notes = st.text_area("Test Analysis / Mistakes to Avoid", placeholder="e.g. SILLY ERRORS: 3 in kinematics. TIME MANAGEMENT: Math took 75 mins...")

            submit_test = st.form_submit_button("💾 Save Score", type="primary", use_container_width=True)
            if submit_test:
                final_name = test_name.strip() or (preset_choice if (preset_choice and not preset_choice.startswith("--")) else "")
                if final_name:
                    if isinstance(test_date, (list, tuple)):
                        date_val = test_date[0] if test_date else date.today()
                    elif isinstance(test_date, (date, datetime)):
                        date_val = test_date
                    else:
                        date_val = date.today()
                    date_str = date_val.isoformat()

                    dm.add_mock_test(
                        data,
                        test_name=final_name,
                        date_str=date_str,
                        physics_score=p_score,
                        chem_score=c_score,
                        math_score=m_score,
                        total_marks=max_marks,
                        notes=test_notes,
                        test_type=test_cat,
                        attempted=int(q_att),
                        correct=int(q_corr),
                        incorrect=int(q_inc),
                        unattempted=int(q_unatt),
                        silly_errors=int(e_silly),
                        conceptual_errors=int(e_concept),
                        time_pressure=int(e_time)
                    )
                    st.session_state["toast_msg"] = f"✅ Saved score for '{final_name}'! Total: {p_score + c_score + m_score:.1f}/{max_marks:.0f}"
                    st.rerun()
                else:
                    st.error("Please enter a Test Name or choose an Official PYQ paper.")

    # Performance Trend Chart
    st.markdown("##### 📈 Performance Progression")
    chart_fig = an.create_mock_test_trend_chart(mock_tests, dark_mode=dark_mode)
    st.plotly_chart(chart_fig, use_container_width=True)

    st.divider()

    # History Table with Delete confirmation
    st.markdown("##### 📋 Mock Test & PYQ History Breakdown")
    if not mock_tests:
        st.info("No mock tests or PYQ papers recorded yet. Use the form above to log your first test score!")
    else:
        for t in reversed(mock_tests):
            t_id = t.get("id")
            total = t.get("total_score", 0.0)
            max_m = t.get("max_marks", 300.0)
            pct = (total / max(1.0, max_m)) * 100.0
            t_type = t.get("test_type", "Full Mock (300M)")

            type_color = "#38BDF8" if "PYQ" in t_type else ("#10B981" if "Full" in t_type else "#F59E0B")
            with st.container():
                tc1, tc2, tc3, tc4, tc5 = st.columns([3, 1.2, 1.2, 1.2, 0.8])
                with tc1:
                    st.markdown(f"<span style='background:{type_color}22; color:{type_color}; border:1px solid {type_color}55; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:700;'>{t_type}</span> **{t.get('name')}** • `{t.get('date')}`", unsafe_allow_html=True)
                    if t.get("notes"):
                        st.caption(f"📝 {t.get('notes')}")

                    # Question Breakdown & Error Analysis Pills (Feature 7)
                    q_att_val = t.get("attempted", 0)
                    q_corr_val = t.get("correct", 0)
                    q_inc_val = t.get("incorrect", 0)
                    q_un_val = t.get("unattempted", 0)
                    silly_val = t.get("silly_errors", 0)
                    concept_val = t.get("conceptual_errors", 0)
                    time_val = t.get("time_pressure", 0)

                    has_qb = (q_att_val > 0 or q_corr_val > 0 or q_inc_val > 0)
                    has_err = (silly_val > 0 or concept_val > 0 or time_val > 0)

                    if has_qb or has_err:
                        qb_parts = []
                        if has_qb:
                            acc = (q_corr_val / max(1, q_att_val)) * 100.0 if q_att_val > 0 else 0.0
                            qb_parts.append(f"🎯 Accuracy: `{acc:.0f}%` ({q_corr_val}C / {q_inc_val}W / {q_un_val}U)")
                        if silly_val > 0:
                            qb_parts.append(f"<span style='background:#EF444422; color:#EF4444; border:1px solid #EF444455; padding:1px 5px; border-radius:4px; font-size:11px; font-weight:600;'>⚠️ {silly_val} Silly</span>")
                        if concept_val > 0:
                            qb_parts.append(f"<span style='background:#8B5CF622; color:#8B5CF6; border:1px solid #8B5CF655; padding:1px 5px; border-radius:4px; font-size:11px; font-weight:600;'>🧠 {concept_val} Concept</span>")
                        if time_val > 0:
                            qb_parts.append(f"<span style='background:#F59E0B22; color:#F59E0B; border:1px solid #F59E0B55; padding:1px 5px; border-radius:4px; font-size:11px; font-weight:600;'>⏳ {time_val} Time</span>")

                        st.markdown("<div style='margin-top:2px; margin-bottom:4px;'>" + "  ".join(qb_parts) + "</div>", unsafe_allow_html=True)

                with tc2:
                    st.markdown(f"**Total: `{total:.1f} / {max_m:.0f}`** (`{pct:.1f}%`)")
                with tc3:
                    st.caption(f"⚛️ Phys: `{t.get('physics', 0):.0f}` | 🧪 Chem: `{t.get('chemistry', 0):.0f}` | 📐 Math: `{t.get('mathematics', 0):.0f}`")
                with tc4:
                    if max_m >= 250:
                        if total >= 180:
                            st.markdown("<span style='color:#10B981; font-weight:700;'>🌟 99%+ Target Met</span>", unsafe_allow_html=True)
                        elif total >= 140:
                            st.markdown("<span style='color:#3B82F6; font-weight:700;'>⚡ 97%+ Strong Score</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color:#F59E0B; font-weight:700;'>🎯 Keep Pushing</span>", unsafe_allow_html=True)
                    else:
                        if pct >= 75:
                            st.markdown("<span style='color:#10B981; font-weight:700;'>🌟 High Accuracy</span>", unsafe_allow_html=True)
                        elif pct >= 50:
                            st.markdown("<span style='color:#3B82F6; font-weight:700;'>⚡ Decent Attempt</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color:#F59E0B; font-weight:700;'>🎯 Needs Practice</span>", unsafe_allow_html=True)
                with tc5:
                    with st.popover("🗑️", help="Delete score"):
                        st.caption(f"Delete test '{t.get('name')}'?")
                        if st.button("Delete", key=f"del_test_{t_id}", type="primary", use_container_width=True):
                            dm.delete_mock_test(data, t_id)
                            st.toast("Deleted mock test score.")
                            st.rerun()
                st.markdown("<hr style='margin:4px 0 10px 0; border:0; border-top:1px solid rgba(148,163,184,0.15);'>", unsafe_allow_html=True)


# =====================================================================
# ANALYTICS DASHBOARD & HEATMAP
# =====================================================================
def render_analytics_dashboard(dark_mode: bool) -> None:
    """Renders the comprehensive Plotly analytics dashboard, heatmap, and trends."""
    data = st.session_state.study_data
    st.subheader("📊 JEE 2028 Preparation Analytics & Insights")

    subjects = ["Physics", "Chemistry", "Mathematics"]
    overall_avg = sum(data["subjects"][s]["progress"] for s in subjects) / 3.0
    streak = dm.get_streak(data)
    time_totals = dm.get_subject_time_totals(data)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("🏆 Total Readiness", f"{overall_avg:.1f}%")
    kpi2.metric("⚛️ Physics", f"{data['subjects']['Physics']['progress']:.1f}%", f"{time_totals['Physics'] // 60}h {time_totals['Physics'] % 60}m")
    kpi3.metric("🧪 Chemistry", f"{data['subjects']['Chemistry']['progress']:.1f}%", f"{time_totals['Chemistry'] // 60}h {time_totals['Chemistry'] % 60}m")
    kpi4.metric("📐 Mathematics", f"{data['subjects']['Mathematics']['progress']:.1f}%", f"{time_totals['Mathematics'] // 60}h {time_totals['Mathematics'] % 60}m")
    kpi5.metric("🔥 Study Streak", f"{streak['current']} Days", f"Best: {streak['best']}d")

    st.divider()

    # 1. Study Activity Heatmap (GitHub-style)
    st.markdown("##### 1. Study Activity Heatmap (12-Week Consistency)")
    heatmap_fig = an.create_study_heatmap(data, dark_mode=dark_mode)
    st.plotly_chart(heatmap_fig, use_container_width=True)

    st.divider()

    # 2. Time Distribution & 14-Day Trend
    r2_c1, r2_c2 = st.columns([1.1, 1.1])
    with r2_c1:
        st.markdown("##### 2. Subject Time Distribution")
        pie_fig = an.create_subject_time_pie(data, dark_mode=dark_mode)
        st.plotly_chart(pie_fig, use_container_width=True)

    with r2_c2:
        st.markdown("##### 3. 14-Day Study Trend vs Daily Goal")
        trend_fig = an.create_weekly_trend_chart(data, dark_mode=dark_mode)
        st.plotly_chart(trend_fig, use_container_width=True)

    st.divider()

    # 3. Subject-wise Completion Bar Chart & Task Difficulty
    r3_c1, r3_c2 = st.columns([1.1, 1.1])
    with r3_c1:
        st.markdown("##### 4. Subject-Wise Syllabus Completion")
        bar_fig = an.create_subject_bar_chart(data, dark_mode=dark_mode)
        st.plotly_chart(bar_fig, use_container_width=True)

    with r3_c2:
        st.markdown("##### 5. Task Difficulty Breakdown")
        diff_fig = an.create_difficulty_distribution(data, dark_mode=dark_mode)
        st.plotly_chart(diff_fig, use_container_width=True)

    st.divider()

    # 4. Individual Chapter Donut
    r4_c1, r4_c2 = st.columns([1.1, 1.1])
    with r4_c1:
        st.markdown("##### 6. Chapter Deep-Dive")
        sel_subj = st.selectbox("Select Subject", subjects, key="an_subj_pick")
        chaps = data["subjects"][sel_subj]["chapters"]
        if chaps:
            c_names = [c["name"] for c in chaps]
            sel_chap_name = st.selectbox("Select Chapter", c_names, key="an_chap_pick")
            sel_ch = next(c for c in chaps if c["name"] == sel_chap_name)
            donut_fig = an.create_chapter_donut_chart(sel_ch, sel_subj, dark_mode=dark_mode)
            st.plotly_chart(donut_fig, use_container_width=True)
        else:
            st.info("No chapters available.")

    with r4_c2:
        st.markdown(f"##### 7. All Chapters Breakdown in {sel_subj}")
        if chaps:
            comp_fig = an.create_chapter_comparison_donut(data, sel_subj, dark_mode=dark_mode)
            st.plotly_chart(comp_fig, use_container_width=True)
        else:
            st.info("No chapters available.")


# =====================================================================
# FORMULA QUICK REFERENCE
# =====================================================================
def render_formula_reference() -> None:
    """Displays key JEE formulas and user-bookmarked shortcuts organized by subject and topic with search and bookmark management."""
    data = st.session_state.study_data
    st.subheader("📐 JEE Formula & Equation Handbook")
    st.markdown("Quick revision handbook of high-yield formulas, plus your personal tricks and bookmarked shortcuts.")

    all_formulas = dm.get_all_formulas(data)
    custom_formulas = dm.get_custom_formulas(data)

    # Calculate total custom bookmarked shortcuts
    total_custom = sum(len(eqs) for subj_dict in custom_formulas.values() for eqs in subj_dict.values())

    # 1. Add Custom Formula / Shortcut Expander
    with st.expander("➕ Bookmark a New Formula / Trick / Shortcut", expanded=False):
        cf_subj = st.selectbox("Subject", ["Physics", "Chemistry", "Mathematics"], key="cf_subj")
        existing_topics = sorted(list(all_formulas.get(cf_subj, {}).keys()))

        with st.form("custom_formula_form", clear_on_submit=True):
            c1, c2 = st.columns([1.5, 2.5])
            with c1:
                topic_choice = st.selectbox(
                    "Choose Existing Topic",
                    ["-- Select Topic --"] + existing_topics,
                    key=f"cf_topic_pick_{cf_subj}"
                )
            with c2:
                custom_topic = st.text_input(
                    "OR Type New Custom Topic",
                    placeholder="e.g. Modern Physics, GOC, Conics...",
                    key="cf_custom_topic"
                )

            cf_text = st.text_input(
                "Formula / Shortcut Expression",
                placeholder="e.g. Shortcut for Radius of Gyration: k = √(I/M)",
                key="cf_text"
            )
            submitted = st.form_submit_button("💾 Save to Formula Handbook", type="primary")

            if submitted:
                target_topic = custom_topic.strip() if custom_topic.strip() else (topic_choice if topic_choice != "-- Select Topic --" else "")
                if target_topic and cf_text.strip():
                    dm.add_custom_formula(data, cf_subj, target_topic, cf_text.strip())
                    st.toast(f"Saved custom formula under '{target_topic}' in {cf_subj}!")
                    st.rerun()
                else:
                    st.error("Please provide both a valid topic name (select from dropdown or type new) and the formula expression.")

    # Search & View Controls Row
    sc1, sc2 = st.columns([3, 1])
    with sc1:
        search_query = st.text_input("🔍 Search Formulas, Laws, or Topics", placeholder="e.g. Bernoulli, Torque, Carnot, Integration...", key="formula_search").strip().lower()
    with sc2:
        st.write("")
        st.write("")
        expand_all = st.checkbox("📂 Expand All Topics", value=bool(search_query), key="expand_all_formulas")

    tab_p, tab_c, tab_m, tab_custom = st.tabs([
        "⚛️ Physics Formulas",
        "🧪 Chemistry Formulas",
        "📐 Mathematics Formulas",
        f"⭐ My Bookmarked Tricks ({total_custom})"
    ])

    for tab, subj in zip([tab_p, tab_c, tab_m], ["Physics", "Chemistry", "Mathematics"]):
        with tab:
            subj_formulas = all_formulas.get(subj, {})
            all_subj_topics = sorted(list(subj_formulas.keys()))

            # Topic filter selector
            selected_topic_filter = st.selectbox(
                f"Filter {subj} Topics",
                options=["All Topics"] + all_subj_topics,
                key=f"topic_filter_{subj}"
            )

            topics_to_show = all_subj_topics if selected_topic_filter == "All Topics" else [selected_topic_filter]
            found_any = False

            for topic in topics_to_show:
                eq_list = subj_formulas.get(topic, [])
                filtered_eqs = [
                    item for item in eq_list
                    if (search_query in item["formula"].lower() or search_query in topic.lower())
                ] if search_query else eq_list

                if filtered_eqs:
                    found_any = True
                    has_custom = any(item.get("is_custom") for item in filtered_eqs)
                    custom_count = sum(1 for item in filtered_eqs if item.get("is_custom"))
                    badge_str = f" ⭐ ({custom_count} trick{'s' if custom_count > 1 else ''})" if has_custom else ""
                    topic_label = f"📌 {topic} ({len(filtered_eqs)}){badge_str}"

                    with st.expander(topic_label, expanded=expand_all):
                        for item in filtered_eqs:
                            formula_str = item["formula"]
                            is_custom = item.get("is_custom", False)
                            idx = item.get("index")

                            if is_custom:
                                f_col, del_col = st.columns([8.8, 1.2])
                                with f_col:
                                    st.markdown("<span style='background:#F59E0B22; color:#F59E0B; border:1px solid #F59E0B55; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:700;'>⭐ Custom Trick</span>", unsafe_allow_html=True)
                                    st.code(formula_str, language="text")
                                with del_col:
                                    st.write("")
                                    if st.button("🗑️", key=f"del_cf_{subj}_{topic}_{idx}_{abs(hash(formula_str))%100000}", help="Delete custom formula"):
                                        dm.delete_custom_formula(data, subj, topic, index=idx, formula_str=formula_str)
                                        st.rerun()
                            else:
                                st.code(formula_str, language="text")

            if not found_any:
                st.info(f"No formulas matching '{search_query}' in {subj}." if search_query else f"No formulas found in {subj}.")

    # Dedicated 4th Tab: Bookmarked Tricks Hub
    with tab_custom:
        st.markdown("#### ⭐ Your Personal Tricks & Shortcut Bookmarks")
        st.caption("All custom formulas and shortcuts you have bookmarked across Physics, Chemistry, and Mathematics.")

        if total_custom == 0:
            st.info("No personal formulas or tricks bookmarked yet! Use the '➕ Bookmark a New Formula / Trick / Shortcut' panel above to save your high-yield shortcuts, mnemonics, and problem-solving tricks.")
        else:
            filter_custom_subj = st.radio(
                "Filter by Subject",
                ["All", "Physics", "Chemistry", "Mathematics"],
                horizontal=True,
                key="filter_custom_bookmarked_subj"
            )

            matched_any = False
            for s in ["Physics", "Chemistry", "Mathematics"]:
                if filter_custom_subj != "All" and filter_custom_subj != s:
                    continue
                s_topics = custom_formulas.get(s, {})
                if not s_topics:
                    continue

                for t_name, f_list in s_topics.items():
                    if not f_list:
                        continue
                    matched_items = [
                        (idx, eq) for idx, eq in enumerate(f_list)
                        if (not search_query or search_query in eq.lower() or search_query in t_name.lower())
                    ]
                    if not matched_items:
                        continue

                    matched_any = True
                    st.markdown(f"**{s}** • `{t_name}`")
                    for idx, eq in matched_items:
                        col1, col2 = st.columns([8.8, 1.2])
                        with col1:
                            st.code(eq, language="text")
                        with col2:
                            st.write("")
                            if st.button("🗑️ Delete", key=f"del_trick_{s}_{t_name}_{idx}_{abs(hash(eq))%100000}", use_container_width=True):
                                dm.delete_custom_formula(data, s, t_name, formula_str=eq)
                                st.rerun()
                    st.divider()

            if not matched_any and search_query:
                st.info(f"No bookmarked tricks matching '{search_query}'.")


# =====================================================================
# NOTES & MISTAKE EXPLORER
# =====================================================================
def render_notes_explorer() -> None:
    """Allows searching and viewing all chapter notes and mistake logs in one place."""
    data = st.session_state.study_data
    st.subheader("🔍 All Chapter Notes & Mistake Logs")
    st.markdown("Review your personalized tips, shortcuts, and frequent errors across all subjects.")

    search_kw = st.text_input("Search notes content or chapter", placeholder="Filter by formula, concept, or mistake...", key="notes_kw").strip().lower()

    count_found = 0
    for subj_name, subj_data in data.get("subjects", {}).items():
        for ch in subj_data.get("chapters", []):
            notes = ch.get("notes", "")
            if notes.strip():
                if not search_kw or (search_kw in notes.lower() or search_kw in ch["name"].lower()):
                    count_found += 1
                    with st.expander(f"📖 {subj_name} • **{ch['name']}**", expanded=bool(search_kw)):
                        st.markdown(notes)
                        st.caption(f"Priority: {ch.get('priority', 'High')} • Completion: {ch.get('progress', 0.0):.1f}%")

    if count_found == 0:
        st.info("No notes found. Open any chapter in the Subject Tracker and expand 'Chapter Notes & Mistake Log' to add your first note!")


# =====================================================================
# PRINTABLE REPORT GENERATOR (HTML / PDF)
# =====================================================================
def generate_html_report(data: Dict[str, Any]) -> str:
    """Generates a self-contained, printable HTML report of the student's JEE preparation."""
    subjects = ["Physics", "Chemistry", "Mathematics"]
    overall_avg = sum(data["subjects"][s]["progress"] for s in subjects) / 3.0
    pomo_stats = data.get("pomodoro_stats", {"sessions_completed": 0, "total_minutes": 0})
    streak = dm.get_streak(data)
    badges = dm.calculate_badges(data)
    time_totals = dm.get_subject_time_totals(data)
    today_str = datetime.now().strftime("%B %d, %Y")

    table_rows = ""
    for s in subjects:
        for ch in data["subjects"][s].get("chapters", []):
            total_tasks, done_tasks = an.count_leaf_tasks_recursive(ch.get("tasks", []))
            table_rows += f"""
            <tr>
                <td><b>{s}</b></td>
                <td>{ch['name']}</td>
                <td>{ch.get('priority', 'Medium')}</td>
                <td>{ch.get('weightage', 'Medium (4-8 M)')}</td>
                <td>{done_tasks} / {total_tasks}</td>
                <td><b>{ch['progress']:.1f}%</b></td>
            </tr>
            """

    badges_html = "".join([f"<span class='badge'>{b['icon']} {b['label']}</span>" for b in badges])

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>JEE 2028 Study Tracker — Preparation Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; color: #0F172A; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #3B82F6; padding-bottom: 12px; margin-bottom: 20px; }}
            h1 {{ margin: 0; color: #1E3A8A; font-size: 24px; }}
            .date {{ color: #64748B; font-size: 14px; }}
            .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }}
            .card {{ background: #F1F5F9; border-radius: 8px; padding: 12px; border-left: 4px solid #3B82F6; }}
            .card-num {{ font-size: 22px; font-weight: 800; color: #1E3A8A; }}
            .card-lbl {{ font-size: 12px; text-transform: uppercase; color: #64748B; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13px; }}
            th, td {{ border: 1px solid #CBD5E1; padding: 8px 10px; text-align: left; }}
            th {{ background: #E2E8F0; font-weight: 700; }}
            .badge {{ display: inline-block; background: #DBEAFE; color: #1E40AF; padding: 4px 10px; border-radius: 12px; font-size: 12px; margin: 3px; }}
            @media print {{
                body {{ margin: 10mm; }}
                button {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>🎯 JEE Main & Advanced 2028 Preparation Report</h1>
                <div class="date">Generated on {today_str} • Target Exam: Week 4 January 2028</div>
            </div>
            <button onclick="window.print()" style="padding: 8px 16px; background: #3B82F6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">🖨️ Print to PDF</button>
        </div>

        <div class="grid">
            <div class="card"><div class="card-num">{overall_avg:.1f}%</div><div class="card-lbl">Total Readiness</div></div>
            <div class="card"><div class="card-num">{streak['current']} Days</div><div class="card-lbl">Current Streak (Best: {streak['best']}d)</div></div>
            <div class="card"><div class="card-num">{pomo_stats['total_minutes'] / 60:.1f} hrs</div><div class="card-lbl">Focused Pomodoro Hours</div></div>
            <div class="card"><div class="card-num">{len(badges)}</div><div class="card-lbl">Milestone Badges Earned</div></div>
        </div>

        <h3>📚 Subject-Wise Progress & Time Log</h3>
        <p><b>⚛️ Physics:</b> {data['subjects']['Physics']['progress']:.1f}% ({time_totals['Physics'] // 60}h {time_totals['Physics'] % 60}m) &nbsp;&nbsp;|&nbsp;&nbsp; <b>🧪 Chemistry:</b> {data['subjects']['Chemistry']['progress']:.1f}% ({time_totals['Chemistry'] // 60}h {time_totals['Chemistry'] % 60}m) &nbsp;&nbsp;|&nbsp;&nbsp; <b>📐 Mathematics:</b> {data['subjects']['Mathematics']['progress']:.1f}% ({time_totals['Mathematics'] // 60}h {time_totals['Mathematics'] % 60}m)</p>

        <h3>🏅 Earned Milestones</h3>
        <p>{badges_html if badges_html else 'No milestones unlocked yet.'}</p>

        <h3>📋 Comprehensive Syllabus Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Subject</th>
                    <th>Chapter</th>
                    <th>Priority</th>
                    <th>Weightage</th>
                    <th>Tasks Completed</th>
                    <th>Progress</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


# =====================================================================
# CHAPTERWISE PDF & VIDEO HUB VIEW
# =====================================================================
def render_chapter_resources_view(dark_mode: bool) -> None:
    """Renders the Chapterwise PDF Notes & YouTube Video Reference Hub."""
    data = st.session_state.study_data
    st.subheader("📁 Chapterwise PDF & Video Lecture Reference Hub")
    st.markdown("Organize your chapter study materials in one place: upload local PDFs (class notes, formula sheets, DPPs) and bookmark YouTube video lectures to watch directly inside the app.")

    # 1. Subject & Chapter Selectors
    sc1, sc2 = st.columns([1.5, 2.5])
    with sc1:
        selected_subj = st.selectbox("📚 Select Subject", ["Physics", "Chemistry", "Mathematics"], key="res_hub_subj")

    subj_data = data.get("subjects", {}).get(selected_subj, {})
    chapters = subj_data.get("chapters", [])

    if not chapters:
        st.warning(f"No chapters found in {selected_subj}. Please add chapters in the Subject Tracker or import the JEE syllabus preset.")
        return

    chapter_options = {ch["id"]: f"{ch['name']} ({ch.get('weightage', 'Medium')})" for ch in chapters}
    with sc2:
        selected_chap_id = st.selectbox(
            "📖 Select Chapter",
            options=list(chapter_options.keys()),
            format_func=lambda cid: chapter_options[cid],
            key=f"res_hub_chap_{selected_subj}"
        )

    current_ch = next((ch for ch in chapters if ch["id"] == selected_chap_id), chapters[0])
    selected_chap_id = current_ch["id"]
    ch_res = dm.get_chapter_resources(data, selected_subj, selected_chap_id)
    pdfs = ch_res.get("pdfs", [])
    videos = ch_res.get("videos", [])

    # Chapter Overview Banner
    banner_bg = "#1E293B" if dark_mode else "#F1F5F9"
    st.markdown(
        f"""
        <div style="background:{banner_bg}; border:1px solid {'#334155' if dark_mode else '#CBD5E1'}; border-radius:8px; padding:12px 16px; margin: 8px 0 16px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                <div>
                    <span style="font-size:1.15rem; font-weight:700;">{selected_subj} • {current_ch['name']}</span>
                    <span style="margin-left:8px; background:#3B82F622; color:#3B82F6; border:1px solid #3B82F655; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700;">{current_ch.get('weightage', 'Medium')}</span>
                    <span style="margin-left:4px; background:#10B98122; color:#10B981; border:1px solid #10B98155; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700;">Priority: {current_ch.get('priority', 'High')}</span>
                </div>
                <div style="font-size:0.9rem; font-weight:600; color:#10B981;">
                    Completion: {current_ch.get('progress', 0.0):.1f}%
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_vid, tab_pdf = st.tabs([
        f"🎥 YouTube Video Lectures ({len(videos)})",
        f"📄 Chapter PDFs & DPPs ({len(pdfs)})"
    ])

    # TAB 1: YOUTUBE VIDEOS
    with tab_vid:
        with st.expander("➕ Bookmark a New YouTube Lecture / Solution Video", expanded=False):
            with st.form(f"video_add_form_{selected_chap_id}", clear_on_submit=True):
                v_title = st.text_input("Video Title", placeholder="e.g. Mohit Tyagi - Projectile Motion Full Lec 2", key=f"v_title_{selected_chap_id}")
                v_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...", key=f"v_url_{selected_chap_id}")
                v_notes = st.text_input("Notes / Key Timestamps (Optional)", placeholder="e.g. 15:30 Maximum Height Formula, 42:10 Trajectory Equation", key=f"v_notes_{selected_chap_id}")
                submitted_vid = st.form_submit_button("➕ Add Video Reference", type="primary")

                if submitted_vid:
                    norm_url = normalize_youtube_url(v_url.strip())
                    if norm_url:
                        dm.add_chapter_video(data, selected_subj, selected_chap_id, title=v_title, url=norm_url, notes=v_notes)
                        st.toast(f"Added video reference '{v_title or 'Video'}'!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid YouTube URL.")

        if not videos:
            st.info("No video references added for this chapter yet. Use the button above to bookmark your favorite YouTube lecture or one-shot revision.")
        else:
            for v in reversed(videos):
                v_id = v.get("id")
                video_url = v.get("url", "")
                with st.container():
                    vc1, vc2 = st.columns([8.5, 1.5])
                    with vc1:
                        st.markdown(f"##### 🎥 {v.get('title', 'Video Lecture')}")
                        if v.get("notes"):
                            st.caption(f"📝 {v.get('notes')}")
                        st.caption(f"Added on: `{v.get('added_at', '')}`")
                    with vc2:
                        st.link_button("▶️ Watch", video_url, use_container_width=True)
                        with st.popover("🗑️ Delete", help="Delete video reference"):
                            st.caption(f"Delete video '{v.get('title')}'?")
                            if st.button("Confirm Delete", key=f"del_v_{v_id}", type="primary", use_container_width=True):
                                dm.delete_chapter_video(data, selected_subj, selected_chap_id, v_id)
                                st.rerun()

                    # Embed YouTube player
                    try:
                        st.video(video_url)
                    except Exception as e:
                        st.info(f"Direct player preview unavailable. Please click '▶️ Watch' above to open on YouTube.")

                    st.divider()

    # TAB 2: PDFS & HANDOUTS
    with tab_pdf:
        with st.expander("📤 Upload Local Notes / DPP / Formula Sheet (PDF)", expanded=False):
            with st.form(f"pdf_upload_form_{selected_chap_id}", clear_on_submit=True):
                uploaded_file = st.file_uploader("Select PDF file", type=["pdf"], key=f"pdf_file_{selected_chap_id}")
                pdf_title = st.text_input("Document Title (Optional)", placeholder="e.g. Allen Classroom Notes, DPP 1 Solutions...", key=f"pdf_title_{selected_chap_id}")
                submitted_pdf = st.form_submit_button("📤 Upload PDF", type="primary")

                if submitted_pdf:
                    if uploaded_file is not None:
                        file_bytes = uploaded_file.getvalue()
                        dm.save_chapter_pdf(
                            data,
                            subject=selected_subj,
                            chapter_id=selected_chap_id,
                            filename=uploaded_file.name,
                            file_bytes=file_bytes,
                            title=pdf_title
                        )
                        st.toast(f"Saved PDF '{uploaded_file.name}'!")
                        st.rerun()
                    else:
                        st.error("Please choose a PDF file to upload.")

        if not pdfs:
            st.info("No PDFs uploaded for this chapter yet. Upload class notes, coaching modules, or DPPs above.")
        else:
            for p in reversed(pdfs):
                p_id = p.get("id")
                size_kb = p.get("size_bytes", 0) / 1024.0
                size_str = f"{size_kb / 1024.0:.2f} MB" if size_kb >= 1024 else f"{size_kb:.1f} KB"
                file_path = dm.get_pdf_path(p)
                pdf_data = None
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            pdf_data = f.read()
                    except Exception:
                        pdf_data = None

                with st.container():
                    pc1, pc2, pc3 = st.columns([5.5, 3.0, 1.5])
                    with pc1:
                        st.markdown(f"**📄 {p.get('title')}**")
                        st.caption(f"Filename: `{p.get('filename')}` • Size: `{size_str}` • Uploaded: `{p.get('uploaded_at')}`")
                    with pc2:
                        if pdf_data is not None:
                            st.download_button(
                                label="⬇️ Download / Save",
                                data=pdf_data,
                                file_name=p.get("filename", "document.pdf"),
                                mime="application/pdf",
                                key=f"dl_pdf_{p_id}",
                                use_container_width=True
                            )
                        else:
                            st.caption("⚠️ File not found on disk")
                    with pc3:
                        with st.popover("🗑️ Delete", help="Delete PDF"):
                            st.caption(f"Delete PDF '{p.get('title')}'?")
                            if st.button("Confirm Delete", key=f"del_pdf_{p_id}", type="primary", use_container_width=True):
                                dm.delete_chapter_pdf(data, selected_subj, selected_chap_id, p_id)
                                st.rerun()

                    # In-App PDF Reader & Viewer
                    if pdf_data is not None:
                        with st.expander(f"📖 Read / Preview '{p.get('title')}' in App", expanded=False):
                            try:
                                render_pdf_viewer_component(pdf_data, filename=p.get("filename", "document.pdf"), height=720)
                            except Exception as err:
                                st.caption(f"Preview unavailable: {err}")
                    else:
                        st.info("⚠️ PDF file content is missing on disk. Please re-upload your notes or DPP.")

                    st.markdown("<hr style='margin:4px 0 8px 0; border:0; border-top:1px solid rgba(148,163,184,0.15);'>", unsafe_allow_html=True)


# =====================================================================
# MAIN APPLICATION WORKSPACE
# =====================================================================
def main() -> None:
    data = dm.ensure_schema_migration(st.session_state.study_data)
    st.session_state.study_data = data

    # Check celebratory toast
    if "toast_msg" in st.session_state:
        msg = st.session_state.pop("toast_msg")
        st.toast(msg, icon="🏆")

    # Dark Mode Resolution (Auto vs Manual)
    auto_dark = dm.get_auto_dark_mode(data)
    if auto_dark:
        curr_hour = datetime.now().hour
        dark_mode = (curr_hour >= 18 or curr_hour < 6)
    else:
        dark_mode = data.get("settings", {}).get("dark_mode", True)

    inject_custom_styles(dark_mode=dark_mode)

    # Sidebar
    with st.sidebar:
        st.title("🎯 JEE 2028 Tracker")
        st.caption("Physics • Chemistry • Mathematics")

        # Theme Toggle
        theme_col1, theme_col2 = st.columns([1, 1])
        with theme_col1:
            theme_label = "🌙 Dark Mode" if dark_mode else "☀️ Light Mode"
            if st.button(theme_label, use_container_width=True, disabled=auto_dark):
                dm.set_dark_mode(data, not dark_mode)
                st.rerun()

        with theme_col2:
            today_mins = dm.get_today_minutes(data)
            goal_mins = dm.get_daily_goal(data)
            st.markdown(f"**🎯 Daily Goal:** `{today_mins // 60}h {today_mins % 60}m` / `{goal_mins // 60}h`")

        st.divider()

        # Navigation
        nav_mode = st.radio(
            "Navigation View",
            [
                "📚 Subject Tracker (CRUD & Tasks)",
                "📊 Analytics & Study Heatmap",
                "📝 Mock Test & PYQ Tracker",
                "📁 Chapter Resources & Video Hub",
                "🔎 Global Search & Quick Finder",
                "📅 Spaced Revision Hub",
                "📐 Formula Quick Reference",
                "🔍 Notes & Mistake Explorer"
            ],
            index=0
        )

        st.divider()

        # Task Filters (Priority & Difficulty)
        st.markdown("##### 🏷️ Syllabus Filters")
        priority_filter = st.selectbox("Filter by Priority", ["All", "High", "Medium", "Low"], index=0)
        difficulty_filter = st.selectbox("Filter by Difficulty", ["All", "Easy", "Medium", "Hard"], index=0)

        st.divider()

        # Live Pomodoro Widget
        render_pomodoro_widget()

        st.divider()

        # Earned Badges Expander
        badges = dm.calculate_badges(data)
        with st.expander(f"🏅 Milestones & Badges ({len(badges)})", expanded=False):
            if not badges:
                st.caption("Complete subject milestones, study streaks, and Pomodoro sessions to unlock badges!")
            else:
                for b in badges:
                    st.markdown(f"<div class='badge-pill'>{b['icon']} {b['label']}</div>", unsafe_allow_html=True)

        st.divider()

        # Local Storage & Preset Tools
        st.markdown("##### ⚙️ Settings & Tools")

        # Auto Dark Mode toggle
        new_auto_dark = st.checkbox("⏰ Auto Dark Mode (after 6 PM)", value=auto_dark, help="Automatically switches to Dark Mode between 6 PM and 6 AM")
        if new_auto_dark != auto_dark:
            dm.set_auto_dark_mode(data, new_auto_dark)
            st.rerun()

        # Daily Goal edit
        with st.popover("🎯 Adjust Daily Goal"):
            new_goal_hrs = st.number_input("Target Hours per Day", min_value=1.0, max_value=18.0, value=float(goal_mins / 60.0), step=0.5)
            if st.button("Save Daily Goal"):
                dm.set_daily_goal(data, int(new_goal_hrs * 60))
                st.toast(f"Daily goal set to {new_goal_hrs:.1f} hours!", icon="🎯")
                st.rerun()

        # Load Full NTA Syllabus
        with st.popover("📥 Load Official NTA Syllabus"):
            st.write("Import all standard chapters for Physics (20+), Chemistry (25+), and Math (18+).")
            st.caption("Existing progress will NOT be erased.")
            if st.button("Confirm Load Syllabus", type="primary", use_container_width=True):
                dm.import_preset_syllabus(data)
                st.toast("Official NTA JEE Main syllabus loaded!", icon="🚀")
                st.rerun()

        # Printable HTML Report Download
        report_html = generate_html_report(data)
        st.download_button(
            label="📄 Export Progress Report (.html / PDF)",
            data=report_html,
            file_name=f"jee_2028_progress_report_{dm.get_today_key()}.html",
            mime="text/html",
            use_container_width=True
        )

        # JSON Backup Download
        json_str = json.dumps(data, indent=2)
        st.download_button(
            label="⬇️ Download Backup (.json)",
            data=json_str,
            file_name="jee_2028_study_backup.json",
            mime="application/json",
            use_container_width=True
        )

        # JSON Backup Restore
        with st.popover("📤 Restore Backup (.json)"):
            st.caption("Upload a previously exported `jee_2028_study_backup.json` to restore all progress.")
            uploaded_file = st.file_uploader("Select backup file", type=["json"], key="backup_upload_picker", label_visibility="collapsed")
            if uploaded_file is not None:
                if st.button("Apply Restored Data", type="primary", use_container_width=True, key="btn_apply_restore"):
                    try:
                        restored_dict = json.load(uploaded_file)
                        migrated = dm.ensure_schema_migration(restored_dict)
                        dm.save_data(migrated)
                        st.session_state.study_data = migrated
                        st.toast("🎉 Backup restored successfully!", icon="✅")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to restore backup: {err}")

        # Cloud Cross-Device Synchronization
        with st.expander("☁️ Cloud Cross-Device Sync", expanded=False):
            st.caption("Sync your streak, test scores, formulas, and progress between this PC and your deployed website.")
            cloud_settings = data.setdefault("settings", {}).setdefault("cloud_sync", {})

            sec_token = ""
            sec_gist_id = ""
            try:
                sec_token = st.secrets.get("GITHUB_TOKEN", "")
                sec_gist_id = st.secrets.get("GIST_ID", "")
            except Exception:
                pass

            curr_token = cloud_settings.get("github_token", "") or sec_token
            curr_gist = cloud_settings.get("gist_id", "") or sec_gist_id

            token_val = st.text_input("GitHub Token (PAT with 'gist' scope)", value=curr_token, type="password", key="sync_token_input", help="Generate at github.com/settings/tokens with 'gist' permission.")
            gist_val = st.text_input("Gist ID (leave empty to create new)", value=curr_gist, key="sync_gist_input", placeholder="e.g. 7f3a8b... or empty to create new")

            cs_c1, cs_c2 = st.columns(2)
            with cs_c1:
                if st.button("☁️ Push to Cloud", use_container_width=True, type="primary", key="btn_push_cloud"):
                    if not token_val.strip():
                        st.error("Please enter a GitHub Personal Access Token.")
                    else:
                        with st.spinner("Pushing data to cloud Gist..."):
                            res = dm.push_to_github_gist(data, token_val.strip(), gist_val.strip())
                            if res.get("success"):
                                new_gist = res.get("gist_id", "")
                                cloud_settings["github_token"] = token_val.strip()
                                cloud_settings["gist_id"] = new_gist
                                cloud_settings["last_synced"] = dm.get_today_key()
                                dm.save_data(data)
                                st.success(f"Synced to Cloud! Gist ID: `{new_gist}`")
                                st.caption("Save this Gist ID to paste on your deployed website.")
                                st.rerun()
                            else:
                                st.error(f"Push failed: {res.get('error')}")

            with cs_c2:
                if st.button("🔄 Pull from Cloud", use_container_width=True, key="btn_pull_cloud"):
                    if not token_val.strip() or not gist_val.strip():
                        st.error("Need Token and Gist ID to pull.")
                    else:
                        with st.spinner("Fetching latest data from cloud Gist..."):
                            res = dm.pull_from_github_gist(token_val.strip(), gist_val.strip())
                            if res.get("success"):
                                remote_data = res.get("data", {})
                                migrated = dm.ensure_schema_migration(remote_data)
                                migrated.setdefault("settings", {})
                                migrated["settings"].setdefault("cloud_sync", {})
                                migrated["settings"]["cloud_sync"]["github_token"] = token_val.strip()
                                migrated["settings"]["cloud_sync"]["gist_id"] = gist_val.strip()
                                migrated["settings"]["cloud_sync"]["last_synced"] = dm.get_today_key()
                                dm.save_data(migrated)
                                st.session_state.study_data = migrated
                                st.toast("Successfully pulled cloud data!", icon="✅")
                                st.rerun()
                            else:
                                st.error(f"Pull failed: {res.get('error')}")

            if cloud_settings.get("last_synced"):
                st.caption(f"Last synced: `{cloud_settings.get('last_synced')}` • Gist: `{cloud_settings.get('gist_id')}`")

        # Reset Syllabus with Confirmation Popover
        with st.popover("🔄 Reset to Default Syllabus"):
            st.warning("⚠️ This will overwrite all custom chapters, tasks, and progress with the fresh starter syllabus. Are you sure?")
            if st.button("Yes, Reset Everything", type="primary", use_container_width=True, key="btn_confirm_reset_syllabus"):
                fresh_data = dm.get_initial_data()
                dm.save_data(fresh_data)
                st.session_state.study_data = fresh_data
                st.toast("Reset syllabus to default!")
                st.rerun()

    # Main Workspace Area
    render_top_countdown_banner()
    render_daily_and_weekly_planner()

    # Route based on navigation view
    if nav_mode == "📚 Subject Tracker (CRUD & Tasks)":
        tab_phy, tab_chem, tab_math = st.tabs([
            f"⚛️ Physics ({data['subjects']['Physics']['progress']:.1f}%)",
            f"🧪 Chemistry ({data['subjects']['Chemistry']['progress']:.1f}%)",
            f"📐 Mathematics ({data['subjects']['Mathematics']['progress']:.1f}%)"
        ])

        with tab_phy:
            render_subject_section("Physics", "⚛️", priority_filter, difficulty_filter)
        with tab_chem:
            render_subject_section("Chemistry", "🧪", priority_filter, difficulty_filter)
        with tab_math:
            render_subject_section("Mathematics", "📐", priority_filter, difficulty_filter)

    elif nav_mode == "📊 Analytics & Study Heatmap":
        render_analytics_dashboard(dark_mode=dark_mode)

    elif nav_mode == "📝 Mock Test & PYQ Tracker":
        render_mock_tests_view(dark_mode=dark_mode)

    elif nav_mode == "📁 Chapter Resources & Video Hub":
        render_chapter_resources_view(dark_mode=dark_mode)

    elif nav_mode == "🔎 Global Search & Quick Finder":
        render_global_search_view()

    elif nav_mode == "📅 Spaced Revision Hub":
        render_revision_hub()

    elif nav_mode == "📐 Formula Quick Reference":
        render_formula_reference()

    elif nav_mode == "🔍 Notes & Mistake Explorer":
        render_notes_explorer()


if __name__ == "__main__":
    main()
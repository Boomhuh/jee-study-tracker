# File: data_manager.py
import json
import os
import uuid
from datetime import date, timedelta
from typing import Dict, List, Optional, Any, Iterator

# The local file where all your progress, priorities, theme, and Pomodoro stats are saved
DATA_FILE = "study_data.json"

PRIORITY_OPTIONS = ["High", "Medium", "Low"]
PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}

DIFFICULTY_OPTIONS = ["Easy", "Medium", "Hard"]
DIFFICULTY_RANK = {"Hard": 0, "Medium": 1, "Easy": 2}

WEIGHTAGE_OPTIONS = ["High (8-12 M)", "Medium (4-8 M)", "Low (4 M)"]
WEIGHTAGE_RANK = {"High (8-12 M)": 0, "Medium (4-8 M)": 1, "Low (4 M)": 2}


def get_today_key() -> str:
    """Returns the current day in ISO format for planner persistence."""
    return date.today().isoformat()


def iter_leaf_tasks(tasks: List[Dict[str, Any]], subject_name: str, chapter_name: str, chapter_id: str) -> Iterator[Dict[str, Any]]:
    """Yields leaf tasks that are actionable for today's planner, including priority, difficulty, due date, and estimated duration."""
    for task in tasks:
        subtasks = task.get("subtasks", [])
        if subtasks:
            yield from iter_leaf_tasks(subtasks, subject_name, chapter_name, chapter_id)
        elif not task.get("completed", False):
            yield {
                "key": f"{subject_name}:{chapter_id}:{task['id']}",
                "subject": subject_name,
                "chapter_id": chapter_id,
                "chapter_name": chapter_name,
                "title": task.get("title", "Untitled Task"),
                "priority": task.get("priority", "Medium"),
                "difficulty": task.get("difficulty", "Medium"),
                "due_date": task.get("due_date", ""),
                "estimated_minutes": int(task.get("estimated_minutes", 0)),
                "is_custom": False
            }


def generate_daily_plan(data: Dict[str, Any], max_items: int = 10) -> List[Dict[str, Any]]:
    """Builds a short, prioritized list of incomplete tasks for today."""
    items: List[Dict[str, Any]] = []
    for subject_name, subject_data in data.get("subjects", {}).items():
        for chapter in subject_data.get("chapters", []):
            for leaf in iter_leaf_tasks(chapter.get("tasks", []), subject_name, chapter.get("name", "Untitled"), chapter.get("id", "")):
                items.append({**leaf, "done": False})

    items.sort(key=lambda item: (
        PRIORITY_RANK.get(item.get("priority"), 99),
        DIFFICULTY_RANK.get(item.get("difficulty"), 99),
        item["subject"],
        item["chapter_name"],
        item["title"]
    ))
    return items[:max_items]


def generate_id() -> str:
    """Generates a unique short ID for every chapter, task, and subtask."""
    return str(uuid.uuid4())[:8]


def get_initial_data() -> Dict[str, Any]:
    """
    Returns the default pre-configured JEE dataset with Physics, Chemistry,
    and Mathematics, including priority tags, weightages, settings, and Pomodoro statistics.
    """
    data = {
        "settings": {
            "dark_mode": True,
            "target_exam_date": "2028-01-24T09:00:00",
            "daily_goal_minutes": 360,
            "auto_dark_mode": False
        },
        "pomodoro_stats": {
            "sessions_completed": 0,
            "total_minutes": 0
        },
        "daily_focus": {
            "date": get_today_key(),
            "items": []
        },
        "streak": {
            "current": 0,
            "best": 0,
            "last_active_date": ""
        },
        "daily_log": {},
        "revision_schedule": [],
        "mock_tests": [],
        "custom_formulas": {
            "Physics": {},
            "Chemistry": {},
            "Mathematics": {}
        },
        "chapter_resources": {},
        "subjects": {
            "Physics": {
                "progress": 0.0,
                "chapters": [
                    {
                        "id": generate_id(),
                        "name": "Kinematics & Projectile Motion",
                        "priority": "High",
                        "weightage": "High (8-12 M)",
                        "due_date": "",
                        "progress": 0.0,
                        "notes": "",
                        "tasks": [
                            {
                                "id": generate_id(),
                                "title": "Theory & 1D Motion Equations",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Easy",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "2D Motion & Projectile Problems",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Relative Velocity in 2D",
                                "completed": False,
                                "priority": "Medium",
                                "difficulty": "Hard",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": [
                                    {
                                        "id": generate_id(),
                                        "title": "Rain-Man & River-Boat Problems",
                                        "completed": False,
                                        "priority": "High",
                                        "difficulty": "Hard",
                                        "due_date": "",
                                        "progress": 0.0,
                                        "subtasks": []
                                    },
                                    {
                                        "id": generate_id(),
                                        "title": "Wind-Airplane Motion",
                                        "completed": False,
                                        "priority": "Medium",
                                        "difficulty": "Medium",
                                        "due_date": "",
                                        "progress": 0.0,
                                        "subtasks": []
                                    }
                                ]
                            },
                            {
                                "id": generate_id(),
                                "title": "Solve 2019-2024 PYQs",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Hard",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            }
                        ]
                    },
                    {
                        "id": generate_id(),
                        "name": "Laws of Motion & Friction",
                        "priority": "High",
                        "weightage": "High (8-12 M)",
                        "due_date": "",
                        "progress": 0.0,
                        "notes": "",
                        "tasks": [
                            {
                                "id": generate_id(),
                                "title": "Free Body Diagrams & Newton's 2nd Law",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Pulley & Constraint Systems",
                                "completed": False,
                                "priority": "Medium",
                                "difficulty": "Hard",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Static & Kinetic Friction Problems",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            }
                        ]
                    }
                ]
            },
            "Chemistry": {
                "progress": 0.0,
                "chapters": [
                    {
                        "id": generate_id(),
                        "name": "Chemical Bonding & Molecular Structure",
                        "priority": "High",
                        "weightage": "High (8-12 M)",
                        "due_date": "",
                        "progress": 0.0,
                        "notes": "",
                        "tasks": [
                            {
                                "id": generate_id(),
                                "title": "VSEPR Theory & Shapes of Molecules",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Easy",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Hybridization (sp, sp2, sp3, sp3d)",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Molecular Orbital Theory (MOT) & Bond Order",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Hard",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Dipole Moments & Hydrogen Bonding",
                                "completed": False,
                                "priority": "Medium",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            }
                        ]
                    },
                    {
                        "id": generate_id(),
                        "name": "Atomic Structure",
                        "priority": "Medium",
                        "weightage": "Medium (4-8 M)",
                        "due_date": "",
                        "progress": 0.0,
                        "notes": "",
                        "tasks": [
                            {
                                "id": generate_id(),
                                "title": "Bohr's Model & Rydberg Formula",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "de Broglie Wavelength & Heisenberg Uncertainty",
                                "completed": False,
                                "priority": "Medium",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Quantum Numbers & Electronic Configurations",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Easy",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            }
                        ]
                    }
                ]
            },
            "Mathematics": {
                "progress": 0.0,
                "chapters": [
                    {
                        "id": generate_id(),
                        "name": "Quadratic Equations",
                        "priority": "High",
                        "weightage": "Medium (4-8 M)",
                        "due_date": "",
                        "progress": 0.0,
                        "notes": "",
                        "tasks": [
                            {
                                "id": generate_id(),
                                "title": "Roots, Discriminant, & Nature of Roots",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Easy",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Location of Roots (Advanced Conditions)",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Hard",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Transformation of Equations & Symmetric Functions",
                                "completed": False,
                                "priority": "Medium",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            }
                        ]
                    },
                    {
                        "id": generate_id(),
                        "name": "Matrices & Determinants",
                        "priority": "High",
                        "weightage": "High (8-12 M)",
                        "due_date": "",
                        "progress": 0.0,
                        "notes": "",
                        "tasks": [
                            {
                                "id": generate_id(),
                                "title": "Matrix Multiplication & Properties",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Easy",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Determinant Properties & Row/Col Operations",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Medium",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            },
                            {
                                "id": generate_id(),
                                "title": "Adjoint, Inverse, & System of Linear Equations (Cramer's Rule)",
                                "completed": False,
                                "priority": "High",
                                "difficulty": "Hard",
                                "due_date": "",
                                "progress": 0.0,
                                "subtasks": []
                            }
                        ]
                    }
                ]
            }
        }
    }
    return recalculate_all_progress(data)


# =====================================================================
# AUTOMATIC SCHEMA MIGRATION (BACKWARD COMPATIBILITY)
# =====================================================================

def migrate_tasks_schema(tasks: List[Dict[str, Any]]) -> None:
    """Ensures every task and nested subtask has valid priority, difficulty, due_date, and estimated_minutes fields."""
    for task in tasks:
        if "priority" not in task or task["priority"] not in PRIORITY_OPTIONS:
            task["priority"] = "Medium"
        if "difficulty" not in task or task["difficulty"] not in DIFFICULTY_OPTIONS:
            task["difficulty"] = "Medium"
        if "due_date" not in task:
            task["due_date"] = ""
        if "estimated_minutes" not in task:
            task["estimated_minutes"] = 0
        if "subtasks" not in task:
            task["subtasks"] = []
        migrate_tasks_schema(task["subtasks"])


def ensure_schema_migration(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upgrades older study_data.json files automatically so new features
    (Dark Mode, Countdown, Pomodoro Stats, Priority Tags, Streaks, Revisions,
    Daily Logging, Difficulty, Notes, Daily Goal, Auto Dark Mode, Weightage, Due Dates, Mock Tests,
    Custom Formulas, Chapter Resources, Ad-Hoc Tasks, Estimated Minutes)
    work seamlessly without losing data.
    """
    if "settings" not in data:
        data["settings"] = {
            "dark_mode": True,
            "target_exam_date": "2028-01-24T09:00:00",
            "daily_goal_minutes": 360,
            "auto_dark_mode": False
        }
    else:
        data["settings"].setdefault("dark_mode", True)
        data["settings"].setdefault("target_exam_date", "2028-01-24T09:00:00")
        data["settings"].setdefault("daily_goal_minutes", 360)
        data["settings"].setdefault("auto_dark_mode", False)

    if "pomodoro_stats" not in data:
        data["pomodoro_stats"] = {
            "sessions_completed": 0,
            "total_minutes": 0
        }

    if "daily_focus" not in data:
        data["daily_focus"] = {"date": get_today_key(), "items": []}
    else:
        data["daily_focus"].setdefault("date", get_today_key())
        data["daily_focus"].setdefault("items", [])

    # Streak migration
    if "streak" not in data:
        data["streak"] = {"current": 0, "best": 0, "last_active_date": ""}
    else:
        data["streak"].setdefault("current", 0)
        data["streak"].setdefault("best", 0)
        data["streak"].setdefault("last_active_date", "")

    # Daily log migration
    if "daily_log" not in data:
        data["daily_log"] = {}

    # Revision schedule migration
    if "revision_schedule" not in data:
        data["revision_schedule"] = []

    # Mock tests migration
    if "mock_tests" not in data:
        data["mock_tests"] = []
    for test in data.get("mock_tests", []):
        test.setdefault("attempted", 0)
        test.setdefault("correct", 0)
        test.setdefault("incorrect", 0)
        test.setdefault("unattempted", 0)
        test.setdefault("silly_errors", 0)
        test.setdefault("conceptual_errors", 0)
        test.setdefault("time_pressure", 0)

    # Custom formulas migration
    cf = data.setdefault("custom_formulas", {})
    for s in ["Physics", "Chemistry", "Mathematics"]:
        cf.setdefault(s, {})

    # Chapter resources migration
    data.setdefault("chapter_resources", {})

    for subject_data in data.get("subjects", {}).values():
        for chapter in subject_data.get("chapters", []):
            if "priority" not in chapter or chapter["priority"] not in PRIORITY_OPTIONS:
                chapter["priority"] = "High"
            if "weightage" not in chapter or chapter["weightage"] not in WEIGHTAGE_OPTIONS:
                chapter["weightage"] = "Medium (4-8 M)"
            if "due_date" not in chapter:
                chapter["due_date"] = ""
            if "notes" not in chapter:
                chapter["notes"] = ""
            migrate_tasks_schema(chapter.get("tasks", []))

    ensure_daily_focus(data)
    return data


def ensure_daily_focus(data: Dict[str, Any]) -> None:
    """Keeps the planner aligned with today and the current task list without resetting user completions or custom ad-hoc tasks."""
    today_key = get_today_key()
    planner = data.setdefault("daily_focus", {"date": today_key, "items": []})

    if planner.get("date") != today_key:
        planner["date"] = today_key

    current_items = planner.get("items", [])
    current_map = {item.get("key"): item for item in current_items if item.get("key")}
    custom_items = [it for it in current_items if it.get("is_custom")]
    generated = generate_daily_plan(data)

    updated_items = []
    for item in generated:
        saved = current_map.get(item["key"])
        item["done"] = bool(saved.get("done", False)) if saved else False
        if saved and "estimated_minutes" in saved and saved.get("estimated_minutes", 0) > 0:
            item["estimated_minutes"] = saved["estimated_minutes"]
        updated_items.append(item)
    planner["items"] = updated_items + custom_items


# =====================================================================
# RECURSIVE STATE & PROGRESS ENGINE
# =====================================================================

def recalculate_task_node(task: Dict[str, Any]) -> float:
    """Recursively calculates completion percentage of a task based on its subtasks."""
    subtasks = task.get("subtasks", [])
    if not subtasks:
        task["progress"] = 100.0 if task.get("completed", False) else 0.0
        return task["progress"]

    total_sub_progress = sum(recalculate_task_node(sub) for sub in subtasks)
    avg_progress = round(total_sub_progress / len(subtasks), 1)
    task["progress"] = avg_progress
    task["completed"] = (avg_progress == 100.0)
    return task["progress"]


def recalculate_all_progress(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recalculates bottom-up completion percentages for every task, chapter, and subject."""
    for subject_name, subject_data in data["subjects"].items():
        chapters = subject_data.get("chapters", [])
        if not chapters:
            subject_data["progress"] = 0.0
            continue

        total_chapter_progress = 0.0
        for chapter in chapters:
            tasks = chapter.get("tasks", [])
            if not tasks:
                chapter["progress"] = 0.0
            else:
                total_task_progress = sum(recalculate_task_node(task) for task in tasks)
                chapter["progress"] = round(total_task_progress / len(tasks), 1)
            total_chapter_progress += chapter["progress"]

        subject_data["progress"] = round(total_chapter_progress / len(chapters), 1)

    return data


def set_descendants_completed(task: Dict[str, Any], completed_state: bool) -> None:
    """Recursively propagates completion state down to all subtasks."""
    task["completed"] = completed_state
    task["progress"] = 100.0 if completed_state else 0.0
    for sub in task.get("subtasks", []):
        set_descendants_completed(sub, completed_state)


def toggle_daily_focus_item(data: Dict[str, Any], item_key: str, done: bool) -> bool:
    """
    Updates the persisted completion state for one daily planner item and
    synchronizes the completion status with the underlying syllabus task.
    Returns True if the parent chapter reached 100% completion as a result.
    """
    planner = data.setdefault("daily_focus", {"date": get_today_key(), "items": []})
    matched_item = None
    for item in planner.get("items", []):
        if item.get("key") == item_key:
            item["done"] = bool(done)
            matched_item = item
            break

    # Synchronize back with the actual chapter task in the syllabus tree
    parts = item_key.split(":")
    just_finished_chapter = False
    if len(parts) >= 3 and not item_key.startswith("custom:"):
        subj, chap_id, task_id = parts[0], parts[1], parts[2]
        if subj in data.get("subjects", {}):
            for ch in data["subjects"][subj].get("chapters", []):
                if ch["id"] == chap_id:
                    target = find_task_recursive(ch.get("tasks", []), task_id)
                    if target:
                        set_descendants_completed(target, bool(done))
                    break

    # When marking a focus item done, update streak and log activity
    if done:
        update_streak(data)
        item_mins = matched_item.get("estimated_minutes", 0) if matched_item else 0
        item_subj = matched_item.get("subject") if matched_item and matched_item.get("subject") in ["Physics", "Chemistry", "Mathematics"] else None
        log_daily_activity(data, minutes=item_mins, tasks_done=1, subject=item_subj)

    save_data(data)

    # Check if the chapter reached 100% and auto-schedule spaced revision
    if len(parts) >= 3 and done and not item_key.startswith("custom:"):
        subj, chap_id = parts[0], parts[1]
        if subj in data.get("subjects", {}):
            for ch in data["subjects"][subj].get("chapters", []):
                if ch["id"] == chap_id and ch.get("progress", 0.0) >= 100.0:
                    scheduled = schedule_revision(data, subj, chap_id, ch.get("name", "Chapter"))
                    if scheduled:
                        just_finished_chapter = True
                    break

    return just_finished_chapter


def add_custom_daily_task(
    data: Dict[str, Any],
    title: str,
    estimated_minutes: int = 30,
    subject: str = "General",
    priority: str = "Medium"
) -> Dict[str, Any]:
    """Adds an ad-hoc custom daily focus task (e.g. video lecture, test analysis, doubt clearing)."""
    if not title.strip():
        return {}
    planner = data.setdefault("daily_focus", {"date": get_today_key(), "items": []})
    custom_id = generate_id()
    item = {
        "key": f"custom:{custom_id}",
        "subject": subject if subject in ["Physics", "Chemistry", "Mathematics"] else "General",
        "chapter_id": "",
        "chapter_name": "Ad-Hoc / Custom",
        "title": title.strip(),
        "priority": priority if priority in PRIORITY_OPTIONS else "Medium",
        "difficulty": "Medium",
        "due_date": get_today_key(),
        "estimated_minutes": max(0, int(estimated_minutes)),
        "is_custom": True,
        "done": False
    }
    planner.setdefault("items", []).append(item)
    save_data(data)
    return item


def delete_custom_daily_task(data: Dict[str, Any], item_key: str) -> None:
    """Removes a custom ad-hoc task from the daily focus planner."""
    planner = data.setdefault("daily_focus", {"date": get_today_key(), "items": []})
    planner["items"] = [it for it in planner.get("items", []) if it.get("key") != item_key]
    save_data(data)


# =====================================================================
# LOCAL STORAGE PERSISTENCE (LOAD & SAVE JSON)
# =====================================================================

def load_data() -> Dict[str, Any]:
    """Loads study data from the local JSON file, migrating schema if needed."""
    if not os.path.exists(DATA_FILE):
        initial_data = get_initial_data()
        save_data(initial_data)
        return initial_data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data = ensure_schema_migration(data)
        save_data(data)
        return data
    except (json.JSONDecodeError, IOError):
        initial_data = get_initial_data()
        save_data(initial_data)
        return initial_data


def save_data(data: Dict[str, Any]) -> None:
    """Recalculates all progress and writes the updated data to study_data.json."""
    recalculate_all_progress(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================================================================
# SETTINGS & POMODORO PERSISTENCE
# =====================================================================

def set_dark_mode(data: Dict[str, Any], is_dark: bool) -> None:
    """Saves the user's Dark Mode preference."""
    data["settings"]["dark_mode"] = is_dark
    save_data(data)


def log_pomodoro_session(data: Dict[str, Any], minutes_completed: int, subject: Optional[str] = None) -> None:
    """Increments completed Pomodoro count and adds focused minutes to persistent storage, optionally tagging a subject."""
    data["pomodoro_stats"]["sessions_completed"] += 1
    data["pomodoro_stats"]["total_minutes"] += max(1, int(minutes_completed))
    # Also log daily activity and update streak
    log_daily_activity(data, minutes=max(1, int(minutes_completed)), subject=subject)
    update_streak(data)
    save_data(data)


def reset_pomodoro_stats(data: Dict[str, Any]) -> None:
    """Resets logged Pomodoro sessions and minutes back to zero."""
    data["pomodoro_stats"]["sessions_completed"] = 0
    data["pomodoro_stats"]["total_minutes"] = 0
    save_data(data)


# =====================================================================
# CHAPTER CRUD OPERATIONS
# =====================================================================

def add_chapter(
    data: Dict[str, Any],
    subject: str,
    chapter_name: str,
    priority: str = "High",
    weightage: str = "Medium (4-8 M)",
    due_date: str = ""
) -> None:
    """Adds a new chapter with priority, weightage, and optional due date to the specified subject."""
    if not chapter_name.strip():
        return
    new_chapter = {
        "id": generate_id(),
        "name": chapter_name.strip(),
        "priority": priority if priority in PRIORITY_OPTIONS else "Medium",
        "weightage": weightage if weightage in WEIGHTAGE_OPTIONS else "Medium (4-8 M)",
        "due_date": due_date.strip() if due_date else "",
        "progress": 0.0,
        "notes": "",
        "tasks": []
    }
    data["subjects"][subject]["chapters"].append(new_chapter)
    save_data(data)


def edit_chapter(
    data: Dict[str, Any],
    subject: str,
    chapter_id: str,
    new_name: str,
    new_priority: str = "High",
    new_weightage: Optional[str] = None,
    new_due_date: Optional[str] = None
) -> None:
    """Updates the title, priority, weightage, and due date of an existing chapter."""
    if not new_name.strip():
        return
    for chapter in data["subjects"][subject]["chapters"]:
        if chapter["id"] == chapter_id:
            chapter["name"] = new_name.strip()
            if new_priority in PRIORITY_OPTIONS:
                chapter["priority"] = new_priority
            if new_weightage is not None and new_weightage in WEIGHTAGE_OPTIONS:
                chapter["weightage"] = new_weightage
            if new_due_date is not None:
                chapter["due_date"] = new_due_date.strip()
            break
    save_data(data)


def delete_chapter(data: Dict[str, Any], subject: str, chapter_id: str) -> None:
    """Removes a chapter and all its tasks from a subject."""
    chapters = data["subjects"][subject]["chapters"]
    data["subjects"][subject]["chapters"] = [c for c in chapters if c["id"] != chapter_id]
    save_data(data)


def move_chapter(data: Dict[str, Any], subject: str, chapter_id: str, direction: str) -> None:
    """Moves a chapter up or down in the list order. direction must be 'up' or 'down'."""
    chapters = data["subjects"][subject]["chapters"]
    idx = next((i for i, c in enumerate(chapters) if c["id"] == chapter_id), None)
    if idx is None:
        return
    if direction == "up" and idx > 0:
        chapters[idx], chapters[idx - 1] = chapters[idx - 1], chapters[idx]
    elif direction == "down" and idx < len(chapters) - 1:
        chapters[idx], chapters[idx + 1] = chapters[idx + 1], chapters[idx]
    save_data(data)


# =====================================================================
# RECURSIVE TASK CRUD OPERATIONS (N-LEVEL DEEP)
# =====================================================================

def find_task_recursive(tasks: List[Dict[str, Any]], target_id: str) -> Optional[Dict[str, Any]]:
    """Recursively searches an n-level task list for a task matching target_id."""
    for task in tasks:
        if task["id"] == target_id:
            return task
        found = find_task_recursive(task.get("subtasks", []), target_id)
        if found:
            return found
    return None


def delete_task_recursive(tasks: List[Dict[str, Any]], target_id: str) -> bool:
    """Recursively finds and deletes a task (and its subtasks) at any depth."""
    for i, task in enumerate(tasks):
        if task["id"] == target_id:
            tasks.pop(i)
            return True
        if delete_task_recursive(task.get("subtasks", []), target_id):
            return True
    return False


def add_task(
    data: Dict[str, Any],
    subject: str,
    chapter_id: str,
    title: str,
    priority: str = "Medium",
    parent_task_id: Optional[str] = None,
    difficulty: str = "Medium",
    due_date: str = "",
    estimated_minutes: int = 0
) -> None:
    """
    Adds a task with priority, difficulty, optional due date, and estimated minutes either at the root
    level of a chapter or nested inside an existing task at any depth.
    """
    if not title.strip():
        return

    new_task = {
        "id": generate_id(),
        "title": title.strip(),
        "completed": False,
        "priority": priority if priority in PRIORITY_OPTIONS else "Medium",
        "difficulty": difficulty if difficulty in DIFFICULTY_OPTIONS else "Medium",
        "due_date": due_date.strip() if due_date else "",
        "estimated_minutes": max(0, int(estimated_minutes)),
        "progress": 0.0,
        "subtasks": []
    }

    for chapter in data["subjects"][subject]["chapters"]:
        if chapter["id"] == chapter_id:
            if parent_task_id is not None:
                parent_task = find_task_recursive(chapter["tasks"], parent_task_id)
                if parent_task is not None:
                    parent_task.setdefault("subtasks", []).append(new_task)
            else:
                chapter["tasks"].append(new_task)
            break

    save_data(data)


def edit_task(
    data: Dict[str, Any],
    subject: str,
    chapter_id: str,
    task_id: str,
    new_title: str,
    new_priority: str = "Medium",
    new_difficulty: Optional[str] = None,
    new_due_date: Optional[str] = None,
    new_estimated_minutes: Optional[int] = None
) -> None:
    """Renames any task/subtask and updates its priority, difficulty, due date, and estimated duration at any depth."""
    if not new_title.strip():
        return
    for chapter in data["subjects"][subject]["chapters"]:
        if chapter["id"] == chapter_id:
            target = find_task_recursive(chapter["tasks"], task_id)
            if target is not None:
                target["title"] = new_title.strip()
                if new_priority in PRIORITY_OPTIONS:
                    target["priority"] = new_priority
                if new_difficulty is not None and new_difficulty in DIFFICULTY_OPTIONS:
                    target["difficulty"] = new_difficulty
                if new_due_date is not None:
                    target["due_date"] = new_due_date.strip()
                if new_estimated_minutes is not None:
                    target["estimated_minutes"] = max(0, int(new_estimated_minutes))
            break
    save_data(data)


def delete_task(data: Dict[str, Any], subject: str, chapter_id: str, task_id: str) -> None:
    """Deletes a task or subtask at any depth and recalculates parent completion."""
    for chapter in data["subjects"][subject]["chapters"]:
        if chapter["id"] == chapter_id:
            delete_task_recursive(chapter["tasks"], task_id)
            break
    save_data(data)


def toggle_task(
    data: Dict[str, Any],
    subject: str,
    chapter_id: str,
    task_id: str,
    new_completed_state: bool
) -> bool:
    """
    Toggles a task's checked state and cascades updates up and down the tree.
    Returns True if the chapter newly hit 100% completion and was auto-scheduled for spaced revision.
    """
    target_chapter = None
    was_100 = False
    for chapter in data["subjects"][subject]["chapters"]:
        if chapter["id"] == chapter_id:
            target_chapter = chapter
            was_100 = (chapter.get("progress", 0.0) >= 100.0)
            target = find_task_recursive(chapter["tasks"], task_id)
            if target is not None:
                set_descendants_completed(target, new_completed_state)
            break

    # When marking a task done, update streak and log activity
    if new_completed_state:
        update_streak(data)
        log_daily_activity(data, tasks_done=1)

    save_data(data)

    just_finished = False
    if target_chapter and not was_100 and target_chapter.get("progress", 0.0) >= 100.0:
        scheduled = schedule_revision(data, subject, chapter_id, target_chapter.get("name", "Chapter"))
        if scheduled:
            just_finished = True

    return just_finished


# =====================================================================
# STUDY STREAK TRACKER
# =====================================================================

def update_streak(data: Dict[str, Any]) -> None:
    """Updates the study streak based on activity dates. Called internally by other functions."""
    streak = data.setdefault("streak", {"current": 0, "best": 0, "last_active_date": ""})
    today_str = get_today_key()
    last_active = streak.get("last_active_date", "")

    if last_active == today_str:
        return

    if last_active:
        try:
            last_date = date.fromisoformat(last_active)
            today_date = date.today()
            diff = (today_date - last_date).days
            if diff == 1:
                streak["current"] = streak.get("current", 0) + 1
            elif diff > 1:
                streak["current"] = 1
        except Exception:
            streak["current"] = 1
    else:
        streak["current"] = 1

    if streak["current"] > streak.get("best", 0):
        streak["best"] = streak["current"]

    streak["last_active_date"] = today_str


def get_streak(data: Dict[str, Any]) -> Dict[str, int]:
    """Returns current and best streak counters."""
    streak = data.get("streak", {"current": 0, "best": 0})
    return {"current": streak.get("current", 0), "best": streak.get("best", 0)}


def log_daily_activity(
    data: Dict[str, Any],
    minutes: int = 0,
    tasks_done: int = 0,
    subject: Optional[str] = None
) -> None:
    """Logs study time and/or completed tasks to today's entry in data['daily_log']."""
    today_str = get_today_key()
    daily_log = data.setdefault("daily_log", {})
    entry = daily_log.setdefault(
        today_str,
        {"minutes": 0, "tasks_done": 0, "subjects": {"Physics": 0, "Chemistry": 0, "Mathematics": 0}}
    )
    entry.setdefault("subjects", {"Physics": 0, "Chemistry": 0, "Mathematics": 0})

    if minutes > 0:
        entry["minutes"] = entry.get("minutes", 0) + minutes
        if subject and subject in entry["subjects"]:
            entry["subjects"][subject] = entry["subjects"].get(subject, 0) + minutes

    if tasks_done > 0:
        entry["tasks_done"] = entry.get("tasks_done", 0) + tasks_done


def get_subject_time_totals(data: Dict[str, Any]) -> Dict[str, int]:
    """Returns total minutes logged per subject across all recorded dates."""
    totals = {"Physics": 0, "Chemistry": 0, "Mathematics": 0}
    for entry in data.get("daily_log", {}).values():
        if isinstance(entry, dict) and "subjects" in entry:
            for s, m in entry["subjects"].items():
                if s in totals and isinstance(m, (int, float)):
                    totals[s] += int(m)
    return totals


def get_today_minutes(data: Dict[str, Any]) -> int:
    """Returns total minutes studied today."""
    today_str = get_today_key()
    entry = data.get("daily_log", {}).get(today_str, {})
    return entry.get("minutes", 0) if isinstance(entry, dict) else 0


# =====================================================================
# REVISION SCHEDULER (SPACED REPETITION)
# =====================================================================

def schedule_revision(
    data: Dict[str, Any],
    subject: str,
    chapter_id: str,
    chapter_name: str
) -> bool:
    """
    Schedules spaced repetition reviews at +1, +3, +7, +21 days from today
    when a chapter hits 100% completion.
    Avoids duplicate entries if active pending reviews already exist for this chapter.
    Returns True if reviews were scheduled, False if already scheduled.
    """
    schedule = data.setdefault("revision_schedule", [])
    pending = [r for r in schedule if r.get("chapter_id") == chapter_id and not r.get("completed", False)]
    if pending:
        return False

    today = date.today()
    intervals = [1, 3, 7, 21]

    for interval in intervals:
        scheduled_date = (today + timedelta(days=interval)).isoformat()
        entry = {
            "id": generate_id(),
            "subject": subject,
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
            "scheduled_date": scheduled_date,
            "interval_days": interval,
            "completed": False
        }
        schedule.append(entry)

    save_data(data)
    return True


def get_due_revisions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Returns revision entries that are due today or overdue and not yet completed."""
    today_str = get_today_key()
    due = []
    for r in data.get("revision_schedule", []):
        if not r.get("completed", False) and r.get("scheduled_date", "") <= today_str:
            due.append(r)
    due.sort(key=lambda x: x.get("scheduled_date", ""))
    return due


def get_upcoming_revisions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Returns future scheduled revisions that are not yet due."""
    today_str = get_today_key()
    upcoming = []
    for r in data.get("revision_schedule", []):
        if not r.get("completed", False) and r.get("scheduled_date", "") > today_str:
            upcoming.append(r)
    upcoming.sort(key=lambda x: x.get("scheduled_date", ""))
    return upcoming


def complete_revision(data: Dict[str, Any], revision_id: str) -> None:
    """Marks a scheduled revision review as completed."""
    for r in data.get("revision_schedule", []):
        if r.get("id") == revision_id:
            r["completed"] = True
            break
    save_data(data)


# =====================================================================
# NOTES / MISTAKE LOG PER CHAPTER
# =====================================================================

def save_chapter_notes(data: Dict[str, Any], subject: str, chapter_id: str, notes_text: str) -> None:
    """Saves note / mistake log text for a specific chapter."""
    for chapter in data["subjects"][subject]["chapters"]:
        if chapter["id"] == chapter_id:
            chapter["notes"] = notes_text
            break
    save_data(data)


def get_chapter_notes(data: Dict[str, Any], subject: str, chapter_id: str) -> str:
    """Returns the note / mistake log for a chapter."""
    for chapter in data["subjects"][subject]["chapters"]:
        if chapter["id"] == chapter_id:
            return chapter.get("notes", "")
    return ""


# =====================================================================
# PROGRESS MILESTONES & BADGES
# =====================================================================

def calculate_badges(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluates milestones and returns a list of unlocked badges with icons and labels."""
    badges = []
    subjects = data.get("subjects", {})

    # Subject milestones (25%, 50%, 75%, 100%)
    subject_icons = {"Physics": "⚛️", "Chemistry": "🧪", "Mathematics": "📐"}
    for subj_name, icon in subject_icons.items():
        prog = subjects.get(subj_name, {}).get("progress", 0.0)
        if prog >= 25:
            badges.append({"icon": icon, "label": f"{subj_name} Quarter Way (25%)", "earned": True})
        if prog >= 50:
            badges.append({"icon": icon, "label": f"{subj_name} Halfway Mark (50%)", "earned": True})
        if prog >= 75:
            badges.append({"icon": icon, "label": f"{subj_name} Deep Mastery (75%)", "earned": True})
        if prog >= 100:
            badges.append({"icon": "🏆", "label": f"{subj_name} 100% Mastered!", "earned": True})

    # Overall syllabus mastery
    total_prog = sum(s.get("progress", 0.0) for s in subjects.values()) / max(1, len(subjects))
    if total_prog >= 50:
        badges.append({"icon": "🌟", "label": "Halfway to IIT (50% Overall)", "earned": True})
    if total_prog >= 100:
        badges.append({"icon": "👑", "label": "JEE 2028 Ready (100% Overall)!", "earned": True})

    # Streak badges
    streak = data.get("streak", {}).get("best", 0)
    if streak >= 3:
        badges.append({"icon": "🔥", "label": "3-Day Consistency Streak", "earned": True})
    if streak >= 7:
        badges.append({"icon": "⚡", "label": "7-Day Power Streak", "earned": True})
    if streak >= 30:
        badges.append({"icon": "🚀", "label": "30-Day Relentless Habit", "earned": True})
    if streak >= 100:
        badges.append({"icon": "💎", "label": "100-Day Diamond Discipline", "earned": True})

    # Pomodoro badges
    pomo_sessions = data.get("pomodoro_stats", {}).get("sessions_completed", 0)
    if pomo_sessions >= 10:
        badges.append({"icon": "🍅", "label": "10 Focus Sessions", "earned": True})
    if pomo_sessions >= 50:
        badges.append({"icon": "🎯", "label": "50 Focus Sessions", "earned": True})
    if pomo_sessions >= 100:
        badges.append({"icon": "🧠", "label": "100 Focus Sessions", "earned": True})

    # Mock test badges
    mock_count = len(data.get("mock_tests", []))
    if mock_count >= 1:
        badges.append({"icon": "📝", "label": "First Mock Test Taken", "earned": True})
    if mock_count >= 5:
        badges.append({"icon": "📊", "label": "5 Mock Tests Analysed", "earned": True})
    if mock_count >= 10:
        badges.append({"icon": "🎖️", "label": "10 Mock Tests Veteran", "earned": True})

    return badges


# =====================================================================
# DAILY STUDY GOAL
# =====================================================================

def set_daily_goal(data: Dict[str, Any], minutes: int) -> None:
    """Sets the daily target study goal in minutes."""
    data.setdefault("settings", {})["daily_goal_minutes"] = max(15, int(minutes))
    save_data(data)


def get_daily_goal(data: Dict[str, Any]) -> int:
    """Returns the daily target study goal in minutes (default: 360 min = 6 hrs)."""
    return data.get("settings", {}).get("daily_goal_minutes", 360)


# =====================================================================
# AUTO DARK MODE SETTING
# =====================================================================

def set_auto_dark_mode(data: Dict[str, Any], enabled: bool) -> None:
    """Enables or disables automatic day/night dark mode toggling."""
    data.setdefault("settings", {})["auto_dark_mode"] = bool(enabled)
    save_data(data)


def get_auto_dark_mode(data: Dict[str, Any]) -> bool:
    """Returns whether auto dark mode is enabled."""
    return data.get("settings", {}).get("auto_dark_mode", False)


# =====================================================================
# FORMULA QUICK REFERENCE (HANDBOOK DATA)
# =====================================================================

def get_formula_reference() -> Dict[str, Dict[str, List[str]]]:
    """Returns a curated handbook of high-yield JEE Main formulas across all 3 subjects."""
    return {
        "Physics": {
            "Kinematics": ["v = u + at", "s = ut + ½at²", "v² = u² + 2as", "s_n = u + a/2(2n - 1)"],
            "Newton's Laws & Friction": ["F = ma", "f_s ≤ μ_s·N", "f_k = μ_k·N", "F_net = dp/dt"],
            "Work, Energy & Power": ["W = ∫F·dr = ΔKE", "KE = ½mv²", "P = F·v = dW/dt", "W_nc = ΔE_mech"],
            "Rotational Motion": ["τ = Iα = r × F", "L = Iω = r × p", "KE_rot = ½Iω²", "I_parallel = I_cm + Md²"],
            "Gravitation": ["F = GMm/r²", "g = GM/R²", "v_orb = √(GM/R)", "v_escape = √(2gR)"],
            "Electrostatics": ["F = kq₁q₂/r²", "E = kq/r²", "V = kq/r", "U = kq₁q₂/r"],
            "Current Electricity": ["V = IR", "P = VI = I²R = V²/R", "R = ρl/A", "Kirchhoff: ΣI = 0, ΣV = 0"],
            "Magnetism": ["F = q(v × B)", "F = I(l × B)", "B_wire = μ₀I/(2πr)", "B_solenoid = μ₀nI"],
            "Optics": ["1/f = 1/v - 1/u", "n₁ sin θ₁ = n₂ sin θ₂", "Power = 1/f(m)", "Magnification m = -v/u"],
            "Modern Physics": ["E = hν = hc/λ", "KE_max = hν - Φ", "λ = h/p = h/√(2mE)", "r_n = 0.529 n²/Z Å"]
        },
        "Chemistry": {
            "Atomic Structure": ["E_n = -13.6 Z²/n² eV", "λ = h/mv", "Δx·Δp ≥ h/(4π)", "v_n = 2.18 × 10⁶ Z/n m/s"],
            "Chemical Bonding": ["Bond Order = (N_b - N_a)/2", "Dipole Moment μ = q × d", "Formal Charge = V - L - ½B"],
            "Thermodynamics": ["ΔU = q + w", "w = -P_ext ΔV", "ΔH = ΔU + Δn_g RT", "ΔG = ΔH - TΔS", "ΔG° = -RT ln K"],
            "Equilibrium": ["K_p = K_c(RT)^Δn", "pH = -log[H⁺]", "pH + pOH = 14", "Buffer: pH = pKa + log([Salt]/[Acid])"],
            "Electrochemistry": ["E°_cell = E°_cathode - E°_anode", "ΔG° = -nFE°_cell", "E_cell = E° - (0.0591/n) log Q"],
            "Chemical Kinetics": ["Rate = k[A]^x[B]^y", "Zero order: [A] = [A]₀ - kt", "1st order: t_½ = 0.693/k", "k = A e^(-Ea/RT)"],
            "Solutions": ["P_A = P°_A · X_A", "ΔT_b = i·K_b·m", "ΔT_f = i·K_f·m", "π = i·CRT"]
        },
        "Mathematics": {
            "Quadratics": ["x = (-b ± √(b² - 4ac))/(2a)", "Sum = -b/a, Product = c/a", "D = b² - 4ac", "Roots real & equal if D = 0"],
            "Sequences & Series": ["AP: T_n = a + (n-1)d", "AP: S_n = n/2[2a + (n-1)d]", "GP: T_n = ar^(n-1)", "GP: S_∞ = a/(1-r) (|r|<1)"],
            "Trigonometry": ["sin²θ + cos²θ = 1", "sin(A±B) = sinA cosB ± cosA sinB", "cos(A±B) = cosA cosB ∓ sinA sinB", "tan2θ = 2tanθ/(1-tan²θ)"],
            "Differential Calculus": ["d/dx(xⁿ) = n xⁿ⁻¹", "Product Rule: (uv)' = u'v + uv'", "Quotient Rule: (u/v)' = (u'v - uv')/v²", "Chain Rule: dy/dx = dy/du · du/dx"],
            "Integral Calculus": ["∫ xⁿ dx = x^(n+1)/(n+1) + C", "∫ e^(ax) dx = e^(ax)/a + C", "∫ 1/x dx = ln|x| + C", "By parts: ∫ u v dx = u∫v - ∫(u' ∫v)"],
            "Matrices & Determinants": ["det(AB) = det(A)·det(B)", "A·adj(A) = |A|·I", "A⁻¹ = adj(A)/|A|", "(AB)⁻¹ = B⁻¹A⁻¹"],
            "Coordinate Geometry": ["Distance: √((x₂-x₁)² + (y₂-y₁)²)", "Line: y = mx + c", "Circle: (x-h)² + (y-k)² = r²", "Dist point to line: |ax₁+by₁+c|/√(a²+b²)"],
            "Vectors & 3D": ["A·B = |A||B| cos θ", "|A × B| = |A||B| sin θ", "Line 3D: (x-x₁)/a = (y-y₁)/b = (z-z₁)/c", "Plane: ax + by + cz + d = 0"]
        }
    }


# =====================================================================
# IMPORT SYLLABUS PRESET (JEE MAIN 2025)
# =====================================================================

def _make_preset_chapter(name: str, tasks: List[str], weightage: str = "Medium (4-8 M)") -> Dict[str, Any]:
    """Helper to build a preset chapter dict with default tasks, weightage, and empty due date."""
    return {
        "id": generate_id(),
        "name": name,
        "priority": "High",
        "weightage": weightage,
        "due_date": "",
        "progress": 0.0,
        "notes": "",
        "tasks": [
            {
                "id": generate_id(),
                "title": t,
                "priority": "High",
                "difficulty": "Medium",
                "due_date": "",
                "completed": False,
                "progress": 0.0,
                "subtasks": []
            }
            for t in tasks
        ]
    }


def get_jee_main_2025_syllabus() -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a comprehensive dict with the official NTA JEE Main syllabus
    for Physics, Chemistry, and Mathematics, tagged with realistic weightages.
    """
    default_tasks = ["Complete Concept Lectures", "Solve Practice Problems", "PYQ Practice"]

    physics_chapters = [
        ("Units and Measurements", "Low (4 M)"),
        ("Kinematics", "High (8-12 M)"),
        ("Laws of Motion", "High (8-12 M)"),
        ("Work, Energy, and Power", "Medium (4-8 M)"),
        ("Rotational Motion & Moment of Inertia", "High (8-12 M)"),
        ("Gravitation", "Medium (4-8 M)"),
        ("Properties of Solids and Liquids", "Medium (4-8 M)"),
        ("Thermodynamics", "High (8-12 M)"),
        ("Kinetic Theory of Gases", "Low (4 M)"),
        ("Oscillations", "Medium (4-8 M)"),
        ("Waves", "Medium (4-8 M)"),
        ("Electrostatics", "High (8-12 M)"),
        ("Current Electricity", "High (8-12 M)"),
        ("Magnetic Effects of Current & Magnetism", "High (8-12 M)"),
        ("Electromagnetic Induction & AC", "Medium (4-8 M)"),
        ("Electromagnetic Waves", "Low (4 M)"),
        ("Optics", "High (8-12 M)"),
        ("Dual Nature of Matter and Radiation", "Medium (4-8 M)"),
        ("Atoms and Nuclei", "High (8-12 M)"),
        ("Electronic Devices (Semiconductors)", "Medium (4-8 M)")
    ]

    chemistry_chapters = [
        ("Some Basic Concepts of Chemistry", "Medium (4-8 M)"),
        ("Atomic Structure", "Medium (4-8 M)"),
        ("Chemical Bonding and Molecular Structure", "High (8-12 M)"),
        ("Chemical Thermodynamics", "High (8-12 M)"),
        ("Solutions", "Medium (4-8 M)"),
        ("Equilibrium", "High (8-12 M)"),
        ("Redox Reactions & Electrochemistry", "High (8-12 M)"),
        ("Chemical Kinetics", "Medium (4-8 M)"),
        ("States of Matter (Gases & Liquids)", "Low (4 M)"),
        ("Surface Chemistry", "Low (4 M)"),
        ("Purification & Characterisation of Organic Compounds", "Low (4 M)"),
        ("Hydrocarbons", "High (8-12 M)"),
        ("Organic Compounds Containing Halogens", "Medium (4-8 M)"),
        ("Organic Compounds Containing Oxygen", "High (8-12 M)"),
        ("Organic Compounds Containing Nitrogen", "Medium (4-8 M)"),
        ("Polymers", "Low (4 M)"),
        ("Biomolecules", "Medium (4-8 M)"),
        ("Chemistry in Everyday Life", "Low (4 M)"),
        ("Classification of Elements & Periodicity", "Medium (4-8 M)"),
        ("Hydrogen", "Low (4 M)"),
        ("s-Block Elements", "Low (4 M)"),
        ("p-Block Elements", "High (8-12 M)"),
        ("d- and f-Block Elements", "Medium (4-8 M)"),
        ("Coordination Compounds", "High (8-12 M)"),
        ("Environmental Chemistry", "Low (4 M)")
    ]

    mathematics_chapters = [
        ("Sets, Relations, and Functions", "Medium (4-8 M)"),
        ("Complex Numbers", "Medium (4-8 M)"),
        ("Quadratic Equations", "Medium (4-8 M)"),
        ("Matrices and Determinants", "High (8-12 M)"),
        ("Permutations and Combinations", "Medium (4-8 M)"),
        ("Binomial Theorem", "Medium (4-8 M)"),
        ("Sequences and Series", "High (8-12 M)"),
        ("Limits, Continuity, and Differentiability", "High (8-12 M)"),
        ("Integral Calculus", "High (8-12 M)"),
        ("Differential Equations", "High (8-12 M)"),
        ("Coordinate Geometry (Straight Lines & Circles)", "High (8-12 M)"),
        ("Conic Sections (Parabola, Ellipse, Hyperbola)", "High (8-12 M)"),
        ("Three-Dimensional Geometry", "High (8-12 M)"),
        ("Vector Algebra", "High (8-12 M)"),
        ("Trigonometry", "Medium (4-8 M)"),
        ("Mathematical Reasoning", "Low (4 M)"),
        ("Probability", "High (8-12 M)"),
        ("Statistics", "Low (4 M)")
    ]

    return {
        "Physics": [_make_preset_chapter(name, default_tasks, weightage) for name, weightage in physics_chapters],
        "Chemistry": [_make_preset_chapter(name, default_tasks, weightage) for name, weightage in chemistry_chapters],
        "Mathematics": [_make_preset_chapter(name, default_tasks, weightage) for name, weightage in mathematics_chapters]
    }


def import_preset_syllabus(data: Dict[str, Any], subject: Optional[str] = None) -> None:
    """
    Imports the JEE Main syllabus preset. If subject is None, imports all subjects.
    Merges with existing data — adds chapters that don't already exist by name.
    Does NOT delete existing chapters.
    """
    preset = get_jee_main_2025_syllabus()
    subjects_to_import = [subject] if subject else list(preset.keys())

    for subj in subjects_to_import:
        if subj not in preset or subj not in data.get("subjects", {}):
            continue

        existing_names = {
            ch["name"].strip().lower()
            for ch in data["subjects"][subj].get("chapters", [])
        }

        for preset_chapter in preset[subj]:
            if preset_chapter["name"].strip().lower() not in existing_names:
                data["subjects"][subj]["chapters"].append(preset_chapter)

    save_data(data)


# =====================================================================
# MOCK TEST & PYQ TRACKER
# =====================================================================

def add_mock_test(
    data: Dict[str, Any],
    test_name: str,
    date_str: str,
    physics_score: float,
    chem_score: float,
    math_score: float,
    total_marks: float = 300.0,
    notes: str = "",
    test_type: str = "Full Mock (300M)",
    attempted: int = 0,
    correct: int = 0,
    incorrect: int = 0,
    unattempted: int = 0,
    silly_errors: int = 0,
    conceptual_errors: int = 0,
    time_pressure: int = 0
) -> Dict[str, Any]:
    """Adds a completed mock test / PYQ test score entry with question breakdown and error categorization."""
    mock_tests = data.setdefault("mock_tests", [])
    entry = {
        "id": generate_id(),
        "name": test_name.strip() or "Mock Test",
        "date": date_str or get_today_key(),
        "physics": float(physics_score),
        "chemistry": float(chem_score),
        "mathematics": float(math_score),
        "total_score": round(float(physics_score + chem_score + math_score), 1),
        "max_marks": float(total_marks),
        "test_type": test_type,
        "notes": notes.strip(),
        "attempted": int(attempted),
        "correct": int(correct),
        "incorrect": int(incorrect),
        "unattempted": int(unattempted),
        "silly_errors": int(silly_errors),
        "conceptual_errors": int(conceptual_errors),
        "time_pressure": int(time_pressure)
    }
    mock_tests.append(entry)
    save_data(data)
    return entry


def delete_mock_test(data: Dict[str, Any], test_id: str) -> None:
    """Deletes a mock test score entry."""
    mock_tests = data.setdefault("mock_tests", [])
    data["mock_tests"] = [t for t in mock_tests if t.get("id") != test_id]
    save_data(data)


def get_mock_tests(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Returns all mock tests sorted by date (ascending)."""
    tests = list(data.get("mock_tests", []))
    tests.sort(key=lambda t: t.get("date", ""))
    return tests


# =====================================================================
# CUSTOM FORMULA & SHORTCUT BOOKMARKING
# =====================================================================

def get_custom_formulas(data: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
    """Returns user-bookmarked formulas and tricks organized by subject and topic."""
    cf = data.setdefault("custom_formulas", {})
    if not isinstance(cf, dict):
        cf = data["custom_formulas"] = {}
    for s in ["Physics", "Chemistry", "Mathematics"]:
        if not isinstance(cf.get(s), dict):
            cf[s] = {}
    return cf


def add_custom_formula(data: Dict[str, Any], subject: str, topic: str, formula_str: str) -> bool:
    """Adds a personal formula or shortcut trick to the specified subject and topic."""
    if not formula_str.strip() or not topic.strip():
        return False
    cf = get_custom_formulas(data)
    if subject not in cf:
        cf[subject] = {}
    topic_clean = topic.strip()
    if topic_clean not in cf[subject]:
        cf[subject][topic_clean] = []
    cf[subject][topic_clean].append(formula_str.strip())
    save_data(data)
    return True


def delete_custom_formula(
    data: Dict[str, Any],
    subject: str,
    topic: str,
    index: Optional[int] = None,
    formula_str: Optional[str] = None
) -> bool:
    """Deletes a custom formula by subject, topic, and list index or matching formula string."""
    cf = get_custom_formulas(data)
    if subject in cf and topic in cf[subject]:
        f_list = cf[subject][topic]
        if index is not None and 0 <= index < len(f_list):
            f_list.pop(index)
            if not f_list:
                del cf[subject][topic]
            save_data(data)
            return True
        elif formula_str is not None and formula_str in f_list:
            f_list.remove(formula_str)
            if not f_list:
                del cf[subject][topic]
            save_data(data)
            return True
    return False


def get_all_formulas(data: Dict[str, Any]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Merges preset handbook formulas with user custom bookmarked formulas.
    Returns: {subject: {topic: [{"formula": str, "is_custom": bool, "index": Optional[int]}]}}
    """
    preset = get_formula_reference()
    custom = get_custom_formulas(data)
    all_formulas: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for subj in ["Physics", "Chemistry", "Mathematics"]:
        all_formulas[subj] = {}
        # Presets first
        for topic, eq_list in preset.get(subj, {}).items():
            all_formulas[subj][topic] = [
                {"formula": eq, "is_custom": False, "index": None} for eq in eq_list
            ]
        # Custom additions
        for topic, eq_list in custom.get(subj, {}).items():
            if topic not in all_formulas[subj]:
                all_formulas[subj][topic] = []
            for idx, eq in enumerate(eq_list):
                all_formulas[subj][topic].append(
                    {"formula": eq, "is_custom": True, "index": idx}
                )
    return all_formulas


# =====================================================================
# CHAPTER RESOURCES HUB (PDFs & YOUTUBE VIDEOS)
# =====================================================================

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chapter_resources")


def get_chapter_resources(data: Dict[str, Any], subject: str, chapter_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Returns the PDFs and video links attached to a chapter."""
    cr = data.setdefault("chapter_resources", {})
    if not isinstance(cr, dict):
        cr = data["chapter_resources"] = {}
    subj_res = cr.setdefault(subject, {})
    if not isinstance(subj_res, dict):
        subj_res = cr[subject] = {}
    chap_res = subj_res.setdefault(chapter_id, {"pdfs": [], "videos": []})
    if not isinstance(chap_res, dict):
        chap_res = subj_res[chapter_id] = {"pdfs": [], "videos": []}
    chap_res.setdefault("pdfs", [])
    chap_res.setdefault("videos", [])
    return chap_res


def save_chapter_pdf(
    data: Dict[str, Any],
    subject: str,
    chapter_id: str,
    filename: str,
    file_bytes: bytes,
    title: str = ""
) -> Dict[str, Any]:
    """Saves a local PDF file into chapter_resources/ and records its metadata."""
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    pdf_id = generate_id()
    safe_fname = "".join(c for c in filename if c.isalnum() or c in "._- ")
    if not safe_fname:
        safe_fname = "document.pdf"
    stored_filename = f"{pdf_id}_{safe_fname}"
    file_path = os.path.join(RESOURCES_DIR, stored_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    res = get_chapter_resources(data, subject, chapter_id)
    entry = {
        "id": pdf_id,
        "title": title.strip() or filename,
        "filename": safe_fname,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "size_bytes": len(file_bytes),
        "uploaded_at": get_today_key()
    }
    res["pdfs"].append(entry)
    save_data(data)
    return entry


def delete_chapter_pdf(data: Dict[str, Any], subject: str, chapter_id: str, pdf_id: str) -> bool:
    """Deletes a PDF file from disk and removes its metadata."""
    res = get_chapter_resources(data, subject, chapter_id)
    found_idx = None
    for idx, p in enumerate(res.get("pdfs", [])):
        if p.get("id") == pdf_id:
            found_idx = idx
            file_path = p.get("file_path") or os.path.join(RESOURCES_DIR, p.get("stored_filename", ""))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            break
    if found_idx is not None:
        res["pdfs"].pop(found_idx)
        save_data(data)
        return True
    return False


def add_chapter_video(
    data: Dict[str, Any],
    subject: str,
    chapter_id: str,
    title: str,
    url: str,
    notes: str = ""
) -> Dict[str, Any]:
    """Attaches a YouTube video lecture or solution URL to a chapter."""
    if not url.strip():
        return {}
    res = get_chapter_resources(data, subject, chapter_id)
    entry = {
        "id": generate_id(),
        "title": title.strip() or "Video Lecture",
        "url": url.strip(),
        "notes": notes.strip(),
        "added_at": get_today_key()
    }
    res["videos"].append(entry)
    save_data(data)
    return entry


def delete_chapter_video(data: Dict[str, Any], subject: str, chapter_id: str, video_id: str) -> bool:
    """Deletes a video reference from a chapter."""
    res = get_chapter_resources(data, subject, chapter_id)
    initial_len = len(res.get("videos", []))
    res["videos"] = [v for v in res.get("videos", []) if v.get("id") != video_id]
    if len(res["videos"]) != initial_len:
        save_data(data)
        return True
    return False
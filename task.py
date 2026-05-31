#!/usr/bin/env python3
"""
AI Task Manager — add tasks in plain English, get smart reminders.

Usage:
  task add "call dentist tomorrow afternoon"
  task add "finish report by friday, high priority"
  task list
  task done <id>
  task pending
  task overdue
  task ask "what should I focus on today?"
"""

import sys, os, json, datetime, re
from pathlib import Path

TASKS_DIR  = Path.home() / ".ai_tasks"
TASKS_FILE = TASKS_DIR / "tasks.json"
TASKS_DIR.mkdir(exist_ok=True)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── storage ──────────────────────────────────────────────────────────────────

def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1

# ── AI parsing ────────────────────────────────────────────────────────────────

def ai_parse_task(raw: str) -> dict:
    """Send raw text to Claude, get back structured task JSON."""
    if not ANTHROPIC_API_KEY:
        return fallback_parse(raw)

    import anthropic
    today = datetime.date.today().isoformat()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Today is {today}.
Parse this task and return ONLY valid JSON, no extra text:
"{raw}"

Return this exact shape:
{{
  "title": "clean short task title",
  "due_date": "YYYY-MM-DD or null",
  "due_time": "HH:MM or null",
  "priority": "high | medium | low",
  "tags": ["tag1", "tag2"],
  "notes": "any extra context or null"
}}

Rules:
- "tomorrow" = {(datetime.date.today() + datetime.timedelta(days=1)).isoformat()}
- "this friday" = nearest upcoming Friday
- "end of day" = 17:00
- "morning" = 09:00, "afternoon" = 14:00, "evening" = 19:00
- priority: keywords like urgent/asap/critical → high; soon/today → medium; default → low
- tags: infer from context (work, health, finance, personal, etc.)
"""
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.content[0].text.strip()
    # strip accidental markdown fences
    text = re.sub(r"^```json|^```|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def fallback_parse(raw: str) -> dict:
    """Basic parse when no API key is set."""
    priority = "low"
    if any(w in raw.lower() for w in ["urgent","asap","critical","important"]):
        priority = "high"
    elif any(w in raw.lower() for w in ["soon","today","tonight"]):
        priority = "medium"

    due = None
    today = datetime.date.today()
    if "tomorrow" in raw.lower():
        due = (today + datetime.timedelta(days=1)).isoformat()
    elif "today" in raw.lower():
        due = today.isoformat()

    return {"title": raw.strip(), "due_date": due, "due_time": None,
            "priority": priority, "tags": [], "notes": None}


def ai_ask(question: str, tasks: list) -> str:
    """Ask Claude about your tasks."""
    if not ANTHROPIC_API_KEY:
        return "Set ANTHROPIC_API_KEY to use AI advice."

    import anthropic
    today = datetime.date.today().isoformat()
    pending = [t for t in tasks if t["status"] == "pending"]
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content":
            f"Today is {today}. Here are my pending tasks:\n"
            f"{json.dumps(pending, indent=2)}\n\n"
            f"Question: {question}\n\n"
            f"Give a concise, practical answer. No markdown headers."}]
    )
    return resp.content[0].text.strip()

# ── commands ──────────────────────────────────────────────────────────────────

def cmd_add(raw: str):
    from rich.console import Console
    from rich.panel import Panel
    from rich.spinner import Spinner
    from rich.live import Live

    console = Console()

    if ANTHROPIC_API_KEY:
        with Live(Spinner("dots", text="  AI parsing your task..."), refresh_per_second=10):
            parsed = ai_parse_task(raw)
    else:
        parsed = fallback_parse(raw)
        console.print("[dim]Tip: set ANTHROPIC_API_KEY for smarter parsing[/dim]")

    tasks = load_tasks()
    task = {
        "id":       next_id(tasks),
        "raw":      raw,
        "title":    parsed.get("title", raw),
        "due_date": parsed.get("due_date"),
        "due_time": parsed.get("due_time"),
        "priority": parsed.get("priority", "low"),
        "tags":     parsed.get("tags", []),
        "notes":    parsed.get("notes"),
        "status":   "pending",
        "created":  datetime.datetime.now().isoformat(),
        "done_at":  None
    }
    tasks.append(task)
    save_tasks(tasks)

    pri_color = {"high": "red", "medium": "yellow", "low": "green"}.get(task["priority"], "white")
    due_str = ""
    if task["due_date"]:
        due_str = f"\n  [dim]Due:[/dim] {task['due_date']}" + (f" {task['due_time']}" if task["due_time"] else "")
    tags_str = ""
    if task["tags"]:
        tags_str = f"\n  [dim]Tags:[/dim] " + " ".join(f"[cyan]#{t}[/cyan]" for t in task["tags"])
    notes_str = f"\n  [dim]Note:[/dim] {task['notes']}" if task["notes"] else ""

    console.print(Panel(
        f"[bold]{task['title']}[/bold]{due_str}{tags_str}{notes_str}\n\n"
        f"  [dim]Priority:[/dim] [{pri_color}]{task['priority'].upper()}[/{pri_color}]   [dim]ID:[/dim] #{task['id']}",
        title="[green]✅  Task added[/green]",
        border_style="green"
    ))


def _due_label(task) -> str:
    if not task.get("due_date"):
        return "[dim]—[/dim]"
    today = datetime.date.today()
    due   = datetime.date.fromisoformat(task["due_date"])
    diff  = (due - today).days
    t     = f" {task['due_time']}" if task.get("due_time") else ""
    if diff < 0:    return f"[red]overdue {task['due_date']}{t}[/red]"
    if diff == 0:   return f"[yellow]today{t}[/yellow]"
    if diff == 1:   return f"[yellow]tomorrow{t}[/yellow]"
    return f"[white]{task['due_date']}{t}[/white]"


def cmd_list(filter_status=None, only_overdue=False):
    from rich.console import Console
    from rich.table import Table

    console = Console()
    tasks = load_tasks()
    today = datetime.date.today()

    if only_overdue:
        tasks = [t for t in tasks if t["status"] == "pending"
                 and t.get("due_date")
                 and datetime.date.fromisoformat(t["due_date"]) < today]
    elif filter_status:
        tasks = [t for t in tasks if t["status"] == filter_status]

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    table = Table(show_lines=True, expand=True)
    table.add_column("#",        style="dim",    width=4)
    table.add_column("Task",     style="white",  ratio=3)
    table.add_column("Due",      ratio=2)
    table.add_column("Priority", width=10)
    table.add_column("Tags",     ratio=1)
    table.add_column("Status",   width=10)

    pri_color = {"high": "red", "medium": "yellow", "low": "green"}

    for t in sorted(tasks, key=lambda x: (x["status"] != "pending", x.get("due_date") or "9999")):
        pc    = pri_color.get(t["priority"], "white")
        tags  = " ".join(f"#{g}" for g in t.get("tags", []))
        st    = "[green]done[/green]" if t["status"] == "done" else "[cyan]pending[/cyan]"
        table.add_row(
            str(t["id"]),
            t["title"],
            _due_label(t),
            f"[{pc}]{t['priority']}[/{pc}]",
            f"[dim]{tags}[/dim]",
            st
        )

    label = "overdue" if only_overdue else (filter_status or "all")
    console.print(f"\n[bold]Tasks — {label}[/bold]  ({len(tasks)} shown)\n")
    console.print(table)


def cmd_done(task_id: int):
    from rich.console import Console
    console = Console()
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"]  = "done"
            t["done_at"] = datetime.datetime.now().isoformat()
            save_tasks(tasks)
            console.print(f"[green]✅  Marked done:[/green] {t['title']}")
            return
    console.print(f"[red]Task #{task_id} not found.[/red]")


def cmd_ask(question: str):
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.spinner import Spinner

    console = Console()
    tasks   = load_tasks()

    with Live(Spinner("dots", text="  Thinking..."), refresh_per_second=10):
        answer = ai_ask(question, tasks)

    console.print(Panel(answer, title="[cyan]AI advice[/cyan]", border_style="cyan"))


def main():
    from rich.console import Console
    from rich.table import Table
    console = Console()

    args = sys.argv[1:]
    if not args:
        t = Table(show_header=False, box=None, padding=(0, 2))
        t.add_column(style="bold cyan")
        t.add_column(style="white")
        t.add_row('add "task text"',  'Add a task in plain English')
        t.add_row("list",             "Show all tasks")
        t.add_row("pending",          "Show pending tasks only")
        t.add_row("overdue",          "Show overdue tasks")
        t.add_row("done <id>",        "Mark a task complete")
        t.add_row('ask "question"',   'Ask AI about your tasks')
        console.print(t)
        return

    cmd = args[0]

    if cmd == "add":
        if len(args) < 2:
            console.print('[red]Usage: task add "your task here"[/red]')
        else:
            cmd_add(" ".join(args[1:]))

    elif cmd == "list":
        cmd_list()

    elif cmd == "pending":
        cmd_list(filter_status="pending")

    elif cmd == "overdue":
        cmd_list(only_overdue=True)

    elif cmd == "done":
        if len(args) < 2 or not args[1].isdigit():
            console.print('[red]Usage: task done <id>[/red]')
        else:
            cmd_done(int(args[1]))

    elif cmd == "ask":
        if len(args) < 2:
            console.print('[red]Usage: task ask "your question"[/red]')
        else:
            cmd_ask(" ".join(args[1:]))

    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")


if __name__ == "__main__":
    main()

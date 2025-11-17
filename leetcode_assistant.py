import json
import os
import random
from datetime import datetime, timedelta

DATA_FILE = "leetcode_data.json"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"problems": {}, "sessions": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def input_non_empty(prompt):
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Input cannot be empty.")


def normalize_difficulty(diff):
    diff = diff.lower().strip()
    if diff in ["e", "easy"]:
        return "easy"
    if diff in ["m", "medium", "med"]:
        return "medium"
    if diff in ["h", "hard"]:
        return "hard"
    return None


def add_problem(data):
    print("\n=== Add New Problem ===")
    title = input_non_empty("Title (e.g. Two Sum): ")
    slug = input_non_empty("Slug / ID (e.g. two-sum): ")

    url_default = f"https://leetcode.com/problems/{slug}/"
    url = input(f"URL [default: {url_default}]: ").strip() or url_default

    while True:
        diff_input = input("Difficulty (easy/medium/hard): ")
        difficulty = normalize_difficulty(diff_input)
        if difficulty:
            break
        print("Invalid difficulty. Please enter easy / medium / hard.")

    topics_input = input(
        "Topics (comma-separated, e.g. array, hash-table, greedy): "
    ).strip()
    topics = [t.strip() for t in topics_input.split(",") if t.strip()]

    problem_id = slug  # we’ll use slug as unique key

    if problem_id in data["problems"]:
        print("Problem already exists. Updating its info.")
    else:
        print("Adding new problem.")

    data["problems"][problem_id] = {
        "title": title,
        "slug": slug,
        "url": url,
        "difficulty": difficulty,
        "topics": topics,
        "attempts": 0,
        "last_status": None,
        "last_practiced": None,
        "next_review": None,
    }

    save_data(data)
    print(f"Saved: {title} ({difficulty}, topics: {', '.join(topics) if topics else 'none'})")


def list_problems(data):
    problems = data["problems"]
    if not problems:
        print("\nNo problems saved yet.")
        return

    print("\n=== Problem List ===")
    for pid, p in problems.items():
        print(f"- [{pid}] {p['title']} | {p['difficulty']} | topics: {', '.join(p['topics']) or 'none'}")
        print(f"  URL: {p['url']}")
        print(f"  Attempts: {p['attempts']}, Last status: {p['last_status']}, Next review: {p['next_review']}")
    print()


def filter_problems(data, diff_filter=None, topic_filter=None, only_due=False):
    """Return a list of problem_ids that match filters."""
    now = datetime.now()
    result = []
    for pid, p in data["problems"].items():
        if diff_filter and p["difficulty"] != diff_filter:
            continue
        if topic_filter:
            if topic_filter not in [t.lower() for t in p["topics"]]:
                continue
        if only_due:
            nr = p["next_review"]
            if nr is None:
                # If never practiced, it's due
                pass
            else:
                nr_dt = datetime.strptime(nr, DATE_FORMAT)
                if nr_dt > now:
                    continue
        result.append(pid)
    return result


def choose_problem(data):
    if not data["problems"]:
        print("\nYou have no problems saved. Add some first.")
        return None

    print("\n=== Choose Problem to Practice ===")
    use_filters = input("Apply filters? (y/n): ").strip().lower() == "y"

    diff_filter = None
    topic_filter = None
    only_due = False

    if use_filters:
        diff_input = input("Filter by difficulty (easy/medium/hard or empty for any): ").strip()
        if diff_input:
            diff_filter = normalize_difficulty(diff_input)
        topic_input = input("Filter by topic (exact match, e.g. array) or empty for any: ").strip().lower()
        if topic_input:
            topic_filter = topic_input
        only_due = input("Only show due for review? (y/n): ").strip().lower() == "y"

    candidates = filter_problems(data, diff_filter, topic_filter, only_due)

    if not candidates:
        print("No problems match these filters.")
        return None

    pid = random.choice(candidates)
    p = data["problems"][pid]
    print("\n=== Practice This Problem ===")
    print(f"ID: {pid}")
    print(f"Title: {p['title']}")
    print(f"Difficulty: {p['difficulty']}")
    print(f"Topics: {', '.join(p['topics']) or 'none'}")
    print(f"URL: {p['url']}")
    print("Open the URL, start solving, then come back to log the result.")
    return pid


def schedule_next_review(status, difficulty):
    """
    Very simple spaced repetition:
    - If solved:
        easy: 3 days
        medium: 2 days
        hard: 1 day
    - If partial/unsolved: tomorrow
    """
    now = datetime.now()
    status = (status or "").lower()
    if status == "solved":
        if difficulty == "easy":
            delta = timedelta(days=3)
        elif difficulty == "medium":
            delta = timedelta(days=2)
        else:  # hard
            delta = timedelta(days=1)
    else:
        delta = timedelta(days=1)
    return (now + delta).strftime(DATE_FORMAT)


def start_practice_session(data):
    pid = choose_problem(data)
    if pid is None:
        return

    start_time = datetime.now()
    print(f"\nSession started at {start_time.strftime(DATE_FORMAT)}")
    input("Press Enter when you finish solving (or stop) to log the result...")

    end_time = datetime.now()
    minutes = (end_time - start_time).total_seconds() / 60
    print(f"\nSession duration: {minutes:.1f} minutes")

    while True:
        status = input("Result (solved/partial/unsolved): ").strip().lower()
        if status in ["solved", "partial", "unsolved"]:
            break
        print("Please enter: solved / partial / unsolved")

    notes = input("Any notes (approach, mistakes, patterns)? (optional): ").strip()

    problem = data["problems"][pid]
    problem["attempts"] += 1
    problem["last_status"] = status
    problem["last_practiced"] = end_time.strftime(DATE_FORMAT)
    problem["next_review"] = schedule_next_review(status, problem["difficulty"])

    session_record = {
        "problem_id": pid,
        "start": start_time.strftime(DATE_FORMAT),
        "end": end_time.strftime(DATE_FORMAT),
        "minutes": round(minutes, 1),
        "status": status,
        "notes": notes,
    }
    data["sessions"].append(session_record)

    save_data(data)

    print("\n=== Session Logged ===")
    print(f"Problem: {problem['title']} ({pid})")
    print(f"Status: {status}")
    print(f"Time: {minutes:.1f} minutes")
    print(f"Next review scheduled: {problem['next_review']}")


def stats_overview(data):
    problems = data["problems"]
    sessions = data["sessions"]

    print("\n=== Stats Overview ===")
    print(f"Total problems saved: {len(problems)}")
    print(f"Total sessions: {len(sessions)}")

    by_difficulty = {"easy": 0, "medium": 0, "hard": 0}
    solved_count = 0

    for p in problems.values():
        d = p["difficulty"]
        if d in by_difficulty:
            by_difficulty[d] += 1
        if p["last_status"] == "solved":
            solved_count += 1

    print("Problems by difficulty:")
    for d in ["easy", "medium", "hard"]:
        print(f"  {d}: {by_difficulty[d]}")

    print(f"Solved at least once: {solved_count}")

    # Last 5 sessions
    print("\nLast 5 sessions:")
    for s in sessions[-5:]:
        print(
            f"- {s['start']} | {s['problem_id']} | {s['status']} | {s['minutes']} min"
        )
    print()


def main_menu():
    data = load_data()

    while True:
        print("\n========== LeetCode Practice Assistant ==========")
        print("1) Add / update problem")
        print("2) List problems")
        print("3) Start practice session")
        print("4) View stats")
        print("5) Exit")
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            add_problem(data)
        elif choice == "2":
            list_problems(data)
        elif choice == "3":
            start_practice_session(data)
        elif choice == "4":
            stats_overview(data)
        elif choice == "5":
            print("Goodbye. Keep grinding 💪")
            break
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main_menu()

def anxiety_planner():
    return {
        "morning": [
            "5 min deep breathing",
            "Write top 3 tasks for the day",
            "Avoid phone for first 30 minutes",
        ],
        "afternoon": [
            "Work in 25 min Pomodoro cycles",
            "Take 5 min breaks",
            "Avoid multitasking",
        ],
        "evening": [
            "Go for a light walk",
            "Reflect on completed tasks",
            "Avoid overthinking triggers",
        ],
    }


def depression_planner():
    return {
        "morning": [
            "Wake up and get sunlight",
            "Do 1 small easy task",
            "Take a shower and get ready",
        ],
        "afternoon": [
            "Work on 1 important task (low pressure)",
            "Take breaks without guilt",
            "Eat properly",
        ],
        "evening": [
            "Talk to someone",
            "Write 1 positive thing",
            "Sleep on time",
        ],
    }


def procrastination_planner():
    return {
        "morning": [
            "Start with hardest task (5-minute rule)",
            "No phone until first task is done",
            "Set a clear goal",
        ],
        "afternoon": [
            "Use Pomodoro technique (25/5)",
            "Block distractions",
            "Track progress",
        ],
        "evening": [
            "Review work done",
            "Plan next day",
            "Reward yourself",
        ],
    }


def generate_planner(dep_score, anx_score, root_probs):
    # Top root cause
    top_root = max(root_probs, key=root_probs.get)

    if anx_score > 0.5:
        return "Anxiety", anxiety_planner()

    elif dep_score > 0.5:
        return "Depression", depression_planner()

    else:
        return "Procrastination", procrastination_planner()

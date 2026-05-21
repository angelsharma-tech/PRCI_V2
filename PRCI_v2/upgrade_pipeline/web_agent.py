def get_suggestions(root_cause):
    suggestions_map = {
        "perfectionism": [
            "Start with an imperfect version of the task",
            "Set strict time limits instead of perfect goals",
            "Focus on progress, not perfection",
        ],
        "fear_of_failure": [
            "Break tasks into smaller achievable steps",
            "Focus on learning rather than outcome",
            "Remind yourself that mistakes are normal",
        ],
        "dopamine_addiction": [
            "Reduce phone usage during work hours",
            "Use Pomodoro technique (25 min focus)",
            "Keep distractions out of reach",
        ],
        "environment_distraction": [
            "Clean and organize your workspace",
            "Use website blockers",
            "Work in a quiet environment",
        ],
        "lack_of_interest": [
            "Connect the task to your long-term goals",
            "Reward yourself after completing work",
            "Try starting with just 5 minutes",
        ],
    }

    return suggestions_map.get(root_cause, ["No suggestions available"])

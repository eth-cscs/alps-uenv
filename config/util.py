def colorize(string, color):
    colors = {
        "red":     "31",
        "green":   "32",
        "yellow":  "33",
        "blue":    "34",
        "magenta": "35",
        "cyan":    "36",
        "white":   "37",
    }
    return f"\033[1;{colors[color]}m{string}\033[0m"

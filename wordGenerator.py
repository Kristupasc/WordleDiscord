import random

def generate_word():
    with open("words.txt", "r") as file:
        lines = file.readlines()

    # Pick a random line
    return random.choice(lines).strip().lower()

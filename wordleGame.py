import discord
from datetime import datetime
import wordGenerator


async def play(ctx, index, guess, db):
    now = datetime.now()
    user_data = db.get(index)
    answer = user_data[2]
    board_list = user_data[3]
    blacklisted_letters = user_data[10]
    tried_words = user_data[11]

    # Store the squares in a list (["green", "black", ...]),
    # then convert them to emojis at the end.
    squares = [None] * 5

    # First, mark greens
    answer_remaining = list(answer)  # mutable copy of the answer
    guess_letters = list(guess)

    # Mark green
    green_count = 0
    for i in range(5):
        if guess_letters[i] == answer_remaining[i]:
            squares[i] = "green"
            answer_remaining[i] = None  # remove this letter
            guess_letters[i] = None     # so we don't try to match it again
            green_count += 1

    # Second, mark yellows for anything not green
    for i in range(5):
        if squares[i] is None:  # not green yet
            letter = guess_letters[i]
            if letter and letter in answer_remaining:
                # Mark yellow, remove one occurrence from the answer
                squares[i] = "yellow"
                answer_remaining[answer_remaining.index(letter)] = None
            else:
                # Not in the answer at all (or used up)
                squares[i] = "black"
                # We'll blacklist this letter (if it's not already flagged as yellow or green)
                if letter and letter not in blacklisted_letters:
                    blacklisted_letters.append(letter)

    # Build the line of emojis
    emoji_map = {"green": ":green_square:", "yellow": ":yellow_square:", "black": ":black_large_square:"}
    answer_line = " ".join(emoji_map[color] for color in squares) + "\n"

    # Record the guess
    tried_words.append(guess)
    board_list.append(answer_line)

    # Update DB
    user_data[3] = board_list
    user_data[10] = blacklisted_letters
    user_data[11] = tried_words
    db.set(index, user_data)

    # Show the board to the user
    board_output = "".join(board_list)
    await ctx.edit(content=board_output)

    # Check if user has won or used up tries
    if green_count == 5 or len(board_list) >= 6:
        # The game is over
        user_data[5] += 1  # total_plays += 1

        if green_count == 5:
            # They guessed the word
            # If it's a new day or hasn't played before, extend the streak
            if user_data[1] == now.day - 1 or user_data[1] == -1 or now.day == 1:
                user_data[6] += 1  # current_streak += 1
                if user_data[6] > user_data[7]:
                    user_data[7] = user_data[6]  # max_streak = current_streak
            user_data[8] += 1  # times_won += 1
            await ctx.respond(f"You guessed the word!\n(It was `{answer}`)\nType `/stats` to see your stats.")
        else:
            # They ran out of tries
            user_data[6] = 0     # reset current streak
            user_data[9] += 1    # times_lost += 1
            await ctx.respond(f"You ran out of tries :(\nThe word was: `{answer}`\nType `/stats` to see your stats.")

        # Reset things for the next day
        from wordGenerator import generate_word
        user_data[1] = now.day                   # last_play_day
        user_data[2] = generate_word().strip()   # new daily word
        user_data[4] = True                      # is_finished_today
        # If you prefer to empty the board for the next day:
        user_data[3] = board_list  # or []
        user_data[10] = []
        user_data[11] = []
        db.set(index, user_data)

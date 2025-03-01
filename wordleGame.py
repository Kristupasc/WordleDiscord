import discord
from datetime import datetime
import wordGenerator


async def play(ctx, index, command, db):
    now = datetime.now()
    user_data = db.get(index)
    word = user_data[2]           # the correct word for this user
    board_list = user_data[3]
    blacklisted_letters = user_data[10]
    tried_words = user_data[11]

    green_counter = 0
    answer_line = ""

    # Keep track of letters we flagged as "yellow" to avoid blacklisting them
    found_yellow = []

    if len(command) == 5:
        # Make a copy of the correct word so we can mark used letters as we go
        copy_of_correct = list(word)

        for i in range(5):
            guess_letter = command[i]
            if guess_letter == copy_of_correct[i]:
                # This letter is correct and in the correct position
                answer_line += ":green_square: "
                copy_of_correct[i] = "0"  # Mark as used
                green_counter += 1
            else:
                # Check if guess_letter is anywhere else in copy_of_correct
                found_spot = False
                for j in range(5):
                    if guess_letter == copy_of_correct[j]:
                        # If we haven't used that letter or matched it yet
                        copy_of_correct[j] = "0"
                        answer_line += ":yellow_square: "
                        found_yellow.append(guess_letter)
                        found_spot = True
                        break
                if not found_spot:
                    # It's not in the word at all
                    if guess_letter not in blacklisted_letters and guess_letter not in found_yellow:
                        blacklisted_letters.append(guess_letter)
                    answer_line += ":black_large_square: "

    # The user tried this word
    tried_words.append(command)
    answer_line += "\n"

    # Append this row of squares to their board
    board_list.append(answer_line)

    # Update the database for this user
    user_data[3] = board_list
    user_data[10] = blacklisted_letters
    user_data[11] = tried_words
    db.set(index, user_data)

    # Re-create the board for display
    board_output = "".join(board_list)
    await ctx.edit(content=board_output)

    # Check if they won or used up their tries
    if green_counter == 5 or len(board_list) >= 6:
        # The game is over
        user_data[5] += 1  # total_plays += 1

        if green_counter == 5:
            # They guessed the word
            # If it's a new day or hasn't played before, extend the streak
            if user_data[1] == now.day - 1 or user_data[1] == -1 or now.day == 1:
                user_data[6] += 1  # current_streak += 1
                if user_data[6] > user_data[7]:
                    user_data[7] = user_data[6]  # max_streak = current_streak
            user_data[8] += 1  # times_won += 1
            await ctx.respond(f"You guessed the word!\n(It was `{word}`)\nType `/stats` to see your stats.")
        else:
            # They ran out of tries
            user_data[6] = 0     # reset current streak
            user_data[9] += 1    # times_lost += 1
            await ctx.respond(f"You ran out of tries :(\nThe word was: `{word}`\nType `/stats` to see your stats.")

        # Set them as finished for this day and pick a new word for the next day
        user_data[1] = now.day
        user_data[2] = wordGenerator.generate_word().lower().strip()
        user_data[4] = True
        # Clear out board, blacklisted letters, tried words for the next day
        user_data[3] = board_list  # or []
        user_data[10] = []
        user_data[11] = []

        db.set(index, user_data)

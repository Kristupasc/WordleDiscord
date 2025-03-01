import discord
from discord import Option
from discord import commands
import os
from datetime import datetime
from dotenv import load_dotenv
import pickledb
import wordleGame
import wordGenerator

#
# If you still want to read your token from an environment variable,
# you can do so here. If you prefer to hardcode your token, just
# replace `os.getenv("DISCORD_TOKEN")` with a string: "YOUR_BOT_TOKEN"
#
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")  # or "YOUR_BOT_TOKEN"

client = discord.Bot()
servers = [846826501865603092, 515932305689411594]

# Load pickledb with auto_dump=True so all changes are saved automatically
db = pickledb.load("wordle.db", auto_dump=True)

# Read in the five-letter word list
lines = open("5letterWords.txt", "r").readlines()
stripedLines = [line.strip() for line in lines]

# Utility function to get the 'key' of this user in our pickledb
def get_spot(user_id):
    # The DB keys in this structure are strings "0", "1", "2", ...
    # Each points to a tuple containing the user data.
    for key in db.getall():
        entry = db.get(key)
        if entry and len(entry) >= 1 and entry[0] == user_id:
            return key
    return None


def check_if_first_time(user_id):
    """
    Checks if user_id is in the DB. If not, create a fresh record for them.
    Return True if we created a new record, else False.
    """
    now = datetime.now()
    for key in db.getall():
        entry = db.get(key)
        if entry and entry[0] == user_id:
            return False  # user already in the database

    # Not found -> create a new DB entry for this user:
    # Structure of each entry in db:
    #    ( user_id, last_play_day, current_word, board_list, is_finished_today,
    #      total_plays, current_streak, max_streak, times_won, times_lost,
    #      blacklisted_letters, tried_words )
    db.set(
        str(len(db.getall())),
        [
            user_id,                             # user_id
            -1,                                  # last_play_day
            wordGenerator.generate_word().lower().strip(),  # new random word
            [],                                  # board_list
            False,                               # is_finished_today
            0,                                   # total_plays
            0,                                   # current_streak
            0,                                   # max_streak
            0,                                   # times_won
            0,                                   # times_lost
            [],                                  # blacklisted_letters
            [],                                  # tried_words
        ],
    )
    return True


@client.event
async def on_ready():
    print(f"Bot is logged in as {client.user}")


@client.slash_command(guild_ids=servers, description="Play Wordle!")
async def wordle(ctx: discord.ApplicationContext, word: Option(str, "5-letter word")):
    await ctx.respond("Thinking...")

    now = datetime.now()
    # Ensure user record is in DB
    check_if_first_time(ctx.author.id)
    index = get_spot(ctx.author.id)
    user_data = db.get(index)

    if len(word) != 5:
        await ctx.edit(content="Your word needs to be 5 letters long!")
        return

    # user_data => [user_id, last_play_day, current_word, board_list, is_finished_today, ...]
    last_play_day = user_data[1]
    board_list = user_data[3]
    is_finished_today = user_data[4]

    # If user is done for the day:
    if (is_finished_today and last_play_day == now.day) or (len(board_list) >= 6 and last_play_day == now.day):
        await ctx.edit(
            content=(
                "You have already played today. Type `/stats` to view your board.\n"
                "The game resets at 00:00 CEST."
            )
        )
    else:
        # Ensure the guessed word is in the valid word list
        if word.lower().strip() in stripedLines:
            # If user has used up tries or finished before, but a new day started
            if (len(board_list) >= 6 or is_finished_today) and last_play_day != now.day:
                user_data[3] = []  # reset board for the new day
                user_data[4] = False  # user hasn't finished *today*
                db.set(index, user_data)  # commit changes

            # Hand off to the wordleGame logic, passing the DB instance too
            await wordleGame.play(ctx, index, word.lower(), db)
        else:
            await ctx.edit(content="Your word is not in the approved word list.")


@client.slash_command(guild_ids=servers, description="Shows your stats.")
async def stats(ctx: discord.ApplicationContext):
    await ctx.respond("Thinking...")
    check_if_first_time(ctx.author.id)
    index = get_spot(ctx.author.id)
    user_data = db.get(index)

    total_plays = user_data[5]
    current_streak = user_data[6]
    max_streak = user_data[7]
    times_won = user_data[8]
    times_lost = user_data[9]
    board_list = user_data[3]

    embed = discord.Embed(title="Stats", color=discord.Color.green())
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
    embed.add_field(name="Total times played: ", value=str(total_plays), inline=True)
    embed.add_field(name="Current streak: ", value=str(current_streak), inline=True)
    embed.add_field(name="Maximum streak: ", value=str(max_streak), inline=True)
    embed.add_field(name="Times won: ", value=str(times_won), inline=True)
    embed.add_field(name="Times lost: ", value=str(times_lost), inline=True)

    if board_list:
        board = "".join(board_list)
        embed.add_field(name="Your latest board:", value=board, inline=False)

    await ctx.edit(content=" ", embed=embed)


@client.slash_command(guild_ids=servers, description="Shows the letters/words you used.")
async def info(ctx: discord.ApplicationContext):
    await ctx.respond("Thinking...")
    now = datetime.now()
    check_if_first_time(ctx.author.id)
    index = get_spot(ctx.author.id)
    user_data = db.get(index)

    last_play_day = user_data[1]
    is_finished_today = user_data[4]
    board_list = user_data[3]
    blacklisted_letters = user_data[10]
    tried_words = user_data[11]

    # If user is already finished today or used up tries
    if (is_finished_today and last_play_day == now.day) or (len(board_list) >= 6 and last_play_day == now.day):
        await ctx.edit(
            content=(
                "You have already played today. Type `/stats` to view your board.\n"
                "The game resets at 00:00 CEST"
            )
        )
    else:
        # Show the letters not blacklisted
        abc = "abcdefghijklmnopqrstuvwxyz"
        usable_letters = [ch for ch in abc if ch not in blacklisted_letters]

        if not usable_letters:
            await ctx.edit(content="You need to start a Wordle game in order to see your letter list!")
            return

        letters_str = "``" + "``, ``".join(usable_letters) + "``"
        tried_words_str = "``" + "``, ``".join(tried_words) + "``"

        await ctx.edit(
            content=(
                f"The letters that can still be in the word:\n{letters_str}\n\n"
                f"The words that you have tried (in order):\n{tried_words_str}"
            )
        )


@client.slash_command(guild_ids=servers, description="Shows a help menu.")
async def help(ctx: discord.ApplicationContext):
    await ctx.respond("Thinking...")
    embed = discord.Embed(title="Help menu", color=discord.Color.red())
    embed.add_field(
        name="Game description",
        value=(
            "In Wordle, you have to guess a randomly selected five-letter word in six tries. "
            "After you input a word, each letter's outcome can be:\n"
            ":green_square: – correct letter, correct position\n"
            ":yellow_square: – correct letter, wrong position\n"
            ":black_large_square: – letter not in the selected word\n"
            "**Note:** you can only play this game once per day!"
        ),
        inline=False
    )
    embed.add_field(
        name="Commands",
        value=(
            "`/wordle <5-letter word>` starts/continues a game.\n"
            "`/stats` shows your current stats like streaks, win/loss, and today's board.\n"
            "`/info` shows the letters you've used that turned out to be wrong, and the words you tried.\n"
            "This can only be run if you are in a game."
        ),
        inline=False
    )

    await ctx.edit(content="", embed=embed)


# Finally, run the bot
client.run(TOKEN if TOKEN else "YOUR_BOT_TOKEN")

import discord
from discord import Option
from discord import commands
import os
# every user has a database spot with an str(index)
from replit import db
from datetime import datetime
#from keep_alive import keep_alive
import wordleGame, wordGenerator

client = discord.Bot()

abc = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j','k', 'l', 'm', 'n', 'o','p', 'q', 'r', 's', 't','u', 'v', 'w', 'x', 'y','z']

servers = [846826501865603092, 515932305689411594]

lines = open("5letterWords.txt", 'r').readlines()
stripedLines = []
print("generating word list...")
for i in lines:
  stripedLines.append(i.strip())

#PROBABLY FIXED: for a word 'catch' the last c is black square, so it automatically adds it to unusable letter list, but the first c can be yellow

def get_spot(id):
  for i in range(len(db.keys())):
    try:
      if id == db[str(i)][0]:
        return str(i)
    except KeyError:
      continue
  return None

def checkIfFirstTime(id):
  now = datetime.now()
  for i in range(len(db.keys())):
    if db[str(i)][0] == id:
       # The user is already in the database
      return False
  # create a new database for the user
  db[str(len(db.keys()))] = int(id), -1, wordGenerator.generate_word().lower().strip(), [], False, 0, 0, 0, 0, 0, [], []
  print(len(db.keys()))
  print("keys:")
  print(db.keys())
  print("Created a new database entry! " + str(db['0']))
  return True

@client.event
async def on_ready():
  print("Bot is logged in as {0.user}".format(client))

@client.slash_command(guild_ids = servers, description="Plays Wordle!")
async def wordle(
    ctx: discord.ApplicationContext,
    word: Option(str, "5-letter word")
):
  await ctx.respond("pala biski...")
  now = datetime.now()
  checkIfFirstTime(ctx.author.id)
  index = get_spot(ctx.author.id)
  if len(word) != 5:
    await ctx.edit(content=("Your word needs to be 5 letters long!"))
  else:
    if (db[index][4] == True and db[index][1] == now.day) or (len(db[index][3]) >= 6 and db[index][1] == now.day):
      await ctx.edit(content=("You have already played today. Type ``/stats`` to view your board.\nThe game resets at 00:00 CEST"))
    else:
      if word.strip().lower() in stripedLines:
        if (len(db[index][3]) >= 6 or db[index][4] == True) and db[index][1] != now.day:
          # reset a new wordle for the day
          db[index][3] = []
        db[index][4] = False
        # play wordle
        await wordleGame.play(ctx, index, word.lower())
      else:
        await ctx.edit(content=("Your word is not in the approved word list."))

@client.slash_command(guild_ids = servers, description="Shows your stats.")
async def stats(
  ctx: discord.ApplicationContext,
):
  await ctx.respond("pala biski...")
  checkIfFirstTime(ctx.author.id)
  index = get_spot(ctx.author.id)
  embed=discord.Embed(title="Stats", color=discord.Color.green())
  #embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
  embed.add_field(name="Total times played: ", value=str(db[index][5]), inline = True)
  embed.add_field(name="Current streak: ", value=str(db[index][6]), inline = True)
  embed.add_field(name="Maximum streak: ", value=str(db[index][7]), inline = True)
  embed.add_field(name="Times won: ", value=str(db[index][8]), inline = True)
  embed.add_field(name="Times lost: ", value=str(db[index][9]), inline = True)
  board = ""
  if len(db[index][3]) >= 1:
    for i in range(len(db[index][3])):
      board += db[index][3][i]
    embed.add_field(name="Your latest board:", value=board, inline = False)
  await ctx.edit(content=" ", embed=embed)
  
@client.slash_command(guild_ids = servers, description="Shows the letters and words you used.")
async def info(
  ctx: discord.ApplicationContext,
):
  await ctx.respond("pala biski...")
  now = datetime.now()
  checkIfFirstTime(ctx.author.id)
  index = get_spot(ctx.author.id)
  if (db[index][4] == True and db[index][1] == now.day) or (len(db[index][3]) >= 6 and db[index][1] == now.day):
    await ctx.edit(content=("You have already played today. Type ``/stats`` to view your board.\nThe game resets at 00:00 CEST"))
  else:
    message = '``'
    for i in range(len(abc)):
      if abc[i] not in db[index][10]:
        message += abc[i]
        if i != len(abc) -1:
          message += "``, ``"
      if i == len(abc) -1:
        message += "``"
    if message == "":
      await ctx.edit(content=("You need to start a Wordle game in order to see your letter list!"))
    else:
      word_list = "``"
      for i in range(len(db[index][11])):
        word_list += db[index][11][i]
        if i != len(db[index][11]) -1:
          word_list += "``, ``"
        else:
          word_list += "``"
      await ctx.edit(content=("The letters that can be in the word: \n" + message + "\nThe words that you have tried (in order):\n" + word_list))

@client.slash_command(guild_ids = servers, description="Shows a help menu.")
async def help(
  ctx: discord.ApplicationContext,
):
  await ctx.respond("pala biski...")
  embed=discord.Embed(title="Help menu", color=discord.Color.red())
  embed.add_field(name="Game description", value = "In Wordle, you have to guess a randomly selected five-letter word in six tries. After you input a word, in every letter, you get three different outcome.\n:green_square: means that the letter in that spot matches the letter in the selected word.\n:yellow_square: means that the letter is in the selected word, but in the wrong location.\n:black_large_square: means that the corresponding letter is not in the selected word.\n**Note:** you can only play this game once per day!", inline = False)
  embed.add_field(name="Commands", value="``/wordle <5-letter word>`` starts/continues a game.\n``/stats`` shows your current stats like streaks, win/loss count, games played and today's board.\n``/info`` shows the words that you used and the letters that you used which turned out to be :black_large_square. This command can only be run if you are in game.", inline = False)

  await ctx.edit(embed=embed)

#keep_alive()
client.run(os.getenv('TOKEN'))
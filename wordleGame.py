import discord
from discord import Option
from replit import db
from datetime import datetime
import wordGenerator

empty_wordle = ":black_large_square: :black_large_square: :black_large_square: :black_large_square: :black_large_square:"

test_wordle = empty_wordle + "\n:green_square: :black_large_square: :yellow_square: :black_large_square: :black_large_square:\n:green_square: :yellow_square: :yellow_square: :black_large_square: :black_large_square:\n:green_square: :yellow_square: :yellow_square: :black_large_square: :green_square:\n:green_square: :green_square: :green_square: :green_square: :green_square:\n"

async def play(ctx, index, command):
  yellow = []
  now = datetime.now()
  green_counter = 0
  didFind = False
  word = db[index][2]
  our_word = command
  answer = ""
  if len(our_word) == 5:
    copy = list(word)
    for i in range(len(our_word)):
      if our_word[i] == copy[i]:
          answer += ":green_square: "
          copy[i] = '0'
          green_counter += 1
          didFind = True
      else:
          for j in range(len(copy)):
              if our_word[i] == copy[j]:
                  if our_word[j] == copy[j]:
                    if (our_word[i] not in db[index][10]) and (our_word[i] not in yellow):
                      db[index][10].append(our_word[i])
                    answer += ":black_large_square: "
                  else:
                    copy[j] = '0'
                    yellow.append(our_word[j])
                    answer += ":yellow_square: "
                  didFind = True
                  break
      if not didFind:
        if (our_word[i] not in db[index][10]) and (our_word[i] not in yellow):
          db[index][10].append(our_word[i])
        answer += ":black_large_square: "
      didFind = False
  db[index][11].append(our_word)
  answer += "\n"
  # update the database and send the result.
  if db[index][3] == []:
    db[index][3] = [answer]
  else:
    db[index][3].append(answer)
  board = ""
  for i in range(len(db[index][3])):
    board += db[index][3][i]
  await ctx.edit(content=board)
  if green_counter == 5 or len(db[index][3]) >= 6:
    # The game is over
    # alter the database to forbid the player from playing today and add some statistics
    db[index][5] += 1
    if green_counter == 5:
      if db[index][1] == now.day -1 or now.day == 1 or db[index][1] == -1:
        db[index][6] += 1
        # If the current streak is the highest
        if db[index][6] > db[index][7]:
          db[index][7] = db[index][6]
      db[index][8] += 1
      await ctx.respond("You guessed the word!\n(It was ``" + db[index][2] + "``)\nType ``/stats`` to see your stats.")
    else:
      db[index][6] = 0
      db[index][9] += 1
      await ctx.respond("You ran out of tries :(\nThe word was: ``" + db[index][2] + "``\nType ``/stats`` to see your stats.")
    db[index] = db[index][0], now.day, wordGenerator.generate_word().lower().strip(), db[index][3], True, db[index][5], db[index][6], db[index][7], db[index][8], db[index][9], [], []


          
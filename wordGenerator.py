import random


def generate_word():
  file = open('words.txt', 'r')
  lines = file.readlines()
  num = random.randint(0, len(lines)-1)
  return lines[num]

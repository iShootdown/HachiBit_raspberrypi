from sense_hat import SenseHat
from adafruit_crickit import crickit
from PIL import Image
import numpy as np
from pygame import mixer

import time
import random
import pathlib
from math import floor

#initialisation of sensehat
sense = SenseHat()
sense.low_light = False

ss = crickit.seesaw
# potentiometer connected to signal #8
irsensor = crickit.SIGNAL8

# initalise capicitive touch ports
c1 = crickit.touch_1
c2 = crickit.touch_2
c3 = crickit.touch_3
c4 = crickit.touch_4

#init cricket drivers for servo
servo = crickit.servo_4
servo.actuation_range = 180
servo.set_pulse_width_range(600,2450)
servo.throttle = 100
servo.angle = 180
# min 0 deg, max 171 deg
buzzer = crickit.drive_1
buzzer.fraction = 0.01
time.sleep(0.5)
buzzer.fraction = 0.0

# initialise music player
mixer.init()
mixer.music.set_volume(0.5)

#colours
green = [0, 255, 0]
yellow = [255, 255, 0]
blue = [0, 0, 255]
red = [255, 0, 0]
white = [255,255,255]
nothing = [0,0,0]
pink = [255,105, 180]
gold = [255, 215, 0]
orange = [255,165,0]
purple = [255,0,255]

#misc lists
colours = [green, yellow, red, pink, orange, purple]
secretkey = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right']

#mode settings
easy_mode = {
  'pic': 'levels/easy.png',
  'car': {'rounds': 50, 'movement': 1, 'spacing': 12}, #pixels (1 per second)
  'snake': {'rounds': 5, 'movement': 2}, #no. of fruits
  'bounce': {'rounds': 100, 'movement': 2, 'bouncesize': 4, 'chance': 10}, #waves
  'maze': {'rounds': 2, 'time': None},
  'shooter': {'rounds': 5, 'time': 2.0, 'lives':3},
  'reaction': {'rounds': 4, 'time': 3.0}
}

normal_mode = {
  'pic': 'levels/normal.png',
  'car': {'rounds': 100, 'movement': 4, 'spacing': 10}, #pixels (1 per second)
  'snake': {'rounds': 10, 'movement': 5}, #no. of fruit
  'bounce': {'rounds': 200, 'movement': 10, 'bouncesize': 3, 'chance': 30}, #waves
  'maze': {'rounds': 3, 'time': 60},
  'shooter': {'rounds': 5, 'time': 1.5, 'lives':3},
  'reaction': {'rounds': 8, 'time': 1.0}
}

hell_mode = {
  'pic': 'levels/hell.png',
  'car': {'rounds': 300, 'movement': 10, 'spacing': 8}, #pixels (1 per second)
  'snake': {'rounds': 10, 'movement': 10}, #no. of fruits before last one
  'bounce': {'rounds': 200, 'movement': 20, 'bouncesize': 3, 'chance': 80}, #waves
  'maze': {'rounds': 10, 'time': 30},
  'shooter': {'rounds': 10, 'time': 0.8, 'lives':1},
  'reaction': {'rounds': 16, 'time': 0.5}
}

#misc functions
def clamp(value, min_value=0, max_value=7):
    return min(max_value, max(min_value, value))

def blink_screen(screen,times):
  for _ in range(times):
    sense.set_pixels(screen)
    time.sleep(1)
    sense.clear()
    time.sleep(1)

def index_to_coords(index):
  x = index%8
  y = floor(index/8)
  return [x,y]

def generate_block(start,size):
  pixs = []
  randcol = random.choice(size['column'])
  randrow = random.choice(size['row'])
  for col in range(randcol):
    for row in range(randrow):
      pixs.append(start+row+col*8)
  return pixs

def shift_screen(screen,shift):
  screendict = {i+shift:screen[i] for i in range(len(screen)) if i != nothing}
  screen = [screendict[i] if i in screendict.keys() else screen[i] for i in range(len(screen))]
  return screen

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def numbersign(number):
  if number >= 0:
    return 1
  else:
    return -1

def filepather(filename):
  return f'{pathlib.Path(__file__).parent}/assets/{filename}'

def findcoords(screen,value):
  return screen.index(list(value))

def returncoords(screen,value):
  return [i for i in range(len(screen)) if screen[i] == value]

def screenreplace(screen,value,coords):
  screencoord = coords[0]*8 + coords[1]
  screen[screencoord] = value
  return screen

def presstime(presstime,exptime):
  if exptime == None or presstime == None:
    return False
  else:
    if presstime > exptime:
      return True
    else:
      return False

def countdown(): #screen countdown

  sense.show_letter('3')
  time.sleep(1)
  sense.show_letter('2')
  time.sleep(1)
  sense.show_letter('1')
  time.sleep(1)
  sense.clear()

def preexitprogram():
  mixer.music.unload()
  mixer.music.stop()
  sense.clear()
  buzzer.fraction = 0.0
  servo.angle = 180

warning = sense.load_image(filepather('warning.png'),redraw=False)

# games as functions

def race(mode):

  speed = mode['car']['movement']
  dist = mode['car']['rounds']
  spacing = mode['car']['spacing']

  mixer.music.load(filepather('sound/dejavu.mp3'))
  sense.clear(nothing)

  X = blue
  O = nothing

  showscreen = [
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, X, X, O, O, O, O,
    O, O, X, X, O, O, O, O,
    O, O, X, X, O, O, O, O
    ]

  sense.set_pixels(showscreen)
  
  cooldown = [-1]*4
  carcolours = colours
  carrows = {u:[] for u in list(range(4))}

  for i in range(dist-8): # remove last 8 rows for gold area
    rows = list(range(4))
    for _ in range(4):
      
      r = random.choice(rows) # RANDOMISE ROW 1-4 PER LOOP
      rows.remove(r)

      if cooldown[r] == 0: # put back colours that are cleared from board
        carcolours.append(carrows[r][i-spacing])

      if len([u for u in cooldown if u > 1]) >= 3: 
        carrows[r] = carrows[r] + [nothing] # put nothing
        continue
      
      if cooldown[r] <= 0 and random.randint(1,100) <= 10+(80/(dist-i)): # randomise chance to spawn car
            
          if carcolours != []: # check if there's a colour available to spawn
            cooldown[r] = spacing
            chosencol = random.choice(carcolours)
            carcolours.remove(chosencol)
            carrows[r] = carrows[r] + [chosencol]
          else:
            carrows[r] = carrows[r] + [nothing]
      else:
        carrows[r] = carrows[r] + [nothing]
  
    cooldown = [i-1 for i in cooldown]

  counterdown = 0 # generate 3x1 car
  selectcol = None
  for rower in list(carrows.keys()):
    carrows[rower] = [nothing]*6 + carrows[rower] + [nothing]*8 # init row
    for indexer in range(len(carrows[rower])):
      
      if counterdown <= 0: # once done with car spawn
        colour = carrows[rower][indexer]
        if colour != nothing:
          counterdown = 2
          selectcol = colour # set to colour for next 2 pixels
      elif selectcol != None: # if still spawning car
        carrows[rower][indexer] = selectcol
        counterdown -= 1

      if counterdown == 0: # once done spawn, reset
        selectcol = None

    carrows[rower] = carrows[rower] + [gold]*8 # add last rows as gold

  # Player inputs, show screens
  player = 1
  mixer.music.play(loops=-1)
  for _ in range(len(carrows[1])-7):

    makescreen = []
    for rower in list(carrows.keys()):
      selectpix = carrows[rower][i:i+8]
      selectpix.reverse()
      makescreen = makescreen + [selectpix]*2 
    
    screen = [[makescreen[y][u] for y in range(8)] for u in range(8)] # rotate screen
    screen = [j for i in screen for j in i] # extract RGB values from rows

    if c1.value:
      player = 0
    elif c2.value:
      player = 1
    elif c3.value:
      player = 2
    elif c4.value:
      player = 3

    playerpix = [40+(player*2), 41+(player*2), 48+(player*2), 49+(player*2), 56+(player*2), 57+(player*2)]
    collision = [i for i in playerpix if screen[i] != nothing and screen[i] != gold]

    if len(collision) > 0:
      sense.set_pixels(screen)
      return 'gameover'

    screen = [blue if c in playerpix else screen[c] for c in range(64)]

    time.sleep(1/speed)
    sense.set_pixels(screen)

  return 'win'

def snake(mode):

  speed = 1/mode['snake']['movement']
  rounds = mode['snake']['rounds']

  X = blue
  O = nothing

  showscreen = [
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    X, O, O, O, O, O, O, O,
    X, O, O, O, O, O, O, O,
    X, O, O, O, O, O, O, O
    ]

  snake = [40,48,56]
  x_direction = 0
  y_direction = -1
  showscreen = [showscreen[i] if i not in snake else blue for i in range(len(showscreen))]

  mixer.music.load(filepather('sound/estart.mp3'))
  mixer.music.queue(filepather('sound/eloop.mp3'),loops=-1)
  mixer.music.play()

  for r in range(rounds):

    emptpypix = returncoords(showscreen,nothing)
    fruit = random.choice(emptpypix)
    if r != rounds-1:
      showscreen[fruit] = green
    else:
      showscreen[fruit] = gold

    while True:

      showscreen = [showscreen[i] if i not in snake else nothing for i in range(len(showscreen))]

      accel = sense.get_accelerometer_raw()
      head = snake[0]

      if abs(accel['x']) > abs(accel['y']) and abs(accel['x']) > 0.1:
        if numbersign(accel['x']) != x_direction and y_direction != 0:
          x_direction = numbersign(accel['x'])
          y_direction = 0
      
      elif abs(accel['y']) > abs(accel['x']) and abs(accel['y']) > 0.1:
        if numbersign(accel['y']) != y_direction and x_direction != 0:
          x_direction = 0
          y_direction = numbersign(accel['y'])

      if head%8 == 0 and x_direction == -1:
        head += 7
      elif (head+1)%8 == 0 and x_direction == 1:
        head -= 7
      else:
        head += x_direction
      
      if head in range(0,8) and y_direction == -1:
        head += 56
      elif head in range(56,64) and y_direction == 1:
        head -= 56
      else:
        head += (y_direction*8)

      if fruit == head:
        snake = [head] + snake
      else:
        snake = [head] + snake[:-1]

      showscreen = [showscreen[i] if i not in snake else blue for i in range(len(showscreen))]
      sense.set_pixels(showscreen)

      if fruit == head: # set screen before breaking out of round
        buzzer.fraction = 0.05
        break

      if len(snake) != len(set(snake)): # check dupes
        return 'gameover'

      time.sleep(speed)
      buzzer.fraction = 0.0
  
  return 'win'

def maze(mode):

  rounds = mode['maze']['rounds']
  sleeper = mode['maze']['time']

  sense.clear(nothing)
  mazes = [filepather(f'mazes/maze{i}.png') for i in list(range(1,7))]

  for i in range(rounds):
    buzzer.fraction = 0.0

    choosemaze = random.choice(mazes)
    maze = sense.load_image(choosemaze,redraw=False)
    maze = [i if i != [0,50,255] else [0,0,255] for i in maze] # fix bad blues
    player = findcoords(maze,blue)
    endpoint = findcoords(maze,red)
    barrier = returncoords(maze,white)

    if i == rounds-1:
      maze[endpoint] = gold
    sense.set_pixels(maze)

    if sleeper != None:
      exptime = time.time() + sleeper
    else:
      exptime = None

    nobreak = True
    while nobreak:
      for event in sense.stick.get_events():

        if presstime(event.timestamp, exptime) == True:
          return 'gameover'

        if event.action != 'released':
          if event.direction == 'right':
            if (player+1)%8 != 0:
              templayer = player + 1
          elif event.direction == 'left':
            if player%8 != 0:
              templayer = player - 1
          elif event.direction == 'up':
            if player not in range(0,8):
              templayer = player - 8
          elif event.direction == 'down':
            if player not in range(56,64):
              templayer = player + 8
          else:
            continue
          
          if templayer not in range(0,64) or templayer in barrier:
            continue

          buzzer.fraction = 0.01
          time.sleep(0.05)
          buzzer.fraction = 0.0
          
          maze[player] = nothing
          maze[templayer] = blue
          player = templayer
        
          sense.set_pixels(maze)

          if player == endpoint:
            nobreak = False
            break

    sense.clear()
      
  return 'win'

def shooter(mode):

  rounds = mode['shooter']['rounds']-1
  sleeper = mode['shooter']['time']
  livescount = mode['shooter']['lives']

  lives = [i+56 for i in list(range(livescount))]
  playergun = [32,33,34,40]
  press = []
  cooldown = False

  mixer.music.load(filepather('sound/pewpew.mp3'))

  for r in range(rounds):

    mixer.music.play(loops=-1)

    shot = False

    for p in range(1,4): # starting animation
      gunner = sense.load_image(filepather(f'gunner/{p}.png'),redraw=False)
      if r == rounds-1: # check last round
        gunner = [gold if i == red else i for i in gunner] # set enemy to gold
      
      sense.set_pixels(gunner) # show zoom out
      time.sleep(1)

      gunner = [blue if c in lives else gunner[c] for c in range(len(gunner))]

    for sec in range(1,31): # timer

      servo.angle = 180 - 6*(sec+1)

      if cooldown == False:
        press = []
        chance = round((sec/30)*100,ndigits=1)
        randscreen = random.randint(1,100)
        if chance >= float(randscreen):
          gunner = [green if i == nothing else i for i in gunner] # set background to green
          press = [True]
        else:
          gunner = [nothing if i == green else i for i in gunner] # reset green background
          press = [False]

        randbuzz = random.randint(1,100)
        if chance >= float(randbuzz):
          buzzer.fraction = 0.05
          press = press + [True]
        else:
          buzzer.fraction = 0.0
          press = press + [False]
      else:
        press = [False]*2
        cooldown = False

      sense.set_pixels(gunner)
      
      exptime = time.time() + sleeper
      savetime = time.time()
      nobreak = True
      if all(press):
        mixer.music.pause()

      if press[0] or press[1]:
        cooldown = True
        while nobreak:
          
          for event in sense.stick.get_events():

            if event.timestamp < savetime:
              continue
            
            if event.action != 'released':
              buzzer.fraction = 0
              shot = True
              nobreak = False
              if all(press) and presstime(event.timestamp, exptime) == False:
                gunner = [nothing if i == green or i == red or i == gold else i for i in gunner] # kill red
                break
              else:
                gunner[lives[-1]] = nothing
                lives = lives[:-1]
                gunner = [nothing if gunner[i] == green or i in playergun else gunner[i] for i in range(len(gunner))] # kill player
                break

          if all(press) and presstime(time.time(), exptime):
            gunner[lives[-1]] = nothing
            lives = lives[:-1]
            gunner = [nothing if gunner[i] == green or i in playergun else gunner[i] for i in range(len(gunner))] # kill player
            break
          elif presstime(time.time(), exptime) and nobreak == True:
            break
      
      sense.set_pixels(gunner)
      time.sleep(2)

      if len(lives) == 0:
        return 'gameover'

      if all(press) or shot:
        break

  return 'win'

def ballblaster(mode):

  mode        = mode['bounce'] # initiate dict from mode
  
  rounds      = mode['rounds']
  movement    = mode['movement']
  bouncesize  = mode['bouncesize']
  chance      = mode['chance']

  buzzer.fraction = 0.0

  lower = 200
  upper = 700

  playerzone = [(8*i)-1 for i in range(1,9)] # list of player bounce coords
  possiblepos = 8-bouncesize+1
  irrange = int(round((upper-lower)/possiblepos))
  
  irranges = [lower+irrange*i for i in range(possiblepos)]

  ballpix = 54
  x_direction = -1 # x,y movement
  y_direction = -1
  coords = [6,6]
  colourdict = {} #key=index, value=colour

  screen = [nothing]*64
  prevind = 0

  for _ in range(rounds): # distance mode

    x_directions = 0
    y_directions = 0
 
    # reverse_x = False
    # reverse_y = False
    
    tempcolourlist = [i for i in colours if i not in colourdict.values()]
    if len(tempcolourlist) != 0 and random.randint(0,100) <= chance:
      randscreen = [i for i in range(len(screen)) if screen[i] == nothing and index_to_coords(i)[0] < 6 and index_to_coords(i)[0] not in list(range(coords[0]-1,coords[0]+2)) and index_to_coords(i)[1] not in list(range(coords[1]-1,coords[1]+2))]
      randscreen = random.choice(randscreen)
      randcolour = random.choice(tempcolourlist)
      colourdict[randscreen] = randcolour
      screen[randscreen] = randcolour

    screen = [nothing if i == blue or i == white else i for i in screen]

    irdist = ss.analog_read(irsensor) # 700 = close, 200 = far
    for ind in range(len(irranges)):
      if ind != len(irranges)-1:
        if irdist >= irranges[ind] and irdist <= irranges[ind+1]:
          break

    playerpix = playerzone[ind:ind+bouncesize]
    tempcoords = [coords[0]+x_direction, coords[1]+y_direction]
    
    if tempcoords[0] == 7 and (coords[1] in range(ind,ind+bouncesize) or coords[1] in range(prevind,prevind+bouncesize)): # check if bouncer is to right of ball
      x_directions += 1
      buzzer.fraction = 0.01
    if tempcoords[0] < 0:
      x_directions += 1
      buzzer.fraction = 0.01
    if tempcoords[0] > 7:
      return 'gameover'
    if tempcoords[1] < 0 or tempcoords[1] > 7:
      y_directions += 1
      buzzer.fraction = 0.01

    for indexer in [*colourdict]: # cycles around temporary list of colourdict iteratables so won't be affected by changes to colourdict in loop
      indexcoords = index_to_coords(indexer)
      temptempcoords = tempcoords
      if x_directions == 1:
        temptempcoords[0] = coords[0] - x_direction
      if y_directions == 1:
        temptempcoords[1] = coords[1] - y_direction
      
      if temptempcoords == indexcoords:
        x_directions += 1
        y_directions += 1
      elif indexcoords[0] == coords[0]+x_direction and indexcoords[1] == coords[1] and x_direction != 0:
        x_directions += 1
      elif indexcoords[0] == coords[0] and indexcoords[1] == coords[1]+y_direction and y_direction != 0:
        y_directions += 1
      else:
        continue
      
      screen[indexer] = nothing
      del colourdict[indexer]
      buzzer.fraction = 0.01

    if x_directions != 2:
      if x_directions == 1:
        x_direction = -x_direction
      coords[0] = coords[0]+x_direction
    
    if y_directions != 2:
      if y_directions == 1:
        y_direction = -y_direction
      coords[1] = coords[1]+y_direction
    
    ballpix = coords[0] + coords[1]*8
    screen[ballpix] = white
    screen = [blue if i in playerpix else screen[i] for i in range(len(screen))]
    prevind = ind
    sense.set_pixels(screen)

    time.sleep(1/movement)
    buzzer.fraction = 0.0
  return 'win'

def reaction(mode):

  rounds = mode['reaction']['rounds']
  sleeper = mode['reaction']['time']
  score = {'win':0,'lose':0}

  directions = ['up','down','left','right','middle']

  pointscreen = [nothing]*16

  for r in range(rounds):

    direct = random.choice(directions)

    sense.clear()
    time.sleep(1)
    time.sleep(random.random()*4)
    sense.load_image(filepather(f'directions/{direct}.png'))
    buzzer.fraction = 0.01

    if sleeper != None:
      exptime = time.time() + sleeper
      savetime = time.time()
    else:
      exptime = None
      savetime = None

    nobreak = True
    
    while nobreak:
      for event in sense.stick.get_events():
        
        if presstime(savetime, event.timestamp) == True:
          continue
       
        if presstime(event.timestamp, exptime) == True:
          score['lose'] += 1
          pointscreen[r] = red
          nobreak = False
          break

        if event.action == 'pressed':
          
          if event.direction == direct:
            score['win'] += 1
            pointscreen[r] = green
          else:
            score['lose'] += 1
            pointscreen[r] = red
          
          nobreak = False
          break

      if presstime(time.time(), exptime) and nobreak == True:
        score['lose'] += 1
        pointscreen[r] = red
        nobreak = False
    
    buzzer.fraction = 0.0
    showscreen = np.array(list(chunks([np.uint8(i) for i in pointscreen],4)))
    showscreen = Image.fromarray(showscreen,mode='RGB')
    showscreen = showscreen.resize((8,8),Image.BOX)
    showscreen = [list(r) for i in list(np.asarray(showscreen)) for r in i]
    sense.set_pixels(showscreen)
    time.sleep(4)
    
  if score['win'] > score['lose']:
    return 'win'
  else:
    return 'gameover'

def main():
  mixer.music.load(filepather('sound/startup.mp3'))
  mixer.music.play()
  sense.load_image(filepather('8.png'))
  time.sleep(10)
  mixer.music.stop()
  mixer.music.unload()
    
  # selection program
  lvls = {'easy': easy_mode, 'normal': normal_mode}
  sense.show_message(text_string='Choose Difficulty',scroll_speed=0.04)

  chooselvl = 0
  chosen = True
  newlvler = True
  seecount = 0

  while chosen:
    
    if newlvler == True:
      lvl = list(lvls.keys())[chooselvl]
      #sense.show_message(text_string=lvl.capitalize(),scroll_speed=0.05)
      sense.load_image(filepather(lvls[lvl]['pic']))
      newlvler = False
    
    breakout = True

    while breakout:
      for event in sense.stick.get_events():
        if event.action == 'pressed':
          if event.direction == 'left':
            chooselvl += 1
            newlvler = True 
          elif event.direction == 'right':
            chooselvl -= 1
            newlvler = True
          elif event.direction == 'middle':
            moder = lvls[lvl]
            chosen = False
          
          if event.direction == secretkey[seecount]:
            seecount += 1
          else:
            seecount = 0
          
          breakout = False
          break
    
    if seecount == 8:
      mixer.music.load(filepather('sound/hazard.mp3'))
      mixer.music.play()
      blink_screen(warning,3)
      sense.load_image(filepather(hell_mode['pic']),redraw=True)
      moder = hell_mode
      mixer.music.stop()
      mixer.music.unload()
      break
    
    if chooselvl < 0:
      chooselvl = 1
    elif chooselvl > 1:
      chooselvl = 0

  # randomise games on random mode
  gamelist = [race, snake, maze, shooter, ballblaster, reaction]
  for _ in range(len(gamelist)):
    
    countdown()
    # setup to get result from function
    gamer = random.choice(gamelist)
    gamelist.remove(gamer)
    
    result = gamer(moder)
    preexitprogram()

    if result == 'gameover':
      preexitprogram()
      mixer.music.load(filepather('sound/gameoveryea.mp3'))
      mixer.music.play()
      time.sleep(1)
      sense.load_image(filepather('gameover/1.png'),redraw=True)
      time.sleep(1)
      sense.load_image(filepather('gameover/2.png'),redraw=True)
      time.sleep(1)
      sense.load_image(filepather('gameover/3.png'),redraw=True)
      time.sleep(6)
      main()

    elif result == 'win':
      mixer.music.load(filepather('sound/leveldone.mp3'))
      mixer.music.play()
      sense.load_image(filepather('medal.png'),redraw=True)
      time.sleep(7)

  mixer.music.load(filepather('sound/thankyou.mp3'))
  mixer.music.play()
  sense.load_image(filepather('trophy.png'),redraw=True)
  time.sleep(5)

  preexitprogram()
  main()

# main loop
if __name__ == "__main__":
  main()
import random
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "lib/site-packages"))
from this import d
from flask import Flask, request
from flask_sock import Sock
from flask_cors import CORS
import json

app = Flask(__name__)

sock = Sock(app)

CORS(app)

Games = []

def GetGameById(id):
    for i in range(len(Games)):
        if(Games[i].id == id):
            return Games[i]
    return -1

class Game:
    count = 0
    def __init__(self, x, y, name, difficulty, isBordered):
        Game.count += 1
        self.id = Game.count
        self.sizeX = x
        self.sizeY = y
        self.name = name
        self.difficulty = difficulty
        mat = []
        for i in range(x):
            newArr = []
            for j in range(y):
                newArr.append('Empty')
            mat.append(newArr)
        self.board = mat
        self.board[0][0] = 'Head'
        self.head = [0,0]
        self.tail = self.head[:]
        self.path = [self.head[:]]
        self.direction = 1
        self.queue = []
        self.isOver = False
        if(difficulty == "Easy"):
            self.speed = 500 - ((self.sizeX-10)//(self.sizeX+10))*100
        elif(difficulty == "Medium"):
            self.speed = 300 - ((self.sizeX-10)//(self.sizeX+10))*100
        else:
            self.speed = 100 - ((self.sizeX-10)//(self.sizeX+10))*100
        self.isBordered = isBordered
        self.SpawnFood()
        self.SpawnBlocks()
    def CheckCrash(self):
        if(self.head[0] >= self.sizeX or self.head[0] < 0 or self.head[1] >= self.sizeY or self.head[1] < 0):
            return True
        return False

    def CheckSnakeBite(self):
        if(len(self.path) == 1):
            return False
        for i in range(len(self.path)-1):
            if(self.path[i] == self.head):
                return True
        return False

    def Move(self):
        if(self.direction == 1):
            self.head[1] += 1
        elif(self.direction == 2):
            self.head[0] += 1
        elif(self.direction == 3):
            self.head[1] -= 1
        else:
            self.head[0] -= 1


        if(not self.isBordered):
            if(self.head[0] == self.sizeX):
                self.head[0] = 0
            elif(self.head[0] < 0):
                self.head[0] = self.sizeX - 1
            elif(self.head[1] == self.sizeY):
                self.head[1] = 0
            elif(self.head[1] < 0):
                self.head[1] = self.sizeY - 1

        if(self.CheckCrash()):
            self.isOver = True
            return False
        self.queue = []

        if self.board[self.head[0]][self.head[1]] == 'Empty':
            self.path.append(self.head[:])
            self.board[self.head[0]][self.head[1]] = 'Snake'
            self.path = self.path[1:len(self.path)]
            if(self.head != self.tail):
                self.board[self.tail[0]][self.tail[1]] = 'Empty'
            self.tail = self.path[0]
        elif(self.board[self.head[0]][self.head[1]] == 'Food'):
            self.path.append(self.head[:])
            self.board[self.head[0]][self.head[1]] = 'Snake'
            self.IncreaseSpeed()
            self.SpawnFood()
        elif(self.board[self.head[0]][self.head[1]] == 'Block'):
            self.board[self.head[0]][self.head[1]] = 'Empty'
            if(len(self.path) == 1):
                return False
            self.path = self.path[1:len(self.path)]
            self.board[self.tail[0]][self.tail[1]] = 'Empty'
            self.tail = self.path[0]
            self.head = self.path[len(self.path)-1][:]
            self.SpawnBlock()

        if(self.CheckSnakeBite()):
            self.isOver = True
            return False
        return True

    def IncreaseSpeed(self):
        self.speed -= 20

    def ChangeDirection(self, inp):
        if(self.direction + inp == 4 or self.direction + inp == 6):
            return
        if(len(self.queue) > 0):
            return
        self.direction = inp
        self.queue.append(inp)
    
    def GetEmptySpaces(self):
        empty = []
        for i in range(self.sizeX):
            for j in range(self.sizeY):
                if(self.board[i][j] == 'Empty'):
                    empty.append([i,j])
        return empty

    def SpawnBlock(self):
        empty = self.GetEmptySpaces()
        rand = random.randint(0,len(empty)-1)
        self.board[empty[rand][0]][empty[rand][1]] = 'Block'

    def SpawnBlocks(self):
        empty = self.GetEmptySpaces()
        blocks = self.sizeX//3
        if(self.difficulty == 'Medium'):
            blocks = 2 * self.sizeX//3
        elif(self.difficulty == 'Hard'):
            blocks = 3 * self.sizeX//4
        rand = random.sample(empty, blocks)
        for i in range(len(rand)):
            self.board[rand[i][0]][rand[i][1]] = 'Block'

    def SpawnFood(self):
        empty = self.GetEmptySpaces()
        rand = random.randint(0,len(empty)-1)
        self.board[empty[rand][0]][empty[rand][1]] = 'Food'

    def Restart(self):
        self.board = []
        for i in range(self.sizeX):
            newArr = []
            for j in range(self.sizeY):
                newArr.append('Empty')
            self.board.append(newArr)
        self.board[0][0] = 'Snake'
        self.head = [0,0]
        self.tail = self.head[:]
        self.path = [self.head[:]]
        self.direction = 1
        self.queue = []
        self.isOver = False
        if(self.difficulty == "Easy"):
            self.speed = 500
        elif(self.difficulty == "Medium"):
            self.speed = 200
        else:
            self.speed = 50
        self.SpawnFood()
        self.SpawnBlocks()

    def GameResponse(self):
        d = {
            "game": {
                "id": self.id,
                "board": self.board,   
                "difficulty": self.difficulty,
                "x": self.sizeX,
                "y": self.sizeY,
                "path": self.path,
                "head": self.head,
                "tail": self.tail,
                "direction": self.direction,
                "isOver": self.isOver,
                "speed": self.speed,
                "isBordered": self.isBordered
            }
        }
        return json.dumps(d)

def Run(ws,game):
    d = ws.receive()
    msg = json.loads(d)
    if(game.isOver):
        return
    if(msg['msg'] == "move"):
        if not game.Move():
            ws.send(json.dumps({"msg": "over", "game": game.GameResponse()}))
        else:
            ws.send(game.GameResponse())
    elif(msg['msg'] == "change"):
        direction = msg['direction']
        game.ChangeDirection(direction)
    elif(msg['msg'] == "restart"):
        game.Restart()
        ws.send(json.dumps({"msg": "restart","game": game.GameResponse()}))

@sock.route('/<int:id>')
def reverse(ws,id):
    game = GetGameById(id)
    if(game == -1):
        return
    while(True):
        Run(ws,game)

@app.route('/', methods = ['POST'])
def game():
    if request.method == 'POST':
        data = request.get_json()
        game = Game(data['x'],data['y'],data['name'],data['difficulty'],data['isBordered'])
        Games.append(game)
        return game.GameResponse()

if __name__ == "__main__":
    app.run(debug=True)

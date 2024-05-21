from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
import sys, random,copy

class PoPoPenk(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tboard = MainBoard(self)
        self.setCentralWidget(self.tboard)
        self.statusbar = self.statusBar()
        self.tboard.msg[str].connect(self.statusbar.showMessage)
        self.tboard.start()
        self.resize(300, 500)
        #location
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)
        ##name
        self.setWindowTitle('PoPoPenk')
        self.show()

class MainBoard(QFrame):
    msg = pyqtSignal(str)
    BoardWidth = 10
    BoardHeight = 20
    Speed = 300
    flag=True
    isspleep=False
    isadd = False
    def __init__(self, parent):
        super().__init__(parent)
        self.initBoard()
        for i in range(200):
          self.setBrickAt(random.randint(0, MainBoard.BoardWidth - 1), random.randint(0, MainBoard.BoardHeight - 1), random.randint(1, 7))
        self.RemoveAll()

    def initBoard(self):
        self.timer = QBasicTimer()
        self.isWaitingAfterLine = False##True表示正在下落
        self.curX = 0
        self.curY = 0
        self.numRemoved = 0
        self.board = []
        self.setFocusPolicy(Qt.StrongFocus)
        self.isStarted = False
        self.isPaused = False
        self.isOver=False
        self.clearAll()


    def brickAt(self, j, i):
        return self.board[(i * MainBoard.BoardWidth) + j]
###直接往下？
    def setBrickAt(self, j, i, brick):
        self.board[(i * MainBoard.BoardWidth) + j] = brick

    def squareWidth(self):
        return self.contentsRect().width() // MainBoard.BoardWidth

    def squareHeight(self):
        return self.contentsRect().height() // MainBoard.BoardHeight
####游戏事件
    def start(self):
        if self.isPaused:
            return
        self.isStarted = True
        self.isWaitingAfterLine = False
        self.numRemoved = 0
        self.clearAll()
        self.msg.emit(str(self.numRemoved))
        self.newOne()
        self.timer.start(MainBoard.Speed, self)
        self.update()

    def pause(self):
        if not self.isStarted:
            return
        self.isPaused = not self.isPaused
        if self.isPaused:
            self.timer.stop()
            self.msg.emit("paused")
        else:
            self.timer.start(MainBoard.Speed, self)
            self.msg.emit(str(self.numRemoved))
        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.contentsRect()
        boardTop = rect.bottom() - MainBoard.BoardHeight * self.squareHeight()
        for i in range(MainBoard.BoardHeight):
            for j in range(MainBoard.BoardWidth):
                shape = self.brickAt(j, MainBoard.BoardHeight - i - 1)
                if shape != 0:
                        self.drawOne(painter,
                                     rect.left() + j * self.squareWidth(),
                                     boardTop + i * self.squareHeight(), shape, 0)

        if self.curPiece.shape() !=0:
            for i in range(2):
                x = self.curX + self.curPiece.x(i)
                y = self.curY - self.curPiece.y(i)
                ##一格一格填充
                self.drawOne(painter, rect.left() + x * self.squareWidth(),
                             boardTop + (MainBoard.BoardHeight - y - 1) * self.squareHeight(),
                             self.curPiece.shape(), i)

    def keyPressEvent(self, event):
        key = event.key()
        if self.isOver:#restart
            super(MainBoard, self).keyPressEvent(event)
            if key == Qt.Key_R:
                for i in range(MainBoard.BoardHeight * MainBoard.BoardWidth):
                    self.board[i] =0
                for i in range(200):
                    self.setBrickAt(random.randint(0, MainBoard.BoardWidth - 1),
                                    random.randint(0, MainBoard.BoardHeight - 1), random.randint(1, 7))
                self.RemoveAll()
                self.update()
                self.start()
                self.isOver=False
                return
            return

        if key == Qt.Key_P:
            self.pause()
            return
        if self.isPaused:
            return

        elif key == Qt.Key_Left:
            self.tryMove(self.curPiece, self.curX - 1, self.curY)
        elif key == Qt.Key_Right:
            self.tryMove(self.curPiece, self.curX + 1, self.curY)
        elif key == Qt.Key_Down:
            self.tryMove(self.curPiece.rotateRight(), self.curX, self.curY)
        elif key == Qt.Key_Up:
            self.tryMove(self.curPiece.rotateLeft(), self.curX, self.curY)
        elif key == Qt.Key_Space:
            self.dropDown()
        elif key == Qt.Key_D:
            self.oneLineDown()
        else:
            super(MainBoard, self).keyPressEvent(event)

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.isWaitingAfterLine:##待下落（前面没下完不下）
                self.isWaitingAfterLine = False
                self.newOne()
            else:
                self.oneLineDown()
        else:
            super(MainBoard, self).timerEvent(event)

    def clearAll(self):
        for i in range(MainBoard.BoardHeight * MainBoard.BoardWidth):
            self.board.append(0)

    def dropDown(self):
        newY = self.curY
        while newY > 0:##一直下落直到碰撞
            if not self.tryMove(self.curPiece, self.curX, newY - 1):
                break
            newY -= 1
        self.OneDropped()

    def oneLineDown(self):##一行一行下落
        if not self.tryMove(self.curPiece, self.curX, self.curY - 1):
            self.OneDropped()

    def OneDropped(self):
        self.isspleep=True
        for i in range(2):
            x = self.curX + self.curPiece.x(i)
            y = self.curY - self.curPiece.y(i)
            self.setBrickAt(x, y, self.curPiece.shape() + i)####
        for j in range(MainBoard.BoardWidth):
            templist = []  # 存储第j列的所有元素的列表
            for i in range(MainBoard.BoardHeight):
                templist.append(self.brickAt(j, i))
            count = 0
            while 0 in templist:
                templist.remove(0)
                count += 1
                # 把对应0元素移动到列表起始位置
            for i in range(count):
                templist.append(0)
                # 再赋值给原始的二维数组
            for i in range(len(templist)):
                self.setBrickAt(j, i, templist[i])
        self.RemoveAll()##在函数里判断是否移除
        if not self.isWaitingAfterLine:
            self.newOne()

#############################消除####################
    def RemoveCont(self, pos):
        connectedSet = {( pos[0]  , pos[1] )}
        # 创建集合，存储选中方块及其连通的点序号
        while True:  # 重复找，
            len1=len(connectedSet)
            tempSet = copy.deepcopy(connectedSet)  # 复制一份临时集合
            for each in tempSet:  # 对集合中所有小方块处理
                i = each[1]  # 小方块对应的行序号
                j = each[0]  # 小方块对应的列序号
                colorId = self.brickAt(j, i)
                if i > 0 and self.brickAt(j, i - 1) == colorId:
                    connectedSet.add((j, i - 1))
                if i < MainBoard.BoardHeight - 1 and self.brickAt(j, i + 1) == colorId:
                    connectedSet.add((j, i + 1))
                if j > 0 and self.brickAt(j - 1, i) == colorId:
                    connectedSet.add((j - 1, i))
                if j < MainBoard.BoardWidth - 1 and self.brickAt(j + 1, i) == colorId:
                    connectedSet.add((j + 1, i))
            tempSet.clear()
            len2=len(connectedSet)# 临时集合清空
            if (len2==len1):
              break
        if len(connectedSet) >= 3:
            for each in connectedSet:  # 集合中的所有方块遍历
                if self.brickAt(each[0], each[1]) != 0:
                    self.setBrickAt(each[0], each[1], 0)# 标记为0，对应黑色小方块
                    self.numRemoved+=1
                self.repaint()
            self.flag=False

    def RemoveAll(self):
      while True:
         self.flag=True
          # 从下往上遍历，下面一个是0的话，上面的小色块就往下落。最顶上的空出来，变成黑色
         for j in range(MainBoard.BoardWidth):
            templist = []  # 存储第j列的所有元素的列表
            for i in range(MainBoard.BoardHeight):
                templist.append(self.brickAt(j, i))
            count = 0
            while 0 in templist:
                templist.remove(0)
                count += 1

            for i in range(count):# 把对应0元素移动到列表起始位置
                templist.append(0)

            for i in range(len(templist)):# 再赋值给原始的二维数组
                self.setBrickAt(j, i, templist[i])

         for i1 in range(MainBoard.BoardHeight):
            for j1 in range(MainBoard.BoardWidth):
                if not self.brickAt(j1, i1) == 0:
                    pos=[j1,i1]
                    self.RemoveCont(pos)
         if self.flag:
             break
      self.msg.emit(str(self.numRemoved))

    def newOne(self):
        self.curPiece = Brick()
        self.curPiece.setRandomBrick()
        ##开始坐标
        self.curX = MainBoard.BoardWidth // 2
        self.curY = MainBoard.BoardHeight - 1 + self.curPiece.minY()
        if not self.tryMove(self.curPiece, self.curX, self.curY):
            self.curPiece.setBrick(0)
            self.isOver=True
            self.msg.emit("GAME OVER,your scores:"+str(self.numRemoved))

    def tryMove(self, newPiece, newX, newY):
        for i in range(2):
            x = newX + newPiece.x(i)
            y = newY - newPiece.y(i)
            if x < 0 or x >= MainBoard.BoardWidth or y < 0 or y >= MainBoard.BoardHeight:
                return False
            if self.brickAt(x, y) != 0:##占位
                return False
        self.curPiece = newPiece
        self.curX = newX
        self.curY = newY
        self.update()
        return True
#################################上色##################################################
    def drawOne(self, painter, x, y, brick, i):##需要分两部分
        colorTable = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]
        color = QColor(colorTable[(brick + i) % 8])
        painter.fillRect(x + 1, y +1, self.squareWidth() -2,
            self.squareHeight() - 2, color)



########方块########

class Brick(object):
    coordsTable = (
        ((0, 0),     (0, 0)),
        ((0, 1),    (0, 0))
    )

    def __init__(self):
        self.coords = [[0,0] for i in range(2)]
        self.piece = 0
        self.setBrick(0)

    def shape(self):
        return self.piece

    def setBrick(self, brick):
        table = Brick.coordsTable[1]#第shape行
        for i in range(2):
            for j in range(2):
                self.coords[i][j] = table[i][j]#转化为4*2矩阵
        self.piece = brick
    def setRandomBrick(self):
        self.setBrick(random.randint(1, 7))
##旋转图像
    def rotateLeft(self):
        result = Brick()
        result.piece = self.piece
        for i in range(4):
            result.setX(i, self.y(i))
            result.setY(i, -self.x(i))
        return result

    def rotateRight(self):
        result = Brick()
        result.piece = self.piece
        for i in range(4):
            result.setX(i, -self.y(i))
            result.setY(i, self.x(i))
        return result
######一些辅助函数
    def x(self, index):
        return self.coords[index][0]

    def y(self, index):
        return self.coords[index][1]

    def setX(self, index, x):
        self.coords[index][0] = x

    def setY(self, index, y):
        self.coords[index][1] = y

    def minX(self):
        m = self.coords[0][0]
        for i in range(2):
            m = min(m, self.coords[i][0])
        return m

    def maxX(self):
        m = self.coords[0][0]
        for i in range(2):
            m = max(m, self.coords[i][0])
        return m

    def minY(self):
        m = self.coords[0][1]
        for i in range(2):
            m = min(m, self.coords[i][1])
        return m

    def maxY(self):
        m = self.coords[0][1]
        for i in range(2):
            m = max(m, self.coords[i][1])
        return m


if __name__ == '__main__':
    app = QApplication([])
    popopenk = PoPoPenk()
    sys.exit(app.exec_())
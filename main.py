import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath

class Block(QGraphicsItem):
    def __init__(self, x, y, w, h, text):
        super().__init__()
        self.rect = QRectF(0, 0, w, h)
        self.text = text
        self.setPos(x, y)
        self.pen = QPen(Qt.black, 1)  # Thin black outline
        self.brush = QBrush(Qt.transparent)  # No fill
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        path = QPainterPath()
        path.addRoundedRect(self.rect, 5, 5)  # Slightly rounded corners
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawPath(path)
        painter.drawText(self.rect, Qt.AlignCenter, self.text)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for line in self.scene().items():
                if isinstance(line, Connection) and (line.startItem == self or line.endItem == self):
                    line.updatePosition()
        return super().itemChange(change, value)

class Connection(QGraphicsItem):
    def __init__(self, startItem, endItem):
        super().__init__()
        self.startItem = startItem
        self.endItem = endItem
        self.setZValue(-1)
        self.updatePosition()

    def boundingRect(self):
        return QRectF(self.line().p1(), self.line().p2()).normalized()

    def paint(self, painter, option, widget):
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(self.line())

    def updatePosition(self):
        self.setLine(QLineF(self.startItem.sceneBoundingRect().center(),
                            self.endItem.sceneBoundingRect().center()))

    def setLine(self, line):
        self._line = line
        self.prepareGeometryChange()

    def line(self):
        return self._line

class SystemView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(Qt.white))  # White background

    def create_system_from_spec(self, spec):
        # Clear existing items
        self.scene.clear()

        # Parse the spec and create blocks and connections
        blocks = {}
        for line in spec.strip().split('\n'):
            parts = line.split()
            if parts[0] == 'block':
                name, x, y, w, h = parts[1:6]
                text = ' '.join(parts[6:])  # Join the remaining parts as the text
                block = Block(float(x), float(y), float(w), float(h), text)
                self.scene.addItem(block)
                blocks[name] = block
            elif parts[0] == 'connect':
                start, end = parts[1], parts[2]
                connection = Connection(blocks[start], blocks[end])
                self.scene.addItem(connection)

        # Adjust the scene rect to fit all items
        self.scene.setSceneRect(self.scene.itemsBoundingRect())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamical System Visualizer")
        self.view = SystemView()
        self.setCentralWidget(self.view)

        # Example specification
        spec = """
        block A 0 0 100 50 "System A"
        block B 200 0 100 50 "System B"
        block C 100 100 100 50 "Sum"
        connect A C
        connect B C
        """
        self.view.create_system_from_spec(spec)
        self.view.fitInView(self.view.scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.fitInView(self.view.scene.sceneRect(), Qt.KeepAspectRatio)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())
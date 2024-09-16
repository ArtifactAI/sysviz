import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath, QPolygonF
import math

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
        self.arrowSize = 5
        self.pen = QPen(Qt.black, 1)  # Define the pen here

    def boundingRect(self):
        extra = (self.pen.width() + self.arrowSize) / 2.0
        return QRectF(self.line().p1(), self.line().p2()).normalized().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setBrush(Qt.black)

        line = self.line()
        painter.drawLine(line)

        # Draw the arrow
        angle = math.atan2(-line.dy(), line.dx())
        arrowP1 = line.p2() - QPointF(math.sin(angle + math.pi / 3) * self.arrowSize,
                                      math.cos(angle + math.pi / 3) * self.arrowSize)
        arrowP2 = line.p2() - QPointF(math.sin(angle + math.pi - math.pi / 3) * self.arrowSize,
                                      math.cos(angle + math.pi - math.pi / 3) * self.arrowSize)

        arrowHead = QPolygonF()
        arrowHead.append(line.p2())
        arrowHead.append(arrowP1)
        arrowHead.append(arrowP2)
        painter.drawPolygon(arrowHead)

    def updatePosition(self):
        start_point = self.getEdgePoint(self.startItem, self.endItem)
        end_point = self.getEdgePoint(self.endItem, self.startItem)
        self.setLine(QLineF(start_point, end_point))

    def setLine(self, line):
        self._line = line
        self.prepareGeometryChange()

    def line(self):
        return self._line

    def getEdgePoint(self, sourceItem, targetItem):
        source_rect = sourceItem.sceneBoundingRect()
        target_center = targetItem.sceneBoundingRect().center()
        
        # Calculate the center points of each edge
        top = QPointF(source_rect.center().x(), source_rect.top())
        bottom = QPointF(source_rect.center().x(), source_rect.bottom())
        left = QPointF(source_rect.left(), source_rect.center().y())
        right = QPointF(source_rect.right(), source_rect.center().y())
        
        # Find the edge point closest to the target center
        edge_points = [top, bottom, left, right]
        return min(edge_points, key=lambda p: QLineF(p, target_center).length())

class SystemView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(Qt.white))  # White background
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # Enable panning

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Remove the fitInView call to keep blocks the same size

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())
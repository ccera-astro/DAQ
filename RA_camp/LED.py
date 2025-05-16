from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtCore import Qt

class LED(QWidget):
    def __init__(self, color="red", on=False, shape="circle", parent=None):
        super().__init__(parent)
        self.color = color
        self.on = on
        self.shape = shape
        self.setFixedSize(20, 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.on:
            painter.setBrush(QBrush(QColor(self.color)))
        else:
            painter.setBrush(QBrush(QColor("gray")))

        if self.shape == "circle":
            painter.drawEllipse(0, 0, self.width(), self.height())
        elif self.shape == "square":
            painter.drawRect(0, 0, self.width(), self.height())

    def set_on(self, on):
        self.on = on
        self.update()

    def set_color(self, color):
        self.color = color
        self.update()

    def set_shape(self, shape):
        self.shape = shape
        self.update()
from PySide2 import QtCore, QtGui
import sys

class Example(QWidget):
    def __init__(self):
        super(Example, self).__init__()
        self.setGeometry(300, 300, 250, 150)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            print("Killing")
            self.deleteLater()
        elif event.key() == QtCore.Qt.Key_Enter:
            self.proceed()
        event.accept()

    def proceed(self):
        print ("Call Enter Key")

def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
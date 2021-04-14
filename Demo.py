import sys
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QWidget





class Window(QWidget):
    def keyevent_to_string(self,event):
        sequence = []
        for modifier, text in modmap.items():
            if event.modifiers() & modifier:
                sequence.append(text)
        key = keymap.get(event.key(), event.text())
        if key not in sequence:
            sequence.append(key)
        return '+'.join(sequence)
    def keyPressEvent(self, event):
        X = self.keyevent_to_string(event)
        print(X)
        if X == "Up":
            print('Pressed')

if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = Window()
    window.setGeometry(600, 100, 300, 200)
    window.show()
    sys.exit(app.exec_())
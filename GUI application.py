import sys

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtPrintSupport import *
from PySide2.QtGui import QIcon
from PySide2 import QtGui, QtCore
import os
import webbrowser
from galilBackend import Galil

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QApplication, QWidget, QTabWidget, QDialog,
                               QMainWindow, QVBoxLayout, QLabel, QPushButton,
                               QFormLayout, QHBoxLayout, QMenuBar, QMenu,
                               QAction, QComboBox, QGroupBox, QSpinBox, QRadioButton, QGridLayout,
                               QLineEdit, QStatusBar, QFileDialog)

import h5py
import yaml
import numpy as np
from Picoscope import Picoscope
from Siglent import FunctionGenerator
import pyqtgraph as pg
import gclib
import time as t

keymap = {}
for key, value in vars(Qt).items():
    if isinstance(value, Qt.Key):
        keymap[value] = key.partition('_')[2]

modmap = {
    Qt.ControlModifier: keymap[Qt.Key_Control],
    Qt.AltModifier: keymap[Qt.Key_Alt],
    Qt.ShiftModifier: keymap[Qt.Key_Shift],
    Qt.MetaModifier: keymap[Qt.Key_Meta],
    Qt.GroupSwitchModifier: keymap[Qt.Key_AltGr],
    Qt.KeypadModifier: keymap[Qt.Key_NumLock],
}


class MainWindow(QMainWindow):
    def __init__(self):  # creates a constructor for the MainWindow Object
        super().__init__()
        self.yEnabled = False
        self.xEnabled = False
        self.zEnabled = False
        self.feedback_Update = QTextBrowser()
        self.Keyboard_Update = False
        self.scanData = None
        self.config = None
        self.load_parameters()
        self.func = None
        self.pico = None
        self.f = None
        self.scanning = False

        self.width = 1
        self.depth = 1
        self.height = 1
        self.xCoordinates = np.zeros(1)
        self.yCoordinates = np.zeros(1)
        self.zCoordinates = np.zeros(1)



        # app = QApplication(sys.argv)
        # self.screen_resolution = app.desktop().screenGeometry()
        self.screen_resolution = None

        self.initialize_FunctionGenerator()
        self.initialize_Picoscope()
        self.Galil = Galil()

        self.Galil.x_pos.connect(self.update_position_x)
        self.Galil.y_pos.connect(self.update_position_y)
        self.Galil.z_pos.connect(self.update_position_z)
        self.Galil.limits.connect(self.get_limit_status)

        # setting title
        self.setWindowTitle("Ultra Hydrophonics")

        # setting geometry
        self.setGeometry(70, 70, 1800, 900)
        # calling UI components
        self.ui_components()
        # showing all the widgets
        self.show()
        self.path = None

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        file_menu = self.menuBar().addMenu("&File")

        open_file_action = QAction(QIcon(os.path.join('images', 'blue-folder-open-document.png')), "Open file...", self)
        open_file_action.setStatusTip("Open file")
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)

        save_file_action = QAction(QIcon(os.path.join('images', 'disk.png')), "Save", self)
        save_file_action.setStatusTip("Save current page")
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)

        saveas_file_action = QAction(QIcon(os.path.join('images', 'disk--pencil.png')), "Save As...", self)
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)

        print_action = QAction(QIcon(os.path.join('images', 'printer.png')), "Print...", self)
        print_action.setStatusTip("Print current page")
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)

        # adding Help on menu bar and open a specific file saved as "Help"
        file_menu = self.menuBar().addMenu("&Help")

        Show_Help_action = QAction(QIcon(os.path.join('images', 'blue-folder-open-document.png')), "Open Help...", self)
        Show_Help_action.setStatusTip("Open Help")
        Show_Help_action.triggered.connect(self.Show_Help)
        file_menu.addAction(Show_Help_action)

    @Slot(int)
    def update_position_x(self, position):
        position = np.round(position / self.config["galil_mmConversion"], 2)
        self.xPosition.setText(str(position) + ' mm')
        print(position)

    @Slot(int)
    def update_position_y(self, position):
        position = np.round(position / self.config["galil_mmConversion"], 2)
        self.yPosition.setText(str(position) + ' mm')
        print(position)

    @Slot(int)
    def update_position_z(self, position):
        position = np.round(position / self.config["galil_mmConversion"], 2)
        self.zPosition.setText(str(position) + ' mm')
        print(position)

    @Slot(str)
    def get_limit_status(self, limit):
        self.feedback_Update.append('Cannot jog: ' + limit)

    def ui_components(self):
        # Notes of what I've learned
        # - Group Boxes need to have a general layout assigned to them
        # - This layout must match that with the components being added to them (vbox1, vbox2)
        # - Central Widget Layout must match that of the groupboxes
        # - This doesn't take into account complex layout structures
        # - Grid Layout Option is the way to go (can stretch the boxes when needed)

        # LAYOUTS
        # LAYOUTS - Vertical Layout
        # Used for setting a vertical layout for certain groupboxes
        self.showMaximized()
        self.releaseKeyboard()


        self.vbox1 = QVBoxLayout()
        self.vbox2 = QVBoxLayout()
        self.vbox3 = QVBoxLayout()
        self.vbox4 = QVBoxLayout()
        self.vbox5 = QVBoxLayout()

        self.hbox = QHBoxLayout()
        self.formLayout = QFormLayout()
        self.grid = QGridLayout()
        self.gridScan = QGridLayout()

        # GIANT GROUP BOXES
        # GIANT GROUP BOXES - Layout
        self.giantGrid1 = QGridLayout()
        self.giantGrid2 = QGridLayout()

        # GIANT GROUP BOXES - Creation
        self.giantGroupBox1 = QGroupBox('')
        self.giantGroupBox1.setLayout(self.giantGrid1)
        self.giantGroupBox2 = QGroupBox('')
        self.giantGroupBox2.setLayout(self.giantGrid2)

        # HARDWARE SETTINGS
        # HARDWARE SETTINGS - Group Box
        # Created a Group Box to contain the tabs for the Hardware
        self.tabGroupBox = QGroupBox('Hardware Settings')
        self.tabGroupBox.setStyleSheet('QGroupBox { color: #52988C; font: bold 12pt; }')
        self.tabGroupBox.setLayout(self.vbox1)  # Setting the layout of the group box as vertical

        # HARDWARE SETTINGS - Tab Widget
        # Assigning a variable from the Class tabWidget

        self.tabWidgetBox = tabWidget(self, self.config, self.pico,self.Keyboard_Update,self.func, self.feedback_Update,galil=self.Galil)

        # Adding Group Boxes to the widget
        self.giantGrid1.addWidget(self.tabGroupBox, 0, 0)  # Adds the Group Box to the Grid Layout
        self.vbox1.addWidget(self.tabWidgetBox.tabs)  # Adds Tabs to the Hardware Settings GroupBox

        # HARDWARE SETTINGS - Setting Width
        # Set a fixed width for the Hardware Settings Group Box & Tab Widget
        self.tabGroupBox.setFixedWidth(525)
        self.tabWidgetBox.tabs.setFixedWidth(500)

        # Creating Notes Settings
        self.notesGroupBox = QGroupBox('Notes')
        self.notesGroupBox.setStyleSheet('QGroupBox { color: #52988C; font: bold 12pt; }')
        self.notesGroupBox.setLayout(self.vbox2)

        self.giantGrid1.addWidget(self.notesGroupBox, 0, 1)

        # Creating a note pad
        self.editor = QPlainTextEdit()
        self.vbox2.addWidget(self.editor)
        self.saveNotesBtn = QPushButton('Save Notes')
        self.vbox2.addWidget(self.saveNotesBtn)

        # Adding action to the save button
        self.saveNotesBtn.clicked.connect(self.file_saveas)

        # Setup the QTextEdit editor configuration
        fixedfont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixedfont.setPointSize(11)
        self.editor.setFont(fixedfont)

        # Test box under
        self.testGroupBox = QGroupBox('Scan Area Settings')
        self.testGroupBox.setStyleSheet('QGroupBox { color: #52988C; font: bold 12pt; }')
        self.testGroupBox.setLayout(self.gridScan)

        # Test Box: Widgets
        self.minLabel = QLabel()
        self.samplesLabel = QLabel()
        self.maxLabel = QLabel()
        self.xAxisLabel = QLabel()
        self.yAxisLabel = QLabel()
        self.zAxisLabel = QLabel()
        self.positionLabel = QLabel()
        self.blankLabel = QLabel()
        self.blankLabel2 = QLabel()
        self.homeLabel = QLabel()
        self.speedLabel = QLabel()
        self.keyboardLabel = QLabel()
        self.loadLabel = QLabel()

        # Test Box - Label: Assigning Names
        # SCAN AREA - LABELS: Assigning Names
        # Assigned the names for the labels
        self.minLabel.setText('Negative limit (mm)')
        self.samplesLabel.setText('# Samples')
        self.maxLabel.setText('Positive limit (mm)')
        self.xAxisLabel.setText('X-Axis')
        self.yAxisLabel.setText('Y-Axis')
        self.zAxisLabel.setText('Z-Axis')
        self.positionLabel.setText('Current Position')
        self.blankLabel.setText('        ')
        self.blankLabel2.setText('        ')
        self.homeLabel.setText('Set Current Position as Home')
        self.speedLabel.setText('Speed')
        self.keyboardLabel.setText('Keyboard Control')
        self.loadLabel.setText('Load in Position')

        self.xAxisLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # Aligning label horizontally
        self.yAxisLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # Aligning label horizontally
        self.zAxisLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # Aligning label horizontally
        self.minLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # Aligning label horizontally
        self.maxLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # Aligning label horizontally
        self.samplesLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # Aligning label horizontally
        self.positionLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.homeLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.speedLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.keyboardLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.loadLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # Test Box - SpinBox
        self.xMinSb = QDoubleSpinBox()  # x-axis min spinbox
        self.xMinSb.setRange(-1 * self.config["galil_xLimit"], 0)
        self.xMinSb.setSingleStep(self.config["galil_step"])
        self.xMaxSb = QDoubleSpinBox()  # x-axis max spinbox
        self.xMaxSb.setRange(0, self.config["galil_xLimit"])
        self.xMaxSb.setSingleStep(self.config["galil_step"])
        self.xSamplesSb = QSpinBox()  # x-axis step spinbox
        self.xSamplesSb.setRange(1, self.config["galil_maxSamples"])
        self.yMinSb = QDoubleSpinBox()  # y-axis min spinbox
        self.yMinSb.setRange(-1 * self.config["galil_yLimit"], 0)
        self.yMinSb.setSingleStep(self.config["galil_step"])
        self.yMinSb.setValue(-18.0)
        self.yMaxSb = QDoubleSpinBox()  # y-axis max spinbox
        self.yMaxSb.setRange(0, self.config["galil_yLimit"])
        self.yMaxSb.setSingleStep(self.config["galil_step"])
        self.yMaxSb.setValue(18.0)
        self.ySamplesSb = QSpinBox()  # y-axis step spinbox
        self.ySamplesSb.setRange(1, self.config["galil_maxSamples"])
        self.ySamplesSb.setValue(15)
        self.zMinSb = QDoubleSpinBox()  # z-axis min spinbox
        self.zMinSb.setRange(-1 * self.config["galil_zLimit"], 0)
        self.zMinSb.setSingleStep(self.config["galil_step"])
        self.zMinSb.setValue(-18.0)
        self.zMaxSb = QDoubleSpinBox()  # z-axis max spinbox
        self.zMaxSb.setRange(0, self.config["galil_zLimit"])
        self.zMaxSb.setSingleStep(self.config["galil_step"])
        self.zMaxSb.setValue(18.0)
        self.zSamplesSb = QSpinBox()  # z-axis step spinbox
        self.zSamplesSb.setRange(1, self.config["galil_maxSamples"])
        self.zSamplesSb.setValue(15)

        self.Scan = QPushButton('Scan')
        self.Scan.pressed.connect(self.scan)

        self.xLoadSb = QSpinBox()  # Load position spinbox
        self.yLoadSb = QSpinBox()
        self.zLoadSb = QSpinBox()

        # Scan Area - QCheckBoxes
        # Figureing out how to turn on and off function
        self.xCheckBox = QCheckBox('X-Axis')
        self.xCheckBox.toggled.connect(self.checkBox_state)
        self.yCheckBox = QCheckBox('Y-Axis')
        self.yCheckBox.toggled.connect(self.checkBox_state)

        self.zCheckBox = QCheckBox('Z-Axis')
        self.zCheckBox.toggled.connect(self.checkBox_state)

        self.yCheckBox.setChecked(True)
        self.zCheckBox.setChecked(True)

        self.checkBox_state()



        # Test Box - Resizing Widgets
        # self.xMinSb.setFixedWidth(100)
        # self.xMaxSb.setFixedWidth(100)
        # self.xSamplesSb.setFixedWidth(100)
        # self.yMinSb.setFixedWidth(100)
        # self.yMaxSb.setFixedWidth(100)
        # self.ySamplesSb.setFixedWidth(100)
        # self.zMinSb.setFixedWidth(100)
        # self.zMaxSb.setFixedWidth(100)
        # self.zSamplesSb.setFixedWidth(100)

        # self.minLabel.setFixedWidth(100)
        self.minLabel.setFixedHeight(50)
        # self.maxLabel.setFixedWidth(100)
        self.maxLabel.setFixedHeight(50)
        # self.samplesLabel.setFixedWidth(100)
        self.samplesLabel.setFixedHeight(50)
        self.homeLabel.setFixedHeight(50)

        # Test Box - QLineEdit
        self.xPosition = QLineEdit()
        self.xPosition.setReadOnly(True)  # Can't be edited
        self.yPosition = QLineEdit()
        self.yPosition.setReadOnly(True)
        self.zPosition = QLineEdit()
        self.zPosition.setReadOnly(True)

        # Test Box - QPushButton

        self.xUpBtn = QPushButton('X Forward')
        self.xUpBtn.pressed.connect(self.X_Up)
        self.xUpBtn.released.connect(self.stop_motion)

        self.xDownBtn = QPushButton('X Backwards')
        self.xDownBtn.pressed.connect(self.X_Down)
        self.xDownBtn.released.connect(self.stop_motion)

        self.yUpBtn = QPushButton('Y Left')
        self.yUpBtn.pressed.connect(self.Y_Up)
        self.yUpBtn.released.connect(self.stop_motion)

        self.yDownBtn = QPushButton('Y Right')
        self.yDownBtn.pressed.connect(self.Y_Down)
        self.yDownBtn.released.connect(self.stop_motion)

        self.zUpBtn = QPushButton('Z Up')
        self.zUpBtn.pressed.connect(self.Z_Up)
        self.zUpBtn.released.connect(self.stop_motion)

        self.zDownBtn = QPushButton('Z Down')
        self.zDownBtn.pressed.connect(self.Z_Down)
        self.zDownBtn.released.connect(self.stop_motion)

        self.setHomeBtn = QPushButton('Set Home')
        self.setHomeBtn.clicked.connect(self.set_origin_pressed)

        self.goHomeBtn = QPushButton('Go Home')
        self.goHomeBtn.pressed.connect(self.go_home_button)

        # Test Box - QComboBox
        self.speedCombo = QComboBox()
        self.speedCombo.addItems(['LOW', 'MEDIUM', 'HIGH'])
        self.keyboardCombo = QComboBox()
        self.keyboardCombo.addItems(['OFF', 'ON'])

        self.AbortBtn = QPushButton('Abort')
        self.AbortBtn.setStyleSheet("background-color: red")
        self.AbortBtn.pressed.connect(self.abort_button)

        # Organizing into a grid
        self.giantGrid1.addWidget(self.testGroupBox, 1, 0, 1, 2)  # extends column & row size of groupbox

        self.gridScan.addWidget(self.minLabel, 0, 1, 1, 1)
        self.gridScan.addWidget(self.samplesLabel, 0, 2, 1, 1)
        self.gridScan.addWidget(self.maxLabel, 0, 3, 1, 1)
        # self.gridScan.addWidget(self.xAxisLabel, 1, 0, 1, 1) REMOVE THIS LATER
        self.gridScan.addWidget(self.xCheckBox, 1, 0)
        # self.gridScan.addWidget(self.yAxisLabel, 2, 0, 1, 1)
        self.gridScan.addWidget(self.yCheckBox, 2, 0)
        # self.gridScan.addWidget(self.zAxisLabel, 3, 0, 1, 1)
        self.gridScan.addWidget(self.zCheckBox, 3, 0)

        self.gridScan.addWidget(self.xMinSb, 1, 1)
        self.gridScan.addWidget(self.xSamplesSb, 1, 2)
        self.gridScan.addWidget(self.xMaxSb, 1, 3)
        self.gridScan.addWidget(self.yMinSb, 2, 1)
        self.gridScan.addWidget(self.ySamplesSb, 2, 2)
        self.gridScan.addWidget(self.yMaxSb, 2, 3)
        self.gridScan.addWidget(self.zMinSb, 3, 1)
        self.gridScan.addWidget(self.zSamplesSb, 3, 2)
        self.gridScan.addWidget(self.zMaxSb, 3, 3)
        self.gridScan.addWidget(self.Scan, 4, 2)

        self.gridScan.addWidget(self.positionLabel, 5, 2)
        self.gridScan.addWidget(self.xPosition, 6, 1)
        self.gridScan.addWidget(self.yPosition, 6, 2)
        self.gridScan.addWidget(self.zPosition, 6, 3)
        # self.gridScan.addWidget(self.loadLabel, 7, 2)
        # self.gridScan.addWidget(self.xLoadSb, 8, 1)
        # self.gridScan.addWidget(self.yLoadSb, 8, 2)
        # self.gridScan.addWidget(self.zLoadSb, 8, 3) REMOVE THESE LATER

        self.gridScan.addWidget(self.blankLabel, 1, 4)  # Blank Label work around to seperate widgets
        self.gridScan.addWidget(self.xUpBtn, 1, 5)
        self.gridScan.addWidget(self.xDownBtn, 1, 6)
        self.gridScan.addWidget(self.yUpBtn, 2, 5)
        self.gridScan.addWidget(self.yDownBtn, 2, 6)
        self.gridScan.addWidget(self.zUpBtn, 3, 5)
        self.gridScan.addWidget(self.zDownBtn, 3, 6)
        # self.gridScan.addWidget(self.homeLabel, 4, 5, 1, 2) Remove these later
        self.gridScan.addWidget(self.setHomeBtn, 5, 5, 1, 2)
        self.gridScan.addWidget(self.goHomeBtn, 6, 5, 1, 2)
        self.gridScan.addWidget(self.AbortBtn, 7, 1, 1, 3)

        self.gridScan.addWidget(self.blankLabel2, 1, 7)
        # self.gridScan.addWidget(self.speedLabel, 0, 8)
        # self.gridScan.addWidget(self.speedCombo, 1, 8)
        # self.gridScan.addWidget(self.keyboardLabel, 2, 8)
        # self.gridScan.addWidget(self.keyboardCombo, 3, 8) REMOVE THESE FOR LATER

        # Plot Box
        self.plotGroupBox = QGroupBox('Graph Box')
        self.plotGroupBox.setStyleSheet('QGroupBox { color: #52988C; font: bold 12pt; }')
        self.plotGroupBox.setLayout(self.vbox4)

        self.giantGrid2.addWidget(self.plotGroupBox, 0, 0, 2, 1)
        self.vbox4.addWidget(self.tabWidgetBox.graphTabs)

        # Feedback Box
        self.feedbackGroupBox = QGroupBox('Feedback')
        self.feedbackGroupBox.setStyleSheet('QGroupBox { color: #52988C; font: bold 12pt; }')
        self.feedbackGroupBox.setLayout(self.vbox5)

        # Updating feedback message
        self.vbox5.addWidget(self.feedback_Update)
        self.feedback_Update.setObjectName("feedback_Update")
        self.feedback_Update.setFocusPolicy(QtCore.Qt.NoFocus)

        self.giantGrid2.addWidget(self.feedbackGroupBox, 2, 0, 1, 1)

        # SPLITTER
        # Create the splitter to seperate the giant group boxes
        self.splitter = QSplitter(Qt.Horizontal)

        # Add the giant group boxes to the splitter widget
        self.splitter.addWidget(self.giantGroupBox1)
        self.splitter.addWidget(self.giantGroupBox2)

        # These values for setSizes makes it so the screen is split evenly
        self.splitter.setSizes([400, 800])
        self.hbox.addWidget(self.splitter)  # Add splitter to hbox

        # Setting the central widget
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.hbox)  # Set Central Widget to the layout of the splitter
        self.setCentralWidget(self.centralWidget)

        # this will remove minimized status
        # and restore window with keeping maximized/normal state
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)

        # Creates output file, or opens it if it already exists

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    # Menu bar Actions
    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "",
                                              "HDF5 files (*.hdf5); Text documents (*.hdf5 *.txt)")
        if ".txt" in path:
            try:
                with open(path, 'r') as note:
                    text = note.read()
            except Exception as e:
                self.dialog_critical(str(e))
            else:
                self.editor.setPlainText(text)

        if ".hdf5" in path:
            self.path = path
            try:
                with h5py.File(path, "r") as f:
                    # List all groups
                    print("Keys: %s" % f.keys())
                    a_group_key = list(f.keys())[0]

                    # Get the data
                    data = f[a_group_key]
                    print(data["Intensity map"])
                    self.tabWidgetBox.intensityMap.setImage(data["Intensity map"][:][:][:])
                    self.tabWidgetBox.imagePlot.setLabel(axis='bottom', text='y-axis (left/right)')
                    self.tabWidgetBox.imagePlot.setLabel(axis='left', text='z-axis (up/down)')
            except:
                self.feedback_Update.append("Error loading file, it may have not closed properly")

    def file_save(self):

        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()

        self._save_to_path(self.path)

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Text documents (*.txt)")

        if not path:
            # If dialog is cancelled, will return ''
            return

        self._save_to_path(path)

    def _save_to_path(self, path):
        text = self.editor.toPlainText()
        try:
            with open(path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

            # Updating the Feedback window
            Progress = "Document Saved"
            self.feedback_Update.append(str(Progress))

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

        # Updating the Feedback window
        Progress = "Document Printed"
        self.feedback_Update.append(str(Progress))

    def load_parameters(self):
        try:
            with open('default.yaml') as file:
                self.feedback_Update.append("Loading parameters from default.yaml")
                # The FullLoader parameter handles the conversion from YAML
                # scalar values to Python the dictionary format
                self.config = yaml.load(file, Loader=yaml.FullLoader)
        except FileNotFoundError:
            self.feedback_Update.append("default.yaml not found")

        try:
            with open('local.yaml') as file:
                self.feedback_Update.append("Overriding parameters from default.yaml")
                try:
                    changes = yaml.load(file, Loader=yaml.FullLoader)
                    self.cofig.update(changes)
                except:
                    print("No changes made")
        except FileNotFoundError:
            self.feedback_Update.append("Local.yaml not found, no parameters overwritten")

        # print(self.config)

    # Updating the program title

    def update_title(self):
        self.setWindowTitle(
            "%s - Ultra Hydrophonics" % (os.path.basename(self.path.split(".")[0]) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(1 if self.editor.lineWrapMode() == 0 else 0)

    def estimate_time(self):
        numPoints = self.width * self.height * self.depth

        timePerPoint = self.config["picoscope_baseTimePerPoint"] + (self.config["picoscope_baseTimePerWaveform"] +
                                                                    (
                                                                                self.tabWidgetBox.preTriggerSamplesSpinBox.value() + self.tabWidgetBox.postTriggerSamplesSpinBox.value())
                                                                    * float(
                    self.tabWidgetBox.intervalCombo.currentText()) / (
                                                                        1000000000)) * self.tabWidgetBox.waveformsSpinBox.value()

        totalTime = timePerPoint * numPoints

        if totalTime < 180:
            self.feedback_Update.append("Estimated scan time = " + str(totalTime) + " seconds")
        else:
            self.feedback_Update.append("Estimated scan time= " + str(int(totalTime / 60)) + "minutes")

    def estimate_fileSize(self):
        numPoints = self.width * self.height * self.depth

        dataPerPoint = self.config["picoscope_baseDataPerPoint"] + (
                    self.tabWidgetBox.preTriggerSamplesSpinBox.value() + self.tabWidgetBox.postTriggerSamplesSpinBox.value()) * \
                       self.config["picoscope_dataPerSample"]

        totalData = dataPerPoint * numPoints + self.config["picoscope_baseDataPerScan"]

        if totalData < 10000000:
            self.feedback_Update.append("Estimated file size = " + str(totalData / 1000) + " kilobytes")
        else:
            self.feedback_Update.append("Estimated file size = " + str(totalData / 1000000) + " megabytes")

    def getCoordinates(self):
        if self.xEnabled:
            self.width = self.xSamplesSb.value()
            self.xCoordinates = np.linspace(self.xMinSb.value(), self.xMaxSb.value(), self.width)
            self.feedback_Update.append("X axis width = " + str(self.width) + " samples")
        else:
            self.width = 1
            self.xCoordinates = np.zeros(1)
        if self.yEnabled:
            self.depth = self.ySamplesSb.value()
            self.yCoordinates = np.linspace(self.yMinSb.value(), self.yMaxSb.value(), self.depth)
            self.feedback_Update.append("Y axis depth = " + str(self.depth) + " samples")
        else:
            self.depth = 1
            self.yCoordinates = np.zeros(1)
        if self.zEnabled:
            self.height = self.zSamplesSb.value()
            self.zCoordinates = np.linspace(self.zMinSb.value(), self.zMaxSb.value(), self.height)
            self.feedback_Update.append("Z axis height = " + str(self.height) + " samples")
        else:
            self.height = 1
            self.zCoordinates = np.zeros(1)

    # Jogging Actions
    def scan(self):
        self.getCoordinates()
        if self.width == 2 or self.height == 2 or self.depth == 2:
            self.feedback_Update.append("Scan dimensions with 2 samples are not supported")
            self.end_scan()
            return

        self.estimate_time()
        self.estimate_fileSize()

        # This will end the graphing loop in the pico_confirm_data function
        self.tabWidgetBox.set_jogging(False)
        self.scanning = True
        self.tabWidgetBox.disable_buttons()
        self.disable_buttons()

        Filename, ok = QInputDialog.getText(self, 'New scan', 'Enter file name for scan data:')

        self.feedback_Update.append("Creating output file: " + Filename + ".hdf5")
        try:
            self.f = h5py.File(Filename + ".hdf5", "a")
        except:
            print("unable to create file")
            self.end_scan()
            return
        # Creates subfolder within the file for scan data
        try:
            self.scanData = self.f.create_group("Scan")
        except:
            self.feedback_Update.append("file or HDF5 group already exists")

        self.feedback_Update.append("Beginning scan")

        #self.Galil.scan(self.scanSize, self.stepSize)

        #self.feedback_Update.append("Could not connect to the motor controller")

        self.intensity = np.zeros((self.width, self.depth, self.height))

        galil_x = 0
        galil_y = 0
        galil_z = 0

        scanStartTime = t.time()

        # Used for mfp demo, delete later
        #focusFlag = 0
        #self.tabWidgetBox.func.SetAmplitude("1", 0)

        average = np.array([])
        counter = 0
        for x in range(self.width):
            for y in range(self.depth):
                for z in range(self.height):
                    if not self.scanning:
                        try:
                            self.f.close()
                        finally:
                            self.end_scan()
                            return


                    #distanceFromCenter = (((self.width-1) / 2 - x) ** 2 + ((self.depth-1) / 2 - y) ** 2 + ((self.height-1) / 2 - z) ** 2) ** 0.5

                    #try:
                    #    if distanceFromCenter > 3 and not focusFlag == 0:
                    #        self.tabWidgetBox.func.SetAmplitude("1", 0)
                    #        focusFlag = 0
                    #    elif 3 >= distanceFromCenter > 2 and not focusFlag == 1:
                    #        self.tabWidgetBox.func.SetAmplitude("1", 1)
                    #        focusFlag = 1
                    #    elif distanceFromCenter <= 2 and not focusFlag == 2:
                    #        self.tabWidgetBox.func.SetAmplitude("1", 5)
                    #        focusFlag = 2
                    #except:
                    #    self.feedback_Update.append("Error setting function generator")


                    position_index = str(x) + "," + str(y) + "," + str(z)

                    try:
                        galil_x = self.xCoordinates[x] * self.config["galil_mmConversion"]
                        galil_y = self.yCoordinates[y] * self.config["galil_mmConversion"]
                        galil_z = self.zCoordinates[z] * self.config["galil_mmConversion"]

                        # For testing, remove later
                        print("Motor coordinates:" + str(galil_x) + "," + str(galil_y) + "," + str(galil_z))

                        # move robot to galil_x, galil_y, galil_z and wait for it to stop

                        self.Galil.handle.GCommand('PA {0},{1},{2}'.format(galil_x, galil_y, galil_z))
                        self.Galil.handle.GCommand('BG ABC')
                        self.Galil.get_position()

                        while self.Galil.isMoving():
                            t.sleep(0.05)
                    except:
                        self.feedback_Update.append("Error moving motors")
                        if self.config["end_scan_on_errors"]:
                            try:
                                self.f.close()
                            finally:
                                self.end_scan()
                                return



                    try:
                        print("Scanning position:" + position_index)
                        self.pico.block()
                        average = np.mean(self.pico.data_mVRay, axis=0)
                        self.tabWidgetBox.plotWidget.plot(self.pico.time, average, clear=True)
                        pg.QtGui.QApplication.processEvents()
                    except:
                        self.feedback_Update.append("Error collecting data from picoscope")
                        if self.config["end_scan_on_errors"]:
                            try:
                                self.f.close()
                            finally:
                                self.end_scan()
                                return
                    try:
                        self.scanData.create_dataset(name=position_index, data=average)
                    except:
                        self.feedback_Update.append("Error writing data, the selected file may already exist")
                        if self.config["end_scan_on_errors"]:
                            try:
                                self.f.close()
                            finally:
                                self.end_scan()
                                return
                    try:
                        self.intensity.itemset((x, y, z), average.max())
                    except ValueError:
                        self.feedback_Update.append("Empty waveform detected at position: " + position_index)
                        self.intensity.itemset((x, y, z), 0)

                    if self.xEnabled and self.yEnabled and not self.zEnabled:
                        arr = np.transpose(self.intensity, (2, 0, 1))
                        self.tabWidgetBox.intensityMap.setImage(arr[:][:][0])
                        self.tabWidgetBox.imagePlot.setLabel(axis='bottom', text='x-axis (forward/backward)')
                        self.tabWidgetBox.imagePlot.setLabel(axis='left', text='y-axis (left/right)')
                    elif self.xEnabled and self.zEnabled and not self.yEnabled:
                        arr = np.transpose(self.intensity, (1, 0, 2))
                        self.tabWidgetBox.intensityMap.setImage(arr[:][:][0])
                        self.tabWidgetBox.imagePlot.setLabel(axis='bottom', text='x-axis (forward/backward)')
                        self.tabWidgetBox.imagePlot.setLabel(axis='left', text='z-axis (up/down)')
                    elif self.yEnabled and self.zEnabled and not self.xEnabled:
                        arr = self.intensity
                        self.tabWidgetBox.intensityMap.setImage(arr[:][:][0])
                        self.tabWidgetBox.imagePlot.setLabel(axis='bottom', text='y-axis (left/right)')
                        self.tabWidgetBox.imagePlot.setLabel(axis='left', text='z-axis (up/down)')
                    else:
                        self.tabWidgetBox.intensityMap.setImage(self.intensity[:][:][:])
                        self.tabWidgetBox.imagePlot.setLabel(axis='bottom', text='y-axis (left/right)')
                        self.tabWidgetBox.imagePlot.setLabel(axis='left', text='z-axis (up/down)')

                    pg.QtGui.QApplication.processEvents()
                    # iv.show()
                    # plots the average across waveforms of captured data from the picoscope

        try:
            self.scanData.create_dataset(name="Intensity map", data=self.intensity)
            self.f.close()
        except:
            self.feedback_Update.append("Error closing file")
        self.end_scan()

        print("Scan time = " + str(t.time() - scanStartTime))

    # The following functions disable/enable x, y, and z rows.
    def disable_xRow(self):
        self.xEnabled = False
        self.xMaxSb.setEnabled(False)
        self.xSamplesSb.setEnabled(False)
        self.xMinSb.setEnabled(False)

    def enable_xRow(self):
        self.xEnabled = True
        self.xMaxSb.setEnabled(True)
        self.xSamplesSb.setEnabled(True)
        self.xMinSb.setEnabled(True)

    def disable_yRow(self):
        self.yEnabled = False
        self.yMaxSb.setEnabled(False)
        self.ySamplesSb.setEnabled(False)
        self.yMinSb.setEnabled(False)

    def enable_yRow(self):
        self.yEnabled = True
        self.yMaxSb.setEnabled(True)
        self.ySamplesSb.setEnabled(True)
        self.yMinSb.setEnabled(True)

    def disable_zRow(self):
        self.zEnabled = False
        self.zMaxSb.setEnabled(False)
        self.zSamplesSb.setEnabled(False)
        self.zMinSb.setEnabled(False)

    def enable_zRow(self):
        self.zEnabled = True
        self.zMaxSb.setEnabled(True)
        self.zSamplesSb.setEnabled(True)
        self.zMinSb.setEnabled(True)

    # checkBox_state is in charge of determing which checkboxes are checked
    def checkBox_state(self):
        if self.xCheckBox.isChecked():
            self.enable_xRow()
        else:
            self.disable_xRow()
        if self.yCheckBox.isChecked():
            self.enable_yRow()
        else:
            self.disable_yRow()
        if self.zCheckBox.isChecked():
            self.enable_zRow()
        else:
            self.disable_zRow()

    def disable_buttons(self):
        self.keyboardCombo.setEnabled(False)
        self.xDownBtn.setEnabled(False)
        self.xMaxSb.setEnabled(False)
        self.xMinSb.setEnabled(False)
        self.xUpBtn.setEnabled(False)
        self.Scan.setEnabled(False)
        self.setHomeBtn.setEnabled(False)
        self.speedCombo.setEnabled(False)
        self.saveNotesBtn.setEnabled(False)
        self.yLoadSb.setEnabled(False)
        self.ySamplesSb.setEnabled(False)
        self.yMaxSb.setEnabled(False)
        self.xSamplesSb.setEnabled(False)
        self.zSamplesSb.setEnabled(False)
        self.xLoadSb.setEnabled(False)
        self.zDownBtn.setEnabled(False)
        self.yDownBtn.setEnabled(False)
        self.goHomeBtn.setEnabled(False)
        self.yMinSb.setEnabled(False)
        self.yUpBtn.setEnabled(False)
        self.zMinSb.setEnabled(False)
        self.zMaxSb.setEnabled(False)
        self.zUpBtn.setEnabled(False)
        self.zLoadSb.setEnabled(False)
        self.xCheckBox.setEnabled(False)
        self.yCheckBox.setEnabled(False)
        self.zCheckBox.setEnabled(False)

    def enable_buttons(self):
        self.keyboardCombo.setEnabled(True)
        self.xDownBtn.setEnabled(True)
        self.xMaxSb.setEnabled(True)
        self.xMinSb.setEnabled(True)
        self.xUpBtn.setEnabled(True)
        self.Scan.setEnabled(True)
        self.setHomeBtn.setEnabled(True)
        self.speedCombo.setEnabled(True)
        self.saveNotesBtn.setEnabled(True)
        self.yLoadSb.setEnabled(True)
        self.ySamplesSb.setEnabled(True)
        self.yMaxSb.setEnabled(True)
        self.xSamplesSb.setEnabled(True)
        self.zSamplesSb.setEnabled(True)
        self.xLoadSb.setEnabled(True)
        self.zDownBtn.setEnabled(True)
        self.yDownBtn.setEnabled(True)
        self.goHomeBtn.setEnabled(True)
        self.yMinSb.setEnabled(True)
        self.yUpBtn.setEnabled(True)
        self.zMinSb.setEnabled(True)
        self.zMaxSb.setEnabled(True)
        self.zUpBtn.setEnabled(True)
        self.zLoadSb.setEnabled(True)
        self.xCheckBox.setEnabled(True)
        self.yCheckBox.setEnabled(True)
        self.zCheckBox.setEnabled(True)
        self.checkBox_state()


    @Slot(int)
    def abort_button(self):
        self.scanning = False

    def go_home_button(self):
        self.Galil.handle.GCommand('PA 0,0,0')
        self.Galil.begin_motion('ABC')
        while self.Galil.isMoving():
            t.sleep(0.05)
        self.Galil.get_position()

    # Once the scanning variable is false, the end scan method will be triggered in the scan loop
    def end_scan(self):
        if self.f is not None:
            self.f.close()
        self.scanning = False
        self.feedback_Update.append("Ending scan")
        try:
            self.Galil.stop_motion()
        except:
            self.feedback_Update.append(
                "Could not connect to motor controller. If the robot is moving, turn the power switch off manually")
        self.enable_buttons()
        self.tabWidgetBox.enable_buttons()

        self.tabWidgetBox.set_jogging(True)

    def set_origin_pressed(self):
        try:
            self.Galil.set_origin()
            self.feedback_Update.append('Origin Defined')
        except gclib.GclibError as e:
            self.feedback_Update.append('Controller Error (set origin): {0}'.format(e))

    def X_Up(self):
        # Check if speed is negative, invert if true
        Progress = "X Up pressed"
        self.feedback_Update.append(str(Progress))
        if self.Galil.jogSpeed['x'] < 0:
            self.Galil.jogSpeed['x'] = self.Galil.jogSpeed['x'] * -1

        try:
            self.Galil.jog('x')
            self.Galil.begin_motion('A')
        except gclib.GclibError as e:
            self.feedback_Update.append("Controller Error (jog): {0}".format(e))
        print('jogging!')

    def X_Down(self):
        # Check is speed is positive, invert if true
        Progress = "X Down pressed"
        self.feedback_Update.append(str(Progress))
        if self.Galil.jogSpeed['x'] > 0:
            self.Galil.jogSpeed['x'] = -1 * self.Galil.jogSpeed['x']
        try:
            self.Galil.jog('x')
            self.Galil.begin_motion('A')
        except gclib.GclibError as e:
            self.feedback_Update.append("Controller Error (jog): {0}".format(e))
        print('jogging!')

    def Y_Up(self):

        # Check if Y speed is positive, invert if true
        Progress = "Y left pressed"
        self.feedback_Update.append(str(Progress))
        if self.Galil.jogSpeed['y'] > 0:
            self.Galil.jogSpeed['y'] = -1 * self.Galil.jogSpeed['y']
        try:
            self.Galil.jog('y')
            self.Galil.begin_motion('B')
        except gclib.GclibError as e:
            self.feedback_Update.append("Controller Error (jog): {0}".format(e))
        print('jogging!')

    def Y_Down(self):

        # Check if Y speed is negative, invert if true
        Progress = "Y right pressed"
        self.feedback_Update.append(str(Progress))
        if self.Galil.jogSpeed['y'] < 0:
            self.Galil.jogSpeed['y'] = -1 * self.Galil.jogSpeed['y']
        try:
            self.Galil.jog('y')
            self.Galil.begin_motion('B')
        except gclib.GclibError as e:
            self.feedback_Update.append("Controller Error (jog): {0}".format(e))
        print('jogging!')


    def Z_Up(self):
        # Check if Z speed is negative, invert if true
        Progress = "Z UP pressed"
        self.feedback_Update.append(str(Progress))
        if self.Galil.jogSpeed['z'] < 0:
            self.Galil.jogSpeed['z'] = -1 * self.Galil.jogSpeed['z']
        try:
            self.Galil.jog('z')
            self.Galil.begin_motion('C')
        except gclib.GclibError as e:
            self.feedback_Update.append("Controller Error (jog): {0}".format(e))
        print('jogging!')

    def Z_Down(self):
        # Check if Z speed is positive, invert if true
        Progress = "Z Down pressed"
        self.feedback_Update.append(str(Progress))
        if self.Galil.jogSpeed['z'] > 0:
            self.Galil.jogSpeed['z'] = -1 * self.Galil.jogSpeed['z']
        try:
            self.Galil.jog('z')
            self.Galil.begin_motion('C')
        except gclib.GclibError as e:
            self.feedback_Update.append("Controller Error (jog): {0}".format(e))
        print('jogging!')

    def stop_motion(self):
        try:
            self.Galil.stop_motion()
            print('stopping motion')
        except:
            pass

    # Open help document
    def Show_Help(self):
        webbrowser.open("Help.txt")

    # Initializing hardwares
    def initialize_FunctionGenerator(self):
        try:
            self.func = FunctionGenerator(frequency=self.config["siglent_frequencyHz"],
                                          amplitude=self.config["siglent_amplitudeV"],
                                          period=self.config["siglent_burstPeriodS"],
                                          cycles=self.config["siglent_cycles"],
                                          C1output=self.config["siglent_C1output"],
                                          C2output=self.config["siglent_C2output"])
        except:
            self.feedback_Update.append("Function generator failed to connect, make sure one is connected and restart")

    def initialize_Picoscope(self):

        try:
            self.pico = Picoscope()
            self.pico.setup(range_mV=self.config["picoscope_rangemV"], blocks=self.config["picoscope_blocks"],
                            timebase=self.config["picoscope_timebase"],
                            external=self.config["picoscope_externalTrigger"],
                            triggermV=self.config["picoscope_triggermV"],
                            delay=self.config["picoscope_delay"],
                            preSamples=self.config["picoscope_preSamples"],
                            postSamples=self.config["picoscope_postSamples"])
        except:
            self.feedback_Update.append(
                "Oscilliscope failed to connect, make sure it is connected to a USB 3 port and restart")

    # Adding a warning when close button is pressed
    def closeEvent(self, event):
        bQuit = False
        qReply = QMessageBox.question(
            self,
            'Confirm Exit',
            'Do you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if qReply == QMessageBox.Yes:
            bQuit = True

        if bQuit:
            self.Galil.clean_up()
            event.accept()
            print("Galil Disconnected")
        else:
            event.ignore()


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
        self.grabKeyboard()
        self.setFocus()
        event_value = self.keyevent_to_string(event)
       # print(event_value)
       # print(f"keyboard update is {self.tabWidgetBox.Keyboard_Update}")
        if self.tabWidgetBox.Keyboard_Update == True:
            if event_value == "Control+Up" :
                self.grabKeyboard()
                self.setFocus()
                if self.Galil.jogSpeed['x'] < 0:
                    self.Galil.jogSpeed['x'] = self.Galil.jogSpeed['x'] * -1
                try:
                    self.Galil.jog('x')
                    self.Galil.begin_motion('A')
                except gclib.GclibError as e:
                    self.feedback_Update.append("Controller Error (jog): {0}".format(e))
                print('jogging!')

            elif event_value == "Control+Down" :
                if self.Galil.jogSpeed['x'] > 0:
                    self.Galil.jogSpeed['x'] = -1 * self.Galil.jogSpeed['x']
                try:
                    self.Galil.jog('x')
                    self.Galil.begin_motion('A')
                except gclib.GclibError as e:
                    self.feedback_Update.append("Controller Error (jog): {0}".format(e))

            elif event_value == "Control+Right" :

                if self.Galil.jogSpeed['y'] < 0:
                    self.Galil.jogSpeed['y'] = -1 * self.Galil.jogSpeed['y']
                try:
                    self.Galil.jog('y')
                    self.Galil.begin_motion('B')
                except gclib.GclibError as e:
                    self.feedback_Update.append("Controller Error (jog): {0}".format(e))
                print('jogging!')


            elif event_value == "Control+Left" :

                if self.Galil.jogSpeed['y'] > 0:
                    self.Galil.jogSpeed['y'] = -1 * self.Galil.jogSpeed['y']
                try:
                    self.Galil.jog('y')
                    self.Galil.begin_motion('B')
                except gclib.GclibError as e:
                    self.feedback_Update.append("Controller Error (jog): {0}".format(e))
                print('jogging!')

            elif event_value == "Control+PageUp"  :
                if self.Galil.jogSpeed['z'] < 0:
                    self.Galil.jogSpeed['z'] = -1 * self.Galil.jogSpeed['z']
                try:
                    self.Galil.jog('z')
                    self.Galil.begin_motion('C')
                except gclib.GclibError as e:
                    self.feedback_Update.append("Controller Error (jog): {0}".format(e))
                print('jogging!')

            elif event_value == "Control+PageDown"  :
                if self.Galil.jogSpeed['z'] > 0:
                    self.Galil.jogSpeed['z'] = -1 * self.Galil.jogSpeed['z']
                try:
                    self.Galil.jog('z')
                    self.Galil.begin_motion('C')
                except gclib.GclibError as e:
                    self.feedback_Update.append("Controller Error (jog): {0}".format(e))
                print('jogging!')
            else:
                self.releaseKeyboard()
        else:
            self.releaseKeyboard()

    def keyReleaseEvent(self, event):
        event_value = self.keyevent_to_string(event)

        if event_value == "Control+Up" or event_value == "Control+Down" or event_value == "Control+Right" or event_value == "Control+Left" or event_value == "Control+Minus" or event_value == "Control+Equal" or event_value == "Control":

            try:
                self.Galil.stop_motion()
            except:
                pass

        if not event.isAutoRepeat() and self.tabWidgetBox.Keyboard_Update == True:
            self.releaseKeyboard()
            try:
                self.stop_motion()
            except:
                pass
        elif not event.isAutoRepeat() and self.tabWidgetBox.Keyboard_Update == False:
            Progress = "Keyboard jogging is disabled"
            self.feedback_Update.append(str(Progress))
            self.releaseKeyboard()
            # self.Galil.stop_motion()
            try:
                self.stop_motion()
            except:
                pass




# Tab Widget in its own Class
class tabWidget(QWidget):

    def __init__(self, parent, parameters, picoscope, Keyboard_feedback, siglent, feedback, galil=None):
        self.feedback_Update = feedback
        self.Keyboard_Update = Keyboard_feedback
        self.screen_resolution = None
        self.pgOffset = {}  # empty dictionary
        self.jogging = False
        self.scanning = False


        if galil is not None:
            self.Galil = galil
        else:
            print('no galil object passed to tab widget')

        if self.screen_resolution is not None:
            if self.screen_resolution.width() > 1920:  # 4K resolution
                self.left = 100
                self.top = 100
                self.screen_width = 3000
                self.screen_height = 1000
                self.pgHoffset = 105
                self.pgWoffset = 125
        else:  # full HD
            self.left = 50
            self.top = 50
            self.screen_width = 1500
            self.screen_height = 750
            self.pgHoffset = 55
            self.pgWoffset = 75

        self.pico = picoscope
        self.func = siglent

        super().__init__()
        # self.Galil = Galil()

        self.config = parameters  # this is the dictionary of parameters from the .yaml files
        self.gridTab1 = QGridLayout()  # Layout for Pico Tab
        self.gridTab2 = QGridLayout()  # Layout for Function Gen Tab
        self.gridTab3 = QGridLayout()  # Layout for Motors Tab
        self.mainVbox = QVBoxLayout()
        formLayout = QFormLayout()

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        vbox = QVBoxLayout()
        vbox2 = QVBoxLayout()

        self.graphTabs = QTabWidget()
        self.graphTab1 = QWidget()
        self.graphTab2 = QWidget()

        # Add tabs
        self.tabs.addTab(self.tab1, "Oscilloscope")
        self.tabs.addTab(self.tab2, "Function Generator")
        self.tabs.addTab(self.tab3, "Motors")

        # plotWidget = pg.PlotWidget()
        # vbox.addWidget(plotWidget)
        # self.graphTab1.setLayout(vbox)

        # self.plotWidget = pg.PlotWidget()
        self.plotWidget = self.createPlotWidget()

        vbox.addWidget(self.plotWidget)
        self.graphTab1.setLayout(vbox)

        self.imagePlot = pg.PlotItem()
        self.intensityMap = pg.ImageView(view = self.imagePlot)

        vbox2.addWidget(self.intensityMap)
        self.graphTab2.setLayout(vbox2)

        self.graphTabs.addTab(self.graphTab1, 'Real Time')
        self.graphTabs.addTab(self.graphTab2, 'Pressure Map')

        # Pico Tab - Labels
        self.resolutionLabel = QLabel()
        self.rangeLabel = QLabel()
        self.intervalLabel = QLabel()
        self.triggerLabel = QLabel()
        self.thresholdLabel = QLabel()
        self.delayLabel = QLabel()
        self.preTriggerLabel = QLabel()
        self.postTriggerLabel = QLabel()
        self.waveformsLabel = QLabel()

        self.resolutionLabel.setText('Resolution (bits)')
        self.rangeLabel.setText('ADC Range (mV)')
        self.intervalLabel.setText('Sample Interval (ns)')
        self.triggerLabel.setText('Trigger')
        self.thresholdLabel.setText('Trigger Threshold (mV)')
        self.delayLabel.setText('Trigger delay (samples)')
        self.preTriggerLabel.setText('Pre Trigger Samples')
        self.postTriggerLabel.setText('Post Trigger Samples')
        self.waveformsLabel.setText('Number of waveforms to average')

        self.resolutionLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.rangeLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.intervalLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.triggerLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.thresholdLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.preTriggerLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.postTriggerLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Pico Tab - Widgets
        self.resolutionCombo = QComboBox(self)
        self.resolutionCombo.addItems(['12', '14', '15', '16'])
        self.resolutionCombo.setCurrentText(str(self.config["picoscope_resolutionBits"]))

        self.rangeCombo = QComboBox(self)
        self.rangeCombo.addItems(['10', '20', '50', '100', '200',
                                  '500', '1000', '2000', '5000', '10000', '20000'])
        self.rangeCombo.setCurrentText(str(self.config["picoscope_rangemV"]))

        self.intervalCombo = QComboBox(self)
        self.intervalCombo.addItems(['4', '8', '16', '32', '48', '64', '80', '96', '112', '128', '144'])
        self.intervalCombo.setCurrentText('144') #str(2 ** (self.config["picoscope_timebase"]))

        self.triggerCombo = QComboBox(self)
        self.triggerCombo.addItems(['Self-trigger', 'External'])

        if self.config["picoscope_externalTrigger"] == False or self.config["picoscope_externalTrigger"] == 0:
            self.triggerCombo.setCurrentText('Self-trigger')
        else:
            self.triggerCombo.setCurrentText('External')

        self.thresholdSpinBox = QSpinBox()
        self.thresholdSpinBox.setMinimum(0)
        self.thresholdSpinBox.setMaximum(self.config["picoscope_triggermVMax"])
        self.thresholdSpinBox.setValue(self.config["picoscope_triggermV"])

        self.preTriggerSamplesSpinBox = QSpinBox()
        self.preTriggerSamplesSpinBox.setMinimum(0)
        self.preTriggerSamplesSpinBox.setMaximum(self.config["picoscope_samplesMax"])
        self.preTriggerSamplesSpinBox.setMaximum(self.config["picoscope_samplesMax"])
        self.preTriggerSamplesSpinBox.setValue(self.config["picoscope_preSamples"])

        self.delaySpinBox = QSpinBox()
        self.delaySpinBox.setMinimum(0)
        self.delaySpinBox.setMaximum(self.config["picoscope_delayMax"])
        self.delaySpinBox.setValue(self.config["picoscope_delay"])

        self.postTriggerSamplesSpinBox = QSpinBox()
        self.postTriggerSamplesSpinBox.setMinimum(0)
        self.postTriggerSamplesSpinBox.setMaximum(self.config["picoscope_samplesMax"])
        self.postTriggerSamplesSpinBox.setValue(self.config["picoscope_postSamples"])

        self.waveformsSpinBox = QSpinBox()
        self.waveformsSpinBox.setMinimum(0)
        self.waveformsSpinBox.setMaximum(self.config["picoscope_blocksMax"])
        self.waveformsSpinBox.setValue(self.config["picoscope_blocks"])

        self.picoConfirmBtn = QPushButton('Confirm Settings')
        self.picoConfirmBtn.pressed.connect(self.pico_confirm_data)  # Press to activate function

        self.picoOnOffBtn = QPushButton('Turn on capture')

        self.picoOnOffBtn.setCheckable(True)
        self.picoOnOffBtn.setStyleSheet("background-color : white")
        self.picoOnOffBtn.pressed.connect(self.pico_toggle_capture)  # Press to activate function

        # Setting the layout to be grid
        self.tab1.setLayout(self.gridTab1)

        # Adding to the tabs
        self.gridTab1.addWidget(self.resolutionLabel, 0, 0)
        self.gridTab1.addWidget(self.rangeLabel, 1, 0)
        self.gridTab1.addWidget(self.intervalLabel, 2, 0)
        self.gridTab1.addWidget(self.triggerLabel, 3, 0)
        self.gridTab1.addWidget(self.thresholdLabel, 4, 0)
        self.gridTab1.addWidget(self.delayLabel, 5, 0)
        self.gridTab1.addWidget(self.preTriggerLabel, 6, 0)
        self.gridTab1.addWidget(self.postTriggerLabel, 7, 0)
        self.gridTab1.addWidget(self.waveformsLabel, 8, 0)

        self.gridTab1.addWidget(self.resolutionCombo, 0, 1)
        self.gridTab1.addWidget(self.rangeCombo, 1, 1)
        self.gridTab1.addWidget(self.intervalCombo, 2, 1)
        self.gridTab1.addWidget(self.triggerCombo, 3, 1)
        self.gridTab1.addWidget(self.thresholdSpinBox, 4, 1)
        self.gridTab1.addWidget(self.delaySpinBox, 5, 1)
        self.gridTab1.addWidget(self.preTriggerSamplesSpinBox, 6, 1)
        self.gridTab1.addWidget(self.postTriggerSamplesSpinBox, 7, 1)
        self.gridTab1.addWidget(self.waveformsSpinBox, 8, 1)
        self.gridTab1.addWidget(self.picoOnOffBtn, 9, 0)
        self.gridTab1.addWidget(self.picoConfirmBtn, 9, 1)

        # FUNCTION GENERATOR TAB (TAB 2)
        self.tab2.setLayout(self.gridTab2)

        # Func Gen Tab - Widgets
        self.freqLabel = QLabel()
        self.amplitudeLabel = QLabel()
        self.periodLabel = QLabel()
        self.cyclesLabel = QLabel()
        self.outputLabel = QLabel()

        self.freqLabel.setText('Frequency (MHz)')
        self.amplitudeLabel.setText('Amplitude (mV)')
        self.periodLabel.setText('period (microseconds)')
        self.cyclesLabel.setText('Cycles per burst')
        self.outputLabel.setText('Output')

        self.freqLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.amplitudeLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.periodLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.cyclesLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.outputLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.freqSpinBox = QDoubleSpinBox()
        self.freqSpinBox.setMinimum(0)
        self.freqSpinBox.setMaximum(float(self.config["siglent_frequencyHzMax"]) / 1000000)
        self.freqSpinBox.setValue(float(self.config["siglent_frequencyHz"]) / 1000000)
        self.freqSpinBox.setSingleStep(0.1)
        self.amplitudeSpinBox = QSpinBox()
        self.amplitudeSpinBox.setMinimum(0)
        self.amplitudeSpinBox.setMaximum(float(self.config["siglent_amplitudeVMax"]) * 1000)
        self.amplitudeSpinBox.setValue(float(self.config["siglent_amplitudeV"]) * 1000)
        self.periodSpinBox = QSpinBox()
        self.periodSpinBox.setMinimum(0)
        self.periodSpinBox.setMaximum(float(self.config["siglent_burstPeriodSMax"]) * 1000000)
        self.periodSpinBox.setValue(float(self.config["siglent_burstPeriodS"]) * 1000000)
        self.cyclesSpinBox = QSpinBox()
        self.cyclesSpinBox.setMinimum(0)
        self.cyclesSpinBox.setMaximum(float(self.config["siglent_cyclesMax"]))
        self.cyclesSpinBox.setValue(float(self.config["siglent_cycles"]))

        self.outputCombo = QComboBox(self)
        self.outputCombo.addItems(['ON', 'OFF'])

        self.functionC1ConfirmBtn = QPushButton('Set channel 1 Settings')
        self.functionC1ConfirmBtn.pressed.connect(self.func_C1_confirm_data)

        self.functionC2ConfirmBtn = QPushButton('Set channel 2 Settings')
        self.functionC2ConfirmBtn.pressed.connect(self.func_C2_confirm_data)

        self.C1_OnOffBtn = QPushButton('Channel 1 on')
        self.C1_OnOffBtn.setCheckable(True)
        self.C1_OnOffBtn.setStyleSheet("background-color : white")
        self.C1_OnOffBtn.pressed.connect(self.func_C1_toggle)

        self.C2_OnOffBtn = QPushButton('Channel 2 on')
        self.C2_OnOffBtn.setCheckable(True)
        self.C2_OnOffBtn.setStyleSheet("background-color : white")
        self.C2_OnOffBtn.pressed.connect(self.func_C2_toggle)

        # Func Gen Tab - Layout
        self.gridTab2.addWidget(self.freqLabel, 0, 0)
        self.gridTab2.addWidget(self.amplitudeLabel, 1, 0)
        self.gridTab2.addWidget(self.periodLabel, 2, 0)
        self.gridTab2.addWidget(self.cyclesLabel, 3, 0)
        self.gridTab2.addWidget(self.outputLabel, 4, 0)
        self.gridTab2.addWidget(self.freqSpinBox, 0, 1)
        self.gridTab2.addWidget(self.amplitudeSpinBox, 1, 1)
        self.gridTab2.addWidget(self.periodSpinBox, 2, 1)
        self.gridTab2.addWidget(self.cyclesSpinBox, 3, 1)
        self.gridTab2.addWidget(self.outputCombo, 4, 1)
        self.gridTab2.addWidget(self.functionC1ConfirmBtn, 5, 0)
        self.gridTab2.addWidget(self.functionC2ConfirmBtn, 5, 1)
        self.gridTab2.addWidget(self.C1_OnOffBtn, 6, 0)
        self.gridTab2.addWidget(self.C2_OnOffBtn, 6, 1)

        # MOTORS TAB
        self.tab3.setLayout(self.gridTab3)  # Setting the Layout for the widgets

        # Motors Tab - Widgets
        self.keyboardLabel = QLabel()
        self.speedLabel = QLabel()

        self.keyboardLabel.setText('Keyboard Control')
        self.speedLabel.setText('Jog Speed')

        self.keyboardLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.speedLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.speedCombo = QComboBox()
        self.speedCombo.addItems(['5 mm/s', '10 mm/s', '15 mm/s', '20 mm/s'])
        self.speedCombo.activated.connect(self.jog_speed_chosen)
        self.speedCombo.setCurrentIndex(2) # Sets the current index to 15 mm/s
        self.motorConnectionBool = False

        self.keyboardCombo = QComboBox()
        self.keyboardCombo.addItems(['OFF', 'ON'])
        self.keyboardCombo.setFocusPolicy(QtCore.Qt.NoFocus)

        self.keyboardCombo.activated[str].connect(self.confirm_Change)


        #text = str(self.speedCombo.currentText())
        #if text == "ON":
        #    print("Keyboard is on")

        self.connectBtn = QPushButton('Toggle Connection')
        self.connectBtn.setStyleSheet("background-color : white")
        self.connectBtn.pressed.connect(self.toggle_connection)

        # Removing for now as it is redundant
        # self.scanSpinBox = QSpinBox()
        # self.scanSpinBox.valueChanged.connect(self.scanSize_changed)

        # self.stepSpinBox = QSpinBox()
        # self.stepSpinBox.valueChanged.connect(self.stepSize_changed)


        # Motors Tab - Layout
        self.gridTab3.addWidget(self.connectBtn, 0, 0, 1, 2)
        # self.gridTab3.addWidget(self.disconnectBtn, 1, 0, 1, 2)
        self.gridTab3.addWidget(self.keyboardCombo, 2, 1)
        self.gridTab3.addWidget(self.speedCombo, 3, 1)



        self.gridTab3.addWidget(self.keyboardLabel, 2, 0)
        self.gridTab3.addWidget(self.speedLabel, 3, 0)

        # Add ALL tabs to widget
        self.mainVbox.addWidget(self.tabs)
        self.mainVbox.addWidget(self.graphTabs)

        self.setLayout(self.mainVbox)


    # This boolean variable can be set to false to stop the jogging loop
    def set_jogging(self, jog):
        self.jogging = jog

    def jog_speed_chosen(self):

        # Checks the current index to determine the speed
        if self.speedCombo.currentIndex() == 0:
            print('SELECTED MEDIUM')
            print(self.speedCombo.currentIndex())
            self.feedback_Update.append('Jog Speed set to 5 mm/s')
            self.Galil.jogSpeed['x'] = 5 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['y'] = 5 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['x'] = 5 * self.config["galil_mmConversion"]
        elif self.speedCombo.currentIndex() == 1:
            print('SELECTED HIGH')
            self.feedback_Update.append('Jog Speed set to 10 mm/s')
            self.Galil.jogSpeed['x'] = 10 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['y'] = 10 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['x'] = 10 * self.config["galil_mmConversion"]
        elif self.speedCombo.currentIndex() == 2:
            self.feedback_Update.append('Jog Speed set to 15 mm/s')
            self.Galil.jogSpeed['x'] = 15 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['y'] = 15 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['x'] = 15 * self.config["galil_mmConversion"]
        else:
            print('SELECTED LOW')
            self.feedback_Update.append('Jog Speed set to 20 mm/s')
            self.Galil.jogSpeed['x'] = 20 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['y'] = 20 * self.config["galil_mmConversion"]
            self.Galil.jogSpeed['x'] = 20 * self.config["galil_mmConversion"]

    def pico_confirm_data(self):
        self.jogging = False

        try:
            self.pico.close()
        except:
            pass

        try:
            self.pico.setup(range_mV=int(self.rangeCombo.currentText()), blocks=self.waveformsSpinBox.value(),
                            timebase=self.intervalCombo.currentIndex() + 2, external=self.triggerCombo.currentIndex(),
                            triggermV=self.thresholdSpinBox.value(), delay=self.delaySpinBox.value(),
                            preSamples=self.preTriggerSamplesSpinBox.value(),
                            postSamples=self.postTriggerSamplesSpinBox.value())
        except AttributeError:
            self.feedback_Update.append("Picoscope not connected. Try plugging it in and restarting the application")

        self.feedback_Update.append("Picoscope capture time = " + str(self.pico.getRuntime()) + " ns")
        self.picoOnOffBtn.setChecked(False)
        self.picoOnOffBtn.setText("Turn on capture")
        self.picoOnOffBtn.setStyleSheet("background-color : white")

        while self.jogging:
            self.displayData()

    def func_C1_toggle(self):
        # if button is checked
        if self.C1_OnOffBtn.isChecked():
            try:
                self.func.SetOutput("1", "Off")
                self.C1_OnOffBtn.setText("Turn channel 1 on")
                self.C1_OnOffBtn.setStyleSheet("background-color : white")
            except:
                pass
        # if it is unchecked
        else:
            try:
                self.func.SetOutput("1", "On")
                self.C1_OnOffBtn.setText("Turn channel 1 off")
                self.C1_OnOffBtn.setStyleSheet("background-color : red")
            except:
                pass

    def func_C2_toggle(self):
        # if button is checked
        if self.C2_OnOffBtn.isChecked():
            try:
                self.func.SetOutput("2", "Off")
                self.C2_OnOffBtn.setText("Turn channel 2 on")
                self.C2_OnOffBtn.setStyleSheet("background-color : white")
            except:
                pass
        # if it is unchecked
        else:
            try:
                self.func.SetOutput("2", "On")
                self.C2_OnOffBtn.setText("Turn channel 2 off")
                self.C2_OnOffBtn.setStyleSheet("background-color : red")
            except:
                pass

    def pico_toggle_capture(self):
        # if button is checked
        if self.picoOnOffBtn.isChecked():
            self.picoOnOffBtn.setText("Turn on capture")
            self.picoOnOffBtn.setStyleSheet("background-color : white")
            self.jogging = False
            return

        # if it is unchecked
        else:
            self.picoOnOffBtn.setText("Turn off capture")
            self.picoOnOffBtn.setStyleSheet("background-color : red")
            try:
                self.pico.block()
                average = np.mean(self.pico.data_mVRay, axis=0)
                self.feedback_Update.append("Standard deviation of signal (mV) = " + str(np.std(average)))
                self.plotWidget.plot(self.pico.time, average, clear=True)
                pg.QtGui.QApplication.processEvents()

                self.jogging = True
                startTime = t.time()
                for i in range(10):
                    if self.jogging == False:
                        return
                    self.displayData()

                self.feedback_Update.append("10 Plots displayed in " + str(t.time() - startTime) + " seconds. Display frequency is " + str(
                    10 / (t.time() - startTime)) + "Hz")

                while self.jogging:
                    self.displayData()
            except:
                self.feedback_Update.append("Error occurred during realtime plotting")


    def displayData(self):
        self.pico.block()
        average = np.mean(self.pico.data_mVRay, axis=0)
        self.plotWidget.plot(self.pico.time, average, clear=True)
        pg.QtGui.QApplication.processEvents()

    def func_C1_confirm_data(self):
        self.func.setup(channel = "1", frequency=str(int(self.freqSpinBox.value() * 1000000)),
                                      amplitude=str(self.amplitudeSpinBox.value() / 1000),
                                      period=str(self.periodSpinBox.value() / 1000000),
                                      cycles=str(self.cyclesSpinBox.value()),
                                      output=self.outputCombo.currentText())

    def func_C2_confirm_data(self):
        self.func.setup(channel = "2", frequency=str(int(self.freqSpinBox.value() * 1000000)),
                                      amplitude=str(self.amplitudeSpinBox.value() / 1000),
                                      period=str(self.periodSpinBox.value() / 1000000),
                                      cycles=str(self.cyclesSpinBox.value()),
                                      output = self.outputCombo.currentText())

    def disable_buttons(self):
        self.delaySpinBox.setEnabled(False)
        self.postTriggerSamplesSpinBox.setEnabled(False)
        self.preTriggerSamplesSpinBox.setEnabled(False)
        self.thresholdSpinBox.setEnabled(False)
        self.triggerCombo.setEnabled(False)
        self.intervalCombo.setEnabled(False)
        self.waveformsSpinBox.setEnabled(False)
        self.rangeCombo.setEnabled(False)
        self.picoConfirmBtn.setEnabled(False)
        self.resolutionCombo.setEnabled(False)
        self.amplitudeSpinBox.setEnabled(False)
        self.cyclesSpinBox.setEnabled(False)
        self.connectBtn.setEnabled(False)
        self.C2_OnOffBtn.setEnabled(False)
        self.picoOnOffBtn.setEnabled(False)
        self.C1_OnOffBtn.setEnabled(False)
        self.freqSpinBox.setEnabled(False)
        self.periodSpinBox.setEnabled(False)

    def enable_buttons(self):
        self.delaySpinBox.setEnabled(True)
        self.postTriggerSamplesSpinBox.setEnabled(True)
        self.preTriggerSamplesSpinBox.setEnabled(True)
        self.thresholdSpinBox.setEnabled(True)
        self.triggerCombo.setEnabled(True)
        self.intervalCombo.setEnabled(True)
        self.waveformsSpinBox.setEnabled(True)
        self.rangeCombo.setEnabled(True)
        self.picoConfirmBtn.setEnabled(True)
        self.resolutionCombo.setEnabled(True)
        self.amplitudeSpinBox.setEnabled(True)
        self.cyclesSpinBox.setEnabled(True)
        self.connectBtn.setEnabled(True)
        self.freqSpinBox.setEnabled(True)
        self.C2_OnOffBtn.setEnabled(True)
        self.picoOnOffBtn.setEnabled(True)
        self.C1_OnOffBtn.setEnabled(True)
        self.periodSpinBox.setEnabled(True)

    def confirm_Change(self,value):
        Keyboard_value = value
        if Keyboard_value == "ON":
            print(Keyboard_value)
            self.Keyboard_Update = True
            Progress = 'Keyboard jogging is enabled \n Press "Ctrl + arrow keys" to jog\n Press "Ctrl and + key" to move forward \n Press "Ctrl and - key" to move backward'
            self.feedback_Update.append(str(Progress))
        elif Keyboard_value == "OFF":
            print(Keyboard_value)
            self.Keyboard_Update = False
            Progress = "Keyboard jogging is disabled"
            self.feedback_Update.append(str(Progress))


    def motors_confirm_data(self):
        print("This function has not yet been developed")

    def toggle_connection(self):

        # try:
        #     self.Galil.has_handle()
        # except gclib.GclibError as e:
        #     self.feedback_Update.append(str(e))

        # if self.Galil.has_handle():
        #     message = "Terminating connection"
        #     self.feedback_Update.append(str(message))
        # else:
        #     message = "Attempting to establish connection to motor controller"
        #     self.feedback_Update.append(str(message))

        try:
            self.Galil.toggle_handle()
        except gclib.GclibError as e:
            self.feedback_Update.append(str("Controller Error (handle toggle): {0}".format(e)))

        if self.Galil.has_handle():
            self.feedback_Update.append("Controller is connected")
            self.connectBtn.setStyleSheet("background-color : red")
            self.motorConnectionBool = True
        else:
            self.feedback_Update.append("Controller is not connected")
            self.connectBtn.setStyleSheet("background-color : white")
            self.motorConnectionBool = False

    def createPlotWidget(self):
        plotWidget = pg.PlotWidget()
        color = self.palette().color(QPalette.Window)  # Get the default window background,
        plotWidget.setBackground(color)

        # plot data: x, y values
        # self.pen = pg.mkPen(color='#52988C', width=1, style=Qt.SolidLine, join=Qt.RoundJoin, cap=Qt.RoundCap)
        # self.pen = pg.mkPen(color='#52988C', width=1)
        # test the ability to add item to the view
        # bg1 = pg.BarGraphItem(x=time_ms, height=volt_mV, width=0.3, brush='r')
        # plotWidget.addItem(bg1)
        self._plot = plotWidget.plot()
        # Add Background color to white
        plotWidget.setBackground('#202227')
        # Add Title
        # plotWidget.setTitle("Your Title Here", color="b", size="15pt")
        # Add Axis Labels
        styles = {"color": "#EDEDED", "font-size": "10pt"}
        plotWidget.setLabel("left", "Voltage (mV)", **styles)
        plotWidget.setLabel("bottom", "Time (ns)", **styles)
        font = QFont()
        font.setPixelSize(30)
        plotWidget.getAxis("bottom").tickFont = font
        plotWidget.getAxis("bottom").setStyle(
            tickTextOffset=20, tickFont=QFont("Roman times", 10), autoExpandTextSpace=True)
        plotWidget.getAxis("bottom").setHeight(h=self.pgHoffset)
        # axBottom = plotWidget.getAxis('bottom')  # get x axis
        # xTicks = [1, 0.5]
        # axBottom.setTickSpacing(xTicks[0], xTicks[1])  # set x ticks (major and minor)
        plotWidget.getAxis("left").tickFont = font
        plotWidget.getAxis("left").setStyle(
            tickTextOffset=20, tickFont=QFont("Roman times", 10), autoExpandTextSpace=True)
        plotWidget.getAxis("left").setWidth(w=self.pgWoffset)
        # axLeft = plotWidget.getAxis('left')  # get y axis
        # yTicks = [10, 5]
        # axLeft.setTickSpacing(yTicks[0], yTicks[1])  # set y ticks (major and minor)
        # Add grid
        plotWidget.showGrid(x=True, y=True, alpha=0.3)
        # # Set Range
        #plotWidget.setXRange(0, 10, padding=0.05)
        #plotWidget.setYRange(-10.0, 10.0, padding=0.05)
        # Set log mode
        # plotWidget.setLogMode(False, True)
        # Disable auto range
        # plotWidget.disableAutoRange()
        this_plot_item = plotWidget.getPlotItem()
        this_plot_item.layout.setContentsMargins(20, 40, 40, 20)  # Left, Top, Right, Bottom
        return plotWidget

    def scanSize_changed(self, i):
        self.scanSize = i

        # test the ability to add item to the view
        # bg1 = pg.BarGraphItem(x=time_ms, height=volt_mV, width=0.3, brush='r')
        # plotWidget.addItem(bg1)

    def stepSize_changed(self, i):
        self.stepSize = i

    def set_origin_pressed(self):
        self.Galil.set_origin()
        print('origin set')



    #This is a legacy method, use the scan method in the MainWindow class instead
    def scan(self):
        MainWindow.disable_buttons()
        self.disable_buttons()
        try:
            print('Scan starting')
            self.Galil.scan(self.scanSize, self.stepSize)
        except:
            print("Galil not connected")

    def closeEvent(self, event):
        bQuit = False
        qReply = QMessageBox.question(
            self,
            'Confirm Exit',
            'Do you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if qReply == QMessageBox.Yes:
            bQuit = True

        if bQuit:
            self.Galil.clean_up()
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # Enable High DPI display with PySide2
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(QStyleFactory, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

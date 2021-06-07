import sys
import datetime
import logging
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

from PySide2.QtWidgets import QApplication, QComboBox, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QFrame, QLabel, QPushButton, QTableWidget, QTabWidget, QTextBrowser
from PySide2.QtCore import Qt, QSize, Signal, QObject, Signal
from PySide2.QtGui import QIcon

from api_scripts import profile_script, vm_script, area_script, timestamps_script

logger = logging.getLogger(__name__)

class XStream(QObject):
    _stdout = None
    _stderr = None

    messageWritten = Signal(str)

    def flush( self ):
        pass

    def fileno( self ):
        return -1

    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(msg)

    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

class onav_lite(QMainWindow):

    def __init__(self, parent=None):
        super(onav_lite, self).__init__(parent)
        self.setWindowTitle("Ocean Navigator Lite")

        self.datasetDict = { '01. GIOPS 10 day Forecast 3D - LatLon' : 'giops_day',
                            '05. CCG RIOPS Forecast Surface - LatLon' : 'riops_fc_2dll',
                            '06. RIOPS Forecast 3D - Polar Stereographic' : 'riops_fc_3dps'
                        }

        self.variableDict = {}

        self.timestampDict = []

        self.quantum = []

        # initialize app widgets
        self.initUI()
        #self.setFixedSize(640,410)
        self.setFixedSize(640,460)
        self.setStyleSheet('Background-Color: #ffffff')

        self.setWindowIcon(QIcon('onavlite.ico'))

        XStream.stdout().messageWritten.connect(self.consoleOutput.insertPlainText)

        # display app
        self.show()        

    def initUI(self):
        main = QWidget(self)
        mainLayout = QVBoxLayout(main)
        self.setCentralWidget(main)

        optionsFrame = QFrame(main)
        optionsLayout = QHBoxLayout(optionsFrame)
        optionsLFrame = QFrame(optionsFrame)
        optionsLLayout = QVBoxLayout(optionsLFrame)
        optionsRFrame = QFrame(optionsFrame)
        optionsRLayout = QVBoxLayout(optionsRFrame)
        optionsLayout.addWidget(optionsLFrame)
        optionsLayout.addWidget(optionsRFrame)

        bottomFrame = QFrame(main)
        bottomLayout = QVBoxLayout(bottomFrame)

        mainLayout.addWidget(optionsFrame)
        mainLayout.addWidget(bottomFrame)

        dataPanel = QWidget(optionsLFrame)
        dataPanel.setFixedWidth(270)
        dataPanelLayout = QVBoxLayout(dataPanel)
        dataPanelLayout.setContentsMargins(0,0,0,0)

        dataHeader = QLabel(dataPanel)
        dataHeader.setFixedWidth(270)
        dataHeader.setFixedHeight(20)
        dataHeader.setStyleSheet('background-color: #008cba; color : #ffffff;')
        dataHeader.setAlignment(Qt.AlignCenter)
        dataHeader.setText('Select Dataset')

        self.datasetCB = QComboBox(dataPanel)
        self.variableCB = QComboBox(dataPanel)
        self.datasetCB.addItems(self.datasetDict.keys())
        self.datasetCB.currentIndexChanged.connect(self.changeDataset)
        self.variableCB.addItems(self.variableDict.keys())

        dataPanelLayout.addWidget(dataHeader)
        dataPanelLayout.addWidget(self.datasetCB)
        dataPanelLayout.addWidget(self.variableCB)
        dataPanelLayout.addStretch()

        locationPanel = QFrame(optionsRFrame)
        locationPanelLayout = QVBoxLayout(locationPanel)
        locationPanelLayout.setContentsMargins(0,0,0,0)

        locationButtons = QWidget(locationPanel)
        locationButtonsLayout = QHBoxLayout(locationButtons)
        rowLabel = QLabel('Point Quanitity', locationButtons)
        addRowButton = QPushButton('+', locationButtons)
        addRowButton.setStyleSheet('background-color: #008cba; color : #ffffff;')
        addRowButton.setFixedSize(20,20)
        addRowButton.clicked.connect(lambda: self.addRows())
        subRowButton = QPushButton('-', locationButtons)
        subRowButton.setStyleSheet('background-color: #008cba; color : #ffffff;')
        subRowButton.setFixedSize(20,20)
        subRowButton.clicked.connect(lambda: self.removeRows())

        locationButtonsLayout.addWidget(rowLabel)
        locationButtonsLayout.addWidget(addRowButton)
        locationButtonsLayout.addWidget(subRowButton)
        locationButtonsLayout.addStretch()

        locationHeader = QLabel(locationPanel)
        locationHeader.setFixedWidth(270)
        locationHeader.setFixedHeight(20)
        locationHeader.setStyleSheet('background-color: #008cba; color : #ffffff;')
        locationHeader.setAlignment(Qt.AlignCenter)
        locationHeader.setText('Coordinates')

        self.latlonTable = QTableWidget(1,2,locationPanel)
        self.latlonTable.setFixedWidth(270)
        self.latlonTable.setHorizontalHeaderLabels(['Latitude', 'Longitude'])

        locationPanelLayout.addWidget(locationHeader)
        locationPanelLayout.addWidget(self.latlonTable)
        locationPanelLayout.addWidget(locationButtons)

        profileWidget = QWidget()
        profileWidgetLayout = QVBoxLayout(profileWidget)
        profileStartTimeLabel = QLabel('Start Time', profileWidget)
        self.profileStartTimeCB = QComboBox(profileWidget)

        profileWidgetLayout.addWidget(profileStartTimeLabel)
        profileWidgetLayout.addWidget(self.profileStartTimeCB)
        profileWidgetLayout.addStretch()

        vmWidget = QWidget()
        vmWidgetlayout = QVBoxLayout(vmWidget)
        vmStartTimeLabel = QLabel('Start Time', vmWidget)
        vmEndTimeLabel = QLabel('End Time', vmWidget)
        self.vmStartTimeCB = QComboBox(vmWidget)
        self.vmEndTimeCB = QComboBox(vmWidget)

        vmWidgetlayout.addWidget(vmStartTimeLabel)
        vmWidgetlayout.addWidget(self.vmStartTimeCB)
        vmWidgetlayout.addWidget(vmEndTimeLabel)
        vmWidgetlayout.addWidget(self.vmEndTimeCB)

        # lineWidget = QWidget()
        # lineWidgetLayout = QVBoxLayout(lineWidget)
        # lineCBLabel = QLabel('Data Type', lineWidget)
        # lineCB = QComboBox(lineWidget)
        # lineCB.addItems(['Transect', 'Hovmoller'])

        # lineWidgetLayout.addWidget(lineCBLabel)
        # lineWidgetLayout.addWidget(lineCB)
        # lineWidgetLayout.addStretch()

        areaWidget = QWidget()
        areaWidgetLayout = QVBoxLayout(areaWidget)
        arrowsLabel = QLabel('Arrows', areaWidget)
        addContLabel = QLabel('Additional Contours', areaWidget)
        areaStartTimeLabel = QLabel('Start Time', profileWidget)
        self.areaStartTimeCB = QComboBox(areaWidget)
        self.arrowsCB = QComboBox(areaWidget)
        self.arrowsCB.addItems(['None', 'Water Velocity'])
        self.addContCB = QComboBox(areaWidget)

        areaWidgetLayout.addWidget(areaStartTimeLabel)
        areaWidgetLayout.addWidget(self.areaStartTimeCB)
        areaWidgetLayout.addWidget(arrowsLabel)
        areaWidgetLayout.addWidget(self.arrowsCB)
        areaWidgetLayout.addWidget(addContLabel)
        areaWidgetLayout.addWidget(self.addContCB)

        plotOptionsHeader = QLabel('API Options', optionsLFrame)
        plotOptionsHeader.setFixedWidth(270)
        plotOptionsHeader.setFixedHeight(20)
        plotOptionsHeader.setStyleSheet('background-color: #008cba; color : #ffffff;')
        plotOptionsHeader.setAlignment(Qt.AlignCenter)

        self.plotOptions = QTabWidget(optionsLFrame)
        self.plotOptions.setFixedSize(270,170)
        self.plotOptions.addTab(profileWidget, 'Profile')
        self.plotOptions.addTab(vmWidget, 'Virtual Mooring')
        self.plotOptions.addTab(areaWidget, 'Area')
        self.plotOptions.currentChanged.connect(lambda: self.optChanged())

        buttonFrame = QFrame(bottomFrame)
        buttonFrameLayout = QHBoxLayout(buttonFrame)

        outputLabel = QLabel('Output Format', buttonFrame)
        outputLabel.setFixedWidth(75)

        self.outputCB = QComboBox(buttonFrame)
        self.outputCB.addItems(['CSV', 'PNG'])
        self.outputCB.setFixedWidth(50)

        # outputLayout.addWidget(outputLabel)
        # outputLayout.addWidget(self.outputCB)
        # outputLayout.addStretch()

        self.consoleOutput = QTextBrowser(bottomFrame)
        #self.consoleOutput.textChanged().connect(self.scrollToBottom())

        submitButton = QPushButton(buttonFrame)
        submitButton.setText('Submit')
        submitButton.setStyleSheet('background-color: #008cba; color : #ffffff;')
        submitButton.clicked.connect(lambda: self.makeAPICall())

        buttonFrameLayout.addWidget(outputLabel)
        buttonFrameLayout.addWidget(self.outputCB)
        #buttonFrameLayout.addStretch()
        buttonFrameLayout.addWidget(submitButton)
        #buttonFrameLayout.addStretch()

        optionsLLayout.addWidget(dataPanel)
        optionsLLayout.addWidget(plotOptionsHeader)
        optionsLLayout.addWidget(self.plotOptions)
        optionsLLayout.addStretch()
        optionsRLayout.addWidget(locationPanel)
        optionsRLayout.addStretch()
        bottomLayout.addWidget(self.consoleOutput)
        bottomLayout.addWidget(buttonFrame)

        self.changeDataset()

    def addRows(self):
        self.latlonTable.setRowCount(self.latlonTable.rowCount() + 1)

    def removeRows(self):
        if self.latlonTable.rowCount() > 1:
            self.latlonTable.setRowCount(self.latlonTable.rowCount() - 1)

    def optChanged(self):
        if self.plotOptions.currentIndex() == 0 or self.plotOptions.currentIndex() == 1:
            self.latlonTable.setRowCount(1)
        elif self.plotOptions.currentIndex() == 2:
            self.latlonTable.setRowCount(4)

    def changeDataset(self):

        if self.datasetCB.currentText() == '01. GIOPS 10 day Forecast 3D - LatLon':
            self.quantum = 'day'

            timeFactor = datetime.datetime.strptime('1950-01-01 00:00:00', '%Y-%m-%d  %H:%M:%S')
            starttime = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            times = [starttime + datetime.timedelta(hours=x) for x in range(12,216,24)]

            self.variableDict = {"Temperature" : "votemper",
                                "Salinity" : "vosaline",
                                "Speed of Sound" : "sspeed",
                                "Sound Channel Axis" : "deepsoundchannel",
                                "Critical Depth" : "deepsoundchannelbottom",
                                "Depth Excess": "depthexcess",
                                "Potential Sub Surface Channel" : "psubsurfacechannel",
                                "Water Velocity" : "magwatervel",
                                }

        elif self.datasetCB.currentText() == '05. CCG RIOPS Forecast Surface - LatLon' :
            self.quantum = 'hour'
            timeFactor = datetime.datetime.strptime('1950-01-01 00:00:00', '%Y-%m-%d  %H:%M:%S')
            starttime = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(hours=1)
            times = [starttime + datetime.timedelta(hours=x) for x in range(44)]

            self.variableDict = {"Temperature" : "votemper",
                                "Salinity" : "vosaline",
                                "Sea Surface Height" : "sossheig",
                                "Water Velocity" : "magwatervel",
                                }

        elif self.datasetCB.currentText() == '06. RIOPS Forecast 3D - Polar Stereographic' :
            timeFactor = datetime.datetime.strptime('1950-01-01 00:00:00', '%Y-%m-%d  %H:%M:%S')
            starttime = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=6)
            times = [starttime + datetime.timedelta(hours=x) for x in range(24)]

            self.variableDict = {"Temperature" : "votemper",
                                "Salinity" : "vosaline",
                                "Speed of Sound" : "sspeed",
                                "Sound Channel Axis" : "deepsoundchannel",
                                "Critical Depth" : "deepsoundchannelbottom",
                                "Depth Excess": "depthexcess",
                                "Potential Sub Surface Channel" : "psubsurfacechannel",
                                "Water Velocity" : "magwatervel",
                                }

        self.variableCB.addItems(self.variableDict.keys())

        timestrings = [dt.strftime("%Y-%m-%d %H:%M:%S") for dt in times]
        timestamps = [int((ts - timeFactor).total_seconds()) for ts in times]
        self.timestampDict = dict(zip(timestrings, timestamps))

        self.profileStartTimeCB.clear()
        self.profileStartTimeCB.addItems(self.timestampDict.keys())
        self.profileStartTimeCB.setCurrentIndex(0)
        self.vmStartTimeCB.clear()
        self.vmStartTimeCB.addItems(self.timestampDict.keys())
        self.vmStartTimeCB.setCurrentIndex(0)
        self.vmEndTimeCB.clear()
        self.vmEndTimeCB.addItems(self.timestampDict.keys())
        self.vmEndTimeCB.setCurrentIndex(len(self.timestampDict.keys())-1)
        self.areaStartTimeCB.clear()
        self.areaStartTimeCB.addItems(self.timestampDict.keys())
        self.areaStartTimeCB.setCurrentIndex(0)
        self.addContCB.clear()
        self.addContCB.addItem('None')
        self.addContCB.addItems(self.variableDict.keys())

        query ={'dataset' : self.datasetDict['01. GIOPS 10 day Forecast 3D - LatLon'],
                    'variable' : self.variableDict[self.variableCB.currentText()]}

        ts = timestamps_script.requestFile(query)

    def getLatLon(self):

        points = []

        for i in range(self.latlonTable.rowCount()):
            try:
                points.append([float(self.latlonTable.item(i,0).text()),
                            float(self.latlonTable.item(i,1).text())])
            except:
                pass

        return points

    def makeAPICall(self):
        print('Making query...')
        points = self.getLatLon()

        if self.plotOptions.currentIndex() == 0:
            if len(points) > 1:
                points = points[0]
            query = {"dataset":self.datasetDict[self.datasetCB.currentText()],
                    "names":[],
                    "plotTitle":"",
                    "quantum":self.quantum,
                    "showmap":0,
                    "station":points,
                    "time":self.timestampDict[self.profileStartTimeCB.currentText()],
                    "type":"profile",
                    "variable":[self.variableDict[self.variableCB.currentText()]]}

            profile_script.requestFile(query, self.outputCB.currentText())

        elif self.plotOptions.currentIndex() == 1:

            if len(points) > 1:
                points = points[0]

            query = {"colormap":"default",
                    "dataset":self.datasetDict[self.datasetCB.currentText()],
                    "depth":0,
                    "endtime":self.timestampDict[self.vmEndTimeCB.currentText()],
                    "names":[],
                    "plotTitle":"",
                    "quantum":self.quantum,
                    "scale":"-5,30,auto",
                    "showmap":0,
                    "starttime":self.timestampDict[self.vmStartTimeCB.currentText()],
                    "station":points,
                    "type":"timeseries",
                    "variable":self.variableDict[self.variableCB.currentText()]
                }

            vm_script.requestFile(query, self.outputCB.currentText())

        elif self.plotOptions.currentIndex() == 2:

            if self.arrowsCB.currentText() == 'None':
                arrowVar = 'none'
            else:
                arrowVar = self.variableDict[self.arrowsCB.currentText()]

            if self.addContCB.currentText() == 'None':
                contVar = 'none'
            else:
                contVar = self.variableDict[self.addContCB.currentText()]

            if len(points) >= 3:
                query = {"area":[{"innerrings":[],
                        "name":"",
                        "polygons":[points]}],
                        "bathymetry":1,
                        "colormap":"default",
                        "contour":{"colormap":"default",
                        "hatch":0,
                        "legend":1,
                        "levels":"auto",
                        "variable":contVar},
                        "dataset":self.datasetDict[self.datasetCB.currentText()],
                        "depth":0,
                        "interp":"gaussian",
                        "neighbours":10,
                        "projection":"EPSG:3857",
                        "quantum":self.quantum,
                        "quiver":{"colormap":"default",
                        "magnitude":"length",
                        "variable":arrowVar},
                        "radius":25,
                        "scale":"-5,30,auto",
                        "showarea":1,
                        "time":self.timestampDict[self.areaStartTimeCB.currentText()],
                        "type":"map",
                        "variable":self.variableDict[self.variableCB.currentText()]
                    }

                area_script.requestFile(query, self.outputCB.currentText())

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    #tray = QSystemTrayIcon(QIcon("icons/256x256.png"), app)
    onav = onav_lite()
    onav.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

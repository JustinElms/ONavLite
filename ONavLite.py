import os
import shutil
import sys

import requests

try:
    from PySide2.QtWinExtras import QtWin
    myappid = 'DFO.ONavLite.0.0'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

import json
from contextlib import closing
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from PIL import Image
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
                               QLabel, QMainWindow, QPushButton, QTableWidget,
                               QTabWidget, QTextEdit, QVBoxLayout, QWidget)


class apiCalls():

    def __init__(self, console=None):
        self.console = console
        self.dpi = 144
        self.location = os.getcwd()
        self.base_plot_url = 'http://navigator.oceansdata.ca/api/v1.0/plot/?'

    def timestamps(query): 
        url = f"http://navigator.oceansdata.ca/api/v1.0/timestamps/?dataset={query['dataset']}&variable={query['variable']}"

        data_file = requests.get(url, timeout=30)

        if data_file.status_code == 200:
            data = data_file.json()
            return {d['value'].replace('T', ' ').replace('+00:00', ' ') : d['id'] for d in data}

    def depths(query):
        url = f"http://navigator.oceansdata.ca/api/v1.0/depth/?dataset={query['dataset']}&variable={query['variable']}"

        data_file = requests.get(url, timeout=30)

        if data_file.status_code == 200:
            data = data_file.json()
            if data:
                depths = {d['value'] : d['id'] for d in data}
                depths['Bottom'] = depths.pop('Bottom')
                return depths
            else:
                return {'0 m' : 0}

    def csv(self, query, fileName):
        url = self.base_plot_url + urlencode({'query': json.dumps(query)}) + '&save&format=csv&size=10x7&dpi=' + str(self.dpi)
        self.console.append(url)

        data_file = requests.get(url, stream=True, timeout=30)
        if data_file.status_code == 200:
            data = data_file.raw

            # Save file and finish
            with open(fileName + '.csv', 'wb') as self.location:
                self.console.append('Saving as ' + fileName + '.csv')
                shutil.copyfileobj(data, self.location)
                self.console.append('Done')
        else:
            self.console.append('Could not complete request.')
    
    def png(self, query, fileName):
        # Assemble full request
        url = self.base_plot_url + urlencode({'query': json.dumps(query)}) + '&dpi=' + str(self.dpi)
        self.console.append(url)

        # Save file and finish
        try:
            with closing(urlopen(url, timeout=30)) as f:
                self.console.append('Saving as ' + fileName + '.png')
                img = Image.open(f)
                self.console.append('Done')
                img.save(fileName + '.png', 'PNG')
        except HTTPError:
            self.console.append('Could not complete request.')

class Onav_lite(QMainWindow):

    def __init__(self, parent=None):
        super(Onav_lite, self).__init__(parent)
        self.setWindowTitle("Ocean Navigator Lite")

        # initialize dictionaries and variables for data
        self.datasetDict = { '01. GIOPS 10 day Forecast 3D - LatLon' : 'giops_day',
                            '05. CCG RIOPS Forecast Surface - LatLon' : 'riops_fc_2dll',
                            '06. RIOPS Forecast 3D - Polar Stereographic' : 'riops_fc_3dps'
                        }

        self.variableDict = {}
        self.timestampDict = []
        self.depthDict = {}
        self.quantum = []

        # initialize app widgets
        self.initUI()

        self.apiCalls = apiCalls(self.outputConsole)

        # set window size and background color
        self.setFixedSize(640,460)
        self.setStyleSheet('Background-Color: #ffffff')
        self.setWindowIcon(QIcon('onavlite.ico'))

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
        self.variableCB.addItems(self.variableDict.keys())
        self.datasetCB.currentIndexChanged.connect(self.datasetChanged)

        dataPanelLayout.addWidget(dataHeader)
        dataPanelLayout.addWidget(self.datasetCB)
        dataPanelLayout.addWidget(self.variableCB)
        dataPanelLayout.addStretch()

        locationPanel = QFrame(optionsRFrame)
        locationPanelLayout = QVBoxLayout(locationPanel)
        locationPanelLayout.setContentsMargins(0,0,0,0)

        locationButtons = QWidget(locationPanel)
        locationButtonsLayout = QHBoxLayout(locationButtons)
        rowLabel = QLabel('Point Quantity', locationButtons)
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
        profileStartTimeLabel = QLabel('Time', profileWidget)
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
        vmDepthLabel = QLabel('Depth', vmWidget)
        self.vmDepthCB = QComboBox(vmWidget)

        vmWidgetlayout.addWidget(vmStartTimeLabel)
        vmWidgetlayout.addWidget(self.vmStartTimeCB)
        vmWidgetlayout.addWidget(vmEndTimeLabel)
        vmWidgetlayout.addWidget(self.vmEndTimeCB)
        vmWidgetlayout.addWidget(vmDepthLabel)
        vmWidgetlayout.addWidget(self.vmDepthCB)

        areaWidget = QWidget()
        areaWidgetLayout = QVBoxLayout(areaWidget)
        arrowsLabel = QLabel('Arrows', areaWidget)
        addContLabel = QLabel('Additional Contours', areaWidget)
        areaStartTimeLabel = QLabel('Start Time', profileWidget)
        self.areaStartTimeCB = QComboBox(areaWidget)
        self.arrowsCB = QComboBox(areaWidget)
        self.arrowsCB.addItems(['None', 'Water Velocity'])
        self.addContourCB = QComboBox(areaWidget)

        areaWidgetLayout.addWidget(areaStartTimeLabel)
        areaWidgetLayout.addWidget(self.areaStartTimeCB)
        areaWidgetLayout.addWidget(arrowsLabel)
        areaWidgetLayout.addWidget(self.arrowsCB)
        areaWidgetLayout.addWidget(addContLabel)
        areaWidgetLayout.addWidget(self.addContourCB)

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

        self.outputConsole = QTextEdit(bottomFrame)
        self.outputConsole.setReadOnly(True)

        submitButton = QPushButton(buttonFrame)
        submitButton.setText('Submit')
        submitButton.setStyleSheet('background-color: #008cba; color : #ffffff;')
        submitButton.clicked.connect(lambda: self.makeAPICall())

        buttonFrameLayout.addWidget(outputLabel)
        buttonFrameLayout.addWidget(self.outputCB)
        buttonFrameLayout.addWidget(submitButton)

        optionsLLayout.addWidget(dataPanel)
        optionsLLayout.addWidget(plotOptionsHeader)
        optionsLLayout.addWidget(self.plotOptions)
        optionsLLayout.addStretch()
        optionsRLayout.addWidget(locationPanel)
        optionsRLayout.addStretch()
        bottomLayout.addWidget(self.outputConsole)
        bottomLayout.addWidget(buttonFrame)

        self.datasetChanged()
    
    def addRows(self):
        # adds an additional row to the coordinates table
        self.latlonTable.setRowCount(self.latlonTable.rowCount() + 1)

    def removeRows(self):
        # removes the last row from the coordinates table
        if self.latlonTable.rowCount() > 1:
            self.latlonTable.setRowCount(self.latlonTable.rowCount() - 1)

    def optChanged(self):
        # change the number of rows in the coordinates table based on which tab is selected
        if self.plotOptions.currentIndex() == 0 or self.plotOptions.currentIndex() == 1:
            self.latlonTable.setRowCount(1)
        elif self.plotOptions.currentIndex() == 2:
            self.latlonTable.setRowCount(4)

    def datasetChanged(self):

        if self.datasetCB.currentText() == '01. GIOPS 10 day Forecast 3D - LatLon':
            self.quantum = 'day'

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

            self.variableDict = {"Temperature" : "votemper",
                                "Salinity" : "vosaline",
                                "Sea Surface Height" : "sossheig",
                                "Water Velocity" : "magwatervel",
                                }

        elif self.datasetCB.currentText() == '06. RIOPS Forecast 3D - Polar Stereographic' :
            self.quantum = 'hour'

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

        query = {'dataset' : self.datasetDict[self.datasetCB.currentText()],
                    'variable' : self.variableDict[self.variableCB.currentText()]}

        self.timestampDict = apiCalls.timestamps(query)

        self.depthDict = apiCalls.depths(query)

        self.profileStartTimeCB.clear()
        self.profileStartTimeCB.addItems(self.timestampDict.keys())
        self.profileStartTimeCB.setCurrentIndex(0)
        self.vmStartTimeCB.clear()
        self.vmStartTimeCB.addItems(self.timestampDict.keys())
        self.vmStartTimeCB.setCurrentIndex(0)
        self.vmEndTimeCB.clear()
        self.vmEndTimeCB.addItems(self.timestampDict.keys())
        self.vmEndTimeCB.setCurrentIndex(len(self.timestampDict.keys())-1)
        self.vmDepthCB.clear()
        self.vmDepthCB.addItems(self.depthDict.keys())
        self.areaStartTimeCB.clear()
        self.areaStartTimeCB.addItems(self.timestampDict.keys())
        self.areaStartTimeCB.setCurrentIndex(0)
        self.addContourCB.clear()
        self.addContourCB.addItem('None')
        self.addContourCB.addItems(self.variableDict.keys())

    def getLatLon(self):

        points = []

        for i in range(self.latlonTable.rowCount()):
            try:
                points.append([float(self.latlonTable.item(i,0).text()),
                            float(self.latlonTable.item(i,1).text())])
            except AttributeError:
                pass
            except ValueError:
                points = []
                self.outputConsole.append('Coordinate format error.')

        return points

    def makeAPICall(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.outputConsole.append('Making query...')
        points = self.getLatLon()
        query = {}
        fileName = ''

        if self.plotOptions.currentIndex() == 0:
            for p in points:
                fileName = '_'.join(['Profile',
                                    self.datasetDict[self.datasetCB.currentText()],
                                    self.variableDict[self.variableCB.currentText()],
                                    str(self.timestampDict[self.profileStartTimeCB.currentText()]),
                                    str(p),
                                    ])

                query = {"dataset":self.datasetDict[self.datasetCB.currentText()],
                        "names":[],
                        "plotTitle":"",
                        "quantum":self.quantum,
                        "showmap":0,
                        "station":[p],
                        "time":self.timestampDict[self.profileStartTimeCB.currentText()],
                        "type":"profile",
                        "variable":[self.variableDict[self.variableCB.currentText()]]}

        elif self.plotOptions.currentIndex() == 1:

            for p in points:
                
                fileName = '_'.join(['Virtual_Mooring',
                                    self.datasetDict[self.datasetCB.currentText()],
                                    self.variableDict[self.variableCB.currentText()],
                                    str(self.timestampDict[self.vmStartTimeCB.currentText()]),
                                    str(self.timestampDict[self.vmEndTimeCB.currentText()]),
                                    str(p),
                                    ])

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
                        "station":[p],
                        "type":"timeseries",
                        "variable":self.variableDict[self.variableCB.currentText()]
                    }

        elif self.plotOptions.currentIndex() == 2:

            if self.arrowsCB.currentText() == 'None':
                arrowVar = 'none'
            else:
                arrowVar = self.variableDict[self.arrowsCB.currentText()]

            if self.addContourCB.currentText() == 'None':
                contoutVar = 'none'
            else:
                contoutVar = self.variableDict[self.addContourCB.currentText()]

            fileName = '_'.join(['Area',
                                    self.datasetDict[self.datasetCB.currentText()],
                                    self.variableDict[self.variableCB.currentText()],
                                    str(self.timestampDict[self.vmStartTimeCB.currentText()]),
                                    ])

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
                        "variable":contoutVar},
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

        if self.outputCB.currentText() == 'CSV':
            self.apiCalls.csv(query, fileName)
        elif self.outputCB.currentText() == 'PNG':
            self.apiCalls.png(query, fileName)

        QApplication.restoreOverrideCursor()

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    onav = Onav_lite()
    onav.show()
    # Run the main Qt loop
    sys.exit(app.exec_())

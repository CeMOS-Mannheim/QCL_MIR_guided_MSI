
"""
%
%
%
%
 """

#I need to structure the packages
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
from numpy import  array, diff, sum, linspace, log10, size, zeros, transpose, shape, zeros_like, ones, ndarray, sort, unique, mean, random, delete, concatenate, sin, append, arange, savetxt
from datetime import datetime
from tifffile import tifffile
from pandas import DataFrame
import pickle
from time import sleep
from math import ceil
from skimage.morphology import remove_small_objects, binary_closing, disk, remove_small_holes
import os
from matplotlib.pyplot import cm, figure, show, imshow
from scipy.sparse.linalg import spsolve
from scipy import sparse
from skimage.transform import rotate
import skimage.exposure as exposure
from sklearn.mixture import GaussianMixture
from skimage.draw import polygon2mask
from functools import partial

#import own stuff
from QCL.ImportShape.XML.xml2shape import xml2shape
from QCL.ImportShape.XML.shape2xml import shape2xml

#import external python code
from QCL.Appearance.DarkMode import EnableDarkMode
from QCL.Appearance.Range_Slider import RangeSlider

#import windows
from QCL.SubWindows.ASLSBaselineSettingsWindow import ASLS_Settings_Dialog
from QCL.SubWindows.ParametersImageMaskButton import Parameters_Mask_Settings_Dialog

#define functions
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class RandomImageStack():
    imageStack = random.random((1001, 1001, 100))
    wavelength = linspace(1000, 2000, 100)

    def Derivative(self, data, order):
        try:
            sizeX = shape(data)[1]
            sizeY = shape(data)[0]
            sizeZ = shape(data)[2]

            data = data.reshape(sizeY * sizeX, sizeZ)
            data = diff(data, order)
            data = data.reshape(sizeY, sizeX, sizeZ-order)
            return data
        except:
            data = diff(data, order)
            return data

    def AsLS_baseline(self, data, lam, p, niter):

        # general Algorithmus for Asymetric Least Squares Smoothing for Baseline Correction: P.H.C.Eilers & H.F.M.Boelens(2005)
        try:
            sizeX = shape(data)[1]
            sizeY = shape(data)[0]
            sizeZ = shape(data)[2]

            data = data.reshape(sizeX * sizeY, sizeZ)
            L = sizeZ
            D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
            D = lam * D.dot(D.transpose())  # Precompute this term since it does not depend on `w`
            w = ones(L)
            W = sparse.spdiags(w, 0, L, L)
            for i in range(sizeX * sizeY):
                y = 100 - data[i, :]
                print(i)
                for it in range(niter):
                    W.setdiag(w)  # Do not create a new matrix, just update diagonal values
                    Z = W + D
                    z = spsolve(Z, w * y)
                    w = p * (y > z) + (1 - p) * (y < z)
                data[i, :] = data[i, :] + transpose(z) - 100

            data = data.reshape(sizeY, sizeX, sizeZ)
            return data

        except:
            sizeZ = shape(data)[0]
            L = sizeZ
            D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
            D = lam * D.dot(D.transpose())  # Precompute this term since it does not depend on `w`
            w = ones(L)
            W = sparse.spdiags(w, 0, L, L)
            y = 100 - data
            for it in range(niter):
                W.setdiag(w)  # Do not create a new matrix, just update diagonal values
                Z = W + D
                z = spsolve(Z, w * y)
                w = p * (y > z) + (1 - p) * (y < z)
            data = data + transpose(z) - 100
            return data

class QuantumView(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(QuantumView, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        #optional
        if parent == None:
            self.dataIR = RandomImageStack()
            self.minInt = self.dataIR.imageStack.min()
            self.maxInt = self.dataIR.imageStack.max()
        else:
            self.dataIR = RandomImageStack()
            self.minInt = self.dataIR.imageStack.min()
            self.maxInt = self.dataIR.imageStack.max()

        #TD: update here
        self.image_mask_help = []
        self.calculateMask()

        self.ListOfSpectraPixel = []
        self.ListOfSpectraPolygon = []
        self.ListOfSpectraDifference = []
        self.pixelTreeElements = []
        self.polygonTreeElements = []
        self.differenceTreeElements = []
        self.X = []
        self.Y = []
        self.wavelength_names = []
        self.PolygonShowList = []
        self.PolygonListAll = []

        self.imageStack_help = []
        self.pressedYesNo = False

        # Timer for double click
        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.timeout)
        self.leftButton_click_count = 0


        #initialize window
        self.initMe()

    def initMe(self):

        self.setStyleSheet("""QToolTip { 
                                   background-color: darkGray; 
                                   color: black; 
                                   border: black solid 2px
                                   }""")

        # Define geometry of this window
        self.setGeometry(200, 200, 800, 800)
        self.setWindowTitle('QuantumViewer')

        #Init statusBar
        self.statusBar().showMessage('Infrared Viewer v0.2')

        #define grid layout
        self.centralWidgetQV = QtWidgets.QWidget(self)
        self.centralWidgetQV.setObjectName('centralWidgetQV')

        #define main grid layout
        self.mainGridLayoutQV = QtWidgets.QGridLayout(self.centralWidgetQV)
        self.mainGridLayoutQV.setSpacing(10)

        # QV Buttons
        self.subWidgeQVButtons = QtWidgets.QWidget(self)
        self.subGridQVButtons = QtWidgets.QGridLayout(self.subWidgeQVButtons)

        textImport = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>I/O:<b></p>',
            self)

        #Import Buttons
        self.importdata = QtWidgets.QPushButton('', self)
        self.importdata.setMaximumSize(40, 40)
        self.importdata.setIcon(QtGui.QIcon(resource_path('Graphics/SelectFolderButton2.png')))
        self.importdata.setIconSize(QtCore.QSize(30, 30))
        self.importdata.clicked.connect(self.importpickle_pressed)

        self.importpolygon = QtWidgets.QPushButton('', self)
        self.importpolygon.setMaximumSize(40, 40)
        self.importpolygon.setIcon(QtGui.QIcon(resource_path('Graphics/OpenXMLPolygon.png')))
        self.importpolygon.setIconSize(QtCore.QSize(30, 30))
        self.importpolygon.clicked.connect(self.importpolygon_pressed)

        verticalSpacer_Buttons = QtWidgets.QSpacerItem(160, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.exportPickleButton = QtWidgets.QPushButton('', self)
        self.exportPickleButton.setMaximumSize(40, 40)
        self.exportPickleButton.setIcon(QtGui.QIcon(resource_path('Graphics/SaveAsPickle.png')))
        self.exportPickleButton.setIconSize(QtCore.QSize(30, 30))
        self.exportPickleButton.clicked.connect(self.to_pickle)

        #ROI and Spectra

        textSpectra = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>ROI & Spectra:<b></p>',
            self)

        self.singlePixelSpectraButton = QtWidgets.QPushButton('', self)
        self.singlePixelSpectraButton.setMaximumSize(40, 40)
        self.singlePixelSpectraButton.setIcon(QtGui.QIcon(resource_path('Graphics/subSpectra.png')))
        self.singlePixelSpectraButton.setIconSize(QtCore.QSize(30, 30))
        self.singlePixelSpectraButton.setCheckable(True)
        self.singlePixelSpectraButton.setChecked(False)
        self.singlePixelSpectraButton.clicked.connect(self.singlePixelSpectraButton_pressed)

        self.subRegionSpectraClearButton = QtWidgets.QPushButton('', self)
        self.subRegionSpectraClearButton.setMaximumSize(40, 40)
        self.subRegionSpectraClearButton.setIcon(QtGui.QIcon(resource_path('Graphics/subSpectraClear.png')))
        self.subRegionSpectraClearButton.setIconSize(QtCore.QSize(30, 30))
        self.subRegionSpectraClearButton.clicked.connect(self.clearSpectra_pressed)

        self.PolygonButton = QtWidgets.QPushButton('', self)
        self.PolygonButton.setMaximumSize(40, 40)
        self.PolygonButton.setIcon(QtGui.QIcon(resource_path('Graphics/Polygon.png')))
        self.PolygonButton.setIconSize(QtCore.QSize(30, 30))
        self.PolygonButton.clicked.connect(self.drawPolygon_pressed)
        self.PolygonButton.setCheckable(True)
        self.PolygonButton.setChecked(False)

        self.PolygonRemoveButton = QtWidgets.QPushButton('', self)
        self.PolygonRemoveButton.setMaximumSize(40, 40)
        self.PolygonRemoveButton.setIcon(QtGui.QIcon(resource_path('Graphics/PolygonRemove.png')))
        self.PolygonRemoveButton.setIconSize(QtCore.QSize(30, 30))
        self.PolygonRemoveButton.clicked.connect(self.removePolygon_pressed)

        self.DifferenceSpectraButton = QtWidgets.QPushButton('', self)
        self.DifferenceSpectraButton.setMaximumSize(40, 40)
        self.DifferenceSpectraButton.setIcon(QtGui.QIcon(resource_path('Graphics/DifferenceButton.png')))
        self.DifferenceSpectraButton.setIconSize(QtCore.QSize(30, 30))
        self.DifferenceSpectraButton.clicked.connect(self.DifferenceSpectraButton_pressed)

        self.LMDnewXMLButton = QtWidgets.QPushButton('', self)
        self.LMDnewXMLButton.setMaximumSize(40, 40)
        self.LMDnewXMLButton.setIcon(QtGui.QIcon('Graphics/saveShapesAsXml.png'))
        self.LMDnewXMLButton.setIconSize(QtCore.QSize(30, 30))
        self.LMDnewXMLButton.clicked.connect(self.exportToXmlButton_pressed)
        self.LMDnewXMLButton.setEnabled(True)

        # define buttons to change from transmittance to absorbance
        self.absorbanceImage = QtWidgets.QPushButton('', self)
        self.absorbanceImage.setMaximumSize(40, 40)
        self.absorbanceImage.setIcon(QtGui.QIcon(resource_path('Graphics/Absorbance_Fig.png')))
        self.absorbanceImage.setIconSize(QtCore.QSize(35, 35))
        self.absorbanceImage.clicked.connect(self.calc_absorbance_pressed)

        self.transmittanceImage = QtWidgets.QPushButton('', self)
        self.transmittanceImage.setMaximumSize(40, 40)
        self.transmittanceImage.setIcon(QtGui.QIcon(resource_path('Graphics/Transmittance_Fig.png')))
        self.transmittanceImage.setIconSize(QtCore.QSize(35, 35))
        self.transmittanceImage.clicked.connect(self.calc_transmittance_pressed)

        # define buttons for modifying the image orientation
        textImageOrientation = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>image orientation:<b></p>',
            self)

        self.rotateLeft = QtWidgets.QPushButton('', self)
        self.rotateLeft.setMaximumSize(40, 40)
        self.rotateLeft.setIcon(QtGui.QIcon(resource_path('Graphics/rotateLeft2.png')))
        self.rotateLeft.setIconSize(QtCore.QSize(35, 35))
        self.rotateLeft.clicked.connect(self.rotateLeft_pressed)

        self.rotateRight = QtWidgets.QPushButton('', self)
        self.rotateRight.setMaximumSize(40, 40)
        self.rotateRight.setIcon(QtGui.QIcon(resource_path('Graphics/rotateRight2.png')))
        self.rotateRight.setIconSize(QtCore.QSize(35, 35))
        self.rotateRight.clicked.connect(self.rotateRight_pressed)

        self.invertX = QtWidgets.QPushButton('', self)
        self.invertX.setMaximumSize(40, 40)
        self.invertX.setIcon(QtGui.QIcon(resource_path('Graphics/invertX.png')))
        self.invertX.setIconSize(QtCore.QSize(35, 35))
        self.invertX.clicked.connect(self.invertX_pressed)

        self.invertY = QtWidgets.QPushButton('', self)
        self.invertY.setMaximumSize(40, 40)
        self.invertY.setIcon(QtGui.QIcon(resource_path('Graphics/invertY.png')))
        self.invertY.setIconSize(QtCore.QSize(35, 35))
        self.invertY.clicked.connect(self.invertY_pressed)

        textPreProcessing = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>pre-processing:<b></p>',
            self)

        self.progressBaseLine = QtGui.QProgressBar(self)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(QtGui.QPalette.Highlight, QtCore.Qt.green)
        self.progressBaseLine.setPalette(palette)

        self.resetPreProcessingButton = QtWidgets.QPushButton('', self)
        self.resetPreProcessingButton.setMaximumSize(20, 20)
        self.resetPreProcessingButton.setIcon(QtGui.QIcon(resource_path('Graphics/Reset.png')))
        self.resetPreProcessingButton.setIconSize(QtCore.QSize(10, 10))
        self.resetPreProcessingButton.clicked.connect(self.resetPreProcessingButton_pressed)

        self.runPreProcessingButton = QtWidgets.QPushButton('', self)
        self.runPreProcessingButton.setMaximumSize(20, 20)
        self.runPreProcessingButton.setIcon(QtGui.QIcon(resource_path('Graphics/RunButton.png')))
        self.runPreProcessingButton.setIconSize(QtCore.QSize(10, 10))
        self.runPreProcessingButton.clicked.connect(self.runPreProcessingButton_pressed)

        HorizontalLayoutPreProcessingSpacer = QtWidgets.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)

        HorizontalLayoutPreProcessing = QtWidgets.QHBoxLayout()
        HorizontalLayoutPreProcessing.addWidget(textPreProcessing)
        HorizontalLayoutPreProcessing.addSpacerItem(HorizontalLayoutPreProcessingSpacer)
        HorizontalLayoutPreProcessing.addWidget(self.progressBaseLine)
        HorizontalLayoutPreProcessing.addWidget(self.resetPreProcessingButton)
        HorizontalLayoutPreProcessing.addWidget(self.runPreProcessingButton)

        # input for baseline correction
        textBaseline = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>baseline correction:<b></p>',
            self)

        self.BaselineBox = QtWidgets.QComboBox(self)
        self.BaselineBox.addItem("AsLS baseline")

        self.BaselineCheckBox = QtWidgets.QCheckBox('', self)
        self.BaselineCheckBox.setChecked(False)

        self.BaselineSettingsButton = QtWidgets.QPushButton('', self)
        self.BaselineSettingsButton.setMaximumSize(20, 20)
        self.BaselineSettingsButton.setIcon(QtGui.QIcon(resource_path('Graphics/SettingsButton.png')))
        self.BaselineSettingsButton.setIconSize(QtCore.QSize(10, 10))
        self.BaselineSettingsButton.clicked.connect(self.BaselineSettingsButton_pressed)
        self.ASLSSettingsWindow = None

        #initial settings for ASLS baseline correction
        self.smoothFactorValue = '1000000'
        self.weightingFactorValue = '0.01'
        self.iterationFactorValue = '10'

        HorizontalLayoutBaselineSpacer = QtWidgets.QSpacerItem(160, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        HorizontalLayoutBaseline = QtWidgets.QHBoxLayout()
        HorizontalLayoutBaseline.addWidget(self.BaselineBox)
        HorizontalLayoutBaseline.addWidget(self.BaselineCheckBox)
        HorizontalLayoutBaseline.addWidget(self.BaselineSettingsButton)
        HorizontalLayoutBaseline.addSpacerItem(HorizontalLayoutBaselineSpacer)

        HorizontalLayoutSpacer = QtWidgets.QSpacerItem(120, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        HorizontalLayout = QtWidgets.QHBoxLayout()
        HorizontalLayout.addWidget(self.rotateLeft)
        HorizontalLayout.addWidget(self.rotateRight)
        HorizontalLayout.addWidget(self.invertX)
        HorizontalLayout.addWidget(self.invertY)
        HorizontalLayout.addSpacerItem(HorizontalLayoutSpacer)

        textTransAbs = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Absorbance & Transmittance:<b></p>',
            self)
        HorizontalLayoutTransAbsSpacer = QtWidgets.QSpacerItem(207, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        HorizontalLayoutTransAbs = QtWidgets.QHBoxLayout()
        HorizontalLayoutTransAbs.addWidget(self.absorbanceImage)
        HorizontalLayoutTransAbs.addWidget(self.transmittanceImage)
        HorizontalLayoutTransAbs.addSpacerItem(HorizontalLayoutTransAbsSpacer)


        #Regions of Interest Colors
        #Colors
        self.AnnotationCombo = QtWidgets.QComboBox(self)
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/red_icon.png"), "")  # red
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/pink_icon.png"), "")  # pink
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/rosa_icon.png"), "")  # rosa
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/hellrosa_icon.png"), "")  # hellrosa

        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/green_icon.png"), "")  # green
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/DarkGreen_Icon.png"), "")  # DarkGreen
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/LightGreen_Icon.png"), "")  # LightGreen

        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/yellow_icon.png"), "")  # yellow
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/orange_icon.png"), "")  # orange
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/yellow_ImSc_icon.png"), "")  # yellow_ImSc

        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/black_icon.png"), "")  # black
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/grey_icon.png"), "")  # grey
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/black_ImSc_icon.png"), "")  # black_ImSc
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/brown_icon.png"), "")  # brown

        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/blue_icon.png"), "")  # blue
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/cyan_icon.png"), "")  # cyan
        self.AnnotationCombo.addItem(QtGui.QIcon("Icons/purple_icon.png"), "")  # pruple
        self.AnnotationCombo.setIconSize(QtCore.QSize(50, 15))

        self.LineStyleCombo = QtWidgets.QComboBox(self)
        self.LineStyleCombo.addItem(QtGui.QIcon("Icons/SolidLine.png"), "")  # solid
        self.LineStyleCombo.addItem(QtGui.QIcon("Icons/DashedLine.png"), "")  # solid
        self.LineStyleCombo.addItem(QtGui.QIcon("Icons/DottedLine.png"), "")  # solid
        self.LineStyleCombo.setIconSize(QtCore.QSize(30, 15))

        self.PenThicknessValue = '1'
        self.PenThicknessFactor = QtGui.QDoubleValidator(0, 5, 0, self)
        self.PenThicknessFactor.setLocale(self.locale())
        self.PenThicknessInput = QtWidgets.QLineEdit(self)
        self.PenThicknessInput.setMaximumSize(QtCore.QSize(30, 22))
        self.PenThicknessInput.setLocale(self.locale())
        self.PenThicknessInput.setValidator(self.PenThicknessFactor)
        self.PenThicknessInput.setPlaceholderText('1')
        self.PenThicknessInput.returnPressed.connect(self.PenThickness_Enter)

        self.opacitySlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.opacitySlider.setRange(0, 100)
        self.opacitySlider.setSingleStep(1)
        self.opacitySlider.setValue(20)
        self.opacitySlider.setEnabled(True)
        self.opacitySlider.valueChanged.connect(self.opacitySlider_changed)

        # For polygons
        self.FillingCheckbox = QtWidgets.QCheckBox("")
        self.FillingCheckbox.setChecked(True)

        HorizontalLayoutShapes = QtWidgets.QHBoxLayout()
        HorizontalLayoutShapes.addWidget(self.AnnotationCombo)
        HorizontalLayoutShapes.addWidget(self.LineStyleCombo)
        HorizontalLayoutShapes.addWidget(self.PenThicknessInput)
        HorizontalLayoutShapes.addWidget(self.opacitySlider)
        HorizontalLayoutShapes.addWidget(self.FillingCheckbox)




        # input for derivative
        textDerivative = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>derivative:<b></p>',
            self)

        self.derivativeBox = QtWidgets.QComboBox(self)
        self.derivativeBox.addItem("1st derivative")
        self.derivativeBox.addItem("2nd derivative")

        self.derivativeCheckBox = QtWidgets.QCheckBox('', self)
        self.derivativeCheckBox.setChecked(False)

        spaceItem01 = QtWidgets.QSpacerItem(120, 10, QtWidgets.QSizePolicy.Expanding)
        HorizontalLayoutDerivative = QtWidgets.QHBoxLayout()
        HorizontalLayoutDerivative.addWidget(self.derivativeBox)
        HorizontalLayoutDerivative.addWidget(self.derivativeCheckBox)
        HorizontalLayoutDerivative.addSpacerItem(spaceItem01)

        # input for SNV
        textNormalization = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>normalization:<b></p>',
            self)

        self.NormalizationBox = QtWidgets.QComboBox(self)
        self.NormalizationBox.addItem("Standard Normal Variate")

        self.NormalizationCheckBox = QtWidgets.QCheckBox('', self)
        self.NormalizationCheckBox.setChecked(False)

        self.modifyMaskButtonIR = QtWidgets.QPushButton('', self)
        self.modifyMaskButtonIR.setMaximumSize(25, 25)
        self.modifyMaskButtonIR.setIcon(QtGui.QIcon('Graphics/RunButton.png'))
        self.modifyMaskButtonIR.setIconSize(QtCore.QSize(14, 14))
        self.modifyMaskButtonIR.clicked.connect(self.modifyMaskButtonIR_pressed)

        textMask = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Mask:<b></p>',
            self)

        self.MaskListButton = QtWidgets.QPushButton('', self)
        self.MaskListButton.setMaximumSize(30, 30)
        self.MaskListButton.setIcon(QtGui.QIcon(resource_path('Graphics/MaskList.png')))
        self.MaskListButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskListButton.clicked.connect(self.maskList_pressed)

        self.MaskInvertButton = QtWidgets.QPushButton('', self)
        self.MaskInvertButton.setMaximumSize(30, 30)
        self.MaskInvertButton.setIcon(QtGui.QIcon(resource_path('Graphics/InvertMask.png')))
        self.MaskInvertButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskInvertButton.clicked.connect(self.maskInvert_pressed)

        self.MaskSettingsButton = QtWidgets.QPushButton('', self)
        self.MaskSettingsButton.setMaximumSize(30, 30)
        self.MaskSettingsButton.setIcon(QtGui.QIcon(resource_path('Graphics/SettingsButton.png')))
        self.MaskSettingsButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskSettingsButton.clicked.connect(self.MaskSettingsButton_pressed)
        self.MaskSettingsWindow = None
        self.closing_value = 1
        self.object_size_remove = 200
        self.object_size_fill = 200

        spaceHorizontalLayoutMaskButtons = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Expanding)
        spaceHorizontalLayoutMaskButtons1 = QtWidgets.QSpacerItem(170, 10, QtWidgets.QSizePolicy.Expanding)
        HorizontalLayoutMaskButtons = QtWidgets.QHBoxLayout()
        HorizontalLayoutMaskButtons.addWidget(self.modifyMaskButtonIR)
        HorizontalLayoutMaskButtons.addWidget(self.MaskSettingsButton)
        HorizontalLayoutMaskButtons.addSpacerItem(spaceHorizontalLayoutMaskButtons)
        HorizontalLayoutMaskButtons.addWidget(self.MaskListButton)
        HorizontalLayoutMaskButtons.addWidget(self.MaskInvertButton)
        HorizontalLayoutMaskButtons.addSpacerItem(spaceHorizontalLayoutMaskButtons1)

        #HorizontalLayoutMask1 = QtWidgets.QHBoxLayout()
        #HorizontalLayoutMask1.addWidget(self.modifyMaskButtonIR)
        #HorizontalLayoutMask1.addWidget(self.MaskBinaryClosingInputIR)
        #HorizontalLayoutMask1.addWidget(self.MaskRemoveHolesObjectsInputIR)
        #HorizontalLayoutMask1.addWidget(self.MaskRemoveSmallObjectsInputIR)

        spaceItem02 = QtWidgets.QSpacerItem(50, 10, QtWidgets.QSizePolicy.Expanding)
        HorizontalLayoutNormalization = QtWidgets.QHBoxLayout()
        HorizontalLayoutNormalization.addWidget(self.NormalizationBox)
        HorizontalLayoutNormalization.addWidget(self.NormalizationCheckBox)
        HorizontalLayoutNormalization.addSpacerItem(spaceItem02)

        HorizontalLayoutButtons = QtWidgets.QHBoxLayout()
        HorizontalLayoutButtons.addWidget(self.importdata)
        HorizontalLayoutButtons.addWidget(self.importpolygon)
        HorizontalLayoutButtons.addSpacerItem(verticalSpacer_Buttons)
        HorizontalLayoutButtons.addWidget(self.exportPickleButton)

        verticalSpacer_Spectra = QtWidgets.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        HorizontalLayoutSpectra = QtWidgets.QHBoxLayout()
        HorizontalLayoutSpectra.addWidget(self.singlePixelSpectraButton)
        HorizontalLayoutSpectra.addWidget(self.PolygonButton)
        HorizontalLayoutSpectra.addWidget(self.PolygonRemoveButton)
        HorizontalLayoutSpectra.addWidget(self.subRegionSpectraClearButton)
        HorizontalLayoutSpectra.addWidget(self.DifferenceSpectraButton)
        HorizontalLayoutSpectra.addSpacerItem(verticalSpacer_Spectra)
        HorizontalLayoutSpectra.addWidget(self.LMDnewXMLButton)

        self.SpectraListTree = QtWidgets.QTreeWidget()
        self.SpectraListTree.setMinimumSize(100,280)
        self.SpectraListTree.setColumnCount(2)
        self.SpectraListTree.setHeaderLabels(['', ''])
        self.pixelTree = QtWidgets.QTreeWidgetItem(self.SpectraListTree)
        self.pixelTree.setText(0, "Pixel")
        self.polygonTree = QtWidgets.QTreeWidgetItem(self.SpectraListTree)
        self.polygonTree.setText(0, "Polygon")
        self.differenceTree = QtWidgets.QTreeWidgetItem(self.SpectraListTree)
        self.differenceTree.setText(0, "Difference")
        self.SpectraListTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.SpectraListTree.customContextMenuRequested.connect(self.openMenu)
        header = self.SpectraListTree.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.subGridQVButtons.addWidget(textImport, 0, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutButtons, 1, 0)
        self.subGridQVButtons.addWidget(textTransAbs, 2, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutTransAbs, 3, 0)
        self.subGridQVButtons.addWidget(textSpectra, 4, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutSpectra, 5, 0)
        self.subGridQVButtons.addWidget(self.SpectraListTree, 6, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutShapes, 7, 0)
        self.subGridQVButtons.addWidget(textImageOrientation, 8, 0)
        self.subGridQVButtons.addLayout(HorizontalLayout, 9, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutPreProcessing, 10, 0)
        self.subGridQVButtons.addWidget(textBaseline, 11, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutBaseline, 12, 0)
        self.subGridQVButtons.addWidget(textDerivative, 13, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutDerivative, 14, 0)
        self.subGridQVButtons.addWidget(textNormalization, 15, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutNormalization, 16, 0)
        self.subGridQVButtons.addWidget(textMask, 17, 0)
        self.subGridQVButtons.addLayout(HorizontalLayoutMaskButtons, 18, 0)
        #self.subGridQVButtons.addLayout(HorizontalLayoutMask0, 19, 0)
        #self.subGridQVButtons.addLayout(HorizontalLayoutMask1, 20, 0)

        # QV show
        self.subWidgeQVShow = QtWidgets.QWidget(self)
        self.subGridQVShow = QtWidgets.QGridLayout(self.subWidgeQVShow)

        self.nextLeft = QtWidgets.QPushButton('', self)
        self.nextLeft.setMaximumSize(30, 30)
        self.nextLeft.setIcon(QtGui.QIcon(resource_path('Graphics/rotateLeft.png')))
        self.nextLeft.setIconSize(QtCore.QSize(15, 15))
        self.nextLeft.clicked.connect(self.nextLeft_pressed)

        self.nextRight = QtWidgets.QPushButton('', self)
        self.nextRight.setMaximumSize(30, 30)
        #self.nextRight.setIcon(QtGui.QIcon('Graphics/rotateRight.png'))
        self.nextRight.setIcon(QtGui.QIcon(resource_path('Graphics/rotateRight.png')))
        self.nextRight.setIconSize(QtCore.QSize(15, 15))
        self.nextRight.clicked.connect(self.nextRight_pressed)

        self.currentWavenumber = str(int(self.dataIR.wavelength.min()))
        self.validatorcurrentWavenumber = QtGui.QDoubleValidator(0, 5000, 0, self)
        self.validatorcurrentWavenumber.setLocale(self.locale())
        self.currentWavenumberInput = QtWidgets.QLineEdit(self)
        self.currentWavenumberInput.setLocale(self.locale())
        self.currentWavenumberInput.setValidator(self.validatorcurrentWavenumber)
        self.currentWavenumberInput.setPlaceholderText(str(self.currentWavenumber))
        #self.currentWavenumberInput.returnPressed.connect(self.PixelSizeIREnter)
        self.currentWavenumberInput.setEnabled(False)

        textinverseCM = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>inverse cm<b></p>',
            self)

        self.ColormapComboBox = QtWidgets.QComboBox(self)
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/gray_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/binary_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/gist_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/inferno_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/PiYg_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/viridis_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/cividis_icon.png")), "")
        #self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/mako_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/plasma_icon.png")), "")
        self.ColormapComboBox.currentTextChanged.connect(self.on_ColormapComboBox_changed)
        self.ColormapComboBox.setIconSize(QtCore.QSize(50, 15))

        randomImage = self.dataIR.imageStack[:, :, -1]
        maxSizeX = 500
        maxSizeY = 500

        self.winQV = pg.GraphicsLayoutWidget()
        self.winQV.setBackground(0.21)
        self.winQV.ci.setContentsMargins(0, 0, 0, 0)
        self.winQV.ci.setSpacing(0)
        self.winQV.setMinimumSize(maxSizeY, maxSizeX)
        self.winQV.setMaximumSize(maxSizeY, maxSizeX)
        self.viewQV = self.winQV.addViewBox(enableMouse=True)
        self.viewQV.setAspectLocked(True)
        self.viewQV.invertY(False)
        yMax = randomImage.shape[1]
        xMax = randomImage.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewQV.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.imgQV = pg.ImageItem()
        self.viewQV.addItem(self.imgQV)
        self.imgQV.setImage(randomImage)
        self.winQV.scene().sigMouseClicked.connect(self.onImageSpectra_clicked)

        self.QVShowButton = QtWidgets.QPushButton('', self)
        self.QVShowButton.setMaximumSize(30, 30)
        self.QVShowButton.setIcon(QtGui.QIcon(resource_path('Graphics/QVButton.png')))
        self.QVShowButton.setIconSize(QtCore.QSize(15, 15))
        self.QVShowButton.setCheckable(True)
        self.QVShowButton.setChecked(True)
        self.QVShowButton.clicked.connect(self.QVShow_pressed)

        self.MaskShowButton = QtWidgets.QPushButton('', self)
        self.MaskShowButton.setMaximumSize(30, 30)
        self.MaskShowButton.setIcon(QtGui.QIcon(resource_path('Graphics/MaskButton.png')))
        self.MaskShowButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskShowButton.setCheckable(True)
        self.MaskShowButton.setChecked(False)
        self.MaskShowButton.clicked.connect(self.maskShow_pressed)

        self.MaskApplyButton = QtWidgets.QPushButton('', self)
        self.MaskApplyButton.setMaximumSize(30, 30)
        self.MaskApplyButton.setIcon(QtGui.QIcon(resource_path('Graphics/ApplyMask.png')))
        self.MaskApplyButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskApplyButton.clicked.connect(self.maskApply_pressed)

        self.HideMeanButton = QtWidgets.QPushButton('', self)
        self.HideMeanButton.setMaximumSize(30, 30)
        self.HideMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/HideMeanButton.png')))
        self.HideMeanButton.setIconSize(QtCore.QSize(15, 15))
        self.HideMeanButton.clicked.connect(self.hideMean_pressed)
        self.HideMeanButton.setCheckable(True)
        self.HideMeanButton.setChecked(False)

        self.RelativeScaleButton = QtWidgets.QPushButton('', self)
        self.RelativeScaleButton.setMaximumSize(30, 30)
        self.RelativeScaleButton.setIcon(QtGui.QIcon(resource_path('Graphics/RelativeScale.png')))
        self.RelativeScaleButton.setIconSize(QtCore.QSize(19, 19))
        self.RelativeScaleButton.clicked.connect(self.RelativeScaleButton_pressed)
        self.RelativeScaleButton.setCheckable(True)
        self.RelativeScaleButton.setChecked(True)

        self.AbsoluteScaleButton = QtWidgets.QPushButton('', self)
        self.AbsoluteScaleButton.setMaximumSize(30, 30)
        self.AbsoluteScaleButton.setIcon(QtGui.QIcon(resource_path('Graphics/AbsoluteScale.png')))
        self.AbsoluteScaleButton.setIconSize(QtCore.QSize(15, 15))
        self.AbsoluteScaleButton.clicked.connect(self.AbsoluteScaleButton_pressed)
        self.AbsoluteScaleButton.setCheckable(True)
        self.AbsoluteScaleButton.setChecked(False)

        self.rangeSlider = RangeSlider(QtCore.Qt.Horizontal)
        #self.rangeSlider.setMinimumHeight(30)
        self.rangeSlider.setMinimumSize(100, 30)
        self.rangeSlider.setMinimum(0)
        self.rangeSlider.setMaximum(100)
        self.rangeSlider.setLow(0)
        self.rangeSlider.setHigh(100)
        self.rangeSlider.sliderMoved.connect(self.rangeSlider_moved)
        self.sliderlow = self.rangeSlider.low()
        self.sliderhigh = self.rangeSlider.high()

        spaceItemLayout = QtWidgets.QSpacerItem(510, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayout = QtWidgets.QHBoxLayout()
        VerticalLayout.addWidget(self.nextLeft)
        VerticalLayout.addWidget(self.nextRight)
        VerticalLayout.addWidget(self.currentWavenumberInput)
        VerticalLayout.addWidget(textinverseCM)
        VerticalLayout.addSpacerItem(spaceItemLayout)

        spaceItemVerticalLayoutBottom = QtWidgets.QSpacerItem(40, 10, QtWidgets.QSizePolicy.Expanding)
        spaceItemVerticalLayoutBottom2 = QtWidgets.QSpacerItem(310, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutBottom = QtWidgets.QHBoxLayout()
        VerticalLayoutBottom.addWidget(self.ColormapComboBox)
        VerticalLayoutBottom.addWidget(self.QVShowButton)
        VerticalLayoutBottom.addWidget(self.MaskShowButton)
        VerticalLayoutBottom.addWidget(self.MaskApplyButton)
        VerticalLayoutBottom.addSpacerItem(spaceItemVerticalLayoutBottom)
        VerticalLayoutBottom.addWidget(self.RelativeScaleButton)
        VerticalLayoutBottom.addWidget(self.AbsoluteScaleButton)
        VerticalLayoutBottom.addWidget(self.rangeSlider)
        VerticalLayoutBottom.addSpacerItem(spaceItemVerticalLayoutBottom2)

        self.showSelectedBox = QtWidgets.QPushButton('', self)
        self.showSelectedBox.setMaximumSize(30, 30)
        self.showSelectedBox.setIcon(QtGui.QIcon(resource_path('Graphics/ShowLineButton.png')))
        self.showSelectedBox.setIconSize(QtCore.QSize(15, 15))
        self.showSelectedBox.clicked.connect(self.showToggle)
        self.showSelectedBox.setCheckable(True)
        self.showSelectedBox.setChecked(True)


        spaceVerticalLayoutTop = QtWidgets.QSpacerItem(500, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutTop = QtWidgets.QHBoxLayout()
        VerticalLayoutTop.addSpacerItem(spaceVerticalLayoutTop)
        VerticalLayoutTop.addWidget(self.showSelectedBox)
        VerticalLayoutTop.addWidget(self.HideMeanButton)

        spaceItemwin = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutwin = QtWidgets.QHBoxLayout()
        VerticalLayoutwin.addSpacerItem(spaceItemwin)
        VerticalLayoutwin.addWidget(self.winQV)
        VerticalLayoutwin.addSpacerItem(spaceItemwin)

        self.subGridQVShow.addLayout(VerticalLayout, 0, 0, 1, 4)
        self.subGridQVShow.addLayout(VerticalLayoutBottom, 1, 0, 1, 4)
        self.subGridQVShow.addLayout(VerticalLayoutwin, 2, 0, 4, 4)

        # QV Spectra
        self.subWidgedQVSpectra = QtWidgets.QWidget(self)
        self.subGridQVSpectra = QtWidgets.QGridLayout(self.subWidgedQVSpectra)

        #addPlot
        self.plotWindow = pg.GraphicsWindow()
        self.plotWindow.setBackground(0.25)
        self.plotWindow.ci.setContentsMargins(10, 10, 10, 10)
        self.plotWindow.ci.setSpacing(0)

        self.plotWindow.addLabel('wavenumber (inverse cm)', row=1, col=1)
        self.plotWindow.addLabel('signal (arb. units)', angle=-90, row=0, col=0)
        self.plotAbsorption = self.plotWindow.addPlot(row=0, col=1)

        self.plotAbsorption.setXRange(700, 3050, padding = 0)
        meanSpectrum = mean(self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0]*self.dataIR.imageStack.shape[1]), int(self.dataIR.imageStack.shape[2]))), 0)
        self.plotData = self.plotAbsorption.plot(x=self.dataIR.wavelength, y=meanSpectrum)
        maxSizePlotY = 200
        maxSizePlotX = 800
        self.plotWindow.setMinimumSize(maxSizePlotX, maxSizePlotY)
        self.plotWindow.setMaximumSize(maxSizePlotX, maxSizePlotY)

        self.line = pg.InfiniteLine(pos = int(self.dataIR.wavelength.min()), angle=90, movable=True)
        self.plotLine = self.plotAbsorption.addItem(self.line)
        self.line.setBounds([self.dataIR.wavelength.min(), self.dataIR.wavelength.max()])
        self.line.sigPositionChangeFinished.connect(self.line_obtainPosition)

        center = int((self.dataIR.wavelength.max()+self.dataIR.wavelength.min())/2)
        centerPM = 50
        self.regionLine = pg.LinearRegionItem([center-centerPM, center+centerPM], bounds=[self.dataIR.wavelength.min(), self.dataIR.wavelength.max()], movable=True)
        self.plotRegionLine = self.plotAbsorption.addItem(self.regionLine)

        self.subGridQVSpectra.addLayout(VerticalLayoutTop, 0, 0)
        self.subGridQVSpectra.addWidget(self.plotWindow, 1, 0)

        # QV SpectraButtons
        self.subWidgedQVSpectraButtons = QtWidgets.QWidget(self)
        self.subGridQVSpectraButtons = QtWidgets.QGridLayout(self.subWidgedQVSpectraButtons)


        #select certain wavenumber(s) and generate a list
        textQListWidgetTitle= QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Selected wavenumbers:<b></p>',
            self)

        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.itemDoubleClicked.connect(self.double_click_pressed)

        self.addWidgetButton = QtWidgets.QPushButton('', self)
        self.addWidgetButton.setMaximumSize(30, 30)
        self.addWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/AddSingleWavenumber.png')))
        self.addWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.addWidgetButton.clicked.connect(self.addWidgetButton_pressed)

        self.addRangeWidgetButton = QtWidgets.QPushButton('', self)
        self.addRangeWidgetButton.setMaximumSize(30, 30)
        self.addRangeWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/AddWavenumberRange.png')))
        self.addRangeWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.addRangeWidgetButton.clicked.connect(self.addRangeWidgetButton_pressed)

        self.removeWidgetButton = QtWidgets.QPushButton('', self)
        self.removeWidgetButton.setMaximumSize(30, 30)
        self.removeWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/RemoveWavenumberFromList.png')))
        self.removeWidgetButton.setIconSize(QtCore.QSize(10, 10))
        self.removeWidgetButton.clicked.connect(self.removeWidgetButton_pressed)

        self.clearWidgetButton = QtWidgets.QPushButton('', self)
        self.clearWidgetButton.setMaximumSize(30, 30)
        self.clearWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/ClearButtonList.png')))
        self.clearWidgetButton.setIconSize(QtCore.QSize(15, 15))
        self.clearWidgetButton.clicked.connect(self.clearWidgetButton_pressed)

        self.sortOrder = QtWidgets.QPushButton('', self)
        self.sortOrder.setMaximumSize(30, 30)
        self.sortOrder.setIcon(QtGui.QIcon(resource_path('Graphics/AscendingButton.png')))
        self.sortOrder.setIconSize(QtCore.QSize(15, 15))
        self.sortOrder.setCheckable(True)
        self.sortOrder.setChecked(False)

        self.sortWidgetButton = QtWidgets.QPushButton('', self)
        self.sortWidgetButton.setMaximumSize(30, 30)
        self.sortWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/SortIconList.png')))
        self.sortWidgetButton.setIconSize(QtCore.QSize(12, 15))
        self.sortWidgetButton.clicked.connect(self.sortWidgetButton_pressed)

        self.saveWidgetButton = QtWidgets.QPushButton('', self)
        self.saveWidgetButton.setMaximumSize(30, 30)
        self.saveWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/SaveListTxt.png')))
        self.saveWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.saveWidgetButton.clicked.connect(self.saveWidgetButton_pressed)

        self.openWidgetButton = QtWidgets.QPushButton('', self)
        self.openWidgetButton.setMaximumSize(30, 30)
        self.openWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/OpenList.png')))
        self.openWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.openWidgetButton.clicked.connect(self.openWidgetButton_pressed)

        VerticalLayoutList = QtWidgets.QHBoxLayout()
        VerticalLayoutList.addWidget(self.addWidgetButton)
        VerticalLayoutList.addWidget(self.addRangeWidgetButton)
        VerticalLayoutList.addWidget(self.removeWidgetButton)
        VerticalLayoutList.addWidget(self.clearWidgetButton)
        VerticalLayoutList.addWidget(self.saveWidgetButton)
        VerticalLayoutList.addWidget(self.openWidgetButton)

        spaceVerticalLayoutSort = QtWidgets.QSpacerItem(100, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutSort = QtWidgets.QHBoxLayout()
        VerticalLayoutSort.addSpacerItem(spaceVerticalLayoutSort)
        VerticalLayoutSort.addWidget(self.sortOrder)
        VerticalLayoutSort.addWidget(self.sortWidgetButton)


        self.SumMeanButton = QtWidgets.QPushButton('', self)
        self.SumMeanButton.setMaximumSize(25, 25)
        self.SumMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/Sum_Mean_Button.png')))
        self.SumMeanButton.setIconSize(QtCore.QSize(20, 20))
        self.SumMeanButton.clicked.connect(self.SumMeanButton_pressed)

        self.ShowMeanButton = QtWidgets.QPushButton('', self)
        self.ShowMeanButton.setMaximumSize(25, 25)
        self.ShowMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/Show_Mean_Button.png')))
        self.ShowMeanButton.setIconSize(QtCore.QSize(20, 20))
        self.ShowMeanButton.setCheckable(True)
        self.ShowMeanButton.setChecked(False)
        self.ShowMeanButton.clicked.connect(self.ShowMeanButton_pressed)

        self.ExportMeanButton = QtWidgets.QPushButton('', self)
        self.ExportMeanButton.setMaximumSize(25, 25)
        self.ExportMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/ExportCSV.png')))
        self.ExportMeanButton.setIconSize(QtCore.QSize(20, 20))
        self.ExportMeanButton.clicked.connect(self.ExportMeanButton_pressed)

        spaceItem0 = QtWidgets.QSpacerItem(100, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutButtons = QtWidgets.QHBoxLayout()
        VerticalLayoutButtons.addWidget(self.SumMeanButton)
        VerticalLayoutButtons.addSpacerItem(spaceItem0)
        VerticalLayoutButtons.addWidget(self.ShowMeanButton)
        VerticalLayoutButtons.addWidget(self.ExportMeanButton)

        self.subGridQVSpectraButtons.addWidget(textQListWidgetTitle, 0, 0)
        self.subGridQVSpectraButtons.addWidget(self.listWidget, 1, 0)
        self.subGridQVSpectraButtons.addLayout(VerticalLayoutList, 2, 0)
        self.subGridQVSpectraButtons.addLayout(VerticalLayoutSort, 3, 0)
        self.subGridQVSpectraButtons.addLayout(VerticalLayoutButtons, 4, 0)


        # Place Elements to MainGrid (mainGridLayoutIRA)
        self.mainGridLayoutQV.addWidget(self.subWidgeQVButtons, 0, 0, 2, 1)
        self.mainGridLayoutQV.addWidget(self.subWidgeQVShow, 0, 1)
        self.mainGridLayoutQV.addWidget(self.subWidgedQVSpectra, 1, 1, 1, 2)
        self.mainGridLayoutQV.addWidget(self.subWidgedQVSpectraButtons, 0, 2)

        # show  Widget
        self.centralWidgetQV.setLayout(self.mainGridLayoutQV)
        self.setCentralWidget(self.centralWidgetQV)

        self.winQV.scene().sigMouseMoved.connect(self.OnClick)

        #set tooltips
        self.importdata.setToolTip('Open data set(s).')
        self.importpolygon.setToolTip('Import shape(s) from .xml file.')
        self.exportPickleButton.setToolTip('Save data as .pickle file.')
        self.singlePixelSpectraButton.setToolTip('Obtain single spectra.')
        self.subRegionSpectraClearButton.setToolTip('Delete all ROI elements and spectra.')
        self.PolygonButton.setToolTip('Create ROI.')
        self.PolygonRemoveButton.setToolTip('Delete incomplete polygon.')
        self.DifferenceSpectraButton.setToolTip('Generate spectral difference.')
        self.LMDnewXMLButton.setToolTip('Save shape(s) as .xml file.')
        self.absorbanceImage.setToolTip('Absorbance')
        self.transmittanceImage.setToolTip('Transmittance')
        self.rotateLeft.setToolTip('Rotate image by -90 degree.')
        self.rotateRight.setToolTip('Rotate image by +90 degree.')
        self.invertX.setToolTip('Flip image vertically.')
        self.invertY.setToolTip('Flip image horizontally.')
        self.resetPreProcessingButton.setToolTip('Re-import data. Reset button.')
        self.runPreProcessingButton.setToolTip('Perform pre-processing, i.e. baseline correction, on current data set.')
        self.BaselineSettingsButton.setToolTip('Open settings for baseline correction.')
        self.AnnotationCombo.setToolTip('Color(s) for spectra and ROI.')
        self.LineStyleCombo.setToolTip('Line style.')
        self.PenThicknessInput.setToolTip('Line thickness.')
        self.opacitySlider.setToolTip('ROI opacity.')
        self.FillingCheckbox.setToolTip('ROI filling y/n.')
        self.modifyMaskButtonIR.setToolTip('Modify image mask.')
        self.MaskListButton.setToolTip('Generate image mask based on wavenumber list.')
        self.MaskInvertButton.setToolTip('Invert mask.')
        self.MaskSettingsButton.setToolTip('Open settings for image mask generation.')

        self.nextLeft.setToolTip('-1 wavenumber step size.')
        self.nextRight.setToolTip('+1 wavenumber step size.')
        self.currentWavenumberInput.setToolTip('Current wavenumber.')
        self.ColormapComboBox.setToolTip('Select color scheme.')
        self.QVShowButton.setToolTip('Show IR image.')
        self.MaskShowButton.setToolTip('Show mask image. By default, image mask is calculated based on GGM thresholding for the mean image \n of the following wavenumbers: 1080, 1552, 1660 and 2924 cm-1.')
        self.MaskApplyButton.setToolTip('Mask current IR image.')
        self.HideMeanButton.setToolTip('Hide mean IR spectrum.')
        self.RelativeScaleButton.setToolTip('Relative scale.')
        self.AbsoluteScaleButton.setToolTip('Absolute scale.')

        self.rangeSlider.setToolTip('Absolute scale intensity limits.')
        self.showSelectedBox.setToolTip('Visualize selected wavenumber(s).')
        self.addWidgetButton.setToolTip('Add single wavenumbre to list.')
        self.addRangeWidgetButton.setToolTip('Add wavenumber range to list.')
        self.removeWidgetButton.setToolTip('Remove single entry.')
        self.clearWidgetButton.setToolTip('Clear all.')
        self.sortOrder.setToolTip('.')
        self.sortWidgetButton .setToolTip('Sort list.')
        self.saveWidgetButton.setToolTip('Save list.')
        self.openWidgetButton.setToolTip('Import list.')
        self.SumMeanButton.setToolTip('Generate mean IR image from list.')
        self.ShowMeanButton.setToolTip('Show mean image.')
        self.ExportMeanButton.setToolTip('Save mean IR image as .tif.')

    # import shapes from xml file
    def importpolygon_pressed(self):
        # select xml-file for ROI import
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(None, "Select xml files", os.getcwd(),
                                                             'Files (*.xml)')

        #allow for import of multiple xml files
        ll = 0
        rr = 0
        for file in file_names:

            file_extension = os.path.splitext(file)[-1]

            if file_extension == ".xml":
                shapes, calibrationPoints, capID = xml2shape(file)

                for i, shape in enumerate(shapes):

                    #this requires some uniform notation (of course, could be solved in a different way)
                    #need more colors
                    if capID[i] == 'A':
                        threshold_yellow = [0.950, 0.950, 0.050]
                        threshold_yellow = [i * 255 for i in threshold_yellow]
                        self.color = threshold_yellow
                        region_state = 0

                    if capID[i] == 'B':
                        threshold_purple = [0.950, 0.050, 0.950]
                        threshold_purple = [i * 255 for i in threshold_purple]
                        self.color = threshold_purple
                        region_state = 1


                    if capID[i] == 'C':
                        threshold_green = [0.050, 0.850, 0.050]
                        threshold_green = [i * 255 for i in threshold_green]
                        self.color = threshold_green
                        region_state = 2

                    if capID[i] == 'D':
                        threshold_pink = [1.000, 0.400, 0.467]
                        threshold_pink = [i * 255 for i in threshold_pink]
                        self.color = threshold_pink
                        region_state = 3

                    if capID[i] == 'E':
                        threshold_blue = [0.44, 0.44, 0.88]
                        threshold_blue = [i * 255 for i in threshold_blue]
                        self.color = threshold_blue
                        region_state = 4

                    if capID[i] == 'F':
                        threshold_black = [0.050, 0.050, 0.050]
                        threshold_black = [i * 255 for i in threshold_black]
                        self.color = threshold_black
                        region_state = 5

                    lineSyleSelected = self.LineStyleCombo.currentIndex()
                    if lineSyleSelected == 0:
                        lineStyle = QtCore.Qt.SolidLine
                    elif lineSyleSelected == 1:
                        lineStyle = QtCore.Qt.DashLine
                    elif lineSyleSelected == 2:
                        lineStyle = QtCore.Qt.DotLine

                    self.polygon_item = QtWidgets.QGraphicsPolygonItem()
                    self.polygon_item.setPen(
                        QtGui.QPen(QtGui.QColor(self.color[0], self.color[1], self.color[2]), 2, lineStyle))
                    self.polygon_item.setToolTip(str(i))
                    self.PolygonShowList = append(self.PolygonShowList, self.polygon_item)
                    self.polygonList = array([[0, 0]])

                    for p in shape:
                        self.viewQV.removeItem(self.polygon_item)
                        point = [p[0] + + self.dataIR.image_Offsets[ll,0], p[1] + self.dataIR.image_Offsets[ll,1]]
                        lp = QtCore.QPointF(point[0], point[1])

                        poly = self.polygon_item.polygon()
                        poly.append(lp)
                        self.polygon_item.setPolygon(poly)
                        self.viewQV.addItem(self.polygon_item)

                        point_new = array([[p[0] + self.dataIR.image_Offsets[ll,0], p[1] + self.dataIR.image_Offsets[ll,1]]])
                        if self.polygonList[0, 0] == 0:
                            self.polygonList = point_new
                        else:
                            self.polygonList = concatenate((self.polygonList, point_new), axis=0)


                    #obtain mean spectra from masked image (needs to be speed up)
                    image_shape = (int(self.dataIR.imageStack[:, :, 0].shape[0]), int(self.dataIR.imageStack[:, :, 0].shape[1]))
                    image_polygon = polygon2mask(image_shape, self.polygonList).astype(int)

                    # self.showQVImages(new_image)
                    image_reshaped = self.dataIR.imageStack.reshape(
                        int(self.dataIR.imageStack.shape[0]) * int(self.dataIR.imageStack.shape[1]),
                        int(self.dataIR.imageStack.shape[2]))
                    mask_reshaped = image_polygon.reshape(int(image_polygon.shape[0] * image_polygon.shape[1]), 1)
                    dataHelp = image_reshaped[mask_reshaped[:, 0] != 0, 0]
                    data = zeros((dataHelp.shape[0], int(self.dataIR.imageStack.shape[2])))

                    for j in range(int(self.dataIR.imageStack.shape[2])):
                        data[:, j] = image_reshaped[mask_reshaped[:, 0] != 0, int(j)]

                    newSpectrum = mean(data[:, :], 0)

                    color = list(random.choice(range(256), size=3))

                    lineSyleSelected = self.LineStyleCombo.currentIndex()
                    if lineSyleSelected == 0:
                        lineStyle = QtCore.Qt.SolidLine
                    elif lineSyleSelected == 1:
                        lineStyle = QtCore.Qt.DashLine
                    elif lineSyleSelected == 2:
                        lineStyle = QtCore.Qt.DotLine

                    pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue), style=lineStyle)
                    plotDataNew = self.plotAbsorption.plot(x=self.dataIR.wavelength, y=newSpectrum, pen=pen)
                    self.ListOfSpectraPolygon = append(self.ListOfSpectraPolygon, plotDataNew)
                    print(rr)
                    self.ListOfSpectraPolygon[rr].setAlpha(0.0, False)


                    # add item to WidgetTree
                    elementNumber = int(len(self.polygonTreeElements))
                    child = QtWidgets.QTreeWidgetItem(self.polygonTree)
                    child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
                    child.setText(0, "RegionSpectrum {}".format(elementNumber))
                    child.setText(1, "{}".format(region_state))
                    child.setCheckState(0, QtCore.Qt.Checked)
                    child.setForeground(0, QtGui.QBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2])))
                    self.polygonTreeElements = append(self.polygonTreeElements, child)

                    rr = rr + 1
            ll = ll + 1

        self.showPolygon_pressed()

        print('done')
    # import .pickle files
    def importpickle_pressed(self):
        # select file
        self.fileName = self.OpenFile()

        print(self.fileName)

        if size(self.fileName) == 1:
            pickle_in = open(self.fileName[0], "rb")
            type_pickle = os.path.splitext(self.fileName[0])[0][-10:]
            if type_pickle == 'wavenumber':
                self.dataIR.wavelength = pickle.load(pickle_in)
                data_imported = False
            else:
                self.dataIR.imageStack = pickle.load(pickle_in)
                meanSpectrum = mean(self.dataIR.imageStack.reshape((int(
                    self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                                                     int(self.dataIR.imageStack.shape[2]))), 0)
                selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
                data_imported = True
            pickle_in.close()
            self.dataIR.image_Offsets = zeros((len(self.fileName), 2))

        print('size'+ str(size(self.fileName)))

        if size(self.fileName) >= 2 and size(self.fileName)%2 == 0:
            #split file into two classes:
            files_wavenumber = []
            files_data = []
            for ii in range(size(self.fileName)):
                type_pickle = os.path.splitext(self.fileName[ii])[0][-10:]
                if type_pickle == 'wavenumber':
                    files_wavenumber.append(self.fileName[ii])
                else:
                    files_data.append(self.fileName[ii])

            self.dataIR.image_Offsets = zeros((len(files_data), 2))

            #eigentlich müsste hier ein vgl. der listen rein....quick fix aktuell
            if len(files_wavenumber) != 0:
                pickle_in = open(files_wavenumber[0], "rb")
                self.dataIR.wavelength = pickle.load(pickle_in)
                sleep(0.1)
                pickle_in.close()
                data_imported = False
            if len(files_data) != 0 and len(files_wavenumber) != 0:
                #maybe optimize the next line
                #size_blocks = [int(sqrt(len(files_data))), int(ceil(sqrt(len(files_data))))]
                if len(files_data) == 1:
                    size_blocks = [int(1), int(1)]
                else:
                    size_blocks = [int(2), int(len(files_data)/2)]
                for jj in range(len(files_data)):

                    size_array = zeros((len(files_data), 3))
                    sub_figure_size = [0, 0]

                    ll = 0
                    for file_path in files_data:
                        # check for file sizes
                        pickle_in = open(files_data[ll], "rb")
                        imageStack = pickle.load(pickle_in)
                        # obtain meta data
                        size_array[ll, 0] = shape(imageStack)[0]
                        size_array[ll, 1] = shape(imageStack)[1]
                        size_array[ll, 2] = shape(imageStack)[2]
                        ll = ll + 1
                        sleep(0.1)
                        pickle_in.close()

                    sub_figure_size[0] = max(size_array[:, 0]).astype(int)  # y
                    sub_figure_size[1] = max(size_array[:, 1]).astype(int)  # x

                    print('size_array')
                    print(size_array[:, 0])
                    print(size_array[:, 1])

                    print('sub_figure_size')
                    print(sub_figure_size[0])
                    print(sub_figure_size[1])


                    self.dataIR.imageStack = 100 * ones(
                        (size_blocks[0] * sub_figure_size[0], size_blocks[1] * sub_figure_size[1],
                         size_array[0, 2].astype(int)))  # y,x

                    # now fill the image
                    i = 0  # x
                    j = 0  # y
                    kk = 0
                    for file_path in files_data:
                        pickle_in = open(files_data[kk], "rb")
                        imageStack = pickle.load(pickle_in)
                        image_dimensions = shape(imageStack)

                        # calculate margins left and right
                        margin_y = sub_figure_size[0] - image_dimensions[0]
                        margin_x = sub_figure_size[1] - image_dimensions[1]

                        print('Margin')
                        print(margin_y)
                        print(margin_x)

                        # ungerade/gerade ceil floor int round....check
                        self.dataIR.imageStack[j * sub_figure_size[0] + int(margin_y / 2):(j + 1) * sub_figure_size[0] - int(
                            ceil(margin_y / 2)),
                        i * sub_figure_size[1] + int(margin_x / 2):(i + 1) * sub_figure_size[1] - int(
                            ceil(margin_x / 2)), :] = imageStack.copy()

                        self.dataIR.image_Offsets[kk, 0] = j * sub_figure_size[0] + int(margin_y / 2)  #maybe -1
                        self.dataIR.image_Offsets[kk, 1] = i * sub_figure_size[1] + int(margin_x / 2)  #maybe -1

                        if j != 1:
                            j = j + 1
                        else:
                            i = i + 1
                            j = 0

                        kk = kk + 1
                        pickle_in.close()

                    meanSpectrum = mean(self.dataIR.imageStack.reshape((int(
                        self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                                                         int(self.dataIR.imageStack.shape[2]))), 0)
                    selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
                data_imported = True

            print('Offsets:')
            print(self.dataIR.image_Offsets)
            print(files_wavenumber)
            print(files_data)

        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()


        if data_imported == True:
            self.showAbsorptionSpectrum(meanSpectrum, selected_wavelength)

            image_display = self.dataIR.imageStack[:, :, selected_wavelength]
            self.showQVImages(image_display)

            self.calculateMask()
            self.clearSpectra_pressed()
        print('Done')

        self.transmittanceImage.setEnabled(True)
        self.absorbanceImage.setEnabled(True)

    def OpenFile(self):
        fileName, fileTypes = QtWidgets.QFileDialog.getOpenFileNames(None, "Select one or more files to open", os.getcwd(), 'Files (*.pickle)')
        return fileName

    # Image Pixel Positions
    def OnClick(self, event):
        position = self.imgQV.mapFromScene(event)
        posX = int((position.x()))
        posY = int((position.y()))
        printPosition = 'x:' + str(posX) + ' px, y:' + str(posY) + ' px'
        self.statusBar().showMessage(printPosition)

    #Get spectra information: single pixel or Polygon
    # Action upon left mouse click on image
    def timeout(self):
        if self.leftButton_click_count == 1:
            print('Single left click')
            self.SinglePointImage()
        elif self.leftButton_click_count > 1:
            print('Double left click')
            self.subRegionSpectraPolygonButton_pressed()
        self.leftButton_click_count = 0
    def onImageSpectra_clicked(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.leftButton_click_count += 1
            if not self.timer.isActive():
                self.timer.start()

        self.position = self.imgQV.mapFromScene(event.scenePos())
    def SinglePointImage(self):
        if self.singlePixelSpectraButton.isChecked() == True:
            if self.leftButton_click_count == 1:

                posX = int(self.position.x())
                posY = int(self.position.y())

                newSpectrum = self.dataIR.imageStack[int(posX), int(posY), :]

                self.color = list(random.choice(range(256), size=3))

                lineSyleSelected = self.LineStyleCombo.currentIndex()
                if lineSyleSelected == 0:
                    lineStyle = QtCore.Qt.SolidLine
                elif lineSyleSelected == 1:
                    lineStyle = QtCore.Qt.DashLine
                elif lineSyleSelected == 2:
                    lineStyle = QtCore.Qt.DotLine

                pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue), style=lineStyle)

                plotDataNew = self.plotAbsorption.plot(x=self.dataIR.wavelength, y=newSpectrum, pen = pen)
                self.ListOfSpectraPixel = append(self.ListOfSpectraPixel, plotDataNew)

                #add item to WidgetTree
                elementNumber = int(len(self.pixelTreeElements))
                child = QtWidgets.QTreeWidgetItem(self.pixelTree)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
                child.setText(0, "Spectrum {}".format(elementNumber))
                child.setCheckState(0, QtCore.Qt.Checked)
                child.setForeground(0, QtGui.QBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2])))
                self.pixelTreeElements = append(self.pixelTreeElements , child)

        if self.PolygonButton.isChecked() == True:
            if self.leftButton_click_count == 1:

                self.viewQV.removeItem(self.polygon_item)

                lp = self.position
                poly = self.polygon_item.polygon()
                poly.append(lp)

                points = [poly[i] for i in range(poly.size())]

                self.polygon_item.setPolygon(poly)
                polygon_help = self.polygon_item.polygon()

                numberOfPoints = int(polygon_help.size())

                for i in range(numberOfPoints):
                    point = polygon_help[i]

                path_new = self.polygon_item.shape()
                x = path_new.currentPosition().toPoint().x()
                y = path_new.currentPosition().toPoint().y()
                point = array([[x, y]])
                print(point)

                if self.polygonList[0, 0] == 0:
                   self.polygonList = point
                else:
                   self.polygonList = concatenate((self.polygonList, point), axis=0)

                self.viewQV.addItem(self.polygon_item)
    def subRegionSpectraPolygonButton_pressed(self):
        try:
            self.PolygonButton.setChecked(False)
            self.PolygonListAll = append(self.PolygonListAll, self.polygonList)

            image_shape = (int(shape(self.dataIR.imageStack[:, :, 0])[0]), int(shape(self.dataIR.imageStack[:, :, 0])[1]))
            image_polygon = polygon2mask(image_shape, self.polygonList).astype(int)

            image_reshaped = self.dataIR.imageStack.reshape(int(shape(self.dataIR.imageStack)[0] * shape(self.dataIR.imageStack)[1]), int(shape(self.dataIR.imageStack)[2]))
            mask_reshaped = image_polygon.reshape(int(shape(image_polygon)[0] * shape(image_polygon)[1]), 1)
            dataHelp = image_reshaped[mask_reshaped[:, 0] != 0, 0]
            data = zeros((shape(dataHelp)[0], int(shape(self.dataIR.imageStack)[2])))

            for i in range(int(shape(self.dataIR.imageStack)[2])):
                data[:, i] = image_reshaped[mask_reshaped[:, 0] != 0, int(i)]

            newSpectrum = mean(data[:, :], 0)

            color = list(random.choice(range(256), size=3))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue), style=lineStyle)
            plotDataNew = self.plotAbsorption.plot(x=self.dataIR.wavelength, y=newSpectrum, pen=pen)
            self.ListOfSpectraPolygon = append(self.ListOfSpectraPolygon, plotDataNew)

            # add item to WidgetTree
            elementNumber = int(len(self.polygonTreeElements))
            child = QtWidgets.QTreeWidgetItem(self.polygonTree)
            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
            child.setText(0, "RegionSpectrum {}".format(elementNumber))
            child.setText(1, "{}".format(elementNumber))
            child.setCheckState(0, QtCore.Qt.Checked)
            child.setForeground(0, QtGui.QBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2])))
            self.polygonTreeElements = append(self.polygonTreeElements, child)
        except:
            pass
    def singlePixelSpectraButton_pressed(self):
        self.PolygonButton.setChecked(False)
    def drawPolygon_pressed(self):
        self.singlePixelSpectraButton.setChecked(False)

        self.color = list(random.choice(range(256), size=3))

        if self.PolygonButton.isChecked() == True:

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            self.polygon_item = QtWidgets.QGraphicsPolygonItem()
            self.polygon_item.setPen(QtGui.QPen(QtGui.QColor(self.color[0], self.color[1], self.color[2]), 2, lineStyle))
            self.polygon_item.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2]))
            self.polygon_item.setOpacity((self.opacitySlider.value() / 100))

            if self.FillingCheckbox.isChecked() == False:
                self.polygon_item.setBrush(QtGui.QColor(QtCore.Qt.transparent))

            self.PolygonShowList = append(self.PolygonShowList, self.polygon_item)
            self.polygonList = array([[0, 0]])

    def showPolygon_pressed(self):
        for item in self.PolygonShowList:
            self.viewQV.removeItem(item)
        for item in self.PolygonShowList:
            self.viewQV.addItem(item)
    def removePolygon_pressed(self):
        if self.PolygonButton.isChecked() == True:
            self.singlePixelSpectraButton.setChecked(False)
            self.viewQV.removeItem(self.PolygonShowList[-1])
            self.PolygonButton.setChecked(False)
            self.polygonList = array([[0, 0]])
    def removeAllPolygon_pressed(self):
        self.singlePixelSpectraButton.setChecked(False)
        for item in self.PolygonShowList:
            self.viewQV.removeItem(item)
        self.PolygonButton.setChecked(False)
        self.polygonList = array([[0, 0]])

    #calculate difference spectra
    def DifferenceSpectraButton_pressed(self):
        # check for two "yes" in Pixel Tree
        counterPixel = 0
        elementNumber = []
        for i in range(len(self.ListOfSpectraPixel)):
            column = 0
            if self.pixelTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                counterPixel = counterPixel + 1
                elementNumber = append(elementNumber, i)

        print('counter Pixel: ' + str(counterPixel))

        if counterPixel == 2:
            item0 = self.ListOfSpectraPixel[int(elementNumber[0])]
            item1 = self.ListOfSpectraPixel[int(elementNumber[1])]
            itemDifference = item0.yData - item1.yData
            itemDifferenceWavelength = item0.xData

            color = list(random.choice(range(256), size=3))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=color, width=int(self.PenThicknessValue), style=lineStyle)
            plotDataNew = self.plotAbsorption.plot(x=itemDifferenceWavelength, y=itemDifference, pen=pen)
            self.ListOfSpectraDifference = append(self.ListOfSpectraDifference, plotDataNew)

            # add item to WidgetTree
            elementNumber = int(len(self.differenceTreeElements))
            child = QtWidgets.QTreeWidgetItem(self.differenceTree)
            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
            child.setText(0, "Difference {}".format(elementNumber))
            child.setCheckState(0, QtCore.Qt.Unchecked)
            child.setForeground(0, QtGui.QBrush(QtGui.QColor(color[0], color[1], color[2])))
            self.differenceTreeElements = append(self.differenceTreeElements, child)

        #check for two "yes" in Polygon Tree
        counterPolygon = 0
        elementNumber = []
        for i in range(len(self.ListOfSpectraPolygon)):
            column = 0
            if self.polygonTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                counterPolygon = counterPolygon + 1
                elementNumber = append(elementNumber, i)

        print('counter Polygon: ' + str(counterPolygon))

        if counterPolygon == 2:
            item0 = self.ListOfSpectraPolygon[int(elementNumber[0])]
            item1 = self.ListOfSpectraPolygon[int(elementNumber[1])]
            itemDifference = item0.yData - item1.yData
            itemDifferenceWavelength = item0.xData

            color = list(random.choice(range(256), size=3))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=color, width=int(self.PenThicknessValue), style=lineStyle)
            plotDataNew = self.plotAbsorption.plot(x=itemDifferenceWavelength, y=itemDifference, pen=pen)
            self.ListOfSpectraDifference = append(self.ListOfSpectraDifference, plotDataNew)

            # add item to WidgetTree
            elementNumber = int(len(self.differenceTreeElements))
            child = QtWidgets.QTreeWidgetItem(self.differenceTree)
            child.setFlags(child.flags() | QtCore.Qt.ItemIsEditable)
            child.setText(0, "Difference {}".format(elementNumber))
            child.setForeground(0, QtGui.QBrush(QtGui.QColor(color[0], color[1], color[2])))
            self.differenceTreeElements = append(self.differenceTreeElements, child)

    #export to xml file format from Leica
    def exportToXmlButton_pressed(self):

        # select folder
        folder_save = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        # here, we need to ask if the data needs to be sorted, not implemented yet
        capture_ID = []
        shapes = []

        # add Annotations to a new object that is then used for shape export to xml

        j = 0
        for element in self.PolygonShowList:
            poly = element.polygon()
            points = [poly[i] for i in range(poly.size())]


            column = 0
            if self.polygonTreeElements[j].checkState(column) == QtCore.Qt.Checked:
                path_new = element.shape()

                x = []
                y = []

                numberOfPoints = int(poly.size())
                polygonList = zeros((int(numberOfPoints), 2))

                for i in range(numberOfPoints):
                    point = QtCore.QPointF(poly[i])

                    x = append(x, round(point.x()))
                    y = append(y, round(point.y()))

                polygonList[:, 0] = x
                polygonList[:, 1] = y

                shapes.append(polygonList)

                tray = self.polygonTreeElements[j].text(1)
                #hard coded to "8" so far
                if tray == '0':
                    tray = "A"
                elif tray == '1':
                    tray = "B"
                elif tray == '2':
                    tray = "C"
                elif tray == '3':
                    tray = "D"
                elif tray == '4':
                    tray = "E"
                elif tray == '5':
                    tray = "F"
                elif tray == '6':
                    tray = "G"
                elif tray == '7':
                    tray = "h"
                elif tray == '8':
                    tray = "I"
                capture_ID.append(tray)
                print(capture_ID)

            j = j + 1

        # sorting?
        offsetShape = [0, 0]
        scalingFactor = 1
        invertFactor = array([1, 1])
        TeachingPoints = zeros((3, 2))

        shape2xml(shapes, capture_ID, TeachingPoints.astype(int), offsetShape, scalingFactor,
                      invertFactor, folderName=folder_save)

    #QTreeWidget actions
    def openMenu(self, position):
        mdlIdx = self.SpectraListTree.indexAt(position)
        if not mdlIdx.isValid():
            return
        item = self.SpectraListTree.itemFromIndex(mdlIdx)

        right_click_menu = QtWidgets.QMenu()

        if item.parent() != None:
            hide_alpha = right_click_menu.addAction(self.tr("Hide Item"))
            hide_alpha.triggered.connect(partial(self.TreeItem_Hide, item))

            show_alpha = right_click_menu.addAction(self.tr("Show Item"))
            show_alpha.triggered.connect(partial(self.TreeItem_Show, item))

            act_del = right_click_menu.addAction(self.tr("Delete Item"))
            act_del.triggered.connect(partial(self.TreeItem_Delete, item))

            act_del = right_click_menu.addAction(self.tr("Change Color"))
            act_del.triggered.connect(partial(self.TreeItem_ChangeColor, item))

        right_click_menu.exec_(self.sender().viewport().mapToGlobal(position))
    # Function to Delete item
    def TreeItem_Delete(self, item):

        index = self.pixelTree.indexOfChild(item)
        if index != -1:
            self.pixelTree.takeChild(index)
            self.pixelTreeElements = delete(self.pixelTreeElements, index)
            self.plotAbsorption.removeItem(self.ListOfSpectraPixel[index])
            self.ListOfSpectraPixel = delete(self.ListOfSpectraPixel, index)
        else:
            index = self.polygonTree.indexOfChild(item)
            if index != -1:
                self.polygonTree.takeChild(index)
                self.polygonTreeElements = delete(self.polygonTreeElements, index)
                self.plotAbsorption.removeItem(self.ListOfSpectraPolygon[index])
                self.ListOfSpectraPolygon = delete(self.ListOfSpectraPolygon, index)

                print(self.PolygonShowList)
                self.viewQV.removeItem(self.PolygonShowList[index])
                self.PolygonShowList = delete(self.PolygonShowList, index)
                print(index)
                print(self.PolygonShowList)
            else:
                index = self.differenceTree.indexOfChild(item)
                if index != -1:
                    self.differenceTree.takeChild(index)
                    self.differenceTreeElements = delete(self.differenceTreeElements, index)
                    self.plotAbsorption.removeItem(self.ListOfSpectraDifference[index])
                    self.ListOfSpectraDifference = delete(self.ListOfSpectraDifference, index)
    def TreeItem_Hide(self, item):
        index = self.pixelTree.indexOfChild(item)
        if index != -1:
            self.ListOfSpectraPixel[index].setAlpha(0.0, False)
        else:
            index = self.polygonTree.indexOfChild(item)
            if index != -1:
                self.ListOfSpectraPolygon[index].setAlpha(0.0, False)
            else:
                index = self.differenceTree.indexOfChild(item)
                if index != -1:
                    self.ListOfSpectraDifference[index].setAlpha(0.0, False)
    def TreeItem_Show(self, item):
        index = self.pixelTree.indexOfChild(item)
        if index != -1:
            self.ListOfSpectraPixel[index].setAlpha(1.0, False)
        else:
            index = self.polygonTree.indexOfChild(item)
            if index != -1:
                self.ListOfSpectraPolygon[index].setAlpha(1.0, False)
            else:
                index = self.differenceTree.indexOfChild(item)
                if index != -1:
                    self.ListOfSpectraDifference[index].setAlpha(1.0, False)
    def clearSpectra_pressed(self):
        self.removeAllPolygon_pressed()
        self.PolygonShowList = []
        for i in range(len(self.ListOfSpectraPixel)):
            j = len(self.ListOfSpectraPixel)-i-1
            print(j)
            self.plotAbsorption.removeItem(self.ListOfSpectraPixel[j])
            self.pixelTree.takeChild(j)
            self.pixelTreeElements = delete(self.pixelTreeElements, j)
        self.ListOfSpectraPixel = []

        for i in range(len(self.ListOfSpectraPolygon)):
            j = len(self.ListOfSpectraPolygon) - i - 1
            self.polygonTree.takeChild(j)
            self.plotAbsorption.removeItem(self.ListOfSpectraPolygon[j])
            self.polygonTreeElements = delete(self.polygonTreeElements, j)
        self.ListOfSpectraPolygon = []
        for i in range(len(self.ListOfSpectraDifference)):
            j = len(self.ListOfSpectraDifference) - i - 1
            self.differenceTree.takeChild(j)
            self.plotAbsorption.removeItem(self.ListOfSpectraDifference[j])
            self.differenceTreeElements = delete(self.differenceTreeElements, j)
        self.ListOfSpectraDifference = []

    #functions related to list widget
    def addWidgetButton_pressed(self):
        number = "{0:0=4d}".format(int(self.currentWavenumber))
        self.listWidget.addItem(number)

        self.generateItemList()
        self.showSelectedWavenumbers()
    def addRangeWidgetButton_pressed(self):
        region = self.regionLine.getRegion()
        inputString = str(int(region[0])) + ' - ' + str(int(region[1]))
        print(inputString)
        self.listWidget.addItem(inputString)

        self.generateItemList()
        self.showSelectedWavenumbers()
    def clearWidgetButton_pressed(self):
        self.listWidget.clear()

        self.generateItemList()
        self.showSelectedWavenumbers()
    def sortWidgetButton_pressed(self):
        if self.sortOrder.isChecked():
            order = QtCore.Qt.AscendingOrder
        else:
            order = QtCore.Qt.DescendingOrder

        self.listWidget.sortItems(order)

        self.generateItemList()
    def removeWidgetButton_pressed(self):
        self.listWidget.takeItem(self.listWidget.currentRow())

        self.generateItemList()
        self.showSelectedWavenumbers()
    def saveWidgetButton_pressed(self):
        itemsTextList =  [str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())]

        fileName, fileType = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '', 'Files (*.txt)')
        print(fileName)
        file = open(fileName, "w")
        file.writelines(["%s\n" % item  for item in itemsTextList])
        file.close()
    def openWidgetButton_pressed(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "Select a file", os.getcwd(),
                                                               'Files (*.txt)')
        with open(fileName, "r") as file:
            lines = file.read().splitlines()
        file.close()
        self.clearWidgetButton_pressed()
        for item in lines:
            self.listWidget.addItem(item)

        self.generateItemList()
        self.showSelectedWavenumbers()
    def generateItemList(self):
        list = [str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())]

        self.selectedWavenumberList = []

        for item in list:
            x = item.split(' - ')
            if len(x) == 1:
                self.selectedWavenumberList = append(self.selectedWavenumberList, int(x[0]))
            else:
                wavenumberSteps = abs(self.dataIR.wavelength[0] - self.dataIR.wavelength[1])

                list = arange(int(x[0]), int(x[1]) + wavenumberSteps, wavenumberSteps)

                self.selectedWavenumberList = append(self.selectedWavenumberList, list)

        #sort array
        self.selectedWavenumberList = sort(self.selectedWavenumberList)
        #remove same elements
        self.selectedWavenumberList = unique(self.selectedWavenumberList.astype('int'))

        self.selectedWavenumberListPosition = zeros((len(self.selectedWavenumberList)))
        j = 0
        for i in self.selectedWavenumberList:
            self.selectedWavenumberListPosition[j] = int(abs(self.dataIR.wavelength - int(i)).argmin())
            j=j+1


        self.selectedimageStack = self.dataIR.imageStack[:, : ,self.selectedWavenumberListPosition.astype('int')]

        print(shape(self.selectedimageStack))
    def double_click_pressed(self):
        current_item = self.listWidget.currentItem().text()

        x = current_item.split(' - ')
        if len(x) == 1:
            lineWavenumber = int(current_item)
            self.line.setValue(lineWavenumber)
            selected_wavelength = int(abs(self.dataIR.wavelength - int(lineWavenumber)).argmin())

            self.printWavenumber(self.dataIR.wavelength[selected_wavelength])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        else:
            lineWavenumber = int(x[0])
            self.regionLine.setRegion([int(x[0]), int(x[1])])
            selected_wavelength = int(abs(self.dataIR.wavelength - int(lineWavenumber)).argmin())

            self.printWavenumber(self.dataIR.wavelength[selected_wavelength])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def showSelectedWavenumbers(self):

        if self.showSelectedBox.isChecked() == True:

            try:
                for i in range(len(self.ListOfLines)):
                    self.plotAbsorption.removeItem(self.ListOfLines[i])
                for i in range(len(self.ListOfRanges)):
                    self.plotAbsorption.removeItem(self.ListOfRanges[i])
            except:
                pass
            list = [str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())]

            self.ListOfLines = []
            self.ListOfRanges = []

            i = 0
            for item in list:
                x = item.split(' - ')
                if len(x) == 1:
                    lineRed = pg.InfiniteLine(pos=int(x[0]), angle=90, pen=pg.mkPen('r', width=1,
                                                                                               style=QtCore.Qt.DashLine),
                                                   movable=False)

                    self.plotAbsorption.addItem(lineRed)
                    self.ListOfLines.append(lineRed)
                    i = i + 1
                else:
                    regionLineRed = pg.LinearRegionItem([int(x[0]), int(x[1])], brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 30)), pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine), movable=False)
                    self.plotRegionLine = self.plotAbsorption.addItem(regionLineRed)
                    self.ListOfRanges.append(regionLineRed)

        else:
            pass
    def showToggle(self):
        if self.showSelectedBox.isChecked() == True:
            self.showSelectedWavenumbers()
        else:
            try:
                for i in range(len(self.ListOfLines)):
                    self.plotAbsorption.removeItem(self.ListOfLines[i])
                for i in range(len(self.ListOfRanges)):
                    self.plotAbsorption.removeItem(self.ListOfRanges[i])
            except:
                pass

    #show spectra
    def on_ColormapComboBox_changed(self):
        if self.QVShowButton.isChecked() == True:
            selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())

            self.printWavenumber(self.dataIR.wavelength[selected_wavelength])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])
        elif self.MaskShowButton.isChecked() == True:
            self.showQVImages(self.image_mask)
        elif self.ShowMeanButton.isChecked() == True:
            self.showQVImages(self.image_difference)

    def showQVImages(self, image_IR):
        maxlut = 255
        maxScale = 260

        color_value = self.ColormapComboBox.currentIndex()
        if color_value == 0:
            color_name = 'gray'
        elif color_value == 1:
            color_name = 'binary'
        elif color_value == 2:
            color_name = 'gist_ncar_r'
        elif color_value == 3:
            color_name = 'inferno'
        elif color_value == 4:
            color_name = 'PiYG'
        elif color_value == 5:
            color_name = 'viridis'
        elif color_value == 6:
            color_name = 'cividis'
        elif color_value == 7:
            color_name = 'plasma'

        colormap = cm.get_cmap(color_name)
        colormap._init()
        lut = (colormap._lut * maxlut).view(ndarray)

        if self.AbsoluteScaleButton.isChecked() == True:
            min = self.minInt+(self.maxInt-self.minInt)*(self.sliderlow/100)
            max = self.maxInt-(self.maxInt-self.minInt)*(1-self.sliderhigh/100)
            image_IR = (exposure.rescale_intensity(image_IR, in_range=(min, max), out_range=(0, 255))).astype('uint8')
        elif self.RelativeScaleButton.isChecked() == True:
            image_IR = (exposure.rescale_intensity(image_IR, out_range=(0, 255))).astype('uint8')

        if self.pressedYesNo == True:
            image_IR[self.image_mask[:, :] != 1] = 0
        else:
            pass

        self.viewQV.removeItem(self.imgQV)
        self.viewQV.addItem(self.imgQV)
        self.imgQV.setImage(image_IR)

        yMax = image_IR.shape[1]
        xMax = image_IR.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewQV.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.viewQV.autoRange(padding=0)
        self.imgQV.setLookupTable(lut)
        self.imgQV.setLevels([0, maxScale])

        try:
            self.showPolygon_pressed()
        except:
            pass
    def showAbsorptionSpectrum(self, spectrum, selected_wavelength):
        self.plotAbsorption.clear()
        self.plotData = self.plotAbsorption.plot(x=self.dataIR.wavelength, y=spectrum)

        self.line = pg.InfiniteLine(pos=int(self.dataIR.wavelength.min()), angle=90, movable=True)
        self.plotLine = self.plotAbsorption.addItem(self.line)
        self.line.setBounds([self.dataIR.wavelength.min(), self.dataIR.wavelength.max()])
        self.line.sigPositionChangeFinished.connect(self.line_obtainPosition)
        self.line.setValue(int(self.dataIR.wavelength[selected_wavelength]))

        center = int((self.dataIR.wavelength.max() + self.dataIR.wavelength.min()) / 2)
        centerPM = 50
        self.regionLine = pg.LinearRegionItem([center - centerPM, center + centerPM],
                                              bounds=[self.dataIR.wavelength.min(), self.dataIR.wavelength.max()],
                                              movable=True)
        self.plotRegionLine = self.plotAbsorption.addItem(self.regionLine)
    def hideMean_pressed(self):
        if self.HideMeanButton.isChecked() == True:
            self.plotData.setAlpha(0.0, False)
        else:
            self.plotData.setAlpha(1.0, False)

    def AbsoluteScaleButton_pressed(self):
        self.AbsoluteScaleButton.setChecked(True)
        self.RelativeScaleButton.setChecked(False)

        self.on_ColormapComboBox_changed()
    def RelativeScaleButton_pressed(self):
        self.AbsoluteScaleButton.setChecked(False)
        self.RelativeScaleButton.setChecked(True)

        self.on_ColormapComboBox_changed()
    def rangeSlider_moved(self):
        self.sliderlow = self.rangeSlider.low()
        self.sliderhigh = self.rangeSlider.high()
        self.on_ColormapComboBox_changed()


    #Change Color
    def TreeItem_ChangeColor(self, item):
        i = 0
        threshold_green = [0.050, 0.850, 0.050]
        threshold_red = [0.890, 0.050, 0.050]
        threshold_yellow = [0.950, 0.950, 0.050]
        threshold_black = [0.050, 0.050, 0.050]
        threshold_pink = [1.000, 0.400, 0.467]
        threshold_hellrosa = [1.000, 0.670, 0.67059]
        threshold_rosa = [1.000, 0.231, 0.525]
        threshold_blue = [0.44, 0.44, 0.88]
        threshold_orange = [1.000, 0.784, 0.000]

        threshold_yellow_ImSc = [0.950, 0.950, 0.050]
        threshold_Black_ImSc = [0.250, 0.050, 0.25]
        threshold_Cyan_ImSc = [0.050, 0.950, 0.950]
        threshold_Purple_ImSc = [0.950, 0.050, 0.950]
        threshold_Brown_ImSc = [0.500, 0.050, 0.050]
        threshold_Grey_ImSc = [0.750, 0.750, 0.750]
        threshold_DarkGreen_ImSc = [0.050, 0.50, 0.050]
        threshold_LightGreen_ImSc = [0.663, 0.819, 0.556]

        color_selected = self.AnnotationCombo.currentIndex()
        if color_selected == 0:
            threshold_red = [i * 255 for i in threshold_red]
            self.color = threshold_red
        elif color_selected == 10:
            threshold_black = [i * 255 for i in threshold_black]
            self.color = threshold_black
        elif color_selected == 4:
            threshold_green = [i * 255 for i in threshold_green]
            self.color = threshold_green
        elif color_selected == 7:
            threshold_yellow = [i * 255 for i in threshold_yellow]
            self.color = threshold_yellow
        elif color_selected == 1:
            threshold_pink = [i * 255 for i in threshold_pink]
            self.color = threshold_pink
        elif color_selected == 2:
            threshold_rosa = [i * 255 for i in threshold_rosa]
            self.color = threshold_rosa
        elif color_selected == 3:
            threshold_hellrosa = [i * 255 for i in threshold_hellrosa]
            self.color = threshold_hellrosa
        elif color_selected == 14:
            threshold_blue = [i * 255 for i in threshold_blue]
            self.color = threshold_blue
        elif color_selected == 8:
            threshold_orange = [i * 255 for i in threshold_orange]
            self.color = threshold_orange
        elif color_selected == 9:
            threshold_yellow_ImSc = [i * 255 for i in threshold_yellow_ImSc]
            self.color = threshold_yellow_ImSc
        elif color_selected == 12:
            threshold_Black_ImSc = [i * 255 for i in threshold_Black_ImSc]
            self.color = threshold_Black_ImSc
        elif color_selected == 15:
            threshold_Cyan_ImSc = [i * 255 for i in threshold_Cyan_ImSc]
            self.color = threshold_Cyan_ImSc
        elif color_selected == 16:
            threshold_Purple_ImSc = [i * 255 for i in threshold_Purple_ImSc]
            self.color = threshold_Purple_ImSc
        elif color_selected == 13:
            threshold_Brown_ImSc = [i * 255 for i in threshold_Brown_ImSc]
            self.color = threshold_Brown_ImSc
        elif color_selected == 11:
            threshold_Grey_ImSc = [i * 255 for i in threshold_Grey_ImSc]
            self.color = threshold_Grey_ImSc
        elif color_selected == 5:
            threshold_DarkGreen_ImSc = [i * 255 for i in threshold_DarkGreen_ImSc]
            self.color = threshold_DarkGreen_ImSc
        elif color_selected == 6:
            threshold_LightGreen_ImSc = [i * 255 for i in threshold_LightGreen_ImSc]
            self.color = threshold_LightGreen_ImSc

        index = self.pixelTree.indexOfChild(item)
        if index != -1:
            child = self.pixelTree.child(index)
            child.setForeground(0, QtGui.QBrush(
                QtGui.QColor(self.color[0], self.color[1], self.color[2])))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue),style = lineStyle)
            self.ListOfSpectraPixel[index].setPen(pen)

        index = self.polygonTree.indexOfChild(item)
        if index != -1:
            child = self.polygonTree.child(index)
            child.setForeground(0, QtGui.QBrush(
                QtGui.QColor(self.color[0], self.color[1], self.color[2])))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue), style=lineStyle)
            self.ListOfSpectraPolygon[index].setPen(pen)
            self.PolygonShowList[index].setPen(pen)

            self.PolygonShowList[index].setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2]))
            self.PolygonShowList[index].setOpacity((self.opacitySlider.value() / 100))

            if self.FillingCheckbox.isChecked() == False:
                self.PolygonShowList[index].setBrush(QtGui.QColor(QtCore.Qt.transparent))

        index = self.differenceTree.indexOfChild(item)
        if index != -1:
            child = self.differenceTree.child(index)
            child.setForeground(0, QtGui.QBrush(
                QtGui.QColor(self.color[0], self.color[1], self.color[2])))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue), style = lineStyle)
            self.ListOfSpectraDifference[index].setPen(pen)

    def opacitySlider_changed(self):
        if len(self.PolygonShowList) != 0:
            for item in self.PolygonShowList:
                color = item.pen().color().getRgb()

                lineSyleSelected = self.LineStyleCombo.currentIndex()
                if lineSyleSelected == 0:
                    lineStyle = QtCore.Qt.SolidLine
                elif lineSyleSelected == 1:
                    lineStyle = QtCore.Qt.DashLine
                elif lineSyleSelected == 2:
                    lineStyle = QtCore.Qt.DotLine

                pen = pg.mkPen(color=color, width=int(self.PenThicknessValue), style = lineStyle)
                item.setPen(pen)

                item.setBrush(QtGui.QColor(color[0], color[1], color[2]))
                item.setOpacity((self.opacitySlider.value() / 100))

                if self.FillingCheckbox.isChecked() == False:
                    item.setBrush(QtGui.QColor(QtCore.Qt.transparent))


    #display current wavenumber etc.
    def printWavenumber(self, wavenumber):
        self.currentWavenumber = str(int(wavenumber))
        self.currentWavenumberInput.clear()
        self.currentWavenumberInput.setPlaceholderText(str(self.currentWavenumber))
    def nextRight_pressed(self):
        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        if selected_wavelength > 0:
            selected_wavelength = selected_wavelength - 1
            print('Selected wavelength: ', self.dataIR.wavelength[selected_wavelength], 'Element number: ', selected_wavelength)
            self.printWavenumber(self.dataIR.wavelength[selected_wavelength])
            print('show_1')
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])
            print('show_2')
            self.line.setValue(int(self.dataIR.wavelength[selected_wavelength]))

            self.QVShowButton.setChecked(True)
            self.MaskShowButton.setChecked(False)
            self.ShowMeanButton.setChecked(False)
    def nextLeft_pressed(self):
        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        if selected_wavelength < len(self.dataIR.wavelength)-1:
            selected_wavelength = selected_wavelength + 1
            print('Selected wavelength: ', self.dataIR.wavelength[selected_wavelength], 'Element number: ',
                selected_wavelength)
            self.printWavenumber(self.dataIR.wavelength[selected_wavelength])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])
            self.line.setValue(int(self.dataIR.wavelength[selected_wavelength]))

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    # override the key press event
    def keyPressEvent(self, event):

        # if left arrow key is pressed
        if event.key() == QtCore.Qt.Key_Left:
            self.nextLeft_pressed()
        # if right arrow key is pressed
        elif event.key() == QtCore.Qt.Key_Right:
            self.nextRight_pressed()

    def line_obtainPosition(self):
        lineWavenumber = int(self.line.value())
        selected_wavelength = int(abs(self.dataIR.wavelength - int(lineWavenumber)).argmin())

        self.printWavenumber(self.dataIR.wavelength[selected_wavelength])
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)

    #switch between displayed images
    def QVShow_pressed(self):
        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
        # display QV image
        self.ColormapComboBox.setCurrentIndex(0)
        self.on_ColormapComboBox_changed()
    def maskShow_pressed(self):
        self.QVShowButton.setChecked(False)
        self.MaskShowButton.setChecked(True)
        self.ShowMeanButton.setChecked(False)
        self.ColormapComboBox.setCurrentIndex(0)
        # display mask
        self.on_ColormapComboBox_changed()
    def ShowMeanButton_pressed(self):
        self.QVShowButton.setChecked(False)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(True)
        self.ColormapComboBox.setCurrentIndex(0)
        self.on_ColormapComboBox_changed()

    def ExportMeanButton_pressed(self):
        folder_save = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        now = datetime.now()  # current date and time
        date_time = now.strftime("%d%m%Y_%H%M%S")

        fileName_out = folder_save + "/Image_" + date_time + ".tif"
        fileName_out_mask = folder_save + "/Mask_" + date_time + ".tif"
        out_image = (exposure.rescale_intensity(self.image_difference, out_range=(0, 255))).astype('uint8')
        out_mask = (exposure.rescale_intensity(self.image_mask, out_range=(0, 255))).astype('uint8')

        tifffile.imwrite(fileName_out, out_image) #, photometric='rgb'
        tifffile.imwrite(fileName_out_mask, out_mask)  # , photometric='rgb'

    def SumMeanButton_pressed(self):
        if len(self.selectedWavenumberList) >= 1:
            print(self.selectedWavenumberListPosition.astype('int'))
            self.image_difference = sum(
                self.dataIR.imageStack[:, :, self.selectedWavenumberListPosition.astype('int')], axis=2)/(len(self.selectedWavenumberListPosition))

            self.QVShowButton.setChecked(False)
            self.MaskShowButton.setChecked(False)
            self.ShowMeanButton.setChecked(True)

            self.ColormapComboBox.setCurrentIndex(0)
            self.on_ColormapComboBox_changed()
        else:
            print('no image selected')

    def maskList_pressed(self):
        #calculate masked image based on given mass list
        try:
            mean_spectra = (mean(self.selectedimageStack, 2))
            classif_GMM = GaussianMixture(n_components=2)
            classif_GMM.fit(mean_spectra.reshape((mean_spectra.size, 1)))
            thresh_mean = mean(classif_GMM.means_)
            self.image_mask = mean_spectra < thresh_mean
            self.image_mask_help = self.image_mask.copy()
        except:
            pass
    def maskInvert_pressed(self):
        #calculate masked image based on given mass list
        try:
            self.QVShowButton.setChecked(False)
            self.MaskShowButton.setChecked(True)
            self.ShowMeanButton.setChecked(False)
            self.image_mask = (exposure.rescale_intensity(self.image_mask, out_range=(1, 0))).astype('uint8')
            self.image_mask_help = self.image_mask.copy()
            self.ColormapComboBox.setCurrentIndex(0)
            self.on_ColormapComboBox_changed()
        except:
            pass
    def maskApply_pressed(self):
        if self.pressedYesNo == False:
            self.pressedYesNo = True
        else:
            self.pressedYesNo = False
        self.on_ColormapComboBox_changed()

    def to_pickle(self):
        #export infrared data stack and wavenumber list to pickle file format
        now = datetime.now()
        dt_string = now.strftime("%d%m%Y_%H_%M_%S")
        file_name_export = dt_string + '_image' + '.pickle'
        pickle_out = open(file_name_export,"wb")
        pickle.dump(self.dataIR.imageStack, pickle_out)
        pickle_out.close()

        file_name_export = dt_string + '_wavenumber' + '.pickle'
        pickle_out = open(file_name_export, "wb")
        pickle.dump(self.dataIR.wavelength, pickle_out)
        pickle_out.close()

        self.statusBar().showMessage("Export done.")

        print('Done')

        if True:
            self.X = []
            self.Y = []
            # check for "cheked" in Pixel Tree Polygon Items
            imageLabels = zeros((int(shape(self.dataIR.imageStack[:, :, 0])[0]), int(shape(self.dataIR.imageStack[:, :, 0])[1])))

            # xy pixel
            y_list = zeros((int(shape(self.dataIR.imageStack[:, :, 0])[0])*int(shape(self.dataIR.imageStack[:, :, 0])[1])))
            x_list = zeros(
                (int(shape(self.dataIR.imageStack[:, :, 0])[0]) * int(shape(self.dataIR.imageStack[:, :, 0])[1])))
            for ii in range(int(shape(self.dataIR.imageStack[:, :, 0])[1])):
                for jj in range(int(shape(self.dataIR.imageStack[:, :, 0])[0])):
                    y_list[ii + jj * int(shape(self.dataIR.imageStack[:, :, 0])[1])] = int(jj+1)
                    x_list[ii + jj * int(shape(self.dataIR.imageStack[:, :, 0])[1])] = int(ii + 1)
            j = 0
            for element in self.PolygonShowList:
                print(j)
                column = 0
                if self.polygonTreeElements[j].checkState(column) == QtCore.Qt.Checked:
                    polygon_help = element.polygon()
                    x = []
                    y = []

                    numberOfPoints = int(polygon_help.size())
                    polygonList = zeros((int(numberOfPoints), 2))

                    print('Number of Points:' + str(numberOfPoints))

                    for i in range(numberOfPoints):
                        point = polygon_help[i]
                        #ist das runden das problem oder die Datentypen unten?
                        print(point)
                        x = append(x, round(point.x()))
                        y = append(y, round(point.y()))

                    polygonList[:, 0] = x
                    polygonList[:, 1] = y

                    image_shape = (int(shape(self.dataIR.imageStack[:, :, 0])[0]), int(shape(self.dataIR.imageStack[:, :, 0])[1]))
                    image_polygon = polygon2mask(image_shape, polygonList).astype(int)

                    image_polygon = (exposure.rescale_intensity(image_polygon, out_range=(0, 1))).astype('uint8')

                    value = int(self.polygonTreeElements[j].text(1)) + 1
                    image_polygon[image_polygon == 1] = int(value)

                    imageLabels = imageLabels + image_polygon
                    imageLabels[imageLabels > int(value)] = 0

                else:
                    print('Element ', str(j), ' not selected.')

                j = j + 1

            #add export to xlsx
            now = datetime.now()
            dt_string = now.strftime("%d%m%Y_%H_%M_%S")
            file_name_export = dt_string + '_' + str(int(shape(self.dataIR.imageStack)[0])) + '_' + str(shape(self.dataIR.imageStack)[1]) + '.pickle'

            image_reshaped = self.dataIR.imageStack.reshape(
                int(shape(self.dataIR.imageStack)[0] * shape(self.dataIR.imageStack)[1]),
                int(shape(self.dataIR.imageStack)[2]))

            imageLabels_reshaped = imageLabels.reshape(int(shape(self.dataIR.imageStack)[0] * shape(self.dataIR.imageStack)[1]),1)

            dataFrame_excel = DataFrame(image_reshaped, columns=self.dataIR.wavelength)
            dataFrame_excel['labels'] = imageLabels_reshaped
            dataFrame_excel['x'] = x_list
            dataFrame_excel['y'] = y_list
            dataFrame_excel.to_pickle(file_name_export)
            print(dataFrame_excel)
            self.statusBar().showMessage("Export done.")

    #image modifications
    def rotateLeft_pressed(self):
        self.dataIR.imageStack = rotate(self.dataIR.imageStack, 90, resize=True)
        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        self.image_mask = rotate(self.image_mask, 90, resize=True)
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = rotate(self.image_difference, 90, resize=True)

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def rotateRight_pressed(self):
        self.dataIR.imageStack = rotate(self.dataIR.imageStack, -90, resize=True)
        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        self.image_mask = rotate(self.image_mask, -90, resize=True)
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = rotate(self.image_difference, -90, resize=True)

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def invertX_pressed(self):
        self.dataIR.imageStack = self.dataIR.imageStack[::-1, :, :]
        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        self.image_mask = self.image_mask[::-1, :].copy()
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = self.image_difference[::-1, :].copy()

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def invertY_pressed(self):
        self.dataIR.imageStack = self.dataIR.imageStack[:, ::-1, :]
        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        self.image_mask = self.image_mask[:, ::-1].copy()
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = self.image_difference[:, ::-1].copy()

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)

    def PenThickness_Enter(self):
        self.PenThicknessValue = self.PenThicknessInput.text()
        self.PenThicknessInput.clear()
        self.PenThicknessInput.setPlaceholderText(str(self.PenThicknessValue))

    def calc_absorbance_pressed(self):
        #translate transmittance to absorbance
        self.dataIR.imageStack = -log10(self.dataIR.imageStack/100)

        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        meanSpectrum = mean(
            self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                             int(self.dataIR.imageStack.shape[2]))), 0)

        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()

        self.showAbsorptionSpectrum(meanSpectrum, selected_wavelength)

        self.clearSpectra_pressed()

        self.absorbanceImage.setEnabled(False)
        self.transmittanceImage.setEnabled(True)
    def calc_transmittance_pressed(self):
        # translate transmittance to absorbance
        self.dataIR.imageStack = 100*(10**(-(self.dataIR.imageStack)))


        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        meanSpectrum = mean(
            self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                             int(self.dataIR.imageStack.shape[2]))), 0)
        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()

        self.showAbsorptionSpectrum(meanSpectrum, selected_wavelength)

        #self.calculateMask()
        self.clearSpectra_pressed()

        self.absorbanceImage.setEnabled(True)
        self.transmittanceImage.setEnabled(False)


    #thread
    def calculateMask(self):
        # calculate image mask with pre-defined wavelength and thus mean image
        mask_wavelength = array([1080, 1552, 1660, 2924])
        selectedWavenumberListPosition = zeros((len(mask_wavelength)))
        j = 0
        for i in mask_wavelength:
            selectedWavenumberListPosition[j] = int(abs(self.dataIR.wavelength - int(i)).argmin())
            j = j + 1
        mean_spectra = (mean(self.dataIR.imageStack[:, :, selectedWavenumberListPosition.astype('int')], 2))
        classif_GMM = GaussianMixture(n_components=2)
        classif_GMM.fit(mean_spectra.reshape((mean_spectra.size, 1)))
        thresh_mean = mean(classif_GMM.means_)
        self.image_mask = mean_spectra < thresh_mean
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = zeros_like(self.image_mask)

    def resetPreProcessingButton_pressed(self):

        self.extension = os.path.splitext(self.fileName[0])[1]
        if self.extension == '.pickle':
            if size(self.fileName) == 1:
                pickle_in = open(self.fileName[0], "rb")
                type_pickle = os.path.splitext(self.fileName[0])[0][-10:]
                if type_pickle == 'wavenumber':
                    self.dataIR.wavelength = pickle.load(pickle_in)
                    data_imported = False
                else:
                    self.dataIR.imageStack = pickle.load(pickle_in)
                    meanSpectrum = mean(self.dataIR.imageStack.reshape((int(
                        self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                                                         int(self.dataIR.imageStack.shape[2]))), 0)
                    selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
                    data_imported = True
                pickle_in.close()
                self.dataIR.image_Offsets = zeros((len(self.fileName), 2))

            print('size' + str(size(self.fileName)))

            if size(self.fileName) >= 2:
                # split file into two classes:
                files_wavenumber = []
                files_data = []
                for ii in range(size(self.fileName)):
                    type_pickle = os.path.splitext(self.fileName[ii])[0][-10:]
                    if type_pickle == 'wavenumber':
                        files_wavenumber.append(self.fileName[ii])
                    else:
                        files_data.append(self.fileName[ii])

                self.dataIR.image_Offsets = zeros((len(files_data), 2))

                # eigentlich müsste hier ein vgl. der listen rein....quick fix aktuell
                if len(files_wavenumber) != 0:
                    pickle_in = open(files_wavenumber[0], "rb")
                    self.dataIR.wavelength = pickle.load(pickle_in)
                    sleep(0.1)
                    pickle_in.close()
                    data_imported = False
                if len(files_data) != 0 and len(files_wavenumber) != 0:
                    # maybe optimize the next line
                    # size_blocks = [int(sqrt(len(files_data))), int(ceil(sqrt(len(files_data))))]
                    if len(files_data) == 1:
                        size_blocks = [int(1), int(1)]
                    else:
                        size_blocks = [int(2), int(len(files_data) / 2)]
                    for jj in range(len(files_data)):

                        size_array = zeros((len(files_data), 3))
                        sub_figure_size = [0, 0]

                        ll = 0
                        for file_path in files_data:
                            # check for file sizes
                            pickle_in = open(files_data[ll], "rb")
                            imageStack = pickle.load(pickle_in)
                            # obtain meta data
                            size_array[ll, 0] = shape(imageStack)[0]
                            size_array[ll, 1] = shape(imageStack)[1]
                            size_array[ll, 2] = shape(imageStack)[2]
                            ll = ll + 1
                            sleep(0.1)
                            pickle_in.close()

                        sub_figure_size[0] = max(size_array[:, 0]).astype(int)  # y
                        sub_figure_size[1] = max(size_array[:, 1]).astype(int)  # x

                        print('size_array')
                        print(size_array[:, 0])
                        print(size_array[:, 1])

                        print('sub_figure_size')
                        print(sub_figure_size[0])
                        print(sub_figure_size[1])

                        self.dataIR.imageStack = 100 * ones(
                            (size_blocks[0] * sub_figure_size[0], size_blocks[1] * sub_figure_size[1],
                             size_array[0, 2].astype(int)))  # y,x

                        # now fill the image
                        i = 0  # x
                        j = 0  # y
                        kk = 0
                        for file_path in files_data:
                            pickle_in = open(files_data[kk], "rb")
                            imageStack = pickle.load(pickle_in)
                            image_dimensions = shape(imageStack)

                            # calculate margins left and right
                            margin_y = sub_figure_size[0] - image_dimensions[0]
                            margin_x = sub_figure_size[1] - image_dimensions[1]

                            print('Margin')
                            print(margin_y)
                            print(margin_x)

                            # ungerade/gerade ceil floor int round....check
                            self.dataIR.imageStack[
                            j * sub_figure_size[0] + int(margin_y / 2):(j + 1) * sub_figure_size[0] - int(
                                ceil(margin_y / 2)),
                            i * sub_figure_size[1] + int(margin_x / 2):(i + 1) * sub_figure_size[1] - int(
                                ceil(margin_x / 2)), :] = imageStack.copy()

                            self.dataIR.image_Offsets[kk, 0] = j * sub_figure_size[0] + int(margin_y / 2)  # maybe -1
                            self.dataIR.image_Offsets[kk, 1] = i * sub_figure_size[1] + int(margin_x / 2)  # maybe -1

                            if j != 1:
                                j = j + 1
                            else:
                                i = i + 1
                                j = 0

                            kk = kk + 1
                            pickle_in.close()

                        meanSpectrum = mean(self.dataIR.imageStack.reshape((int(
                            self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                                                             int(self.dataIR.imageStack.shape[2]))), 0)
                        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
                    data_imported = True
                print('Offsets:')
                print(self.dataIR.image_Offsets)
                print(files_wavenumber)
                print(files_data)

            if data_imported == True:
                self.showAbsorptionSpectrum(meanSpectrum, selected_wavelength)

                image_display = self.dataIR.imageStack[:, :, selected_wavelength]
                self.showQVImages(image_display)

                self.calculateMask()
                self.clearSpectra_pressed()
            print('Done')

            self.transmittanceImage.setEnabled(True)
            self.absorbanceImage.setEnabled(True)
        else:
            pass

        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()

        print('done')
    def runPreProcessingButton_pressed(self):

        if self.ASLSSettingsWindow is not None:
            self.smoothFactorValue = self.ASLSSettingsWindow.smoothFactorValue
            self.weightingFactorValue = self.ASLSSettingsWindow.weightingFactorValue
            self.iterationFactorValue = self.ASLSSettingsWindow.iterationFactorValue

        self.lam = int(self.smoothFactorValue)
        self.p = float(self.weightingFactorValue)
        self.Niter = int(self.iterationFactorValue)

        self.thread = calculationThread(self)
        self.thread.finished.connect(self.onFinished)
        self.thread.notifyProgress.connect(self.onProgress)
        self.thread.start()

        self.transmittanceImage.setEnabled(False)
        self.absorbanceImage.setEnabled(False)

    def modifyMaskButtonIR_pressed(self):

        if self.MaskSettingsWindow is not None:
            self.closing_value = int(self.MaskSettingsWindow.MaskBinaryClosingInputValueIR)
            self.object_size_remove = int(self.MaskSettingsWindow.MaskRemoveHolesObjectsInputValueIR)
            self.object_size_fill = int(self.MaskSettingsWindow.MaskRemoveSmallObjectsInputValueIR)

            image_mask_help = (exposure.rescale_intensity(self.image_mask_help, out_range=(0, 1))).astype('uint8')

            image = image_mask_help > 0.5
            if self.MaskSettingsWindow.MaskBinaryClosingCheckboxIR.isChecked() == True:
                image = binary_closing(image, disk(self.closing_value))
            if self.MaskSettingsWindow.MaskRemoveHolesObjectsCheckboxIR.isChecked() == True:
                image = remove_small_holes(image, self.object_size_remove, connectivity=1)
            if self.MaskSettingsWindow.MaskRemoveSmallObjectsCheckboxIR.isChecked() == True:
                image = remove_small_objects(image, self.object_size_fill, connectivity=1)
            self.image_mask = (exposure.rescale_intensity(image, out_range=(0, 1))).astype('uint8')

            self.ColormapComboBox.setCurrentIndex(0)
            self.on_ColormapComboBox_changed()

    def onProgress(self, i):
        self.progressBaseLine.setValue(i)
    def onFinished(self):
        if self.BaselineCheckBox.isChecked() == True:
            self.dataIR.imageStack = self.thread.data.copy()

        if self.derivativeCheckBox.isChecked() == True:
            if str(self.derivativeBox.currentText()) == '1st derivative':
                self.dataIR.imageStack = self.dataIR.Derivative(self.dataIR.imageStack, 1)
                distance = abs(self.dataIR.wavelength[0]-self.dataIR.wavelength[1])
                self.dataIR.wavelength = self.dataIR.wavelength[0:-1] - distance / 2
            elif str(self.derivativeBox.currentText()) == '2nd derivative':
                self.dataIR.imageStack = self.dataIR.Derivative(self.dataIR.imageStack, 2)
                distance = abs(self.dataIR.wavelength[0] - self.dataIR.wavelength[1])
                self.dataIR.wavelength = self.dataIR.wavelength[0:-2] - distance

        if self.NormalizationCheckBox.isChecked() == True:
            self.dataIR.imageStack = self.dataIR.SNV(self.dataIR.imageStack)

        # print data
        selected_wavelength = int(abs(self.dataIR.wavelength - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavelength])

        meanSpectrum = mean(
            self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                             int(self.dataIR.imageStack.shape[2]))), 0)
        self.showAbsorptionSpectrum(meanSpectrum, selected_wavelength)
        self.showSelectedWavenumbers()

        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()

        self.statusBar().showMessage('Pre-processing finished.')

    def BaselineSettingsButton_pressed(self):
        try:
            if self.ASLSSettingsWindow is None:
                self.ASLSSettingsWindow = ASLS_Settings_Dialog(parent=self)
                self.ASLSSettingsWindow.show()
                self.ASLSSettingsWindow.isVisible()
            elif self.ASLSSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.ASLSSettingsWindow = ASLS_Settings_Dialog(parent=self)
                self.ASLSSettingsWindow.show()
                self.ASLSSettingsWindow.isVisible()
        except:
            pass
    def MaskSettingsButton_pressed(self):
        try:
            if self.MaskSettingsWindow is None:
                self.MaskSettingsWindow = Parameters_Mask_Settings_Dialog(parent=self)
                self.MaskSettingsWindow.show()
                self.MaskSettingsWindow.isVisible()
            elif self.MaskSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.MaskSettingsWindow = Parameters_Mask_Settings_Dialog(parent=self)
                self.MaskSettingsWindow.show()
                self.MaskSettingsWindow.isVisible()
        except:
            pass

    # Define Thread and Calculation
class calculationThread(QtCore.QThread):
    notifyProgress = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        super(calculationThread, self).__init__(parent)

        self.data = parent.dataIR.imageStack.copy()
        self.lam = parent.lam
        self.p = parent.p
        self.niter = parent.Niter
        self.box = parent.BaselineCheckBox

    def run(self):
        if self.box.isChecked() == True:
            sizeX = shape(self.data)[1]
            sizeY = shape(self.data)[0]
            sizeZ = shape(self.data)[2]

            self.data = self.data.reshape(sizeX * sizeY, sizeZ)
            L = sizeZ
            D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
            D = self.lam * D.dot(D.transpose())
            w = ones(L)
            W = sparse.spdiags(w, 0, L, L)

            #hardcoded threshold for differentiation between absorbance and transmittance
            meanSpectrum = mean(mean(self.data, 0))
            if meanSpectrum > 10:
                print('transmittance baseline correction')
            else:
                print('absorbance baseline correction')

            # for ProgressBar
            for i in range(sizeX * sizeY):
                # for ProgressBar
                completed = int(100 * i / (sizeX * sizeY))
                self.notifyProgress.emit(completed)

                if meanSpectrum > 10:
                    y = 100 - self.data[i, :]
                else:
                    y = self.data[i, :]

                for it in range(self.niter):
                    W.setdiag(w)  # Do not create a new matrix, just update diagonal values
                    Z = W + D
                    z = spsolve(Z, w * y)
                    w = self.p * (y > z) + (1 - self.p) * (y < z)
                if meanSpectrum > 10:
                    self.data[i, :] = self.data[i, :] + transpose(z)
                else:
                    self.data[i, :] = self.data[i, :] - transpose(z)

            # 100 for PrograssBar
            self.notifyProgress.emit(100)
            self.data = self.data.reshape(sizeY, sizeX, sizeZ)

        print('finished')
        #self.finished.emit() #extra emit not necessary

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    EnableDarkMode(app)

    ui = QuantumView()
    ui.show()

    sys.exit(app.exec())

"""
M2iraQuant: Mannheim Mid-Infrared Analysis Quantum
M2iraQuantReg: M2ira Quant Registration
M2iraQuantView: M2ira Quant Viewer

The software part is designed as a Viewer for MIR data
Python v3.8, pyqt5

"""

#import packages
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
from numpy import array, rot90, std, diff, divide, sum, float32, array_equal, exp, linalg, sign, eye, interp, roll, column_stack, linspace, log10, size, zeros, transpose, shape, zeros_like, ones, ndarray, sort, unique, mean, random, delete, concatenate, sin, append, arange, savetxt
from datetime import datetime
from tifffile import tifffile
from pandas import DataFrame
from matplotlib.colors import LinearSegmentedColormap
import pickle
from time import sleep
from specio import specread
from math import ceil
from skimage.morphology import remove_small_objects, binary_closing, disk, remove_small_holes
import os
from matplotlib.pyplot import cm, figure, show, imshow, plot, draw
from scipy.sparse.linalg import spsolve
from scipy import sparse, signal
import skimage.exposure as exposure
from sklearn.mixture import GaussianMixture
from skimage.draw import polygon2mask
from functools import partial
from scipy.spatial import ConvexHull
from scipy.interpolate import interp1d
import zarr

#import code for shape handling
from QCL_v4.ImportShape.XML.xml2shape import xml2shape
from QCL_v4.ImportShape.XML.shape2xml import shape2xml

#import code for visualization (external)
from QCL_v4.Appearance.DarkMode import EnableDarkMode
from QCL_v4.Appearance.Range_Slider import RangeSlider

#import windows
from QCL_v4.SubWindows.ASLSBaselineSettingsWindow import ASLS_Settings_Dialog
from QCL_v4.SubWindows.ParametersImageMaskButton import Parameters_Mask_Settings_Dialog
from QCL_v4.SubWindows.ParametersDerivativeButton import Parameters_derivative_Settings_Dialog
from QCL_v4.SubWindows.MetaDataWindow import MetaData_Dialog
from QCL_v4.SubWindows.CropWindow import Crop_Dialog
from QCL_v4.SubWindows.ImportFileTypeWindow import ImportDataTypeWindow_Dialog


#define functions
def resource_path(relative_path):
    """
    Returns resource path.
    relative_path: part of the file path
    Returns: full file path with base_path being the path of the current working directory
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class RandomImageStack():
    """
    A simple class for regeneration of a random imageStack and list of wavenumbers. Class is used
    as default once M2iraQuantView is initialized.
    """
    imageStack = random.random((1001, 1001, 100))
    wavenumber = linspace(1000, 2000, 100)

class M2iraQuantView(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(M2iraQuantView, self).__init__(parent)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        #optional, set random image stack from class RandomImageStack.
        if parent == None:
            self.dataIR = RandomImageStack()
            self.minInt = self.dataIR.imageStack.min()
            self.maxInt = self.dataIR.imageStack.max()
        else:
            self.dataIR = RandomImageStack()
            self.minInt = self.dataIR.imageStack.min()
            self.maxInt = self.dataIR.imageStack.max()

        #calcualtes a masked image
        self.image_mask_help = []
        self.calculateMask()

        #used for navigation
        self.ListOfSpectraPixel = []
        self.ListOfSpectraPolygon = []
        self.ListOfSpectraDifference = []
        self.pixelTreeElements = []
        self.polygonTreeElements = []
        self.differenceTreeElements = []
        self.X = []
        self.Y = []
        self.wavenumber_names = []
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
        # Define style sheet
        self.setStyleSheet("""QToolTip { 
                                   background-color: darkGray; 
                                   color: black; 
                                   border: black solid 2px
                                   }""")

        # Define geometry of this window
        self.setGeometry(200, 200, 800, 800)
        self.setWindowTitle('M\u00B2IRA QUANT - Viewer')

        # Init statusBar
        self.statusBar().showMessage('M\u00B2IRA QUANT - Viewer v4')

        # Define grid layout
        self.centralWidgetQV = QtWidgets.QWidget(self)
        self.centralWidgetQV.setObjectName('centralWidgetQV')

        # Define main grid layout
        self.mainGridLayoutQV = QtWidgets.QGridLayout(self.centralWidgetQV)
        self.mainGridLayoutQV.setSpacing(10)

        # QV Buttons
        self.subWidgeQVButtons = QtWidgets.QWidget(self)
        self.subGridQVButtons = QtWidgets.QGridLayout(self.subWidgeQVButtons)

        textImport = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>I/O:<b></p>',
            self)

        """
        Group
        """
        # Import Button
        self.importdata = QtWidgets.QPushButton('', self)
        self.importdata.setMaximumSize(40, 40)
        self.importdata.setIcon(QtGui.QIcon(resource_path('Graphics/ImportZarr.png')))
        self.importdata.setIconSize(QtCore.QSize(30, 30))
        self.importdata.clicked.connect(self.importdata_pressed)

        # Button used to open a window for data type selection
        self.importdataType = QtWidgets.QPushButton('', self)
        self.importdataType.setMaximumSize(10, 40)
        self.importdataType.setIcon(QtGui.QIcon(resource_path('Graphics/ImportButtonLine.png')))
        self.importdataType.setIconSize(QtCore.QSize(5, 25))
        self.importdataType.clicked.connect(self.importdataType_pressed)
        self.DataTypeWindow = None

        # Button used to import polygonial regions from xml file format
        self.importpolygon = QtWidgets.QPushButton('', self)
        self.importpolygon.setMaximumSize(40, 40)
        self.importpolygon.setIcon(QtGui.QIcon(resource_path('Graphics/ImportShape2.png')))
        self.importpolygon.setIconSize(QtCore.QSize(30, 30))
        self.importpolygon.clicked.connect(self.importpolygon_pressed)

        # Button used to open a window for manuel input of meta data
        self.SetMetaData = QtWidgets.QPushButton('', self)
        self.SetMetaData.setMaximumSize(40, 40)
        self.SetMetaData.setIcon(QtGui.QIcon(resource_path('Graphics/MetaData.png')))
        self.SetMetaData.setIconSize(QtCore.QSize(30, 30))
        self.SetMetaData.clicked.connect(self.SetMetaData_pressed)
        self.MetaDataWindow = None

        # some spacer for the layout
        verticalSpacer_ButtonsNeg = QtWidgets.QSpacerItem(-5, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        verticalSpacer_Buttons = QtWidgets.QSpacerItem(60, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        # Button used to open a window with setting for image cropping
        self.CropButton = QtWidgets.QPushButton('', self)
        self.CropButton.setMaximumSize(40, 40)
        self.CropButton.setIcon(QtGui.QIcon(resource_path('Graphics/CropButton.png')))
        self.CropButton.setIconSize(QtCore.QSize(30, 30))
        self.CropButton.clicked.connect(self.CropButton_pressed)
        self.CropWindow = None

        # Button used to export image stack as .zarr file
        self.exportZarrButton = QtWidgets.QPushButton('', self)
        self.exportZarrButton.setMaximumSize(40, 40)
        self.exportZarrButton.setIcon(QtGui.QIcon(resource_path('Graphics/ExportZarr.png')))
        self.exportZarrButton.setIconSize(QtCore.QSize(30, 30))
        self.exportZarrButton.clicked.connect(self.to_zarr)

        """
        Group
        """
        # Regions of interest and spectra visualization
        textSpectra = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>ROI & Spectra:<b></p>',
            self)

        # Button used to generate a single pixel spectra
        self.singlePixelSpectraButton = QtWidgets.QPushButton('', self)
        self.singlePixelSpectraButton.setMaximumSize(40, 40)
        self.singlePixelSpectraButton.setIcon(QtGui.QIcon(resource_path('Graphics/subSpectra.png')))
        self.singlePixelSpectraButton.setIconSize(QtCore.QSize(30, 30))
        self.singlePixelSpectraButton.setCheckable(True)
        self.singlePixelSpectraButton.setChecked(False)
        self.singlePixelSpectraButton.clicked.connect(self.singlePixelSpectraButton_pressed)

        # Button used to remove spectra
        self.subRegionSpectraClearButton = QtWidgets.QPushButton('', self)
        self.subRegionSpectraClearButton.setMaximumSize(40, 40)
        self.subRegionSpectraClearButton.setIcon(QtGui.QIcon(resource_path('Graphics/subSpectraClear.png')))
        self.subRegionSpectraClearButton.setIconSize(QtCore.QSize(30, 30))
        self.subRegionSpectraClearButton.clicked.connect(self.clearSpectra_pressed)

        # Button used to draw polygonial regions of interest
        self.PolygonButton = QtWidgets.QPushButton('', self)
        self.PolygonButton.setMaximumSize(40, 40)
        self.PolygonButton.setIcon(QtGui.QIcon(resource_path('Graphics/Polygon.png')))
        self.PolygonButton.setIconSize(QtCore.QSize(30, 30))
        self.PolygonButton.clicked.connect(self.drawPolygon_pressed)
        self.PolygonButton.setCheckable(True)
        self.PolygonButton.setChecked(False)

        # Button used to remove polygonial regions of interest
        self.PolygonRemoveButton = QtWidgets.QPushButton('', self)
        self.PolygonRemoveButton.setMaximumSize(40, 40)
        self.PolygonRemoveButton.setIcon(QtGui.QIcon(resource_path('Graphics/PolygonRemove.png')))
        self.PolygonRemoveButton.setIconSize(QtCore.QSize(30, 30))
        self.PolygonRemoveButton.clicked.connect(self.removePolygon_pressed)

        # Button used to calculate the difference spectra of two selected spectra
        self.DifferenceSpectraButton = QtWidgets.QPushButton('', self)
        self.DifferenceSpectraButton.setMaximumSize(40, 40)
        self.DifferenceSpectraButton.setIcon(QtGui.QIcon(resource_path('Graphics/DifferenceButton.png')))
        self.DifferenceSpectraButton.setIconSize(QtCore.QSize(30, 30))
        self.DifferenceSpectraButton.clicked.connect(self.DifferenceSpectraButton_pressed)

        # Button used to export region of intests to file (.xml)
        self.XMLexportButton = QtWidgets.QPushButton('', self)
        self.XMLexportButton.setMaximumSize(40, 40)
        self.XMLexportButton.setIcon(QtGui.QIcon(resource_path('Graphics/ExportShape.png')))
        self.XMLexportButton.setIconSize(QtCore.QSize(30, 30))
        self.XMLexportButton.clicked.connect(self.exportToXmlButton_pressed)
        self.XMLexportButton.setEnabled(True)

        # Button used to change from transmittance to absorbance
        self.absorbanceImage = QtWidgets.QPushButton('', self)
        self.absorbanceImage.setMaximumSize(40, 40)
        self.absorbanceImage.setIcon(QtGui.QIcon(resource_path('Graphics/Absorbance_Fig.png')))
        self.absorbanceImage.setIconSize(QtCore.QSize(35, 35))
        self.absorbanceImage.clicked.connect(self.calc_absorbance_pressed)

        # Button used to change from absorbance to transmittance
        self.transmittanceImage = QtWidgets.QPushButton('', self)
        self.transmittanceImage.setMaximumSize(40, 40)
        self.transmittanceImage.setIcon(QtGui.QIcon(resource_path('Graphics/Transmittance_Fig.png')))
        self.transmittanceImage.setIconSize(QtCore.QSize(35, 35))
        self.transmittanceImage.clicked.connect(self.calc_transmittance_pressed)

        # Layout for spectra modifiction buttons
        textTransAbs = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Absorbance & Transmittance:<b></p>',
            self)
        HorizontalLayoutTransAbsSpacer = QtWidgets.QSpacerItem(207, 0, QtGui.QSizePolicy.Minimum,
                                                               QtGui.QSizePolicy.Expanding)
        HorizontalLayoutTransAbs = QtWidgets.QHBoxLayout()
        HorizontalLayoutTransAbs.addWidget(self.absorbanceImage)
        HorizontalLayoutTransAbs.addWidget(self.transmittanceImage)
        HorizontalLayoutTransAbs.addSpacerItem(HorizontalLayoutTransAbsSpacer)

        # Button used for modifying the image orientation
        textImageOrientation = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>image orientation:<b></p>',
            self)

        # Button used to rotate the image by -90 degree
        self.rotateLeft = QtWidgets.QPushButton('', self)
        self.rotateLeft.setMaximumSize(40, 40)
        self.rotateLeft.setIcon(QtGui.QIcon(resource_path('Graphics/rotateLeft2.png')))
        self.rotateLeft.setIconSize(QtCore.QSize(35, 35))
        self.rotateLeft.clicked.connect(self.rotateLeft_pressed)

        # Button used to rotate the image by 90 degree
        self.rotateRight = QtWidgets.QPushButton('', self)
        self.rotateRight.setMaximumSize(40, 40)
        self.rotateRight.setIcon(QtGui.QIcon(resource_path('Graphics/rotateRight2.png')))
        self.rotateRight.setIconSize(QtCore.QSize(35, 35))
        self.rotateRight.clicked.connect(self.rotateRight_pressed)

        # Button used to reverses the order of elements along the x-axis
        self.invertX = QtWidgets.QPushButton('', self)
        self.invertX.setMaximumSize(40, 40)
        self.invertX.setIcon(QtGui.QIcon(resource_path('Graphics/invertX.png')))
        self.invertX.setIconSize(QtCore.QSize(35, 35))
        self.invertX.clicked.connect(self.invertX_pressed)

        # Button used to reverses the order of elements along the y-axis
        self.invertY = QtWidgets.QPushButton('', self)
        self.invertY.setMaximumSize(40, 40)
        self.invertY.setIcon(QtGui.QIcon(resource_path('Graphics/invertY.png')))
        self.invertY.setIconSize(QtCore.QSize(35, 35))
        self.invertY.clicked.connect(self.invertY_pressed)

        # Layout for image manipulation buttons
        HorizontalLayoutSpacer = QtWidgets.QSpacerItem(120, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        HorizontalLayout = QtWidgets.QHBoxLayout()
        HorizontalLayout.addWidget(self.rotateLeft)
        HorizontalLayout.addWidget(self.rotateRight)
        HorizontalLayout.addWidget(self.invertX)
        HorizontalLayout.addWidget(self.invertY)
        HorizontalLayout.addSpacerItem(HorizontalLayoutSpacer)

        """
        Group
        """
        # Buttons used for pre-processing of the MIR data
        textPreProcessing = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>pre-processing:<b></p>',
            self)

        # Progress bar for the thread
        self.progressBaseLine = QtGui.QProgressBar(self)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(QtGui.QPalette.Highlight, QtCore.Qt.green)
        self.progressBaseLine.setPalette(palette)

        # Button used to re-initialize the image / currently only .zarr files
        self.resetPreProcessingButton = QtWidgets.QPushButton('', self)
        self.resetPreProcessingButton.setMaximumSize(20, 20)
        self.resetPreProcessingButton.setIcon(QtGui.QIcon(resource_path('Graphics/Reset.png')))
        self.resetPreProcessingButton.setIconSize(QtCore.QSize(10, 10))
        self.resetPreProcessingButton.clicked.connect(self.resetPreProcessingButton_pressed)

        # Button used to start pre-processing
        self.runPreProcessingButton = QtWidgets.QPushButton('', self)
        self.runPreProcessingButton.setMaximumSize(20, 20)
        self.runPreProcessingButton.setIcon(QtGui.QIcon(resource_path('Graphics/RunButton.png')))
        self.runPreProcessingButton.setIconSize(QtCore.QSize(10, 10))
        self.runPreProcessingButton.clicked.connect(self.runPreProcessingButton_pressed)

        #some spacer
        HorizontalLayoutPreProcessingSpacer = QtWidgets.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)

        # Layout for pre-processing buttons and icons
        HorizontalLayoutPreProcessing = QtWidgets.QHBoxLayout()
        HorizontalLayoutPreProcessing.addWidget(textPreProcessing)
        HorizontalLayoutPreProcessing.addSpacerItem(HorizontalLayoutPreProcessingSpacer)
        HorizontalLayoutPreProcessing.addWidget(self.progressBaseLine)
        HorizontalLayoutPreProcessing.addWidget(self.resetPreProcessingButton)
        HorizontalLayoutPreProcessing.addWidget(self.runPreProcessingButton)

        """
        Group
        """
        # Regions of Interest Visualization
        # Colors
        self.AnnotationCombo = QtWidgets.QComboBox(self)
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/red_icon.png")), "")  # red
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/pink_icon.png")), "")  # pink
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/rosa_icon.png")), "")  # rosa
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/hellrosa_icon.png")), "")  # hellrosa
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/green_icon.png")), "")  # green
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/DarkGreen_Icon.png")), "")  # DarkGreen
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/LightGreen_Icon.png")), "")  # LightGreen
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/yellow_icon.png")), "")  # yellow
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/orange_icon.png")), "")  # orange
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/yellow_ImSc_icon.png")), "")  # yellow_ImSc
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/black_icon.png")), "")  # black
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/grey_icon.png")), "")  # grey
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/black_ImSc_icon.png")), "")  # black_ImSc
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/brown_icon.png")), "")  # brown
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/blue_icon.png")), "")  # blue
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/cyan_icon.png")), "")  # cyan
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/purple_icon.png")), "")  # pruple
        self.AnnotationCombo.setIconSize(QtCore.QSize(50, 15))

        # Line style
        self.LineStyleCombo = QtWidgets.QComboBox(self)
        self.LineStyleCombo.addItem(QtGui.QIcon(resource_path("Icons/SolidLine.png")), "")  # solid
        self.LineStyleCombo.addItem(QtGui.QIcon(resource_path("Icons/DashedLine.png")), "")  # solid
        self.LineStyleCombo.addItem(QtGui.QIcon(resource_path("Icons/DottedLine.png")), "")  # solid
        self.LineStyleCombo.setIconSize(QtCore.QSize(30, 15))

        # Line thickness
        self.PenThicknessValue = '1'
        self.PenThicknessFactor = QtGui.QDoubleValidator(0, 5, 0, self)
        self.PenThicknessFactor.setLocale(self.locale())
        self.PenThicknessInput = QtWidgets.QLineEdit(self)
        self.PenThicknessInput.setMaximumSize(QtCore.QSize(30, 22))
        self.PenThicknessInput.setLocale(self.locale())
        self.PenThicknessInput.setValidator(self.PenThicknessFactor)
        self.PenThicknessInput.setPlaceholderText('1')
        self.PenThicknessInput.returnPressed.connect(self.PenThickness_Enter)

        # Opacity for the region of interest
        self.opacitySlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.opacitySlider.setRange(0, 100)
        self.opacitySlider.setSingleStep(1)
        self.opacitySlider.setValue(20)
        self.opacitySlider.setEnabled(True)
        self.opacitySlider.valueChanged.connect(self.opacitySlider_changed)

        # Set filling
        self.FillingCheckbox = QtWidgets.QCheckBox("")
        self.FillingCheckbox.setChecked(True)

        # Layout for the ROI visualization
        HorizontalLayoutShapes = QtWidgets.QHBoxLayout()
        HorizontalLayoutShapes.addWidget(self.AnnotationCombo)
        HorizontalLayoutShapes.addWidget(self.LineStyleCombo)
        HorizontalLayoutShapes.addWidget(self.PenThicknessInput)
        HorizontalLayoutShapes.addWidget(self.opacitySlider)
        HorizontalLayoutShapes.addWidget(self.FillingCheckbox)

        """
        Group
        """
        # Input for baseline correction
        textBaseline = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>baseline correction:<b></p>',
            self)

        # Type
        self.BaselineBox = QtWidgets.QComboBox(self)
        self.BaselineBox.addItem("ASLS")
        self.BaselineBox.addItem("IASLS")
        self.BaselineBox.addItem("ARPLS")
        self.BaselineBox.addItem("Rubberband")
        self.BaselineBox.addItem("Linear")

        # Active y/n
        self.BaselineCheckBox = QtWidgets.QCheckBox('', self)
        self.BaselineCheckBox.setChecked(False)

        # Button used to open a window where one can select the parameters for the baseline correction
        self.BaselineSettingsButton = QtWidgets.QPushButton('', self)
        self.BaselineSettingsButton.setMaximumSize(30, 30)
        self.BaselineSettingsButton.setIcon(QtGui.QIcon(resource_path('Graphics/SettingsButton.png')))
        self.BaselineSettingsButton.setIconSize(QtCore.QSize(15, 15))
        self.BaselineSettingsButton.clicked.connect(self.BaselineSettingsButton_pressed)
        self.BaselineSettingsWindow = None

        #initial settings for baseline correction
        self.smoothFactorValue = '100000'
        self.smoothFactorValue1 = '100000'
        self.weightingFactorValue = '0.01'
        self.iterationFactorValue = '10'

        # Layout for baseline correction
        HorizontalLayoutBaselineSpacer = QtWidgets.QSpacerItem(160, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        HorizontalLayoutBaseline = QtWidgets.QHBoxLayout()
        HorizontalLayoutBaseline.addWidget(self.BaselineCheckBox)
        HorizontalLayoutBaseline.addWidget(self.BaselineBox)
        HorizontalLayoutBaseline.addWidget(self.BaselineSettingsButton)
        HorizontalLayoutBaseline.addSpacerItem(HorizontalLayoutBaselineSpacer)

        # input for spectral differentiation
        textDerivative = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>derivative:<b></p>',
            self)

        # Type
        self.derivativeBox = QtWidgets.QComboBox(self)
        self.derivativeBox.addItem("Savitzky-Golay")
        self.derivativeBox.addItem("Linear")

        # Button used to open a window where one can select the parameters for the spectral differentiation
        self.derivativeSettingsBox = QtWidgets.QPushButton('', self)
        self.derivativeSettingsBox.setMaximumSize(30, 30)
        self.derivativeSettingsBox.setIcon(QtGui.QIcon(resource_path('Graphics/SettingsButton.png')))
        self.derivativeSettingsBox.setIconSize(QtCore.QSize(15, 15))
        self.derivativeSettingsBox.clicked.connect(self.derivativeSettings_pressed)
        self.derivativeSettingsWindow = None
        self.der_order = 1
        self.window_length = 5
        self.poly_order = 2

        # Active y/n
        self.derivativeCheckBox = QtWidgets.QCheckBox('', self)
        self.derivativeCheckBox.setChecked(False)

        # Layout for spectral differentiation
        spaceItem01 = QtWidgets.QSpacerItem(120, 10, QtWidgets.QSizePolicy.Expanding)
        HorizontalLayoutDerivative = QtWidgets.QHBoxLayout()
        HorizontalLayoutDerivative.addWidget(self.derivativeCheckBox)
        HorizontalLayoutDerivative.addWidget(self.derivativeBox)
        HorizontalLayoutDerivative.addWidget(self.derivativeSettingsBox)
        HorizontalLayoutDerivative.addSpacerItem(spaceItem01)

        # input for normalization
        textNormalization = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>normalization:<b></p>',
            self)

        # Type
        self.NormalizationBox = QtWidgets.QComboBox(self)
        self.NormalizationBox.addItem("Standard Normal Variate")
        # Active y/n
        self.NormalizationCheckBox = QtWidgets.QCheckBox('', self)
        self.NormalizationCheckBox.setChecked(False)

        # Layout for the normalization options
        spaceItem02 = QtWidgets.QSpacerItem(50, 10, QtWidgets.QSizePolicy.Expanding)
        HorizontalLayoutNormalization = QtWidgets.QHBoxLayout()
        HorizontalLayoutNormalization.addWidget(self.NormalizationCheckBox)
        HorizontalLayoutNormalization.addWidget(self.NormalizationBox)
        HorizontalLayoutNormalization.addSpacerItem(spaceItem02)

        """
        Group
        """
        # Button used to modifiy the masked image
        self.modifyMaskButtonIR = QtWidgets.QPushButton('', self)
        self.modifyMaskButtonIR.setMaximumSize(25, 25)
        self.modifyMaskButtonIR.setIcon(QtGui.QIcon(resource_path('Graphics/RunButton.png')))
        self.modifyMaskButtonIR.setIconSize(QtCore.QSize(14, 14))
        self.modifyMaskButtonIR.clicked.connect(self.modifyMaskButtonIR_pressed)

        textMask = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Mask:<b></p>',
            self)

        # Button used to generate a masekd image based on a selected list of wavenumbers
        self.MaskListButton = QtWidgets.QPushButton('', self)
        self.MaskListButton.setMaximumSize(30, 30)
        self.MaskListButton.setIcon(QtGui.QIcon(resource_path('Graphics/MaskList.png')))
        self.MaskListButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskListButton.clicked.connect(self.maskList_pressed)

        # Button used to invert the mask image
        self.MaskInvertButton = QtWidgets.QPushButton('', self)
        self.MaskInvertButton.setMaximumSize(30, 30)
        self.MaskInvertButton.setIcon(QtGui.QIcon(resource_path('Graphics/InvertMask.png')))
        self.MaskInvertButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskInvertButton.clicked.connect(self.maskInvert_pressed)

        # Button used to open a window for the selection of paramters for the generation of the image mask
        self.MaskSettingsButton = QtWidgets.QPushButton('', self)
        self.MaskSettingsButton.setMaximumSize(30, 30)
        self.MaskSettingsButton.setIcon(QtGui.QIcon(resource_path('Graphics/SettingsButton.png')))
        self.MaskSettingsButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskSettingsButton.clicked.connect(self.MaskSettingsButton_pressed)
        self.MaskSettingsWindow = None
        self.closing_value = 1
        self.object_size_remove = 200
        self.object_size_fill = 200

        # Layout for the generation of an image mask
        spaceHorizontalLayoutMaskButtons = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Expanding)
        spaceHorizontalLayoutMaskButtons1 = QtWidgets.QSpacerItem(170, 10, QtWidgets.QSizePolicy.Expanding)
        HorizontalLayoutMaskButtons = QtWidgets.QHBoxLayout()
        HorizontalLayoutMaskButtons.addWidget(self.modifyMaskButtonIR)
        HorizontalLayoutMaskButtons.addWidget(self.MaskSettingsButton)
        HorizontalLayoutMaskButtons.addSpacerItem(spaceHorizontalLayoutMaskButtons)
        HorizontalLayoutMaskButtons.addWidget(self.MaskListButton)
        HorizontalLayoutMaskButtons.addWidget(self.MaskInvertButton)
        HorizontalLayoutMaskButtons.addSpacerItem(spaceHorizontalLayoutMaskButtons1)

        # Layout for main options like import and export
        HorizontalLayoutButtons = QtWidgets.QHBoxLayout()
        HorizontalLayoutButtons.addWidget(self.importdata)
        HorizontalLayoutButtons.addSpacerItem(verticalSpacer_ButtonsNeg)
        HorizontalLayoutButtons.addWidget(self.importdataType)
        HorizontalLayoutButtons.addWidget(self.importpolygon)
        HorizontalLayoutButtons.addSpacerItem(verticalSpacer_Buttons)
        HorizontalLayoutButtons.addWidget(self.CropButton)
        HorizontalLayoutButtons.addWidget(self.SetMetaData)
        HorizontalLayoutButtons.addWidget(self.exportZarrButton)

        # A spacer
        verticalSpacer_Spectra = QtWidgets.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        # Layout for main options for regions of interest
        HorizontalLayoutSpectra = QtWidgets.QHBoxLayout()
        HorizontalLayoutSpectra.addWidget(self.singlePixelSpectraButton)
        HorizontalLayoutSpectra.addWidget(self.PolygonButton)
        HorizontalLayoutSpectra.addWidget(self.PolygonRemoveButton)
        HorizontalLayoutSpectra.addWidget(self.subRegionSpectraClearButton)
        HorizontalLayoutSpectra.addWidget(self.DifferenceSpectraButton)
        HorizontalLayoutSpectra.addSpacerItem(verticalSpacer_Spectra)
        HorizontalLayoutSpectra.addWidget(self.XMLexportButton)

        # QTreeWidgets for regions of interest
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

        # QTreeWidgets for regions of interest
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

        # Set grid layout
        self.subWidgeQVShow = QtWidgets.QWidget(self)
        self.subGridQVShow = QtWidgets.QGridLayout(self.subWidgeQVShow)

        """
        Group
        """
        # Button to select reduce the selected wavenumber by one step
        self.nextLeft = QtWidgets.QPushButton('', self)
        self.nextLeft.setMaximumSize(30, 30)
        self.nextLeft.setIcon(QtGui.QIcon(resource_path('Graphics/rotateLeft.png')))
        self.nextLeft.setIconSize(QtCore.QSize(15, 15))
        self.nextLeft.clicked.connect(self.nextLeft_pressed)

        # Button to select increase the selected wavenumber by one step
        self.nextRight = QtWidgets.QPushButton('', self)
        self.nextRight.setMaximumSize(30, 30)
        self.nextRight.setIcon(QtGui.QIcon(resource_path('Graphics/rotateRight.png')))
        self.nextRight.setIconSize(QtCore.QSize(15, 15))
        self.nextRight.clicked.connect(self.nextRight_pressed)

        # Field to visualize the active wavenumber for visualization
        self.currentWavenumber = str(int(self.dataIR.wavenumber.min()))
        self.validatorcurrentWavenumber = QtGui.QDoubleValidator(0, 5000, 0, self)
        self.validatorcurrentWavenumber.setLocale(self.locale())
        self.currentWavenumberInput = QtWidgets.QLineEdit(self)
        self.currentWavenumberInput.setLocale(self.locale())
        self.currentWavenumberInput.setValidator(self.validatorcurrentWavenumber)
        self.currentWavenumberInput.setPlaceholderText(str(self.currentWavenumber))
        #self.currentWavenumberInput.returnPressed.connect(self.PixelSizeIREnter)
        self.currentWavenumberInput.setEnabled(False)

        # Text "inverse cm"
        textinverseCM = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>inverse cm<b></p>',
            self)

        # Colormaps for the image
        self.ColormapComboBox = QtWidgets.QComboBox(self)
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/gray_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/binary_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/gist_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/inferno_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/PiYg_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/viridis_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/viridis_icon_inverted.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/cividis_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/plasma_icon.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/Reds.png")), "")
        self.ColormapComboBox.addItem(QtGui.QIcon(resource_path("Icons/Reds_Inverted.png")), "")
        self.ColormapComboBox.currentTextChanged.connect(self.on_ColormapComboBox_changed)
        self.ColormapComboBox.setIconSize(QtCore.QSize(50, 15))

        # Graphics Layout for visualization of the selected MIR image
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

        # Button to show image of selected wavenumber
        self.QVShowButton = QtWidgets.QPushButton('', self)
        self.QVShowButton.setMaximumSize(30, 30)
        self.QVShowButton.setIcon(QtGui.QIcon(resource_path('Graphics/QVButton.png')))
        self.QVShowButton.setIconSize(QtCore.QSize(15, 15))
        self.QVShowButton.setCheckable(True)
        self.QVShowButton.setChecked(True)
        self.QVShowButton.clicked.connect(self.QVShow_pressed)

        # Button to import a .tiff for an image mask
        self.MaskImportButton = QtWidgets.QPushButton('', self)
        self.MaskImportButton.setMaximumSize(30, 30)
        self.MaskImportButton.setIcon(QtGui.QIcon(resource_path('Graphics/Import_Mask.png')))
        self.MaskImportButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskImportButton.clicked.connect(self.MaskImportButton_pressed)

        # Button to show the image mask
        self.MaskShowButton = QtWidgets.QPushButton('', self)
        self.MaskShowButton.setMaximumSize(30, 30)
        self.MaskShowButton.setIcon(QtGui.QIcon(resource_path('Graphics/MaskButton.png')))
        self.MaskShowButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskShowButton.setCheckable(True)
        self.MaskShowButton.setChecked(False)
        self.MaskShowButton.clicked.connect(self.maskShow_pressed)

        # Button to apply the image mask to the MIR image
        self.MaskApplyButton = QtWidgets.QPushButton('', self)
        self.MaskApplyButton.setMaximumSize(30, 30)
        self.MaskApplyButton.setIcon(QtGui.QIcon(resource_path('Graphics/ApplyMask.png')))
        self.MaskApplyButton.setIconSize(QtCore.QSize(15, 15))
        self.MaskApplyButton.clicked.connect(self.maskApply_pressed)


        # Button set change the scale for the ion image
        self.RelativeScaleButton = QtWidgets.QPushButton('', self)
        self.RelativeScaleButton.setMaximumSize(30, 30)
        self.RelativeScaleButton.setIcon(QtGui.QIcon(resource_path('Graphics/RelativeScale.png')))
        self.RelativeScaleButton.setIconSize(QtCore.QSize(19, 19))
        self.RelativeScaleButton.clicked.connect(self.RelativeScaleButton_pressed)
        self.RelativeScaleButton.setCheckable(True)
        self.RelativeScaleButton.setChecked(True)

        # Button set change the scale for the ion image
        self.AbsoluteScaleButton = QtWidgets.QPushButton('', self)
        self.AbsoluteScaleButton.setMaximumSize(30, 30)
        self.AbsoluteScaleButton.setIcon(QtGui.QIcon(resource_path('Graphics/AbsoluteScale.png')))
        self.AbsoluteScaleButton.setIconSize(QtCore.QSize(15, 15))
        self.AbsoluteScaleButton.clicked.connect(self.AbsoluteScaleButton_pressed)
        self.AbsoluteScaleButton.setCheckable(True)
        self.AbsoluteScaleButton.setChecked(False)

        # Slider for select the intensity scaling
        self.rangeSlider = RangeSlider(QtCore.Qt.Horizontal)
        self.rangeSlider.setMinimumSize(100, 30)
        self.rangeSlider.setMinimum(0)
        self.rangeSlider.setMaximum(100)
        self.rangeSlider.setLow(0)
        self.rangeSlider.setHigh(100)
        self.rangeSlider.sliderMoved.connect(self.rangeSlider_moved)
        self.sliderlow = self.rangeSlider.low()
        self.sliderhigh = self.rangeSlider.high()

        # Button to active image corpping
        self.CropButtonYN = QtWidgets.QPushButton('', self)
        self.CropButtonYN.setMaximumSize(30, 30)
        self.CropButtonYN.setIcon(QtGui.QIcon(resource_path('Graphics/CropButton2.png')))
        self.CropButtonYN.setIconSize(QtCore.QSize(15, 15))
        self.CropButtonYN.setCheckable(True)
        self.CropButtonYN.setChecked(False)
        self.CropButtonYN.clicked.connect(self.CropButtonYN_pressed)

        # Layout for the selection of the current wavenumber
        spaceItemLayout = QtWidgets.QSpacerItem(510, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayout = QtWidgets.QHBoxLayout()
        VerticalLayout.addWidget(self.nextLeft)
        VerticalLayout.addWidget(self.nextRight)
        VerticalLayout.addWidget(self.currentWavenumberInput)
        VerticalLayout.addWidget(textinverseCM)
        VerticalLayout.addSpacerItem(spaceItemLayout)

        # Layout for the visualization of the image
        spaceItemVerticalLayoutBottom = QtWidgets.QSpacerItem(100, 10, QtWidgets.QSizePolicy.Expanding)
        spaceItemVerticalLayoutBottom2 = QtWidgets.QSpacerItem(80, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutBottom = QtWidgets.QHBoxLayout()
        VerticalLayoutBottom.addWidget(self.ColormapComboBox)
        VerticalLayoutBottom.addWidget(self.MaskImportButton)
        VerticalLayoutBottom.addWidget(self.QVShowButton)
        VerticalLayoutBottom.addWidget(self.MaskShowButton)
        VerticalLayoutBottom.addWidget(self.MaskApplyButton)
        VerticalLayoutBottom.addSpacerItem(spaceItemVerticalLayoutBottom)
        VerticalLayoutBottom.addWidget(self.RelativeScaleButton)
        VerticalLayoutBottom.addWidget(self.AbsoluteScaleButton)
        VerticalLayoutBottom.addWidget(self.rangeSlider)
        VerticalLayoutBottom.addSpacerItem(spaceItemVerticalLayoutBottom)
        VerticalLayoutBottom.addWidget(self.CropButtonYN)
        VerticalLayoutBottom.addSpacerItem(spaceItemVerticalLayoutBottom2)

        """
        Group
        """
        # Button to toggle the visualization of selected wavenumbers in the spectra view
        self.showSelectedBox = QtWidgets.QPushButton('', self)
        self.showSelectedBox.setMaximumSize(30, 30)
        self.showSelectedBox.setIcon(QtGui.QIcon(resource_path('Graphics/ShowLineButton.png')))
        self.showSelectedBox.setIconSize(QtCore.QSize(15, 15))
        self.showSelectedBox.clicked.connect(self.showToggle)
        self.showSelectedBox.setCheckable(True)
        self.showSelectedBox.setChecked(True)

        # Button to set the alpha value of the mean spectral information of the image to zero
        self.HideMeanButton = QtWidgets.QPushButton('', self)
        self.HideMeanButton.setMaximumSize(30, 30)
        self.HideMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/HideMeanButton.png')))
        self.HideMeanButton.setIconSize(QtCore.QSize(15, 15))
        self.HideMeanButton.clicked.connect(self.hideMean_pressed)
        self.HideMeanButton.setCheckable(True)
        self.HideMeanButton.setChecked(False)

        # Button to toggle the visualization of selected wavenumbers in the spectra view
        spaceVerticalLayoutTop = QtWidgets.QSpacerItem(500, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutTop = QtWidgets.QHBoxLayout()
        VerticalLayoutTop.addSpacerItem(spaceVerticalLayoutTop)
        VerticalLayoutTop.addWidget(self.showSelectedBox)
        VerticalLayoutTop.addWidget(self.HideMeanButton)

        #Layout
        spaceItemwin = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutwin = QtWidgets.QHBoxLayout()
        VerticalLayoutwin.addSpacerItem(spaceItemwin)
        VerticalLayoutwin.addWidget(self.winQV)
        VerticalLayoutwin.addSpacerItem(spaceItemwin)

        self.subGridQVShow.addLayout(VerticalLayout, 0, 0, 1, 4)
        self.subGridQVShow.addLayout(VerticalLayoutBottom, 1, 0, 1, 4)
        self.subGridQVShow.addLayout(VerticalLayoutwin, 2, 0, 4, 4)

        """
        Group
        """
        # Visualization for Spectra
        self.subWidgedQVSpectra = QtWidgets.QWidget(self)
        self.subGridQVSpectra = QtWidgets.QGridLayout(self.subWidgedQVSpectra)

        # Add graphics window
        self.plotWindow = pg.GraphicsWindow()
        self.plotWindow.setBackground(0.25)
        self.plotWindow.ci.setContentsMargins(10, 10, 10, 10)
        self.plotWindow.ci.setSpacing(0)
        self.plotWindow.addLabel('wavenumber (inverse cm)', row=1, col=1)
        self.plotWindow.addLabel('signal (arb. units)', angle=-90, row=0, col=0)
        self.plotAbsorption = self.plotWindow.addPlot(row=0, col=1)
        self.plotAbsorption.setXRange(700, 3050, padding = 0)
        meanSpectrum = mean(self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0]*self.dataIR.imageStack.shape[1]), int(self.dataIR.imageStack.shape[2]))), 0)
        self.plotData = self.plotAbsorption.plot(x=self.dataIR.wavenumber, y=meanSpectrum)
        maxSizePlotY = 200
        maxSizePlotX = 800
        self.plotWindow.setMinimumSize(maxSizePlotX, maxSizePlotY)
        self.plotWindow.setMaximumSize(maxSizePlotX, maxSizePlotY)

        # Add line for selection of current wavenumber
        self.line = pg.InfiniteLine(pos = int(self.dataIR.wavenumber.min()), angle=90, movable=True)
        self.plotLine = self.plotAbsorption.addItem(self.line)
        self.line.setBounds([self.dataIR.wavenumber.min(), self.dataIR.wavenumber.max()])
        self.line.sigPositionChangeFinished.connect(self.line_obtainPosition)
        center = int((self.dataIR.wavenumber.max()+self.dataIR.wavenumber.min())/2)
        centerPM = 50
        self.regionLine = pg.LinearRegionItem([center-centerPM, center+centerPM], bounds=[self.dataIR.wavenumber.min(), self.dataIR.wavenumber.max()], movable=True)
        self.plotRegionLine = self.plotAbsorption.addItem(self.regionLine)

        # Layout
        self.subGridQVSpectra.addLayout(VerticalLayoutTop, 0, 0)
        self.subGridQVSpectra.addWidget(self.plotWindow, 1, 0)

        # QV SpectraButtons
        self.subWidgedQVSpectraButtons = QtWidgets.QWidget(self)
        self.subGridQVSpectraButtons = QtWidgets.QGridLayout(self.subWidgedQVSpectraButtons)

        """
        Group
        """
        #select certain wavenumber(s) and generate a list
        textQListWidgetTitle= QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Selected wavenumbers:<b></p>',
            self)

        # Action to show current wavenumber from list
        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.itemDoubleClicked.connect(self.double_click_pressed)

        # Button to add a single wavenumber to list
        self.addWidgetButton = QtWidgets.QPushButton('', self)
        self.addWidgetButton.setMaximumSize(30, 30)
        self.addWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/AddSingleWavenumber.png')))
        self.addWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.addWidgetButton.clicked.connect(self.addWidgetButton_pressed)

        # Button to add a range of wavenumbers
        self.addRangeWidgetButton = QtWidgets.QPushButton('', self)
        self.addRangeWidgetButton.setMaximumSize(30, 30)
        self.addRangeWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/AddWavenumberRange.png')))
        self.addRangeWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.addRangeWidgetButton.clicked.connect(self.addRangeWidgetButton_pressed)

        # Button to remove single element from list
        self.removeWidgetButton = QtWidgets.QPushButton('', self)
        self.removeWidgetButton.setMaximumSize(30, 30)
        self.removeWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/RemoveWavenumberFromList.png')))
        self.removeWidgetButton.setIconSize(QtCore.QSize(10, 10))
        self.removeWidgetButton.clicked.connect(self.removeWidgetButton_pressed)

        # Button to clear the list
        self.clearWidgetButton = QtWidgets.QPushButton('', self)
        self.clearWidgetButton.setMaximumSize(30, 30)
        self.clearWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/ClearButtonList.png')))
        self.clearWidgetButton.setIconSize(QtCore.QSize(15, 15))
        self.clearWidgetButton.clicked.connect(self.clearWidgetButton_pressed)

        # Button for options to sort the list
        self.sortOrder = QtWidgets.QPushButton('', self)
        self.sortOrder.setMaximumSize(30, 30)
        self.sortOrder.setIcon(QtGui.QIcon(resource_path('Graphics/AscendingButton.png')))
        self.sortOrder.setIconSize(QtCore.QSize(15, 15))
        self.sortOrder.setCheckable(True)
        self.sortOrder.setChecked(False)

        # Button to sort the list
        self.sortWidgetButton = QtWidgets.QPushButton('', self)
        self.sortWidgetButton.setMaximumSize(30, 30)
        self.sortWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/SortIconList.png')))
        self.sortWidgetButton.setIconSize(QtCore.QSize(12, 15))
        self.sortWidgetButton.clicked.connect(self.sortWidgetButton_pressed)

        # Button to save the list
        self.saveWidgetButton = QtWidgets.QPushButton('', self)
        self.saveWidgetButton.setMaximumSize(30, 30)
        self.saveWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/SaveListTxt.png')))
        self.saveWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.saveWidgetButton.clicked.connect(self.saveWidgetButton_pressed)

        # Button to import a list
        self.openWidgetButton = QtWidgets.QPushButton('', self)
        self.openWidgetButton.setMaximumSize(30, 30)
        self.openWidgetButton.setIcon(QtGui.QIcon(resource_path('Graphics/OpenList.png')))
        self.openWidgetButton.setIconSize(QtCore.QSize(20, 20))
        self.openWidgetButton.clicked.connect(self.openWidgetButton_pressed)

        #Layout for the list of wavenumbers
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

        # Button to calculate mean image from list
        self.SumMeanButton = QtWidgets.QPushButton('', self)
        self.SumMeanButton.setMaximumSize(25, 25)
        self.SumMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/Sum_Mean_Button.png')))
        self.SumMeanButton.setIconSize(QtCore.QSize(20, 20))
        self.SumMeanButton.clicked.connect(self.SumMeanButton_pressed)

        # Button to show mean image
        self.ShowMeanButton = QtWidgets.QPushButton('', self)
        self.ShowMeanButton.setMaximumSize(25, 25)
        self.ShowMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/Show_Mean_Button.png')))
        self.ShowMeanButton.setIconSize(QtCore.QSize(20, 20))
        self.ShowMeanButton.setCheckable(True)
        self.ShowMeanButton.setChecked(False)
        self.ShowMeanButton.clicked.connect(self.ShowMeanButton_pressed)

        # Button to export mean image
        self.ExportMeanButton = QtWidgets.QPushButton('', self)
        self.ExportMeanButton.setMaximumSize(25, 25)
        self.ExportMeanButton.setIcon(QtGui.QIcon(resource_path('Graphics/ExportCSV.png')))
        self.ExportMeanButton.setIconSize(QtCore.QSize(20, 20))
        self.ExportMeanButton.clicked.connect(self.ExportMeanButton_pressed)

        # Layout
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

        # Place elements to main grid (mainGridLayoutQV)
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
        self.importdataType.setToolTip('Opens a window for data type selection.')
        self.importpolygon.setToolTip('Import shape(s) from .xml file.')
        self.SetMetaData.setToolTip('Opens a window for meta data input.')
        self.CropButton.setToolTip('Opens a window to select crop options.')
        self.exportZarrButton.setToolTip('Save data as .zarr file.')
        self.singlePixelSpectraButton.setToolTip('Obtain single spectra.')
        self.subRegionSpectraClearButton.setToolTip('Delete all ROI elements and spectra.')
        self.PolygonButton.setToolTip('Create ROI.')
        self.PolygonRemoveButton.setToolTip('Delete incomplete polygon.')
        self.DifferenceSpectraButton.setToolTip('Generate spectral difference.')
        self.XMLexportButton.setToolTip('Save shape(s) as .xml file.')
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
        """
        1. Opens a file dialog for the selection of an .xml file for the import of regions of interest.
        2. Import of polygons stored in the .xml file.
        3. Calcualtes mean spectra from the regions of interest.
        4. ROIs are stored in the widget tree
        Returns: None
        """
        # select xml-file for ROI import
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(None, "Select xml files", os.getcwd(),
                                                             'Files (*.xml)')

        #allows for import of multiple .xml files
        ll = 0
        rr = 0
        for file in file_names:

            file_extension = os.path.splitext(file)[-1]

            if file_extension == ".xml":
                shapes, calibrationPoints, capID = xml2shape(file)

                for i, shape in enumerate(shapes):

                    #ToDo: this requires some uniform notation
                    #ToDo: need more colors
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
                        # image offsets are included in case multiple files (images) were loaded.
                        self.viewQV.removeItem(self.polygon_item)
                        point = [p[0] + self.dataIR.image_Offsets[ll, 0], p[1] + self.dataIR.image_Offsets[ll, 1]]
                        lp = QtCore.QPointF(point[0], point[1])

                        poly = self.polygon_item.polygon()
                        poly.append(lp)
                        self.polygon_item.setPolygon(poly)
                        self.viewQV.addItem(self.polygon_item)

                        # image offsets are included in case multiple files (images) were loaded.
                        point_new = array([[p[0] + self.dataIR.image_Offsets[ll,0], p[1] + self.dataIR.image_Offsets[ll,1]]])
                        if self.polygonList[0, 0] == 0:
                            self.polygonList = point_new
                        else:
                            self.polygonList = concatenate((self.polygonList, point_new), axis=0)


                    #obtain mean spectra from masked image (ToDo: needs to be faster)
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

                    lineSyleSelected = self.LineStyleCombo.currentIndex()
                    if lineSyleSelected == 0:
                        lineStyle = QtCore.Qt.SolidLine
                    elif lineSyleSelected == 1:
                        lineStyle = QtCore.Qt.DashLine
                    elif lineSyleSelected == 2:
                        lineStyle = QtCore.Qt.DotLine

                    pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue), style=lineStyle)
                    plotDataNew = self.plotAbsorption.plot(x=self.dataIR.wavenumber, y=newSpectrum, pen=pen)
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
        
        # visualize regions of interest
        self.showPolygon_pressed()
        self.statusBar().showMessage('Regions of interest have been imported from .xml file.')

    # import .pickle files
    def importdata_pressed(self):
        """
        Import of a single or multiple data files of type: .zarr, .fsm, .pickle.
        Executes different functions for file type specific import.
        Returns: Nonte
        """
        if self.DataTypeWindow is None:
            extension = '.zarr'
            multipleFiles = False
        else:
            extension = self.DataTypeWindow.rbtnTextSelected
            #Ask for a single or multiple files to be imported
            if self.DataTypeWindow.NumberFilesBox.currentText() == 'multiple files':
                multipleFiles = True
            elif self.DataTypeWindow.NumberFilesBox.currentText() == 'single file':
                multipleFiles = False

        # Import data based on selected file type 
        if extension == '.zarr':
            # select file
            self.fileName = self.OpenFolder()
            data_imported = self.importZarrFile(self.fileName, multipleFiles)

        elif extension == '.pickle':
            self.fileName = self.OpenFilePickle()
            data_imported = self.importPickleFile(self.fileName, multipleFiles)

        elif extension == '.fsm':
            self.fileName = self.OpenFileFSM()
            data_imported = self.importFSMFile(self.fileName, multipleFiles)

        #generate mean spectrum and find min and max intensities
        if data_imported == True:
            meanSpectrum = mean(self.dataIR.imageStack.reshape((int(
                self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                                                int(self.dataIR.imageStack.shape[2]))), 0)
            selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())

            self.dataIR.image_Offsets = zeros((len(self.fileName), 2))

            self.minInt = self.dataIR.imageStack.min()
            self.maxInt = self.dataIR.imageStack.max()

            self.showAbsorptionSpectrum(meanSpectrum, selected_wavenumber)

            image_display = self.dataIR.imageStack[:, :, selected_wavenumber]
            self.showQVImages(image_display)

            self.calculateMask()
            self.clearSpectra_pressed()

            self.statusBar().showMessage('Data is imported.')
        else:
            self.statusBar().showMessage('No import.')

        self.transmittanceImage.setEnabled(True)
        self.absorbanceImage.setEnabled(True)
        
    def importPickleFile(self, fileName, multipleFiles=False):
        """
        Imports data as an image stack.
        fileName: path to the files
        multipleFiles: If single file - FALSE, if multiple files TRUE.
        Returns: image stack
        """
        #ToDo: optimize code and if conditions
        if multipleFiles == False:
            if size(fileName) == 1:
                pickle_in = open(fileName[0], "rb")
                type_pickle = os.path.splitext(fileName[0])[0][-10:]
                if type_pickle == 'wavenumber':
                    self.dataIR.wavenumber = pickle.load(pickle_in)
                    data_imported = False
                else:
                    self.dataIR.imageStack = pickle.load(pickle_in)
                    data_imported = True
                pickle_in.close()
            elif size(fileName) == 2:
                files_wavenumber = []
                files_data = []
                for ii in range(size(fileName)):
                    type_pickle = os.path.splitext(fileName[ii])[0][-10:]
                    if type_pickle == 'wavenumber':
                        files_wavenumber.append(fileName[ii])
                    else:
                        files_data.append(fileName[ii])
                if len(files_wavenumber) == 1 and len(files_data) == 1:
                    pickle_in = open(files_wavenumber[0], "rb")
                    self.dataIR.wavenumber = pickle.load(pickle_in)
                    sleep(0.1)
                    pickle_in.close()
                    sleep(0.1)
                    pickle_in = open(files_data[0], "rb")
                    self.dataIR.imageStack = pickle.load(pickle_in)
                    sleep(0.1)
                    pickle_in.close()
                    data_imported = True
                else:
                    data_imported = False

        elif multipleFiles == True:
            # ToDo: allow import of multiple zarr files
            data_imported = False

        return data_imported
    def importZarrFile(self, fileName, multipleFiles=False):
        """
        Imports data as an image stack.
        fileName: path to the files
        multipleFiles: If single file - FALSE, if multiple files TRUE.
        Returns: image stack
        """
        if multipleFiles == False:
            z1 = zarr.open(fileName)
            self.dataIR.imageStack = (z1['hypercube'][:])[:, :, ::-1]
            self.dataIR.wavenumber = (z1['wvnm'][:])[::-1]
            data_imported = True
            # ToDo: update meta data table
        elif multipleFiles == True:
            # ToDo: allow import of multiple zarr files
            data_imported = False

        return data_imported
    def importFSMFile(self, fileName, multipleFiles=False):
        """
        Imports data as an image stack.
        fileName: path to the files
        multipleFiles: If single file - FALSE, if multiple files TRUE.
        Returns: image stack
        """
        if multipleFiles == False:
            data = specread(fileName)
            self.dataIR.wavenumber = data.wavelength
            meta = data.meta
            image_dimensions = [meta["n_x"], meta["n_y"], meta["n_z"]]
            self.dataIR.imageStack = data.amplitudes.reshape(image_dimensions[1], image_dimensions[0], image_dimensions[2])
            #ToDo: update meta data table

            data_imported = True
        elif multipleFiles == True:
            # ToDo: allow import of multiple zarr files
            data_imported = False

        return data_imported

    def OpenFolder(self):
        """
        Opens a file dialog.
        Returns: Path to selected directory
        """
        directoryName = QtWidgets.QFileDialog.getExistingDirectory(None, "Select .zarr directory.")
        return directoryName
    def OpenFilePickle(self):
        """
        Opens a file dialog.
        Returns: Path to selected files
        """
        fileName, fileTypes = QtWidgets.QFileDialog.getOpenFileNames(None, "Select one or more files to open", os.getcwd(), 'Files (*.pickle)')
        return fileName
    def OpenFileFSM(self):
        """
        Opens a file dialog.
        Returns: Path to selected files
        """
        fileName, fileTypes = QtWidgets.QFileDialog.getOpenFileNames(None, "Select one or more files to open", os.getcwd(), 'Files (*.fsm)')
        return fileName
    def OpenTifFile(self):
        """
        Opens a file dialog.
        Returns: Path to selected files
        """
        fileName, fileTypes = QtWidgets.QFileDialog.getOpenFileName(None, "Select one file to open", os.getcwd(), 'Files (*.tif)')
        return fileName

    def OnClick(self, event):
        """
        Returns the pixel position to the status bar.
        """
        position = self.imgQV.mapFromScene(event)
        posX = int((position.x()))
        posY = int((position.y()))
        printPosition = 'x:' + str(posX) + ' px, y:' + str(posY) + ' px'
        self.statusBar().showMessage(printPosition)

    # Get spectra information: single pixel or Polygon
    # Action upon left mouse click on image
    def timeout(self):
        """
        Single left click: calls singlePointImage
        Double click: calls subRegionSpectraPolygonButton_pressed
        ... and sets the counter to zero.
        """
        if self.leftButton_click_count == 1:
            print('Single left click')
            self.SinglePointImage()
        elif self.leftButton_click_count > 1:
            print('Double left click')
            self.subRegionSpectraPolygonButton_pressed()
        self.leftButton_click_count = 0
    def onImageSpectra_clicked(self, event):
        """
        Obtain pixel position from image.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.leftButton_click_count += 1
            if not self.timer.isActive():
                self.timer.start()

        self.position = self.imgQV.mapFromScene(event.scenePos())
    def SinglePointImage(self):
        """
        1. Returns spectra for selected pixel for case 1.
        2. Adds pixel positions to list for polygon for case 2.
        """
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

                # Plots the data
                plotDataNew = self.plotAbsorption.plot(x=self.dataIR.wavenumber, y=newSpectrum, pen = pen)
                self.ListOfSpectraPixel = append(self.ListOfSpectraPixel, plotDataNew)

                # Add item to WidgetTree
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

                self.polygon_item.setPolygon(poly)
                polygon_help = self.polygon_item.polygon()

                numberOfPoints = int(polygon_help.size())

                path_new = self.polygon_item.shape()
                x = path_new.currentPosition().toPoint().x()
                y = path_new.currentPosition().toPoint().y()
                point = array([[x, y]])

                if self.polygonList[0, 0] == 0:
                   self.polygonList = point
                else:
                   self.polygonList = concatenate((self.polygonList, point), axis=0)

                self.viewQV.addItem(self.polygon_item)
    def subRegionSpectraPolygonButton_pressed(self):
        """
        Generates the polygon including mean spectra ...
        """
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

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=self.color, width=int(self.PenThicknessValue), style=lineStyle)
            plotDataNew = self.plotAbsorption.plot(x=self.dataIR.wavenumber, y=newSpectrum, pen=pen)
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
        """
        Function is used to visualize the polygon.
        """
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
        """
        Delete and re-draw the polygons.
        """
        for item in self.PolygonShowList:
            self.viewQV.removeItem(item)
        for item in self.PolygonShowList:
            self.viewQV.addItem(item)
    def removePolygon_pressed(self):
        """
        Removes a given polygon from the list.
        """
        if self.PolygonButton.isChecked() == True:
            self.singlePixelSpectraButton.setChecked(False)
            self.viewQV.removeItem(self.PolygonShowList[-1])
            self.PolygonButton.setChecked(False)
            self.polygonList = array([[0, 0]])
    def removeAllPolygon_pressed(self):
        """
        Removes all polygons from the list.
        """
        self.singlePixelSpectraButton.setChecked(False)
        for item in self.PolygonShowList:
            self.viewQV.removeItem(item)
        self.PolygonButton.setChecked(False)
        self.polygonList = array([[0, 0]])

    def DifferenceSpectraButton_pressed(self):
        """
        Function is used to calculate the difference spectra for two different regions/pixels.
        """
        # Check for two selected pixel in the pixel tree.
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
            itemDifferencewavenumber = item0.xData

            color = list(random.choice(range(256), size=3))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=color, width=int(self.PenThicknessValue), style=lineStyle)
            plotDataNew = self.plotAbsorption.plot(x=itemDifferencewavenumber, y=itemDifference, pen=pen)
            self.ListOfSpectraDifference = append(self.ListOfSpectraDifference, plotDataNew)

            # add item to WidgetTree
            elementNumber = int(len(self.differenceTreeElements))
            child = QtWidgets.QTreeWidgetItem(self.differenceTree)
            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
            child.setText(0, "Difference {}".format(elementNumber))
            child.setCheckState(0, QtCore.Qt.Unchecked)
            child.setForeground(0, QtGui.QBrush(QtGui.QColor(color[0], color[1], color[2])))
            self.differenceTreeElements = append(self.differenceTreeElements, child)

        #check for two selected regions in polygon tree
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
            itemDifferencewavenumber = item0.xData

            color = list(random.choice(range(256), size=3))

            lineSyleSelected = self.LineStyleCombo.currentIndex()
            if lineSyleSelected == 0:
                lineStyle = QtCore.Qt.SolidLine
            elif lineSyleSelected == 1:
                lineStyle = QtCore.Qt.DashLine
            elif lineSyleSelected == 2:
                lineStyle = QtCore.Qt.DotLine

            pen = pg.mkPen(color=color, width=int(self.PenThicknessValue), style=lineStyle)
            plotDataNew = self.plotAbsorption.plot(x=itemDifferencewavenumber, y=itemDifference, pen=pen)
            self.ListOfSpectraDifference = append(self.ListOfSpectraDifference, plotDataNew)

            # add item to WidgetTree
            elementNumber = int(len(self.differenceTreeElements))
            child = QtWidgets.QTreeWidgetItem(self.differenceTree)
            child.setFlags(child.flags() | QtCore.Qt.ItemIsEditable)
            child.setText(0, "Difference {}".format(elementNumber))
            child.setForeground(0, QtGui.QBrush(QtGui.QColor(color[0], color[1], color[2])))
            self.differenceTreeElements = append(self.differenceTreeElements, child)

    def exportToXmlButton_pressed(self):
        """
        Function used to export polygonial regions of interest as .xml file.
        1. Ask for a directory to save the file.
        2. Writes the data.
        """
        # Select folder
        folder_save = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        # ToDo: Here, we need to ask if the data should be sorted in a specific way. Not implemented yet.
        capture_ID = []
        shapes = []

        # ToDo: Add annotations to a new object that is then used for shape export to xml
        j = 0
        for element in self.PolygonShowList:
            poly = element.polygon()

            column = 0
            if self.polygonTreeElements[j].checkState(column) == QtCore.Qt.Checked:

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
                #ToDo: Hard coded to "8" so far
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

            j = j + 1

        offsetShape = [0, 0]
        scalingFactor = 1
        invertFactor = array([1, 1])
        TeachingPoints = zeros((3, 2))

        shape2xml(shapes, capture_ID, TeachingPoints.astype(int), offsetShape, scalingFactor,
                      invertFactor, folderName=folder_save)

    def openMenu(self, position):
        """
        Actions for the tree widgets (regions of interest)
        1. opens function to hide the item (via opacity)
        2. opens function to show the item (via opacity)
        3. opens function to delete the item
        4. opens function to change the color of the item
        """
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
    def TreeItem_Delete(self, item):
        """
        Deletes element from tree.
        """
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
        """
        Hides element via alpha value.
        """
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
        """
        Shows element via alpha value.
        """
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
    def TreeItem_ChangeColor(self, item):
        """
        Changes the color of the element in the tree.
        """
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
    def clearSpectra_pressed(self):
        """
        Removes all elements from the tree.
        """
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

    def addWidgetButton_pressed(self):
        """
        Adds an element (wavenumber) to the list of wavenumbers.
        """
        number = "{0:0=4d}".format(int(self.currentWavenumber))
        self.listWidget.addItem(number)

        self.generateItemList()
        self.showSelectedWavenumbers()
    def addRangeWidgetButton_pressed(self):
        """
        Adds an element (range of wavenumbers) to the list of wavenumbers.
        """
        region = self.regionLine.getRegion()
        inputString = str(int(region[0])) + ' - ' + str(int(region[1]))

        self.listWidget.addItem(inputString)

        self.generateItemList()
        self.showSelectedWavenumbers()
    def clearWidgetButton_pressed(self):
        """
        Delets the elements in the list of wavenumbers.
        """
        self.listWidget.clear()

        self.generateItemList()
        self.showSelectedWavenumbers()
    def sortWidgetButton_pressed(self):
        """
        Sorts the elements in the list of wavenumbers.
        """
        if self.sortOrder.isChecked():
            order = QtCore.Qt.AscendingOrder
        else:
            order = QtCore.Qt.DescendingOrder

        self.listWidget.sortItems(order)

        self.generateItemList()
    def removeWidgetButton_pressed(self):
        """
        Removes a single element in the list of wavenumbers.
        """
        self.listWidget.takeItem(self.listWidget.currentRow())

        self.generateItemList()
        self.showSelectedWavenumbers()
    def saveWidgetButton_pressed(self):
        """
        Save the list of wavenumbers as a .txt file.
        """
        itemsTextList =  [str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())]

        fileName, fileType = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '', 'Files (*.txt)')

        file = open(fileName, "w")
        file.writelines(["%s\n" % item  for item in itemsTextList])
        file.close()
    def openWidgetButton_pressed(self):
        """
        Imports the list of wavenumbers from a .txt file.
        """
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
        """
        Generates a reduced image stack (selectedimageStack) based on the elements selected in the list.
        """
        list = [str(self.listWidget.item(i).text()) for i in range(self.listWidget.count())]

        self.selectedWavenumberList = []

        for item in list:
            x = item.split(' - ')
            if len(x) == 1:
                self.selectedWavenumberList = append(self.selectedWavenumberList, int(x[0]))
            else:
                wavenumberSteps = abs(self.dataIR.wavenumber[0] - self.dataIR.wavenumber[1])

                list = arange(int(x[0]), int(x[1]) + wavenumberSteps, wavenumberSteps)

                self.selectedWavenumberList = append(self.selectedWavenumberList, list)

        # Sorts array
        self.selectedWavenumberList = sort(self.selectedWavenumberList)
        # Removes same elements
        self.selectedWavenumberList = unique(self.selectedWavenumberList.astype('int'))

        self.selectedWavenumberListPosition = zeros((len(self.selectedWavenumberList)))
        j = 0
        for i in self.selectedWavenumberList:
            self.selectedWavenumberListPosition[j] = int(abs(self.dataIR.wavenumber - int(i)).argmin())
            j=j+1

        # Defines reduced image stack
        self.selectedimageStack = self.dataIR.imageStack[:, : ,self.selectedWavenumberListPosition.astype('int')]

    def double_click_pressed(self):
        """
        Sets the image from the selected wavenumber list as active by double click.
        """
        current_item = self.listWidget.currentItem().text()

        x = current_item.split(' - ')
        if len(x) == 1:
            lineWavenumber = int(current_item)
            self.line.setValue(lineWavenumber)
            selected_wavenumber = int(abs(self.dataIR.wavenumber - int(lineWavenumber)).argmin())

            self.printWavenumber(self.dataIR.wavenumber[selected_wavenumber])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        else:
            lineWavenumber = int(x[0])
            self.regionLine.setRegion([int(x[0]), int(x[1])])
            selected_wavenumber = int(abs(self.dataIR.wavenumber - int(lineWavenumber)).argmin())

            self.printWavenumber(self.dataIR.wavenumber[selected_wavenumber])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def showSelectedWavenumbers(self):
        """
        Shows the image of the selected wavenumber.
        In case a wavenumber range is selected, the first wavenumber is the range is chosen.
        """
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
        """
        Excecutes the showSelectedWavenumbers function.
        """
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

    #ToDo: add discription.
    def on_ColormapComboBox_changed(self):
        """
        Initiates change of the colormap. The current wavenumber image will be re-plotted.
        """
        if self.QVShowButton.isChecked() == True:
            selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())

            self.printWavenumber(self.dataIR.wavenumber[selected_wavenumber])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])
        elif self.MaskShowButton.isChecked() == True:
            self.showQVImages(self.image_mask)
        elif self.ShowMeanButton.isChecked() == True:
            self.showQVImages(self.image_difference)

    def showQVImages(self, image_IR):
        """
        1. Set lut.
        2. Removes and sets current image.
        """
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
            color_name = 'viridis_r'
        elif color_value == 7:
            color_name = 'cividis'
        elif color_value == 8:
            color_name = 'plasma'
        elif color_value == 9:
            # Define the black-to-red colormap
            colors = [(0, "black"), (1, 'red')]  # RGB values for black (0, 0, 0) and red (1, 0, 0)
            n_bins = 200  # Number of bins (steps) for smooth gradient
            black_to_red = LinearSegmentedColormap.from_list("black_to_red", colors, N=n_bins)
            black_to_red.set_under('white')
            color_name = black_to_red
        elif color_value == 10:
            # Define the black-to-red colormap
            colors = [(0, "red"), (1, 'black')]  # RGB values for black (0, 0, 0) and red (1, 0, 0)
            n_bins = 200  # Number of bins (steps) for smooth gradient
            black_to_red = LinearSegmentedColormap.from_list("black_to_red", colors, N=n_bins)
            black_to_red.set_under('white')
            color_name = black_to_red

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
    def showAbsorptionSpectrum(self, spectrum, selected_wavenumber):
        """
        Adds an item to the spectra view.
        """
        self.plotAbsorption.clear()
        self.plotData = self.plotAbsorption.plot(x=self.dataIR.wavenumber, y=spectrum)

        self.line = pg.InfiniteLine(pos=int(self.dataIR.wavenumber.min()), angle=90, movable=True)
        self.plotLine = self.plotAbsorption.addItem(self.line)
        self.line.setBounds([self.dataIR.wavenumber.min(), self.dataIR.wavenumber.max()])
        self.line.sigPositionChangeFinished.connect(self.line_obtainPosition)
        self.line.setValue(int(self.dataIR.wavenumber[selected_wavenumber]))

        center = int((self.dataIR.wavenumber.max() + self.dataIR.wavenumber.min()) / 2)
        centerPM = 50
        self.regionLine = pg.LinearRegionItem([center - centerPM, center + centerPM],
                                              bounds=[self.dataIR.wavenumber.min(), self.dataIR.wavenumber.max()],
                                              movable=True)
        self.plotRegionLine = self.plotAbsorption.addItem(self.regionLine)
    def hideMean_pressed(self):
        """
        Set the alpha value of the mean spectra to either 0 or 1.
        """
        if self.HideMeanButton.isChecked() == True:
            self.plotData.setAlpha(0.0, False)
        else:
            self.plotData.setAlpha(1.0, False)

    def AbsoluteScaleButton_pressed(self):
        """
        Changes between absolute and relative scale.
        """
        self.AbsoluteScaleButton.setChecked(True)
        self.RelativeScaleButton.setChecked(False)

        self.on_ColormapComboBox_changed()
    def RelativeScaleButton_pressed(self):
        """
        Changes between absolute and relative scale.
        """
        self.AbsoluteScaleButton.setChecked(False)
        self.RelativeScaleButton.setChecked(True)

        self.on_ColormapComboBox_changed()
    def rangeSlider_moved(self):
        """
        Updates the intensity range based on an action on the range slider.
        """
        self.sliderlow = self.rangeSlider.low()
        self.sliderhigh = self.rangeSlider.high()
        self.on_ColormapComboBox_changed()

    def opacitySlider_changed(self):
        """
        Updates the opacity of the outline of the regions of interest based on an action on the opacity slider.
        """
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

    def printWavenumber(self, wavenumber):
        """
        Updates the current wavenumber to be displayed.
        """
        self.currentWavenumber = str(int(wavenumber))
        self.currentWavenumberInput.clear()
        self.currentWavenumberInput.setPlaceholderText(str(self.currentWavenumber))
    def nextRight_pressed(self):
        """
        Updates the current wavenumber images based on "right click" pressed.
        """
        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        if selected_wavenumber > 0:
            selected_wavenumber = selected_wavenumber - 1
            print('Selected wavenumber: ', self.dataIR.wavenumber[selected_wavenumber], 'Element number: ', selected_wavenumber)
            self.printWavenumber(self.dataIR.wavenumber[selected_wavenumber])
            print('show_1')
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])
            print('show_2')
            self.line.setValue(int(self.dataIR.wavenumber[selected_wavenumber]))

            self.QVShowButton.setChecked(True)
            self.MaskShowButton.setChecked(False)
            self.ShowMeanButton.setChecked(False)
    def nextLeft_pressed(self):
        """
        Updates the current wavenumber images based on "left click" pressed.
        """
        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        if selected_wavenumber < len(self.dataIR.wavenumber)-1:
            selected_wavenumber = selected_wavenumber + 1
            print('Selected wavenumber: ', self.dataIR.wavenumber[selected_wavenumber], 'Element number: ',
                selected_wavenumber)
            self.printWavenumber(self.dataIR.wavenumber[selected_wavenumber])
            self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])
            self.line.setValue(int(self.dataIR.wavenumber[selected_wavenumber]))

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)


    def keyPressEvent(self, event):
        """
        Updates the current wavenumber images based on keyboard action (left and right key).
        """
        # if left arrow key is pressed
        if event.key() == QtCore.Qt.Key_Left:
            self.nextLeft_pressed()
        # if right arrow key is pressed
        elif event.key() == QtCore.Qt.Key_Right:
            self.nextRight_pressed()

    def line_obtainPosition(self):
        """
        Updates the position (selected wavenumber) line presented in the spectra view.
        """
        lineWavenumber = int(self.line.value())
        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(lineWavenumber)).argmin())

        self.printWavenumber(self.dataIR.wavenumber[selected_wavenumber])
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)

    def MaskImportButton_pressed(self):
        """
        Opens and dialog window for the import of a .tiff file for the image mask and sets the image_mask.
        """
        # open Open dialog window
        fileNames = self.OpenTifFile()
        # obtain file extension of first file, should be the same for all other files
        self.extension_tif = os.path.splitext(fileNames)[1]
        if self.extension_tif == '.tif':
            image_mask = tifffile.imread(fileNames)
            self.image_mask = (exposure.rescale_intensity(image_mask, out_range=(0, 1))).astype('uint8')
            print('Done')

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
        """
        Export of the mean intensity image and image mask in a .tif file format to a used defined directory.
        """
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
        """
        Generates a sum image based on the list of wavenumbers.
        """
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
        """
        Calculate masked image based on given mass list using a gaussian mixture model.
        """
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
        """
        Invert the mask image from 0-1 to 1-0.
        """
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
        """
        Selects if the masked image is applied to the shown current wavenumber image or not.
        """
        if self.pressedYesNo == False:
            self.pressedYesNo = True
        else:
            self.pressedYesNo = False
        self.on_ColormapComboBox_changed()

    def create_label_image(self):
        """
        Creates a label image.
        Return: numpy array with label information.
        ToDo: this can be done more efficient.
        """
        if True:
            self.X = []
            self.Y = []
            # check for "checked" in Pixel Tree Polygon Items
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

                    #gives wrong result if the ordering is not from 0 to N.
                    imageLabels[imageLabels > int(value)] = 0

                else:
                    print('Element ', str(j), ' not selected.')

                j = j + 1
        return(imageLabels)

    def to_zarr(self):
        """
        Saves the image stack and corresponding information as .zarr file.
        """
        # select folder
        file_save = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
        folder = file_save[0] + '.zarr'

        fileName_hyper = folder + '\hypercube'
        fileName_wvnm = folder + '\wvnm'
        fileName_labels = folder + '\lbls'
        fileName_mask = folder + '\mask'
        fileName_meta = folder + '\meta'

        #obtain label image
        labeledImage = self.create_label_image()

        #save data and attributes
        zarr.save(fileName_labels, labeledImage)
        zarr.save(fileName_mask, self.image_mask)
        z0 = zarr.group(fileName_meta)

        if self.CropButtonYN.isChecked() == True:
            xstart = int(self.roiBox.pos()[0])
            xwidth = int(self.roiBox.size()[0])
            ystart = int(self.roiBox.pos()[1])
            ywidth = int(self.roiBox.size()[1])
            zarr.save(fileName_hyper, self.dataIR.imageStack[xstart: xstart + xwidth, ystart: ystart + ywidth, ::-1])
        else:
            zarr.save(fileName_hyper, self.dataIR.imageStack[:, :, ::-1])
        zarr.save(fileName_wvnm, self.dataIR.wavenumber[::-1])


        if self.MetaDataWindow is None:
            self.SetMetaData_pressed()

        z0.attrs['Device'] = str(self.MetaDataWindow.deviceBox.currentText())
        z0.attrs['Mode'] = str(self.MetaDataWindow.modeBox.currentText())
        z0.attrs['wvnm_min'] = self.MetaDataWindow.WvnmMinInputValue
        z0.attrs['wvnm_max'] = self.MetaDataWindow.WvnmMaxInputValue
        z0.attrs['px'] = self.MetaDataWindow.pxInputValue
        z0.attrs['py'] = self.MetaDataWindow.pyInputValue
        z0.attrs['tsx'] = self.MetaDataWindow.tsxInputValue
        z0.attrs['tsy'] = self.MetaDataWindow.tsyInputValue

        #print to status bar
        self.statusBar().showMessage("Export done.")

    #image modifications
    def rotateLeft_pressed(self):
        """
        Function is used to rotate the image stack, masked image and so on...
        """
        self.dataIR.imageStack = rot90(self.dataIR.imageStack, k=1)

        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        self.image_mask = rot90(self.image_mask, k=1)
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = rot90(self.image_difference, k=1)

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def rotateRight_pressed(self):
        """
        Function is used to rotate the image stack, masked image and so on...
        """
        self.dataIR.imageStack = rot90(self.dataIR.imageStack, k=-1)

        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        self.image_mask = rot90(self.image_mask, k=-1)
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = rot90(self.image_difference, k=-1)

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def invertX_pressed(self):
        """
        Function is used to flip the image stack, masked image and so on...
        """
        self.dataIR.imageStack = self.dataIR.imageStack[::-1, :, :]
        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        self.image_mask = self.image_mask[::-1, :].copy()
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = self.image_difference[::-1, :].copy()

        self.QVShowButton.setChecked(True)
        self.MaskShowButton.setChecked(False)
        self.ShowMeanButton.setChecked(False)
    def invertY_pressed(self):
        """
        Function is used to flip the image stack, masked image and so on...
        """
        self.dataIR.imageStack = self.dataIR.imageStack[:, ::-1, :]
        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

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
        """
        Function used to translate transmittance into absorbance
        """
        self.dataIR.imageStack = -log10(self.dataIR.imageStack/100)

        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        #generate mean
        meanSpectrum = mean(
            self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                             int(self.dataIR.imageStack.shape[2]))), 0)

        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()

        self.showAbsorptionSpectrum(meanSpectrum, selected_wavenumber)

        self.clearSpectra_pressed()

        self.absorbanceImage.setEnabled(False)
        self.transmittanceImage.setEnabled(True)
    def calc_transmittance_pressed(self):
        """
        Function used to translate absorbance into transmittance
        """
        self.dataIR.imageStack = 100*(10**(-(self.dataIR.imageStack)))


        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        meanSpectrum = mean(
            self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                             int(self.dataIR.imageStack.shape[2]))), 0)
        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()

        self.showAbsorptionSpectrum(meanSpectrum, selected_wavenumber)

        #self.calculateMask()
        self.clearSpectra_pressed()

        self.absorbanceImage.setEnabled(True)
        self.transmittanceImage.setEnabled(False)

    def calculateMask(self):
        """
        Calculate image mask with pre-defined wavenumber and thus mean image
        """
        # hard coded are 4 characteristic bands
        mask_wavenumber = array([1080, 1552, 1660, 1740])
        selectedWavenumberListPosition = zeros((len(mask_wavenumber)))
        j = 0
        for i in mask_wavenumber:
            selectedWavenumberListPosition[j] = int(abs(self.dataIR.wavenumber - int(i)).argmin())
            j = j + 1
        mean_spectra = (mean(self.dataIR.imageStack[:, :, selectedWavenumberListPosition.astype('int')], 2))
        # use a gaussian mixture model with 2 components
        classif_GMM = GaussianMixture(n_components=2)
        classif_GMM.fit(mean_spectra.reshape((mean_spectra.size, 1)))
        thresh_mean = mean(classif_GMM.means_)
        self.image_mask = mean_spectra < thresh_mean
        self.image_mask_help = self.image_mask.copy()

        self.image_difference = zeros_like(self.image_mask, dtype = float32)

    def resetPreProcessingButton_pressed(self):
        """
        re-load the data
        ToDo: add all other options like pickle or fsm data
        """
        extension = os.path.splitext(self.fileName)[1]
        print(extension)
        if extension == '.zarr':
            if size(self.fileName) == 1:
                z1 = zarr.open(self.fileName)
                self.dataIR.imageStack = (z1['hypercube'][:])[:, :, ::-1]
                self.dataIR.wavenumber = (z1['wvnm'][:])[::-1]

                meanSpectrum = mean(self.dataIR.imageStack.reshape((int(
                    self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                                                    int(self.dataIR.imageStack.shape[2]))), 0)
                selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())

                self.dataIR.image_Offsets = zeros((len(self.fileName), 2))

                self.minInt = self.dataIR.imageStack.min()
                self.maxInt = self.dataIR.imageStack.max()

                data_imported = True
            else:
                data_imported = False

        if data_imported == True:
            self.showAbsorptionSpectrum(meanSpectrum, selected_wavenumber)

            image_display = self.dataIR.imageStack[:, :, selected_wavenumber]
            self.showQVImages(image_display)

            self.calculateMask()
            self.clearSpectra_pressed()
        print('Done')

        self.transmittanceImage.setEnabled(True)
        self.absorbanceImage.setEnabled(True)

    def runPreProcessingButton_pressed(self):
        """
        Execute pre-procssing
        """
        if self.BaselineSettingsWindow is not None:
            self.smoothFactorValue = self.BaselineSettingsWindow.smoothFactorValue
            self.smoothFactorValue1 = self.BaselineSettingsWindow.smoothFactorValue1
            self.weightingFactorValue = self.BaselineSettingsWindow.weightingFactorValue
            self.iterationFactorValue = self.BaselineSettingsWindow.iterationFactorValue

        self.lam = int(self.smoothFactorValue)
        self.lam1 = int(self.smoothFactorValue1)
        self.p = float(self.weightingFactorValue)
        self.Niter = int(self.iterationFactorValue)

        self.thread = calculationThread(self)
        self.thread.finished.connect(self.onFinished)
        self.thread.notifyProgress.connect(self.onProgress)
        self.thread.start()

        self.transmittanceImage.setEnabled(False)
        self.absorbanceImage.setEnabled(False)

    def modifyMaskButtonIR_pressed(self):
        """
        Fuction used to modify the image mask
        1. Binary closing
        2. Remove Holes
        3. Remove Small Objects
        """
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
        """
        Apply pre-processing.
        :return:
        """
        #baseline
        if self.BaselineCheckBox.isChecked() == True:
            self.dataIR.imageStack = self.thread.data.copy()

        #spectral differentiation
        if self.derivativeCheckBox.isChecked() == True:
            if self.derivativeSettingsWindow is not None:
                if str(self.derivativeBox.currentText()) == 'Linear':
                    self.derivativeSettingsWindow.LengthInputValue = 'None'
                    self.derivativeSettingsWindow.LengthInput.setPlaceholderText('None')
                    self.derivativeSettingsWindow.PolyInputValue = 'None'
                    self.derivativeSettingsWindow.PolyInput.setPlaceholderText('None')
                    self.dataIR.imageStack = self.dataIR.Derivative(self.dataIR.imageStack, int(self.derivativeSettingsWindow.OrderInputValue))
                    distance = abs(self.dataIR.wavenumber[0] - self.dataIR.wavenumber[1])
                    if int(self.derivativeSettingsWindow.OrderInputValue) == 1:
                        self.dataIR.wavenumber = self.dataIR.wavenumber[0:-int(self.derivativeSettingsWindow.OrderInputValue)] - distance / 2
                    elif int(self.derivativeSettingsWindow.OrderInputValue) == 2:
                        self.dataIR.wavenumber = self.dataIR.wavenumber[0:-int(self.derivativeSettingsWindow.OrderInputValue)] - distance
                elif str(self.derivativeBox.currentText()) == 'Savitzky-Golay':
                    if int(self.derivativeSettingsWindow.LengthInputValue) <= int(self.derivativeSettingsWindow.PolyInputValue):
                        self.derivativeSettingsWindow.LengthInputValue = str(int(self.derivativeSettingsWindow.PolyInputValue) + 1)
                    self.dataIR.imageStack = signal.savgol_filter(self.dataIR.imageStack, int(self.derivativeSettingsWindow.LengthInputValue), int(self.derivativeSettingsWindow.PolyInputValue), deriv=int(self.derivativeSettingsWindow.OrderInputValue))

            else:
                print('No')
                #default methods
                self.derivativeBox.setCurrentText('linear')
                self.der_order = 2
                self.dataIR.imageStack = self.dataIR.Derivative(self.dataIR.imageStack, self.der_order)
                distance = abs(self.dataIR.wavenumber[0] - self.dataIR.wavenumber[1])
                self.dataIR.wavenumber = self.dataIR.wavenumber[0:-self.der_order] - distance

        #normalization
        if self.NormalizationCheckBox.isChecked() == True:
            #e.g. SNV
            self.dataIR.imageStack = self.SNV(self.dataIR.imageStack)

        # print data
        selected_wavenumber = int(abs(self.dataIR.wavenumber - int(self.currentWavenumber)).argmin())
        self.showQVImages(self.dataIR.imageStack[:, :, selected_wavenumber])

        meanSpectrum = mean(
            self.dataIR.imageStack.reshape((int(self.dataIR.imageStack.shape[0] * self.dataIR.imageStack.shape[1]),
                                             int(self.dataIR.imageStack.shape[2]))), 0)
        self.showAbsorptionSpectrum(meanSpectrum, selected_wavenumber)
        self.showSelectedWavenumbers()

        self.minInt = self.dataIR.imageStack.min()
        self.maxInt = self.dataIR.imageStack.max()

        self.statusBar().showMessage('Pre-processing finished.')

    def SNV(self, data):
        """
        Calculates the standard normal variate
        :parameter: data - hyperspectral image stack
        :return:
        """
        try:
            sizeX = shape(data)[1]
            sizeY = shape(data)[0]
            sizeZ = shape(data)[2]
            data = data.reshape(sizeX * sizeY, sizeZ)
            dataMean = mean(data, axis=1)
            step1 = (data - dataMean.reshape((sizeX * sizeY, 1)))
            step1Std = std(step1, axis=1, ddof=1)
            for i, element in enumerate(step1Std):
                if step1Std[i] == 0:
                    step1Std[i] = 1
            step2 = step1 / step1Std.reshape((sizeX * sizeY, 1))
            data = step2.reshape(sizeY, sizeX, sizeZ)
            return data
        except:
            dataMean = mean(data)
            step1 = (data - dataMean)
            step1Std = std(step1, ddof=1)
            for i, element in enumerate(step1Std):
                if step1Std[i] == 0:
                    step1Std[i] = 1
            step2 = step1 / step1Std
            return step2

    def BaselineSettingsButton_pressed(self):
        """
        Opens a dialog window for the input parameters for the baseline correction.
        :return:
        """
        try:
            if self.BaselineSettingsWindow is None:
                self.BaselineSettingsWindow = ASLS_Settings_Dialog(parent=self)
                self.BaselineSettingsWindow.show()
                self.BaselineSettingsWindow.isVisible()
            elif self.BaselineSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.BaselineSettingsWindow = ASLS_Settings_Dialog(parent=self)
                self.BaselineSettingsWindow.show()
                self.BaselineSettingsWindow.isVisible()
        except:
            pass
    def MaskSettingsButton_pressed(self):
        """
        Opens a dialog window for the input parameters of masking the image.
        :return:
        """
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
    def derivativeSettings_pressed(self):
        """
        Opens a dialog window for the input parameters of the spectral diffentiation.
        :return:
        """
        try:
            if self.derivativeSettingsWindow is None:
                self.derivativeSettingsWindow = Parameters_derivative_Settings_Dialog(parent=self)
                self.derivativeSettingsWindow.show()
                self.derivativeSettingsWindow.isVisible()
            elif self.derivativeSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.derivativeSettingsWindow = Parameters_derivative_Settings_Dialog(parent=self)
                self.derivativeSettingsWindow.show()
                self.derivativeSettingsWindow.isVisible()
        except:
            pass

    def CropButton_pressed(self):
        """
        Opens a dialog window for the input parameters from cropping the image stack.
        :return:
        """
        try:
            if self.CropWindow is None:
                self.CropWindow = Crop_Dialog(parent=self)
                self.CropWindow.show()
                self.CropWindow.isVisible()
            elif self.CropWindow.reply == QtWidgets.QMessageBox.Yes:
                self.CropWindow = Crop_Dialog(parent=self)
                self.CropWindow.show()
                self.CropWindow.isVisible()
        except:
            pass

    def CropButtonYN_pressed(self):
        """
        Used to display a rectangle used for cropping of the image stack.
        :return:
        """
        #get image size
        if self.CropWindow is None:
            size_x = shape(self.dataIR.imageStack)[0]
            size_y = shape(self.dataIR.imageStack)[1]
            frame = 10
            xstart = int(0 + frame)
            ystart = int(0 + frame)
            xwidth = int(size_x - 2*frame)
            ywidth = int(size_y - 2*frame)
        else:
            size_x = int(self.CropWindow.tsxInputValue)
            size_y = int(self.CropWindow.tsyInputValue)
            frame = 0
            xstart = int(0 + frame)
            ystart = int(0 + frame)
            xwidth = int(size_x*int(self.CropWindow.NxInputValue) - frame)
            ywidth = int(size_y*int(self.CropWindow.NyInputValue) - frame)
        # Add ROI

        if self.CropButtonYN.isChecked() == True:
            #create ROI
            self.roiBox = pg.ROI([xstart, ystart], [xwidth, ywidth])
            self.roiBox.setPen(pg.mkPen('b', width=3))
            self.viewQV.addItem(self.roiBox)

            self.roiBox.addScaleHandle([1, 1], [0, 0])
            self.roiBox.addScaleHandle([0, 0], [1, 1])
        else:
            self.viewQV.removeItem(self.roiBox)

    def importdataType_pressed(self):
        """
        Opens a dialog window with the data type information used for the import of MIR data.
        :return:
        """
        try:
            if self.DataTypeWindow is None:
                self.DataTypeWindow = ImportDataTypeWindow_Dialog(parent=self)
                self.DataTypeWindow.show()
                self.DataTypeWindow.isVisible()
            elif self.DataTypeWindow.reply == QtWidgets.QMessageBox.Yes:
                self.DataTypeWindow = ImportDataTypeWindow_Dialog(parent=self)
                self.DataTypeWindow.show()
                self.DataTypeWindow.isVisible()
        except:
            pass

    def SetMetaData_pressed(self):
        """
        Opens a dialog window with the meta data information.
        :return:
        """
        try:
            if self.MetaDataWindow is None:
                self.MetaDataWindow = MetaData_Dialog(parent=self)
                self.MetaDataWindow.show()
                self.MetaDataWindow.isVisible()
            elif self.MetaDataWindow.reply == QtWidgets.QMessageBox.Yes:
                self.MetaDataWindow = MetaData_Dialog(parent=self)
                self.MetaDataWindow.show()
                self.MetaDataWindow.isVisible()
        except:
            pass

    # Define Thread and Calculation
class calculationThread(QtCore.QThread):
    """
    Thread for baseline correction as calculation could last longer
    """
    notifyProgress = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        super(calculationThread, self).__init__(parent)

        self.data = parent.dataIR.imageStack.copy()
        self.wvnm = parent.dataIR.wavenumber.copy()
        self.lam = parent.lam
        self.lam1 = parent.lam1
        self.p = parent.p
        self.niter = parent.Niter

        self.box = parent.BaselineCheckBox
        self.baselineType = parent.BaselineBox

    def run(self):
        """
        runs baseline correction
        :return:
        ToDo: improve on implementation
        """
        if self.box.isChecked() == True:
            sizeX = shape(self.data)[1]
            sizeY = shape(self.data)[0]
            sizeXY = sizeX * sizeY
            sizeZ = shape(self.data)[2]

            print(self.wvnm[::-1])

            self.data = self.data.reshape(sizeXY, sizeZ)
            self.data = transpose(self.data, (1, 0))
            #check if absorbance or transmittance spectra
            meanSpectrum = mean(mean(self.data, 0))

            Baseline = []
            if meanSpectrum > 10:
                print('transmittance baseline correction')
            else:
                print('absorbance baseline correction')
                for jj in range(sizeXY):
                    if str(self.baselineType.currentText()) == 'ASLS':
                        Baseline.append(self.AsLS_baseline_abs(self.data[:, jj], self.lam, self.p, self.niter))

                    elif str(self.baselineType.currentText()) == 'IASLS':
                        Baseline.append(self.iasls_abs(self.data[:, jj], self.lam, self.lam1, self.p, self.niter))

                    elif str(self.baselineType.currentText()) == 'ARPLS':
                        Baseline.append(self.iasls_abs(self.data[:, jj], self.lam, self.p, self.niter))

                    elif str(self.baselineType.currentText()) == 'Rubberband':
                        Baseline.append(self.rubberband_abs(self.wvnm[::-1], self.data[:, jj]))

                    elif str(self.baselineType.currentText()) == 'Linear':
                        Baseline.append(self.linear_abs(self.wvnm[::-1], self.data[:, jj]))

                    completed = int(100 * jj / (sizeX * sizeY))
                    self.notifyProgress.emit(completed)

                Baseline = transpose(Baseline, (0, 2, 1))
                self.data = Baseline[:, :, 0]

            # 100 for PrograssBar
            self.notifyProgress.emit(100)
            self.data = self.data.reshape(sizeY, sizeX, sizeZ)

    def AsLS_baseline_abs(self, y, lam, p, niter):
        """
        general Algorithmus for Asymetric Least Squares Smoothing for Baseline Correction: P.H.C.Eilers & H.F.M.Boelens(2005)
        implementations: https://stackoverflow.com/questions/29156532/python-baseline-correction-library or https://github.com/ctroein/octavvs

        :param y: one spectrum to correct
        :param lam: the smoothness parameter
        :param p: the asymmetry parameter, typically .001 to 0.1
        :param niter: number of iterations
        :return: corrected spectra and baseline of the spectrum
        """
        L = y.shape[-1]
        D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
        D = lam * D.dot(D.transpose())
        w = ones(L)
        W = sparse.spdiags(w, 0, L, L)
        for it in range(niter):
            W.setdiag(w)
            Z = W + D
            z = spsolve(Z, w * y)
            w = p * (y > z) + (1 - p) * (y < z)
        yb = transpose(z)
        y = y - yb

        return y, yb
    def iasls_abs(self, y, lam, lam1, p, niter):
        """
        :param y: one spectrum to correct
        :param lam: the smoothness parameter
        :param lam1: the 1st derivatives smoothness parameter
        :param p: the asymmetry parameter, typically .001 to 0.1
        :param niter: number of iterations
        :return: corrected spectra and baseline of the spectrum
        """

        L = y.shape[-1]
        D = sparse.csc_matrix(diff(eye(L), 2))
        D = lam * D.dot(D.T)
        D1 = sparse.csc_matrix(diff(eye(L), 1))
        D1 = lam1 * D1.dot(D1.T)

        w = ones(L)
        W = sparse.spdiags(w, 0, L, L)
        #        W = W @ W.T
        z = spsolve(W + D, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
        for i in range(niter):
            W = sparse.spdiags(w, 0, L, L)
            #            W = W @ W.T
            z = spsolve(W + D + D1, (W + D1) * y)
            wnew = p * (y > z) + (1 - p) * (y < z)
            if array_equal(wnew, w):
                break
            w = wnew
        yb = z
        y = y - yb

        return y, yb
    def arpls_abs(y, lam, ratio, niter):
        """
        asymmetric reweighted penalized least squares smoothing, arPLS
        Reference: Sung-June Baek, Aaron Park, Young-Jin Ahn and Jaebum Choo
            Analyst, 2015, 140, 250-257. DOI: 10.1039/C4AN01061B
        Implementation: https://github.com/ctroein/octavvs
        :param y: one spectrum to correct
        :param lam: the smoothness parameter
        :param ratio: convergence criterion
        :param niter: number of iterations
        :return: corrected spectra and baseline of the spectrum
        """
        L = y.shape[-1]
        D = sparse.csc_matrix(diff(eye(L), 2))
        D = lam * D.dot(D.T)

        w = ones(L)
        for i in range(niter):
            W = sparse.spdiags(w, 0, L, L)
            z = sparse.linalg.spsolve(W + D, w * y)
            d = y - z
            dn = d[d < 0]
            s = dn.std()
            wt = 1. / (1 + exp(2 / s * (d - (2 * s - dn.mean()))))
            if linalg.norm(w - wt) / linalg.norm(w) < ratio:
                break
            w = wt
        yb = z
        y = y - yb

        return y, yb
    def rubberband_abs(self, x, y):
        """
        implementations: https://github.com/ctroein/octavvs

        :param x: list of wavenumbers
        :param y: spectrum
        :return: corrected spectra and baseline of the spectrum
        """
        # Find the convex hull
        v = ConvexHull(column_stack((x, y))).vertices
        # Rotate convex hull vertices until they start from the lowest one
        v = roll(v, -v.argmin())
        # Leave only the ascending part
        v = v[:v.argmax() + 1]
        # Create baseline using linear interpolation between vertices
        b = interp(x, x[v], y[v])
        yb = b
        y = y - yb

        return y, yb
    def linear_abs(self, x, y):
        """
        implementations: https://github.com/ctroein/octavvs
        
        :param x: 
        :param y: 
        :return: corrected spectra and baseline of the spectrum
        """""
        if x[0] < x[-1]:
            z = interp1d(x[[0, -1]], y[..., [0, -1]], assume_sorted=True)(x)
        yb = z
        y = y - yb

        return y, yb

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    EnableDarkMode(app)

    ui = M2iraQuantView()
    ui.show()

    sys.exit(app.exec())

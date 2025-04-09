"""
M2iraQuant: Mannheim Mid-Infrared Analysis Quantum
M2iraQuantReg: M2ira Quant Registration
M2iraQuantView: M2ira Quant Viewer

The software part is designed as a Viewer for MIR data
Python v3.8, pyqt5

"""

# packages
import sys
from PyQt5 import QtWidgets, QtGui, QtCore

import pyqtgraph as pg
from numpy import random, rot90, array, ones_like, zeros, ndarray, zeros_like, size, shape, mean, append,  arange, around, delete, asarray, bincount, diff, absolute, uint8
from datetime import datetime
import os
from skimage import io
import skimage.exposure as exposure
import SimpleITK as sitk
from skimage.color import rgb2gray, gray2rgb
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans, BisectingKMeans
from matplotlib.pyplot import cm, figure, show, imshow, subplot, hist, plot, xlabel, ylabel, title, gca, draw, rcParams, legend
from functools import partial
from tifffile import tifffile
from skimage.transform import rotate
from skimage.morphology import remove_small_objects, binary_closing, disk, remove_small_holes, binary_erosion, binary_dilation
from skimage.filters import gaussian, threshold_multiotsu
from skimage.segmentation import flood_fill
from skimage.filters import threshold_otsu


#import windows
from QCL_v4.SubWindows.IRTransferSettingsWindow import IR_Transfer_Settings_Dialog
from QCL_v4.SubWindows.OptImportSettingsWindow import Opt_Import_Settings_Dialog
from QCL_v4.SubWindows.SegmentationSettingsWindow import Segmentation_Settings_Dialog
from QCL_v4.SubWindows.RegistrationSettingsWindow import Registration_Settings_Dialog
from QCL_v4.SubWindows.maskSettingsWindow import Mask_Settings_Dialog
from QCL_v4.SubWindows.M2iraQuantView import M2iraQuantView

from QCL_v4.Appearance.DarkMode import EnableDarkMode

from QCL_v4.ImportShape.XML.shape2xml import shape2xml
from QCL_v4.ImportShape.XML.xml2shape import xml2shape
from QCL_v4.ImportShape.XML.addshape2xml import addshape2xml
from QCL_v4.ImportShape.mis_maker_class import mismaker

from QCL_v4.Functions.ContourFinding import FindContours, FindOpenContours


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


#create new window class
class M2iraReg(QtWidgets.QMainWindow):
    def __init__(self):
        super(M2iraReg, self).__init__()
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        # add variables
        self.wavenumbers = []
        self.image_IR = []
        self.mask_IR = []
        self.mask_IR_mean = []
        self.image_opt_gray = []
        self.image_opt_mask = []
        self.image_IR_opt_reg = []
        self.mask_IR_reg = []
        self.image_segment = []
        self.image_optical = []
        self.image_optical_help = []
        self.image_opt_mask_help = []
        self.mask_IR_reg_help = []
        self.ROI_trans_help = []
        self.image_IR_mask_mean_help = []
        self.image_IR_mask_help = []

        # teaching marks
        self.TeachingCounter = 0
        self.TeachingPoints = zeros((3, 2))

        # used for navigation
        self.InfraredTreeElements = []
        self.ListRegionsInfrared = {}
        self.ShapesTreeElements = []
        self.ListRegionsShapes = {}

        self.QVWindow = None

        # initialize window
        self.initMe()

    # initialize window
    def initMe(self):

        #StatusBar
        self.statusBar().showMessage('')

        # Define geometry of this window
        self.setGeometry(100, 200, 900, 760)
        self.setMaximumSize(900, 760)
        self.setWindowTitle('M\u00B2IRA QUANT - Registration')

        #define grid layout
        self.centralWidgetQR = QtWidgets.QWidget(self)
        self.centralWidgetQR.setObjectName('centralWidgetQR')

        # define main grid layout
        self.mainGridLayoutQR = QtWidgets.QGridLayout(self.centralWidgetQR)
        self.mainGridLayoutQR.setSpacing(10)

        #Layout Left: IR images for analysis
        self.subWidgetLeft = QtWidgets.QWidget(self)
        self.subGridLeft = QtWidgets.QGridLayout(self.subWidgetLeft)

        #Layout Right: Microscope Images for Registration
        self.subWidgetRight = QtWidgets.QWidget(self)
        self.subGridRight = QtWidgets.QGridLayout(self.subWidgetRight)


#Left Layout - "infrared layout"
        # parameters used for the size of the QIcons
        sizeMax = 40; sizeMin = 40; sizeIcon = 30; maxSize = 25; minSize = 25

        # IR Buttons - opens M2iraQuantView
        self.openM2iraView = QtWidgets.QPushButton('', self)
        self.openM2iraView.setMaximumSize(sizeMax, sizeMax)
        self.openM2iraView.setMinimumSize(sizeMin, sizeMin)
        self.openM2iraView.setIcon(QtGui.QIcon(resource_path('Graphics/QuantumViewer3.png')))
        self.openM2iraView.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.openM2iraView.clicked.connect(self.openM2iraView_pressed)
        self.openM2iraView.setToolTip('Open M\u00B2IRAQUANT- Viewer.')

        # Transfer IR data from M2iraQuantViewer
        self.transferIRdata = QtWidgets.QPushButton('', self)
        self.transferIRdata.setMaximumSize(sizeMax, sizeMax)
        self.transferIRdata.setMinimumSize(sizeMin, sizeMin)
        self.transferIRdata.setIcon(QtGui.QIcon(resource_path('Graphics/QCLImagesButton.png')))
        self.transferIRdata.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.transferIRdata.clicked.connect(self.transferIRdata_pressed)
        self.transferIRdata.setEnabled(False)
        self.transferIRdata.setToolTip('Transfer selected IR images from M\u00B2IRAQUANT - Viewer.')

        # Settings Window for transfered IR data
        self.IRTransferSettings = QtWidgets.QPushButton('', self)
        self.IRTransferSettings.setMaximumSize(sizeMax, sizeMax)
        self.IRTransferSettings.setMinimumSize(sizeMin, sizeMin)
        self.IRTransferSettings.setIcon(QtGui.QIcon(resource_path('Graphics/QCLSettingsButton.png')))
        self.IRTransferSettings.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.IRTransferSettings.clicked.connect(self.IRTransferSettings_pressed)
        self.IRTransferWindow = None
        self.IRTransferSettings.setToolTip('Defines Settings for image transfer from QV window.')

        # Runs image segmentation on IR data
        self.segmentationButton = QtWidgets.QPushButton('', self)
        self.segmentationButton.setMaximumSize(sizeMax, sizeMax)
        self.segmentationButton.setMinimumSize(sizeMin, sizeMin)
        self.segmentationButton.setIcon(QtGui.QIcon(resource_path('Graphics/SegmentationButton2.png')))
        self.segmentationButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.segmentationButton.clicked.connect(self.segmentationButton_pressed)
        self.segmentationButton.setEnabled(False)
        self.segmentationButton.setToolTip('Perform image segmentation on selected IR data.')

        # Opens window for image segmentation
        self.segmentationSettingsButton = QtWidgets.QPushButton('', self)
        self.segmentationSettingsButton.setMaximumSize(sizeMax, sizeMax)
        self.segmentationSettingsButton.setMinimumSize(sizeMin, sizeMin)
        self.segmentationSettingsButton.setIcon(QtGui.QIcon(resource_path('Graphics/SegmentationSettingsButton.png')))
        self.segmentationSettingsButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.segmentationSettingsButton.clicked.connect(self.segmentationSettingsButton_pressed)
        self.segmentationSettingsWindow = None
        self.segmentationSettingsButton.setToolTip('Segmentation Settings.')

        # transfer selected image segment
        self.segmentationTransferButton = QtWidgets.QPushButton('', self)
        self.segmentationTransferButton.setMaximumSize(sizeMax, sizeMax)
        self.segmentationTransferButton.setMinimumSize(sizeMin, sizeMin)
        self.segmentationTransferButton.setIcon(QtGui.QIcon(resource_path('Graphics/SegReg_button.png')))
        self.segmentationTransferButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.segmentationTransferButton.clicked.connect(self.segmentationTransferButton_pressed)
        self.segmentationTransferButton.setEnabled(False)
        self.segmentationTransferButton.setToolTip('Transfer segments on optical image via registration.')

        # Top layout
        spaceItem_left = QtWidgets.QSpacerItem(40, 10, QtWidgets.QSizePolicy.Expanding)
        self.HorizontalLayout_Left = QtWidgets.QHBoxLayout()
        self.HorizontalLayout_Left.addWidget(self.openM2iraView)
        self.HorizontalLayout_Left.addWidget(self.transferIRdata)
        self.HorizontalLayout_Left.addWidget(self.IRTransferSettings)
        self.HorizontalLayout_Left.addSpacerItem(spaceItem_left)
        self.HorizontalLayout_Left.addWidget(self.segmentationButton)
        self.HorizontalLayout_Left.addWidget(self.segmentationSettingsButton)
        self.HorizontalLayout_Left.addWidget(self.segmentationTransferButton)

        #IR Image
        #Edit for pixel size input
        textPixelSizeIR = QtWidgets.QLabel('<font size="3"><p style="font-variant:small-caps;"><b>px:<b></p>',
                                         self)
        self.PixelSizeIRValue = 'None'
        self.validatorInputPix = QtGui.QDoubleValidator(0, 200, 2, self)
        self.validatorInputPix.setLocale(self.locale())
        self.PixelSizeIR = QtWidgets.QLineEdit(self)
        self.PixelSizeIR.setLocale(self.locale())
        self.PixelSizeIR.setValidator(self.validatorInputPix)
        self.PixelSizeIR.setPlaceholderText('None')
        self.PixelSizeIR.returnPressed.connect(self.PixelSizeIREnter)
        self.PixelSizeIR.setToolTip('Specify pixel size of IR image.')

        # Edits for Colormap
        self.ColormapBox = QtWidgets.QComboBox(self)
        self.ColormapBox.addItem(QtGui.QIcon(resource_path("Icons/gray_icon.png")), "")
        self.ColormapBox.addItem(QtGui.QIcon(resource_path("Icons/binary_icon.png")), "")
        self.ColormapBox.addItem(QtGui.QIcon(resource_path("Icons/gist_icon.png")), "")
        self.ColormapBox.addItem(QtGui.QIcon(resource_path("Icons/inferno_icon.png")), "")
        self.ColormapBox.addItem(QtGui.QIcon(resource_path("Icons/PiYg_icon.png")), "")
        self.ColormapBox.currentTextChanged.connect(self.on_ColormapBox_changed)
        self.ColormapBox.setIconSize(QtCore.QSize(40, 15))
        self.ColormapBox.setToolTip('Select colormap.')

        # Edits for Colormap
        self.ColormapBox2 = QtWidgets.QComboBox(self)
        self.ColormapBox2.addItem(QtGui.QIcon(resource_path("Icons/gray_icon.png")), "")
        self.ColormapBox2.addItem(QtGui.QIcon(resource_path("Icons/gist_icon.png")), "")
        self.ColormapBox2.currentTextChanged.connect(self.on_showMaskSeg_changed)
        self.ColormapBox2.setIconSize(QtCore.QSize(40, 15))
        self.ColormapBox2.setToolTip('Select colormap.')

        # random image
        randomImage = random.random((1001, 1001))
        maxSizeX = 300
        maxSizeY = 300

        # Upper image window
        self.winLambda0 = pg.GraphicsLayoutWidget()
        self.winLambda0.setBackground(0.21)
        self.winLambda0.ci.setContentsMargins(0, 0, 0, 0)
        self.winLambda0.ci.setSpacing(0)
        self.viewLambda0 = self.winLambda0.addViewBox(enableMouse=True)
        self.viewLambda0.setAspectLocked(True)
        self.viewLambda0.invertY(False)
        yMax = randomImage.shape[1]
        xMax = randomImage.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewLambda0.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.imgLambda0 = pg.ImageItem()
        self.viewLambda0.addItem(self.imgLambda0)
        self.imgLambda0.setImage(randomImage)
        self.winLambda0.setMinimumSize(maxSizeY+10, maxSizeX+10)
        self.winLambda0.setMaximumSize(maxSizeY+10, maxSizeX+10)
        self.winLambda0.scene().sigMouseMoved.connect(self.OnClick_IR)

        # Lower image window
        self.winSegment = pg.GraphicsLayoutWidget()
        self.winSegment.setBackground(0.21)
        self.winSegment.ci.setContentsMargins(0, 0, 0, 0)
        self.winSegment.ci.setSpacing(0)
        self.viewSegment = self.winSegment.addViewBox(enableMouse=True, enableMenu = False)
        self.viewSegment.setAspectLocked(True)
        self.viewSegment.invertY(False)
        yMax = randomImage.shape[1]
        xMax = randomImage.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewSegment.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.imgSegment = pg.ImageItem()
        self.viewSegment.addItem(self.imgSegment)
        self.imgSegment.setImage(randomImage)
        self.winSegment.setMinimumSize(maxSizeY + 10, maxSizeX + 10)
        self.winSegment.setMaximumSize(maxSizeY + 10, maxSizeX + 10)
        self.winSegment.scene().sigMouseClicked.connect(self.onImageSegmentation_clicked)

        # Above upper image
        # Next wavenumber button
        self.nextLeft = QtWidgets.QPushButton('', self)
        self.nextLeft.setMaximumSize(maxSize, maxSize)
        self.nextLeft.setMinimumSize(minSize, minSize)
        self.nextLeft.setIcon(QtGui.QIcon(resource_path('Graphics/rotateLeft.png')))
        self.nextLeft.setIconSize(QtCore.QSize(15, 15))
        self.nextLeft.clicked.connect(self.nextLeft_pressed)
        self.nextLeft.setToolTip('Previous image.')

        # Previous wavenumber button
        self.nextRight = QtWidgets.QPushButton('', self)
        self.nextRight.setMaximumSize(maxSize, maxSize)
        self.nextRight.setMinimumSize(minSize, minSize)
        self.nextRight.setIcon(QtGui.QIcon(resource_path('Graphics/rotateRight.png')))
        self.nextRight.setIconSize(QtCore.QSize(15, 15))
        self.nextRight.clicked.connect(self.nextRight_pressed)
        self.nextRight.setToolTip('Next image.')

        # Field to display the selected wavenumber
        self.currentWavenumber = 'None'
        self.validatorcurrentWavenumber = QtGui.QDoubleValidator(0, 15000, 0, self)
        self.validatorcurrentWavenumber.setLocale(self.locale())
        self.currentWavenumberInput = QtWidgets.QLineEdit(self)
        self.currentWavenumberInput.setLocale(self.locale())
        self.currentWavenumberInput.setValidator(self.validatorcurrentWavenumber)
        self.currentWavenumberInput.setPlaceholderText(str(self.currentWavenumber))
        self.currentWavenumberInput.setEnabled(False)
        self.currentWavenumberInput.setToolTip('Shows current wavenumber.')

        # Show if MIR images were selected
        self.QVButtonShow = QtWidgets.QPushButton('', self)
        self.QVButtonShow.setMaximumSize(maxSize, maxSize)
        self.QVButtonShow.setMinimumSize(minSize, minSize)
        self.QVButtonShow.setIcon(QtGui.QIcon(resource_path('Graphics/QuantumViewer4.png')))
        self.QVButtonShow.setIconSize(QtCore.QSize(15, 15))
        self.QVButtonShow.setCheckable(True)
        self.QVButtonShow.setChecked(True)
        self.QVButtonShow.clicked.connect(self.QVButtonShow_pressed)
        self.QVButtonShow.setToolTip('Select IR images as displayed image type.')

        # import regions of interest as an label image
        self.Import_ROI_TIF_button = QtWidgets.QPushButton('', self)
        self.Import_ROI_TIF_button.setMaximumSize(maxSize, maxSize)
        self.Import_ROI_TIF_button.setMinimumSize(minSize, minSize)
        self.Import_ROI_TIF_button.setIcon(QtGui.QIcon(resource_path('Graphics/ImportROITif.png')))
        self.Import_ROI_TIF_button.setIconSize(QtCore.QSize(15, 15))
        self.Import_ROI_TIF_button.clicked.connect(self.Import_ROI_TIF_button_pressed)
        self.Import_ROI_TIF_button.setToolTip('Import label image (.tif).')

        # Above lower image
        # Show image mask
        self.maskMeanButtonShow = QtWidgets.QPushButton('', self)
        self.maskMeanButtonShow.setMaximumSize(maxSize, maxSize)
        self.maskMeanButtonShow.setMinimumSize(minSize, minSize)
        self.maskMeanButtonShow.setIcon(QtGui.QIcon(resource_path('Graphics/MaskButton.png')))
        self.maskMeanButtonShow.setIconSize(QtCore.QSize(15, 15))
        self.maskMeanButtonShow.setCheckable(True)
        self.maskMeanButtonShow.setChecked(False)
        self.maskMeanButtonShow.setEnabled(False)
        self.maskMeanButtonShow.clicked.connect(self.maskMeanButtonShow_pressed)
        self.maskMeanButtonShow.setToolTip('Show image mask.')

        # Show segmentation
        self.segButtonShow = QtWidgets.QPushButton('', self)
        self.segButtonShow.setMaximumSize(maxSize, maxSize)
        self.segButtonShow.setMinimumSize(minSize, minSize)
        self.segButtonShow.setIcon(QtGui.QIcon(resource_path('Graphics/SegmentationButtonFull.png')))
        self.segButtonShow.setIconSize(QtCore.QSize(15, 15))
        self.segButtonShow.setCheckable(False)
        self.segButtonShow.setChecked(False)
        self.segButtonShow.setEnabled(False)
        self.segButtonShow.clicked.connect(self.segButtonShow_pressed)
        self.segButtonShow.setToolTip('Show segmentation.')

        # Show segmentation with selected regions
        self.segButtonRightShow = QtWidgets.QPushButton('', self)
        self.segButtonRightShow.setMaximumSize(maxSize, maxSize)
        self.segButtonRightShow.setMinimumSize(minSize, minSize)
        self.segButtonRightShow.setIcon(QtGui.QIcon(resource_path('Graphics/SegmentationButtonArea.png')))
        self.segButtonRightShow.setIconSize(QtCore.QSize(15, 15))
        self.segButtonRightShow.setCheckable(False)
        self.segButtonRightShow.setChecked(False)
        self.segButtonRightShow.setEnabled(False)
        self.segButtonRightShow.clicked.connect(self.segButtonRightShow_pressed)
        self.segButtonRightShow.setToolTip('Show selected segments.')

        # Show selected regions
        self.segButtonSelectedShow = QtWidgets.QPushButton('', self)
        self.segButtonSelectedShow.setMaximumSize(maxSize, maxSize)
        self.segButtonSelectedShow.setMinimumSize(minSize, minSize)
        self.segButtonSelectedShow.setIcon(QtGui.QIcon(resource_path('Graphics/SegmentationButtonAreaSeg.png')))
        self.segButtonSelectedShow.setIconSize(QtCore.QSize(15, 15))
        self.segButtonSelectedShow.setCheckable(False)
        self.segButtonSelectedShow.setChecked(False)
        self.segButtonSelectedShow.setEnabled(False)
        self.segButtonSelectedShow.clicked.connect(self.segButtonSelectedShow_pressed)
        self.segButtonSelectedShow.setToolTip('Show selected segments for transfer.')

        # Save label image
        self.saveTIFF_Button_Segmentation = QtWidgets.QPushButton('', self)
        self.saveTIFF_Button_Segmentation.setMaximumSize(maxSize, maxSize)
        self.saveTIFF_Button_Segmentation.setMinimumSize(minSize, minSize)
        self.saveTIFF_Button_Segmentation.setIcon(QtGui.QIcon(resource_path('Graphics/ROI_Tif_Button.png')))
        self.saveTIFF_Button_Segmentation.setIconSize(QtCore.QSize(15, 15))
        self.saveTIFF_Button_Segmentation.clicked.connect(self.saveTIFF_Segmentation_pressed)
        self.saveTIFF_Button_Segmentation.setToolTip('Save segmentation as .tiff image.')

        # Save selected regions as label image
        self.saveTIFF_Button_Segmentation_Selected = QtWidgets.QPushButton('', self)
        self.saveTIFF_Button_Segmentation_Selected.setMaximumSize(maxSize, maxSize)
        self.saveTIFF_Button_Segmentation_Selected.setMinimumSize(minSize, minSize)
        self.saveTIFF_Button_Segmentation_Selected.setIcon(QtGui.QIcon(resource_path('Graphics/ROI_Tif_Button_Selected.png')))
        self.saveTIFF_Button_Segmentation_Selected.setIconSize(QtCore.QSize(15, 15))
        self.saveTIFF_Button_Segmentation_Selected.clicked.connect(self.saveTIFF_Segmentation_Selected_pressed)
        self.saveTIFF_Button_Segmentation_Selected.setToolTip('Save selected segmentation as .tiff image.')

        # Layout
        spaceItem_1 = QtWidgets.QSpacerItem(40, 10, QtWidgets.QSizePolicy.Expanding)
        spaceItem_2 = QtWidgets.QSpacerItem(100, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayout = QtWidgets.QHBoxLayout()
        VerticalLayout.addWidget(self.ColormapBox)
        VerticalLayout.addWidget(self.currentWavenumberInput)
        VerticalLayout.addWidget(self.nextLeft)
        VerticalLayout.addWidget(self.nextRight)
        VerticalLayout.addSpacerItem(spaceItem_1)
        VerticalLayout.addWidget(textPixelSizeIR)
        VerticalLayout.addWidget(self.PixelSizeIR)
        VerticalLayout.addSpacerItem(spaceItem_2)
        VerticalLayout.addWidget(self.QVButtonShow)

        # Layout
        spaceVerticalLayout1 = QtWidgets.QSpacerItem(70, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayout1 = QtWidgets.QHBoxLayout()
        VerticalLayout1.addWidget(self.ColormapBox2)
        VerticalLayout1.addSpacerItem(spaceVerticalLayout1)
        VerticalLayout1.addWidget(self.Import_ROI_TIF_button)
        VerticalLayout1.addWidget(self.maskMeanButtonShow)
        VerticalLayout1.addWidget(self.segButtonShow)
        VerticalLayout1.addWidget(self.segButtonRightShow)
        VerticalLayout1.addWidget(self.segButtonSelectedShow)
        VerticalLayout1.addWidget(self.saveTIFF_Button_Segmentation)
        VerticalLayout1.addWidget(self.saveTIFF_Button_Segmentation_Selected)

        #include layouts into sub grid
        self.subGridLeft.addLayout(self.HorizontalLayout_Left, 0, 0)
        self.subGridLeft.addLayout(VerticalLayout, 1, 0)
        self.subGridLeft.addWidget(self.winLambda0, 2, 0, 2, 2)
        self.subGridLeft.addLayout(VerticalLayout1, 4, 0)
        self.subGridLeft.addWidget(self.winSegment, 5, 0, 2, 2)


#Right layout - "optical layout"
        # Opt Buttons
        # button for importing the refence image
        self.importOptdata = QtWidgets.QPushButton('', self)
        self.importOptdata.setMaximumSize(sizeMax, sizeMax)
        self.importOptdata.setMinimumSize(sizeMin, sizeMin)
        self.importOptdata.setIcon(QtGui.QIcon(resource_path('Graphics/SelectFolderButton2.png')))
        self.importOptdata.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.importOptdata.clicked.connect(self.importOptButton_pressed)
        self.importOptdata.setEnabled(True)
        self.importOptdata.setToolTip('Import reference image.')

        # button for the settings of the import
        self.importOptdataSettings = QtWidgets.QPushButton('', self)
        self.importOptdataSettings.setMaximumSize(sizeMax, sizeMax)
        self.importOptdataSettings.setMinimumSize(sizeMin, sizeMin)
        self.importOptdataSettings.setIcon(QtGui.QIcon(resource_path('Graphics/Settings_Import_Tiff.png')))
        self.importOptdataSettings.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.importOptdataSettings.clicked.connect(self.importOptButtonSettings_pressed)
        self.importOptdataSettings.setEnabled(True)
        self.OptSettingsWindow = None
        self.importOptdata.setToolTip('Opens setting window for import.')

        # obtain image for sub ROI used for registration
        self.getROIButton = QtWidgets.QPushButton('', self)
        self.getROIButton.setMaximumSize(sizeMax, sizeMax)
        self.getROIButton.setMinimumSize(sizeMin, sizeMin)
        self.getROIButton.setIcon(QtGui.QIcon(resource_path('Graphics/roi_button.png')))
        self.getROIButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.getROIButton.clicked.connect(self.getROIButton_pressed)
        self.getROIButton.setEnabled(False)
        self.getROIButton.setToolTip('Creates image subset from rectangle.')

        #  "run" the modification of the image mask
        self.modifyMaskButton = QtWidgets.QPushButton('', self)
        self.modifyMaskButton.setMaximumSize(sizeMax, sizeMax)
        self.modifyMaskButton.setMinimumSize(sizeMin, sizeMin)
        self.modifyMaskButton.setIcon(QtGui.QIcon(resource_path('Graphics/RunButton.png')))
        self.modifyMaskButton.setIconSize(QtCore.QSize(sizeIcon-5, sizeIcon-5))
        self.modifyMaskButton.clicked.connect(self.modifyMaskButton_pressed)
        self.modifyMaskButton.setToolTip('Executes the modification of the image mask or labels.')

        # define the operations for modification of the image mask
        self.maskSettingsButton = QtWidgets.QPushButton('', self)
        self.maskSettingsButton.setMaximumSize(sizeMax, sizeMax)
        self.maskSettingsButton.setMinimumSize(sizeMin, sizeMin)
        self.maskSettingsButton.setIcon(QtGui.QIcon(resource_path('Graphics/SettingsMaskButton.png')))
        self.maskSettingsButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.maskSettingsButton.clicked.connect(self.maskSettingsButton_pressed)
        self.maskSettingsWindow = None
        self.maskSettingsButton.setToolTip('Opens setting dialog.')

        # perform image registration
        self.regButton = QtWidgets.QPushButton('', self)
        self.regButton.setMaximumSize(sizeMax, sizeMax)
        self.regButton.setMinimumSize(sizeMin, sizeMin)
        self.regButton.setIcon(QtGui.QIcon(resource_path('Graphics/reg_button.png')))
        self.regButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.regButton.clicked.connect(self.regButton_pressed)
        self.regButton.setEnabled(False)
        self.regButton.setToolTip('Perform image registration.')

        # settings for image registration
        self.regSettingsButton = QtWidgets.QPushButton('', self)
        self.regSettingsButton.setMaximumSize(sizeMax, sizeMax)
        self.regSettingsButton.setMinimumSize(sizeMin, sizeMin)
        self.regSettingsButton.setIcon(QtGui.QIcon(resource_path('Graphics/SettingsRegistrationButton.png')))
        self.regSettingsButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.regSettingsButton.clicked.connect(self.regSettingsButton_pressed)
        self.registrationSettingsWindow = None
        self.regSettingsButton.setToolTip('Open dialog window for image registration.')

        # settings for image registration
        self.showROIButton = QtWidgets.QPushButton('', self)
        self.showROIButton.setMaximumSize(sizeMax, sizeMax)
        self.showROIButton.setMinimumSize(sizeMin, sizeMin)
        self.showROIButton.setIcon(QtGui.QIcon(resource_path('Graphics/show_mask.png')))
        self.showROIButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.showROIButton.clicked.connect(self.showROIButton_pressed)
        self.showROIButton.setToolTip('Generates region-of-interest outlines on reference image.')

        # apply contour finding
        self.findContoursButton = QtWidgets.QPushButton('', self)
        self.findContoursButton.setMaximumSize(sizeMax, sizeMax)
        self.findContoursButton.setMinimumSize(sizeMin, sizeMin)
        self.findContoursButton.setIcon(QtGui.QIcon(resource_path('Graphics/findcontour.png')))
        self.findContoursButton.setIconSize(QtCore.QSize(sizeIcon-5, sizeIcon-5))
        self.findContoursButton.clicked.connect(self.findContoursButton_pressed)
        self.findContoursButton.setToolTip('Generates outlines.')


        # import .mis file (path)
        self.importMisButton = QtWidgets.QPushButton('', self)
        self.importMisButton.setMaximumSize(sizeMax, sizeMax)
        self.importMisButton.setMinimumSize(sizeMin, sizeMin)
        self.importMisButton.setIcon(QtGui.QIcon(resource_path('Graphics/ImportMisNeu.png')))
        self.importMisButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.importMisButton.clicked.connect(self.importMIS)
        self.importMisButton.setEnabled(True)
        self.importMisButton.setToolTip('Imports .mis file (Reference to mis file).')


        # write data into .mis file
        self.writeMisButton = QtWidgets.QPushButton('', self)
        self.writeMisButton.setMaximumSize(sizeMax, sizeMax)
        self.writeMisButton.setMinimumSize(sizeMin, sizeMin)
        self.writeMisButton.setIcon(QtGui.QIcon(resource_path('Graphics/addregion2mis.png')))
        self.writeMisButton.setIconSize(QtCore.QSize(sizeIcon, sizeIcon))
        self.writeMisButton.clicked.connect(self.writeMIS)
        self.writeMisButton.setEnabled(False)
        self.writeMisButton.setToolTip('Add region information to .mis file.')

        # create xml for saving ROI information
        self.newXMLButton = QtWidgets.QPushButton('', self)
        self.newXMLButton.setMaximumSize(sizeMax, sizeMax)
        self.newXMLButton.setMinimumSize(sizeMin, sizeMin)
        self.newXMLButton.setIcon(QtGui.QIcon(resource_path('Graphics/SaveROI2XML.png')))
        self.newXMLButton.setIconSize(QtCore.QSize(sizeIcon-5, sizeIcon-5))
        self.newXMLButton.clicked.connect(self.newXMLButton_pressed)
        self.newXMLButton.setEnabled(True)
        self.newXMLButton.setToolTip('Saves region information into xml file.')

        # add RPO to xml
        self.addXMLButton = QtWidgets.QPushButton('', self)
        self.addXMLButton.setMaximumSize(sizeMax, sizeMax)
        self.addXMLButton.setMinimumSize(sizeMin, sizeMin)
        self.addXMLButton.setIcon(QtGui.QIcon(resource_path('Graphics/AddROI2XML.png')))
        self.addXMLButton.setIconSize(QtCore.QSize(sizeIcon-5, sizeIcon-5))
        self.addXMLButton.clicked.connect(self.addXMLButton_pressed)
        self.addXMLButton.setEnabled(True)
        self.addXMLButton.setToolTip('Adds region information into xml file.')

        # import ROI from xml
        self.showXMLButton = QtWidgets.QPushButton('', self)
        self.showXMLButton.setMaximumSize(sizeMax, sizeMax)
        self.showXMLButton.setMinimumSize(sizeMin, sizeMin)
        self.showXMLButton.setIcon(QtGui.QIcon(resource_path('Graphics/ImportXML2Shape.png')))
        self.showXMLButton.setIconSize(QtCore.QSize(sizeIcon-5, sizeIcon-5))
        self.showXMLButton.clicked.connect(self.showXMLButton_pressed)
        self.showXMLButton.setEnabled(True)
        self.showXMLButton.setToolTip('Import of region information from xml file.')

        # define vertical sub grid layout
        self.subGridOptButtonsVerticalLayout = QtWidgets.QHBoxLayout()
        spaceItem_1 = QtWidgets.QSpacerItem(50, 10, QtWidgets.QSizePolicy.Expanding)
        spaceItem_2 = QtWidgets.QSpacerItem(50, 10, QtWidgets.QSizePolicy.Expanding)
        self.subGridOptButtonsVerticalLayout.addWidget(self.importOptdata)
        self.subGridOptButtonsVerticalLayout.addWidget(self.importOptdataSettings)
        self.subGridOptButtonsVerticalLayout.addSpacerItem(spaceItem_1)
        self.subGridOptButtonsVerticalLayout.addWidget(self.getROIButton)
        self.subGridOptButtonsVerticalLayout.addSpacerItem(spaceItem_1)
        self.subGridOptButtonsVerticalLayout.addWidget(self.modifyMaskButton)
        self.subGridOptButtonsVerticalLayout.addWidget(self.maskSettingsButton)
        self.subGridOptButtonsVerticalLayout.addSpacerItem(spaceItem_1)
        self.subGridOptButtonsVerticalLayout.addWidget(self.regButton)
        self.subGridOptButtonsVerticalLayout.addWidget(self.regSettingsButton)
        self.subGridOptButtonsVerticalLayout.addSpacerItem(spaceItem_1)
        self.subGridOptButtonsVerticalLayout.addWidget(self.showROIButton)
        self.subGridOptButtonsVerticalLayout.addWidget(self.findContoursButton)
        self.subGridOptButtonsVerticalLayout.addSpacerItem(spaceItem_1)
        self.subGridOptButtonsVerticalLayout.addWidget(self.importMisButton)
        self.subGridOptButtonsVerticalLayout.addWidget(self.writeMisButton)
        self.subGridOptButtonsVerticalLayout.addSpacerItem(spaceItem_1)
        self.subGridOptButtonsVerticalLayout.addWidget(self.newXMLButton)
        self.subGridOptButtonsVerticalLayout.addWidget(self.addXMLButton)
        self.subGridOptButtonsVerticalLayout.addWidget(self.showXMLButton)
        self.subGridOptButtonsVerticalLayout.addSpacerItem(spaceItem_2)

        # Opt Show
        self.subWidgetOptShow = QtWidgets.QWidget(self)
        self.subGridOptShow = QtWidgets.QGridLayout(self.subWidgetOptShow)

        self.winOptZoom = pg.GraphicsLayoutWidget()
        self.winOptZoom.setBackground(0.21)
        self.winOptZoom.ci.setContentsMargins(0, 0, 0, 0)
        self.winOptZoom.ci.setSpacing(0)
        self.viewOptZoom = self.winOptZoom.addViewBox(enableMouse=True, enableMenu=False)
        self.viewOptZoom.setAspectLocked(True)
        self.viewOptZoom.invertY(False)
        yMax = randomImage.shape[1]
        xMax = randomImage.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewOptZoom.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.imgOptZoom = pg.ImageItem()
        self.viewOptZoom.addItem(self.imgOptZoom)
        self.imgOptZoom.setImage(randomImage)
        self.winOptZoom.setMinimumSize(maxSizeY + 10, maxSizeX + 10)
        self.winOptZoom.setMaximumSize(maxSizeY + 10, maxSizeX + 10)
        self.winOptZoom.scene().sigMouseMoved.connect(self.OnClick_OptZoom)

        self.winOpt = pg.GraphicsLayoutWidget()
        self.winOpt.setBackground(0.45)
        self.winOpt.ci.setContentsMargins(0, 0, 0, 0)
        self.winOpt.ci.setSpacing(0)
        self.viewOpt = self.winOpt.addViewBox(enableMouse=True)
        self.viewOpt.setAspectLocked(True)
        self.viewOpt.invertY(False)
        self.imgOpt = pg.ImageItem()
        self.viewOpt.addItem(self.imgOpt)
        self.imgOpt.setImage(randomImage)
        self.winOpt.setMinimumSize(int(2.5 *maxSizeY + 10), maxSizeX + 10)
        self.winOpt.setMaximumSize(int(2.5 * maxSizeY + 10), maxSizeX + 10)
        self.winOpt.scene().sigMouseClicked.connect(self.on_OptImage_clicked)
        self.winOpt.scene().sigMouseMoved.connect(self.OnClick_Opt)

        # Opt Settings
        self.subWidgetOptSettings = QtWidgets.QWidget(self)
        self.subGridOptSettings = QtWidgets.QGridLayout(self.subWidgetOptSettings)

        textPixelSizeOpt = QtWidgets.QLabel(
            '<font size="3"><p style="font-variant:small-caps;"><b>px (x/y):<b></p>',
            self)

        # QDouble Validator für pixel size input
        self.PixelSizeOptValue_x = 'None'
        self.validatorInputPixOpt_x = QtGui.QDoubleValidator(0, 200, 7, self)
        self.validatorInputPixOpt_x.setLocale(self.locale())
        self.PixelSizeOpt_x = QtWidgets.QLineEdit(self)
        self.PixelSizeOpt_x.setLocale(self.locale())
        self.PixelSizeOpt_x.setValidator(self.validatorInputPixOpt_x)
        self.PixelSizeOpt_x.setPlaceholderText('None')
        self.PixelSizeOpt_x.returnPressed.connect(self.PixelSizeOptEnter_x)
        self.PixelSizeOpt_x.setMaximumSize(sizeMax,sizeMax)

        # QDouble Validator für pixel size input
        self.PixelSizeOptValue_y = 'None'
        self.validatorInputPixOpt_y = QtGui.QDoubleValidator(0, 200, 7, self)
        self.validatorInputPixOpt_y.setLocale(self.locale())
        self.PixelSizeOpt_y = QtWidgets.QLineEdit(self)
        self.PixelSizeOpt_y.setLocale(self.locale())
        self.PixelSizeOpt_y.setValidator(self.validatorInputPixOpt_y)
        self.PixelSizeOpt_y.setPlaceholderText('None')
        self.PixelSizeOpt_y.returnPressed.connect(self.PixelSizeOptEnter_y)
        self.PixelSizeOpt_y.setMaximumSize(sizeMax, sizeMax)

        # for tab#1
        # ROI list for "infrared" data
        self.RegionsListTree = QtWidgets.QTreeWidget()
        self.RegionsListTree.setColumnCount(3)
        self.RegionsListTree.setHeaderLabels(['', '', 'ID'])
        self.InfraredTree = QtWidgets.QTreeWidgetItem(self.RegionsListTree)
        self.InfraredTree.setText(0, "Infrared")

        # ROI list for "shapes", e.g. if one deduce it from optical images
        self.ShapesTree = QtWidgets.QTreeWidgetItem(self.RegionsListTree)
        self.ShapesTree.setText(0, "Shapes")
        self.RegionsListTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.RegionsListTree.customContextMenuRequested.connect(self.openMenu)
        header = self.RegionsListTree.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        # options for .mis writing
        textExportMis = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>Mis Parameters:<b></p>',
                                         self)

        # Set area type
        self.defaultpolygontypeMIS = QtWidgets.QComboBox(self)
        self.defaultpolygontypeMIS.setObjectName(("comboBox"))
        self.defaultpolygontypeMIS.addItem("Area")
        self.defaultpolygontypeMIS.addItem("ROI")
        self.defaultpolygontypeMIS.setMaximumSize(80,20)
        self.defaultpolygontypeMIS.setToolTip('Region type for .mis file.')

        # Set pixel size
        self.defaultrasterInput = QtWidgets.QComboBox(self)
        self.defaultrasterInput.setObjectName(("comboBox"))
        self.defaultrasterInput.addItem("5 um")
        self.defaultrasterInput.addItem("10 um")
        self.defaultrasterInput.addItem("20 um")
        self.defaultrasterInput.addItem("30 um")
        self.defaultrasterInput.addItem("40 um")
        self.defaultrasterInput.addItem("50 um")
        self.defaultrasterInput.addItem("100 um")
        self.defaultrasterInput.setMaximumSize(80, 20)
        self.defaultrasterInput.setToolTip('Pixel size for region type for .mis file.')

        # Set ROI name
        self.defaultareanameInputString = 'default area name'
        self.defaultareanameInput = QtWidgets.QLineEdit(self)
        self.defaultareanameInput.setLocale(self.locale())
        self.defaultareanameInput.setPlaceholderText('default area name')
        self.defaultareanameInput.returnPressed.connect(self.defaultareanameInputEnter)
        self.defaultareanameInput.setToolTip('Region name.')

        # options for shape generation, 1: normal, 2: with holes, 3: open holes
        textImageShapeOption = QtWidgets.QLabel('<font size="4"><p style="font-variant:small-caps;"><b>shape options:<b></p>', self)
        textOffset_x = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Offset x:<b></p>', self)
        textOffset_y = QtWidgets.QLabel(
            '<font size="4"><p style="font-variant:small-caps;"><b>Offset y:<b></p>', self)
        self.BoxShapeOption = QtWidgets.QComboBox(self)
        self.BoxShapeOption.setObjectName(("comboBoxShape"))
        self.BoxShapeOption.addItem("normal")
        self.BoxShapeOption.addItem("holes")
        self.BoxShapeOption.addItem("open holes")
        self.BoxShapeOption.setMaximumSize(80, 20)
        self.BoxShapeOption.setToolTip('Shape options.')

        # offset for shifting ROIs by x/y pixels during transfer to the reference image
        self.OffsetXInputValue = '0'
        self.validatorOffsetXInput = QtGui.QDoubleValidator(-1500, 1500, 0, self)
        self.validatorOffsetXInput.setLocale(self.locale())
        self.OffsetXInput = QtWidgets.QLineEdit(self)
        self.OffsetXInput.setLocale(self.locale())
        self.OffsetXInput.setValidator(self.validatorOffsetXInput)
        self.OffsetXInput.setPlaceholderText('0')
        self.OffsetXInput.returnPressed.connect(self.OffsetXInputEnter)
        self.OffsetXInput.setMaximumSize(80, 20)

        self.OffsetYInputValue = '0'
        self.validatorOffsetYInput = QtGui.QDoubleValidator(-1500, 1500, 0, self)
        self.validatorOffsetYInput.setLocale(self.locale())
        self.OffsetYInput = QtWidgets.QLineEdit(self)
        self.OffsetYInput.setLocale(self.locale())
        self.OffsetYInput.setValidator(self.validatorOffsetYInput)
        self.OffsetYInput.setPlaceholderText('0')
        self.OffsetYInput.returnPressed.connect(self.OffsetYInputEnter)
        self.OffsetYInput.setMaximumSize(80, 20)

        # Set layout
        spaceItem_tab = QtWidgets.QSpacerItem(10, 80, QtWidgets.QSizePolicy.Expanding)
        SpacerLayout = QtWidgets.QHBoxLayout()
        SpacerLayout.addSpacerItem(spaceItem_tab)
        self.subWidgetTabRegions = QtWidgets.QWidget(self)
        self.subGridTabRegionsLayout = QtWidgets.QGridLayout(self.subWidgetTabRegions)
        self.subGridTabRegionsLayout.addWidget(self.RegionsListTree, 0, 0, 8, 3)
        self.subGridTabRegionsLayout.addWidget(textExportMis, 0, 3)
        self.subGridTabRegionsLayout.addWidget(self.defaultpolygontypeMIS, 1, 3)
        self.subGridTabRegionsLayout.addWidget(self.defaultrasterInput, 1, 4)
        self.subGridTabRegionsLayout.addWidget(self.defaultareanameInput, 2, 3, 1, 2)
        self.subGridTabRegionsLayout.addWidget(textImageShapeOption, 3, 3)
        self.subGridTabRegionsLayout.addWidget(self.BoxShapeOption, 4, 3)
        self.subGridTabRegionsLayout.addWidget(textOffset_x, 5, 3)
        self.subGridTabRegionsLayout.addWidget(self.OffsetXInput, 6, 3)
        self.subGridTabRegionsLayout.addWidget(textOffset_y, 5, 4)
        self.subGridTabRegionsLayout.addWidget(self.OffsetYInput, 6, 4)
        self.subGridTabRegionsLayout.addLayout(SpacerLayout, 7, 3, 1, 2)

        # Define and create QTabWidget
        self.OptTabWidget = QtWidgets.QTabWidget(self)
        self.OptTabWidget.addTab(self.subWidgetTabRegions, "Regions of Interest")

#Buttons right upper Image
        # Colormap combo box
        self.ColormapBoxOpt = QtWidgets.QComboBox(self)
        self.ColormapBoxOpt.addItem(QtGui.QIcon(resource_path("Icons/gray_icon.png")), "")
        self.ColormapBoxOpt.addItem(QtGui.QIcon(resource_path("Icons/binary_icon.png")), "")
        self.ColormapBoxOpt.addItem(QtGui.QIcon(resource_path("Icons/gist_icon.png")), "")
        self.ColormapBoxOpt.addItem(QtGui.QIcon(resource_path("Icons/inferno_icon.png")), "")
        self.ColormapBoxOpt.addItem(QtGui.QIcon(resource_path("Icons/PiYg_icon.png")), "")
        self.ColormapBoxOpt.currentTextChanged.connect(self.on_ColormapBoxOpt_changed)
        self.ColormapBoxOpt.setIconSize(QtCore.QSize(40, 15))
        self.ColormapBoxOpt.setToolTip('Select colormap for regions-of-interest.')

        # Select if colormap is inverted or not
        self.ColormapInverted = QtWidgets.QPushButton('', self)
        self.ColormapInverted.setMaximumSize(maxSize, maxSize)
        self.ColormapInverted.setMinimumSize(minSize, minSize)
        self.ColormapInverted.setIcon(QtGui.QIcon(resource_path('Graphics/reverseIntensityIcon.png')))
        self.ColormapInverted.setIconSize(QtCore.QSize(15, 15))
        self.ColormapInverted.clicked.connect(self.on_ColormapInverted_pressed)
        self.ColormapInverted.setCheckable(True)
        self.ColormapInverted.setChecked(True)
        self.ColormapInverted.setToolTip('Inverts the visualization.')

        # Toggle to IR image
        self.IR_Button = QtWidgets.QPushButton('', self)
        self.IR_Button.setMaximumSize(maxSize, maxSize)
        self.IR_Button.setMinimumSize(minSize, minSize)
        self.IR_Button.setIcon(QtGui.QIcon(resource_path('Graphics/IR_button.png')))
        self.IR_Button.setIconSize(QtCore.QSize(15, 15))
        self.IR_Button.setCheckable(True)
        self.IR_Button.setChecked(False)
        self.IR_Button.setEnabled(False)
        self.IR_Button.clicked.connect(self.IR_Button_pressed)
        self.IR_Button.setToolTip('Show registered IR image.')

        # Toggle to IR mask
        self.IRmask_Button = QtWidgets.QPushButton('', self)
        self.IRmask_Button.setMaximumSize(maxSize, maxSize)
        self.IRmask_Button.setMinimumSize(minSize, minSize)
        self.IRmask_Button.setIcon(QtGui.QIcon(resource_path('Graphics/IRmask_buttonNew.png')))
        self.IRmask_Button.setIconSize(QtCore.QSize(15, 15))
        self.IRmask_Button.setCheckable(True)
        self.IRmask_Button.setChecked(False)
        self.IRmask_Button.setEnabled(False)
        self.IRmask_Button.clicked.connect(self.IRmask_Button_pressed)
        self.IRmask_Button.setToolTip('Show IR mask.')

        # Toggle to optical image
        self.Opt_Button = QtWidgets.QPushButton('', self)
        self.Opt_Button.setMaximumSize(maxSize, maxSize)
        self.Opt_Button.setMinimumSize(minSize, minSize)
        self.Opt_Button.setIcon(QtGui.QIcon(resource_path('Graphics/Opt_button.png')))
        self.Opt_Button.setIconSize(QtCore.QSize(15, 15))
        self.Opt_Button.setCheckable(True)
        self.Opt_Button.setChecked(False)
        self.Opt_Button.setEnabled(True)
        self.Opt_Button.clicked.connect(self.Opt_Button_pressed)
        self.Opt_Button.setToolTip('Show image subset for reference image.')

        # Toggle to optical mask
        self.Optmask_Button = QtWidgets.QPushButton('', self)
        self.Optmask_Button.setMaximumSize(maxSize, maxSize)
        self.Optmask_Button.setMinimumSize(minSize, minSize)
        self.Optmask_Button.setIcon(QtGui.QIcon(resource_path('Graphics/Optmask_button.png')))
        self.Optmask_Button.setIconSize(QtCore.QSize(15, 15))
        self.Optmask_Button.setCheckable(True)
        self.Optmask_Button.setChecked(False)
        self.Optmask_Button.setEnabled(False)
        self.Optmask_Button.clicked.connect(self.Optmask_Button_pressed)
        self.Optmask_Button.setToolTip('Show image mask for subset  reference image.')

        # Toggle to overlay of both image masks
        self.OptIR_Button = QtWidgets.QPushButton('', self)
        self.OptIR_Button.setMaximumSize(maxSize, maxSize)
        self.OptIR_Button.setMinimumSize(minSize, minSize)
        self.OptIR_Button.setIcon(QtGui.QIcon(resource_path('Graphics/IROpt_button.png')))
        self.OptIR_Button.setIconSize(QtCore.QSize(15, 15))
        self.OptIR_Button.setCheckable(True)
        self.OptIR_Button.setChecked(False)
        self.OptIR_Button.setEnabled(False)
        self.OptIR_Button.clicked.connect(self.OptIR_Button_pressed)
        self.OptIR_Button.setToolTip('Show overlay of image masks.')

        # Toggle to regions of interest
        self.OptSeg_Button = QtWidgets.QPushButton('', self)
        self.OptSeg_Button.setMaximumSize(maxSize, maxSize)
        self.OptSeg_Button.setMinimumSize(minSize, minSize)
        self.OptSeg_Button.setIcon(QtGui.QIcon(resource_path('Graphics/SegmentationButtonAreaSeg.png')))
        self.OptSeg_Button.setIconSize(QtCore.QSize(15, 15))
        self.OptSeg_Button.setCheckable(True)
        self.OptSeg_Button.setChecked(False)
        self.OptSeg_Button.setEnabled(False)
        self.OptSeg_Button.clicked.connect(self.OptSeg_Button_pressed)
        self.OptIR_Button.setToolTip('Show label image.')

        #Layout
        spaceVerticalLayoutOpt = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutOpt = QtWidgets.QHBoxLayout()
        VerticalLayoutOpt.addWidget(self.ColormapBoxOpt)
        VerticalLayoutOpt.addWidget(self.ColormapInverted)
        VerticalLayoutOpt.addSpacerItem(spaceVerticalLayoutOpt)
        VerticalLayoutOpt.addWidget(self.Opt_Button)
        VerticalLayoutOpt.addWidget(self.Optmask_Button)
        VerticalLayoutOpt.addSpacerItem(spaceVerticalLayoutOpt)
        VerticalLayoutOpt.addWidget(self.IR_Button)
        VerticalLayoutOpt.addWidget(self.IRmask_Button)
        VerticalLayoutOpt.addSpacerItem(spaceVerticalLayoutOpt)
        VerticalLayoutOpt.addWidget(self.OptIR_Button)
        VerticalLayoutOpt.addSpacerItem(spaceVerticalLayoutOpt)
        VerticalLayoutOpt.addWidget(self.OptSeg_Button)

        # Add rectangle to the optical image view
        self.ROI_Button = QtWidgets.QPushButton('', self)
        self.ROI_Button.setMaximumSize(maxSize, maxSize)
        self.ROI_Button.setMinimumSize(minSize, minSize)
        self.ROI_Button.setIcon(QtGui.QIcon(resource_path('Graphics/ROI_button2.png')))
        self.ROI_Button.setIconSize(QtCore.QSize(15, 15))
        self.ROI_Button.clicked.connect(self.showROI)
        self.ROI_Button.setToolTip('Create rectangle for image subset selection.')

# Buttons right lower Image
        # Set teaching marks
        self.TeachingPoints_Button = QtWidgets.QPushButton('', self)
        self.TeachingPoints_Button.setMaximumSize(maxSize, maxSize)
        self.TeachingPoints_Button.setMinimumSize(minSize, minSize)
        self.TeachingPoints_Button.setIcon(QtGui.QIcon(resource_path('Graphics/SetTeachingPoints.png')))
        self.TeachingPoints_Button.setIconSize(QtCore.QSize(15, 15))
        self.TeachingPoints_Button.setCheckable(True)
        self.TeachingPoints_Button.setChecked(False)
        self.TeachingPoints_Button.setEnabled(True)
        self.TeachingPoints_Button.clicked.connect(self.teachPoint_pressed)
        self.TeachingPoints_Button.setToolTip('Add teaching points.')

        # Opacity for regions of interest
        self.opacitySlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.opacitySlider.setRange(0, 100)
        self.opacitySlider.setSingleStep(1)
        self.opacitySlider.setValue(20)
        self.opacitySlider.setEnabled(True)
        self.opacitySlider.valueChanged.connect(self.opacitySlider_changed)

        # Filling selection regions of interest
        self.FillingCheckbox = QtWidgets.QCheckBox("")
        self.FillingCheckbox.setChecked(True)

        # Color for the regions of interest
        self.AnnotationCombo = QtWidgets.QComboBox(self)
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/red_icon.png")), "")         #red
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/pink_icon.png")), "")        #pink
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/rosa_icon.png")), "")        #rosa
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/hellrosa_icon.png")), "")    #hellrosa

        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/green_icon.png")), "")       #green
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/DarkGreen_Icon.png")), "")   #DarkGreen
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/LightGreen_Icon.png")), "")  #LightGreen

        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/yellow_icon.png")), "")  #yellow
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/orange_icon.png")), "")  #orange
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/yellow_ImSc_icon.png")), "")  #yellow_ImSc

        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/black_icon.png")), "")   #black
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/grey_icon.png")), "")   #grey
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/black_ImSc_icon.png")), "")  #black_ImSc
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/brown_icon.png")), "")  #brown

        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/blue_icon.png")), "")    #blue
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/cyan_icon.png")), "")   #cyan
        self.AnnotationCombo.addItem(QtGui.QIcon(resource_path("Icons/purple_icon.png")), "") #pruple
        self.AnnotationCombo.setIconSize(QtCore.QSize(40, 15))
        self.AnnotationCombo.setToolTip('Select colormap.')

        # Layout
        spaceItem6_0 = QtWidgets.QSpacerItem(40, 10, QtWidgets.QSizePolicy.Expanding)
        spaceItem6_1 = QtWidgets.QSpacerItem(400, 10, QtWidgets.QSizePolicy.Expanding)
        spaceItem6_2 = QtWidgets.QSpacerItem(5, 10, QtWidgets.QSizePolicy.Expanding)
        VerticalLayoutOptNew = QtWidgets.QHBoxLayout()
        VerticalLayoutOptNew.addWidget(self.ROI_Button)
        VerticalLayoutOptNew.addSpacerItem(spaceItem6_0)
        VerticalLayoutOptNew.addWidget(self.TeachingPoints_Button)
        VerticalLayoutOptNew.addSpacerItem(spaceItem6_0)
        VerticalLayoutOptNew.addWidget(self.opacitySlider)
        VerticalLayoutOptNew.addWidget(self.FillingCheckbox)
        VerticalLayoutOptNew.addSpacerItem(spaceItem6_0)
        VerticalLayoutOptNew.addWidget(textPixelSizeOpt)
        VerticalLayoutOptNew.addWidget(self.PixelSizeOpt_x)
        VerticalLayoutOptNew.addWidget(self.PixelSizeOpt_y)
        VerticalLayoutOptNew.addSpacerItem(spaceItem6_1)
        VerticalLayoutOptNew.addWidget(self.AnnotationCombo)
        VerticalLayoutOptNew.addSpacerItem(spaceItem6_2)

        self.subGridOptSettings.addWidget(self.OptTabWidget, 0, 0)

        # Place Elements on RightGrid
        self.subGridRight.addLayout(self.subGridOptButtonsVerticalLayout, 0, 0, 1, 5)
        self.subGridRight.addLayout(VerticalLayoutOpt, 1, 0, 1, 2)
        self.subGridRight.addWidget(self.winOptZoom, 2, 0, 2, 2)
        self.subGridRight.addLayout(VerticalLayoutOptNew, 4, 0, 1, 5)
        self.subGridRight.addWidget(self.winOpt, 5, 0, 2, 5)
        self.subGridRight.addWidget(self.subWidgetOptSettings, 2, 2, 2, 3)

        #Place Elements to MainGrid (mainGridLayoutQR)
        self.mainGridLayoutQR.addWidget(self.subWidgetLeft, 0, 0)
        self.mainGridLayoutQR.addWidget(self.subWidgetRight, 0, 1)
        #show  Widget
        self.centralWidgetQR.setLayout(self.mainGridLayoutQR)
        self.setCentralWidget(self.centralWidgetQR)


#left
    #opens the M2iraViewer GUI
    def openM2iraView_pressed(self):
        """
        Opens the M2ira Quant Viewer.
        """
        if self.QVWindow is None:
            self.QVWindow = M2iraQuantView(parent=self)
            self.QVWindow.show()
            self.QVWindow.isVisible()

        self.transferIRdata.setEnabled(True)
        self.QVButtonShow.setChecked(True)

        self.statusBar().showMessage('M2ira Quant Viewer is open.')

    #obtain IR data from QV
    def transferIRdata_pressed(self):
        """
        Images that appear in the list of wavenumbers is "transfered" from the M2ira Quant Viewer to the M2ira Quant Reg. window.
        ToDo: Meta-data are not included or pre-defined values are hard coded.
        """
        self.QVWindow.generateItemList()

        if self.IRTransferWindow is None:
            self.wavenumbers = self.QVWindow.selectedWavenumberList.copy()
            self.image_IR = self.QVWindow.selectedimageStack.copy()
            self.image_IR = (exposure.rescale_intensity(self.image_IR, out_range=(255, 0))).astype('uint8')
            self.mask_IR_mean = (exposure.rescale_intensity(self.QVWindow.image_mask, out_range=(0, 255))).astype('uint8')
            self.image_IR_mask_mean_help = self.mask_IR_mean.copy()

            # set pixel Size to 4.66µm, 3.5x objective (hard coded so far)
            self.PixelSizeIRValue = '4.66'
            self.PixelSizeIR.clear()
            self.PixelSizeIR.setPlaceholderText(str(self.PixelSizeIRValue))

            # set min wavenumber
            self.printWavenumber(self.wavenumbers[0])

            # smoothing
            try:
                if self.IRTransferWindow.checkboxYN.isChecked() == True:
                    #gaussian smoothing
                    for i in range(len(self.wavenumbers)):
                        if self.QVButtonShow.isChecked() == True:
                            test = gaussian(self.image_IR[:, :, i], float(self.IRTransferWindow.smoothValue))
                            self.image_IR[:, :, i] = (exposure.rescale_intensity(test, out_range=(0, 255))).astype('uint8')
            except:
                pass

            self.QVButtonShow_pressed()
            self.maskMeanButtonShow_pressed()
            self.segmentationButton.setEnabled(True)
            self.maskMeanButtonShow.setEnabled(True)
        else:
            if self.IRTransferWindow.RadioButton_IR.isChecked():
                self.wavenumbers = self.QVWindow.selectedWavenumberList.copy()
                self.image_IR = self.QVWindow.selectedimageStack.copy()
                self.image_IR = (exposure.rescale_intensity(self.image_IR, out_range=(255, 0))).astype('uint8')
                self.mask_IR_mean = (exposure.rescale_intensity(self.QVWindow.image_mask, out_range=(0, 255))).astype(
                    'uint8')
                self.image_IR_mask_mean_help = self.mask_IR_mean.copy()

                # set pixel Size to 4.66µm, 3.5x objective (hard coded so far)
                self.PixelSizeIRValue = '4.66'
                self.PixelSizeIR.clear()
                self.PixelSizeIR.setPlaceholderText(str(self.PixelSizeIRValue))

                # set min wavenumber
                self.printWavenumber(self.wavenumbers[0])

                # smoothing
                try:
                    if self.IRTransferWindow.checkboxYN.isChecked() == True:
                        # gaussian smoothing
                        for i in range(len(self.wavenumbers)):
                            if self.QVButtonShow.isChecked() == True:
                                test = gaussian(self.image_IR[:, :, i], float(self.IRTransferWindow.smoothValue))
                                self.image_IR[:, :, i] = (exposure.rescale_intensity(test, out_range=(0, 255))).astype(
                                    'uint8')
                except:
                    pass

                self.QVButtonShow_pressed()
                self.maskMeanButtonShow_pressed()
                self.segmentationButton.setEnabled(True)
                self.maskMeanButtonShow.setEnabled(True)

            if self.IRTransferWindow.RadioButton_Opt.isChecked():
                print(shape(self.QVWindow.selectedimageStack)[2])
                if shape(self.QVWindow.selectedimageStack)[2] == 1:
                    self.statusBar().showMessage('Single Infrared image is selected.')

                    image_optical = gray2rgb(self.QVWindow.selectedimageStack[:, :, 0])

                    self.showOptImage(image_optical)

                    self.image_optical = image_optical.copy()
                    self.image_segment = zeros_like(self.image_optical)
                else:
                    self.statusBar().showMessage('More than one infrared image is available. Please reduce the number of elements in list to one image.')

    def showIRImages(self, image_IR):
        """
        :parameter: infrared image
        Function that is used to display the MIR images
        """
        # Define the colormap and lut
        maxlut = 255
        maxScale = 260

        color_value = self.ColormapBox.currentIndex()
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

        colormap = cm.get_cmap(color_name)
        colormap._init()
        lut = (colormap._lut * maxlut).view(ndarray)  # Convert  colormap from 0-1 to 0-255 for Qt

        #show image
        self.viewLambda0.removeItem(self.imgLambda0)
        self.viewLambda0.addItem(self.imgLambda0)
        self.imgLambda0.setImage(image_IR)
        yMax = image_IR.shape[1]
        xMax = image_IR.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewLambda0.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.viewLambda0.autoRange(padding=0)
        self.imgLambda0.setLookupTable(lut)
        self.imgLambda0.setLevels([0, maxScale])

    def showIRSegmentation(self, segmentedImage):
        """
        :parameter: label image to be displayed
        Function that is used to display the IR Segmentation/Mask etc.
        """
        # Define the colormap and lut
        maxlut = 255
        maxScale = 260

        color_value = self.ColormapBox2.currentIndex()
        if color_value == 0:
            color_name = 'gray'
        elif color_value == 1:
            color_name = 'gist_ncar_r'


        colormap = cm.get_cmap(color_name)
        colormap._init()
        lut = (colormap._lut*maxlut).view(ndarray)  # Convert colormap from 0-1 to 0-255 for Qt

        self.viewSegment.removeItem(self.imgSegment)
        self.viewSegment.addItem(self.imgSegment)
        self.imgSegment.setImage(segmentedImage[:, :])

        yMax = segmentedImage.shape[1]
        xMax = segmentedImage.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewSegment.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.viewSegment.autoRange(padding=0)
        self.imgSegment.setLookupTable(lut)
        self.imgSegment.setLevels([0, maxScale])

    def on_ColormapBox_changed(self):
        """
        Updates the MIR image once the colormap is changed.
        """
        if self.QVButtonShow.isChecked() == True:
            selected_wavenumber = int(abs(self.wavenumbers - int(self.currentWavenumber)).argmin())
            self.showIRImages(self.image_IR[:, :, selected_wavenumber])

    def on_showMaskSeg_changed(self):
        """
        Display of mask image.
        """
        if self.segButtonShow.isEnabled() == False:
            try:
                self.ColormapBox2.setCurrentText("gist_ncar_r")
                self.showIRSegmentation(self.segmented_image)
                self.segmented_image_selected_area = self.segmented_image.copy()

                self.selected_area = zeros_like(self.selected_area)

            except:
                pass
        elif self.segButtonRightShow.isEnabled() == False:
            try:
                self.ColormapBox2.setCurrentText("gist_ncar_r")
                self.showIRSegmentation(self.segmented_image_selected_area)
            except:
                pass
        elif self.segButtonSelectedShow.isEnabled() == False:
            try:
                self.ColormapBox2.setCurrentText("gray")
                self.showIRSegmentation(self.selected_area)
            except:
                pass
        elif self.maskMeanButtonShow.isEnabled() == False:
            try:
                self.ColormapBox2.setCurrentText("gray")
                self.showIRSegmentation(self.mask_IR_mean)
            except:
                pass

    def registerImageElastix(self, fixed, moving, method, iterations, fixed_pixelSize = 1, moving_pixelSize = 1):
        """
        Performs image registration using sitk.
        based on https://simpleelastix.github.io/
        :parameter: fixed - fixed image
        :parameter: moving - moving image
        :parameter: method - rigid, affine or other transformation type
        :parameter: iterations - number of iterations
        :parameter: fixed_pixelSize - pixel size of the fixed image in mm
        :parameter: moving_pixelSize - pixel size of the moving image in mm
        :returns: registered moving image as data type uint16 and tranformation parameters
        """
        fixedImage = sitk.GetImageFromArray(fixed)
        movingImage = sitk.GetImageFromArray(moving)

        fixedImage = sitk.Cast(fixedImage, sitk.sitkFloat32)
        movingImage = sitk.Cast(movingImage, sitk.sitkFloat32)

        fixed_pixelSize =  fixed_pixelSize
        moving_pixelSize =  moving_pixelSize

        fixedImage.SetSpacing((fixed_pixelSize, fixed_pixelSize))  # sets spacing (or pixel/voxel resolution)
        movingImage.SetSpacing((moving_pixelSize, moving_pixelSize))  # sets spacing (or pixel/voxel resolution)

        #mutual information
        elastixImageFilter = sitk.ElastixImageFilter()
        elastixImageFilter.SetFixedImage(fixedImage)
        elastixImageFilter.SetMovingImage(movingImage)

        if True:
            parameterMap = sitk.GetDefaultParameterMap(method)
            parameterMap['MaximumNumberOfIterations'] = [str(iterations)]

            elastixImageFilter.SetParameterMap(parameterMap)
            sitk.PrintParameterMap(parameterMap)
        else:
            pass

        elastixImageFilter.Execute()

        #puts the moving image in the same frame as the reference image
        resultImage = sitk.Cast(elastixImageFilter.GetResultImage(), sitk.sitkFloat32)
        result = sitk.GetArrayViewFromImage(resultImage)
        transformParameterMap = elastixImageFilter.GetTransformParameterMap()

        return result.astype('int16'), transformParameterMap

    def PixelSizeIREnter(self):
        """
        Set value for the pixel size.
        """
        self.PixelSizeIRValue = self.PixelSizeIR.text()
        self.PixelSizeIR.clear()
        self.PixelSizeIR.setPlaceholderText(str(self.PixelSizeIRValue))

    def printWavenumber(self, wavenumber):
        """
        Display of the current wavenumber.
        :params: wavenumber input
        """
        self.currentWavenumber = str(int(wavenumber))
        self.currentWavenumberInput.clear()
        self.currentWavenumberInput.setPlaceholderText(str(self.currentWavenumber))

    def nextLeft_pressed(self):
        """
        Get previous wavenumber.
        """
        selected_wavenumber = int(abs(self.wavenumbers - int(self.currentWavenumber)).argmin())
        if selected_wavenumber > 0:
            selected_wavenumber = selected_wavenumber - 1
            print('Selected wavenumber: ', self.wavenumbers[selected_wavenumber], 'Element number: ', selected_wavenumber)
            self.printWavenumber(self.wavenumbers[selected_wavenumber])
        self.on_ColormapBox_changed()

    def nextRight_pressed(self):
        """
        Get next wavenumber.
        """
        selected_wavenumber = int(abs(self.wavenumbers - int(self.currentWavenumber)).argmin())
        if selected_wavenumber < len(self.wavenumbers)-1:
            selected_wavenumber = selected_wavenumber + 1
            print('Selected wavenumber: ', self.wavenumbers[selected_wavenumber], 'Element number: ',
                  selected_wavenumber)
            self.printWavenumber(self.wavenumbers[selected_wavenumber])
        self.on_ColormapBox_changed()

    def onImageSegmentation_clicked(self, event):
        """
        Perform image segmentation
        """
        if event.button() == QtCore.Qt.LeftButton:
            position = self.imgSegment.mapFromScene(event.scenePos())
            posX = int(position.x())
            posY = int(position.y())
            value = self.segmented_image[int(posX), int(posY)]

            printPosition = 'PNG: x:' + str(posX) + ' px, y:' + str(posY) + ' px'
            print(printPosition)
            print('intensity: ', value)
            #
            self.segmented_image_selected_area[self.segmented_image_selected_area[:,:] == value] = 1
            self.segmented_image_selected_area = self.segmented_image_selected_area.astype('uint8')
            self.selected_area[self.segmented_image_selected_area == 1] = 255

            self.segButtonRightShow_pressed()
            self.segmentationTransferButton.setEnabled(True)

        if event.button() == QtCore.Qt.RightButton:
            position = self.imgSegment.mapFromScene(event.scenePos())
            posX = int(position.x())
            posY = int(position.y())

            #new value equals to 1 as a proper identifier in uint8 image
            self.segmented_image_selected_area = flood_fill(self.segmented_image_selected_area, (posX, posY), 1,
                                                          connectivity=1).astype('uint8')

            self.selected_area[self.segmented_image_selected_area == 1] = 255

            self.segButtonRightShow_pressed()
            self.segmentationTransferButton.setEnabled(True)

    def segmentationButton_pressed(self):
        """
        Perform image segmentation
        """
        if self.QVButtonShow.isChecked() == True:
            masked_image = self.image_IR.copy()

            size_x = int(shape(masked_image)[0])
            size_y = int(shape(masked_image)[1])
            size_z = int(shape(masked_image)[2])
            index = arange(0, size_z).astype(int)

            image_reshaped = masked_image.reshape(size_x * size_y, size_z)
            mask_reshaped = self.mask_IR_mean.reshape(size_x * size_y)


        if self.QVButtonShow.isChecked() == True:
            if self.segmentationSettingsWindow == None:
                self.statusBar().showMessage('Please open Segmentation Settings Window.')
            else:
                #t0 = time()
                dataHelp = image_reshaped[mask_reshaped != 0, 0]

                data = zeros((shape(dataHelp)[0], size(index)))
                for i in range(size(index)):
                    data[:, i] = image_reshaped[mask_reshaped != 0, int(index[i])]
                if size_z == 1:
                    data = data.reshape(-1, 1)

                if self.segmentationSettingsWindow == None:
                    n_clus = 2
                else:
                    n_clus = int(self.segmentationSettingsWindow.SegmentationInputValue)

                #t1 = time()
                #print('time: ' + str(t1-t0) + ' s')

                if self.segmentationSettingsWindow.SegmentationMethodCombo.currentText() == 'KMeans':
                    #some parameters are hard coded
                    kmeans = KMeans(init='k-means++', n_clusters=n_clus, n_init=10, max_iter=300)
                    kmeans.fit(data)
                elif self.segmentationSettingsWindow.SegmentationMethodCombo.currentText() == 'BisectingKMeans':
                    #some parameters are hard coded
                    kmeans = BisectingKMeans(init='k-means++', n_clusters=n_clus, n_init=10, max_iter=300)
                    kmeans.fit(data)
                #fit_time = time() - t1
                #print('time: ' + str(fit_time) + ' s')

                labels = kmeans.labels_ + 1

                segmented_list = zeros((size_x * size_y))
                segmented_list[mask_reshaped != 0] = labels

                self.segmented_image = segmented_list.reshape(size_x, size_y)
                self.segmented_image = (exposure.rescale_intensity(self.segmented_image, out_range=(0, 255))).astype('uint8')

                self.segmented_image_selected_area = self.segmented_image.copy()

                self.selected_area = zeros_like(self.segmented_image_selected_area).astype('uint8')

                self.segButtonShow_pressed()

    def segmentationTransferButton_pressed(self):
        """
        Uses the image registration parameters to transfer the label image into the reference frame.
        """
        try:
            method = str(self.registrationSettingsWindow.registrationType.currentText())
        except:
            method = 'ridig'

        # transform mask of IR image
        image_trans = self.selected_area.copy()
        transform_px_0 = float(self.PixelSizeIRValue) / 1000 #mm
        transform_px_1 = (float(self.PixelSizeOptValue_x)+float(self.PixelSizeOptValue_y))/2 / 1000 #mm

        if method == 'iterative affine':
            ROI_trans = self.transformixImageMask(image_trans, self.transformMap0,
                                                   transform_pixelSize=transform_px_0)
            ROI_trans = self.transformixImageMask(ROI_trans, self.transformMap1,
                                                   transform_pixelSize=transform_px_1)
        else:
            ROI_trans = self.transformixImageMask(image_trans, self.transformMap0, transform_pixelSize = transform_px_0)

        threshold = threshold_multiotsu(ROI_trans, classes = 3)
        thresh_otsu_reg = max(threshold)

        self.ROI_trans = ROI_trans > thresh_otsu_reg

        self.ROI_trans = (exposure.rescale_intensity(self.ROI_trans, in_range=(0, 1), out_range=(0, 255))).astype('uint8')  # to obtain uint8
        self.ROI_trans_help = self.ROI_trans.copy()

        self.OptSeg_Button_pressed()

    def QVButtonShow_pressed(self):
        self.QVButtonShow.setEnabled(False)
        self.ColormapBox.setCurrentIndex(1)
        self.on_ColormapBox_changed()

    def IRTransferSettings_pressed(self):
        """
        Opens a dialog window.
        """
        try:
            if self.IRTransferWindow is None:
                self.IRTransferWindow = IR_Transfer_Settings_Dialog(parent=self)
                self.IRTransferWindow.show()
                self.IRTransferWindow.isVisible()
            elif self.IRTransferWindow.reply == QtWidgets.QMessageBox.Yes:
                self.IRTransferWindow = IR_Transfer_Settings_Dialog(parent=self)
                self.IRTransferWindow.show()
                self.IRTransferWindow.isVisible()
        except:
            pass

    def regSettingsButton_pressed(self):
        """
        Opens a dialog window.
        """
        try:
            if self.registrationSettingsWindow is None:
                self.registrationSettingsWindow = Registration_Settings_Dialog(parent=self)
                self.registrationSettingsWindow.show()
                self.registrationSettingsWindow.isVisible()
            elif self.registrationSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.registrationSettingsWindow = Registration_Settings_Dialog(parent=self)
                self.registrationSettingsWindow.show()
                self.registrationSettingsWindow.isVisible()
        except:
            pass

    def maskSettingsButton_pressed(self):
        """
        Opens a dialog window.
        """
        try:
            if self.maskSettingsWindow is None:
                self.maskSettingsWindow = Mask_Settings_Dialog(parent=self)
                self.maskSettingsWindow.show()
                self.maskSettingsWindow.isVisible()
            elif self.maskSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.maskSettingsWindow = Mask_Settings_Dialog(parent=self)
                self.maskSettingsWindow.show()
                self.maskSettingsWindow.isVisible()
        except:
            pass

    def segmentationSettingsButton_pressed(self):
        """
        Opens a dialog window.
        """
        try:
            if self.segmentationSettingsWindow is None:
                self.segmentationSettingsWindow = Segmentation_Settings_Dialog(parent=self)
                self.segmentationSettingsWindow.show()
                self.segmentationSettingsWindow.isVisible()
            elif self.segmentationSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.segmentationSettingsWindow = Segmentation_Settings_Dialog(parent=self)
                self.segmentationSettingsWindow.show()
                self.segmentationSettingsWindow.isVisible()
        except:
            pass

    #ToDo: add small discription
    def Import_ROI_TIF_button_pressed(self):
        """
        Function used to import .tif file.
        """
        # open Open dialog window
        fileNames = self.OpenFile()
        print(fileNames)
        print(os.path.splitext(fileNames)[1])
        # obtain file extension of first file, should be the same for all other files
        self.extension_IR = os.path.splitext(fileNames)[1]
        print(self.extension_IR)
        if self.extension_IR == '.tif':
            self.segmented_image = tifffile.imread(fileNames)
            self.selected_area = tifffile.imread(fileNames)
            self.segButtonSelectedShow_pressed()
            print('Done')

    def maskMeanButtonShow_pressed(self):
        """
        Updated buttons.
        """
        self.maskMeanButtonShow.setEnabled(False)
        self.maskMeanButtonShow.setChecked(True)
        self.segButtonShow.setEnabled(True)
        self.segButtonShow.setChecked(False)
        self.segButtonRightShow.setEnabled(True)
        self.segButtonRightShow.setChecked(False)
        self.segButtonSelectedShow.setEnabled(True)
        self.segButtonSelectedShow.setChecked(False)

        self.ColormapBox2.setCurrentIndex(0)
        self.on_showMaskSeg_changed()
    def segButtonShow_pressed(self):
        """
        Updated buttons.
        """
        self.segButtonShow.setEnabled(False)
        self.segButtonShow.setChecked(True)
        self.maskMeanButtonShow.setEnabled(True)
        self.maskMeanButtonShow.setChecked(False)
        self.segButtonRightShow.setEnabled(True)
        self.segButtonRightShow.setChecked(False)
        self.segButtonSelectedShow.setEnabled(True)
        self.segButtonSelectedShow.setChecked(False)

        self.ColormapBox2.setCurrentIndex(1)
        self.on_showMaskSeg_changed()
    def segButtonRightShow_pressed(self):
        """
        Updated buttons.
        """
        self.segButtonRightShow.setEnabled(False)
        self.segButtonRightShow.setChecked(True)
        self.maskMeanButtonShow.setEnabled(True)
        self.maskMeanButtonShow.setChecked(False)
        self.segButtonShow.setEnabled(True)
        self.segButtonShow.setChecked(False)
        self.segButtonSelectedShow.setEnabled(True)
        self.segButtonSelectedShow.setChecked(False)

        self.ColormapBox2.setCurrentIndex(1)
        self.on_showMaskSeg_changed()
    def segButtonSelectedShow_pressed(self):
        """
        Updated buttons.
        """
        self.segButtonSelectedShow.setEnabled(False)
        self.segButtonSelectedShow.setChecked(False)
        self.maskMeanButtonShow.setEnabled(True)
        self.maskMeanButtonShow.setChecked(False)
        self.segButtonShow.setEnabled(True)
        self.segButtonShow.setChecked(False)
        self.segButtonRightShow.setEnabled(True)
        self.segButtonRightShow.setChecked(False)

        self.ColormapBox2.setCurrentIndex(0)
        self.on_showMaskSeg_changed()

#right
    def importOptButton_pressed(self):
        """
        Import of a reference image.
        """
        self.fileName = self.OpenFile()
        # obtain file extension
        self.extension = os.path.splitext(self.fileName)[1]
        # in this version we limited the import to .tiff/.tif files only

        if self.OptSettingsWindow == None:
            if self.extension == '.tiff' or self.extension == '.tif':
                try:
                    image_optical = io.imread(fname=self.fileName)
                except:
                    pass
                image_optical = rot90(image_optical, -1)
                self.showOptImage(image_optical)

                self.image_optical = image_optical.copy()
                self.image_segment = zeros_like(self.image_optical[:, :, 0:4])
            try:
                self.showROI()
            except:
                pass
            self.getROIButton.setEnabled(True)
        else:
            if self.OptSettingsWindow.RadioButton_Opt.isChecked() == True:
                if self.extension == '.tiff' or self.extension == '.tif':
                    try:
                        image_optical = io.imread(fname=self.fileName)
                    except:
                        pass
                    image_optical = rot90(image_optical, -1)
                    self.showOptImage(image_optical)

                    self.image_optical = image_optical.copy()
                    self.image_segment = zeros_like(self.image_optical[:, :, 0:4])

                try:
                    self.showROI()
                except:
                    pass
                self.getROIButton.setEnabled(True)

            elif self.OptSettingsWindow.RadioButton_IR.isChecked() == True:
                if self.extension == '.tiff' or self.extension == '.tif':
                    try:
                        image_IR = io.imread(fname=self.fileName)
                    except:
                        pass

                    self.image_IR = zeros((shape(image_IR)[0],shape(image_IR)[1],1))
                    self.image_IR[:,:,0] = (exposure.rescale_intensity(rgb2gray(image_IR), out_range=(255, 0))).astype(
                        'uint8')
                    self.wavenumbers = array([0])
                    self.printWavenumber(self.wavenumbers[0])

                    #mask image
                    self.mask_IR_mean = 255*ones_like(self.image_IR[:,:,0]).astype('uint8')
                    self.mask_IR_mean[0:400,0:400] = 0

                    self.QVButtonShow_pressed()
                    self.maskMeanButtonShow_pressed()
                    self.segmentationButton.setEnabled(True)
                    self.maskMeanButtonShow.setEnabled(True)

                    self.getROIButton.setEnabled(True)

    def importOptButtonSettings_pressed(self):
        """
        Open dialog window.
        """
        try:
            if self.OptSettingsWindow is None:
                self.OptSettingsWindow = Opt_Import_Settings_Dialog(parent=self)
                self.OptSettingsWindow.show()
                self.OptSettingsWindow.isVisible()
            elif self.OptSettingsWindow.reply == QtWidgets.QMessageBox.Yes:
                self.OptSettingsWindow = Opt_Import_Settings_Dialog(parent=self)
                self.OptSettingsWindow.show()
                self.OptSettingsWindow.isVisible()
        except:
            pass

    def showROI(self):
        """
        Generates an a rectangle for creating an image subset.
        """
        pixelSize_opt = (float(self.PixelSizeOptValue_x) + float(self.PixelSizeOptValue_y))/2
        pixelSize_IR = float(self.PixelSizeIRValue)
        ratio = (pixelSize_IR / pixelSize_opt)

        sizeIR_x = shape(self.image_IR)[0]
        sizeIR_y = shape(self.image_IR)[1]
        # Add ROI
        xstart = int(sizeIR_x/10)
        ystart = int(sizeIR_y/10)
        xwidth = int(sizeIR_x * ratio)
        ywidth = int(sizeIR_y * ratio)

        try:
            self.viewOpt.removeItem(self.roiBox)
        except:
            pass

        self.roiBox = pg.ROI([xstart, ystart], [xwidth, ywidth])
        self.roiBox.setPen(pg.mkPen('r', width=3))
        self.viewOpt.addItem(self.roiBox)

        self.roiBox.addScaleHandle([1, 0.5], [0, 0.5])
        self.roiBox.addScaleHandle([0, 0.5], [1, 0.5])

        self.roiBox.addScaleHandle([0.5, 0], [0.5, 1])
        self.roiBox.addScaleHandle([0.5, 1], [0.5, 0])

        self.roiBox.addScaleHandle([1, 1], [0, 0])
        self.roiBox.addScaleHandle([0, 0], [1, 1])

    def OpenFile(self):
        """
        Opens a file dialog.
        """
        file, fileType = QtWidgets.QFileDialog.getOpenFileName(None, "Select one file", os.getcwd(), 'Files (*.tiff *.tif)')
        self.statusBar().showMessage('File has been selected.')

        return file

    def showOptImage(self, image):
        """
        Sets the optical image.
        """
        try:
            self.viewOpt.removeItem(self.imgOpt)
            self.viewOpt.addItem(self.imgOpt)
        except:
            self.viewOpt.addItem(self.imgOpt)

        self.imgOpt.setImage(image)

    def showOptImageZoom(self, image):
        """
        Sets the optical subset image.
        """
        maxlut = 255
        maxScale = 260

        color_value = self.ColormapBoxOpt.currentIndex()
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

        colormap = cm.get_cmap(color_name)
        colormap._init()
        lut = (colormap._lut * maxlut).view(ndarray)

        try:
            for element in self.ContourPathList:
                self.viewOptZoom.removeItem(element)
            for element in self.ContourPathList_Holes:
                self.viewOptZoom.removeItem(element)
        except:
            pass

        self.viewOptZoom.removeItem(self.imgOptZoom)
        self.viewOptZoom.addItem(self.imgOptZoom)
        self.imgOptZoom.setImage(image)
        yMax = image.shape[1]
        xMax = image.shape[0]
        if xMax > yMax:
            yMax = xMax
        else:
            xMax = yMax
        self.viewOptZoom.setLimits(xMin=0, xMax=xMax, yMin=0, yMax=yMax)
        self.viewOptZoom.setRange(xRange=[0, image.shape[0]], yRange=[0, image.shape[1]])
        self.viewOptZoom.autoRange(padding=0)
        self.imgOptZoom.setLookupTable(lut)
        self.imgOptZoom.setLevels([0, maxScale])

    def PixelSizeOptEnter_x(self):
        """
        Input field for the pixel siz.
        """
        self.PixelSizeOptValue_x = self.PixelSizeOpt_x.text()
        self.PixelSizeOpt_x.clear()
        self.PixelSizeOpt_x.setPlaceholderText(str(self.PixelSizeOptValue_x))
    def PixelSizeOptEnter_y(self):
        """
        Input field for the pixel siz.
        """
        self.PixelSizeOptValue_y = self.PixelSizeOpt_y.text()
        self.PixelSizeOpt_y.clear()
        self.PixelSizeOpt_y.setPlaceholderText(str(self.PixelSizeOptValue_y))

    def getROIButton_pressed(self):
        """
        Generates an a rectangle for creating an image subset.
        """
        #obtain image subset
        self.xstart = int(self.roiBox.pos()[0])
        self.xwidth = int(self.roiBox.size()[0])
        xstart = int(self.xstart)
        xwidth = int(self.xwidth)

        self.ystart = int(self.roiBox.pos()[1])
        self.ywidth = int(self.roiBox.size()[1])
        ystart = int(self.ystart)
        ywidth = int(self.ywidth)

        yInvert = shape(self.image_segment)[1]
        xInvert = shape(self.image_segment)[0]

        yend = yInvert-ystart
        self.ybegin = yInvert-(ystart+ywidth)

        print('Width ROI: x:' , xwidth, 'y:', ywidth)

        if self.extension == '.tiff' or self.extension == '.tif':

            image_optical = self.image_optical[xstart: xstart + xwidth, ystart: ystart + ywidth]

            self.image_opt_gray = rgb2gray(image_optical)
            if self.ColormapInverted.isChecked() == True:
                self.image_opt_gray = (exposure.rescale_intensity(self.image_opt_gray, out_range=(255, 0))).astype(
                    'uint8')
            else:
                self.image_opt_gray = (exposure.rescale_intensity(self.image_opt_gray, out_range=(0, 255))).astype(
                    'uint8')
            self.showOptImageZoom(self.image_opt_gray)

        #generate mask
        classif_GMM = GaussianMixture(n_components=2)
        classif_GMM.fit(self.image_opt_gray.reshape((self.image_opt_gray.size, 1)))
        thresh_GMM_opt = mean(classif_GMM.means_)
        self.image_opt_mask = self.image_opt_gray > thresh_GMM_opt
        self.image_opt_mask = (exposure.rescale_intensity(self.image_opt_mask, out_range=(0, 255))).astype('uint8')
        self.image_opt_mask_help = self.image_opt_mask.copy()

        self.regButton.setEnabled(True)

        self.Opt_Button_pressed()

    def regButton_pressed(self):
        """
        Perform image registration
        """
        #select moving image
        selected_wavenumber = int(abs(self.wavenumbers - int(self.currentWavenumber)).argmin())

        #set fixed image
        moving = self.image_IR[:, :, selected_wavenumber].copy()
        fixed = self.image_opt_gray.copy()

        #get pixel size
        pixel_size_fixed = (float(self.PixelSizeOptValue_x) + float(self.PixelSizeOptValue_y))/2 / 1000
        pixel_size_moving = float(self.PixelSizeIRValue) / 1000

        #take image mask
        reg_mask = self.mask_IR_mean.copy()

        try:
            method = str(self.registrationSettingsWindow.registrationType.currentText())
        except:
            method = str('rigid')

        try:
            iterN = int(self.registrationSettingsWindow.registrationInput1Value)
        except:
            iterN = 500

        if True:    #can be used to add different reg. algorithms

            if method == 'iterative affine':
                affine_image, self.transformMap0 = self.registerImageElastix(fixed=fixed, moving=moving, method='rigid', iterations=iterN, fixed_pixelSize= pixel_size_fixed, moving_pixelSize=pixel_size_moving)
                self.image_IR_opt_reg, self.transformMap1 = self.registerImageElastix(fixed=fixed, moving=affine_image, method='affine', iterations=iterN, fixed_pixelSize= pixel_size_fixed, moving_pixelSize=pixel_size_fixed)
                self.image_IR_opt_reg = (exposure.rescale_intensity(self.image_IR_opt_reg, out_range=(0, 255))).astype('uint8')

                #transform mask of IR image
                mask_trans = self.transformixImageMask(reg_mask, self.transformMap0, transform_pixelSize = pixel_size_moving)
                mask_trans = self.transformixImageMask(mask_trans, self.transformMap1, transform_pixelSize = pixel_size_fixed)
                thresh_otsu_reg = threshold_otsu(mask_trans)
                self.mask_IR_reg = mask_trans > thresh_otsu_reg
                self.mask_IR_reg = (exposure.rescale_intensity(self.mask_IR_reg, in_range=(0, 1), out_range=(0, 255))).astype('uint8')  # to obtain uint8
            else:
                self.image_IR_opt_reg, self.transformMap0 = self.registerImageElastix(fixed=fixed, moving=moving, method=method, iterations=iterN, fixed_pixelSize= pixel_size_fixed, moving_pixelSize=pixel_size_moving)
                self.image_IR_opt_reg = (exposure.rescale_intensity(self.image_IR_opt_reg, out_range=(0, 255))).astype('uint8')
                print('reg_mask_shape: ', shape(reg_mask))
                # transform mask of IR image
                mask_trans = self.transformixImageMask(reg_mask, self.transformMap0, transform_pixelSize = pixel_size_moving)
                thresh_otsu_reg = threshold_otsu(mask_trans)
                self.mask_IR_reg = mask_trans > thresh_otsu_reg
                self.mask_IR_reg = (exposure.rescale_intensity(self.mask_IR_reg, in_range=(0, 1), out_range=(0, 255))).astype('uint8')  # to obtain uint8
                self.mask_IR_reg_help = self.mask_IR_reg.copy()

        self.showOptImageZoom(self.image_IR_opt_reg)

        self.IR_Button_pressed()
        self.segmentationTransferButton.setEnabled(True)
    def transformixImageMask(self, image, transformParameterMap, transform_pixelSize = 1):
        """
        Transform an image into the reference frame.
        """
        transformixImageFilter = sitk.TransformixImageFilter()
        transformixImageFilter.SetTransformParameterMap(transformParameterMap)

        image_transformed = sitk.GetImageFromArray(image)
        image_transformed = sitk.Cast(image_transformed, sitk.sitkFloat64)

        transform_pixelSize = transform_pixelSize
        image_transformed.SetSpacing((transform_pixelSize, transform_pixelSize))  # sets spacing (or pixel/voxel resolution)

        transformixImageFilter.SetMovingImage(image_transformed)
        transformixImageFilter.Execute()

        result_transformed = sitk.Cast(transformixImageFilter.GetResultImage(), sitk.sitkFloat64)
        transformedImage = sitk.GetArrayViewFromImage(result_transformed)

        result = (exposure.rescale_intensity(transformedImage, out_range=(0, 255))).astype('uint8')  # to obtain uint8

        print('transform_pixelSize', transform_pixelSize)

        return result

    def on_ColormapBoxOpt_changed(self):
        """
        Update the images.
        """
        if self.Opt_Button.isChecked() == True:
            self.showOptImageZoom(self.image_opt_gray)
        elif self.Optmask_Button.isChecked() == True:
            self.showOptImageZoom(self.image_opt_mask)
        elif self.IR_Button.isChecked() == True:
            self.showOptImageZoom(self.image_IR_opt_reg)
        elif self.IRmask_Button.isChecked() == True:
            self.showOptImageZoom(self.mask_IR_reg)
        elif self.OptIR_Button.isChecked() == True:
            image = zeros_like(self.image_opt_gray).astype('float32')
            image[:, :] = self.image_opt_mask[:, :].astype('float32') - self.mask_IR_reg[:, :].astype('float32')
            image[:, :] = (exposure.rescale_intensity(image[:, :], in_range=(-255, 255), out_range=(0, 255))).astype('uint8')
            self.ColormapBoxOpt.setCurrentIndex(4)
            self.showOptImageZoom(image)
        elif self.OptSeg_Button.isChecked() == True:
            self.showOptImageZoom(self.ROI_trans)

    def on_ColormapBoxOptAll_changed(self):
        self.showOptImage(self.image_optical)

    def on_ColormapInverted_pressed(self):
        """
        Invert image to 255 - 0 scale.
        """
        if self.ColormapInverted.isChecked() == True:
            self.image_opt_gray = 255-self.image_opt_gray
        else:
            self.image_opt_gray = 255-self.image_opt_gray
        self.showOptImageZoom(self.image_opt_gray)

    def OffsetXInputEnter(self):
        """
        Input for the manual x-offset for the regions of interest.
        """
        self.OffsetXInputValue = self.OffsetXInput.text()
        self.OffsetXInput.clear()
        self.OffsetXInput.setPlaceholderText(str(self.OffsetXInputValue))
    def OffsetYInputEnter(self):
        """
        Input for the manual x-offset for the regions of interest.
        """
        self.OffsetYInputValue = self.OffsetYInput.text()
        self.OffsetYInput.clear()
        self.OffsetYInput.setPlaceholderText(str(self.OffsetYInputValue))

    def defaultareanameInputEnter(self):
        """
        Input for the region names.
        """
        self.defaultareanameInputString = self.defaultareanameInput.text()
        self.defaultareanameInput.clear()
        self.defaultareanameInput.setPlaceholderText(str(self.defaultareanameInputString))

    def modifyMaskButton_pressed(self):
        """
        Performs a modification of the image mask.
        """
        try:
            closing_value = int(self.maskSettingsWindow.MaskBinaryClosingInputValue)
            object_size_remove = int(self.maskSettingsWindow.MaskRemoveHolesObjectsInputValue)
            object_size_fill = int(self.maskSettingsWindow.MaskRemoveSmallObjectsInputValue)
            object_size_erosion = int(self.maskSettingsWindow.MaskBinaryErosionInputValue)
            object_size_dilation = int(self.maskSettingsWindow.MaskBinaryDilationInputValue)

            if self.Optmask_Button.isChecked() == True:
                image = self.image_opt_mask_help > 200
            if self.IRmask_Button.isChecked() == True:
                image = self.mask_IR_reg_help > 200
            if self.OptSeg_Button.isChecked() == True:
                image = self.ROI_trans_help > 200

            if self.maskSettingsWindow.MaskBinaryClosingCheckbox.isChecked() == True:
                image = binary_closing(image, disk(closing_value))
            if self.maskSettingsWindow.MaskRemoveHolesObjectsCheckbox.isChecked() == True:
                image = remove_small_holes(image, object_size_remove, connectivity=1)
            if self.maskSettingsWindow.MaskRemoveSmallObjectsCheckbox.isChecked() == True:
                image = remove_small_objects(image, object_size_fill, connectivity=1)
            if self.maskSettingsWindow.MaskBinaryErosionCheckbox.isChecked() == True:
                image = binary_erosion(image, disk(object_size_erosion))
            if self.maskSettingsWindow.MaskRemoveSmallObjectsCheckbox.isChecked() == True:
                image = remove_small_objects(image, object_size_fill, connectivity=1)
            if self.maskSettingsWindow.MaskBinaryDilationCheckbox.isChecked() == True:
                image = binary_dilation(image, disk(object_size_dilation))
            if self.maskSettingsWindow.MaskBinaryMaskCheckbox.isChecked() == True:
                print('True')
                image = (exposure.rescale_intensity(image, out_range=(0, 255))).astype('uint8')
                image = image & self.mask_IR_reg
            print('Done')
            #self.mask_IR_reg


            #if str(self.imageTypeOpt.currentText()) == 'Opt mask':
            if self.Optmask_Button.isChecked() == True:
                self.image_opt_mask = (exposure.rescale_intensity(image, out_range=(0, 255))).astype('uint8')
                self.showOptImageZoom(self.image_opt_mask)
            #if str(self.imageTypeOpt.currentText()) == 'IR reg mask':
            if self.IRmask_Button.isChecked() == True:
                self.mask_IR_reg = (exposure.rescale_intensity(image, out_range=(0, 255))).astype('uint8')
                self.showOptImageZoom(self.mask_IR_reg)
            #if str(self.imageTypeOpt.currentText()) == 'ROI reg':
            if self.OptSeg_Button.isChecked() == True:
                self.ROI_trans = (exposure.rescale_intensity(image, out_range=(0, 255))).astype('uint8')
                self.showOptImageZoom(self.ROI_trans)
            print('Done')
        except:
            pass

    def findContoursButton_pressed(self):
        """
        Generates contours of the labeled image.
        Option:
        1. normal: all contours (even for holes)
        2. holes: identifies holes in donut like regions
        3. open holes: opens donut like regions
        """
        if self.BoxShapeOption.currentText() == 'normal' or self.BoxShapeOption.currentText() == 'holes' or self.BoxShapeOption.currentText() == 'open holes':
            #
            if self.Optmask_Button.isChecked() == True:
                self.contours, self.contours_holes = FindContours(self.image_opt_mask, level=0.5)
            if self.IRmask_Button.isChecked() == True:
                self.contours, self.contours_holes = FindContours(self.mask_IR_reg, level=0.5)
            if self.OptSeg_Button.isChecked() == True:
                self.contours, self.contours_holes = FindContours(self.ROI_trans, level=0.5)

            print('number of contours: ', len(self.contours))
            print('number of holes: ', len(self.contours_holes))

            self.on_ColormapBoxOpt_changed()

            try:
                for element in self.ContourPathList:
                    self.viewOptZoom.removeItem(element)
                for element in self.ContourPathList_Holes:
                    self.viewOptZoom.removeItem(element)
            except:
                pass

            if self.BoxShapeOption.currentText() == 'normal':
                self.contours = self.contours + self.contours_holes
                self.ContourPathList = []
                self.ContourPathList_Holes = []
                self.contours_holes = []
                i = 0
                for contour in self.contours:
                    self.path = pg.arrayToQPath(contour[:, 0] + 0.5, contour[:, 1] + 0.5)
                    ContourPath = pg.QtGui.QGraphicsPathItem()
                    ContourPath.setPen(pg.mkPen('r', width=3))
                    ContourPath.setPath(self.path)
                    self.ContourPathList = append(self.ContourPathList, ContourPath)
                    self.viewOptZoom.addItem(self.ContourPathList[i])
                    i = i + 1

            if self.BoxShapeOption.currentText() == 'holes':
                self.ContourPathList = []
                i = 0
                for contour in self.contours:
                    self.path = pg.arrayToQPath(contour[:, 0] + 0.5, contour[:, 1] + 0.5)
                    ContourPath = pg.QtGui.QGraphicsPathItem()
                    ContourPath.setPen(pg.mkPen('r', width=3))
                    ContourPath.setPath(self.path)
                    self.ContourPathList = append(self.ContourPathList, ContourPath)
                    self.viewOptZoom.addItem(self.ContourPathList[i])
                    i = i + 1

                self.ContourPathList_Holes = []
                i = 0
                for contour in self.contours_holes:
                    self.path_holes = pg.arrayToQPath(contour[:, 0] + 0.5, contour[:, 1] + 0.5)
                    ContourPath = pg.QtGui.QGraphicsPathItem()
                    ContourPath.setPen(pg.mkPen('b', width=3))
                    ContourPath.setPath(self.path_holes)
                    self.ContourPathList_Holes = append(self.ContourPathList_Holes, ContourPath)
                    self.viewOptZoom.addItem(self.ContourPathList_Holes[i])
                    i = i + 1

            if self.BoxShapeOption.currentText() == 'open holes':
                self.contours = FindOpenContours(self.contours, self.contours_holes)
                self.ContourPathList = []
                self.ContourPathList_Holes = []
                self.contours_holes = []
                i = 0
                for contour in self.contours:
                    self.path = pg.arrayToQPath(contour[:, 0] + 0.5, contour[:, 1] + 0.5)
                    ContourPath = pg.QtGui.QGraphicsPathItem()
                    ContourPath.setPen(pg.mkPen('r', width=3))
                    ContourPath.setPath(self.path)
                    self.ContourPathList = append(self.ContourPathList, ContourPath)
                    self.viewOptZoom.addItem(self.ContourPathList[i])
                    i = i + 1

    def showROIButton_pressed(self):
        """
        Generates contours on the reference image.
        """
        try:
            for i in range(len(self.ListRegionsInfrared)):
                key = list(self.ListRegionsInfrared.keys())
                for region in self.ListRegionsInfrared[key[i]]:
                    self.viewOpt.removeItem(region)
        except:
            pass

        self.ContourPathListOpt = []

        if self.extension == '.tiff' or self.extension == '.tif' or self.extension == '.fsm' or self.extension == '.imzML' or self.extension == '.pickle' or self.extension == '.jpg':
            if self.OptSeg_Button.isChecked() == True or self.Optmask_Button.isChecked() == True or self.IRmask_Button.isChecked() == True:
                xstart = self.xstart
                ystart = self.ystart

                i = 0

                # add item to WidgetTree

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

                try:
                    key = list(self.ListRegionsInfrared.keys())
                    elementNumber = max(key) + 1
                except:
                    elementNumber = 0

                for contour in self.contours:
                    pen = pg.mkPen(color=self.color, width=3)
                    # contourNew = (contour + 0.5)*ratio
                    contourNew = (contour + 0.5)
                    path = pg.arrayToQPath(contourNew[:, 0] + xstart + int(self.OffsetXInputValue),
                                           contourNew[:, 1] + ystart + int(self.OffsetYInputValue))
                    ContourPath = pg.QtGui.QGraphicsPathItem()
                    ContourPath.setPen(pen)
                    if self.FillingCheckbox.isChecked() == True:

                        ContourPath.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2]))
                    ContourPath.setOpacity((self.opacitySlider.value() / 100))
                    ContourPath.setPath(path)

                    self.ContourPathListOpt = append(self.ContourPathListOpt, ContourPath)
                    self.viewOpt.addItem(self.ContourPathListOpt[i])

                    i = i + 1

                    self.ListRegionsInfrared[elementNumber] = self.ContourPathListOpt

                # infrared
                # add item to WidgetTree
                elementNumber = int(len(self.InfraredTreeElements))
                child = QtWidgets.QTreeWidgetItem(self.InfraredTree)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
                child.setCheckState(0, QtCore.Qt.Unchecked)
                child.setCheckState(0, QtCore.Qt.Checked)
                child.setText(0, "Region of Interest {}".format(elementNumber))
                type_of_contour = 1
                child.setText(1, "{}".format(type_of_contour))
                child.setText(2, "A")
                child.setForeground(0, QtGui.QBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2])))
                self.InfraredTreeElements = append(self.InfraredTreeElements, child)

                self.ContourPathListOpt = []
                if len(self.contours_holes) != 0:  # annotations
                    try:
                        key = list(self.ListRegionsInfrared.keys())
                        elementNumber = max(key) + 1
                    except:
                        elementNumber = 0

                    self.color = [30, 144, 255]

                    i = 0
                    for contour in self.contours_holes:
                        pen = pg.mkPen(color=self.color, width=3)
                        contourNew = (contour + 0.5)
                        path = pg.arrayToQPath(contourNew[:, 0] + xstart + int(self.OffsetXInputValue),
                                               contourNew[:, 1] + ystart + int(self.OffsetYInputValue))
                        ContourPath = pg.QtGui.QGraphicsPathItem()
                        ContourPath.setPen(pen)
                        if self.FillingCheckbox.isChecked() == True:
                            ContourPath.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2]))
                        ContourPath.setOpacity((self.opacitySlider.value() / 100))
                        ContourPath.setPath(path)
                        self.ContourPathListOpt = append(self.ContourPathListOpt, ContourPath)
                        self.viewOpt.addItem(self.ContourPathListOpt[i])

                        i = i + 1

                        self.ListRegionsInfrared[elementNumber] = self.ContourPathListOpt

                    # add item to WidgetTree
                    elementNumber = int(len(self.InfraredTreeElements))
                    child = QtWidgets.QTreeWidgetItem(self.InfraredTree)
                    child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
                    child.setCheckState(0, QtCore.Qt.Unchecked)
                    child.setCheckState(0, QtCore.Qt.Checked)
                    child.setText(0, "Region of Interest {}".format(elementNumber))
                    type_of_contour = 0
                    child.setText(1, "{}".format(type_of_contour))
                    child.setText(2, "A")
                    child.setForeground(0, QtGui.QBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2])))
                    self.InfraredTreeElements = append(self.InfraredTreeElements, child)

    def teachPoint_pressed(self):
        try:
            for item in self.TeachingPointsShow:
                self.viewOpt.removeItem(item)
        except:
            pass
        self.TeachingPointsShow = []

    def saveTIFF_Segmentation_pressed(self):
        """
        Exports the image segmentation image (labels) as a .tif file.
        """
        folder_save = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        now = datetime.now()  # current date and time
        date_time = now.strftime("%d%m%Y_%H%M%S")

        fileName_out = folder_save + "/Image_" + date_time + ".tif"

        print(fileName_out)

        image_seg = gray2rgb(self.segmented_image)

        image_seg = (exposure.rescale_intensity(image_seg, out_range=(255, 0))).astype('uint8')

        tifffile.imwrite(fileName_out, image_seg)  # , photometric='rgb'

    def saveTIFF_Segmentation_Selected_pressed(self):
        """
        Exports the image segmentation image (selected labels) as a .tif file.
        """
        folder_save = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        now = datetime.now()  # current date and time
        date_time = now.strftime("%d%m%Y_%H%M%S")

        fileName_out = folder_save + "/Image_Selected_" + date_time + ".tif"

        print(fileName_out)

        image_seg = (exposure.rescale_intensity(self.selected_area, out_range=(0, 255))).astype('uint8')

        tifffile.imwrite(fileName_out, image_seg)  # , photometric='rgb'

    def on_OptImage_clicked(self, event):
        """
        Action for adding e.g. teach marks on the image.
        """
        # when right button is clicked, select specific area from segmentation
        if event.button() == QtCore.Qt.LeftButton:
            if self.TeachingPoints_Button.isChecked() == True:
                if self.TeachingCounter != 3:
                    try:
                        position = self.imgOpt.mapFromScene(event.scenePos())
                        posX = int(position.x())
                        posY = int(position.y())
                        value = self.image_optical[int(posX), int(posY)]

                        printPosition = 'PNG: x:' + str(posX) + ' px, y:' + str(posY) + ' px'
                        print(printPosition)
                        print('intensity: ', value)

                        siz = 20

                        pointItem = QtWidgets.QGraphicsLineItem()
                        pointItem.setLine(posX + 0.5, posY-siz + 0.5, posX + 0.5, posY+siz + 0.5)
                        pen = pg.mkPen(color=(0, 0, 0), width=1)
                        pointItem.setPen(pg.mkPen(pen))
                        self.viewOpt.addItem(pointItem)
                        pointItem1 = QtWidgets.QGraphicsLineItem()
                        pointItem1.setLine(posX - siz + 0.5, posY + 0.5, posX + siz + 0.5, posY + 0.5)
                        pen1 = pg.mkPen(color=(0, 0, 0), width=1)
                        pointItem1.setPen(pg.mkPen(pen1))
                        self.viewOpt.addItem(pointItem1)
                        self.TeachingPointsShow = append(self.TeachingPointsShow, pointItem)
                        self.TeachingPointsShow = append(self.TeachingPointsShow, pointItem1)

                        self.TeachingPoints[self.TeachingCounter, 0] = posX
                        self.TeachingPoints[self.TeachingCounter, 1] = posY
                        print(self.TeachingPoints)
                        self.TeachingCounter = self.TeachingCounter + 1
                        if self.TeachingCounter == 3:
                            self.TeachingCounter = 0
                            self.TeachingPoints_Button.setChecked(False)

                    except:
                        pass

    #mis file
    def importMIS(self):
        self.fileNameMis, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Test Dialog', os.getcwd(), 'Files (*.mis)')
        self.statusBar().showMessage('.mis file import successful.')
        self.writeMisButton.setEnabled(True)
    def writeMIS(self):
        """"
        Export a selected segment/contour to an existing .mis-File (adding an area or region of interest)
        first, a .mis file need to be pre-selected by the function importMIS.
        """
        if self.defaultrasterInput.currentText() == '5 um':
            rasterSize= 5
        if self.defaultrasterInput.currentText() == '10 um':
            rasterSize= 10
        elif self.defaultrasterInput.currentText() == '20 um':
            rasterSize= 20
        elif self.defaultrasterInput.currentText() == '30 um':
            rasterSize = 30
        elif self.defaultrasterInput.currentText() == '40 um':
            rasterSize = 40
        elif self.defaultrasterInput.currentText() == '50 um':
            rasterSize= 50
        elif self.defaultrasterInput.currentText() == '100 um':
            rasterSize= 100

        raster_size = [rasterSize, rasterSize]
        local_reference = [0, 0]
        polygon_type = str(self.defaultpolygontypeMIS.currentText())
        area_name = str(self.defaultareanameInputString + '_')
        #

        newMis = mismaker(self.fileNameMis, defaultraster=raster_size,
                          defaultlocalreference=local_reference,
                          defaultpolygontype=polygon_type, defaultareaname=area_name)
        #
        newMis.load_mis(self.fileNameMis, mode="add")

        #
        yInvert = int(shape(self.image_optical)[1])
        shapes = []
        # add Infrared
        try:
            column = 0
            for i in range(len(self.ListRegionsInfrared)):
                key = list(self.ListRegionsInfrared.keys())
                jj = 0
                for region in self.ListRegionsInfrared[key[i]]:
                    if self.InfraredTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        jj = jj + 1

                        x = []
                        y = []

                        pathNew = region.path()
                        numberOfPoints = int(pathNew.elementCount())
                        print("numberOfPoints: ", numberOfPoints)
                        polygonList = zeros((numberOfPoints, 2))
                        for ii in range(numberOfPoints):
                            point = QtCore.QPointF(pathNew.elementAt(ii))
                            # print(str(i), '-Element: x', round(point.x()), 'y: ', round(point.y()))
                            x = append(x, int(point.x()))
                            y = append(y, int(point.y()))
                        polygonList[:, 0] = x[:]
                        polygonList[:, 1] = y[:]
                        print(polygonList)
                        shapes.append(polygonList)
        except:
            pass

        # add shapes
        try:
            column = 0
            for i in range(len(self.ListRegionsShapes)):
                key = list(self.ListRegionsShapes.keys())
                jj = 0
                for region in self.ListRegionsShapes[key[i]]:
                    if self.ShapesTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        jj = jj + 1

                        x = []
                        y = []

                        # obtain possible translation
                        try:
                            x0 = region.pos().x()
                            y0 = region.pos().y()
                        except:
                            pass

                        pathNew = region.path()
                        numberOfPoints = int(pathNew.elementCount())
                        print("numberOfPoints: ", numberOfPoints)
                        polygonList = zeros((numberOfPoints, 2))
                        for ii in range(numberOfPoints):
                            point = QtCore.QPointF(pathNew.elementAt(ii))
                            # print(str(i), '-Element: x', round(point.x()), 'y: ', round(point.y()))
                            x = append(x, int(point.x() + x0))
                            y = append(y, int(point.y() + y0))
                        polygonList[:, 0] = x[:]
                        polygonList[:, 1] = y[:]
                        shapes.append(polygonList)
        except:
            pass

        contourDict = {}
        i = 0
        for contour in shapes:
            contourHelp = (contour + 0.0)
            contourHelp[:, 0] = (around(contourHelp[:, 0])) + int(self.OffsetXInputValue)
            contourHelp[:, 1] = yInvert - (around(contourHelp[:, 1])) + int(self.OffsetYInputValue)
            contourDict[i] = {"contour": contourHelp.astype(int)}
            i = i + 1

        newMis.add_contours(contourDict)
        newMis.save_mis(self.fileNameMis)

    def Opt_Button_pressed(self):
        """
        Updates buttons.
        """
        self.Opt_Button.setChecked(True)
        self.Opt_Button.setEnabled(False)
        self.Optmask_Button.setChecked(False)
        self.Optmask_Button.setEnabled(True)
        self.IR_Button.setChecked(False)
        self.IR_Button.setEnabled(True)
        self.IRmask_Button.setChecked(False)
        self.IRmask_Button.setEnabled(True)
        self.OptIR_Button.setChecked(False)
        self.OptIR_Button.setEnabled(True)
        self.OptSeg_Button.setChecked(False)
        self.OptSeg_Button.setEnabled(True)
        try:
            self.ColormapBoxOpt.setCurrentIndex(0)
            self.on_ColormapBoxOpt_changed()
        except:
            pass
    def Optmask_Button_pressed(self):
        """
        Updates buttons.
        """
        self.Opt_Button.setChecked(False)
        self.Opt_Button.setEnabled(True)
        self.Optmask_Button.setChecked(True)
        self.Optmask_Button.setEnabled(False)
        self.IR_Button.setChecked(False)
        self.IR_Button.setEnabled(True)
        self.IRmask_Button.setChecked(False)
        self.IRmask_Button.setEnabled(True)
        self.OptIR_Button.setChecked(False)
        self.OptIR_Button.setEnabled(True)
        self.OptSeg_Button.setChecked(False)
        self.OptSeg_Button.setEnabled(True)
        try:
            self.ColormapBoxOpt.setCurrentIndex(0)
            self.on_ColormapBoxOpt_changed()
        except:
            pass
    def IR_Button_pressed(self):
        """
        Updates buttons.
        """
        self.Opt_Button.setChecked(False)
        self.Opt_Button.setEnabled(True)
        self.Optmask_Button.setChecked(False)
        self.Optmask_Button.setEnabled(True)
        self.IR_Button.setChecked(True)
        self.IR_Button.setEnabled(False)
        self.IRmask_Button.setChecked(False)
        self.IRmask_Button.setEnabled(True)
        self.OptIR_Button.setChecked(False)
        self.OptIR_Button.setEnabled(True)
        self.OptSeg_Button.setChecked(False)
        self.OptSeg_Button.setEnabled(True)
        try:
            self.ColormapBoxOpt.setCurrentIndex(0)
            self.on_ColormapBoxOpt_changed()
        except:
            pass
    def IRmask_Button_pressed(self):
        """
        Updates buttons.
        """
        self.Opt_Button.setChecked(False)
        self.Opt_Button.setEnabled(True)
        self.Optmask_Button.setChecked(False)
        self.Optmask_Button.setEnabled(True)
        self.IR_Button.setChecked(False)
        self.IR_Button.setEnabled(True)
        self.IRmask_Button.setChecked(True)
        self.IRmask_Button.setEnabled(False)
        self.OptIR_Button.setChecked(False)
        self.OptIR_Button.setEnabled(True)
        self.OptSeg_Button.setChecked(False)
        self.OptSeg_Button.setEnabled(True)
        try:
            self.ColormapBoxOpt.setCurrentIndex(0)
            self.on_ColormapBoxOpt_changed()
        except:
            pass
    def OptIR_Button_pressed(self):
        """
        Updates buttons.
        """
        self.Opt_Button.setChecked(False)
        self.Opt_Button.setEnabled(True)
        self.Optmask_Button.setChecked(False)
        self.Optmask_Button.setEnabled(True)
        self.IR_Button.setChecked(False)
        self.IR_Button.setEnabled(True)
        self.IRmask_Button.setChecked(False)
        self.IRmask_Button.setEnabled(True)
        self.OptIR_Button.setChecked(True)
        self.OptIR_Button.setEnabled(False)
        self.OptSeg_Button.setChecked(False)
        self.OptSeg_Button.setEnabled(True)
        try:
            self.ColormapBoxOpt.setCurrentIndex(4)
            self.on_ColormapBoxOpt_changed()
        except:
            pass
    def OptSeg_Button_pressed(self):
        """
        Updates buttons.
        """
        self.Opt_Button.setChecked(False)
        self.Opt_Button.setEnabled(True)
        self.Optmask_Button.setChecked(False)
        self.Optmask_Button.setEnabled(True)
        self.IR_Button.setChecked(False)
        self.IR_Button.setEnabled(True)
        self.IRmask_Button.setChecked(False)
        self.IRmask_Button.setEnabled(True)
        self.OptIR_Button.setChecked(False)
        self.OptIR_Button.setEnabled(True)
        self.OptSeg_Button.setChecked(True)
        self.OptSeg_Button.setEnabled(False)
        try:
            self.ColormapBoxOpt.setCurrentIndex(0)
            self.on_ColormapBoxOpt_changed()
        except:
            pass

    #XML export
    def newXMLButton_pressed(self):
        """
        Save region-of-interest information (polygon) into a xml file.
        """
        #select folder
        folder_save = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        #here, we need to ask if the data needs to be sorted
        capture_ID = []
        shapes = []

        # add Regions/Others
        try:
            column = 0
            for i in range(len(self.ListRegionsShapes)):
                key = list(self.ListRegionsShapes.keys())
                jj = 0
                for region in self.ListRegionsShapes[key[i]]:
                    if self.ShapesTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        tray = self.ShapesTreeElements[i].text(2)
                        capture_ID.append(tray)
                        jj = jj + 1

                        x = []
                        y = []

                        # obtain possible translation
                        try:
                            x0 = region.pos().x()
                            y0 = region.pos().y()
                        except:
                            pass

                        pathNew = region.path()
                        numberOfPoints = int(pathNew.elementCount())
                        print("numberOfPoints: ", numberOfPoints)
                        polygonList = zeros((numberOfPoints, 2))
                        for ii in range(numberOfPoints):
                            point = QtCore.QPointF(pathNew.elementAt(ii))
                            # print(str(i), '-Element: x', round(point.x()), 'y: ', round(point.y()))
                            x = append(x, int(point.x() + x0))
                            y = append(y, int(point.y() + y0))
                        polygonList[:, 0] = x[:]
                        polygonList[:, 1] = y[:]
                        shapes.append(polygonList)
        except:
            pass

        # add Infrared
        try:
            column = 0
            for i in range(len(self.ListRegionsInfrared)):
                key = list(self.ListRegionsInfrared.keys())
                jj = 0
                for region in self.ListRegionsInfrared[key[i]]:
                    if self.InfraredTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        tray = self.InfraredTreeElements[i].text(2)
                        capture_ID.append(tray)
                        jj = jj + 1

                        x = []
                        y = []

                        pathNew = region.path()
                        numberOfPoints = int(pathNew.elementCount())
                        print("numberOfPoints: ", numberOfPoints)
                        polygonList = zeros((numberOfPoints, 2))
                        for ii in range(numberOfPoints):
                            point = QtCore.QPointF(pathNew.elementAt(ii))
                            # print(str(i), '-Element: x', round(point.x()), 'y: ', round(point.y()))
                            x = append(x, int(point.x()))
                            y = append(y, int(point.y()))
                        polygonList[:, 0] = x[:]
                        polygonList[:, 1] = y[:]
                        print(polygonList)
                        shapes.append(polygonList)
        except:
            pass

        # add Regions/Others
        try:
            column = 0
            for i in range(len(self.ListRegionsShapes)):
                key = list(self.ListRegionsShapes.keys())
                jj = 0
                for region in self.ListRegionsShapes[key[i]]:
                    if self.ShapesTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        tray = self.ShapesTreeElements[i].text(2)
                        capture_ID.append(tray)
                        jj = jj + 1

                        x = []
                        y = []

                        #obtain possible translation
                        try:
                            x0 = region.pos().x()
                            y0 = region.pos().y()
                        except:
                            pass

                        pathNew = region.path()
                        numberOfPoints = int(pathNew.elementCount())
                        print("numberOfPoints: ", numberOfPoints)
                        polygonList = zeros((numberOfPoints, 2))
                        for ii in range(numberOfPoints):
                            point = QtCore.QPointF(pathNew.elementAt(ii))
                            # print(str(i), '-Element: x', round(point.x()), 'y: ', round(point.y()))
                            x = append(x, int(point.x() + x0))
                            y = append(y, int(point.y() + y0))
                        polygonList[:, 0] = x[:]
                        polygonList[:, 1] = y[:]
                        shapes.append(polygonList)
        except:
            pass

        #shapes needs to be sorted - not included yet

        offsetShape = [0, 0]
        scalingFactor = 1
        invertFactor = array([1, 1])

        shape2xml(shapes, capture_ID, self.TeachingPoints.astype(int), offsetShape, scalingFactor,
                  invertFactor, folderName = folder_save)

    def addXMLButton_pressed(self):
        """
        Adds region-of-interest information (polygon) to a xml file.
        """
        #open Dialog
        file_name,_ = QtWidgets.QFileDialog.getOpenFileName(None, 'Test Dialog', os.getcwd(), 'Files (*.xml)')
        file_extension = os.path.splitext(file_name)[-1]

        print(file_extension)

        # here, we need to ask if the data needs to be sorted
        capture_ID = []
        shapes = []

        # add Annotations to a new object that is then used for shape export to xml
        # add Infrared
        try:
            column = 0
            for i in range(len(self.ListRegionsInfrared)):
                key = list(self.ListRegionsInfrared.keys())
                jj = 0
                for region in self.ListRegionsInfrared[key[i]]:
                    if self.InfraredTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        tray = self.InfraredTreeElements[i].text(2)
                        capture_ID.append(tray)
                        jj = jj + 1

                        x = []
                        y = []

                        pathNew = region.path()
                        numberOfPoints = int(pathNew.elementCount())
                        print("numberOfPoints: ", numberOfPoints)
                        polygonList = zeros((numberOfPoints, 2))
                        for ii in range(numberOfPoints):
                            point = QtCore.QPointF(pathNew.elementAt(ii))
                            # print(str(i), '-Element: x', round(point.x()), 'y: ', round(point.y()))
                            x = append(x, int(point.x()))
                            y = append(y, int(point.y()))
                        polygonList[:, 0] = x[:]
                        polygonList[:, 1] = y[:]
                        print(polygonList)
                        shapes.append(polygonList)
        except:
            pass

        # add Regions/Others
        try:
            column = 0
            for i in range(len(self.ListRegionsShapes)):
                key = list(self.ListRegionsShapes.keys())
                jj = 0
                for region in self.ListRegionsShapes[key[i]]:
                    if self.ShapesTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        tray = self.ShapesTreeElements[i].text(2)
                        capture_ID.append(tray)
                        jj = jj + 1

                        x = []
                        y = []

                        # obtain possible translation
                        try:
                            x0 = region.pos().x()
                            y0 = region.pos().y()
                        except:
                            pass

                        pathNew = region.path()
                        numberOfPoints = int(pathNew.elementCount())
                        print("numberOfPoints: ", numberOfPoints)
                        polygonList = zeros((numberOfPoints, 2))
                        for ii in range(numberOfPoints):
                            point = QtCore.QPointF(pathNew.elementAt(ii))
                            # print(str(i), '-Element: x', round(point.x()), 'y: ', round(point.y()))
                            x = append(x, int(point.x() + x0))
                            y = append(y, int(point.y() + y0))
                        polygonList[:, 0] = x[:]
                        polygonList[:, 1] = y[:]
                        shapes.append(polygonList)
        except:
            pass

        offsetShape = [0, 0]
        scalingFactor = 1
        invertFactor = array([1, 1])

        if file_extension == ".xml":
            addshape2xml(shapes, capture_ID, offset=offsetShape, scalingFactor=scalingFactor,
                         invertFactor=invertFactor, fileName=file_name)
        else:
            pass

    def showXMLButton_pressed(self):
        """
        Import of region-of-interest information (polygon) from a xml file.
        """
        # select file
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select xml file", os.getcwd(), 'Files (*.xml)')
        file_extension = os.path.splitext(file_name)[-1]


        if file_extension == ".xml":
            shapes, calibrationPoints, capID = xml2shape(file_name)

            for i, shape in enumerate(shapes):
                print('i:' + str(i))
                #this requires some uniform notation (of course, could be solved in a different way)
                #need more colors
                if capID[i] == 'A':
                    threshold_yellow = [0.950, 0.950, 0.050]
                    threshold_yellow = [i * 255 for i in threshold_yellow]
                    self.color = threshold_yellow
                    region_state = 0

                if capID[i] == 'B':
                    threshold_black = [0.050, 0.050, 0.050]
                    threshold_black = [i * 255 for i in threshold_black]
                    self.color = threshold_black
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
                    threshold_purple = [0.950,  0.050, 0.950]
                    threshold_purple = [i * 255 for i in threshold_purple]
                    self.color = threshold_purple
                    region_state = 5

                capID_selected = capID[i]
                i = 0
                self.ContourPathListOpt = []

                pen = pg.mkPen(color=self.color, width=3)
                path = pg.arrayToQPath(shape[:, 0], shape[:, 1])
                ContourPath = pg.QtGui.QGraphicsPathItem()
                ContourPath.setPen(pen)
                if self.FillingCheckbox.isChecked() == True:
                    ContourPath.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2]))
                    ContourPath.setOpacity((self.opacitySlider.value() / 100))
                ContourPath.setPath(path)

                self.ContourPathListOpt = append(self.ContourPathListOpt, ContourPath)
                self.viewOpt.addItem(self.ContourPathListOpt[i])

                self.ContourPathListOpt[i].setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)

                elementNumber = int(len(self.ShapesTreeElements))
                self.ListRegionsShapes[elementNumber] = self.ContourPathListOpt
                child = QtWidgets.QTreeWidgetItem(self.ShapesTree)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
                child.setText(0, "Region of Interest {}".format(elementNumber))
                type_of_contour = region_state
                child.setText(1, "{}".format(type_of_contour))
                child.setText(2, capID_selected)
                child.setCheckState(0, QtCore.Qt.Unchecked)
                child.setCheckState(0, QtCore.Qt.Checked)
                child.setForeground(0, QtGui.QBrush(
                    QtGui.QColor(self.color[0], self.color[1], self.color[2])))
                self.ShapesTreeElements = append(self.ShapesTreeElements, child)

        print('done')

    def OnClick_IR(self, event):
        """
        Get position information and add it to the status bar.
        """
        position = self.imgLambda0.mapFromScene(event)
        posX = int((position.x()))
        posY = int((position.y()))
        printPosition = 'x:' + str(posX) + ' px, y:' + str(posY) + ' px'
        self.statusBar().showMessage(printPosition)
    def OnClick_Opt(self, event):
        """
        Get position information and add it to the status bar.
        """
        position = self.imgOpt.mapFromScene(event)
        posX = int((position.x()))
        posY = int((position.y()))
        printPosition = 'x:' + str(posX) + ' px, y:' + str(posY) + ' px'
        self.statusBar().showMessage(printPosition)
    def OnClick_OptZoom(self, event):
        """
        Get position information and add it to the status bar.
        """
        position = self.imgOptZoom.mapFromScene(event)
        posX = int((position.x()))
        posY = int((position.y()))
        printPosition = 'x:' + str(posX) + ' px, y:' + str(posY) + ' px'
        self.statusBar().showMessage(printPosition)

    def opacitySlider_changed(self):
        self.showROIAll_pressed()

    #QTreeWidget actions
    def openMenu(self, position):
        """
        Opens a menu for the region tree.
        """
        mdlIdx = self.RegionsListTree.indexAt(position)
        if not mdlIdx.isValid():
            return
        item = self.RegionsListTree.itemFromIndex(mdlIdx)

        right_click_menu = QtWidgets.QMenu()

        if item.parent() != None:
            act_del = right_click_menu.addAction(self.tr("Delete Item"))
            act_del.triggered.connect(partial(self.TreeItem_Delete, item))

        if item.parent() != None:
            act_del = right_click_menu.addAction(self.tr("Delete All"))
            act_del.triggered.connect(partial(self.TreeItem_DeleteAll, item))

        if item.parent() != None:
            act_del = right_click_menu.addAction(self.tr("Change Color"))
            act_del.triggered.connect(partial(self.TreeItem_ChangeColor, item))

        right_click_menu.exec_(self.sender().viewport().mapToGlobal(position))

    # Function to Delete item
    def TreeItem_Delete(self, item):
        """
        Delete element from region tree.
        :parameter: item - item to delete
        """
        index = self.InfraredTree.indexOfChild(item)
        if index != -1:
            self.InfraredTree.takeChild(index)
            self.InfraredTreeElements = delete(self.InfraredTreeElements, index)

            key = list(self.ListRegionsInfrared.keys())
            for region in self.ListRegionsInfrared[key[index]]:

                self.viewOpt.removeItem(region)

            self.ListRegionsInfrared.pop(key[index])
        else:
            index = self.ShapesTree.indexOfChild(item)
            if index != -1:
                self.ShapesTree.takeChild(index)
                self.ShapesTreeElements = delete(self.ShapesTreeElements, index)

                key = list(self.ListRegionsShapes.keys())
                for region in self.ListRegionsShapes[key[index]]:
                    if self.regButtonReverse.isChecked() == False:
                        self.viewOpt.removeItem(region)
                    else:
                        self.viewLambda0.removeItem(region)

                self.ListRegionsShapes.pop(key[index])

    def TreeItem_DeleteAll(self):
        """
        Delete all elements from region tree.
        """
        try:
            key = list(self.ListRegionsInfrared.keys())
            for i in range(len(self.ListRegionsInfrared)):
                index = len(self.ListRegionsInfrared) - i - 1
                for region in self.ListRegionsInfrared[key[index]]:
                    self.viewOpt.removeItem(region)
                self.ListRegionsInfrared.pop(key[index])
        except:
            pass

        try:
            key = list(self.ListRegionsShapes.keys())
            for i in range(len(self.ListRegionsShapes)):
                index = len(self.ListRegionsShapes) - i - 1
                for region in self.ListRegionsShapes[key[index]]:
                    if self.regButtonReverse.isChecked() == False:
                        self.viewOpt.removeItem(region)
                    else:
                        self.viewLambda0.removeItem(region)
                self.ListRegionsShapes.pop(key[index])
        except:
            pass

        self.ShapesTreeElements = []

        iterator = QtGui.QTreeWidgetItemIterator(self.InfraredTree, QtGui.QTreeWidgetItemIterator.All)
        iterator.value().takeChildren()

    def TreeItem_ChangeColor(self, item):
        """
        Specifies a color for the given element in the region tree.
        """
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

        index = self.InfraredTree.indexOfChild(item)
        if index != -1:
            child = self.InfraredTree.child(index)
            child.setForeground(0, QtGui.QBrush(
                QtGui.QColor(self.color[0], self.color[1], self.color[2])))
            key = list(self.ListRegionsInfrared.keys())
            for region in self.ListRegionsInfrared[key[index]]:
                pen = pg.mkPen(color=self.color, width=3)
                region.setPen(pen)
                region.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2]))
        else:
            index = self.ShapesTree.indexOfChild(item)
            if index != -1:
                child = self.ShapesTree.child(index)
                child.setForeground(0, QtGui.QBrush(
                    QtGui.QColor(self.color[0], self.color[1], self.color[2])))
                key = list(self.ListRegionsShapes.keys())
                for region in self.ListRegionsShapes[key[index]]:
                    pen = pg.mkPen(color=self.color, width=3)
                    region.setPen(pen)
                    region.setBrush(QtGui.QColor(self.color[0], self.color[1], self.color[2]))

            self.showROIAll_pressed()

    def showROIAll_pressed(self):
        """
        Displays the regions-of-interest on the reference image.
        """
        try:
            for i in range(len(self.ListRegionsInfrared)):
                key = list(self.ListRegionsInfrared.keys())
                for region in self.ListRegionsInfrared[key[i]]:
                    self.viewOpt.removeItem(region)
            for i in range(len(self.ListRegionsShapes)):
                key = list(self.ListRegionsShapes.keys())
                for region in self.ListRegionsShapes[key[i]]:
                    self.viewOpt.removeItem(region)
        except:
            pass

        try:
            column = 0

            for i in range(len(self.ListRegionsInfrared)):
                key = list(self.ListRegionsInfrared.keys())
                for region in self.ListRegionsInfrared[key[i]]:
                    if self.InfraredTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        region.setOpacity((self.opacitySlider.value() / 100))
                    else:
                        region.setOpacity((0))

                    if self.FillingCheckbox.isChecked() == False:
                        region.setBrush(QtGui.QColor(QtCore.Qt.transparent))
                    else:
                        color = region.pen().color()
                        region.setBrush(color)

                    self.viewOpt.addItem(region)

            for i in range(len(self.ListRegionsShapes)):
                key = list(self.ListRegionsShapes.keys())
                for region in self.ListRegionsShapes[key[i]]:
                    if self.ShapesTreeElements[i].checkState(column) == QtCore.Qt.Checked:
                        region.setOpacity((self.opacitySlider.value() / 100))
                    else:
                        region.setOpacity((0))

                    if self.FillingCheckbox.isChecked() == False:
                        region.setBrush(QtGui.QColor(QtCore.Qt.transparent))
                    else:
                        color = region.pen().color()
                        region.setBrush(color)

                    self.viewOpt.addItem(region)
        except:
           pass

if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    EnableDarkMode(app)

    ui = M2iraReg()
    ui.show()
    sys.exit(app.exec())
import sys
import numpy
import binascii
from curses import window
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from Window import Ui_MainWindow


hounsfieldPixelData = []
newHounsfieldPixelData = []

def ReadDicomData():
    pixelData = []
    for i in range(1,113):
        path = 'head-dicom/IM{}'.format(i)
        file = numpy.fromfile(path, dtype="uint16")
        for j, x in enumerate(file):
            if binascii.hexlify(x) == b'2800':
                if binascii.hexlify(file[j + 1]) == b'5010':
                    windowCenter = file[j + 5]
                if binascii.hexlify(file[j + 1]) == b'5110':
                    windowWidth = int(binascii.unhexlify(binascii.hexlify(file[j + 4]) + binascii.hexlify(file[j + 5])))
                if binascii.hexlify(file[j + 1]) == b'5210':
                    rescaleInterscept = (int(binascii.unhexlify(binascii.hexlify(file[j + 4]) + binascii.hexlify(file[j + 5]) + binascii.hexlify(file[j + 6]))))
                if binascii.hexlify(file[j + 1]) == b'5310':
                    rescaleSlope = int(binascii.unhexlify(binascii.hexlify(file[j + 4])))
            if binascii.hexlify(x) == b'e07f':
                temp = j
        file = file[temp + 6:]
        pixelData.append(file.reshape(512,512))
    pixelData = numpy.array(pixelData)
    return pixelData, windowCenter, windowWidth, rescaleSlope, rescaleInterscept

def SetGuiMethods(gui):
    gui.horizontalSlider1.valueChanged.connect(lambda: DrawDicom(gui, 0))
    gui.horizontalSlider2.valueChanged.connect(lambda: DrawDicom(gui, 1))
    gui.horizontalSlider3.valueChanged.connect(lambda: DrawDicom(gui, 2))
    gui.pushButton_4.clicked.connect(lambda: SetHounsfieldPixelData('default'))
    gui.pushButton_3.clicked.connect(lambda: SetHounsfieldPixelData('bones'))
    gui.pushButton_2.clicked.connect(lambda: SetHounsfieldPixelData('muscles'))
    gui.pushButton.clicked.connect(lambda: SetHounsfieldPixelData('blood'))

def setupSliders(gui):
    gui.horizontalSlider1.setMinimum(0)
    gui.horizontalSlider1.setMaximum(111)
    gui.horizontalSlider1.setValue(60)

    gui.horizontalSlider2.setMinimum(0)
    gui.horizontalSlider2.setMaximum(511)
    gui.horizontalSlider2.setValue(255)

    gui.horizontalSlider3.setMinimum(0)
    gui.horizontalSlider3.setMaximum(511)
    gui.horizontalSlider3.setValue(255)

def SetHounsfieldPixelData(type):
    global hounsfieldPixelData
    global newHounsfieldPixelData

    if type == "default":
        print("default")
        newHounsfieldPixelData = numpy.select([
            hounsfieldPixelData <= (windowCenter - 0.5 - (windowWidth - 1) / 2),
            hounsfieldPixelData > (windowCenter - 0.5 + (windowWidth - 1) / 2)
        ],
            [0, 255],
            ((hounsfieldPixelData - (windowCenter - 0.5)) / (windowWidth - 1) + 0.5) * 255 
        )
        newHounsfieldPixelData = numpy.array(newHounsfieldPixelData.reshape((112, 512, 512)), dtype=numpy.uint8)
    elif type == "bones":
        print("bones")
        newHounsfieldPixelData = numpy.select([
            hounsfieldPixelData <= (500 - 0.5 - (1900 - 1) / 2),
            hounsfieldPixelData > (500 - 0.5 + (1900 - 1) / 2),
        ],
            [0, 255],
            ((hounsfieldPixelData - (500-0.5)) / (1900 - 1) + 0.5) * 255
        )
        newHounsfieldPixelData = numpy.array(newHounsfieldPixelData.reshape((112, 512, 512)), dtype=numpy.uint8)
    elif type == "muscles":
        print("muscles")
        newHounsfieldPixelData = numpy.select([
            hounsfieldPixelData <= (35 - 0.5 - (55 - 1) / 2),
            hounsfieldPixelData > (35 - 0.5 + (55 - 1) / 2)
        ],
            [0,255],
            ((hounsfieldPixelData - (35 - 0.5)) / (55 - 1) + 0.5 ) * 255    
        )
        newHounsfieldPixelData = numpy.array(newHounsfieldPixelData.reshape((112, 512, 512)), dtype=numpy.uint8)
    elif type == "blood":
        print("blood")
        newHounsfieldPixelData = numpy.select([
            hounsfieldPixelData <= (50 - 0.5 - (75 - 1) / 2),
            hounsfieldPixelData > (50 - 0.5 + (75 - 1) / 2)
        ],
            [0,255],
            ((hounsfieldPixelData - (50 - 0.5)) / (75 - 1) + 0.5) * 255
        )
        newHounsfieldPixelData = numpy.array(newHounsfieldPixelData.reshape((112, 512, 512)), dtype=numpy.uint8)
    DrawDicom(gui, 3)

def DrawDicom(gui, id):
    if id == 0:
        image = QImage(newHounsfieldPixelData[gui.horizontalSlider1.value(),:,:], 512, 512, QImage.Format_Grayscale8)
        gui.label_3.setPixmap(QPixmap.fromImage(image))
    elif id == 1:
        val = numpy.rot90(newHounsfieldPixelData[:, int(gui.horizontalSlider2.value()), :], 2) 
        val = numpy.repeat(val, 5, axis = 0)
        image = QImage(val, 512, 512, QImage.Format_Grayscale8)
        gui.label_2.setPixmap(QPixmap.fromImage(image))  
    elif id == 2:
        val = numpy.rot90(newHounsfieldPixelData[:,:, int(gui.horizontalSlider3.value())], 2)
        val = numpy.repeat(val, 5, axis = 0)
        image = QImage(val, 512, 512, QImage.Format_Grayscale8)
        gui.label.setPixmap(QPixmap.fromImage(image))   
    else:
        DrawDicom(gui, 0)
        DrawDicom(gui, 1)
        DrawDicom(gui, 2)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv) #create a new instance of QApplication
    window = QtWidgets.QMainWindow() #create an instance of QMainWindow
    gui = Ui_MainWindow()
    gui.setupUi(window)
    setupSliders(gui)

    pixelData, windowCenter, windowWidth, rescaleSlope, rescaleInterscept = ReadDicomData()

    print("windowCenter: ", windowCenter)
    print("windowWidth: ", windowWidth)
    print("rescaleSlope: ", rescaleSlope)
    print("rescaleInterscept: ", rescaleInterscept)

    SetGuiMethods(gui)

    hounsfieldPixelData = rescaleSlope * pixelData + rescaleInterscept
    SetHounsfieldPixelData('default')
    DrawDicom(gui, 3)

    window.show() #show the window.
    sys.exit(app.exec_()) #Exit the program when you close the application window.
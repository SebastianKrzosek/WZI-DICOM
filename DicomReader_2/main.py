from random import gauss
import sys
import numpy
import binascii
from scipy import signal
from curses import window
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from Window import Ui_MainWindow


hounsfieldPixelData = []
newHounsfieldPixelData = []
edgeMatrix = numpy.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
gaussMatrix = 1/16 * numpy.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]])
gaussMatrix5 = 1/273 * numpy.array([[1,4,7,4,1],[4,16,26,16,4],[7,26,41,26,7],[4,16,26,16,4],[1,4,7,4,1]])
sharpMatrix = numpy.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

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
    gui.pushButton_9.clicked.connect(lambda: convFilters(gui,"sharp"))
    gui.pushButton_8.clicked.connect(lambda: useFilter("avg"))
    gui.pushButton_7.clicked.connect(lambda: convFilters(gui, "gauss"))
    gui.pushButton_6.clicked.connect(lambda: useFilter("max"))
    gui.pushButton_5.clicked.connect(lambda: convFilters(gui, "edge"))
    gui.pushButton_4.clicked.connect(lambda: SetHounsfieldPixelData('default'))
    gui.pushButton_3.clicked.connect(lambda: SetHounsfieldPixelData('bones'))
    gui.pushButton_2.clicked.connect(lambda: SetHounsfieldPixelData('muscles'))
    gui.pushButton_1.clicked.connect(lambda: firstHit(90))
    gui.pushButton.clicked.connect(lambda: SetHounsfieldPixelData('blood'))
    gui.firstHitBox.valueChanged.connect(lambda value: firstHit(value))

def setupSliders(gui):
    gui.horizontalSlider1.setMinimum(0)
    gui.horizontalSlider1.setMaximum(111)
    gui.horizontalSlider1.setValue(50)

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

def drawNewDicom(valueX, valueY, valueZ):
    image = QImage(valueX.astype("ubyte"), 512, 512, QImage.Format_Grayscale8)
    gui.label_3.setPixmap(QPixmap.fromImage(image))

    val = numpy.rot90(valueY.astype("ubyte"), 2)
    val = numpy.repeat(val, 5, axis = 0)
    image1 = QImage(val, 512, 512, QImage.Format_Grayscale8)
    gui.label_2.setPixmap(QPixmap.fromImage(image1))  

    value = numpy.rot90(valueZ.astype("ubyte"), 10)
    value = numpy.repeat(value, 5, axis=0)
    image2 = QImage(value, 512, 512, QImage.Format_Grayscale8)
    gui.label.setPixmap(QPixmap.fromImage(image2))

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

def firstHit(value):
    newHounsfieldPixelData = numpy.array(hounsfieldPixelData.reshape((112, 512, 512)), dtype=numpy.uint8)
    maximumX = numpy.argmax(newHounsfieldPixelData > value, axis = 2)
    maximumY = numpy.argmax(newHounsfieldPixelData > value, axis = 1)
    maximumZ = numpy.argmax(newHounsfieldPixelData > value, axis = 0)
    X = maximumX.copy()
    Y = maximumY.copy()
    Z = maximumZ.copy()

    for x in range(512):
        for y in range(512):
            if newHounsfieldPixelData[maximumZ[x, y], x, y] <= value and maximumZ[x, y] == 0:
                Z[x, y] = 0
            else:
                Z[x, y] = newHounsfieldPixelData[maximumZ[x, y], x, y].copy()

    for i in range(112):
        for j in range(512):
            if newHounsfieldPixelData[i, maximumY[i, j], j] <= value and maximumY[i, j] == 0:
                Y[i, j] = 0
            else:
                Y[i, j] = newHounsfieldPixelData[i, maximumY[i, j], j].copy()
            if  newHounsfieldPixelData[i, y, maximumX[i, j]] <= value and maximumX[i, j] == 0:
                    X[i, j] = 0
            else:
                X[i, j] = newHounsfieldPixelData[i, j, maximumX[i, j]].copy()
                
    drawNewDicom(Z, Y, X) 

def useFilter(type):
    pixData = numpy.array(hounsfieldPixelData.reshape((112, 512, 512)), dtype=numpy.uint8)
    if type == "max":
        X = pixData.max(axis=0).astype("ubyte")
        Y = pixData.max(axis=1).astype("ubyte")
        Z = pixData.max(axis=2).astype("ubyte")
    elif type == "avg":
        X = pixData.mean(axis=0).astype("ubyte")
        Y = pixData.mean(axis=1).astype("ubyte")
        Z = pixData.mean(axis=2).astype("ubyte")
        
    drawNewDicom(X, Y, Z)

def convFilters(gui, type):
    if type == "edge":
        tmpMatrix = edgeMatrix
    elif type == "gauss":
        tmpMatrix = gaussMatrix
    elif type == "sharp":
        tmpMatrix = sharpMatrix


    X = newHounsfieldPixelData[int(gui.horizontalSlider1.value()),:,:]
    X = convolve2D(X, tmpMatrix)
    
    Y = newHounsfieldPixelData[:, int(gui.horizontalSlider2.value()), :]
    Y = convolve2D(Y, tmpMatrix)

    Z = newHounsfieldPixelData[:, :, int(gui.horizontalSlider3.value())]
    Z = convolve2D(Z, tmpMatrix)

    drawNewDicom(X, Y, Z)

def convolve2D(data, transformMatrix):
    transformMatrix = numpy.flipud(numpy.fliplr(transformMatrix))
    result = numpy.zeros((int(((data.shape[0] - transformMatrix.shape[0] + 2 )) + 1), int(((data.shape[1] - transformMatrix.shape[1] + 2 )) + 1)))
    imagePadded = numpy.zeros((data.shape[0] + 2, data.shape[1] + 2))
    imagePadded[1:-1, 1:-1] = data

    for y in range(data.shape[1]):
        if y > data.shape[1] - transformMatrix.shape[1]:
            break
        for x in range(data.shape[0]):
            if x > data.shape[0] - transformMatrix.shape[0]:
                break
            try:
                result[x, y] = (transformMatrix * imagePadded[x: x + transformMatrix.shape[0], y: y + transformMatrix.shape[1]]).sum()
            except:
                break
    return result

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
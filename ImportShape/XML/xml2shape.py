# 23.10.20 SSR

"""Import of an xml-file and return the individual shapes

# https://www.geeksforgeeks.org/serialize-python-dictionary-to-xml/
# https://wiki.selfhtml.org/wiki/XML/Regeln/XML-Deklaration

"""

from numpy import zeros, array
from matplotlib.pyplot import show, figure, plot, draw, imshow
import xmltodict
from collections import OrderedDict


# used for print warning
import warnings
def format_Warning(message, category, filename, lineno, line=''):
    return str(filename) + ':' + str(lineno) + ': ' + category.__name__ + ': ' + str(message) + '\n'
warnings.formatwarning = format_Warning


# define function
def xml2shape(FileName):
    if not isinstance(FileName, str):
        FileName = str(FileName)

    print(FileName)

    try:
        #dict_file = parse(FileName)  # parse an open file
        #print(dict_file)
        with open(FileName) as fd:
            dict_file = xmltodict.parse(fd.read())
            #print(dict_file)

            calibrationPoints = zeros((3, 2))

            calibrationPoints[0, 0] = int(dict_file['ImageData']['X_CalibrationPoint_1'])
            calibrationPoints[0, 1] = int(dict_file['ImageData']['Y_CalibrationPoint_1'])
            calibrationPoints[1, 0] = int(dict_file['ImageData']['X_CalibrationPoint_2'])
            calibrationPoints[1, 1] = int(dict_file['ImageData']['Y_CalibrationPoint_2'])
            calibrationPoints[2, 0] = int(dict_file['ImageData']['X_CalibrationPoint_3'])
            calibrationPoints[2, 1] = int(dict_file['ImageData']['Y_CalibrationPoint_3'])

            print(dict_file['ImageData']['ShapeCount'])
            print(int(dict_file['ImageData']['Shape_1']['PointCount']))
            print(dict_file['ImageData']['Shape_1']['X_1'])

            shape_count = int(dict_file['ImageData']['ShapeCount'])

            shape_list = OrderedDict()

            capID = []

            for jj in range(0, shape_count):

                shape_number = 'Shape_' + str(jj + 1)
                size_shape = int(dict_file['ImageData'][shape_number]['PointCount'])
                shape_help = zeros((size_shape, 2))
                capID.append(dict_file['ImageData'][shape_number]['CapID'])
                print(size_shape)

                for ii in range(0, size_shape):

                    point_number_x = 'X_' + str(ii+1)
                    point_number_y = 'Y_' + str(ii+1)
                    shape_number = 'Shape_' + str(jj + 1)

                    shape_help[ii, 0] = int(float((dict_file['ImageData'][shape_number][point_number_x])))
                    shape_help[ii, 1] = int(float((dict_file['ImageData'][shape_number][point_number_y])))

                shape_list[jj] = shape_help
                print(shape_number)

            shapes = [array(shapes) for _, shapes in sorted(shape_list.items())]
            return shapes, calibrationPoints, capID
    except:
        warnings.warn('Data type is not accepted for input in function xml2shape().')


# Example
if __name__ == "__main__":

    file_name = r'E:\schmidts\Daten\20210708_FTIR_POL_PEN\LMD\shape_13072021_1649.xml'
    file_name = r'E:\schmidts\Daten\20210708_FTIR_POL_PEN\LMD\shape_13072021_1648.xml'

    shapes, calibrationPoints, capID = xml2shape(file_name)

    print(calibrationPoints)
    print(capID)
    for n, shape in enumerate(shapes):
        print(n)
        fig = figure(1)
        plot(calibrationPoints[:, 0].astype(int), calibrationPoints[:, 1].astype(int), '.r')
        plot(shape[:, 0].astype(int), shape[:, 1].astype(int), linewidth=2)
        draw()
    show()

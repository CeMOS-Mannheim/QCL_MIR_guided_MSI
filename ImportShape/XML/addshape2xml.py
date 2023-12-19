# 22.09.21 SSR

"""Add a shape to an excisting xml-file and return the individual shapes

# https://www.geeksforgeeks.org/serialize-python-dictionary-to-xml/
# https://wiki.selfhtml.org/wiki/XML/Regeln/XML-Deklaration

"""

from numpy import zeros, array, ones, size
import xml.etree.ElementTree as ET

# used for print warning
import warnings
def format_Warning(message, category, filename, lineno, line=''):
    return str(filename) + ':' + str(lineno) + ': ' + category.__name__ + ': ' + str(message) + '\n'
warnings.formatwarning = format_Warning

# define function
def addshape2xml(segments, capture_ID, calibration_points = zeros((3, 2)), offset = array([0, 0]), scalingFactor = 1, invertFactor = array([1, 1]), fileName = "None"):
    # parsing directly.
    tree = ET.parse(fileName)
    root = tree.getroot()

    #find number of Counts
    item_ShapeCount = root.find('ShapeCount')
    number_of_shapes = item_ShapeCount.text
    print(number_of_shapes)

    print(len(segments))

    item_ShapeCount.text = str(int(number_of_shapes) + len(segments))
    i = 0
    for segment in segments:
        add_shape_name = str('Shape_' + str(int(number_of_shapes) + i + 1))
        itemid = ET.Element(add_shape_name)
        root.append(itemid)

        new = ET.SubElement(itemid, 'PointCount')
        new.text = str(len(segment))
        new = ET.SubElement(itemid, 'CapID')
        new.text = str(capture_ID[i])

        for jj in range(len(segment)):
            x_number = "X_" + str(jj + 1)
            y_number = "Y_" + str(jj + 1)
            x = round(invertFactor[0] * segment[jj, 0] * scalingFactor + offset[0])
            y = round(invertFactor[1] * segment[jj, 1] * scalingFactor + offset[1])

            new_x = ET.SubElement(itemid, x_number)
            new_x.text = str(x)
            new_y = ET.SubElement(itemid, y_number)
            new_y.text = str(y)

        i = i + 1

    #name = r'E:\schmidts\Daten\AlexandraScils\shape_22092021_113014 - Kopie_2.xml'
    tree.write(fileName)

# Example
if __name__ == "__main__":

    file_name = r'E:\schmidts\Daten\AlexandraScils\shape_22092021_113014 - Kopie.xml'

    # create radnom list of ndarrays
    list_ndarray = dict()
    array_0 = zeros((2, 2))
    array_1 = ones((3, 2))
    array_1[2, 1] = 6
    list_ndarray[0] = array_0
    list_ndarray[1] = array_1
    segments = [array(segment) for _, segment in sorted(list_ndarray.items())]

    capture_ID = [''] * size(segments)
    capture_ID[0] = 'C3'
    capture_ID[1] = 'A1'

    addshape2xml(segments, capture_ID, fileName = file_name)



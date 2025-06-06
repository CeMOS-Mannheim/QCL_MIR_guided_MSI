"""The function shape2xml accepts a list of ndarrays with the position
informations of pixels of a given shape (element of the list, N pixels),
array(N,2), 2: x,y, The information is writtin into a dictionary which
is then transformed into xml format using dicttoxml

Infos
# https://www.geeksforgeeks.org/serialize-python-dictionary-to-xml/
# https://wiki.selfhtml.org/wiki/XML/Regeln/XML-Deklaration

"""

from numpy import zeros, ones, ndarray, array, shape, size
import dicttoxml
from collections import OrderedDict
from datetime import datetime

# used for print warning
import warnings
def format_Warning(message, category, filename, lineno, line=''):
    return str(filename) + ':' + str(lineno) + ': ' + category.__name__ + ': ' + str(message) + '\n'
warnings.formatwarning = format_Warning


# define function
def shape2xml(segments, capture_ID, calibration_points, offset = array([0, 0]), scalingFactor = 1, invertFactor = array([1, 1]), folderName = "None"):
    try:
        # list of ndarray as dictionary
        dict = OrderedDict()  # initialize ordered dictionary
        dict["GlobalCoordinates"] = 1  # add alement
        dict["X_CalibrationPoint_1"] = calibration_points[0,0]  # add element
        dict["Y_CalibrationPoint_1"] = calibration_points[0,1]  # add element
        dict["X_CalibrationPoint_2"] = calibration_points[1,0]  # add element
        dict["Y_CalibrationPoint_2"] = calibration_points[1,1]  # add element
        dict["X_CalibrationPoint_3"] = calibration_points[2,0]  # add element
        dict["Y_CalibrationPoint_3"] = calibration_points[2,1]  # add element
        dict["ShapeCount"] = shape(segments)[0]  # add element

        # add list with the pixel positions of a segement (x_i,y_i) to the dictionary

        for n, segment in enumerate(segments):
            shape_number = "Shape_" + str(n+1)

            new_dict = OrderedDict()
            new_dict["PointCount"] = shape(segment)[0]
            new_dict["CapID"] = capture_ID[n]

            for jj in range(shape(segment)[0]):
                x_number = "X_" + str(jj + 1)
                y_number = "Y_" + str(jj + 1)
                print(segment[jj, 0], segment[jj, 1])
                print(round(segment[jj, 0]), round(segment[jj, 1]))
                new_dict[str(x_number)] = round(invertFactor[0]*segment[jj, 0]*scalingFactor + offset[0])
                new_dict[str(y_number)] = round(invertFactor[1]*segment[jj, 1]*scalingFactor + offset[1])
            dict[shape_number] = new_dict

        xml_file = dicttoxml.dicttoxml(dict, custom_root="ImageData", attr_type=False)

        # string to xml, saving to xml file, Obtain decode string by decode() function
        xml_decode = xml_file.decode()

        if folderName == "None":
            now = datetime.now()  # current date and time
            date_time = now.strftime("%d%m%Y_%H%M%S")

            file_name = "shape_" + date_time + ".xml"
        else:
            now = datetime.now()  # current date and time
            date_time = now.strftime("%d%m%Y_%H%M%S")

            file_name = "shape_" + date_time + ".xml"
            file_name = folderName + "/" + file_name

        print(file_name)
        xmlfile = open(file_name, "w")
        xmlfile.write(xml_decode)
        xmlfile.close()

        print('Export done.')

    except:
        warnings.warn('Data type is not accepted for input in function shape2xml(). Xml file was not written.')

#add shapes to an existing xml file
def addshape2xml(segments, capture_ID, offset = array([0, 0]), scalingFactor = 1, invertFactor = array([1, 1])):
    try:
        pass
    except:
        warnings.warn('Data type is not accepted for input in function shape2xml(). Xml file was not written.')


# Example
if __name__ == "__main__":

    print('None included here.')


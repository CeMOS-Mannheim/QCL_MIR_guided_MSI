"""
This functions helps to recognize counts with holes.

"""

import numpy as np
from skimage.measure import euler_number, label
from skimage import measure
from scipy.ndimage.morphology import binary_fill_holes
import skimage.exposure as exposure

# define function
def FindContours(image, loop = 5, level = 0.5):
    image = (exposure.rescale_intensity(image, out_range=(0, 1))).astype('uint8')

    #obtain number of holes and regions with connectivity of 2 (8pixels)
    eNum = euler_number(image, connectivity=2) # Euler number is the number of objects minus the number of holes
    object_nb_eNum = label(image, connectivity=2).max() # number of objects
    holes_nb_eNum = object_nb_eNum - eNum # number oholes

    number_of_repetitions = loop

    if holes_nb_eNum >= 1:
        donut_filled = binary_fill_holes(image)
        donut_holes = image.astype(bool) ^ donut_filled.astype(bool)
        donut_holes_filled = binary_fill_holes(donut_holes)

        # Find contours at a constant value of 0.5
        contours_outer_shape = measure.find_contours(donut_filled, level, positive_orientation='low',
                                                     fully_connected='high')
        contours_holes = measure.find_contours(donut_holes_filled, level, positive_orientation='high',
                                               fully_connected='high')

        print('Number of elements in outer shapes: ', len(contours_outer_shape))
        print('Number of elements in holes: ', len(contours_outer_shape))


        eNum = euler_number(donut_holes, connectivity=2)
        object_nb_eNum = label(donut_holes, connectivity=2).max()
        holes_nb_eNum = object_nb_eNum - eNum
        print('Number of holes: ', holes_nb_eNum)

        for i in range(number_of_repetitions):
            if holes_nb_eNum >= 1:
                donut_filled = binary_fill_holes(donut_holes)
                donut_holes_inner = donut_holes.astype(bool) ^ donut_filled.astype(bool)
                donut_holes_filled = binary_fill_holes(donut_holes_inner)
                donut_holes = donut_holes_inner.astype(bool) ^ donut_holes_filled.astype(bool)
                donut_holes_new_filled = binary_fill_holes(donut_holes)

                contours_outer_shape_new = measure.find_contours(donut_holes_filled, level, positive_orientation='low',
                                                                 fully_connected='high')
                contours_holes_new = measure.find_contours(donut_holes_new_filled, level, positive_orientation='high',
                                                           fully_connected='high')

                for contour in contours_outer_shape_new:
                    contours_outer_shape.append(contour)
                for contour in contours_holes_new:
                    contours_holes.append(contour)

                eNum = euler_number(donut_holes, connectivity=2)
                object_nb_eNum = label(donut_holes, connectivity=2).max()
                holes_nb_eNum = object_nb_eNum - eNum
                print('Number of holes: ', holes_nb_eNum)

        return contours_outer_shape, contours_holes
    else:
        # Find contours at a constant value of 0.5
        contours_outer_shape = measure.find_contours(image, level, positive_orientation='low',
                                                     fully_connected='high')

        print('Number of elements in outer shapes: ', len(contours_outer_shape))
        return contours_outer_shape, []

def FindOpenContours(contours_outer_shape, contours_holes):
    min_index_list = np.zeros((len(contours_holes), 2)).astype(int)
    new_contours = []
    number_of_initial_holes = int(len(contours_holes))
    m = 0
    for iii in range(number_of_initial_holes):
        hole_index = np.zeros(len(contours_holes)).astype(int)
        min_dist = np.zeros(len(contours_holes)).astype(int)
        k = 0
        for contour_holes in contours_holes:
            l = 0
            min_dist_single = 100000
            for contour in contours_outer_shape:
                i = 0
                for ii in contour:
                    j = 0
                    for jj in contour_holes:
                        dx = abs(contour[i, 0] - contour_holes[j, 0])
                        dy = abs(contour[i, 1] - contour_holes[j, 1])
                        dist = np.sqrt(dx * dx + dy * dy)
                        if dist < min_dist_single:
                            min_index_list[k, 1] = int(i)
                            min_index_list[k, 0] = int(j)
                            min_dist_single = dist
                            hole_index[k] = l
                        j = j + 1
                    i = i + 1
                l = l + 1
            min_dist[k] = min_dist_single
            k = k + 1

        min_value = min(min_dist)
        itemindex = np.where(min_dist == min_value)
        index_k = itemindex[0][0].astype(int)
        k = index_k
        print("min dist ", min_dist)
        print("index_k ", index_k)
        print("hole_index ", hole_index)

        contour = contours_outer_shape[hole_index[index_k]]
        contour = np.delete(contour, -1, 0)
        contour_holes = contours_holes[index_k]
        contour_holes = np.delete(contour_holes, -1, 0)

        new_shape = np.zeros((len(contour_holes) + len(contour) - 2 * 1, 2))

        new_shape[0:min_index_list[k, 0], 0] = contour_holes[0:min_index_list[k, 0], 0]
        new_shape[0:min_index_list[k, 0], 1] = contour_holes[0:min_index_list[k, 0], 1]

        contour = np.roll(contour, len(contour) - min_index_list[k, 1] - 1, 0)
        contour = np.delete(contour, -1, 0)

        new_shape[min_index_list[k, 0]:min_index_list[k, 0] + len(contour), 0] = contour[:, 0]
        new_shape[min_index_list[k, 0]:min_index_list[k, 0] + len(contour), 1] = contour[:, 1]

        new_shape[min_index_list[k, 0] + len(contour):, 0] = contour_holes[min_index_list[k, 0] + 1:, 0]
        new_shape[min_index_list[k, 0] + len(contour):, 1] = contour_holes[min_index_list[k, 0] + 1:, 1]

        new_shape = np.append(new_shape, [new_shape[0, :]], axis=0)

        new_contours.append(new_shape)

        contours_outer_shape[hole_index[index_k]] = new_shape
        print("amount of holes: ", len(contours_holes))
        contours_holes = np.delete(contours_holes, index_k, 0)
        print("amount of holes: ", len(contours_holes))
        m = m + 1

    return contours_outer_shape

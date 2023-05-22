import os
import cv2 as cv
import numpy as np
import circle_fit

slider_max = 255
title_window = "Threshold_window"


def on_trackbar(val):
    R_src = srcWithoutCircles.copy()
    # BGR coding
    (B, G, R) = cv.split(R_src)
    copy_src = R.copy()
    ret, threshold_img = cv.threshold(copy_src, val, 255, cv.THRESH_BINARY)
    # threshold_img=cv.adaptiveThreshold(copy_src,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,\
    #                        cv.THRESH_BINARY_INV,val,3)
    kernel = np.ones((3, 3), np.uint8)

    # threshold_img=cv.erode(threshold_img,kernel,iterations=1)
    # threshold_img=cv.dilate(threshold_img,kernel,iterations=1)
    grad_x = cv.Sobel(threshold_img, -1, 1, 0)
    cv.imshow(title_window, threshold_img)


def find_sample_edges(src, threshold_value):
    """'function is working on the image without markers and their surroundings (only "edges" of the sample are present)"""
    R_src = src.copy()
    # BGR coding
    (B, G, R) = cv.split(R_src)
    # taking only red component of the image
    copy_src = R.copy()
    copy_src = cv.blur(copy_src, (3, 3))

    ret, threshold_img = cv.threshold(copy_src, threshold_value, 255, cv.THRESH_BINARY)

    grad_x = cv.Sobel(threshold_img, -1, 1, 0)
    # Find contours
    contours, hierarchy = cv.findContours(grad_x, cv.RETR_CCOMP, cv.CHAIN_APPROX_NONE)

    # get edges
    contour_list = []
    for contour in contours:
        moments = cv.moments(contour)

        # filter out short contours
        if (contour[:, :, 1].max() - contour[:, :, 1].min() < 100) or (
            moments["mu20"] == 0
        ):
            continue
        param = moments["mu02"] / moments["mu20"]
        area = cv.contourArea(contour)
        # check if is a circle
        if (param > 0.98) & (area > 100):
            contour_list.append(contour)
            cv.drawContours(R_src, contour_list, -1, (255, 0, 0), 2)
            x = []
            y = []
            for t in contour:
                x.append(t[0][0])
                y.append(t[0][1])
            x = np.r_[x]
            y = np.r_[y]
            temp = circle_fit.fit_circle(x, y)
        Result_file = open(result_path + os.path.splitext(img_file)[0] + ".txt", "w+")
        Result_file.write(img_file + "\n")
        for c in contour_list:
            np.savetxt(Result_file, np.squeeze(c), fmt="%.4f", delimiter=",")
        Result_file.close()

    # take all contours and join them into single one
    edge_array = np.squeeze(contour_list[0])
    for i in range(1, len(contour_list)):
        temp_array = np.squeeze(contour_list[i])
        edge_array = np.vstack((edge_array, temp_array))
    # calculate curvature for joined contour
    fitted_circle = circle_fit.fit_circle(edge_array[:, 0], edge_array[:, 1])
    return fitted_circle


catalog_names = [
    "02_S1_3",
    "03_S1_5",
    "04_S1_6",
]

# window with trackbar to tune the threshold
cv.namedWindow(title_window)
trackbar_name = "Threshold %d" % slider_max

cv.createTrackbar(
    trackbar_name,
    title_window,
    127,
    slider_max,
    on_trackbar,
)

print("Filename\tCurvature [1/pix]")

for i in range(0, len(catalog_names)):
    img_path = "Example_images\\" + catalog_names[i][:] + "\\"
    img_list = os.listdir(img_path)
    result_path = img_path

    # Result_file=open(result_path+'results.txt','w+')

    for img_file in img_list:
        if img_file.endswith(".jpg" or ".JPG"):
            src = cv.imread(img_path + img_file)
            if src is None:
                print("Could not open or find the image:", img_file)
                exit(0)
            # print("Processing of: " + img_file)

            # remove markers and their surrounding from the photo
            srcWithoutCircles = src.copy()
            circlesInPhoto = circle_fit.find_circles(src)
            for circle_param in circlesInPhoto:
                x_c_0 = int(circle_param[0]) - int(circle_param[2]) - 25
                x_c_1 = int(circle_param[0]) + int(circle_param[2]) + 25
                y_c_0 = int(circle_param[1]) - int(circle_param[2]) - 25
                y_c_1 = int(circle_param[1]) + int(circle_param[2]) + 25
                if x_c_0 < 0:
                    x_c_0 = 0
                if y_c_0 < 0:
                    y_c_0 = 0
                srcWithoutCircles[y_c_0:y_c_1, x_c_0:x_c_1] = 0

            current_slider_value = cv.getTrackbarPos(trackbar_name, title_window)
            on_trackbar(current_slider_value)
            cv.waitKey()
            fitted_circle = find_sample_edges(srcWithoutCircles, current_slider_value)
            print(img_file, "\t", str(1 / fitted_circle[2]))

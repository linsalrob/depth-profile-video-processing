'''Create a pairwise score between a single image and a series of images in a directory'''

import matplotlib
matplotlib.use('agg')
import numpy as np
import cv2
import argparse
import os
import sys

parser = argparse.ArgumentParser(description="Calculate a distance matrix between a single image and a folder of other images")
parser.add_argument('-b', '--base', help="The original image", required=True)
parser.add_argument('-d', '--dir', help="The directory of images", required=True)
parser.add_argument('-r', '--ratio', help="Maximum ratio between two key points (default=0.7)", default=0.7, type=int)
args=parser.parse_args()

# Initiate SIFT detector
sift = cv2.SIFT()

img1 = cv2.imread(args.base)
# find the keypoints and descriptors with SIFT
kp1, des1 = sift.detectAndCompute(img1,None)

for imfile in os.listdir(args.dir):
    sys.stderr.write("Reading " + imfile + "\n")
    img2 = cv2.imread(os.path.sep.join([args.dir, imfile]), 0)

    # find the keypoints and descriptors with SIFT
    kp2, des2 = sift.detectAndCompute(img2,None)

    # FLANN parameters
    sys.stderr.write("Flanning\n")
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks=50)   # or pass empty dictionary

    sys.stderr.write("Flan matching\n")
    flann = cv2.FlannBasedMatcher(index_params,search_params)

    matches = flann.knnMatch(des1,des2,k=2)

    # Need to keep only good matches, so create a mask
    matchesMask = [[0,0] for i in xrange(len(matches))]

    sys.stderr.write("Ratioing\n")
    # ratio test as per Lowe's paper
    dist=0
    for i,(m,n) in enumerate(matches):
        if m.distance < args.ratio*n.distance:
            dist+=1

    print("\t".join([args.base, imfile, str(dist)]))




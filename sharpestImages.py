''' Find the sharpest images in a video using the laplacian '''

# coding: utf-8
import matplotlib
import cv2
matplotlib.use('agg')
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy
from scipy.cluster import vq
import sys
import argparse
import random
import os

parser = argparse.ArgumentParser(description="Find the sharpest images in a video using the laplacian")
parser.add_argument('-f', '--file', help='Movie file(s). You can provide more than one video and the first will be used to create the list of random images. Color plots will be made for all images.', required=True, nargs='+')
parser.add_argument('-p', '--peaks', help='Peaks file. This should be one line per movie file with comma separated peaks. If this is provided we only run through the movies once. Otherwise we will run through them 2x each')
parser.add_argument('-i', '--ignore', help='Number of frames at the beginning to ignore. If you want to run in a bit and ignore some frames, use this.', type=int, default=0);

args=parser.parse_args()


peaks = {}
firstPeaks = []

def readPeaks(fin):
    global firstPeaks
    with open (fin, 'r') as f:
        for data in f:
            data = data.rstrip()
            parts=data.split("\t")
            peaks[parts[0]]=parts[1].split(',')
            if len(firstPeaks) < 1:
                firstPeaks=parts[1].split(',')


def printImages(filename, imgs, band):
    keys = imgs.keys()

    if len(keys)-1 <= 0:
        sys.stderr.write("No more images to write. skipped\n")
        return

    if not os.path.exists(str(band)):
        os.mkdir(str(band))
    for r in keys:
        cv2.imwrite(str(band) + os.path.sep + str(keys[r]) + "." + filename + ".JPG", imgs[keys[r]])
    sys.stderr.write("Saved images from " + str(filename) + " after band " + str(band) + " are: " + " ".join(map (str, savedImages.keys())) + "\n")


def printAnImage(img, filename, count, loc):
    outfile = str(loc) + os.path.sep + str(count) + "." + filename + ".JPG";
    sys.stderr.write("Saving " + outfile + "\n")
    cv2.imwrite(outfile, img)

def findPeaks(fileName):
    vid = cv2.VideoCapture(fileName)

    paths = fileName.split('/')
    videoFileName = paths[-1]

    ret, img = vid.read()
    average=[]
    count=0
    band=1
    allpeaks=[]


    lastimwrite=0
    while (ret):
        count += 1
        if (count < args.ignore):
            ret, img = vid.read()
            continue

        rgb=[]
        for i in range(3):
            channel = img[:,:,i]
            if args.median:
                rgb.append(numpy.median(channel))
            else:
                rgb.append(numpy.average(channel))
        if (count % 1000) < 1:
            sys.stderr.write(str(count) + ": " + str(rgb[0]) + " " + str(rgb[1]) + " " + str(rgb[2]) + "\n")

        if numpy.average(img[:,:,0]) > 200 or numpy.average(img[:,:,1]) > 200 or numpy.average(img[:,:,2]) > 200:
            allpeaks.append(count)
            if count - lastimwrite > 300 and len(imgset.keys()) >= 1: #this is because we may have multiple images with BGR >150. This requires 10s between peaks (at 30 fps)
                band+=1
                lastimwrite=count

        ret, img = vid.read()

    global firstPeaks
    # now use kmeans to identify the rgb peaks.
    if len(firstPeaks) < 1:
        # if we already have some peaks we want to use them as a seed for the k means clustering
        peaks[videoFileName], variance = vq.kmeans(numpy.array(allpeaks), band)
        firstPeaks = peaks[videoFileName]
    else:
        peaks[videoFileName], variance = vq.kmeans(numpy.array(allpeaks), firstPeaks)
    peaks[videoFileName].sort()
    sys.stderr.write(videoFileName + "\t" + ",".join(map(str, peaks[videoFileName])) + "\n")


if args.peaks:
    readPeaks(args.peaks)

## process the other files
for f in args.file:
    if f not in peaks:
        sys.stderr.write("Finding the peaks in " + f)
        findPeaks(f)
    sys.stderr.write("Processing " + f + "\n")

    paths = f.split('/')
    videoFileName = paths[-1]

    vid = cv2.VideoCapture(f)
    ret, img = vid.read()
    count=0
    maxl=0
    maxf=0
    minf=1000
    minl=1000
    while (ret):
        count+=1
        if (count < args.ignore):
            ret, img = vid.read()
            continue

        grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(grey,cv2.CV_64F)
        cumsum = laplacian.cumsum()
        # find the value of the 95% quantile
        flat = laplacian.flatten()
        flat.sort()
        ninetyfive =  flat[int(0.95 * len(flat))] # 5% quantile
        fifty = flat[int(0.5 * len(flat))] # midpoint
        five =  flat[int(0.05 * len(laplacian))] # 5% quantile

        if fifty > maxf: 
            maxf = fifty
        if fifty < minf:
            minf = fifty

        if ninetyfive > maxl: 
            maxl = ninetyfive
        if ninetyfive < minl: 
            minl = ninetyfive

        if count % 100 == 0:
            print "\t".join(map(str, [count, minl, maxl, minf, maxf]))
            maxl=0
            minl=1000
        
        ## print "\t".join(map(str, [five, ninetyfive]))
        
        ## some debug code:
        ##
        ## print("Lap shape is " + str(laplacian.shape))
        ## print("Lap flat shape is " + str(flat.shape))
        ## print("Lap first element is " + str(flat[0]))
        ## print("Lap LAST element is " + str(flat[len(flat)-1]))
        ## print("Lap 5% is " + str(five))
        ## print("Lap 95% is " + str(ninetyfive))
        ## print("max: " + str(flat.max()) + " versus " + str(laplacian.max()))
        ## print("Min: " + str(flat.min()) + " versus " + str(laplacian.min()))
        ## print
























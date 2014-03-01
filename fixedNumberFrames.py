
'''

Generate some random frames from an image, and also plot out the colors

Gareth flips the camera every 5m, and this causes a spike in the RGB signals. We want to use these as pointers and to allow us to 
register the videos. We use k-means to identify the middle of each slice, and use the difference of those as the offset in the register.

In this version, I create a directory for each of the movies and save from min to max number of images per shot. The min/max are calculated from aligning the peaks.

'''




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

parser = argparse.ArgumentParser(description="Plot the color profiles of movies from Gareth's goPros")
parser.add_argument('-f', '--file', help='Movie file(s). You can provide more than one video and the first will be used to create the list of random images. Color plots will be made for all images.', required=True, nargs='+')
# parser.add_argument('-o', '--out', help='output file name to draw the graph to', required=True)
parser.add_argument('-g', '--gap', help='Number of images between printing', required=True, type=int)
parser.add_argument('-m', '--frames', help='Stop after this number of frames (default == all)', type=int)
parser.add_argument('-i', '--ignore', help='Number of frames at the beginning to ignore. If you want to run in a bit and ignore some frames, use this.', type=int, default=0);
parser.add_argument('-s', '--start', help='Start saving at this image number. This includes any ignored images', type=int, default=1);
args = parser.parse_args()

savedImages = {}

if args.start < args.ignore:
    args.start += args.ignore

if not os.path.exists("FixedFrames"):
    os.mkdir("FixedFrames")
dest=os.path.sep.join(["FixedFrames", str(args.gap)])
os.mkdir(dest) ## I leave this here without a check so the program breaks if the file exists.


def printAnImage(img, filename, count, loc):
    outfile = str(loc) + os.path.sep + str(count) + "." + filename + ".JPG";
    sys.stderr.write("Saving " + outfile + "\n")
    cv2.imwrite(outfile, img)


## proess the first image
vid = cv2.VideoCapture(args.file[0])
if vid.isOpened():
    print("Reading video " + args.file[0])
else:
    sys.stderr.write("There was an error opening " + args.file[0] + "\n")
    sys.exit()

paths = args.file[0].split('/')
videoFileName = paths[-1]
sys.stderr.write("Parsing images in " + args.file[0] + " (" + videoFileName + ")\n")

ret, img = vid.read()
count=0
band=1
allpeaks=[]
countdown=args.gap + 1

lastimwrite=0
while (ret):
    count += 1
    if (count < args.ignore):
        ret, img = vid.read()
        continue

    if numpy.average(img[:,:,0]) > 200:
        allpeaks.append(count)
        if count - lastimwrite > 300: #this is because we may have multiple images with BGR >150. This requires 10s between peaks (at 30 fps)
            band+=1
            lastimwrite=count
    else:
        # this is a regular image. Do we need to print
        countdown -= 1;
        if countdown == 0:
            savedImages[count]=band
            outputlocation = os.path.sep.join([dest, str(band)])
            if not os.path.exists(outputlocation):
                os.mkdir(outputlocation)
            printAnImage(img, videoFileName, count, outputlocation)
            countdown=args.gap
    
    ret, img = vid.read()
    if args.frames > 1 and count > args.frames:
        ret = False




# now use kmeans to identify the rgb peaks.
peaks, variance = vq.kmeans(numpy.array(allpeaks), band)
peaks.sort()
sys.stderr.write("The peaks for " + videoFileName + " are at " + str(peaks) + "\n")


## process the other files
for fileNo in range(1, len(args.file)):
    sys.stderr.write("Processing " + args.file[fileNo] + "\n")
    vid = cv2.VideoCapture(args.file[fileNo])

    paths = args.file[fileNo].split('/')
    videoFileName = paths[-1]

    ret, img = vid.read()
    average=[]
    count=0
    lastimwrite=0

    myallpeaks = []
    while (ret):
        count+=1
        if (count < args.ignore):
            ret, img = vid.read()
            continue

        ## here we only consider the blue chanel to make things go faster!
        if numpy.average(img[:,:,0]) > 200:
            myallpeaks.append(count)
        ret, img = vid.read()

    mypeaks, variance = vq.kmeans(numpy.array(myallpeaks), peaks)

    mypeaks.sort()
    sys.stderr.write("The peaks for " + videoFileName + " are at " + str(mypeaks) + "\n")

    diff=[]

    for p in mypeaks:
        peakdiff=[]
        for q in peaks:
            peakdiff.append(abs(p-q))
        peakdiff.sort()
        diff.append(peakdiff[0])

    diff.sort()
    mindiff = diff[0]
    maxdiff = diff[-1]
    difference = int(numpy.average(diff))
    sys.stderr.write("The average delay between " + videoFileName + " and " + args.file[0] + " is " + str(difference) + " frames from " + str(mindiff) + " to " + str(maxdiff) + ".\n")


    sys.stderr.write("Running through the second iteration of " + videoFileName)

    vid = cv2.VideoCapture(args.file[fileNo])

    ret, img = vid.read()
    count=0
    while (ret):
        count+=1
        if (count < args.ignore):
            ret, img = vid.read()
            continue
        
        correctedImage = count - difference;
        if correctedImage in savedImages:
            outputlocation = os.path.sep.join([dest, str(savedImages[correctedImage])])
            sys.stderr.write("Saving " + str(correctedImage) + " as we are at " + str(count) + "\n")
            #printAnImage(img, videoFileName, correctedImage, savedImages[correctedImage])
            printAnImage(img, videoFileName, correctedImage, outputlocation)
        ret, img = vid.read()








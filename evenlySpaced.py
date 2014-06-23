''' output a fixed number of images per window '''

# coding: utf-8
import matplotlib
import cv2
matplotlib.use('agg')
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy
import sys
import argparse
import os

parser = argparse.ArgumentParser(description="output a fixed number of images per window")
parser.add_argument('-f', '--file', help='Movie file(s). You can provide more than one video and the first will be used to create the list of random images. Color plots will be made for all images.', required=True, nargs='+')
parser.add_argument('-p', '--peaks', help='Peaks file. This should be one line per movie file with comma separated peaks.', required=True)
parser.add_argument('-i', '--ignore', help='Number of frames at the beginning to ignore. If you want to run in a bit and ignore some frames, use this.', type=int, default=0);
parser.add_argument('-n', '--number', help='Number of frames per window to print out. Default=30', default=30, type=int)

args=parser.parse_args()




def readPeaks(fin):
    firstPeaks = {}
    minpeak = 10000
    minPeakFile = None
    difference = {}
    with open (fin, 'r') as f:
        for data in f:
            data = data.rstrip()
            parts=data.split("\t")
            firstPeaks[parts[0]]=map(int, parts[1].split(','))
            if firstPeaks[parts[0]][0] < minpeak:
                minpeak = firstPeaks[parts[0]][0]
                minPeakFile = parts[0]
    
    # calculate the difference between our peaks
    for p in firstPeaks:
        difference[p] = firstPeaks[p][0] - minpeak


    # now calculate when we should save the file
    # now we have to calculate the spacing between the images that we save
    # for the first image, we go from our burn in to the first peak
    saveat={}
    fpeaks = firstPeaks[minPeakFile]
    gap = ( fpeaks[0] - args.ignore ) / args.number
    save = args.ignore
    band=0

    if save < fpeaks[0]:
        band +=1
        while save < fpeaks[0]:
            save += gap
            saveat[save]=band
    

    for peakfrom in range(1, len(fpeaks)):
        gap = (fpeaks[peakfrom] - save) / (args.number + 1)
        save += gap
        band +=1 
        while save < fpeaks[peakfrom]:
            save += gap
            saveat[save]=band
   
    return saveat, difference

def printAnImage(img, filename, count, loc):
    outfile = str(loc) + os.path.sep + str(count) + "." + filename + ".JPG";
    #sys.stderr.write("Saving " + outfile + "\n")
    cv2.imwrite(outfile, img)





saveat, difference = readPeaks(args.peaks)



dest="EvenlySpaced"
if not os.path.exists(dest):
        os.mkdir(dest)


## process the other files
for f in args.file:
    if f not in difference:
        sys.stderr.write("There were no peaks described for " + f + ". Please add them\n")
        sys.exit(-1)
    sys.stderr.write("Processing " + f + "\n")


    print("The difference for " + f + " is " + str(difference[f]))


    paths = f.split('/')
    videoFileName = paths[-1]

    vid = cv2.VideoCapture(f)
    ret, img = vid.read()
    count=0
    while (ret):
        count+=1
        correctedCount = count + difference[f]
        if correctedCount in saveat:
            outputlocation = os.path.sep.join([dest, str(saveat[correctedCount])])
            if not os.path.exists(outputlocation):
                os.mkdir(outputlocation)
            printAnImage(img, videoFileName, correctedCount, outputlocation)
        ret, img = vid.read()








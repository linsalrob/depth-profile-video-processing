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
parser.add_argument('-e', '--extra', help='Number of extra frames surrounding each image to print out. This number will be divided in two for 1/2 before and 1/2 after Default=0', default=0, type=int)

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
    

    # now calculate when we should save a file
    # now we have to calculate the spacing between the images that we save
    # for the first image, we go from our burn in to the first peak
    saveat={}
    fpeaks = firstPeaks[minPeakFile]
    gap = ( fpeaks[0] - args.ignore ) / args.number
    save = args.ignore
    band=0
    
    # calculate the first band
    if save < fpeaks[0]:
        band +=1
        while save < fpeaks[0]:
            save += gap
            saveat[save]=band

    # calculate the positions from the other bands
    for peakfrom in range(1, len(fpeaks)):
        gap = (fpeaks[peakfrom] - save) / (args.number + 1)
        save += gap
        band +=1 
        while save < fpeaks[peakfrom]:
            save += gap
            saveat[save]=band

    # put the positions to save in order
    orderedsaves = saveat.keys()
    orderedsaves.sort()
    
    ## finally for each video figure out which frames we will save
    tosave={}
    sys.stderr.write("File\tPosition to save\tCorrected Position\tBand\n")
    
    # calculate the difference between our peaks
    for p in firstPeaks:
        difftot=0
        n=0
        for i in range(len(firstPeaks[p])):
           n+=1
           difftot += firstPeaks[p][i] - firstPeaks[minPeakFile][i]
        #difference[p] = firstPeaks[p][0] - minpeak
        difference = int(difftot/n)
        sys.stderr.write("The average difference between " + p + " and  " + minPeakFile + " is " + str(difference) + "\n")

        tosave[p]=[]
        for s in orderedsaves:
            frame=s+difference
            tosave[p].append([s, frame, saveat[s]])
            sys.stderr.write(p + "\t" + str(s) + "\t" + str(frame) + "\t" + str(saveat[s]) + "\n")
   
    return tosave

def printAnImage(img, filename, count, oricount, loc):
    outfile = str(loc) + os.path.sep + str(count) + "." + str(oricount) + "." + filename + ".JPG";
    #sys.stderr.write("Saving " + outfile + "\n")
    cv2.imwrite(outfile, img)





save = readPeaks(args.peaks)



dest="EvenlySpaced"
if not os.path.exists(dest):
        os.mkdir(dest)


## process the other files
for f in args.file:
    if f not in save:
        sys.stderr.write("There were no save locations described for " + f + ". Please add them\n")
        sys.exit(-1)

for f in args.file:
    sys.stderr.write("Processing " + f + "\n")


    paths = f.split('/')
    videoFileName = paths[-1]

    vid = cv2.VideoCapture(f)

    for tple in save[f]:
        count, frame, band = tple

        outputlocation = os.path.sep.join([dest, str(band)])
        if not os.path.exists(outputlocation):
            os.mkdir(outputlocation)
            if args.extra > 0:
                os.mkdir(os.path.sep.join([outputlocation, 'extra_images']))
        
        # jump to the position before this frame
        vid.set(1, frame)
        ret, img = vid.read()
        if not ret:
            sys.stderr.write("Got an error trying to read frame " + str(frame) + " from " + f + "\n")
            continue

        printAnImage(img, videoFileName, count, frame, outputlocation)

        if args.extra > 0:
            start = frame-(args.extra/2)
            vid.set(1, start)
            while start < frame+(args.extra/2):
                ret, img = vid.read()
                start += 1
                if not ret:
                    sys.stderr.write("Got an error trying to read frame " + str(frame) + " from " + f + "\n")
                    continue

                printAnImage(img, videoFileName, count, start, os.path.sep.join([outputlocation, 'extra_images']))


    
    vid.release()








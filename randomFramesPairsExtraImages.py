
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
parser.add_argument('-n', '--number', help='Number of images to print', required=True)
parser.add_argument('-m', '--frames', help='Stop after this number of frames (default == all)', type=int)
parser.add_argument('-d', '--median', help='Calculate and plot the median color intenity instead of the mean color intensity. Note that the median is more noisy and longer to compute than the mean', action='store_true')
parser.add_argument('-w', '--window', help='Window size to average the numbers over (try 1/100 * # images). If not provided the numbers are not averaged. 100 is a good starting point if you are not sure!')
parser.add_argument('-i', '--ignore', help='Number of frames at the beginning to ignore. If you want to run in a bit and ignore some frames, use this.', type=int, default=0);
args = parser.parse_args()

savedImages = {}

def movingAverage(interval, window_size):
    window= numpy.ones(int(window_size))/float(window_size)
    return numpy.convolve(interval, window, 'same')

def plotProfile(plotname, data):
    ''' Plot a profile of the colors'''
    dtc=None
    if args.window:
        dt=numpy.transpose(data)
        for i in range(dt.shape[0]):
            dt[i]=movingAverage(dt[i], args.window)

        dtc=numpy.transpose(dt)
    else:
        dtc=data

    fontP = FontProperties()
    fontP.set_size('small')
    fig = plt.figure()
    ax = plt.subplot(111)
    ax.plot(dtc)
    #ax.set_xticklabels(xlabels, rotation=45, fontproperties=fontP)
    #ax.set_xlabel('Image number in the series')
    ax.set_ylabel('Reef colors')
    box = ax.get_position()
    #ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
    #ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height])
    ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height *0.85])
    header=["blue", "green", "red"]

    ax.legend((header), loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=4, prop=fontP)
    fig.savefig(plotname)


def printImages(filename, imgs, band):
    keys = imgs.keys()

    if len(keys)-1 <= 0:
        sys.stderr.write("No more images to write. skipped\n")
        return

    if not os.path.exists(str(band)):
        os.mkdir(str(band))
    for i in range(int(args.number)):
        r = random.randint(0, len(imgs)-1)
        savedImages[keys[r]] = band
        cv2.imwrite(str(band) + os.path.sep + str(keys[r]) + "." + filename + ".JPG", imgs[keys[r]])
    sys.stderr.write("Saved images from " + str(filename) + " after band " + str(band) + " are: " + " ".join(map (str, savedImages.keys())) + "\n")

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
average=[]
count=0
band=1
allpeaks=[]


imgset = {}
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

    if rgb[0] > 200 or rgb[1] > 200 or rgb[2] > 200:
        sys.stderr.write('Peak at ' + str(count) + " with blue: " + str(rgb[0]) + " green: " + str(rgb[1]) + " red: " + str(rgb[2]) + "\n")
        allpeaks.append(count)
        if count - lastimwrite > 300 and len(imgset.keys()) >= 1: #this is because we may have multiple images with BGR >150. This requires 10s between peaks (at 30 fps)
            sys.stderr.write("Writing images at " + str(count) + "\n")
            printImages(videoFileName, imgset, band)
            band+=1
            lastimwrite=count
        imgset = {}

    rint = random.randint(1, 100)
    if rint == 1: # choose 1:100 images first, and than randomly from those
        imgset[count]=img
    average.append(rgb)
    ret, img = vid.read()
    if args.frames > 1 and count > args.frames:
        ret = False
sys.stderr.write("Read " + str(count) + " images\n")

# finish off the file
allpeaks.append(count)
sys.stderr.write("Writing images at the end of the file\n")
printImages(videoFileName, imgset, band)


# now use kmeans to identify the rgb peaks.
peaks, variance = vq.kmeans(numpy.array(allpeaks), band)
peaks.sort()
sys.stderr.write("The peaks are at " + str(peaks) + "\n")


filename = videoFileName + ".profile.png"
filename.replace('.MP4', '')
sys.stderr.write("Plotting a profile in " + filename + "\n")
plotProfile(filename, average)


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

        rgb=[]
        for i in range(3):
            channel = img[:,:,i]
            if args.median:
                rgb.append(numpy.median(channel))
            else:
                rgb.append(numpy.average(channel))
        average.append(rgb)
        if (count % 1000) < 1:
            sys.stderr.write(videoFileName + " : " + str(count) + ": " + str(rgb[0]) + " " + str(rgb[1]) + " " + str(rgb[2]) + "\n")

        if rgb[0] > 200 or rgb[1] > 200 or rgb[2] > 200:
            sys.stderr.write('Peak at ' + str(count) + " with blue: " + str(rgb[0]) + " green: " + str(rgb[1]) + " red: " + str(rgb[2]) + "\n")
            myallpeaks.append(count)
        ret, img = vid.read()

    # finish off the file
    myallpeaks.append(count)
    sys.stderr.write("Writing images at the end of the file\n")
    printImages(videoFileName, imgset, band)

    ## do we have the same number of peaks
    mypeaks, variance = vq.kmeans(numpy.array(myallpeaks), peaks)

    mypeaks.sort()
    sys.stderr.write("The peaks are at " + str(mypeaks) + "\n")

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

    filename = videoFileName + ".profile.png"
    filename.replace('.MP4', '')
    plotProfile(filename, average)

    sys.stderr.write("Running through the second iteration of " + videoFileName)

    vid = cv2.VideoCapture(args.file[fileNo])

    ret, img = vid.read()
    count=0
    while (ret):
        count+=1
        if (count < args.ignore):
            ret, img = vid.read()
            continue

        for correctedImage in range(count - maxdiff, count - mindiff): 
            if correctedImage in savedImages:
                outputlocation = os.path.sep.join([str(savedImages[correctedImage]), str(correctedImage)])
                if not os.path.exists(outputlocation):
                    os.mkdir(outputlocation)
                sys.stderr.write("Saving " + str(correctedImage) + " as we are at " + str(count) + "\n")
                #printAnImage(img, videoFileName, correctedImage, savedImages[correctedImage])
                printAnImage(img, videoFileName, count, outputlocation)
        ret, img = vid.read()








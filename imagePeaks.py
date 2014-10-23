'''

Identify the peaks in an image, optionally making a plot of the RGB profiles of that image

'''


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
from scipy.cluster import vq

parser = argparse.ArgumentParser(description="Plot the color profiles of movies and figure out where the peaks are")
parser.add_argument('-f', '--file', help='Movie file', required=True)
parser.add_argument('-o', '--out', help='output file name to draw the graph to', required=True)
parser.add_argument('-p', '--peaksFile', help="File to write the peaks to. Note if this file exists we will append to it", required=True)
parser.add_argument('-i', '--image', help='Generate an image of the peaks in the video. If not specified we will just calculate the location of the peaks (faster)', action='store_true')
parser.add_argument('-m', '--frames', help='Stop after this number of frames (default == all)', type=int)
parser.add_argument('-w', '--window', help='Window size to average the numbers over (try 1/100 * # images). If not provided the numbers are not averaged.')
args = parser.parse_args()



def movingaverage(interval, window_size):
    window= numpy.ones(int(window_size))/float(window_size)
    return numpy.convolve(interval, window, 'same')


vid = cv2.VideoCapture(args.file)

ret, img = vid.read()
average  = []
allpeaks = []
count = 0
band  = 1
lastimwrite = 0

imgset = {}
while (ret):
    count+=1
    rgb=[]
    if args.image:
        for i in range(3):
            channel = img[:,:,i]
            rgb.append(numpy.average(channel))
        if (count % 200) < 1:
            sys.stderr.write(str(count) + ": " + str(rgb[0]) + " " + str(rgb[1]) + " " + str(rgb[2]) + "\n")
        average.append(rgb)

    if numpy.average(img[:,:,0]) > 200:
        allpeaks.append(count)
        sys.stderr.write("Peak at " + str(count) + "\n")
        if count - lastimwrite > 600: #this is because we may have multiple images with BGR >150. This requires 10s between peaks (at 30 fps)
            band+=1
            lastimwrite=count
    

    ret, img = vid.read()
    if args.frames > 0 and count > args.frames:
        ret = False

# now use kmeans to identify the rgb peaks.
peaks, variance = vq.kmeans(numpy.array(allpeaks), band)
peaks.sort()
with open(args.peaksFile, 'a') as peaksF:
    peaksF.write(args.file + "\t" + ",".join([str(x) for x in peaks]) + "\n")


if not args.image:
    sys.exit(0)


## plot the images

dtc=None
if args.window:
    dt=numpy.transpose(average)
    for i in range(dt.shape[0]):
        dt[i]=movingaverage(dt[i], args.window)
        
    dtc=numpy.transpose(dt)
else:
    dtc=average

fontP = FontProperties()
fontP.set_size('small')
fig = plt.figure()
ax = plt.subplot(111)
ax.plot(dtc)
ax.set_ylabel('Reef colors')
box = ax.get_position()
ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height *0.85])
header=["blue", "green", "red"]

ax.legend((header), loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=4, prop=fontP)
fig.savefig(args.out)


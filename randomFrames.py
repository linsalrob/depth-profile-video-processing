'''

Generate some random frames from an image, and also plot out the colors

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
import random
import os

parser = argparse.ArgumentParser(description="Plot the color profiles of movies from Gareth's goPros")
parser.add_argument('-f', '--file', help='Movie file', required=True)
parser.add_argument('-o', '--out', help='output file name to draw the graph to', required=True)
parser.add_argument('-n', '--number', help='Number of images to print', required=True)
parser.add_argument('-m', '--frames', help='Stop after this number of frames (default == all)', type=int)
parser.add_argument('-d', '--median', help='Calculate and plot the median color intenity instead of the mean color intensity. Note that the median is more noisy and longer to compute than the mean', action='store_true')
parser.add_argument('-w', '--window', help='Window size to average the numbers over (try 1/100 * # images). If not provided the numbers are not averaged.')
args = parser.parse_args()


def printImages(imgs, band):
    keys = imgs.keys()
    print "Choosing from " + str(len(keys)) + " images"
    if not os.path.exists(str(band)):
        os.mkdir(str(band))
    for i in range(int(args.number)):
        r = random.randint(0, len(imgs)-1)
        print("Wrote the file to: " + str(band) + os.path.sep + str(keys[r]))
        cv2.imwrite(str(band) + os.path.sep + str(keys[r]) + ".JPG", imgs[keys[r]])

def movingaverage(interval, window_size):
    window= numpy.ones(int(window_size))/float(window_size)
    return numpy.convolve(interval, window, 'same')


vid = cv2.VideoCapture(args.file)

ret, img = vid.read()
average=[]
count=0
band=1

imgset = {}
while (ret):
    rgb=[]
    for i in range(3):
        channel = img[:,:,i]
        if args.median:
            rgb.append(numpy.median(channel))
        else:
            rgb.append(numpy.average(channel))
    if (count % 200) < 1:
        sys.stderr.write(str(count) + ": " + str(rgb[0]) + " " + str(rgb[1]) + " " + str(rgb[2]) + "\n")

    if rgb[2] > 150:
        print("Length of the image set is " + str(len(imgset)))
        if len(imgset) > 10: # this is because we may have multiple images with BGR >150
            print("Writing images at " + str(count))
            printImages(imgset, band)
            band+=1
        imgset = {}

    rint = random.randint(1, 100)
    if rint == 1: # choose 1:100 images first, and than randomly from those
        imgset[count]=img
        print("Saving frame: " + str(count) + " rint: " + str(rint))
    average.append(rgb)
    count += 1
    ret, img = vid.read()
    if args.frames > 0 and count > args.frames:
        ret = False

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
#ax.set_xticklabels(xlabels, rotation=45, fontproperties=fontP)
#ax.set_xlabel('Image number in the series')
ax.set_ylabel('Reef colors')
box = ax.get_position()
#ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
#ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height])
ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height *0.85])
header=["blue", "green", "red"]

ax.legend((header), loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=4, prop=fontP)
fig.savefig(args.out)


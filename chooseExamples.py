"""Randomly choose some example images to try the stitching approach"""
 
import os
import shutil
import re

os.mkdir("Examples/")
for i in map(str, range(1, 10)):
    if not os.path.exists(i):
        continue
    os.mkdir(os.path.sep.join(["Examples", i]))
    paths=[]
    files=[]
    for f in os.listdir(i):
        if os.path.isdir(os.path.sep.join([i, f])):
            paths.append(f)
        elif os.path.isfile(os.path.sep.join([i, f])):
            files.append(f)
    for p in paths:
        os.mkdir(os.path.sep.join(["Examples", i, p]))
        for f in files:
            if f.startswith(p):
                print "Copying master file " + os.path.sep.join([i, f]) + " into " + os.path.sep.join(["Examples", i, p, f])
                shutil.copy(os.path.sep.join([i, f]), os.path.sep.join(["Examples", i, p, f]))
        seen={}
        for f in os.listdir(os.path.sep.join([i, p])):
            m=re.search("GoPro\d+", f)
            if not m.group(0) in seen:
                seen[m.group(0)]=1
                shutil.copy(os.path.sep.join([i, p, f]), os.path.sep.join(["Examples", i, p, f]))
                print "Copying " + os.path.sep.join([i, p, f]) + " into " + os.path.sep.join(["Examples", i, p, f])



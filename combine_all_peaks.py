import sklearn.cluster
import numpy as np
data={}
with open("all_peaks_raw_data.tsv", 'r') as inf:
    for l in inf:
        l=l.strip()
        p=l.split("\t")
        data[p[0]]=[int(x) for x in p[1].split(" ")]

alldata = []
for d in data:
    for i in data[d]:
        alldata.append(i)

sdata=np.vstack(alldata)
km=sklearn.cluster.KMeans(n_clusters=22, init='k-means++')
fit=km.fit(sdata)
sd=np.vstack(data['Cam1'])
f=km.fit(sd, fit.cluster_centers_)
with open('peaks.tsv', 'w') as outf:
    for d in data:
        sd=np.vstack(data[d])
        f=km.fit(sd, fit.cluster_centers_)
        a=[]
        for i in f.cluster_centers_:
            a.append(i[0])
        a.sort()
        outf.write(d + "\t" + "\t".join([str(int(x)) for x in a]) + "\n")

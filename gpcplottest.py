# Copyright (c) 2015, Qiurui He
# Department of Engineering, University of Cambridge
"""
Usage:

ipython gpcplotdemo.py
"""

import GPy
import numpy as np
import pods
from gpcplot import GPCPlot as gpcplt

# 1D
data = pods.datasets.toy_linear_1d_classification(seed=500)
X = data['X']
Y = data['Y'][:, 0:1]
Y[Y.flatten() == -1] = 0
m = GPy.models.GPClassification(X, Y)

plotobj = gpcplt.create(m, (r'Toy x',))
plotobj.draw()
plotobj.save('test1d_before')
m.optimize()
plotobj.draw()
plotobj.save('test1d_after')

# 2D
data = pods.datasets.crescent_data(seed=500)
X = data['X']
Y = data['Y']
Y[Y.flatten()==-1] = 0
m = GPy.models.GPClassification(X, Y, kernel=None)

plotobj = gpcplt.create(m, (r'Crescent $x_1$', r'Crescent $x_2$'), usetex=True)
plotobj.draw()
plotobj.save('test2d_before')
m.optimize()
plotobj.draw()
plotobj.save('test2d_after')

# 3D - Iris
data = pods.datasets.iris()
X = data['X']
Y = data['Y']
versi_ind = np.where(Y == 'Iris-versicolor')
virgi_ind = np.where(Y == 'Iris-virginica')
X = np.hstack((X[versi_ind,:], X[virgi_ind,:])).squeeze()
Ynum = np.zeros(Y.size)
Ynum[virgi_ind] = 1
Ynum = np.hstack((Ynum[versi_ind], Ynum[virgi_ind])).reshape(X.shape[0], 1)
m = GPy.models.GPClassification(X[:,0:3], Ynum, kernel=None)

plotobj = gpcplt.create(m, ('SL', 'SW', 'PL'))
plotobj.draw()
plotobj.save('test3d_before')
m.optimize()
plotobj.draw()
plotobj.save('test3d_after')

# 4D - Iris
data = pods.datasets.iris()
X = data['X']
Y = data['Y']
versi_ind = np.where(Y == 'Iris-versicolor')
virgi_ind = np.where(Y == 'Iris-virginica')
X = np.hstack((X[versi_ind,:], X[virgi_ind,:])).squeeze()
Ynum = np.zeros(Y.size)
Ynum[virgi_ind] = 1
Ynum = np.hstack((Ynum[versi_ind], Ynum[virgi_ind])).reshape(X.shape[0], 1)
m = GPy.models.GPClassification(X, Ynum, kernel=None)

plotobj = gpcplt.create(m, ('Sepal length', 'Sepal width', 'Petal length', 'Petal width'), usetex=False)
m.optimize()
plotobj.draw()
plotobj.save('test4d_after')
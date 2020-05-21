import numpy as np
import os
from sktime.transformers.compose import ColumnConcatenator
from sktime.classifiers.compose import TimeSeriesForestClassifier
from sktime.classifiers.dictionary_based.boss import BOSSEnsemble
from sktime.classifiers.compose import ColumnEnsembleClassifier
from sktime.classifiers.shapelet_based import ShapeletTransformClassifier
from sktime.datasets import load_basic_motions
from sktime.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import pandas as pd


def loadData(fileDir1, fileDir2):
    datas = {}
    datas1 = []
    datas2 = []
    y = []
    fileNames = os.listdir(fileDir1)
    for fileName in fileNames:
        filePath = os.path.join(fileDir1,fileName)
        data = np.load(filePath)
        datas1.append(pd.Series(data[0]))
        datas2.append(pd.Series(data[1]))
        y.append(1)
    fileNames = os.listdir(fileDir2)
    for fileName in fileNames:
        filePath = os.path.join(fileDir2, fileName)
        data = np.load(filePath)
        datas1.append(pd.Series(data[0]))
        datas2.append(pd.Series(data[1]))
        y.append(0)
    datas['data1'] = datas1
    datas['data2'] = datas2
    X = pd.DataFrame(data=datas)
    y = np.asarray(y, dtype=np.float32)
    return X,y


X,y = loadData('train-data/miner', 'train-data/else')
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
steps = [
    ('concatenate', ColumnConcatenator()),
    ('classify', TimeSeriesForestClassifier(n_estimators=100))]
print(X_train.shape)
clf = Pipeline(steps)
clf.fit(X_train, y_train)
result = clf.score(X_test, y_test)
print(result)

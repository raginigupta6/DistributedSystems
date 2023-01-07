import numpy as np
import keras
from keras.datasets import mnist
from keras.models import Model
from keras.layers import Dense, Input
from keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten
from keras import backend as k
import numpy as np
import sys
from keras.models import load_model
import pickle
from keras.utils import np_utils
from tensorflow import keras
import matplotlib.pyplot as plt
import pickle
import time
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import keras.losses
import statistics
import numpy as np


filename = "cnn.pkl"
# load the model from disk
#loaded_model = pickle.load(open(filename, 'rb'))
loaded_model=load_model('./my_cnn.h5', compile=False)
loaded_model.compile(optimizer='adam',
              loss=keras.losses.categorical_crossentropy,
              metrics=['accuracy'])
number_batches=30


def main(number_batches_start,number_batches_end,previous):
    while 1:
        previous=time.time()
        procesing_time=[]
        Average=0.0
        STD=0.0
        query_counter=0
        percentile=0.0
        for i in range(int(number_batches_start),int(number_batches_end)):
            #with open("C:/Users/ragin/PycharmProjects/MP4/ABatch_{}.pkl".format(i), "rb") as f:
            #extracted_list_x_y = pickle.load(f)
            extracted_list_x_y=pickle.load(open("ABatch_{}.pkl".format(i), "rb"))
            #print(len(extracted_list_x_y))
            #exit(0)
            #continue
            x_test=extracted_list_x_y[0]
            y_test=extracted_list_x_y[1]
            #exit(0)
            print("read batch number:", i)
            score = loaded_model.evaluate(x_test, y_test, verbose=0)
            print('loss=', score[0])
            print('accuracy=', score[1])
            current_time=time.time()
            procesing_time.append(current_time-previous)
            print("Processing time of current query is: ",procesing_time[-1])
            previous=current_time
            query_counter=query_counter+1
        #time.sleep(2)
        Average= sum(procesing_time) / len(procesing_time)
        STD=statistics.stdev(procesing_time)
        percentile=np.percentile(procesing_time,95)
        print("Average processing time", Average)
        print("Standard Deviation is", STD)
        print("95th Percentile", percentile)
        print('# of Queries', query_counter)
    print("Querying Rate", query_counter/Average)



if __name__ == "__main__":
    previous = time.time()
    main(sys.argv[1], sys.argv[2],previous)

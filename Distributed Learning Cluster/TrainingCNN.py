import numpy as np
import keras
from keras.datasets import mnist
from keras.models import Model
from keras.layers import Dense, Input
from keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten
from keras import backend as k
from keras.utils import np_utils

from keras.models import load_model

import numpy as np
import pickle
from keras.utils import np_utils
from tensorflow import keras
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
(x_train, y_train), (x_test, y_test) = mnist.load_data()
img_rows, img_cols = 28, 28
split=500
x = np.concatenate((x_train, x_test))
y = np.concatenate((y_train, y_test))



# x_train=data[:split,1:]
# x_test=data[split:1:]
#
# y_train=data[:split,0]
# y_test=data[split:,0]
train_size = 0.7
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=train_size, random_state=2019) 
## using 70% training and 30% testing data
number_batches=210   ## Note this is the number of batches to create from the test data, and not the number of batches for the query. 
originial_x_test_size=x_test.shape[0]




#print(x_train.shape)
#print(y_train.shape)

if k.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    inpx = (1, img_rows, img_cols)

else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    inpx = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255


y_train = keras.utils.to_categorical(y_train)
y_test = keras.utils.to_categorical(y_test)
print("#############",x_train.shape)
print("#############",y_train.shape)
print("#############",x_test.shape)
print("#############",y_test.shape)
#


number_batches=50
batch_size=int(originial_x_test_size/number_batches)  ## this ensures that the number of images inside each batch of testData will be 21,000/210 ==> 100 images of batches. And total such batches are 210. Query will be executed on these 210 batches, each of size 100 images. 

#print("x_test", x_test.shape[0])
#print("batch size", batch_size)
#exit(0)
L=[]

for i in range(number_batches):
     batch_1_x=x_test[i*batch_size : (i + 1) * batch_size , : , : ]
     batch_1_y=y_test[i*batch_size : (i + 1) * batch_size]
     #L.append([batch_1_x,batch_1_y])

     #with open("C:/Users/ragin/PycharmProjects/MP4/batch_{}.pkl".format(i), "wb") as f:
     pickle.dump([batch_1_x,batch_1_y],  open("Batches/Batch_{}.pkl".format(i), 'wb'))
     #print(batch_1_x.shape)
     #print(batch_1_y.shape)



inpx = Input(shape=inpx)
layer1 = Conv2D(32, kernel_size=(3, 3), activation='relu')(inpx)
layer2 = Conv2D(64, (3, 3), activation='relu')(layer1)
layer3 = MaxPooling2D(pool_size=(3, 3))(layer2)
layer4 = Dropout(0.5)(layer3)
layer5 = Flatten()(layer4)
layer6 = Dense(250, activation='sigmoid')(layer5)
layer7 = Dense(10, activation='softmax')(layer6)
model = Model([inpx], layer7)
#model.compile(optimizer=keras.optimizers.Adadelta(),
#              loss=keras.losses.categorical_crossentropy,
#              metrics=['accuracy'])
model.compile(optimizer='adam',
              loss=keras.losses.categorical_crossentropy,
              metrics=['accuracy'])



model.fit(x_train, y_train, epochs=12, batch_size=500)

model.save('my_cnn.h5')  # creates a HDF5 file 'my_model.h5'
filename = 'cnn.pkl'
try:

    pickle.dump(model, open(filename, 'wb'))

except Exception as e:
    value = str(e).encode()
    print(value)
# load the model from disk



## Save the test data as follows:

#print(x_test.shape)
#print(x_test.shape[0])

#
#
#
# for i in range(21000):
#     with open("C:/Users/ragin/PycharmProjects/MP4/testImage_{}.pkl".format(i), "wb") as f:
#         pickle.dump(x_test[i], f)
#


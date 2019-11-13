# Make sure that you have all these libaries available to run the code successfully
from pandas_datareader import data
import matplotlib.pyplot as plt
import datetime as dt
import os
import numpy as np
import tensorflow as tf # This code has been tested with TensorFlow 1.6
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

import math
def round_up_to_even(f):
  return math.ceil(f / 2.) * 2

os.chdir("C:/Users/mfrangos/Desktop/2020 Forecast Recurrent Neural Net/data")
#df = pd.read_excel("All_Store_Weekly_Sales.xlsx") #Weekly Data
df = pd.read_excel("C:/Users/mfrangos/Desktop/2020 Forecast Recurrent Neural Net/Data/Daily Data/Daily Data.xlsx")

#Stores brenda wanted
#df = pd.read_excel("2018 Store opening Data.xlsx")
#df = pd.read_excel("2018 Store opening Data.xlsx") #Doesn't exist yet
#df = df.sort_values('Date')

storelist2019 = [318,358,364,366,367,378,382,401,419,428,447]
storelist2018 =  [369, 402, 420,350,354]

select_stores = [349]

 #337,349 363, 379,

#Do 2019 stores
#for store_i in storelist2019:
#  store = store_i

#2018
#for store_i in storelist2018:
 
#Do select stores
for store_i in select_stores:

#for store_i in df.columns[220:]:
  #print(store_i)
  store = store_i
  print("Store: ",store)
  #
  ##Override
  #store = 349
  #len(df)
  
  Store_Sales = df[:-1][store].as_matrix()
  train_data = Store_Sales
  #eliminate nan
  train_data = train_data[~np.isnan(train_data)]
  
  scaler = MinMaxScaler()
  train_data = train_data.reshape(-1,1)
  #test_data = test_data.reshape(-1,1)
  
  
  all_mid_data = train_data
  
  windowPercent = .50
  # Train the Scaler with training data and smooth data
  smoothing_window_size = int(windowPercent*len(train_data))

  #train_data = train_data[:(int(round(len(train_data)/smoothing_window_size)*smoothing_window_size))]
  
  for di in range(0,int((round(len(train_data)/smoothing_window_size)-1)*smoothing_window_size),smoothing_window_size):
      print(di)
      scaler.fit(train_data[di:di+smoothing_window_size,:])
      train_data[di:di+smoothing_window_size,:] = scaler.transform(train_data[di:di+smoothing_window_size,:])
  
  # You normalize the last bit of remaining data
  try:
    scaler.fit(train_data[di+smoothing_window_size:,:]) 
    train_data[di+smoothing_window_size:,:] = scaler.transform(train_data[di+smoothing_window_size:,:])
  except Exception as e:
    print(e,"line 64")
    pass
    

  
  
  class DataGeneratorSeq(object):
  
      def __init__(self,prices,batch_size,num_unroll):
          self._prices = prices
          self._prices_length = len(self._prices) - num_unroll
          self._batch_size = batch_size
          self._num_unroll = num_unroll
          self._segments = self._prices_length // self._batch_size
          self._cursor = [offset * self._segments for offset in range(self._batch_size)]
  
      def next_batch(self):
  
          batch_data = np.zeros((self._batch_size),dtype=np.float32)
          batch_labels = np.zeros((self._batch_size),dtype=np.float32)
          
          for b in range(self._batch_size):
              #print("batch: ",b)
              if self._cursor[b]+1>=self._prices_length:
                  #print("Line 88 is good")
                  #self._cursor[b] = b * self._segments
                  self._cursor[b] = np.random.randint(0,(b+1)*self._segments)
                  #print("Line 91 is good")
  
              batch_data[b] = self._prices[self._cursor[b]]
              #print("Line 94 is good")
              batch_labels[b]= self._prices[self._cursor[b]+np.random.randint(0,5)]
              #print("Line 96 is good")
  
              self._cursor[b] = (self._cursor[b]+1)%self._prices_length
              #print("Line 99 is good")
  
          return batch_data,batch_labels
  
      def unroll_batches(self):
  
          unroll_data,unroll_labels = [],[]
          init_data, init_label = None,None
          for ui in range(self._num_unroll):
              
              try:
                data, labels = self.next_batch()    
    
                unroll_data.append(data)
                unroll_labels.append(labels)
              except Exception as e:
                print(e, "line 109")
                pass
  
          return unroll_data, unroll_labels
  
      def reset_indices(self):
          for zz in range(self._batch_size):
              self._cursor[zz] = np.random.randint(0,min((zz+1)*self._segments,self._prices_length-1))
  
  
  
  dg = DataGeneratorSeq(train_data,5,5)
  u_data, u_labels = dg.unroll_batches()
  
  for ui,(dat,lbl) in enumerate(zip(u_data,u_labels)):   
      print('\n\nUnrolled index %d'%ui)
      dat_ind = dat
      lbl_ind = lbl
      print('\tInputs: ',dat )
      print('\n\tOutput:',lbl)
  
  
  
  D = 1 # Dimensionality of the data. Since your data is 1-D this would be 1
  num_unrollings = 26 # Number of time steps you look into the future in weeks. This must be smaller if your dataset is smaller, or it won't train.
  batch_size = round_up_to_even(int((20/82)*len(train_data))) # Number of samples in a batch
  num_nodes = [400,400,150] # Number of hidden nodes in each layer of the deep LSTM stack we're using
  n_layers = len(num_nodes) # number of layers
  dropout = 0.2 # dropout amount
  
  tf.reset_default_graph() # This is important in case you run this multiple times
  
  print(batch_size)
  # Input data.
  train_inputs, train_outputs = [],[]
  
  # You unroll the input over time defining placeholders for each time step
  for ui in range(num_unrollings):
      train_inputs.append(tf.placeholder(tf.float32, shape=[batch_size,D],name='train_inputs_%d'%ui))
      train_outputs.append(tf.placeholder(tf.float32, shape=[batch_size,1], name = 'train_outputs_%d'%ui))
  
  
  
  
  lstm_cells = [
      tf.contrib.rnn.LSTMCell(num_units=num_nodes[li],
                              state_is_tuple=True,
                              initializer= tf.contrib.layers.xavier_initializer()
                             )
   for li in range(n_layers)]
  
  drop_lstm_cells = [tf.contrib.rnn.DropoutWrapper(
      lstm, input_keep_prob=1.0,output_keep_prob=1.0-dropout, state_keep_prob=1.0-dropout
  ) for lstm in lstm_cells]
  drop_multi_cell = tf.contrib.rnn.MultiRNNCell(drop_lstm_cells)
  multi_cell = tf.contrib.rnn.MultiRNNCell(lstm_cells)
  
  w = tf.get_variable('w',shape=[num_nodes[-1], 1], initializer=tf.contrib.layers.xavier_initializer())
  b = tf.get_variable('b',initializer=tf.random_uniform([1],-0.1,0.1))
  
  
  
  
  
  
  
  
  
  # Create cell state and hidden state variables to maintain the state of the LSTM
  c, h = [],[]
  initial_state = []
  for li in range(n_layers):
    c.append(tf.Variable(tf.zeros([batch_size, num_nodes[li]]), trainable=False))
    h.append(tf.Variable(tf.zeros([batch_size, num_nodes[li]]), trainable=False))
    initial_state.append(tf.contrib.rnn.LSTMStateTuple(c[li], h[li]))
  
  # Do several tensor transofmations, because the function dynamic_rnn requires the output to be of
  # a specific format. Read more at: https://www.tensorflow.org/api_docs/python/tf/nn/dynamic_rnn
  all_inputs = tf.concat([tf.expand_dims(t,0) for t in train_inputs],axis=0)
  
  # all_outputs is [seq_length, batch_size, num_nodes]
  all_lstm_outputs, state = tf.nn.dynamic_rnn(
      drop_multi_cell, all_inputs, initial_state=tuple(initial_state),
      time_major = True, dtype=tf.float32)
  
  all_lstm_outputs = tf.reshape(all_lstm_outputs, [batch_size*num_unrollings,num_nodes[-1]])
  
  all_outputs = tf.nn.xw_plus_b(all_lstm_outputs,w,b)
  
  split_outputs = tf.split(all_outputs,num_unrollings,axis=0)
  
  
  
  
  #CALCULATE LOSS
  # When calculating the loss you need to be careful about the exact form, because you calculate
  # loss of all the unrolled steps at the same time
  # Therefore, take the mean error or each batch and get the sum of that over all the unrolled steps
  
  print('Defining training Loss')
  loss = 0.0
  with tf.control_dependencies([tf.assign(c[li], state[li][0]) for li in range(n_layers)]+
                               [tf.assign(h[li], state[li][1]) for li in range(n_layers)]):
    for ui in range(num_unrollings):
      loss += tf.reduce_mean(0.5*(split_outputs[ui]-train_outputs[ui])**2)
  
  print('Learning rate decay operations')
  global_step = tf.Variable(0, trainable=False)
  inc_gstep = tf.assign(global_step,global_step + 1)
  tf_learning_rate = tf.placeholder(shape=None,dtype=tf.float32)
  tf_min_learning_rate = tf.placeholder(shape=None,dtype=tf.float32)
  
  learning_rate = tf.maximum(
      tf.train.exponential_decay(tf_learning_rate, global_step, decay_steps=1, decay_rate=0.5, staircase=True),
      tf_min_learning_rate)
  
  # Optimizer.
  print('TF Optimization operations')
  optimizer = tf.train.AdamOptimizer(learning_rate)
  gradients, v = zip(*optimizer.compute_gradients(loss))
  gradients, _ = tf.clip_by_global_norm(gradients, 5.0)
  optimizer = optimizer.apply_gradients(
      zip(gradients, v))
  
  print('\tAll done')
  
  
  
  
  
  
  
  
  
  
  print('Defining prediction related TF functions')
  
  sample_inputs = tf.placeholder(tf.float32, shape=[1,D])
  
  # Maintaining LSTM state for prediction stage
  sample_c, sample_h, initial_sample_state = [],[],[]
  for li in range(n_layers):
    sample_c.append(tf.Variable(tf.zeros([1, num_nodes[li]]), trainable=False))
    sample_h.append(tf.Variable(tf.zeros([1, num_nodes[li]]), trainable=False))
    initial_sample_state.append(tf.contrib.rnn.LSTMStateTuple(sample_c[li],sample_h[li]))
  
  reset_sample_states = tf.group(*[tf.assign(sample_c[li],tf.zeros([1, num_nodes[li]])) for li in range(n_layers)],
                                 *[tf.assign(sample_h[li],tf.zeros([1, num_nodes[li]])) for li in range(n_layers)])
  
  sample_outputs, sample_state = tf.nn.dynamic_rnn(multi_cell, tf.expand_dims(sample_inputs,0),
                                     initial_state=tuple(initial_sample_state),
                                     time_major = True,
                                     dtype=tf.float32)
  
  with tf.control_dependencies([tf.assign(sample_c[li],sample_state[li][0]) for li in range(n_layers)]+
                                [tf.assign(sample_h[li],sample_state[li][1]) for li in range(n_layers)]):  
    sample_prediction = tf.nn.xw_plus_b(tf.reshape(sample_outputs,[1,-1]), w, b)
  
  print('\tAll done')
  
  
  
  
  
  
  #TRAIN THE NET
  epochs = 50
  valid_summary = 1 # Interval you make test predictions
  
  n_predict_once = 1095 # Number of steps you continously predict for. #Number of predictions
  
  train_seq_length = train_data.size # Full length of the training data
  
  train_mse_ot = [] # Accumulate Train losses
  test_mse_ot = [] # Accumulate Test loss
  predictions_over_time = [] # Accumulate predictions
  
  session = tf.InteractiveSession()
  
  tf.global_variables_initializer().run()
  
  # Used for decaying learning rate
  loss_nondecrease_count = 0
  loss_nondecrease_threshold = 2 # If the test error hasn't increased in this many steps, decrease learning rate
  
  print('Initialized')
  average_loss = 0
  

  
  
  # Define data generator
  data_gen = DataGeneratorSeq(train_data,batch_size,num_unrollings) #Unrolling is # of datapoints to predict. Batch size must be even?
  
  x_axis_seq = []
  
  # Points you start your test predictions from
  test_points_seq = np.arange(int(.8*len(train_data)),int(len(train_data)),1).tolist()
  
  for ep in range(epochs):       
  
      # ========================= Training =====================================
      for step in range(train_seq_length//batch_size):
  
          u_data, u_labels = data_gen.unroll_batches() #ERROR?
  
          feed_dict = {}
          for ui,(dat,lbl) in enumerate(zip(u_data,u_labels)):            
              feed_dict[train_inputs[ui]] = dat.reshape(-1,1)
              feed_dict[train_outputs[ui]] = lbl.reshape(-1,1)
  
          feed_dict.update({tf_learning_rate: 0.0001, tf_min_learning_rate:0.000001})
          
          try:
            _, l = session.run([optimizer, loss], feed_dict=feed_dict)
            average_loss += l
          except Exception as e:
            print(e, "line 326")
            pass
  
      # ============================ Validation ==============================
      if (ep+1) % valid_summary == 0:
  
        average_loss = average_loss/(valid_summary*(train_seq_length//batch_size))
  
        # The average loss
        if (ep+1)%valid_summary==0:
          print('Average loss at step %d: %f' % (ep+1, average_loss))
          
          
#        track_average_loss = []
#        track_average_loss.append(average_loss)
#        lowest_loss_epoch = 
          
        train_mse_ot.append(average_loss)
  
        average_loss = 0 # reset loss
  
        predictions_seq = []
  
        mse_test_loss_seq = []
  
        # ===================== Updating State and Making Predicitons ========================
        for w_i in test_points_seq:
          mse_test_loss = 0.0
          our_predictions = []
  
          if (ep+1)-valid_summary==0:
            # Only calculate x_axis values in the first validation epoch
            x_axis=[]
  
          # Feed in the recent past behavior of stock prices
          # to make predictions from that point onwards
          for tr_i in range(w_i-num_unrollings+1,w_i-1):
            current_price = all_mid_data[tr_i]
            feed_dict[sample_inputs] = np.array(current_price).reshape(1,1)    
            _ = session.run(sample_prediction,feed_dict=feed_dict)
  
          feed_dict = {}
  
          current_price = all_mid_data[w_i]
  
          feed_dict[sample_inputs] = np.array(current_price).reshape(1,1)
  
          # Make predictions for this many steps
          # Each prediction uses previous prediciton as it's current input
          for pred_i in range(n_predict_once):
  
            pred = session.run(sample_prediction,feed_dict=feed_dict)
  
            our_predictions.append(np.asscalar(pred))
  
            feed_dict[sample_inputs] = np.asarray(pred).reshape(-1,1)
  
            if (ep+1)-valid_summary==0:
              # Only calculate x_axis values in the first validation epoch
              x_axis.append(w_i+pred_i)
  
            #mse_test_loss += 0.5*(pred-all_mid_data[w_i+pred_i])**2
  
          session.run(reset_sample_states)
  
          predictions_seq.append(np.array(our_predictions))
  
  #        mse_test_loss /= n_predict_once
  #        mse_test_loss_seq.append(mse_test_loss)
  
          if (ep+1)-valid_summary==0:
            x_axis_seq.append(x_axis)
  
        #current_test_mse = np.mean(mse_test_loss_seq)
  
        # Learning rate decay logic
  #      if len(test_mse_ot)>0 and current_test_mse > min(test_mse_ot):
  #          loss_nondecrease_count += 1
  #      else:
  #          loss_nondecrease_count = 0
  
        if loss_nondecrease_count > loss_nondecrease_threshold :
              session.run(inc_gstep)
              loss_nondecrease_count = 0
              print('\tDecreasing learning rate by 0.5')
  
  #      test_mse_ot.append(current_test_mse)
  #      print('\tTest MSE: %.5f'%np.mean(`_seq))
        predictions_over_time.append(predictions_seq)
        print('\tFinished Predictions')
  
  
  
  
  
  
  
  
  
  
  
  #plot predictions
  best_prediction_epoch = 39 # replace this with the epoch that you got the best results when running the plotting code
  
  plt.figure(figsize = (18,18))
  plt.subplot(2,1,1)
  plt.plot(range(train_data.shape[0]),all_mid_data,color='b')
  
  # Plotting how the predictions change over time
  # Plot older predictions with low alpha and newer predictions with high alpha
  start_alpha = 0.25
  alpha  = np.arange(start_alpha,1.1,(1.0-start_alpha)/len(predictions_over_time[::3]))
  for p_i,p in enumerate(predictions_over_time[::3]):
      for xval,yval in zip(x_axis_seq,p):
          plt.plot(xval,yval,color='r',alpha=alpha[p_i])
  
  plt.title('Evolution of Test Predictions Over Time',fontsize=18)
  plt.xlabel('Date',fontsize=18)
  plt.ylabel('Store Sales',fontsize=18)
  plt.xlim(0,len(train_data+100))
  
  plt.subplot(2,1,2)
  
  # Predicting the best test prediction you got
  plt.plot(range(train_data.shape[0]),all_mid_data,color='b')
  for xval,yval in zip(x_axis_seq,predictions_over_time[best_prediction_epoch]):
      plt.plot(xval,yval,color='r')
  
  plt.title('Best Test Predictions Over Time',fontsize=18)
  plt.xlabel('Date',fontsize=18)
  plt.ylabel('Store Sales',fontsize=18)
  plt.xlim(0,len(train_data+100))
  plt.savefig(f"{store}")
  plt.show()
  
  
  #How to unscale the data back to original form
  scaler.inverse_transform(all_mid_data)
  
  
  #i = 0
  ##Print several predictions
  #while i<len(predictions_over_time):
  #  print(scaler.inverse_transform(predictions_over_time[i]))
  #  plt.plot(scaler.inverse_transform(predictions_over_time[i]))
  
  #Show last prediction
  print(scaler.inverse_transform(predictions_over_time[-1]))
  
  
  #Exports the final prediction
  export_prediction = pd.DataFrame(scaler.inverse_transform(predictions_over_time[-1])).T
  
  export_prediction.to_excel(f"Store {store}.xlsx")
  

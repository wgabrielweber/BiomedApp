import tensorflow as tf
import numpy as np
import pandas as pd
import math
from datetime import datetime
from scipy.signal import cheby2, filtfilt
from scipy.interpolate import interp1d

# Read the data from the .txt file
data_file = 'new_measure.txt'
with open(data_file, 'r') as file:
    data = file.readlines()

# Extract values from each line
values = []
for line_num, line in enumerate(data, start=1):
    line = line.strip()
    if line:  # This check ensures that the line is not empty
        try:
            value = int(line)
            values.append(value)
        except ValueError:
            print(f"Error parsing line {line_num}: {line}")

# Convert values to a numpy array
ppg_signal = np.array(values)* -1

# 4th order Chebyshev-II bandpass filter
num_values = len(ppg_signal)
fs = num_values / 10
lowcut = 0.5
highcut = 8.0
nyquist = 0.5 * fs
low = lowcut / nyquist
high = highcut / nyquist

b, a = cheby2(4, 40, [low, high], btype='bandpass')

# Apply the filter to the PPG signal
filtered_signal = filtfilt(b, a, ppg_signal)

# Interpolate the signal to a specific number of values
desired_num_values = 1250  # Expected number of values
x = np.linspace(0, 1, num=len(filtered_signal))  # Normalized time axis
x_new = np.linspace(0, 1, num=desired_num_values)  # New normalized time axis
f = interp1d(x, filtered_signal, kind='cubic')  # Cubic interpolation
interpolated_signal = f(x_new)

# Scale the filtered signal between 0 and 1
scaled_signal = (interpolated_signal - np.min(interpolated_signal)) / (np.max(interpolated_signal) - np.min(interpolated_signal))

# Prepare the data for the model
scaled_signal = np.array(scaled_signal, dtype=np.float32)
data = tf.reshape(scaled_signal, [1, -1, 1])

# Load the model using tf.saved_model.load
model_path = 'C:/Users/wgabr/Python Codes/BiomedApp/model_new'
model = tf.saved_model.load(model_path)

# Prepare the input as a tensor
input_tensor = tf.convert_to_tensor(data, dtype=tf.float32)

# Assuming the model has a default serving signature
infer = model.signatures['serving_default']

# Make prediction
prediction = infer(input_tensor)

# Extract prediction result from the tensor
predictions = [pred.numpy()[0][0] for pred in prediction.values()]

# Convert prediction to systolic and diastolic pressure
systolic_pressure = math.exp(predictions[1])
diastolic_pressure = math.exp(predictions[0])

systolic_pressure = f"{float(systolic_pressure):.3f}"
diastolic_pressure = f"{float(diastolic_pressure):.3f}"

# Print the predictions
print(f'\nSystolic Pressure: {systolic_pressure}\nDiastolic Pressure: {diastolic_pressure}')

# Create the new measurement dictionary
new_measurement = {
    'Date_of_Measurement': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'Systolic_Pressure': systolic_pressure,
    'Diastolic_Pressure': diastolic_pressure,
}

# Convert to DataFrame and save to CSV
df = pd.DataFrame([new_measurement])
df.to_csv("new_measure.csv", index=False)
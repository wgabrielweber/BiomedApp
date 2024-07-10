import tensorflow as tf
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.signal import cheby2, filtfilt
from scipy.interpolate import interp1d

# Function to process and predict for a single measure
def process_and_predict(timestamp, values):
    ppg_signal = np.array(values) * -1

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

    # Prepare the input as a tensor
    input_tensor = tf.convert_to_tensor(data, dtype=tf.float32)

    # Make prediction
    prediction = infer(input_tensor)

    # Extract prediction result from the tensor
    predictions = [pred.numpy()[0][0] for pred in prediction.values()]

    # Convert prediction to systolic and diastolic pressure with three decimal places
    systolic_pressure = f"{float(predictions[0]):.3f}"
    diastolic_pressure = f"{float(predictions[1]):.3f}"

    return "", timestamp, systolic_pressure, diastolic_pressure

# Read the data from the .txt file
data_file = 'requested_measures.txt'
with open(data_file, 'r') as file:
    data = file.readlines()

# Load the model using tf.saved_model.load
model_path = 'C:/Users/wgabr/Python Codes/BiomedApp/model'
model = tf.saved_model.load(model_path)

# Assuming the model has a default serving signature
infer = model.signatures['serving_default']

# Process each line and predict
results = []
for line in data:
    try:
        line = line.strip().strip('()')  # Remove leading and trailing parentheses
        timestamp_str, values_str = line.split(', ', 1)
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        values = eval(values_str)
        results.append(process_and_predict(timestamp, values))
    except Exception as e:
        print(f"Error processing line: {line}")
        print(e)

# Create a DataFrame from the results
df = pd.DataFrame(results, columns=['Name', 'Date_of_Measurement', 'Systolic_Pressure', 'Diastolic_Pressure'])
df['Name'] = df['Name'].astype(str)

# Append the DataFrame to the CSV file
df.to_csv("requested_measures.csv", mode='a', index=False, header=False)

# Clear the contents of the .txt file
with open(data_file, 'w') as file:
    file.write("")
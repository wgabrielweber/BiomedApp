import pandas as pd
from faker import Faker
import random

# Initialize Faker to generate synthetic names and dates
fake = Faker()

# Parameters for synthetic data generation
num_patients = 15

# Generate synthetic data
data = []

for patient_id in range(1, num_patients + 1):
    name = fake.name()
    num_measurements = random.randint(5, 15)
    for _ in range(num_measurements):
        date_of_measurement = fake.date_time_between(start_date='-1y', end_date='now')
        diastolic_pressure = random.randint(40, 120)
        systolic_pressure = diastolic_pressure + random.randint(35, 65)
        data.append([patient_id, name, date_of_measurement, systolic_pressure, diastolic_pressure])

# Create DataFrame
columns = ['Id', 'Name', 'Date_of_Measurement', 'Systolic_Pressure', 'Diastolic_Pressure']
df = pd.DataFrame(data, columns=columns)

# Save to CSV
csv_file = "data.csv"
df.to_csv(csv_file, index=False)

print(f"Synthetic data saved to {csv_file}")

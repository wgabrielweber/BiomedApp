import os
import pandas as pd
import streamlit as st
import altair as alt
import random
import subprocess
import sys
from datetime import datetime
from time import sleep

def check_device_connection():
    # Simulate device connection status
    return random.choice([True, False])

# Set page configuration
st.set_page_config(
    page_title="Medical Clinic App",
    page_icon="🩺",
    layout="wide",  # Set layout to wide
)

# Load data from CSV file
def load_data(file_path):
    return pd.read_csv(file_path)

# Write data to CSV file
def write_to_csv(file_path, measurement):
    if os.path.exists(file_path):
        data = pd.read_csv(file_path)
    else:
        data = pd.DataFrame(columns=['Id', 'Name', 'Date_of_Measurement', 'Systolic_Pressure', 'Diastolic_Pressure'])
    data = data._append(measurement, ignore_index=True)
    data.to_csv(file_path, index=False)

# Define blood pressure categories and color scheme
BP_CATEGORIES = {'Low': {'min_systolic': 0, 'max_systolic': 90, 'min_diastolic': 0, 'max_diastolic': 60},
                  'Normal': {'min_systolic': 90, 'max_systolic': 120, 'min_diastolic': 60, 'max_diastolic': 80},
                  'High': {'min_systolic': 120, 'max_systolic': float('inf'), 'min_diastolic': 80, 'max_diastolic': float('inf')}}
COLOR_SCHEME = {'Low': '#CAF4FF', 'Normal': '#5AB2FF', 'High': '#FF8080'}

# Function to generate a new measurement
def get_new_measurement(name, data):
    # Get the existing ID for the given name or assign a new ID if the name is not found
    if name in data['Name'].values:
        patient_id = data[data['Name'] == name]['Id'].iloc[0]
    else:
        patient_id = data['Id'].max() + 1
    
    # Run the BLE communication script
    subprocess.run([sys.executable, "ble_manager.py"])

    # Load the result from the CSV file
    df_result = pd.read_csv("result_measurement.csv")

    # Create a new measurement record
    new_measurement = {
        'Id': patient_id,
        'Name': name,
        'Date_of_Measurement': df_result['Date_of_Measurement'][0],
        'Systolic_Pressure': df_result['Systolic_Pressure'][0],
        'Diastolic_Pressure': df_result['Diastolic_Pressure'][0],
    }

    return new_measurement

def get_column_config(config_type):
    if config_type == 1:
        return {
            "Name": st.column_config.Column(
                "Nome",
                width=None,
                required=True,
            ),
            "Date_of_Measurement": st.column_config.Column(
                "Data de Medição",
                width=None,
                required=True,
            ),
            "Diastolic_Pressure": st.column_config.Column(
                "Pressão Diastólica",
                width=None,
                required=True,
            ),
            "Systolic_Pressure": st.column_config.Column(
                "Pressão Sistólica",
                width=None,
                required=True,
            )
        }
    elif config_type == 2:
        return {
            "Date_of_Measurement": st.column_config.Column(
                "Measurement Date",
                width=None,
                required=True,
            ),
            "Diastolic_Pressure": st.column_config.Column(
                "Diastolic BP",
                width=None,
                required=True,
            ),
            "Systolic_Pressure": st.column_config.Column(
                "Systolic BP",
                width=None,
                required=True,
            )
        }
    else:
        return {}

# Categorize blood pressure readings
def categorize_blood_pressure(systolic, diastolic):
    for category, thresholds in BP_CATEGORIES.items():
        if thresholds['min_systolic'] <= systolic <= thresholds['max_systolic'] and thresholds['min_diastolic'] <= diastolic <= thresholds['max_diastolic']:
            return category
    return 'Unknown'

# Create a bar chart for blood pressure categories
def create_bp_bar_chart(data, title):
    # Filter the data based on the selected patient
    BP_categories = data.copy()  # Make a copy to avoid the SettingWithCopyWarning

    # Categorize blood pressure readings
    BP_categories['BP_Category'] = BP_categories.apply(
        lambda row: categorize_blood_pressure(row['Systolic_Pressure'], row['Diastolic_Pressure']), axis=1)

    # Count the occurrences of each category
    category_counts = BP_categories['BP_Category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']

    bar_chart = alt.Chart(category_counts).mark_bar().encode(
        x=alt.X('Category', sort=['Low', 'Normal', 'High']),
        y='Count',
        color=alt.Color('Category', scale=alt.Scale(domain=['Low', 'Normal', 'High'], range=[COLOR_SCHEME['Low'], COLOR_SCHEME['Normal'], COLOR_SCHEME['High']])),
    ).properties(
        title=title
    )
    return bar_chart

def general_screen(data):
    st.title('All Patients Data')
    st.write("Patient Data:")

    col1, col2 = st.columns(spec=[0.6,0.4])

    with col1:
        data = load_data("data.csv")  # Reload data to ensure we're appending to the latest version
        data_general = data.drop(columns=['Id']).reset_index(drop=True)

        st.data_editor(
            data_general,
            column_config=get_column_config(1),
            hide_index=True,
        )

    with col2:
        with st.popover("Novo Paciente"):
            patient_name = st.text_input("Insira o Nome do Paciente")

        #st.text_input(label="", placeholder="Enter your Query here:" ,disabled=True,label_visibility="collapsed")

        st.write("Nome do Paciente:", patient_name)

        # Button to generate a new measurement 
        if st.button("Nova Medição"):
            if patient_name:
                data = load_data("data.csv")  # Reload data to ensure we're appending to the latest version
                new_measurement = get_new_measurement(patient_name, data)
                # Append the new measurement to the dataframe
                data = data._append(new_measurement, ignore_index=True)
                # Save the updated dataframe to the CSV file
                data.to_csv("data.csv", index=False)
                st.success("New measurement added successfully!")
                sleep(1.5)
                st.rerun()  # Reload the file to update the dataframe
            else:
                st.error("Please enter a patient name.")

    st.subheader("Medições de pressão categorizadas")

    st.altair_chart(create_bp_bar_chart(data_general, "Bar chart for all measurements"), use_container_width=True)

def patient_screen(data):
    
    st.title('Informações Individuais dos Pacientes')
    
    data = load_data("data.csv")  # Reload data to ensure we're appending to the latest version
    patients = sorted(data['Name'].unique().tolist())
    selected_patient = st.selectbox("Selecione o Paciente", patients)
    filtered_data = data[data['Name'] == selected_patient]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Medições para o paciente: {selected_patient}:")

        # Display the pivoted data as a table
        st.data_editor(
            filtered_data.pivot_table(index='Date_of_Measurement', values=['Systolic_Pressure', 'Diastolic_Pressure'], aggfunc='first'),
            column_config=get_column_config(2),
            hide_index=True,
        )
    with col2:
        st.altair_chart(create_bp_bar_chart(data[data['Name'] == selected_patient], f"Blood Pressure Categories for {selected_patient}"), use_container_width=True)

def main():
    # Load data from CSV
    csv_file = "data.csv"  # Update with your CSV file path
    data = st.cache_data(load_data)(csv_file)

    # Add a sidebar menu for selecting the table to display
    menu_selection = st.sidebar.selectbox("Menu", ("Informações Gerais", "Informações Individuais"))

    if menu_selection == "Informações Gerais":
        general_screen(data)
    elif menu_selection == "Informações Individuais":
        patient_screen(data)

    # Check device connection status
    device_connected = check_device_connection()
    if device_connected:
        st.sidebar.success("Device is connected.", icon=":material/check:")
    else:
        st.sidebar.error("Device is not connected.", icon=":material/cancel:")

if __name__ == '__main__':
    main()
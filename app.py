import os
import pandas as pd
import streamlit as st
import altair as alt
import random
import subprocess
import sys
from datetime import datetime, timedelta
from time import sleep

# Function to communicate with BLE device
def ble_new_measure():
    subprocess.run([sys.executable, "ble_new_measure.py"])
    subprocess.run([sys.executable, "bp_new_predict.py"])
    df_result = pd.read_csv("new_measure.csv")
    return df_result

def ble_request_measures():
    subprocess.run([sys.executable, "ble_request_measures.py"])
    subprocess.run([sys.executable, "bp_request_predicts.py"])
    df_requested_measures = pd.read_csv("requested_measures.csv")
    df_requested_measures['Name'] = df_requested_measures['Name'].astype(str)
    return df_requested_measures

# Set page configuration
st.set_page_config(
    page_title="Central de Medições",
    page_icon="🩺",
    layout="wide",  # Set layout to wide
)

# Load data from CSV file
def load_data(file_path):
    return pd.read_csv(file_path)

# Save data to CSV
def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Write data to CSV file
def write_to_csv(file_path, measurement):
    if os.path.exists(file_path):
        data = pd.read_csv(file_path)
    else:
        data = pd.DataFrame(columns=['Id', 'Name', 'Date_of_Measurement', 'Systolic_Pressure', 'Diastolic_Pressure'])
    data = data._append(measurement, ignore_index=True)
    data.to_csv(file_path, index=False)

# Define blood pressure categories and color scheme
BP_CATEGORIES = {'Baixa': {'min_systolic': 0, 'max_systolic': 100, 'min_diastolic': 0, 'max_diastolic': 90},
                  'Normal': {'min_systolic': 90, 'max_systolic': 120, 'min_diastolic': 70, 'max_diastolic': 80},
                  'Alta': {'min_systolic': 130, 'max_systolic': float('inf'), 'min_diastolic': 90, 'max_diastolic': float('inf')}}
COLOR_SCHEME = {'Baixa': '#CAF4FF', 'Normal': '#5AB2FF', 'Alta': '#FF8080'}

# Function to generate a new measurement
def get_new_measurement(name, data):
    # Get the existing ID for the given name or assign a new ID if the name is not found
    if name in data['Name'].values:
        patient_id = data[data['Name'] == name]['Id'].iloc[0]
    else:
        patient_id = data['Id'].max() + 1
    
    # Run the BLE communication script
    df_result = ble_new_measure()

    # Create a new measurement record
    new_measurement = {
        'Id': patient_id,
        'Name': name,
        'Date_of_Measurement': df_result['Date_of_Measurement'][0],
        'Systolic_Pressure': df_result['Systolic_Pressure'][0],
        'Diastolic_Pressure': df_result['Diastolic_Pressure'][0],
    }
    return new_measurement

def append_measurements():
    # Load the full dataset
    data_df = load_data("data.csv")
    processed_measures_df = load_data("processed_measures.csv")

    # Ensure 'Name' column is treated as strings
    data_df['Name'] = data_df['Name'].astype(str)
    processed_measures_df['Name'] = processed_measures_df['Name'].astype(str)

    # Create a dictionary to map names to IDs
    name_to_id = dict(zip(data_df['Name'], data_df['Id']))

    # Find the highest existing ID
    if not data_df.empty:
        highest_id = data_df['Id'].max()
    else:
        highest_id = 0

    # Assign IDs to the processed measures
    new_ids = []
    for name in processed_measures_df['Name']:
        if name in name_to_id:
            new_ids.append(name_to_id[name])
        else:
            highest_id += 1
            name_to_id[name] = highest_id
            new_ids.append(highest_id)

    # Create a DataFrame with IDs and other columns from processed measures
    processed_with_ids_df = processed_measures_df.copy()
    processed_with_ids_df['Id'] = new_ids

    # Append the processed measures to the main data DataFrame
    data_df = data_df._append(processed_with_ids_df, ignore_index=True)
    
    # Save the updated data DataFrame
    save_data(data_df, "data.csv")

    # Clear the processed measures file
    processed_measures_df = processed_measures_df.iloc[0:0]
    processed_measures_df.to_csv("processed_measures.csv", index=False, header=True)

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
    category_counts.columns = ['Categoria', 'Número de Medições']

    bar_chart = alt.Chart(category_counts).mark_bar().encode(
        x=alt.X('Categoria', sort=['Baixa', 'Normal', 'Alta']),
        y='Número de Medições',
        color=alt.Color('Categoria', scale=alt.Scale(domain=['Baixa', 'Normal', 'Alta'], range=[COLOR_SCHEME['Baixa'], COLOR_SCHEME['Normal'], COLOR_SCHEME['Alta']])),
    ).properties(
        title=title
    )
    return bar_chart

def create_bp_history_chart(data, title, period):
    # Convert Date_of_Measurement to datetime if not already
    if data['Date_of_Measurement'].dtype == 'object':
        data['Date_of_Measurement'] = pd.to_datetime(data['Date_of_Measurement'])

    # Create a line chart for systolic and diastolic pressure
    chart = alt.Chart(data).mark_circle(color='red').encode(
        x=alt.X('Date_of_Measurement:T', title='Time'),
        y=alt.Y('Systolic_Pressure:Q', title='Systolic Pressure', scale=alt.Scale(domain=[data['Systolic_Pressure'].min() - 10, data['Systolic_Pressure'].max() + 10])),
        tooltip=['Date_of_Measurement:T', 'Systolic_Pressure:Q']
    ).properties(
        title=title
    ) + alt.Chart(data).mark_circle(color='blue').encode(
        x=alt.X('Date_of_Measurement:T', title='Time'),
        y=alt.Y('Diastolic_Pressure:Q', title='Diastolic Pressure', scale=alt.Scale(domain=[data['Diastolic_Pressure'].min() - 10, data['Diastolic_Pressure'].max() + 10])),
        tooltip=['Date_of_Measurement:T', 'Diastolic_Pressure:Q']
    )

    # Customize the x-axis for "Yesterday" period
    if period == 'Último dia':
        chart = chart.encode(
            x=alt.X('Date_of_Measurement:T', axis=alt.Axis(format='%H:%M', title='Hora', tickCount=24))
        )

    return chart

def create_measurements_chart(data, title, period):
    # Convert Date_of_Measurement to datetime if not already
    if data['Date_of_Measurement'].dtype == 'object':
        data['Date_of_Measurement'] = pd.to_datetime(data['Date_of_Measurement'])

# Customize the chart based on the period
    if period == 'Último dia':
        # Group by hour for the last day
        data['Hour'] = data['Date_of_Measurement'].dt.floor('H')
        count_data = data.groupby('Hour').size().reset_index(name='Count')
        
        # Create a bar chart for the number of measurements grouped by hour
        chart = alt.Chart(count_data).mark_bar(color='lightblue').encode(
            x=alt.X('Hour:T', axis=alt.Axis(format='%H:%M', title='Hora')),
            y=alt.Y('Count:Q', title='Número de Medições')
        ).properties(
            title=title
        )
    else:
        # Group by date for other periods
        data['Date'] = data['Date_of_Measurement'].dt.date
        count_data = data.groupby('Date').size().reset_index(name='Count')

        # Create a bar chart for the number of measurements grouped by date
        chart = alt.Chart(count_data).mark_bar(color='lightblue').encode(
            x=alt.X('Date:T', title='Data'),
            y=alt.Y('Count:Q', title='Número de Medições')
        ).properties(
            title=title
        )
    
    return chart

def filter_data_by_period(data, period):
    data = data.copy()  # Avoid SettingWithCopyWarning
    data['Date_of_Measurement'] = pd.to_datetime(data['Date_of_Measurement'])  # Ensure datetime format
    now = datetime.now()
    if period == 'Último dia':
        start_date = now - timedelta(days=1)
    elif period == 'Última semana':
        start_date = now - timedelta(weeks=1)
    elif period == 'Último mês':
        start_date = now - timedelta(days=30)
    else:
        start_date = data['Date_of_Measurement'].min()
    return data[data['Date_of_Measurement'] >= start_date]

def measurement_screen(data):

    with st.container():
        col1, col2, col3 = st.columns(spec=[0.325, 0.35, 0.325])

        with col1:
            st.empty()

        with col2:
            with st.container():
                st.title("Tela de Medições")

        with col3:
            st.empty()

        st.subheader("Requisitar nova medição:")

    col1, col2, col3 = st.columns(spec=[0.35, 0.2, 0.45])

    with col1:
        patient_name = st.text_input(label="Novo Paciente", placeholder="Insira o Nome do(a) Paciente", disabled=False, label_visibility="collapsed")

    with col2:
        # Check device connection status
        if patient_name:
            st.success("Medição Habilitada", icon=":material/check:")
        #else:
        #    st.error("Insira um nome", icon=":material/cancel:")

    with col3:
        st.empty()

    with st.container():
        col1, col2, col3 = st.columns(spec=[0.125, 0.225, 0.65])

        with col1:
            # Button to generate a new measurement 
            if st.button("Nova Medição"):
                if patient_name:
                    data = load_data("data.csv")  # Reload data to ensure we're appending to the latest version
                    new_measurement = get_new_measurement(patient_name, data)
                    # Append the new measurement to the dataframe
                    data = data._append(new_measurement, ignore_index=True)
                    # Save the updated dataframe to the CSV file
                    data.to_csv("data.csv", index=False)
                    with col2:
                        st.success("Medição realizada!")
                        sleep(1.5)
                        st.rerun()  # Reload the file to update the dataframe
                else:
                    with col2:
                        st.error("Insira o nome do(a) paciente")

        with col3:
            st.empty()

    st.empty()
    st.subheader("Medições Pendentes:")

    # Button to get requested measurements 
    if st.button("Procurar Novas Medições"):
        # Load existing measurements
        before_measures = load_data("requested_measures.csv")
        before_count = len(before_measures)
        
        # Request new measurements via BLE
        ble_request_measures()

        # Load measurements after BLE request
        after_measures = load_data("requested_measures.csv")
        after_count = len(after_measures)

        # Compare the number of rows before and after the BLE request
        if after_count > before_count:
            st.success("Novas medições foram adicionadas.")
            st.rerun()
        else:
            st.error("Nenhuma nova medição para ler.")

    # Load pending measures
    pending_measures_df = load_data("requested_measures.csv")
    pending_measures_df['Name'] = pending_measures_df['Name'].astype(str).replace('nan', '')

    #----------------------------------------------------------------------------------------------
    col1, col2 = st.columns(spec=[0.5, 0.5])
    
    with col1:
        # Display the pending measures for editing
        st.write("Medições Pendentes:")

        edited_pending_measures_df = st.data_editor(
            pending_measures_df,
            column_config=get_column_config(1),
            hide_index=True,
            key="1",
        )

        # Separate rows with names entered from the ones without names
        named_measures_df = edited_pending_measures_df[edited_pending_measures_df['Name'].str.strip() != '']
        unnamed_measures_df = edited_pending_measures_df[edited_pending_measures_df['Name'].str.strip() == '']

    with col2:
        # Display the processed measures
        st.write("Medições prontas para apontar:")

        st.data_editor(
            named_measures_df,
            column_config=get_column_config(1),
            hide_index=True,
            key="2",
        )

        # Button to get requested measurements 
        if st.button("Apontar Medições"):
            placeholder = st.empty()
            # Save the unnamed measures back to the pending measures CSV
            save_data(unnamed_measures_df, "requested_measures.csv")

            # Append the new named measurements to the processed measures CSV
            if not named_measures_df.empty:
                processed_measures_df = load_data("processed_measures.csv")
                processed_measures_df['Name'] = processed_measures_df['Name'].astype(str)

                processed_measures_df = processed_measures_df._append(named_measures_df, ignore_index=True)
                save_data(processed_measures_df, "processed_measures.csv")
                append_measurements()
                st.rerun()
            else:
                placeholder.error("Nenhuma nova medição foi apontada", icon=":material/cancel:")


    #----------------------------------------------------------------------------------------------

def general_screen(data):
    
    with st.container():
        col1, col2, col3 = st.columns(spec=[0.225, 0.55, 0.225])

        with col1:
            st.empty()

        with col2:
            with st.container():
                st.title('Tela de Informações Gerais')

        with col3:
            st.empty()
    
    col1, col2 = st.columns(spec=[0.6,0.4])

    with col1:
        data = load_data("data.csv")  # Reload data to ensure we're appending to the latest version
        data_general = data.drop(columns=['Id']).reset_index(drop=True)

        st.write("Dados dos pacientes:")

        st.data_editor(
            data_general,
            column_config=get_column_config(1),
            hide_index=True,
        )

    with col2:
        period = st.selectbox("Selecione o Período de análise", ["Histórico completo", "Último mês", "Última semana", "Último dia"])
        filtered_period_data = filter_data_by_period(data_general, period)
        st.altair_chart(create_measurements_chart(filtered_period_data, f"Histórico de medidas: {period}", period), use_container_width=True)

    st.subheader("Medições de pressão categorizadas")

    st.altair_chart(create_bp_bar_chart(data_general, "Gráfico de medições categorizadas"), use_container_width=True)

def patient_screen(data):
    
    with st.container():
        col1, col2, col3 = st.columns(spec=[0.21, 0.58, 0.21])

        with col1:
            st.empty()

        with col2:
            with st.container():
                st.title('Tela de Informações Individuais')

        with col3:
            st.empty()
    
    data = load_data("data.csv")  # Reload data to ensure we're appending to the latest version
    data_patients = data.drop(columns=['Id']).reset_index(drop=True)
    
    data_patients = sorted(data['Name'].unique().tolist())
    selected_patient = st.selectbox("Selecione o Paciente", data_patients)
    filtered_data = data[data['Name'] == selected_patient]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Medições para o paciente: {selected_patient}:")

        # Display the pivoted data as a table
        patient_data = st.data_editor(
            filtered_data.pivot_table(index='Date_of_Measurement', values=['Systolic_Pressure', 'Diastolic_Pressure'], aggfunc='first'),
            column_config=get_column_config(2),
            hide_index=True,
        )
    with col2:
        st.altair_chart(create_bp_bar_chart(data[data['Name'] == selected_patient], f"Medições de pressão categorizadas; {selected_patient}"), use_container_width=True)

    period = st.selectbox("Selecione o Período", ["Histórico completo", "Último mês", "Última semana", "Último dia"])
    filtered_period_data = filter_data_by_period(filtered_data, period)
    st.altair_chart(create_bp_history_chart(filtered_period_data, f"Medições de pressão: {selected_patient} ({period})", period), use_container_width=True)

def main():
    # Load data from CSV
    csv_file = "data.csv"  # Update with your CSV file path
    data = st.cache_data(load_data)(csv_file)

    # Add a sidebar menu for selecting the table to display
    menu_selection = st.sidebar.selectbox("Menu", ("Medições","Informações Gerais", "Informações Individuais"))

    if menu_selection == "Medições":
        measurement_screen(data)
    elif menu_selection == "Informações Gerais":
        general_screen(data)
    elif menu_selection == "Informações Individuais":
        patient_screen(data)

if __name__ == '__main__':
    main()
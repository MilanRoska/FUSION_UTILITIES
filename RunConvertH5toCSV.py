# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 11:12:47 2024

@author: m.roska
"""

# %% packages
import os
import pandas as pd
import h5py
import numpy as np
from datetime import datetime
import re


# %% functions
def clean_label(label):
    # Remove 'm/z ' from the beginning if it exists
    if label.startswith('m/z '):
        label = label[len('m/z '):]
    
    # Remove ' []' from the end if it exists
    if label.endswith(' []'):
        label = label[:-len(' []')]
    
    return label

# Function to extract chemica formula and reduce by one H and add _ppbV at the end
def modify_formula(desc):
    mass_hydron = 1.00728
    # check if formula was assigned
    # no formula assigned will ahve only []
    if '[]' in desc:
        #filter mass from string
        mass_part = desc
        mass_part = clean_label(mass_part)
        modified_formula = float(mass_part)
        #substract mass of hydron asumming pure ionization by H+
        modified_formula = modified_formula - mass_hydron
        modified_formula = round(modified_formula,5)
        modified_formula = str(modified_formula)
        
    # otherwise a formula is assigned    
    else:
        # Extract the part after '['
        formula_part = desc.split('[')[-1]

        # Extract elements and numbers using regex
        elements_counts = re.findall(r'([A-Za-z]+)(\d*)', formula_part)
    
        modified_formula = ""
        for element, count in elements_counts:
            if element == 'H' and count:
                # Decrease hydrogen count by 1
                count = str(int(count) - 1) if int(count) > 1 else ""
            modified_formula += f"{element}{count}"

    modified_formula += '_ppbV'
    return modified_formula


# %% inputs
# set file name and path of file
file_name = '2024_CHANEL_07_01_LIM_day_export.h5'
file_path = 'C://Users/m.roska/OneDrive - Forschungszentrum Jülich GmbH/Desktop/'

# %% load
# open h5 file
with h5py.File(os.path.join(file_path + file_name), 'r') as current_file:
    # open ppbV data group
    data_grp = current_file['TS_all_ppbV']
    # load peak data from ppbV group
    peak_data = np.array(data_grp['TS'])
    # load timing data from ppbV group
    buf_times = np.array(data_grp['time_string'])
    # convert time format to datetime
    time_format = '%d-%b-%Y %H:%M:%S'
    buf_times = [datetime.strptime(bt.decode('utf-8'), time_format) for bt in buf_times]

    # load formula liit and convert from bytes to string
    peak_table = data_grp['description']
    formulas = [desc.decode('utf-8') for desc in peak_table]
    # reduce to pure chemical formula and reduce H count by one. add _ppbV at end of string
    formulas = [modify_formula(desc) for desc in formulas]



# %% concat
# Create a DataFrame
# time as index, formulas as labels and peak data as column data
df = pd.DataFrame(data=peak_data, index=buf_times, columns=formulas)

# %% filter
# get a 1 min averaged standard deviation
# Resample the DataFrame to one-minute intervals and calculate the standard deviation
std_per_minute = df.resample('T').std()
# Calculate the average of these standard deviations for each column
average_std = std_per_minute.mean()

# Create DataFrame with column statistics
stats = {
    'min': df.min(),
    'max': df.max(),
    'average': df.mean(),
    'average_std': average_std
}
df_stats = pd.DataFrame(stats)

# drop TS with max bellow min ppb and snr bellow min snr
min_ppb = 0.01
min_snr = 3
columns_to_drop = df_stats[(df_stats['max'] < min_ppb) | (min_snr * df_stats['average_std'] > df_stats['max'])].index
# Drop the identified columns from df
df_cleaned = df.drop(columns=columns_to_drop)


# %% export
# Change the file extension to .csv
output_file_full_name = os.path.join(file_path, os.path.splitext(file_name)[0] + '.csv')

# Export the DataFrame to a CSV file with the same name as the imported file
# seting seperator to be ';' and index label to be 'Time_Text'
df.to_csv(output_file_full_name, sep=';', index_label='Time_Text')

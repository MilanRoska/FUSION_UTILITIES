# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 11:12:47 2024

@author: m.roska
"""

#%% packages
import os
import pandas as pd
import h5py
import numpy as np
from datetime import datetime
import re

# %% functions
# Function to extract chemica formula and reduce by one H and add _ppbV at the end
def modify_formula(desc):
    # Extract the part after '['
    if '[' in desc:
        formula_part = desc.split('[')[-1]
    else:
        formula_part = desc
    
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

#%% inputs
#set file name and path of file
file_name = 'IDA_Export_test.h5'
file_path = 'C://Users/m.roska/OneDrive - Forschungszentrum Jülich GmbH/Desktop/'

#%% load
#open h5 file
with h5py.File(os.path.join(file_path + file_name), 'r') as current_file:
    #open ppbV data group
    data_grp = current_file['TS_all_ppbV']
    #load peak data from ppbV group
    peak_data = np.array(data_grp['TS'])
    #load timing data from ppbV group
    buf_times = np.array(data_grp['time_string'])
    #convert time format to datetime
    time_format = '%d-%b-%Y %H:%M:%S'
    buf_times = [datetime.strptime(bt.decode('utf-8'), time_format) for bt in buf_times]
    
    # load formula liit and convert from bytes to string
    peak_table = data_grp['description']
    formulas = [desc.decode('utf-8') for desc in peak_table]
    # reduce to pure chemical formula and reduce H count by one. add _ppbV at end of string
    formulas = [modify_formula(desc) for desc in formulas]


#%% concat
# Create a DataFrame
# time as index, formulas as labels and peak data as column data
df = pd.DataFrame(data=peak_data, index=buf_times, columns=formulas)

#%% export
# Change the file extension to .csv
output_file_full_name = os.path.join(file_path, os.path.splitext(file_name)[0] + '.csv')

# Export the DataFrame to a CSV file with the same name as the imported file
# seting seperator to be ';' and index label to be 'Time_Text'
df.to_csv(output_file_full_name, sep=';', index_label='Time_Text')

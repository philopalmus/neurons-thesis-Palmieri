import os
import re

import pandas as pd
import numpy as np

# ! PARAMETERS TO CHANGE EVERY TIME

directories_matching_pattern = r'P-([\d\.]+)--range-([\d\.]+)'  #! should contain P and range
simulation_name = r'example_simulation'

pout = 20
max_lines = 30  #* sarebbe tmax / flush

#
# general_dir = r'/home/apicella/Output_Files/'
general_dir = r'./'
output_name = r'q3-' + simulation_name

# ! #####################

# 
simulation_dir = os.path.join(general_dir, simulation_name)
savedir = os.path.join(simulation_dir, output_name)

def merge_all_q3_files(out_format='.feather'):
    """
    Merges all q3 files in a simulation directory and creates a unique feather file to be easily read.
    """

    print(f"Out format = {out_format}.")

    first_iteration = True

    # Loop through the directories and files
    for entry in os.listdir(simulation_dir):
        full_path = os.path.join(simulation_dir, entry)
        
        if os.path.isdir(full_path):
            # Extract P and range:
            try:
                number_patterns, mixing_range = extract_numbers(entry)
                print(f'dir = {entry}: P={number_patterns}, range={mixing_range}')
            except ValueError:
                print(f'dir = {entry}: not counted')
                continue

            for filename in os.listdir(full_path):
                # Select only q3 files:
                if filename[:2] == 'q3':    
                    q3_filepath = os.path.join(full_path, filename)
                    q3_file_df = pd.read_csv(q3_filepath, sep='\s+', header=None)
                    q3_file_df = format_df(q3_file_df, number_patterns=number_patterns, mixing_range=mixing_range)

                    # create df variable on first file
                    if first_iteration:
                        df = q3_file_df
                        first_iteration = False
                    # add to the df variable
                    else:
                        df = pd.concat([df, q3_file_df], ignore_index=True)

    # save the file
    match(out_format):
        case '.feather':
            df.to_feather(savedir + out_format)
        case '.csv':
            df.to_csv(savedir + out_format, index=False)
        case _:
            raise ValueError(purple(f"Format {out_format} is not supported but you can easily add it to the code"))
        
    print("I am done")

def format_df(df, number_patterns, mixing_range):
    """
    This function takes a headerless df as input and adds the correct number of rows and colums by adding NaN values.
    This way one can merge dataframes from simulations with less patterns printed or
    simulations ended prematurely due to the maxsp2 mechanism.
    Also adds information like the line, the range and the number of patterns used in the simulation.
    24_11_19 adds also the rate of the last time window calculated as (#spikes)/(tmax-tmin)
    """

    # Check if all values in the first three columns are equal using the `all()` method
    conditions = [(df.iloc[:, column] == df.iloc[0, column]).all() for column in range(3)]
    # get sigma, delta, alpha if they are the same, raise error instead
    if all(conditions):
        sigma, delta, alpha = df.iloc[0, 0:3]
    else:
        raise ValueError(purple("\n\n\tformat_df: not all sigmas, deltas or alphas in the dataframe are equal!\n\n"))

    number_rows, number_cols = df.shape

    # get the right number of rows by putting NaN values in
    if number_rows > max_lines:
        raise TypeError(purple(f"\n\n\tformat_df: numebr of rows ({number_rows}) is greater than max lines ({max_lines})!\n\n"))
    elif number_rows < max_lines:
        # cycle until you get to max_lines lines
        while df.shape[0] < max_lines:
            # sigma, delta and alpha need to be correct
            new_row = np.array([sigma, delta, alpha] + [np.nan for _ in range(number_cols-3)])
            new_row_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_row_df], ignore_index=True)

    # get the right number of columns by putting NaN values in    
    while df.shape[1] < (9 + 2 * pout):
        df[len(df.columns)] = np.full(max_lines, np.nan)

    # add range and P columns
    df[len(df.columns)] = np.full(max_lines, number_patterns)
    df[len(df.columns)] = np.full(max_lines, mixing_range)

    # add line-number columns (reverse the order, 1 is the last one and so on)
    df[len(df.columns)] = np.arange(max_lines, 0, -1)

    # create the column names
    cols = ['sigma','delta','alpha','tmin','tmax','# spike','which_max','max overlap','fluctuations']
    for i in range(pout):
        cols.append(f'window pattern {i}')
        cols.append(f'overlap pattern {i}')
    cols += ['P', 'range', 'line']
    df.columns = cols

    # add a rate column
    df['rate'] = df['# spike'] / (df['tmax'] - df['tmin'])

    return df

def extract_numbers(directory_name):
    """
    Gets the range and the number of patterns from the directories whose names are like "P-500--range-4.0"
    """

    # Search for the correct directory pattern in the directory name
    match = re.search(directories_matching_pattern, directory_name)
    
    if match:
        # Extract the numbers and convert them to appropriate types
        number_patterns = int(match.group(1))  
        mixing_range = float(match.group(2))
        return number_patterns, mixing_range
    else:
        raise ValueError("No match found")
    
def extract_connessioni_file():
    """
    Finds and returns in a dataframe all the directories of the files CONNESSIONI
    """
    # Create empty  dataframe
    df_connessioni = pd.DataFrame(columns=['P', 'range', 'connessioni_file'])

    # Create a regular expression pattern for files starting with 'CONNESSIONI'
    pattern = r'^CONNESSIONI.*'

    for entry in os.listdir(simulation_dir):
        full_path = os.path.join(simulation_dir, entry)
        
        if os.path.isdir(full_path):
            # Extract P and range:
            try:
                number_patterns, mixing_range = extract_numbers(entry)
                files = os.listdir(full_path)
                # Filter the files based on the pattern using re.match
                matching_files = [f for f in files if re.match(pattern, f)]
                # Get the full paths of the matching files
                matching_file_paths = [os.path.join(full_path, f) for f in matching_files]

                # Check if exactly one file matches the pattern
                if len(matching_file_paths) == 1:
                    # Add the found file path to the dataframe
                    new_row = {'P': number_patterns, 'range': mixing_range, 'connessioni_file':matching_file_paths[0]}
                    df_connessioni.loc[len(df_connessioni)] = new_row
                    print(f'dir = {entry}: P={number_patterns}, range={mixing_range}, single file CONNESSIONI found')
                else:
                    if len(matching_file_paths) == 0:
                        print(purple("No file starting with 'CONNESSIONI' was found."))
                    else:
                        print(purple("Multiple files starting with 'CONNESSIONI' were found."))

            except ValueError:
                print(f'dir = {entry}: not counted')
    
    # Return the dataframe
    return df_connessioni

def purple(string: str):
    return "\033[95m" + string + "\033[0m"

def test():
    test_file = r'/home/apicella/Output_Files/random-21x21-gauss-CUE_only-t500--Z-300--capacity2/P-50--range-10.0/q3-9.55-0-0.dat'
    df = pd.read_csv(test_file, sep='\s+', header=None)
    df = format_df(df, 50, 10.0)
    df.to_csv('test.csv', index=False)


if __name__ == "__main__":
    # test()
    merge_all_q3_files()
    # merge_all_q3_files(out_format='.csv')

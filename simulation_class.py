import os, re
import itertools
from typing import Tuple, List, Callable

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

import ipywidgets as widgets
from ipywidgets import Output
from IPython.display import display, Image


class Simulation:
    def __init__(
            self, 
            files_dir: str, #? example: /home/ilenia/OutputFiles
            simulation_name: str, 

            numbers_of_patterns: List[str]=[], 
            mixing_ranges: List[str]=[], 
            max_lines: int=1,
            directories_matching_pattern: str = r'P-([\d\.]+)--range-([\d\.]+)' #! should contain P and range
            ):
        
        self.files_dir = files_dir
        self.simulation_name = simulation_name
        self.numbers_of_patterns = numbers_of_patterns
        self.mixing_ranges = mixing_ranges
        self.max_lines = max_lines
        self.directories_matching_pattern = directories_matching_pattern

        # Calculate the real simulation directory
        dir = os.path.join(files_dir, simulation_name)
        self.dir = dir.replace("/", os.sep).replace("\\", os.sep)

        # Look for feather file of all q3 files merged
        q3_merged_path = os.path.join(self.dir, 'q3-' + self.simulation_name + '.feather')
        #? example of how the file is formatted, in the case of 20 patterns: 
        #? sigma,delta,alpha,tmin,tmax,# spike,which_max,max overlap,fluctuations,window pattern 0,overlap pattern 0,...,window pattern 19,overlap pattern 19,P,range,line,rate

        if os.path.isfile(q3_merged_path):
            self.q3_merged_df = pd.read_feather(q3_merged_path)

            # create a lighter version, may be useful later
            columns = ['sigma','delta','alpha','tmin','tmax','# spike','which_max','max overlap','fluctuations','window pattern 0','overlap pattern 0','P','range','line','rate']
            self.q3_merged_df_light = self.q3_merged_df[columns]

            # calculate numbers of patterns, mixing ranges, sigmas, deltas, alphas from the file
            self.int_n_patterns = sorted(self.q3_merged_df['P'].unique().tolist())
            self.float_mixing_ranges = sorted(self.q3_merged_df['range'].unique().tolist())

            self.sigmas = sorted(self.q3_merged_df['sigma'].unique().tolist())
            self.deltas = sorted(self.q3_merged_df['delta'].unique().tolist())
            self.alphas = sorted(self.q3_merged_df['alpha'].unique().tolist())

            # Sometimes fluctuations can be negative (numerical error)
            self.min_fluctuations = self.q3_merged_df['fluctuations'][self.q3_merged_df['fluctuations'] > 0].min()
            self.max_fluctuations = self.q3_merged_df['fluctuations'].max()

            self.max_lines = self.q3_merged_df['line'].max()

            self.max_rate = self.q3_merged_df['rate'].max()

            self.q3merged = True

        else:
            print(f"Simulation class: looked for feather file with path '{q3_merged_path}'. \n Could not find it.")
            print(f"THIS VERSION OF THE CODE IS NOT GOOD FOR WORKING IN THIS CASE, you need to use q3merge.py to generate a file that this code can read.")

            # Non-string versions of numbers of patterns or mixing ranges if they were passed
            if numbers_of_patterns:
                self.int_n_patterns = [int(i) for i in self.numbers_of_patterns].sort()
            else:
                raise ValueError("No patterns passed and no q3-merged file found")
            if mixing_ranges:
                self.float_mixing_ranges = [float(i) for i in self.mixing_ranges].sort()
            else:
                raise ValueError("No mixing ranges passed and no q3-merged file found")

            # Calculate max and min of fluctuations and sigmas and deltas (legacy way)
            self.min_fluctuations, self.max_fluctuations = self.find_min_max_values()[1]
            self.sigmas_deltas()
            self.alphas = None

            self.q3merged = False

        #! These are useful for the future, calculating modularity or capacity
        # Initialize the connessioni files directory dataframe which can be used to find the matrix for each value of P and range
        self.df_paths_connessioni = self.extract_connessioni_file()

        self.threshold = 0.9
    
    def print_values(self):
        # todo - make this function print more useful info
        print(f'self.files_dir = {self.files_dir}')
        print(f'self.simulation_name = {self.simulation_name}')
        print(f'self.numbers_of_patterns = {self.numbers_of_patterns}')
        print(f'self.mixing_ranges = {self.mixing_ranges}')
        print(f'self.max_lines = {self.max_lines}')
        print(f'self.dir = {self.dir}')
        print(f'self.min_fluctuations = {self.min_fluctuations}')
        print(f'self.max_fluctuations = {self.max_fluctuations}')
        print(f'self.sigmas = {self.sigmas}')
        print(f'self.deltas = {self.deltas}')
        print(f'self.alphas = {self.alphas}')

    def extract_numbers(self, directory_name):
        """
        Gets the range and the number of patterns from the directories whose names are like "P-500--range-4.0"
        """
        # Search for the pattern in the directory name
        match = re.search(self.directories_matching_pattern, directory_name)
        
        if match:
            # Extract the numbers and convert them to appropriate types
            number_patterns = int(match.group(1))  
            mixing_range = float(match.group(2))
            return number_patterns, mixing_range
        else:
            raise ValueError("No match found")

    #! this function is not used right now, but can be useful to study the file connessioni if needed
    def extract_connessioni_file(self):
        """
        Finds and returns in a dataframe all the directories of the files CONNESSIONI
        """
        # Create empty  dataframe
        df_connessioni = pd.DataFrame(columns=['P', 'range', 'connessioni_file'])

        # Create a regular expression pattern for files starting with 'CONNESSIONI'
        pattern = r'^CONNESSIONI.*'

        for entry in os.listdir(self.dir):
            full_path = os.path.join(self.dir, entry)
            
            if os.path.isdir(full_path):
                # Extract P and range:
                try:
                    number_patterns, mixing_range = self.extract_numbers(entry)
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
                        #* print(f'dir = {entry}: P={number_patterns}, range={mixing_range}, single file CONNESSIONI found')
                    else:
                        if len(matching_file_paths) == 0:
                            print(Simulation.purple("No file starting with 'CONNESSIONI' was found."))
                        else:
                            print(Simulation.purple("Multiple files starting with 'CONNESSIONI' were found."))

                except ValueError:
                    print(f'dir = {entry}: not counted')
        # Return the dataframe
        return df_connessioni

    def set_min_fluctuations(self, v_min):
        """Manually set the minimum of the fluctuations"""
        self.min_fluctuations = v_min

    def set_max_fluctuations(self, v_max):
        """Manually set the maximum of the fluctuations"""
        self.max_fluctuations = v_max

    def sigmas_deltas(self):
        """
        Find the values of sigmas and deltas when not merging the q3 files
        """
        # Get one of the directories of the simulations
        pattern = self.numbers_of_patterns[0]
        mixing_range = self.mixing_ranges[0]
        first_folder = f'P-{pattern}--range-{mixing_range}'
        directory = os.path.join(self.dir, first_folder)
        
        # Lists to store unique values
        sigmas = set()
        deltas = set()

        # Go over all the files q3 in that dorectory to retrieve the values of sigmas and deltas
        for filename in os.listdir(directory):
            if filename[:2] == 'q3':    
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    with open(filepath) as file:
                        df = pd.read_csv(file, sep='\s+').to_numpy()
                        sigmas.add(df[0][0])
                        deltas.add(df[0][1])

        # Set the values of sigmas and deltas of the simulation object as ordered lists
        self.sigmas = sorted(sigmas, key=float)
        self.deltas = sorted(deltas, key=float)
        
    def pivot_df(self, what: str, n_patterns: int, mixing_range: float, line: int):
        """
        Returns a pivot dataframe, useful for plotting heatmaps, of 'what' as a function of sigma and delta
        'what' can be, for example 'overlap', 'max_overlap', 'overlap pattern 0', 'fluctuations'
        """
        df = self.q3_merged_df_light
        # df = self.q3_merged_df
        filtered_df = df[
            (df['P'] == n_patterns) &
            (df['range'] == mixing_range) &
            (df['line'] == line)
        ]
        return filtered_df.pivot(index='delta', columns='sigma', values=what)

    def plot_overlap(self,
        n_patterns: int,
        mixing_range: float,
        line: int=1,
        annotations: bool=False,
        save_as: str=None,
        savedir: str='.',
        dpi:int =300,
        ax=None
        ):
        """
        Heatmap of the overlap for selected line of the q3 files, range and number of patterns.
        Can save the plot as a file.
        """
        # set the data to plot
        pivot = self.pivot_df('max overlap', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        min_heatmap_overlap, max_heatmap_overlap = 0,  1

        # if ax is not passed, create the object
        if ax == None:
            fig, ax = plt.subplots()  # default is 1x1
            was_ax_passed = None
        else:
            was_ax_passed = True
        
        # do the plot
        sns.heatmap(pivot, annot=annotations, cmap='coolwarm', mask=pivot.isnull(),
                vmin=min_heatmap_overlap, vmax=max_heatmap_overlap, ax=ax, fmt=".2f")
        ax.invert_yaxis()
        ax.set_title('Overlap')

        # if ax is not passed, also do the plot
        if was_ax_passed == None:
            # save it if requested
            if save_as is not None:
                plt.tight_layout()
                img_file = f"Overlap_range{mixing_range}_P{n_patterns}_line{line}." + save_as
                plt.savefig(savedir + os.sep + img_file, format=save_as, dpi=dpi)
                print("saved to: ", savedir + os.sep + img_file)

            plt.show()

    def plot_overlap_pattern_0(self,
        n_patterns: int,
        mixing_range: float,
        line: int=1,
        annotations: bool=False,
        save_as: str=None,
        savedir: str='.',
        dpi:int =300,
        ax=None
        ):
        """
        Heatmap of the overlap with pattern 0 for selected line of the q3 files, range and number of patterns.
        Can save the plot as a file.
        """
        # set the data to plot
        pivot = self.pivot_df('overlap pattern 0', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        min_heatmap_overlap, max_heatmap_overlap = 0,  1

        # if ax is not passed, create the object
        if ax == None:
            fig, ax = plt.subplots()  # default is 1x1
            was_ax_passed = None
        else:
            was_ax_passed = True
        
        # do the plot
        sns.heatmap(pivot, annot=annotations, cmap='coolwarm', mask=pivot.isnull(),
                vmin=min_heatmap_overlap, vmax=max_heatmap_overlap, ax=ax, fmt=".2f")
        ax.invert_yaxis()
        ax.set_title('Overlap pattern 0')

        # if ax is not passed, also do the plot
        if was_ax_passed == None:
            # save it if requested
            if save_as is not None:
                plt.tight_layout()
                img_file = f"Overlap_pattern_0_range{mixing_range}_P{n_patterns}_line{line}." + save_as
                plt.savefig(savedir + os.sep + img_file, format=save_as, dpi=dpi)
                print("saved to: ", savedir + os.sep + img_file)

            plt.show()

    def calculate_max_rate(self, n_patterns: int, mixing_range: float, line: int) -> float:
        """
        Calculates the maximum of the rate among all the simulations
        """
        pivot = self.pivot_df('rate', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        return pivot[pivot.index != 0].max().max()

    def plot_rate(self,
        n_patterns: int,
        mixing_range: float,
        line: int=1,
        annotations: bool=False,
        save_as: str=None,
        savedir: str='.',
        dpi:int =300,
        ax=None
        ):
        """
        Heatmap of the rate for selected line of the q3 files, range and number of patterns.
        Can save the plot as a file.
        """
        # set the data to plot
        pivot = self.pivot_df('rate', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        min_rate, max_rate = 0,  self.calculate_max_rate(n_patterns=n_patterns, mixing_range=mixing_range, line=line)

        # if ax is not passed, create the object
        if ax == None:
            fig, ax = plt.subplots()  # default is 1x1
            was_ax_passed = None
        else:
            was_ax_passed = True
        
        # do the plot
        sns.heatmap(pivot, annot=annotations, cmap='coolwarm', mask=pivot.isnull(),
                vmin=min_rate, vmax=max_rate, ax=ax, fmt=".2f")
        ax.invert_yaxis()
        ax.set_title('Rate  [#spikes / (tmax-tmin)]')

        # if ax is not passed, also do the plot
        if was_ax_passed == None:
            # save it if requested
            if save_as is not None:
                plt.tight_layout()
                img_file = f"Rate_coarse_range{mixing_range}_P{n_patterns}_line{line}." + save_as
                plt.savefig(savedir + os.sep + img_file, format=save_as, dpi=dpi)
                print("saved to: ", savedir + os.sep + img_file)

            plt.show()
    
    def plot_fluctuations(self,
        n_patterns: int,
        mixing_range: float,
        line: int=1,
        annotations: bool=False,
        save_as: str=None,
        savedir: str='.',
        dpi:int =300,
        ax=None
        ):
        """
        Heatmap of the fluctuations for selected line of the q3 files, range and number of patterns.
        Can save the plot as a file.
        Scale is logarithmic.
        """

        # set the data to plot
        pivot = self.pivot_df('fluctuations', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        min_heatmap_fluctuations = self.min_fluctuations 
        max_heatmap_fluctuations = self.max_fluctuations

        # if ax is not passed, create the object
        if ax == None:
            fig, ax = plt.subplots()  # default is 1x1
            was_ax_passed = None
        else:
            was_ax_passed = True
        
        # do the plot
        sns.heatmap(pivot, annot=annotations, cmap='coolwarm', ax=ax, mask=pivot.isnull(),
                        norm=matplotlib.colors.LogNorm(vmin=min_heatmap_fluctuations, vmax=max_heatmap_fluctuations),
                        fmt=".2f")
        ax.invert_yaxis()
        ax.set_title('Fluctuations')

        # if ax is not passed, also do the plot
        if was_ax_passed == None:
            # save it if requested
            if save_as is not None:
                plt.tight_layout()
                img_file = f"Fluctuations_range{mixing_range}_P{n_patterns}_line{line}." + save_as
                plt.savefig(savedir + os.sep + img_file, format=save_as, dpi=dpi)
                print("saved to: ", savedir + os.sep + img_file)

            plt.show()

    def plot_which_max(self,
        n_patterns: int,
        mixing_range: float,
        line: int=1,
        annotations: bool=False,
        save_as: str=None,
        savedir: str='.',
        dpi:int =300,
        ax=None
        ):
        """
        Heatmap of the pattern that maximizes the overlap for selected line of the q3 files, range and number of patterns.
        Can save the plot as a file.
        """

        # set the data to plot
        pivot = self.pivot_df('which_max', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        max_heatmap_which_max = n_patterns
        min_heatmap_which_max = 0

        # if ax is not passed, create the object
        if ax == None:
            fig, ax = plt.subplots()  # default is 1x1
            was_ax_passed = None
        else:
            was_ax_passed = True
        
        # do the plot
        sns.heatmap(pivot, annot=True, cmap='Spectral', mask=pivot.isnull(),
                        vmin=min_heatmap_which_max, vmax=max_heatmap_which_max, ax=ax)
        ax.invert_yaxis()
        ax.set_title('Which max')

        # if ax is not passed, also do the plot
        if was_ax_passed == None:
            # save it if requested
            if save_as is not None:
                plt.tight_layout()
                img_file = f"Which_max_range{mixing_range}_P{n_patterns}_line{line}." + save_as
                plt.savefig(savedir + os.sep + img_file, format=save_as, dpi=dpi)
                print("saved to: ", savedir + os.sep + img_file)

            plt.show()

    def plot_heatmap_overlap_fluctuations_whichmax_3(
            self,
            n_patterns: int,
            mixing_range: float,
            line: int,
            annotations: bool=False,
            save_as: str='',
            savedir: str=''
            ):
            """
            Creates plot from the output of q3merge.py (feather file for now)
            It requires for the directory to contain only a file that starts with "q3" and ends with ".feather"
            24_11_19 - uses the single plot functions for the different things
            Can be used to save to file.
            """
            fig, ax = plt.subplots(2, 3, sharex=True, sharey=True, figsize=(15,9))
            self.plot_overlap(n_patterns=n_patterns, mixing_range=mixing_range, line=line, ax=ax[0,0])
            self.plot_fluctuations(n_patterns=n_patterns, mixing_range=mixing_range, line=line, ax=ax[0,1])
            self.plot_rate(n_patterns=n_patterns, mixing_range=mixing_range, line=line, ax=ax[0,2])
            self.plot_overlap_pattern_0(n_patterns=n_patterns, mixing_range=mixing_range, line=line, ax=ax[1,0])
            self.plot_which_max(n_patterns=n_patterns, mixing_range=mixing_range, line=line, ax=ax[1,1])
            ax[1,2].axis('off')

            # Save the figure if a format is specified in "save_as" into "savedir"
            if save_as:
                name = f'P-{n_patterns}_range-{mixing_range}_line-{line}'

                # Add a title to the figure
                title = self.simulation_name + f'\n' + name
                plt.suptitle(title)

                # Default save to the directory of the simulation
                if not savedir:
                    savedir = self.dir
                savepath = os.path.join(savedir, name + '.' + save_as)
                plt.tight_layout()
                plt.savefig(savepath, format=save_as)

            else:
                plt.tight_layout()
            plt.show()



    def plot_heatmap_overlap_fluctuations_whichmax_2(
        self,
        n_patterns: int,
        mixing_range: float,
        line: int,
        annotations: bool=False,
        save_as: str='',
        savedir: str=''
        ):
        """
        OLD VERSION, MAKES THE PLOTS INSIDE THE FUNCTION ITSELF
        Creates plot from the output of q3merge.py (feather file for now)
        It requires for the directory to contain only a file that starts with "q3" and ends woth ".feather"
        """
        pivot_overlap = self.pivot_df('max overlap', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        pivot_fluctuations = self.pivot_df('fluctuations', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        pivot_overlap_pattern_0 = self.pivot_df('overlap pattern 0', n_patterns=n_patterns, mixing_range=mixing_range, line=line)
        pivot_which_max = self.pivot_df('which_max', n_patterns=n_patterns, mixing_range=mixing_range, line=line)

        min_heatmap_overlap, max_heatmap_overlap = 0,  1
        min_heatmap_fluctuations = self.min_fluctuations 
        max_heatmap_fluctuations = self.max_fluctuations
        max_heatmap_which_max = n_patterns
        min_heatmap_which_max = 0

        fig, ax = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(10,9))
        '''overlap'''
        sns.heatmap(pivot_overlap, annot=annotations, cmap='coolwarm', mask=pivot_overlap.isnull(),
                    vmin=min_heatmap_overlap, vmax=max_heatmap_overlap, ax=ax[0][0], fmt=".2f")
        ax[0, 0].set_title('Overlap')
        plt.gca().invert_yaxis()

        '''fluctuations'''
        sns.heatmap(pivot_fluctuations, annot=annotations, cmap='coolwarm', ax=ax[0][1], mask=pivot_fluctuations.isnull(),
                    norm=matplotlib.colors.LogNorm(vmin=min_heatmap_fluctuations, vmax=max_heatmap_fluctuations),
                    fmt=".2f")
        ax[0, 1].set_title('Fluctuations')
        plt.gca().invert_yaxis()

        '''overlap pattern 0'''
        sns.heatmap(pivot_overlap_pattern_0, annot=annotations, cmap='coolwarm', mask=pivot_overlap_pattern_0.isnull(),
                    vmin=min_heatmap_overlap, vmax=max_heatmap_overlap, ax=ax[1][0], fmt=".2f")
        ax[1, 0].set_title('Overlap pattern 0')
        plt.gca().invert_yaxis()

        '''which_max'''
        sns.heatmap(pivot_which_max, annot=True, cmap='Spectral', mask=pivot_which_max.isnull(),
                    vmin=min_heatmap_which_max, vmax=max_heatmap_which_max, ax=ax[1][1])
        # TODO -> fmt does not work (may be due to sharey)
        ax[1, 1].set_title('Which pattern')
        plt.gca().invert_yaxis()

        # Save the figure if a format is specified in "save_as" into "savedir"
        if save_as:
            name = f'P-{n_patterns}_range-{mixing_range}_line-{line}'

            # Add a title to the figure
            title = self.simulation_name + f'\n' + name
            plt.suptitle(title)

            # Default save to the directory of the simulation
            if not savedir:
                savedir = self.dir
            savepath = os.path.join(savedir, name + '.' + save_as)
            plt.tight_layout()
            plt.savefig(savepath, format=save_as)

        else:
            plt.tight_layout()
        plt.show()

    def slider_image(self):
        """
        Makes an interactive plot with three sliders, for the line (counting from the last one), range and number of patterns.
        It plots whatever "plot_heatmap_overlap_fluctuations_whichmax_3" plots; 
        change this function to make it plot whatever you want
        """
        def auxiliary_function(n_patterns: int, mixing_range: float, line: int):
            # not return anything, it plots an image
            self.plot_heatmap_overlap_fluctuations_whichmax_3(n_patterns=n_patterns, mixing_range=mixing_range, line=line)

        # Make the sliders
        p_slider = widgets.SelectionSlider(
            options=self.int_n_patterns,
            value=self.int_n_patterns[0], 
            description="Pattern:",
            style={'description_width': 'initial'}
        )
        range_slider = widgets.SelectionSlider(
            options=self.float_mixing_ranges,
            value=self.float_mixing_ranges[0], 
            description="Range:",
            style={'description_width': 'initial'}
        )
        line_slider = widgets.IntSlider(
            value=1, 
            min=1, 
            max=self.max_lines,
            step=1, 
            description="Line:",
            style={'description_width': 'initial'}
        )

        # Make the interactive plot
        interactive_plot = widgets.interactive_output(
            auxiliary_function,
            {'n_patterns': p_slider, 'mixing_range': range_slider, 'line': line_slider}
        )
        title = "<h3>" + self.simulation_name + "</h3>"
        title_widget = widgets.HTML(value=title)
        display(title_widget, p_slider, range_slider, line_slider, interactive_plot)

def test() -> None:
    """Useless as of right now, I used it with my old test simulation"""
    return None


if __name__ == "__main__":
    test()
    
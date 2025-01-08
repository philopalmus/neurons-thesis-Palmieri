import os
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches

import pandas as pd
import numpy as np

def make_fig_spikes2(
        spike_file: str,
        savedir: str='.',
        save_as: str=None, 
        time_ini=0,   # initial time (of the plot)
        time_fin=500,   # final time (of the plot)
        stripes=False,   # stripes i used to separate neurons in modules that participate or don't to a pattern
        figsize=(16,10), 
        pattern=0,    # set the order of the neurons according to a particular pattern, to see if that pattern is recalled
        file_name: str = 'Rasterplot',
        title: str='',
        dpi: int=900,
        sizes=None,  # sizes of the markers for cue and non-cue spikes
        alpha=0.7,   # transparency of the markers, useful when there are a lot of spikes near each other, set to one if there are very few spikes and you want to clearly see them
        legend=False,
        ax=None
        ):
    """
    This function plot a rasterplot starting from a spikes3 file of a simulation.
    The plot can be done in an ax of a matplotlib figure by passing the ax.
    There are a lot of graphical parameters.
    """
    
    Zeta = 300
    Kappa = Zeta // 2

    # Color palette
    colors = {
        "blue": "#1f77b4",
        "green": "#2ca02c",
        "red": "#d62728",
        "yellow": "#ffbf00",
        "purple": "#9467bd",
        "highlight": "#ff7f0e",  # Bright orange for highlighting
    }

    # To make the legend manually
    categories = {
        "Cue spikes": "red",
        "Non-cue spikes": "blue",
    }
    # Create legend handles manually
    legend_handles = [
        mpatches.Patch(color=color, label=label) for label, color in categories.items()
    ]


    # read the file
    file_type = os.path.splitext(spike_file)[1]
    if file_type == '.dat':
        spikes_df = pd.read_csv(spike_file, sep="\s+", header=None)
    elif file_type == '.feather':
        spikes_df = pd.read_feather(spike_file)
    else:
        print("Invalid file type")
        sys.exit(1)
    print(f"read {spike_file}")

    # format dataframe
    cols = ['time', 'cue', 'neuron']
    number_of_patterns = spikes_df.shape[1] - 3
    for i in range(number_of_patterns):
        cols.append(f'{i}')
    spikes_df.columns = cols

    # take the right spikes and other useful info
    df_filtered = spikes_df[(spikes_df['time'] >= time_ini) & (spikes_df['time'] <= time_fin)]
    spike_times = df_filtered['time']
    neuron_ids = df_filtered[str(pattern)]
    num = df_filtered.shape[0]
    greatest_neuron = np.max(neuron_ids)
    num_zones = greatest_neuron // Kappa
    t_max = np.max(spike_times)

    # make the plot
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        was_ax_none = True
    else:
        was_ax_none = False
    # loop through the number of zones and add horizontal spans and lines
    for i in range(num_zones):
        if stripes:
            ax.axhspan(Kappa+i*Zeta, Zeta+i*Zeta, color='purple', alpha=0.1)
        ax.axhline(y=i*Zeta, color=colors["purple"], linestyle='--', linewidth=1, zorder=3)
        # ax.axhline(y=Kappa+i*Zeta, color='g', linestyle=':')
    # Define the color map and sizes
    colors = ListedColormap(['blue', 'red'])
    if not sizes:
        sizes = [10, 25]
    sizes_list = [sizes[val] for val in df_filtered['cue']]
    scatter = ax.scatter(spike_times, neuron_ids, c=df_filtered['cue'], cmap=colors, s=sizes_list, alpha=alpha, edgecolors=None, marker='|', zorder=4)
    # Set limits for x and y axes
    ax.set_xlim(time_ini, t_max * 105 // 100)
    ax.set_ylim(-greatest_neuron * 5 // 100, greatest_neuron * 105 // 100)
    print(greatest_neuron, greatest_neuron * 105 // 100)

    # Make a legend if requested
    if legend:
        ax.legend(handles=legend_handles,
                fontsize=24,
                frameon=True,  # Add a frame around the legend
                shadow=True,   # Add a shadow for depth
                fancybox=True, # Rounded corners
                framealpha=0.9,  # Transparency of the frame
                edgecolor="black",  # Border color
                borderpad=1.1,  # Padding inside the border
                loc='upper left')

    
    # Set the title if requested
    if title:
        ax.set_title(title + f'\nnum spikes= {num}', fontsize=16)
    # else:
    #     ax.set_title(f'{spike_file}\nnumero spikes = {num}', fontsize=16)
    
    if was_ax_none:
        # Save the figure if requested
        if save_as is not None:
            save_file = savedir + os.sep + file_name + '.' + save_as
            fig.savefig(fname=save_file, format=save_as)
            print(f"Saved to: {save_file}")

        plt.show()
        

if __name__ == "__main__":
    dir = r'/path/of/your/spikes3/file.dat'
    make_fig_spikes2(spike_file=dir)
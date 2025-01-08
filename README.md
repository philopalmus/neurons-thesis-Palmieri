# What is this? <!-- omit from toc -->
This is some of the code I used to explore the data and make the plots for my master thesis.
I share it here for my colleagues that use the same or a future evolution of the model in the thesis hoping it could be useful.
I also think this code could be sued as a basis to which other functions and expansions could be added, I try to make the code easy to read and understand.

# DISCLAIMER: <!-- omit from toc -->
*I am not a programmer and this code may be full of very wrong things, or things that are not best practice. Before changing anything in `q3merge.py` or `simulation_class.py` I would check where that thing is used in the rest of the code because it could be easy to break something. I'm always available if help is needed and I was not lear enough in this explanation.*

- [1. Content, utility and logic of the code](#1-content-utility-and-logic-of-the-code)
    - [1.1. `simulation_class.py`](#11-simulation_classpy)
    - [1.2. `q3merge.py`](#12-q3mergepy)
    - [1.3. `make_fig_spikes.py`](#13-make_fig_spikespy)
- [2. Python requirements](#2-python-requirements)
- [3. Instructions on how to use it for the first time](#3-instructions-on-how-to-use-it-for-the-first-time)
- [4. Some quirks of the code](#4-some-quirks-of-the-code)
    - [Why use "line" instead of time since the time at which the overlap is calculated is available?](#why-use-line-instead-of-time-since-the-time-at-which-the-overlap-is-calculated-is-available)
    - [I don't understand `directories_matching_pattern: str = r'P-([\d\.]+)--range-([\d\.]+)'`](#i-dont-understand-directories_matching_pattern-str--rp-d--range-d)

# 1. Content, utility and logic of the code

There are 3 main python files:

### 1.1. `simulation_class.py` 

This file contains a class that allows the creation of an object for each simulation one runs.
These objects then have many methods to plot heatmaps of whatever is contained or calculable starting from the `q3` dat files, and also an interactive window with sliders for the time, number of patterns stored and the range.
New methods can be created on the same footprint.
When the object is initialized (and it requires very few lines) all data from all simulations with different parameters (**range or number of patterns for now**, could be expanded for example to alpha or other parameters with a little bit of work) is easily accessible.

🔴 Important: for this version of the code to work ***it is necessary to launch `q3merge.py` first***.

### 1.2. `q3merge.py`

This is a script that takes a folder, containing the outputs of all the simulations with different parameters you ran and generates a unique file (in the `.feather` format) with the info of all the `q3` files, correctly formatted into a dataframe, also adding NaN values where they are missing (some simulations may be shorter due to the `maxsp2` mechanism).
Once this file is generated the original files are no longer needed to make any heatmaps, this also helps save some space because the rest of the files can be compressed or this single file can be transferred on another machine to explore the data.

When a `simulation` object from `simulation_class.py` is initialized the code looks for this file.

To have a more easily readable dataframe you can also save the data to `csv` (or other formats). The `.feather` format is not human-readable but is efficient in terms of disk space and read times.

It does not matter where the `q3` files are in the directory searched by `q3merge.py`, it looks for all the files that start with "q3" and end with ".dat".
🔴 Important: you need to format the folder names of the simulations with different parameters in a way that contains the info of the **number of patterns** and the **range**.
The default that I used is `P-{number of patterns}--range-{range}` but you can personalize the code in whatever way you named the folders you already have by changing the "regular expression" the code changes.
All the important things to change before launching `q3merge.py` are at the beginning of the script, then you just launch it with no parameters.

### 1.3. `make_fig_spikes.py`

This contains a function that allows you to plot the rasterplots of the runs starting from a single `spikes3` file.
This is independent of the simulation class.


# 2. Python requirements

I have put the content of the environment I used in the `environment.yml` to make it easily reproducible for Anaconda users. I used `python 3.10.13`.

The necessary non-default libraries are:

- for `q3merge.py` and `simulation_class.py`: pandas, numpy, matplotlib, seaborn, ipywidjets, IPython (usually included with jupyter);
- for `make_fig_spikes.py`, numpy, pandas and matplotlib.

# 3. Instructions on how to use it for the first time

Look at the "examples" folders for some examples of what the code can do.
The `plots_examples.ipynb` file also allows you to test them yourself with the data of the simulations in the "example_simulation" folder.
This folder already contains the `.feather` file, so that you can use `plots_examples.ipynb` immediately.
To test `q3merge.py` delete this file and try to recreate it and look at all the parameters to change at the beginning of the script:

- `directories_matching_pattern` is the pattern that will be serched in the names of the folders so that the code can label the data in the `q3` files with also parameters that are fixed when the `C` code runs (for now, only the number of patterns P and the range, which need to be in the names of the flders). You need to put a different regular expression if your folders are formatted differently. 🔴 This regular expression is also an input of the simulation object, the default is the one I used.
- `simulation_name`, `general_dir` are linked to how I ordered my data, into folders for each simulation. They are not important if you order your data differently, but you need to set the 
- `simulation_dir` correctly. This is the directory with all the directories with the output files from all simulations with different number of patterns or range.
- `pout` the parameter used in the simulations for how many patterns write out in the `q3` files.
- `max_lines` is tmax / flush in the simulations and is the maximum number of lines in a single `q3` file.
- `output_name` is the name of the single output file.
- `savedir` where you want the file to be saved (including the file name!).

Now you can lauch `q3merge.py` in your python environment (with no command line arguments), wait for it to finish and you can now use `simulation_class.py`.

The class `Simulation` in `simulation_class.py` has many parameters, but you actulally only need the directory where the simulation is and the name of the simulation (a folder in this directory). If you don't like this structure change the `__init__` function and how the variable `dir` is calculated.
The important part is that the `.feather` file is read correctly, so 🔴 you also may need to change how this file is called if you changed it in `q3merge.py`

# 4. Some quirks of the code

### Why use "line" instead of time since the time at which the overlap is calculated is available?

line=1 means we are looking at the last line. Since not all simulations last the same necessarily, it may mean sometimes we are looking at heatmaps with data taken at different times.
This is not a ploblem for me since if a simulation finishes too early, it would mean that the rate was so high I would kind of already know what was happening.
Using line instead of time made it easy to write the code and still look back in time.
Generalizing to time instead of line is not obvious but could be done, keeping in mind that the times at which the overlap is calculated in different runs are slightly different since they are float.

### I don't understand `directories_matching_pattern: str = r'P-([\d\.]+)--range-([\d\.]+)'`

Regular expressions (using also the default python library re) are very useful since we have data written as strings (in this case in the names of the folders).
I also find them hard to use and I jsut tell a chatbot what I am trying to accomplish to get the right one and then test it.




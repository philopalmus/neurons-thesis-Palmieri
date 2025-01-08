# What is this?
This is some of the code I used to explore the data and make the plots for my master thesis.
I share it here for my colleagues that use the same or a future evolution of the model in the thesis hoping it could be useful.
I also think this code could be sued as a basis to which other functions and expansions could be added, I try to make the code easy to read and understand.

# 1. Content, utility and logic of the code

There are 3 main python files:

### 1. `simulation_class.py` 

This file contains a class that allows the creation of an object for each simulation one runs.
These objects then have many methods to plot heatmaps of whatever is contained or calculable starting from the `q3` dat files, and also an interactive window with sliders for the time, number of patterns stored and the range.
New methods can be created on the same footprint.
When the object is initialized (and it requires very few lines) all data from all simulations with different parameters (**range or number of patterns for now**, could be expanded for example to alpha or other parameters with a little bit of work) is easily accessible.

For this version of the code to work <font color="red">it is necessary to launch `q3merge.py` first</font>.

# 2. Python requirements



# 3. Instructions on how to use it for the first time



# 4. Some quirks of the code






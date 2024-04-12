# TransistorAnalysis
This repository contains the GUI of the Python3-based analysis tool for transistors, especially geared towards TLM, that T. Wollandt created in the framework of his PhD.

## Disclaimer
The code and the according documentation was done to the author's best knowledge and conscience. No guarantees can be made for the functionality of the program on all systems or with all data sets. 

## General Information
This program is based upon a command line interface (CLI) analysis tool that aims to offer an open-source, easy to understand and easy to modify alternative to a preexisting Origin script written by R. Rödel to extract transistor characteristics from static electric measurements.
The CLI basis of this program was written by Tobias Wollandt in Python (v3.10) and originally only offered analysis of transfer characteristics (e.g. effective mobility $\mu_{eff}$, threshold voltage $V_{th}$,...). Later, the possibility to analyze several transistors of different channel length $L$ was added, and based upon this first version, the transmission line method (TLM) could be analyzed and yields e.g. the contact resistance $R_CW$. The underlying code is documented to best knowledge and conscience in-line, but nevertheless there will be a description further down in this README.

## Installation
Execute this command to install the modules necessary to run the GUI program. Here, `pip` refers to pip3, in case this distinction is present in the target system (e.g. Linux)
This list should be complete.
`$ pip install numpy scipy pandas matplotlib PySide6 xlsxwriter` 

## General User Interface (GUI)
This program gives both experts and laymen access to the analysis tools used to extract sample characteristics, regardless of the operating system in use; MacOS has not been tested due to lack of availability to the author. The GUI is based upon the Python-module `PySide6` and consists of several parts:

1. Transfer Analysis
Data can be chosen from the file system and displayed in a plotting window. It can also be used to compare different datasets if the settings (Overwrite, Label,...) are chosen appropriately. For the fitting process the user is to input the correct values. An attempt will be made to read out most relevant values from the data file name, but this is not necessarily successful. Since the program is developed primarily for the use with data acquired by the program `SweepMe!` [(Link)](https://sweep-me.net), this format is heavily tested. Other file formats are in general supported, but not guaranteed to work. Other presets include `LabVIEW`, `ParameterAnalyzer` (VNA for S-Parameter measurements) and the files J. Borchert can take on the machine at 1st Phys. Inst. in Göttingen. For more information, read in `4. Analysis Settings`.
The analysis part of the code is imported from a lower level `.py` file and the fitting process is explained in more detail in the regarding section.

Most common cause of failure in this part of the program is discontinuities in the data. The analysis relies on the value of numeric derivative maximum of the dataset (or better: a fraction thereof. Datapoints where the first derivative is above e.g. 70% of the maximum are incorporated in the fitting process); discontinuities can show artificially high derivatives and therefore skip most data points. Possible solutions can be to smoothen the data more strongly or adjusting the derivative constraints (more detail in the regarding section)

In the code this entity is called `tab1` (chronologic reasons).

2. Transmission Line Method
Linear datasets of several channel lengths can be added to conduct TLM analysis. Correct file labeling is imperative for the success of this automated process. While in `1. Transfer Analysis` the user can adjust values like the channel dimensions $W$ and $L$ and thus gain more flexibility compared to the preexisting Origin script, this does not translate to the TLM analysis.

The summarized values for e.g. the intrinsic mobility $µ_0$ are extracted from fits of the data with respect to $L$ (on the $x$-axis). The value for $R_CW$ is shown by the average of the values for the few highest overdrive voltages; for the reliability of this value, see the plot `RcW (Vg-Vth)`. If there are problems with the fitting of individual datasets, it will be noted in the STDIO (error message in the python shell).

In the code this entity is called `tab3`.

3. S-Parameter Analysis
Uses Vector Network Analyzer data in order to determine the current gain characteristics of a transistor with respect to frequency, and thus determine the transit frequency $f_t$.
In the code this entity is called `tab5`.

4. Analysis Settings
To allow each user to adjust the default settings for each choice, a settings save file is provided and necessary for the program to work (if not given, an error message will tell the user so). Most settings are self-explanatory and just save the current state of checkbuttons, values given for e.g. the oxide capacitance etc.

For convenience reasons, the default directory opened when importing new data can be customized. Also, the user may overwrite the automatically determined fitting range (see the underlying analysis script for more details) with a fixed range of gate voltages.

The least intiutive part of the settings is the datafile preset. Due to the different possible ways a program can store data (most notably the shape and length of the header, the delimiter etc.) the program needs to be told which preset is to be used for the datasets. This should be quite easy, but as of v1.5 most of the program runs conditionally and tries all the available presets; if many more presets shall be added, the code should be rewritten to be more general! Again, `SweepMe!` is the authors preferred measurement program and thus tested the best. Even if the wrong preset is selected the program tries to read the data, although success is not guaranteed. For detailed information of how the data reading is done and what possible errors can occur, please refer to the `self.read_columnnames()` and `self.read_datafile()` methods in the `GUI.py` code.


5. Function Plotter
This part is not useful for transistor analysis per sé, it rather is a general purpose tool allowing laymen to enter arbitrary functions (using basic Python syntax and making use of numpy=np functions) with arbitrary parameters. The independent variable is fixed to be $x$. The scope of this project was to provide a general purpose fitting tool where the fitting function can be adjusted on the fly without need to alter the source code. This functionality is not implemented yet, however the groundwork is done and functional.

## Analysis Code
### analysis_function_definitions.py
Just a way to hide the function definitions used during the actual analysis in a separate file to not clutter. These functions are theoretically derived functions and can be found in text books (e.g. Sze _Physics of Semiconductors_). The most used functions are `mobility_lin()` and `mobility_sat()` which are used to fit the experimental data and extract the effective mobility.
Also important is the broadening kernel `gaussian()` which makes smoothing the data possible and is needed in order to make the numeric derivative viable to used.
### python_analysis_skript.py
Five classes are defined:
1. TransistorAnalysis()
Necessary information for the analysis consists of the channel dimensions $W$ and $L$, and the insulator (oxide) capacitance $C_{ox}$. Other values are assumed a default value, may however be modified from within the GUI. If one measures ***n*** type transistors, the current will have a different sign which needs to be accounted for. The program is initially designed to deal with ***p*** type semiconductors, which is the default setting in the GUI as well.

The backbone of the analysis is the `pandas` module and its `DataFrame` structure which gives easy and even for laymen in the code understandable access to the data. The class is structured in single methods which all refer to the main data and draw conclusions from it, e.g. extracting the on-off-ratio, the mobility and the subthreshold swing.

2. TLM_Analysis()
This class calls `TransistorAnalysis()` for each channel length provided for the TLM and analyzes the resulting data with respect to the overdrive voltage $V_g-V_{th}$ and to $L$. The class is divided into methods that will take this data and attempt to do a fit of the width normalized resistance $RW$ for each available overdrive voltage (`single_overdrive()`). This will yield the main result of the TLM measurement: $R_CW$

3. SparameterAnalysis()
This class yields the means to extract the transit frequency and other values from the S-parameters measured with a VNA.

4. Arrhenius()
This class automatically calculates TLM for each available temperature and makes it possible to extract the results into plots versus temperature. It was chosen to not make an automated TLM(T) plot because this proved to be far from trivial with the way the rest of the code and data is structured. From the T-dependent µ0 and RcW it is possible to extract the effective Schottky barrier height and the MTR activation energy.

5. Inverter()
This class analyzes inverters with respect to their trip point, gain, and noise margin.

## Roadmap & Ideas for the Future
<input type="checkbox" disabled> Add possibility to analyze data which does not include forward **and** backward sweep but only one of those. I started thinking about the implementation but realized that this would require rewriting all the analysis functions so I put it off for now.<br/>

<input type="checkbox" disabled> make the division (left/right) adjustable so the window doesnt get stretched too much if the size is increased (only plot should increase in size if possible)<br/>

<input type="checkbox" disabled> setting the thresholds for linearity manually does not work in the `subthreshold_swing` method. right now only the automatic version works. This was an issue if one wanted to rerun TLM analysis after removing a single datafile from the list.

<input type="checkbox" disabled> clean up the mess with filetype (sweepme, labview, parameteranalyzer etc) to have less try/except and better modularity for easier extension

<input type="checkbox" disabled> improve documentation

<input type="checkbox" disabled> in TLM, fit_mobility_lin() is called 3 times - can this be made more efficiently?

<input type="checkbox" disabled> add automated L correction for other tabs than TLM

<input type="checkbox" disabled> make sure Arrhenius plot works well before publishing anything with it

## Versions & Changelog
- 2023 November 14: v1.9.7.1 - resolved bug that led to long loading times (L-correction database)
- 2023 September 09: v1.9.7 - added m-TLM (Xu et al 2010) to the mix. code is NOT PRETTY but it works, kind of. probably will not be important enough to improve it
- 2023 September 06: v1.9.6.1 - tried to fix Arrhenius plot to work with Marburg SweepMe, and not only the hard-coded Göttingen filetypes - mostly successful, but RcW is off 
- 2023 August 31: v1.9.6 - added support for Marburg measurements (using SweepMe with Agilent 4145B, slightly different format, I guess?)
- 2023 August 24: v1.9.5 - added automated L and W dimension correction for TLM. adding it for TransferAnalysis is work in progress
- 2023 March 29: v1.9.4.1 - added mu0 error in the export/copy to clipboard
- 2023 March 20: v1.9.4 - added option in settings to fix the x-minimum of the TLM plot; if not selected, xmin is determined automatically (according to L_1/2)
- 2023 February 07: v1.9.3 - automatically search for the optimum derivation thresholds and "re-run" TLM accordingly
- 2023 January 17: v1.9.2.1 - replaced + operator with | in the Qt context (self.file_menu) & merged the latest version on the new laptop with some changes not transferred from my old laptop previously - is now up to date again
- 2022 October 06: v1.9.2 - added support for measurements from Surrey (added sep keyword_argument in pd.read_table, may need to be adjusted for old datapresets). minor bugfix ("south" in file name contains "out" and was not automatically added to analysis list)
- 2022 September 27: v1.9.1 - bugfix for inverter analysis
- 2022 August 22: v1.9.0.1 - add error for sheet resistance in TLM analysis as mouseover
- 2022 June 28: v1.9 - comply with Qt6
- 2022 April 22: v1.8.3.3 - changed the derivation method for inverter gain from centered to one sided gradient
- 2022 April 21: v1.8.3.2 - minor fixes, mostly for LabVIEW data reading and presentation
- 2022 April 01: v1.8.3.1 - minor adjustments, including Rsh in TLM_copy and forcing scientific notation for y axis in linear plots (e.g for output curves)
- 2022 March 23: v1.8.3 - fixed bugs with inverter: gain-derivative did contain nan values -> argmax() failed. columns in sweepme weren't read correctly if they varied by a number -> fixed VDS readout by regex for column determination
- 2022 March 17: v1.8.2 - changed SweepMe! expected columns (only for TLM analysis for now) to support files with resistance as well
- 2022 March 14: v1.8.1 - added options to choose linestyle in different plots (tab1, tab7 so far)
- 2022 March 08: v1.8.0 - added inverter analysis
- 2022 March 01: v1.7.3.2 - fix Arrhenius with Custom preset
- 2022 February 17: v1.7.3.1 - bugfixes in Custom preset, backend restructuring of settings tab, manual fit ranges as spinboxes
- 2022 February 08: v1.7.3 - added possibility to define file structure - not limited to the presets (SweepMe, LabVIEW, etc) anymore
- 2021 October 22: v1.7.2.3 - fix bug in 'fit_linear()' method where 'np.arange(50,-50,self.Vstepsize)' yields empty list if stepsize not negative
- 2021 October 11: v1.7.2.2 - add checkbox to save all relevant TLM plots automatically
- 2021 October 08: v1.7.2.1 - updated the explanation and about text of the main window
- 2021 September 30: v1.7.2 - restructure settings, change Vth find_nearest() method to -100V to 100V instead of 0V, set default names for all important plots
- 2021 September 29: v1.7.1 - add new Göttingen data structure and bugfix the TLM/Arrhenius analysis (errors introduced somewhere in 1.6 when fit_linear return values were restructured)
- 2021 September 17: v1.7 - release TLM direction from beta (Origin TLM uses only fwd!); new feature: plot all linear mobility fits, one at a time (similar to all TLM for respective overdrive voltage)
- 2021 September 10: v1.6.4.2 - corrected behavior of TLM analysis export to not duplicate datasets
- 2021 September 10: v1.6.4.1 - added beta version of TLM selection fwd/back/mean
- 2021 August 17: v1.6.4 - added comparison of L_1/2 = RcW/Rsh with TLM results -> second source of RcW value
- 2021 July 09: v1.6.3.2 - bugfix: TLM_copy_to_clipboard had issues with the lately introduced possibility of NaN values in SSw
- 2021 July 07: v1.6.3.1 - restructured the code (order of the functions being defined)
- 2021 July 05: v1.6.3 - fixed issue with drag&drop, and other file loading issues (file could be added more than once to e.g. TLM)
- 2021 July 02: v1.6.2 - slight updates in the TLM result rounding (how many digits are shown); not sure what I changed for the Arrhenius - tried temp-dep TLM plot, but gave up since it is not needed often
- 2021 June 29: v1.6.1 - some bugfixes (wrong units in Arrhenius plots etc)
- 2021 June 28: v1.6 - added Arrhenius analysis for temperature dependent TLM. not 100% done yet (no customization), but usable
- 2021 June 25: v1.5.1 - new version due to Sparameter is implemented; added support for Goettingen measurement files (was much more hassle than expected);added backbone for T-dependent (Arrhenius) analysis - not functional yet
- 2021 June 01: v1.4.13 - minor fixes (a few wrong characters etc)
- 2021 May 12: v1.4.12 - added simplified fT calculation and added it to settings.ini; fixed bug where "lin" or "sat" in the file path led to problems in transfer analysis
- 2021 May 11: v1.4.11 - added possibility to calculate fT based on Meyers capacitance model (see Eq. 57 in James Borchert's PhD thesis)
- 2021 April 28: v1.4.10 - implemented first working S-parameter analysis, this version can be viewed as v1.5rc; only slight adjustments/fixing errors while first real Sparameter measurements have to be done before going to v1.5 
- 2021 April 26: v1.4.9.2 - fixed Q-related messages at startup; introduced initial backbone for S-Parameter analysis in v1.5
- 2021 March 23: v1.4.9.1 - added a bit more concise debug output (command line)
- 2021 February 26: v1.4.9 - fix behavior with capital letters; added `ParameterAnalyzer` data preset; disabled manual setting of linearity restrictions within the subthreshold_swing extraction method (workaround) to circumvent issues with it during redo of TLMs
- 2021 February 24: v1.4.8.3 - added info about Python version which runs the program
- 2021 February 15: v1.4.8.2 - added warning in command line if wrong carrier type is selected, and tested PySide2 v5.15.2
- 2021 February 12: v1.4.8.1 - fixed `SSw` sign for n-type channel analysis
- 2021 February 09: v1.4.8 - changed behavior of `manualFitRanges` in the settings to also affect TLM tab
- 2021 February 08: v1.4.7 - added ability to drag&drop datafiles into TransferAnalysis and TLM tabs 
- 2021 January 28: v1.4.6.1 - added command line `print(version)`
- 2021 January 22: v1.4.6 - added plot for `SSw(L)`in the TLM tab
- 2021 January 18: v1.4.5 - added button to copy L, Vth and µ of transfer curves included in TLM to clipboard
- 2021 January 12: v1.4.4 - added default tab setting, changed the calculation of R*W to be oriented at the Vg step size instead of hardcoded
- 2021 January 07: v1.4.2 - changes to how TLM interacts with the first/second derivative constraints for the mobility fit (didn't work properly before and ignored perfectly fine datasets). updated SSW result label, has shown negative (opposite) values when n-type was selected - solution not elegant but rather a workaround!. since `mobility_fit()` is called far more often now, the TLM takes longer again - this is to be addressed later on 
- 2020 December 21: v1.4.1 - changed the TLM fit label to display in LaTeX style
- 2020 November 13: v1.4 - minor bugfixes (`V_ov` in TLM-Plot label was wrong with last update; there was an `print_exc()` statement which overloaded the CLI when a fit was unsuccessful)
major bugfix: TLM now correctly includes only overdrive voltages, for which each `L` has `RW` values. Consequence: no more hard steps in `RcW(Vg)` that occurred when the fit jumps from e.g. 8 `L` values to 3. `RcW` value in results sheet is slightly higher now, but more reliable/correct.
added setting to control the number of `RcW(Vg)` values averaged for the results sheet.
- 2020 November 09: v1.3 - added possibility for multiple datasets of the same channel length within TLM.
changed `TransferAnalysis` lin/sat fit plotting to linear only. Before it was influenced by the dropdown menu.
- 2020 November 06: v1.2 - replaced the determination of `l_0` and `Rc0W` with a recursive function, greatly reducing the runtime (2.4s instead of 3.5s)
changed the TLM plotting of all transfer curves from transparancy (`alpha!=1`) to a fixed color range with `alpha=1` to deal with overlapping curves. The color range can be redefined if the colors are an issue still.
Fixed the scaling for `µ(Vg)`-Plots in `TransferAnalysis` to linear, since logarithmic has no application there
- 2020 November 05: v1.1 - changed definition of On/Off ratio from `I[half:half-5]/I[5:0]` to `max(I)/min(I)` to fix an issue where the ratio was far smaller than it should be (low datapoint density -> real minimum/maximum was not inclueded). Also added `np.abs(I_max/I_min)`, because `np.log10` returned `np.nan` for a a negative value.
Added tooltips for datafiles in QComboBox in order to avoid truncation of long filenames. On Mouseover they will be displayed in full.
Added a user setting for On/Off ratio averaging range.
Added fit uncertainties as tooltips to the SSw, µ and Vth values (std_deviation from `curve_fit`).
Some code improvements in the tab1 results part to make it less messy.
- 2020 September 23: v1.0.1.1 - added README.md, versioning, roadmap
- 2020 August 13: v1.0.1 - updated TLM `Vth(L)` plot to not show absolute values anymore
- 2020 July 27: v1.0 - several bugfixes, fully usable version
- 2020 June 12: v.0.9.2 - implemented save settings
- 2020 May 23: v0.9 - first usable version able to deal with both SweepMe! and LabVIEW files. TransistorAnalysis, TLM and FunctionPlotter working

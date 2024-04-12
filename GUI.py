#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import platform
import sys
import time
from traceback import print_exc
import matplotlib
import json
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *

# This program was developed originally using PySide2 version 5.14.2;
# newer versions (e.g. 5.14.3) have shown errors importing DLL files. Later on development changed and 5.15.2 seems stable.
# If you experience issues, please make sure your PySide2 module matches version 5.14.2 or 5.15.2
# With GUI v1.9 the change to Qt6 has been made (PySide6). Please ensure this module is installed. However, version 6.5.0 showed an inputerror for the FigureCanvas. Make sure to use version 6.3.1, that one is sure to work!

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import cm
import matplotlib.pyplot as plt

try:
    from python_analysis_skript import *
except:
    print_exc()
    print(
        "Could not import the analysis module (python_analysis_skript.py). Please place it in the same directory as GUI.py if it is not there, otherwise look into the error.")

if platform.system() == "Windows":
    import ctypes  # needed in order for the app icon to display properly

    myappid = 'mpi.fkf.transistoranalysistool.wollandt'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

py_version = platform.python_version()
if sys.version_info[1] < 8: print(
    """This program was developed using Python 3.8.2
    From v1.9 on it uses Python 3.10.5. If you experience issues, please make sure your Python version is newer than that and your packages are up to date.""")
if sys.version_info[0] < 3: raise Exception("Python 3 or a more recent version is required.")
matplotlib.use("Qt5Agg")

program_version = "Program Version: 1.9.7.1 (Date: 14.11.2023)"
author = "Tobias Wollandt"
affiliation = "MPI-FKF"
author_mail = "T.Wollandt@fkf.mpg.de"
print(f"Transistor Analysis Tool {program_version} is currently run with Python v{py_version}. Author: {author} ({affiliation}). Contact: {author_mail}.")
t0 = time.time()
class PlottingEnvironment_Canvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=8, dpi=1000,sizePolicy=None):
        self.fig = Figure(figsize=(width, height),
                     dpi=dpi,
                     tight_layout=True,
                     # constrained_layout=True
                     )
        FigureCanvas.__init__(self, self.fig)
        self.axes = self.fig.add_subplot(111)
        self.empty = True
        self.absolute = True
        self.setParent(parent)

        if sizePolicy==None:
            FigureCanvas.setSizePolicy(self, QSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding))
        else: FigureCanvas.setSizePolicy(self,sizePolicy)
        FigureCanvas.updateGeometry(self)

    def save(self,path = None):
        if path is None:
            return False
        else:
            try:
                plt.tight_layout()
                self.fig.savefig(path, dpi=2*self.fig.dpi)
            except:
                print_exc()
                return False


    def clear(self):
        self.axes.clear()
        self.empty = True
        self.draw()

    def show(self):
        self.draw()

    def setCmap(self, cmap):
        from cycler import cycler
        self.axes.set_prop_cycle(cycler('color', cm.get_cmap('Spectral')))

    def set_absolute_plotting(self, bool):
        # MyTableWidget.print_useroutput(f"absolute plotting {'enabled' if bool else 'disabled'}",MyTableWidget.tab4_outputline)
        self.absolute = bool
        return True

    def plot_new(self, func, par, scale, x, indep_var='x'):
        print(f'func={func}\tpar={par}\tscale={scale}')
        self.axes.clear()

        def identify_parameter_names(funcstr, independent):
            p = []
            funcstr = funcstr.replace(r"\s", '')
            for p_ in re.sub('[ ?!/;:*+()\-]', ',', funcstr).split(','):
                if (p_ not in ['', independent]) and ('np' not in p_):
                    try:
                        z_ = float(p_)
                    except:
                        p.append(p_)
            ps_sorted = sorted(p, key=len, reverse=True)
            print(f'parameter_names_sorted = {ps_sorted}')
            return ps_sorted

        def replace_parameter_values(func, par_):
            func_pattern = r"np.\w+"
            s = list(set(re.findall(func_pattern, func)))

            s__ = []
            for i in range(len(s)):
                exec(f's__.append("_{i}_")', locals())

            for idx, val in enumerate(s__):
                func = func.replace(s[idx], val)

            for p in parameters_needed:
                func = func.replace(p, str(par_[p]))

            for idx, val in enumerate(s__):
                func = func.replace(val, s[idx])

            return func

        parameters_needed = identify_parameter_names(
            func, indep_var)  # parameters essential to the formula

        for p in parameters_needed:
            if p not in par:
                print(f"Value for parameter {p} not assigned!")

        func = replace_parameter_values(func, par)
        func_str = "y = " + func
        exec(func_str, locals(), globals())
        # the following line is there only so PyCharm doesn't show an error - I have no idea why this is an issue
        if ('y' not in locals()) and ('y' not in globals()):
            y = x
        else:
            # not sure what this else statement does...without, it says "local variable y might be ref'd before assignm"
            y = x
        self.axes.plot(x, y)
        self.axes.set_yscale(scale[1])
        self.axes.set_xscale(scale[0])
        self.draw()

    def plot_data(self, x, y, scale, overwrite, yerror=None, xerror=None, xlabel="", ylabel="", label="", marker="", linestyle='-',
                  alpha=1, color=None, lastplot=False, absolute=None, ylim=None, sci=True):
        # global plot_in_abs
        if scale[0] == 'log':
            x = np.abs(x)
        if scale[1] == 'log':
            y = np.abs(y)
        if overwrite:
            self.axes.clear()
        # if plot_in_abs: y = np.abs(y)
        if self.absolute is True and (absolute is None or absolute is True): y = np.abs(y)

        if (yerror is None) and (xerror is None):
            self.axes.plot(x, y, label=label, marker=marker, linestyle=linestyle, alpha=alpha, color=color)
        elif (xerror is None) and (yerror is not None):
            self.axes.errorbar(x, y, yerr=np.abs(yerror), label=label, marker=marker, linestyle=linestyle,
                               markerfacecolor='none', elinewidth=1, capsize=1.5, capthick=1)
        elif (xerror is not None) and (yerror is not None):
            self.axes.errorbar(x, y, xerr=np.abs(xerror), yerr=np.abs(yerror), label=label, marker=marker, linestyle=linestyle,
                               markerfacecolor='none', elinewidth=1, capsize=1.5, capthick=1)

        self.axes.set_yscale(scale[1])
        self.axes.set_xscale(scale[0])
        if (scale[1]=="linear") and (sci==True): self.axes.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
        if len(ylabel) > 0: self.axes.set_ylabel(ylabel)
        if len(xlabel) > 0: self.axes.set_xlabel(xlabel)
        if len(label) > 0: self.axes.legend()
        if not ylim is None: self.axes.set_ylim(ylim)
        if lastplot: self.empty = False; self.draw()


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.table_widget = MyTableWidget(self)
        self.title = 'TobisFitWindow'
        self.left = 0
        self.top = 0
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon('program_icon.png'))

        self.setCentralWidget(self.table_widget)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL | QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        expl = self.help_menu.addMenu('&Explanation')
        expl.addAction('Transfer Analysis', self.explain_ta)
        expl.addAction('TLM', self.explain_tlm)
        expl.addAction('S-Parameter', self.explain_sparam)
        expl.addAction('Arrhenius', self.explain_arrhenius)
        expl.addAction('Function Plotter', self.explain_fp)
        self.help_menu.addAction('&About', self.about)

        self.show()

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QMessageBox.about(self, "About",
            f"""
            <p>You are currently running {program_version} with the Python v{py_version} that is installed
            on your computer.</p><p>This program was written as an extension and replacement for an old Origin script to analyze transfer
            data acquired from organic TFTs.<br/>Reason for this was that the author loves Python and despises Origin for some
            reason, and after he recreated the functionality as command line tool, he was eager to write it up as GUI for
            others to use.<br/>The author acknowdleges that while it is a very useful tool, it took quite some time
            to develop and it is not to be viewed as the most efficient use of time. He had fun programming this and starting
            over would probably make the code a lot cleaner. It was a useful exercise and learning experience to build
            up the whole program step by step with as little module imports as possible. The author hopes the program
            can be of use to many other people and someone might even take over the development should problems arise
            or new analysis possibilities become available.</p>
            <p>Author: {author}<br/>Contact: <a href=mailto:{author_mail}>{author_mail}</a></p>"""
                          )

    def explain_ta(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Details about the Transfer Analysis')
        msg.setText(
            "<p>This window gives an overview over the functionality of the <strong>Transfer Analysis</strong> tab.</p>")
        msg.setInformativeText("""
            <p>The tool consists of 3 main functions that serve the purpose of extracting and displaying the main
            features/characteristics of a given transistor transfer dataset:</p>
            <p>1.) Loading data files from the filesystem. The <strong>Choose Files</strong> button opens a window where the
            desired files can be chosen - this can be done subsequently and more files can be added to the saved list which 
            is displayed besides the button. The <strong>Empty List</strong> button erases the list of saved files
            and resets all selections that are dependent on the given dataset(s).<br/>
            If only one file is selected, it will be automatically loaded into the plot data selection - if more
            are selected, the user has to choose the dataset to plot.</p>
            <p>2.) Plotting a datafile. All the files selected previously are listed and one can be chosen for plotting.
            Make sure the right preset for the data is chosen (check in the Settings tab)! Available columns are displayed
            if the file could be read. Since the main purpose is transistor analysis, the standard selection is V_GS vs I_DS.
            The scaling for the plot can also be selected, standard selection is semilogy. The <strong>Overwrite Plot</strong>
            prompt determines whether the content of the plot window will be erased before plotting the new dataset.
            The default Matplotlib Navigation bar is available and has full functionality such as changing linestyles, zooming, etc.</p>
            <p>3.) Analyzing the transfer data. The crucial parameters (<i>C_ox</i>, <i>W</i>, <i>L</i>) for calculations
            can be changed by the user. Default settings are extracted from the filename if possible.<br/>
            The uncertainties of extracted values are shown as mouseovers.</p>""")
        msg.exec_()

    def explain_fp(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Details about the Function Plotter')
        msg.setText(
            "<p>This window gives an overview over the functionality of the <strong>Function Plotter</strong> tab.</p>")
        msg.setInformativeText(
            """<p>This tool gives the user the ability to define a custom function (in accordance with the Python syntax,
            using numpy as np for functions like sin, cos etc.). The function can take parameters which have to be
            defined in order to work.</p><p>The setup of the plotting environment includes setting the range of <i>x</i>
            (custom independent variables are planned, for now: only <i>x</i> is possible). The scaling can be changed on
            the fly and it automatically updates the plot, given that a valid function is already defined.
            The <strong>Overwrite Plot</strong> prompt determines whether the figure will be erased before plotting the new function.
            </p><p>All parameters used in the plot equation must be defined in the <strong>Parameter Assignment</strong> window.
            This list can contain parameters that are not used, they will be ignored.""")
        msg.exec_()

    def explain_tlm(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Details about the Transmission Line Method (TLM)')
        msg.setText(
            "<p>This window gives an overview over the functionality of the <strong>TLM</strong> tab.</p>")
        msg.setInformativeText(
            """<p>For further information about the method refer to <a href=https://doi.org/10.1016/j.mattod.2014.08.037>this paper</a>.<br/>
            Short version:<br/>
            <i>R</i><sub>total</sub> = <i>R</i><sub>channel</sub> + <i>R</i><sub>contact</sub><br/>
            Using different channel lengths, the channel resistance can be changed and subsequently extrapolated to <i>L</i> = 0
            where only the contact resistance remains.
            </p>
            <p>The extraction of contact resistance via TLM is widely used practice. This part of the GUI gives the
            possibility to analyze a complete set of TLM data (more than 3 channel lengths are needed). Make sure the correct
            data preset is chosen in the <strong>Settings</strong> tab and the type of transistor fits the data, otherwise errors will occur.</p>
            <p>Uncertainties and larger accuracy of the fitting values are given as mouseover information.</p>
            <p>Before this GUI there was an Origin script extracting all the values, that version also used an automated fit
            to extract the threshold voltage from the derivative of the linear curve, and therefore the overdrive voltage.
            Besides the runtime, a striking difference is that this script allows for the choice of fwd/back/mean data
            instead of hardcoded using the forward sweep.</p>
            <p>Data can be exported to an excel file with the analyzed data and all the raw data is given in a single file.</p>
            """)
        msg.exec_()

    def explain_sparam(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Details about the S-Parameter extraction')
        msg.setText(
            "<p>This window gives an overview over the functionality of the <strong>S-Parameter</strong> tab.</p>")
        msg.setInformativeText(
            """<p>To be honest, I know not that much about S-Parameter measurements and analysis. I made sure
            that the code reproduces results from old samples. Refer to
            <a href=https://doi.org/10.1038/s41467-020-18616-0>this paper</a> for further information.</p>""")
        msg.exec_()

    def explain_arrhenius(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Details about the Arrhenius analysis (temperature-dependence)')
        msg.setText(
            "<p>This window gives an overview over the functionality of the <strong>Arrhenius</strong> tab.</p>")
        msg.setInformativeText(
            """<p>From the temperature dependence of the contact resistance and intrinsic mobility the Schottky barrier
            and the activation energy in the multiple-trapping-and-release (MTR) model can be extracted, respectively.</p>
            <p>For this analysis to work there is a complete set of TLM for several temperatures needed. So far only the
            TLM are analyzed for eath temperature and plotted, no fit is done automatically and needs to be done manually
            for now. Not sure if it is worth the time to add this automatically, given how seldom this measurement will
            probably be done.</p>""")
        msg.exec_()


class MyTableWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.root_widget = QWidget(self)
        self.root_layout = QVBoxLayout(self.root_widget)
        self.setAcceptDrops(True) # for drag&drop files into filelists
        self.platform = platform.system()

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()
        self.tab6 = QWidget()
        self.tab7 = QWidget()

        # Add tabs
        self.tabs.addTab(self.tab1, "Transfer Analysis")
        self.tabs.addTab(self.tab3, "Transmission Line Method")
        self.tabs.addTab(self.tab5, "S-Parameters")
        self.tabs.addTab(self.tab6, "Arrhenius")
        self.tabs.addTab(self.tab7, "Inverter Analysis")
        self.tabs.addTab(self.tab4, "Settings")
        self.tabs.addTab(self.tab2, "Function Plotter")
        self.tabs.setCurrentIndex(0)
        # Create first tab
        self.tab1.layout = QVBoxLayout(self.tab1)
        self.tab2.layout = QVBoxLayout(self.tab2)
        self.tab3.layout = QVBoxLayout(self.tab3)
        self.tab4.layout = QVBoxLayout(self.tab4)
        self.tab5.layout = QVBoxLayout(self.tab5)
        self.tab6.layout = QVBoxLayout(self.tab6)
        self.tab7.layout = QVBoxLayout(self.tab7)

        # the sole purpose of the function-structure for the tabs is that the code is foldable in editors, for quick access
        # tab1 contains everything needed to plot a certain dataset and/or do transistor analysis on it
        # for documentation, see the context menu in the "Help" section of the GUI
        def initialize_tab1():
            # set the default directory for choosing files in tab1
            self.default_directory_tab1 = 'C:/Users/wollandt_admin/MPI_Cloud/data/TW_samples/TW099/a/TLM'

            # create top layout of the transistor analysis tab
            # left part is used as a data pool from which data for plotting and/or analysis can be chosen
            # right part defines the plotting environment (only the scaling is considered in the analysis-plots)
            self.tab1_file_selection_layout = QHBoxLayout()

            self.tab1_choose_files_button = QPushButton('Choose Files')
            self.tab1_choose_files_button.clicked.connect(self.choose_files)
            self.tab1_remove_file_from_list_button = QPushButton('Remove File')
            self.tab1_remove_file_from_list_button.clicked.connect(self.remove_transistoranalysis_item)
            self.tab1_empty_filelist_button = QPushButton('Empty List')
            self.tab1_empty_filelist_button.clicked.connect(self.empty_file_list)

            # the program is not displaying whole paths but solely filenames. for reading the data, the whole
            # path is needed, so they have to be stored in combination -> this dictionary holds the references and
            # the QListWidget holds the filenames for the user to choose from in a clean fashion
            self.tab1_file_paths_dictionary = {}  # filename:path
            self.tab1_file_list = QListWidget(minimumHeight=25, maximumHeight=80, minimumWidth=50)
            self.tab1_file_list.currentRowChanged.connect(self.read_columnnames)

            # set up left side of the top file selection part
            self.tab1_filelist_layout = QVBoxLayout()
            self.tab1_filelist_buttons = QHBoxLayout()
            self.tab1_filelist_buttons.addWidget(self.tab1_choose_files_button)
            self.tab1_filelist_buttons.addWidget(self.tab1_empty_filelist_button)
            self.tab1_filelist_buttons.addWidget(self.tab1_remove_file_from_list_button)
            self.tab1_filelist_layout.addLayout(self.tab1_filelist_buttons)
            self.tab1_filelist_layout.addWidget(self.tab1_file_list)
            self.tab1_file_selection_layout.addLayout(self.tab1_filelist_layout)

            # define objects to go into the top right (plot selection) part
            self.tab1_plot_file_choose_xdata_combobox = QComboBox(minimumWidth=100,
                                                                  sizePolicy=QSizePolicy(QSizePolicy.Expanding,
                                                                                         QSizePolicy.Preferred))
            self.tab1_plot_file_choose_xdata_combobox.addItem('None')
            self.tab1_plot_file_choose_ydata_combobox = QComboBox(minimumWidth=100,
                                                                  sizePolicy=QSizePolicy(QSizePolicy.Expanding,
                                                                                         QSizePolicy.Preferred))
            self.tab1_plot_file_choose_ydata_combobox.addItem('None')

            self.tab1_plot_chosen_data_label = QLineEdit(placeholderText="Enter plotting label")
            self.tab1_plot_scale_menu = QComboBox()
            self.tab1_plot_scale_menu.addItem('Linear (x&y)')
            self.tab1_plot_scale_menu.addItem('SemiLog (y)')
            self.tab1_plot_scale_menu.addItem('LogLog (x&y)')
            self.tab1_plot_scale_menu.setCurrentIndex(0)
            self.tab1_plot_scale_menu.currentIndexChanged.connect(self.plot_chosen_data)

            self.tab1_plot_chosen_data_button = QPushButton('Plot Data', minimumWidth=150)
            self.tab1_plot_chosen_data_button.clicked.connect(self.plot_chosen_data)
            self.tab1_plot_chosen_data_overwrite_checkbox = QCheckBox('Overwrite')
            self.tab1_plot_chosen_data_overwrite_checkbox.setChecked(True)
            self.tab1_choose_linestyle = QComboBox()
            self.tab1_choose_linestyle.addItems(['.', 'o', 'x', '.-', 'o-', 'x-', '-', '--'])
            self.tab1_linestyle_layout = QHBoxLayout()
            self.tab1_linestyle_layout.addWidget(QLabel('Linestyle'))
            self.tab1_linestyle_layout.addWidget(self.tab1_choose_linestyle)

            # set up right side of the top part (choosing data for plotting)
            self.tab1_plot_file_setup_layout = QGridLayout()
            self.tab1_plot_file_setup_layout.addWidget(QLabel('x'),                                 0, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_plot_file_setup_layout.addWidget(QLabel('y'),                                 1, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_plot_file_setup_layout.addWidget(QLabel('Label'),                             0, 2, alignment=QtCore.Qt.AlignRight)
            self.tab1_plot_file_setup_layout.addWidget(QLabel('Scaling'),                           1, 2, alignment=QtCore.Qt.AlignRight)
            self.tab1_plot_file_setup_layout.addWidget(self.tab1_plot_file_choose_xdata_combobox,   0, 1,
                                                       alignment=QtCore.Qt.AlignLeft)
            self.tab1_plot_file_setup_layout.addWidget(self.tab1_plot_file_choose_ydata_combobox,   1, 1,
                                                       alignment=QtCore.Qt.AlignLeft)
            self.tab1_plot_file_setup_layout.addWidget(self.tab1_plot_chosen_data_label,            0, 3,
                                                       alignment=QtCore.Qt.AlignLeft)
            self.tab1_plot_file_setup_layout.addWidget(self.tab1_plot_scale_menu,                   1, 3,
                                                       alignment=QtCore.Qt.AlignLeft)
            self.tab1_plot_file_setup_layout.addWidget(self.tab1_plot_chosen_data_button,           2, 0, 1, 2,
                                                       alignment=QtCore.Qt.AlignRight)
            self.tab1_plot_file_setup_layout.addWidget(self.tab1_plot_chosen_data_overwrite_checkbox, 2, 2,
                                                       alignment=QtCore.Qt.AlignLeft)
            self.tab1_plot_file_setup_layout.addLayout(self.tab1_linestyle_layout,                  2,3)


            self.tab1_file_selection_layout.addLayout(self.tab1_plot_file_setup_layout)
            self.tab1.layout.addLayout(self.tab1_file_selection_layout)

            ####################################################################################
            # initializing the bottom left side of the window
            # here all (most) necessary settings that are needed for the fitting can be changed
            self.tab1_analysis_and_plots_layout = QHBoxLayout()
            self.tab1_analysis_setup_and_results_layout = QVBoxLayout()

            self.tab1_analysis_setup_layout = QGridLayout()
            self.tab1_fitsetup_dimensions = QHBoxLayout()
            self.tab1_channel_width = QLineEdit(placeholderText="---", maximumWidth=50)
            self.tab1_channel_length = QLineEdit(placeholderText="---", maximumWidth=50)
            self.tab1_linear_VDS_input = QLineEdit(placeholderText="---", maximumWidth=50)
            self.tab1_carrier_type_button = QPushButton("p", maximumWidth=25, checkable=True)
            self.tab1_carrier_type_button.clicked.connect(self.update_carrier_type_button_text)
            self.tab1_fitsetup_dimensions.addWidget(QLabel("W [µm]"), alignment=QtCore.Qt.AlignRight)
            self.tab1_fitsetup_dimensions.addWidget(self.tab1_channel_width, alignment=QtCore.Qt.AlignLeft)
            self.tab1_fitsetup_dimensions.addWidget(QLabel("L [µm]"), alignment=QtCore.Qt.AlignRight)
            self.tab1_fitsetup_dimensions.addWidget(self.tab1_channel_length, alignment=QtCore.Qt.AlignLeft)
            self.tab1_fitsetup_dimensions.addWidget(QLabel("V<sub>DS</sub> [V]"), alignment=QtCore.Qt.AlignRight)
            self.tab1_fitsetup_dimensions.addWidget(self.tab1_linear_VDS_input, alignment=QtCore.Qt.AlignLeft)
            self.tab1_fitsetup_dimensions.addWidget(QLabel("Type"), alignment=QtCore.Qt.AlignRight)
            self.tab1_fitsetup_dimensions.addWidget(self.tab1_carrier_type_button, alignment=QtCore.Qt.AlignLeft)

            self.tab1_choose_files_for_fit_layout = QGridLayout()
            self.tab1_analysis_choose_lin_data_combobox = QComboBox()
            self.tab1_analysis_choose_lin_data_combobox.addItem('None')
            self.tab1_analysis_choose_sat_data_combobox = QComboBox()
            self.tab1_analysis_choose_sat_data_combobox.addItem('None')
            self.tab1_analysis_choose_sat_data_combobox.setFixedWidth(250)
            self.tab1_analysis_choose_lin_data_combobox.setFixedWidth(250)
            self.tab1_analysis_choose_sat_data_combobox.currentIndexChanged.connect(
                self.determine_transistor_characteristics)
            self.tab1_analysis_choose_lin_data_combobox.currentIndexChanged.connect(
                self.determine_transistor_characteristics)
            self.tab1_choose_files_for_fit_layout.addWidget(QLabel('Lin.:', maximumWidth=50), 0, 0,
                                                            alignment=QtCore.Qt.AlignRight)
            self.tab1_choose_files_for_fit_layout.addWidget(QLabel('Sat.:', maximumWidth=50), 1, 0,
                                                            alignment=QtCore.Qt.AlignRight)
            self.tab1_choose_files_for_fit_layout.addWidget(self.tab1_analysis_choose_lin_data_combobox, 0, 1,
                                                            alignment=QtCore.Qt.AlignLeft)
            self.tab1_choose_files_for_fit_layout.addWidget(self.tab1_analysis_choose_sat_data_combobox, 1, 1,
                                                            alignment=QtCore.Qt.AlignLeft)

            self.tab1_analysis_capacitance_input = QDoubleSpinBox(value=0.65, singleStep=0.01, minimum=0.00,
                                                                  maximum=5.00)
            self.tab1_analysis_first_derivative_threshold_input = QDoubleSpinBox(  # value=0.75,
                singleStep=0.01, minimum=0.00, maximum=1.00)
            self.tab1_analysis_second_derivative_threshold_input = QDoubleSpinBox(  # value=0.35,
                singleStep=0.01, minimum=0.00, maximum=1.00)
            self.tab1_analysis_smoothing_factor = QDoubleSpinBox(value=0.25,
                                                                 singleStep=0.01, minimum=0.00, maximum=1.00)
            fi_x, fi_y = 60, 20  # fixed x an y size for spinboxes
            self.tab1_analysis_capacitance_input.setFixedSize(fi_x, fi_y)
            self.tab1_analysis_first_derivative_threshold_input.setFixedSize(fi_x, fi_y)
            self.tab1_analysis_second_derivative_threshold_input.setFixedSize(fi_x, fi_y)
            self.tab1_analysis_smoothing_factor.setFixedSize(fi_x, fi_y)
            # anytime the value of first derivative (fd) or second derivative (sd) is changed, the analysis should be
            # redone in order to see the changes in included datapoints directly. non-essential functionality!
            self.tab1_analysis_first_derivative_threshold_input.valueChanged.connect(self.analyze_transfer_data)
            self.tab1_analysis_second_derivative_threshold_input.valueChanged.connect(self.analyze_transfer_data)
            self.tab1_analysis_smoothing_factor.valueChanged.connect(self.analyze_transfer_data)

            self.tab1_analysis_setup_layout.addWidget(QLabel('Dielectric Capacitance [µF/cm²]:'), 0, 0,
                                                      alignment=QtCore.Qt.AlignRight)
            self.tab1_analysis_setup_layout.addWidget(self.hline(), 2, 0, 1, 2)
            self.tab1_analysis_setup_layout.addWidget(QLabel('Fit-Data Identification - dI/dV (norm.):',
                                                             toolTip="""<p>This value sets the lower limit to the normalized (1st) derivative,
                                                             above which datapoints are considered in the linear regime.<br>
                                                             If value is 0, the analysis routine will try to determine an appropriate value.</p>"""),
                                                      3, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_analysis_setup_layout.addWidget(QLabel('Fit-Data Identification - d²I/dV² (norm.):',
                                                             toolTip="""<p>This value sets the upper limit to the normalized (2nd) derivative,
                                                             below which datapoints are considered in the linear regime.<br>
                                                             If value is 0, the analysis routine will try to determine an appropriate value.</p>"""),
                                                      4, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_analysis_setup_layout.addWidget(QLabel('Smoothing Factor (Gaussian σ):',
                                                             toolTip="""<p>Data is smoothed to reduce artifacts during derivation.
                                                             This value is used as standard deviation in the gaussian broadening kernel.<br>
                                                             This value does NOT change fitting results, it only influences the automatic
                                                             determination of points to include in the fit (visible in the plots)!<br>
                                                             The original data values used in the fit are not altered/compromised by the smoothing!</p>"""),
                                                      5, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_analysis_setup_layout.addWidget(self.tab1_analysis_capacitance_input, 0, 1,
                                                      alignment=QtCore.Qt.AlignRight)
            self.tab1_analysis_setup_layout.addWidget(self.tab1_analysis_first_derivative_threshold_input, 3, 1,
                                                      alignment=QtCore.Qt.AlignRight)
            self.tab1_analysis_setup_layout.addWidget(self.tab1_analysis_second_derivative_threshold_input, 4, 1,
                                                      alignment=QtCore.Qt.AlignRight)
            self.tab1_analysis_setup_layout.addWidget(self.tab1_analysis_smoothing_factor, 5, 1,
                                                      alignment=QtCore.Qt.AlignRight)

            self.tab1_resultlayout = QGridLayout()
            self.tab1_resultemptybutton = QPushButton('Empty')
            self.tab1_resultemptybutton.clicked.connect(self.empty_analysis_results)

            self.tab1_results_choose_oor_regime = QPushButton('On-Off Ratio (sat.)', checkable=True)
            self.tab1_results_choose_ssw_regime = QPushButton('Subthr. Swing (lin.)', checkable=True)
            self.tab1_results_choose_vth_regime = QPushButton('Threshold Voltage (lin.)', checkable=True)
            self.tab1_results_choose_oor_regime.clicked.connect(self.update_choose_regime_buttons_text)
            self.tab1_results_choose_ssw_regime.clicked.connect(self.update_choose_regime_buttons_text)
            self.tab1_results_choose_vth_regime.clicked.connect(self.update_choose_regime_buttons_text)

            self.tab1_resultlayout.addWidget(self.tab1_results_choose_oor_regime,   0, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_resultlayout.addWidget(self.tab1_results_choose_ssw_regime,   1, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_resultlayout.addWidget(QLabel('Mobility (linear) µ'),         2, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_resultlayout.addWidget(QLabel('Mobility (saturation) µ'),     3, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_resultlayout.addWidget(self.tab1_results_choose_vth_regime,   4, 0, alignment=QtCore.Qt.AlignRight)
            self.tab1_resultlayout.addWidget(QLabel('Reliability (lin./sat.) r', openExternalLinks=True), 5, 0,
                                             alignment=QtCore.Qt.AlignRight)
            self.tab1_result_onoff = QLineEdit(readOnly=True, placeholderText="---")
            self.tab1_result_ssw = QLineEdit(readOnly=True, placeholderText="---")
            self.tab1_result_mulin = QLineEdit(readOnly=True, placeholderText="---")
            self.tab1_result_musat = QLineEdit(readOnly=True, placeholderText="---")
            self.tab1_result_vth = QLineEdit(readOnly=True, placeholderText="---")
            self.tab1_result_reliability = QLineEdit(readOnly=True, placeholderText="---/---")
            rs_x, rs_y = 80, 20
            self.tab1_result_onoff.setFixedSize(rs_x, rs_y)
            self.tab1_result_ssw.setFixedSize(rs_x, rs_y)
            self.tab1_result_mulin.setFixedSize(rs_x, rs_y)
            self.tab1_result_musat.setFixedSize(rs_x, rs_y)
            self.tab1_result_vth.setFixedSize(rs_x, rs_y)
            self.tab1_result_reliability.setFixedSize(rs_x, rs_y)
            self.tab1_resultshowfwd = QRadioButton("Forward")
            self.tab1_resultshowback = QRadioButton("Backward")
            self.tab1_resultshowmean = QRadioButton("Mean", checked=True)
            # pressed instead of toggled does not properly change the state of the radiobutton (since
            # a "press release" is expected).
            # with "pressed" you need to push either the radiobutton or the "Analyze" button again for it to work
            self.tab1_resultshowfwd.toggled.connect(self.analyze_transfer_data)
            self.tab1_resultshowback.toggled.connect(self.analyze_transfer_data)
            self.tab1_resultshowmean.toggled.connect(self.analyze_transfer_data)


            # add everything to the results layout
            self.tab1_resultlayout.addWidget(self.tab1_result_onoff,                0, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_result_ssw,                  1, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_result_mulin,                2, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_result_musat,                3, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_result_vth,                  4, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_result_reliability,          5, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_resultemptybutton,           0, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(QLabel('mV/dec'),                      1, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(QLabel('cm²/Vs'),                      2, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(QLabel('cm²/Vs'),                      3, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(QLabel('V'),                           4, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(
                QLabel('<a href=\"http://dx.doi.org/10.1038/nmat5035\" style=\"color:#606060;\">(details)</a>',
                       openExternalLinks=True),                                     5, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_resultshowfwd,               6, 0, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_resultshowback,              6, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab1_resultlayout.addWidget(self.tab1_resultshowmean,              6, 2, alignment=QtCore.Qt.AlignLeft)

            self.tab1_analyzebutton = QPushButton('Analyze')
            self.tab1_analyzebutton.clicked.connect(self.analyze_transfer_data)
            self.tab1_linear_fit_data_for_export = pd.DataFrame()
            self.tab1_saturation_fit_data_for_export = pd.DataFrame()
            self.tab1_export_layout = QHBoxLayout()
            self.tab1_export_filename = QLineEdit(placeholderText="Enter Filename for Export")
            self.tab1_export_data_button = QPushButton('Export Data / Results')
            self.tab1_export_data_button.clicked.connect(self.analyze_transfer_export_data)
            self.tab1_export_layout.addWidget(self.tab1_export_filename)
            self.tab1_export_layout.addWidget(self.tab1_export_data_button)

            # add everything to the bottom left part layout
            self.tab1_analysis_setup_and_results_layout.addWidget(QLabel('Fit Setup'))
            self.tab1_analysis_setup_and_results_layout.addLayout(self.tab1_fitsetup_dimensions)
            self.tab1_analysis_setup_and_results_layout.addLayout(self.tab1_choose_files_for_fit_layout)
            self.tab1_analysis_setup_and_results_layout.addLayout(self.tab1_analysis_setup_layout)
            self.tab1_analysis_setup_and_results_layout.addWidget(self.hline())
            self.tab1_analysis_setup_and_results_layout.addLayout(self.tab1_resultlayout)
            self.tab1_analysis_setup_and_results_layout.addWidget(QLabel("Analysis does not yet support automated L correction"))
            self.tab1_analysis_setup_and_results_layout.addWidget(self.tab1_analyzebutton)
            self.tab1_analysis_setup_and_results_layout.addLayout(self.tab1_export_layout)

            ####################################################################################
            # create data and analysis result graphing region
            # each tab needs to contain an individual matplotlib toolbar and a canvas which need to be contained withing
            # a layout that only belongs to the certain graph tab. this is initialized in code blocks below
            tabs_sizepolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.tab1_plotting_tabs = QTabWidget(sizePolicy=tabs_sizepolicy)
            self.tab1_plotting_data_tab = QWidget(sizePolicy=tabs_sizepolicy)
            self.tab1_plotting_linfit_tab = QWidget(sizePolicy=tabs_sizepolicy)
            self.tab1_plotting_satfit_tab = QWidget(sizePolicy=tabs_sizepolicy)
            self.tab1_plotting_muvglin_tab = QWidget(sizePolicy=tabs_sizepolicy)
            self.tab1_plotting_muvgsat_tab = QWidget(sizePolicy=tabs_sizepolicy)
            self.tab1_plotting_ssw_tab = QWidget(sizePolicy=tabs_sizepolicy)
            self.tab1_plotting_tabs.addTab(self.tab1_plotting_data_tab, "Data")
            self.tab1_plotting_tabs.addTab(self.tab1_plotting_linfit_tab, "Lin. Fit")
            self.tab1_plotting_tabs.addTab(self.tab1_plotting_satfit_tab, "Sat. Fit")
            self.tab1_plotting_tabs.addTab(self.tab1_plotting_muvglin_tab, "µ(Vg,Lin)")
            self.tab1_plotting_tabs.addTab(self.tab1_plotting_muvgsat_tab, "µ(Vg,Sat)")
            self.tab1_plotting_tabs.addTab(self.tab1_plotting_ssw_tab, "Subth.Sw.")
            self.tab1_plotting_data_tab.layout = QVBoxLayout(self.tab1_plotting_data_tab)
            self.tab1_plotting_linfit_tab.layout = QVBoxLayout(self.tab1_plotting_linfit_tab)
            self.tab1_plotting_satfit_tab.layout = QVBoxLayout(self.tab1_plotting_satfit_tab)
            self.tab1_plotting_muvglin_tab.layout = QVBoxLayout(self.tab1_plotting_muvglin_tab)
            self.tab1_plotting_muvgsat_tab.layout = QVBoxLayout(self.tab1_plotting_muvgsat_tab)
            self.tab1_plotting_ssw_tab.layout = QVBoxLayout(self.tab1_plotting_ssw_tab)

            canvas_width, canvas_height, canvas_dpi, canvas_min_height, canvas_min_width, canvas_sizepolicy = 4, 3, 100, 300, 300, QSizePolicy(
                QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.tab1_plot_canvas_dataset = PlottingEnvironment_Canvas(self.tab1, width=canvas_width,
                                                                       height=canvas_height, dpi=canvas_dpi, sizePolicy=canvas_sizepolicy)
            self.tab1_plot_canvas_dataset.setMinimumHeight(canvas_min_height)
            self.tab1_plot_canvas_dataset.setMinimumWidth(canvas_min_width)
            self.tab1_toolbar = NavigationToolbar(self.tab1_plot_canvas_dataset, self)
            self.tab1_plotting_data_tab.layout.addWidget(self.tab1_toolbar, alignment=QtCore.Qt.AlignLeft)
            self.tab1_plotting_data_tab.layout.addWidget(self.tab1_plot_canvas_dataset, alignment=QtCore.Qt.AlignLeft)

            self.tab1_plot_canvas_linfit = PlottingEnvironment_Canvas(self.tab1, width=canvas_width,
                                                                      height=canvas_height, dpi=canvas_dpi)
            self.tab1_plot_canvas_linfit.setMinimumHeight(canvas_min_height)
            self.tab1_plot_canvas_linfit.setMinimumWidth(canvas_min_width)
            self.tab1_toolbar_linfit = NavigationToolbar(self.tab1_plot_canvas_linfit, self)
            self.tab1_plotting_linfit_tab.layout.addWidget(self.tab1_toolbar_linfit, alignment=QtCore.Qt.AlignLeft)
            self.tab1_plotting_linfit_tab.layout.addWidget(self.tab1_plot_canvas_linfit, alignment=QtCore.Qt.AlignLeft)

            self.tab1_plot_canvas_satfit = PlottingEnvironment_Canvas(self.tab1, width=canvas_width,
                                                                      height=canvas_height, dpi=canvas_dpi, sizePolicy=canvas_sizepolicy)
            self.tab1_plot_canvas_satfit.setMinimumHeight(canvas_min_height)
            self.tab1_plot_canvas_satfit.setMinimumWidth(canvas_min_width)
            self.tab1_toolbar_satfit = NavigationToolbar(self.tab1_plot_canvas_satfit, self)
            self.tab1_plotting_satfit_tab.layout.addWidget(self.tab1_toolbar_satfit, alignment=QtCore.Qt.AlignLeft)
            self.tab1_plotting_satfit_tab.layout.addWidget(self.tab1_plot_canvas_satfit, alignment=QtCore.Qt.AlignLeft)

            self.tab1_plot_canvas_muvglin = PlottingEnvironment_Canvas(self.tab1, width=canvas_width,
                                                                       height=canvas_height, dpi=canvas_dpi, sizePolicy=canvas_sizepolicy)
            self.tab1_plot_canvas_muvglin.setMinimumHeight(canvas_min_height)
            self.tab1_plot_canvas_muvglin.setMinimumWidth(canvas_min_width)
            self.tab1_toolbar_muvglin = NavigationToolbar(self.tab1_plot_canvas_muvglin, self)
            self.tab1_plotting_muvglin_tab.layout.addWidget(self.tab1_toolbar_muvglin, alignment=QtCore.Qt.AlignLeft)
            self.tab1_plotting_muvglin_tab.layout.addWidget(self.tab1_plot_canvas_muvglin,alignment=QtCore.Qt.AlignLeft)

            self.tab1_plot_canvas_muvgsat = PlottingEnvironment_Canvas(self.tab1, width=canvas_width,
                                                                       height=canvas_height, dpi=canvas_dpi, sizePolicy=canvas_sizepolicy)
            self.tab1_plot_canvas_muvgsat.setMinimumHeight(canvas_min_height)
            self.tab1_plot_canvas_muvgsat.setMinimumWidth(canvas_min_width)
            self.tab1_toolbar_muvgsat = NavigationToolbar(self.tab1_plot_canvas_muvgsat, self)
            self.tab1_plotting_muvgsat_tab.layout.addWidget(self.tab1_toolbar_muvgsat, alignment=QtCore.Qt.AlignLeft)
            self.tab1_plotting_muvgsat_tab.layout.addWidget(self.tab1_plot_canvas_muvgsat, alignment=QtCore.Qt.AlignLeft)

            self.tab1_plot_canvas_ssw = PlottingEnvironment_Canvas(self.tab1, width=canvas_width, height=canvas_height,
                                                                   dpi=canvas_dpi, sizePolicy=canvas_sizepolicy)
            self.tab1_plot_canvas_ssw.setMinimumHeight(canvas_min_height)
            self.tab1_plot_canvas_ssw.setMinimumWidth(canvas_min_width)
            self.tab1_toolbar_ssw = NavigationToolbar(self.tab1_plot_canvas_ssw, self)
            self.tab1_plotting_ssw_tab.layout.addWidget(self.tab1_toolbar_ssw, alignment=QtCore.Qt.AlignLeft)
            self.tab1_plotting_ssw_tab.layout.addWidget(self.tab1_plot_canvas_ssw, alignment=QtCore.Qt.AlignLeft)
            ##########################################################################################

            self.tab1_analysis_and_plots_layout.addLayout(self.tab1_analysis_setup_and_results_layout)
            self.tab1_analysis_and_plots_layout.addWidget(self.vline())
            self.tab1_analysis_and_plots_layout.addWidget(self.tab1_plotting_tabs)

            self.testsplitter = QSplitter(QtCore.Qt.Horizontal)
            t11 = QWidget()
            self.tab1_analysis_setup_and_results_layout.setParent(None)
            t11.setLayout(self.tab1_analysis_setup_and_results_layout)
            self.testsplitter.addWidget(t11)
            self.testsplitter.addWidget(self.tab1_plotting_tabs)

            self.tab1.layout.addWidget(self.hline())
            self.tab1.layout.addWidget(self.testsplitter)

            self.tab1_outputline = QLabel(toolTip="""<p>This window is used to display messages to the user without
            the need to look at the Python console output.</p>""")
            self.tab1_outputline.setFrameShape(QFrame.Panel)
            self.tab1_outputline.setFrameShadow(QFrame.Sunken)
            self.tab1_outputline.setLineWidth(3)

            self.tab1.layout.addWidget(self.tab1_outputline)

        # tab2 contains a function plotter where arbitrary functions (in python syntax) can be plotted
        # for documentation, see the context menu in the "Help" section of the GUI
        # this tab is not thoroughly overhauled, tested, names refactored, and comments in the code are missing
        # reason: this was the first part of the code i wrote and i don't remember by heart what does what
        def initialize_tab2():
            # create complete plot block
            self.plot2_layout = QVBoxLayout()
            self.plot2_info = QHBoxLayout()
            self.plot2_label = QLabel('Python Plot Equation')
            self.plot2_label.setToolTip("""<p>Be aware that the plot variable will be replaced by data.
            For example, if the variable is x, np.exp will not work out of the box.</p>""")
            self.plot2_equation = QLineEdit()
            self.plot2_equation.setPlaceholderText('e.g.: a*x**2+b*np.arctan(2/x)-np.exp(np.cos(x-c))')
            self.plot2_update_button = QPushButton('Execute')
            self.plot2_info.addWidget(self.plot2_label)
            self.plot2_info.addWidget(self.plot2_equation)
            self.plot2_info.addWidget(self.plot2_update_button)

            # create dynamic plot environment
            self.sc2 = PlottingEnvironment_Canvas(self.tab2, width=4, height=3, dpi=100)
            self.sc2.setMinimumHeight(100)
            self.toolbar2 = NavigationToolbar(self.sc2, self)

            self.plot2_update_button.clicked.connect(self.plot2_new)
            self.plot2_layout.addLayout(self.plot2_info)
            # self.plot_layout.addWidget(self.sc)

            self.layout32 = QHBoxLayout()
            self.layout52 = QVBoxLayout()
            self.layout52.addWidget(self.toolbar2)
            self.layout52.addWidget(self.sc2)
            self.layout32.addLayout(self.layout52)

            self.layout42 = QVBoxLayout()  # variable layout

            self.var_12_label = QLabel('Parameter Assignment')
            self.var_12_value = QPlainTextEdit(
                placeholderText='Assign parameter values as follows: a=0\\nb=1 etc.')
            self.var_12_value.setMaximumWidth(200)

            self.scale2_layout = QHBoxLayout()
            self.scale2_menu_label = QLabel('Choose Scaling')
            self.plot2_scale_menu = QComboBox()
            self.plot2_scale_menu.addItem('Linear (x&y)')
            self.plot2_scale_menu.addItem('SemiLog (y)')
            self.plot2_scale_menu.addItem('LogLog (x&y)')
            self.plot2_scale_menu.currentIndexChanged.connect(self.plot2_new)
            self.plot2_overwrite_box = QCheckBox('Overwrite Plot')
            self.plot2_overwrite_box.setChecked(True)
            self.scale2_layout.addWidget(self.scale2_menu_label)
            self.scale2_layout.addWidget(self.plot2_scale_menu)
            self.scale2_layout.addWidget(self.plot2_overwrite_box)

            self.plot2_range_layout = QVBoxLayout()
            self.plot2_range_ly1 = QHBoxLayout()
            self.plot2_range_ly2 = QHBoxLayout()
            self.plot2_range_x_min_ly = QVBoxLayout()
            self.plot2_range_x_max_ly = QVBoxLayout()
            self.plot2_range_x_logscale_ly = QVBoxLayout()
            self.plot2_range_x_min = QLineEdit('0')
            self.plot2_range_x_max = QLineEdit('1')
            self.plot2_range_x_steps = QLineEdit('10')
            self.plot2_range_x_steps_logscale = QCheckBox('Logscale')
            self.plot2_range_x_steps_logscale.setToolTip("""<p>If checked, x values will be assigned using np.logscale
            If unchecked, x values will be assined using np.linscale instead</p>""")
            self.plot2_range_x_min_ly.addWidget(QLabel('xmin'))
            self.plot2_range_x_min_ly.addWidget(self.plot2_range_x_min)
            self.plot2_range_x_max_ly.addWidget(QLabel('xmax'))
            self.plot2_range_x_max_ly.addWidget(self.plot2_range_x_max)
            self.plot2_range_ly1.addLayout(self.plot2_range_x_min_ly)
            self.plot2_range_ly1.addLayout(self.plot2_range_x_max_ly)
            self.plot2_range_ly2.addWidget(QLabel('xsteps'))
            self.plot2_range_ly2.addWidget(self.plot2_range_x_steps)
            self.plot2_range_ly2.addWidget(self.plot2_range_x_steps_logscale)
            self.plot2_range_layout.addLayout(self.plot2_range_ly1)
            self.plot2_range_layout.addLayout(self.plot2_range_ly2)

            self.ly12 = QVBoxLayout()
            self.ly12.addLayout(self.plot2_range_layout)
            self.ly12.addWidget(self.var_12_label)
            self.ly12.addWidget(self.var_12_value)
            self.ly12.addLayout(self.scale2_layout)
            self.layout42.addLayout(self.ly12)
            self.layout32.addLayout(self.layout42)

            self.tab2.layout.addLayout(self.layout32)
            self.tab2.layout.addLayout(self.plot2_layout)

        # tab3 contains a full analysis environment for TLM analysis
        # for documentation, see the context menu in the "Help" section of the GUI
        def initialize_tab3():
            # set the default directory for choosing files in tab3
            self.default_directory_tab3 = 'C:/Users/wollandt_admin/MPI_Cloud/data/TW_samples/TW099/a/TLM'

            self.tab3_complete_layout = QHBoxLayout()

            # tab3 is divided into the left, interactive side where data can be chosen, fit parameters set and the
            # results can be displayed. right side will be only plot canvases
            self.tab3_leftside_interactive_layout = QVBoxLayout()

            # setup of the upper left part (file selection for the TLM analysis)
            self.tab3_file_button = QPushButton('Choose Files')
            self.tab3_file_button.clicked.connect(self.choose_filesTLM)
            self.tab3_file_remove_button = QPushButton('Remove Selected')
            self.tab3_file_remove_button.clicked.connect(self.remove_TLM_file)
            self.tab3_file_empty_button = QPushButton('Empty List')
            self.tab3_file_empty_button.clicked.connect(self.empty_TLM_file_list)
            # the program is not displaying whole paths but solely filenames. for reading the data, the whole
            # path is needed, so they have to be stored in combination -> this dictionary holds the references and
            # the QListWidget shows the files included in TLM analysis in a clean fashion
            self.tab3_file_paths = {}  # filename:path
            self.tab3_filelist = QListWidget(minimumHeight=25, maximumHeight=80, minimumWidth=50)
            self.tab3_filelist.currentRowChanged.connect(self.read_columnnames)
            self.tab3_file_selection_layout = QVBoxLayout()
            self.tab3_file_selection_buttons = QHBoxLayout()
            self.tab3_file_selection_buttons.addWidget(self.tab3_file_button)
            self.tab3_file_selection_buttons.addWidget(self.tab3_file_empty_button)
            self.tab3_file_selection_buttons.addWidget(self.tab3_file_remove_button)
            self.tab3_file_selection_layout.addLayout(self.tab3_file_selection_buttons)
            self.tab3_file_selection_layout.addWidget(self.tab3_filelist)

            # setup fit parameters C_ox, fd and sd
            self.tab3_fitsetup = QGridLayout()
            self.tab3_carrier_type_button = QPushButton('p', maximumWidth=30, checkable=True)
            self.tab3_carrier_type_button.clicked.connect(self.update_carrier_type_button_text)
            self.tab3_analysis_capacitance_input = QDoubleSpinBox(value=0.65, singleStep=0.01, minimum=0.00,
                                                                  maximum=5.00)
            self.tab3_analysis_first_derivative_threshold_input = QDoubleSpinBox(value=0.00, singleStep=0.01,
                                                                                 minimum=0.00, maximum=1.00)
            self.tab3_analysis_second_derivative_threshold_input = QDoubleSpinBox(value=0.00, singleStep=0.01,
                                                                                  minimum=0.00, maximum=1.00)
            self.tab3_analysis_smoothing_factor = QDoubleSpinBox(value=0.25, singleStep=0.01, minimum=0.00,
                                                                 maximum=1.00)
            fi_x, fi_y = 50, 20  # fixed size for spinboxes
            self.tab3_analysis_capacitance_input.setFixedSize(fi_x, fi_y)
            self.tab3_analysis_first_derivative_threshold_input.setFixedSize(fi_x, fi_y)
            self.tab3_analysis_second_derivative_threshold_input.setFixedSize(fi_x, fi_y)
            self.tab3_analysis_smoothing_factor.setFixedSize(fi_x, fi_y)
            self.tab3_fitsetup.addWidget(QLabel('Carrier Type'), 0, 0, alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(self.tab3_carrier_type_button, 0, 1, alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(QLabel('Dielectric Capacitance [µF/cm²]:'), 1, 0, alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(self.hline(), 3, 0, 1, 2)
            self.tab3_fitsetup.addWidget(QLabel('Linearity Identification - dI/dV (norm.) >',
                                                toolTip="""<p>This value sets the lower limit to the normalized (1st) derivative,
                                                above which datapoints are considered in the linear regime.</p>"""),
                                         4, 0,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(QLabel('Linearity Identification - d²I/dV² (norm.) <',
                                                toolTip="""<p>This value sets the upper limit to the normalized (2nd) derivative,
                                                below which datapoints are considered in the linear regime.</p>"""),
                                         5, 0,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(QLabel('Smoothing Factor - (Gaussian σ):',
                                                toolTip="""<p>Data is smoothed to reduce artifacts during derivation.</br>
                                                This value does NOT change fitting results, it only influences the automatic
                                                             determination of points to include in the fit (visible in the plots)!<br>
                                                This values is used as standard deviation in the gaussian broadening kernel.</p>"""),
                                         6, 0,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(self.tab3_analysis_capacitance_input, 1, 1, alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(self.tab3_analysis_first_derivative_threshold_input, 4, 1,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(self.tab3_analysis_second_derivative_threshold_input, 5, 1,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab3_fitsetup.addWidget(self.tab3_analysis_smoothing_factor, 6, 1,
                                         alignment=QtCore.Qt.AlignRight)

            # setup the results section
            self.tab3_resultlayout = QGridLayout()
            self.tab3_result_plot_all_transfercurves_checkbox = QCheckBox('Plot all Transfer Curves',checked=True)
            self.tab3_result_save_all_plots_checkbox = QCheckBox('Save all Plots directly',checked=False)
            self.tab3_automatic_Lcorrect = QCheckBox('Automatic L correct?',checked=False)

            self.tab3_result_empty_button = QPushButton('Empty')
            self.tab3_result_empty_button.clicked.connect(self.empty_TLM_results)

            self.tab3_result_show_TLM_VDS_layout = QHBoxLayout()
            self.tab3_result_show_TLM_VDS = QLineEdit(placeholderText="---", maximumWidth=60)
            self.tab3_result_show_TLM_VDS_layout.addWidget(QLabel("V_DS [V]", toolTip="Leave empty unless needed."),
                                                           alignment=QtCore.Qt.AlignCenter)
            self.tab3_result_show_TLM_VDS_layout.addWidget(self.tab3_result_show_TLM_VDS,
                                                           alignment=QtCore.Qt.AlignCenter)
            self.tab3_resultlayout.addWidget(self.tab3_result_plot_all_transfercurves_checkbox, 0, 0,
                                             alignment=QtCore.Qt.AlignCenter)
            self.tab3_resultlayout.addLayout(self.tab3_result_show_TLM_VDS_layout, 0, 1,
                                             alignment=QtCore.Qt.AlignCenter)
            self.tab3_resultlayout.addWidget(self.tab3_result_empty_button, 0, 2, alignment=QtCore.Qt.AlignCenter)
            self.tab3_resultlayout.addWidget(self.tab3_result_save_all_plots_checkbox, 1, 0,
                                             alignment=QtCore.Qt.AlignCenter)
            self.tab3_resultlayout.addWidget(self.tab3_automatic_Lcorrect, 1, 1,
                                             alignment=QtCore.Qt.AlignCenter)

            self.tab3_resultlayout.addWidget(QLabel('R<sub>c</sub>W',toolTip="Using an average of topmost overdrive voltages - see Settings tab."),
                                             2, 0, alignment=QtCore.Qt.AlignRight)

            self.tab3_resultlayout.addWidget(QLabel('R<sub>c,0</sub>W',
                                                    toolTip="""<p>V_GS-independent contact resistance; see U. Kraft thesis. Use this value with caution,
                                                    the automatic determination is only a guideline, not a reliable value!</p>"""
                                                    ), 3, 0, alignment=QtCore.Qt.AlignRight)
            self.tab3_resultlayout.addWidget(QLabel('Intr. Mobility µ<sub>0</sub>'), 4, 0,
                                             alignment=QtCore.Qt.AlignRight)
            self.tab3_resultlayout.addWidget(QLabel('L<sub>1/2</sub>'), 5, 0, alignment=QtCore.Qt.AlignRight)
            self.tab3_resultlayout.addWidget(QLabel('- L<sub>0</sub>',
                                                    toolTip="""<p>Intersection of the TLM fit lines; see U. Kraft thesis. Use this value with caution,
                                                    the automatic determination is only a guideline, not a reliable value!. If the value is not shown
                                                    in the TLM fit itself, take a look at the declaration of xmin_ variable in self.update_Rcfit().</p>"""
                                                    ), 6, 0, alignment=QtCore.Qt.AlignRight)
            self.tab3_resultlayout.addWidget(QLabel('R<sub>sheet</sub>',toolTip="Using an average of the 3 topmost overdrive voltages (hardcoded)"),
                                             7, 0, alignment=QtCore.Qt.AlignRight)
            self.tab3_result_RcW = QLineEdit(readOnly=True, placeholderText="---")
            self.tab3_result_Rc0W = QLineEdit(readOnly=True, placeholderText="---")
            self.tab3_result_intr_mob = QLineEdit(readOnly=True, placeholderText="---")
            self.tab3_result_l_1_2 = QLineEdit(readOnly=True, placeholderText="---")
            self.tab3_result_L0 = QLineEdit(readOnly=True, placeholderText="---")
            self.tab3_result_Rsheet = QLineEdit(readOnly=True, placeholderText="---")
            rs_x, rs_y = 110, 20
            self.tab3_result_RcW.setFixedSize(rs_x, rs_y)
            self.tab3_result_Rc0W.setFixedSize(rs_x, rs_y)
            self.tab3_result_intr_mob.setFixedSize(rs_x, rs_y)
            self.tab3_result_l_1_2.setFixedSize(rs_x, rs_y)
            self.tab3_result_L0.setFixedSize(rs_x, rs_y)
            self.tab3_result_Rsheet.setFixedSize(rs_x, rs_y)
            self.tab3_resultlayout.addWidget(self.tab3_result_RcW, 2, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(self.tab3_result_Rc0W, 3, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(self.tab3_result_intr_mob, 4, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(self.tab3_result_l_1_2, 5, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(self.tab3_result_L0, 6, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(self.tab3_result_Rsheet, 7, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(QLabel('Ωcm'), 2, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(QLabel('Ωcm'), 3, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(QLabel('cm²/Vs'), 4, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(QLabel('µm'), 5, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(QLabel('µm'), 6, 2, alignment=QtCore.Qt.AlignLeft)
            self.tab3_resultlayout.addWidget(QLabel('kΩ/□'), 7, 2, alignment=QtCore.Qt.AlignLeft)

            self.tab3_TLM_select_direction_layout = QHBoxLayout()
            self.tab3_TLM_select_direction_fwd = QRadioButton("Forward") # using only forward data
            self.tab3_TLM_select_direction_back = QRadioButton("Backward") # using only backward data
            self.tab3_TLM_select_direction_mean = QRadioButton("Mean", checked=True) # using complete data; Vth determination is 1/2*(Vth_fwd+Vth_back)
            self.tab3_TLM_select_direction_layout.addWidget(QLabel("Select direction: "), alignment=QtCore.Qt.AlignLeft)
            self.tab3_TLM_select_direction_layout.addWidget(self.tab3_TLM_select_direction_fwd, alignment=QtCore.Qt.AlignLeft)
            self.tab3_TLM_select_direction_layout.addWidget(self.tab3_TLM_select_direction_back, alignment=QtCore.Qt.AlignLeft)
            self.tab3_TLM_select_direction_layout.addWidget(self.tab3_TLM_select_direction_mean, alignment=QtCore.Qt.AlignLeft)

            self.tlmbutton = QPushButton('Execute TLM Analysis')
            self.tlmbutton.clicked.connect(self.analyze_TLM)
            self.tab3_tlm_data_for_export = pd.DataFrame()

            self.tab3_export_layout = QHBoxLayout()
            self.tab3_export_filename = QLineEdit(placeholderText="Enter Filename for Export")
            self.tab3_export_data_button = QPushButton('Export Data / Results')
            self.tab3_export_data_button.clicked.connect(self.TLM_analysis_export_data)
            self.tab3_copy_to_clipboard_button = QPushButton('📋',toolTip="Copy additional info to clipboard",maximumWidth=30)
            self.tab3_copy_to_clipboard_button.setLayoutDirection(QtCore.Qt.LeftToRight)
            self.tab3_copy_to_clipboard_button.clicked.connect(self.TLM_copy_to_clipboard)
            self.tab3_export_layout.addWidget(self.tab3_export_filename)
            self.tab3_export_layout.addWidget(self.tab3_export_data_button)
            self.tab3_export_layout.addWidget(self.tab3_copy_to_clipboard_button)

            self.tab3_leftside_interactive_layout.addLayout(self.tab3_file_selection_layout)
            self.tab3_leftside_interactive_layout.addLayout(self.tab3_fitsetup)
            self.tab3_leftside_interactive_layout.addLayout(self.tab3_resultlayout)
            self.tab3_leftside_interactive_layout.addLayout(self.tab3_TLM_select_direction_layout)
            self.tab3_leftside_interactive_layout.addWidget(self.tlmbutton)
            self.tab3_leftside_interactive_layout.addLayout(self.tab3_export_layout)

            ##########################################################################
            # setup the graphing tabwidget where all the fit results are plotted (right side of the window)
            self.tab3_tlm_plot_tabs = QTabWidget()
            self.tab3_tlm_plot_tab_allRcW = QWidget()
            self.tab3_tlm_plot_tab_single_RW = QWidget()
            self.tab3_tlm_plot_tab_intr_mob = QWidget()
            self.tab3_tlm_plot_tab_RcW_vs_overdrive = QWidget()
            self.tab3_tlm_plot_tab_mobility_vs_overdrive = QWidget()
            self.tab3_tlm_plot_tab_all_transfer_curves = QWidget()
            self.tab3_tlm_plot_tab_single_linear_fit = QWidget()
            self.tab3_tlm_plot_tab_vth_vs_channellength = QWidget()
            self.tab3_tlm_plot_tab_ssw_vs_channellength = QWidget()
            self.tab3_tlm_plot_tab_mTLM_vs_InvChannelLength = QWidget()
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_allRcW, "RcW (Vg-Vth)")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_single_RW, "TLM Fit")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_intr_mob, "µ (L)")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_all_transfer_curves, "TransferCurves")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_mTLM_vs_InvChannelLength, "m-TLM Fit")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_vth_vs_channellength, "Vth (L)")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_ssw_vs_channellength, "SSw (L)")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_single_linear_fit, "LinFit (L)")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_mobility_vs_overdrive, "µ0 (Vg-Vth)")
            self.tab3_tlm_plot_tabs.addTab(self.tab3_tlm_plot_tab_RcW_vs_overdrive, "RcW 1/(Vg-Vth)")
            #self.tab3_tlm_plot_tabs.setCurrentIndex(1)

            self.tab3_tlm_plot_tab_allRcW.layout = QVBoxLayout(self.tab3_tlm_plot_tab_allRcW)
            self.tab3_tlm_plot_tab_single_RW.layout = QVBoxLayout(self.tab3_tlm_plot_tab_single_RW)
            self.tab3_tlm_plot_tab_intr_mob.layout = QVBoxLayout(self.tab3_tlm_plot_tab_intr_mob)
            self.tab3_tlm_plot_tab_RcW_vs_overdrive.layout = QVBoxLayout(self.tab3_tlm_plot_tab_RcW_vs_overdrive)
            self.tab3_tlm_plot_tab_mobility_vs_overdrive.layout = QVBoxLayout(self.tab3_tlm_plot_tab_mobility_vs_overdrive)
            self.tab3_tlm_plot_tab_all_transfer_curves.layout = QVBoxLayout(self.tab3_tlm_plot_tab_all_transfer_curves)
            self.tab3_tlm_plot_tab_mTLM_vs_InvChannelLength.layout = QVBoxLayout(self.tab3_tlm_plot_tab_mTLM_vs_InvChannelLength)
            self.tab3_tlm_plot_tab_single_linear_fit.layout = QVBoxLayout(self.tab3_tlm_plot_tab_single_linear_fit)
            self.tab3_tlm_plot_tab_vth_vs_channellength.layout = QVBoxLayout(self.tab3_tlm_plot_tab_vth_vs_channellength)
            self.tab3_tlm_plot_tab_ssw_vs_channellength.layout = QVBoxLayout(self.tab3_tlm_plot_tab_ssw_vs_channellength)

            canvas_width, canvas_height, canvas_dpi, canvas_min_height, canvas_min_width = 5, 4, 100, 300, 300

            self.tab3_plot_canvas_allRcW = PlottingEnvironment_Canvas(self.tab3,width=canvas_width,height=canvas_height,
                                                                      dpi=canvas_dpi)
            self.tab3_plot_canvas_allRcW.get_default_filename = lambda: 'plot_allRcW.png'
            self.tab3_plot_canvas_allRcW.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_allRcW.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_allRcW = NavigationToolbar(self.tab3_plot_canvas_allRcW, self)
            self.tab3_tlm_plot_tab_allRcW.layout.addWidget(self.tab3_toolbar_allRcW, alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_allRcW.layout.addWidget(self.tab3_plot_canvas_allRcW, alignment=QtCore.Qt.AlignLeft)

            # in the single RW plot there needs to be a selection of which overdrive voltage should be displayed
            # by default this is the case for the overdrive voltage with the highes R^2 value
            self.tab3_plot_canvas_single_RW = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                         height=canvas_height, dpi=canvas_dpi)
            self.tab3_plot_canvas_single_RW.get_default_filename = lambda: 'plot_TLM_fit.png'
            self.tab3_plot_canvas_single_RW.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_single_RW.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_single_RW = NavigationToolbar(self.tab3_plot_canvas_single_RW, self)
            self.tab3_overdrivelayout = QHBoxLayout()
            self.tab3_all_ov_RWs = {}
            self.tab3_singlerw_choose_ov = QComboBox(maximumHeight=25, maximumWidth=80)
            self.tab3_singlerw_choose_ov.currentIndexChanged.connect(self.update_Rcfit)
            self.tab3_overdrivelayout.addWidget(QLabel('Overdrive Voltage'), alignment=QtCore.Qt.AlignRight)
            self.tab3_overdrivelayout.addWidget(self.tab3_singlerw_choose_ov, alignment=QtCore.Qt.AlignCenter)
            self.tab3_overdrivelayout.addWidget(QLabel('V'), alignment=QtCore.Qt.AlignLeft)
            self.tab3_singlerw_showall_checkbox = QCheckBox('Plot multiple?')
            self.tab3_singlerw_showlabel = QCheckBox('Show Label', checked=True)
            self.tab3_overdrivelayout.addWidget(self.tab3_singlerw_showall_checkbox)
            self.tab3_overdrivelayout.addWidget(self.tab3_singlerw_showlabel)
            self.tab3_tlm_plot_tab_single_RW.layout.addLayout(self.tab3_overdrivelayout)
            self.tab3_tlm_plot_tab_single_RW.layout.addWidget(self.tab3_toolbar_single_RW,
                                                              alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_single_RW.layout.addWidget(self.tab3_plot_canvas_single_RW,
                                                              alignment=QtCore.Qt.AlignLeft)

            self.tab3_plot_canvas_intr_mob = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                        height=canvas_height, dpi=canvas_dpi)
            self.tab3_plot_canvas_intr_mob.get_default_filename = lambda: 'plot_mu0.png'
            self.tab3_plot_canvas_intr_mob.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_intr_mob.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_intr_mob = NavigationToolbar(self.tab3_plot_canvas_intr_mob, self)
            self.tab3_tlm_plot_tab_intr_mob.layout.addWidget(self.tab3_toolbar_intr_mob, alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_intr_mob.layout.addWidget(self.tab3_plot_canvas_intr_mob,
                                                             alignment=QtCore.Qt.AlignLeft)

            self.tab3_plot_canvas_mTLM_vs_InvChannelLength = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                        height=canvas_height, dpi=canvas_dpi)
            self.tab3_plot_canvas_mTLM_vs_InvChannelLength.get_default_filename = lambda: 'plot_mTLM.png'
            self.tab3_plot_canvas_mTLM_vs_InvChannelLength.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_mTLM_vs_InvChannelLength.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_mTLM_vs_InvChannelLength = NavigationToolbar(self.tab3_plot_canvas_mTLM_vs_InvChannelLength, self)
            self.tab3_tlm_plot_tab_mTLM_vs_InvChannelLength.layout.addWidget(self.tab3_toolbar_mTLM_vs_InvChannelLength, alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_mTLM_vs_InvChannelLength.layout.addWidget(self.tab3_plot_canvas_mTLM_vs_InvChannelLength,
                                                             alignment=QtCore.Qt.AlignLeft)


            self.tab3_plot_canvas_RcW_vs_overdrive = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                                height=canvas_height, dpi=canvas_dpi)
            self.tab3_plot_canvas_RcW_vs_overdrive.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_RcW_vs_overdrive.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_RcW_vs_overdrive = NavigationToolbar(self.tab3_plot_canvas_RcW_vs_overdrive, self)
            self.tab3_tlm_plot_tab_RcW_vs_overdrive.layout.addWidget(self.tab3_toolbar_RcW_vs_overdrive,
                                                                     alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_RcW_vs_overdrive.layout.addWidget(self.tab3_plot_canvas_RcW_vs_overdrive,
                                                                     alignment=QtCore.Qt.AlignLeft)


            self.tab3_plot_canvas_mobility_vs_overdrive = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                                     height=canvas_height,
                                                                                     dpi=canvas_dpi)
            self.tab3_plot_canvas_mobility_vs_overdrive.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_mobility_vs_overdrive.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_mobility_vs_overdrive = NavigationToolbar(self.tab3_plot_canvas_mobility_vs_overdrive,
                                                                        self)
            self.tab3_tlm_plot_tab_mobility_vs_overdrive.layout.addWidget(self.tab3_toolbar_mobility_vs_overdrive,
                                                                          alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_mobility_vs_overdrive.layout.addWidget(self.tab3_plot_canvas_mobility_vs_overdrive,
                                                                          alignment=QtCore.Qt.AlignLeft)


            self.tab3_plot_canvas_all_transfer_curves = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                                   height=canvas_height,
                                                                                   dpi=canvas_dpi)
            self.tab3_plot_canvas_all_transfer_curves.get_default_filename = lambda: 'plot_transfercurves.png'
            self.tab3_plot_canvas_all_transfer_curves.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_all_transfer_curves.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_all_transfer_curves = NavigationToolbar(self.tab3_plot_canvas_all_transfer_curves,
                                                                      self)
            self.tab3_tlm_plot_tab_all_transfer_curves.layout.addWidget(self.tab3_toolbar_all_transfer_curves,
                                                                        alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_all_transfer_curves.layout.addWidget(self.tab3_plot_canvas_all_transfer_curves,
                                                                        alignment=QtCore.Qt.AlignLeft)

            # in the single RW plot there needs to be a selection of which overdrive voltage should be displayed
            # by default this is the case for the overdrive voltage with the highes R^2 value
            self.tab3_plot_canvas_single_linear_fit = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                         height=canvas_height, dpi=canvas_dpi)
            self.tab3_plot_canvas_single_linear_fit.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_single_linear_fit.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_single_linear_fit = NavigationToolbar(self.tab3_plot_canvas_single_linear_fit, self)
            self.tab3_single_linearFit_layout = QHBoxLayout(alignment=QtCore.Qt.AlignLeft)
            self.tab3_all_Ls = {}
            self.tab3_single_linFit_choose_L = QComboBox(maximumHeight=25, maximumWidth=80,
                                                         toolTip="<p>Only showing channel length and its index for reasons of programming ease, if in doubt which exact dataset (if different channel widths, or duplicates of the same TFT) is chosen please check the TransferAnalysis or remove some duplicates from the TLM file list.</p>")
            self.tab3_single_linFit_choose_L.currentIndexChanged.connect(self.update_single_linFit)
            self.tab3_single_linearFit_layout.addWidget(QLabel('Channel Length'), alignment=QtCore.Qt.AlignRight)
            self.tab3_single_linearFit_layout.addWidget(self.tab3_single_linFit_choose_L, alignment=QtCore.Qt.AlignCenter)
            self.tab3_single_linearFit_layout.addWidget(QLabel('µm'), alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_single_linear_fit.layout.addLayout(self.tab3_single_linearFit_layout)
            self.tab3_tlm_plot_tab_single_linear_fit.layout.addWidget(self.tab3_toolbar_single_linear_fit,
                                                              alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_single_linear_fit.layout.addWidget(self.tab3_plot_canvas_single_linear_fit,
                                                              alignment=QtCore.Qt.AlignLeft)


            self.tab3_plot_canvas_vth_vs_channellength = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                                    height=canvas_height,
                                                                                    dpi=canvas_dpi)
            self.tab3_plot_canvas_vth_vs_channellength.get_default_filename = lambda: 'plot_Vths.png'
            self.tab3_plot_canvas_vth_vs_channellength.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_vth_vs_channellength.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_vth_vs_channellength = NavigationToolbar(self.tab3_plot_canvas_vth_vs_channellength,
                                                                       self)
            self.tab3_tlm_plot_tab_vth_vs_channellength.layout.addWidget(self.tab3_toolbar_vth_vs_channellength,
                                                                         alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_vth_vs_channellength.layout.addWidget(self.tab3_plot_canvas_vth_vs_channellength,
                                                                         alignment=QtCore.Qt.AlignLeft)


            self.tab3_plot_canvas_ssw_vs_channellength = PlottingEnvironment_Canvas(self.tab3, width=canvas_width,
                                                                                    height=canvas_height,
                                                                                    dpi=canvas_dpi)
            self.tab3_plot_canvas_ssw_vs_channellength.get_default_filename = lambda: 'plot_SSws.png'
            self.tab3_plot_canvas_ssw_vs_channellength.setMinimumHeight(canvas_min_height)
            self.tab3_plot_canvas_ssw_vs_channellength.setMinimumWidth(canvas_min_width)
            self.tab3_toolbar_ssw_vs_channellength = NavigationToolbar(self.tab3_plot_canvas_ssw_vs_channellength,
                                                                       self)
            self.tab3_tlm_plot_tab_ssw_vs_channellength.layout.addWidget(self.tab3_toolbar_ssw_vs_channellength,
                                                                         alignment=QtCore.Qt.AlignLeft)
            self.tab3_tlm_plot_tab_ssw_vs_channellength.layout.addWidget(self.tab3_plot_canvas_ssw_vs_channellength,
                                                                         alignment=QtCore.Qt.AlignLeft)

            ##########################################

            self.tab3_complete_layout.addLayout(self.tab3_leftside_interactive_layout)
            self.tab3_complete_layout.addWidget(self.vline())
            self.tab3_complete_layout.addWidget(self.tab3_tlm_plot_tabs)
            self.tab3.layout.addLayout(self.tab3_complete_layout)

            self.tab3_useroutput = QLabel(toolTip="""<p>This window is used to display messages to the user without
                the need to look at the Python console output.</p>""")
            self.tab3_useroutput.setFrameShape(QFrame.Panel)
            self.tab3_useroutput.setFrameShadow(QFrame.Sunken)
            self.tab3_useroutput.setLineWidth(3)
            self.tab3.layout.addWidget(self.tab3_useroutput)

        # tab4 is meant as a way to deflate the fit setup (mostly in tab1). there are many parameters that can be changed
        # and settings (e.g. take Vth from lin or sat regime) that are not important enough to be shown in the fit setup
        # because it makes it too overloaded and not user-friendly anymore. GENERAL SETTINGS TAB
        def initialize_tab4():
            self.default_directory_savefig = os.getcwd()
            self.tab4_mainlayout = QGridLayout()

            self.tab4_tab1settings = QGridLayout()
            self.tab4_settings_overview = QVBoxLayout()

            self.tab4_default_tab = QComboBox(maximumWidth=300)
            self.tab4_default_tab.addItem("Transfer Analysis")
            self.tab4_default_tab.addItem("TLM")
            self.tab4_default_tab.addItem("S-Parameters")
            self.tab4_default_tab.addItem("Arrhenius")
            self.tab4_default_tab.addItem("Inverter Analysis")
            self.tab4_tab1settings.addWidget(QLabel("Default Tab at Startup:"),0, 0, 1, 2)
            self.tab4_tab1settings.addWidget(self.tab4_default_tab,0, 1, 1, 2)


            # gridlayout containing the settings geared towards the Transfer Analysis tab
            self.tab4_tab1settings.addWidget(QLabel('<h2>Global Settings for Transfer Analysis</h2>'), 1, 0, 1, 4,
                                             alignment=QtCore.Qt.AlignCenter)
            self.tab4_set_datapreset = QListWidget(maximumHeight=70, maximumWidth=200)
            self.tab4_set_datapreset.addItem("SweepMe!")
            self.tab4_set_datapreset.addItem("Custom")
            self.tab4_set_datapreset.addItem("LabVIEW")
            self.tab4_set_datapreset.addItem("ParameterAnalyzer")
            self.tab4_set_datapreset.addItem("Goettingen")
            self.tab4_set_datapreset.addItem("Marburg")
            self.tab4_set_datapreset.addItem("Surrey")
            self.tab4_set_datapreset.currentRowChanged.connect(self.change_data_preset)
            self.tab4_set_datapreset.setCurrentRow(0)
            self.tab4_tab1settings.addWidget(self.tab4_set_datapreset,                2, 0, 1, 6, alignment=QtCore.Qt.AlignCenter)

            self.tab4_set_tab1_plotdata_absolute = QCheckBox('Plot Chosen Dataset in Absolute Values', checked=True)
            self.tab4_set_tab1_plotdata_absolute.stateChanged.connect(
                lambda: self.tab1_plot_canvas_dataset.set_absolute_plotting(
                    self.tab4_set_tab1_plotdata_absolute.isChecked()))
            self.tab4_set_tab1_oor_avg_window = QSpinBox(minimum=1, maximum=100, maximumWidth=50)
            self.tab4_set_tab3_rcw_avg_window = QSpinBox(minimum=0, maximum=100, maximumWidth=50)
            self.tab4_set_tab1_oor_avg_window_label = QLabel("No. of datapoints to average for On/Off ratio:",
                                                             toolTip="""<p>The upper- and lowermost 2 values are discarded. From the remaining dataset,
                                                             the highest (lowest) X current values are averaged.</p>""")
            self.tab4_set_tab3_rcw_avg_window_label = QLabel("No. of datapoints to average for R<sub>c</sub>W:",
                                                             toolTip="""<p>The R<sub>c</sub>W values for the highest X overdrive voltages
                                                             (measured from the L for which the least overdrive voltages exist) are averaged.</p>""")
            self.tab4_tab3_result_limit_plot_xrange = QCheckBox("Limit TLM plot?",checked=True,
                                                                toolTip="""<p>If this is chosen, the TLM plot will never look super messed up, but L<sub>0</sub> and L<sub>1/2</sub> will not be always visible in the shown range.</p>""")
            self.tab4_tab1settings.addWidget(self.tab4_set_tab1_plotdata_absolute,    3, 0, 1, 4)
            self.tab4_tab1settings.addWidget(self.tab4_set_tab1_oor_avg_window_label, 4, 0, 1, 3)
            self.tab4_tab1settings.addWidget(self.tab4_set_tab1_oor_avg_window,       4, 3, 1, 1)
            # add RcW averaging value to tab1settings even though it should be tab3settings, because it fits there visually
            # no further reasoning behind it - sorry for the "dirty" code structure there
            self.tab4_tab1settings.addWidget(self.tab4_set_tab3_rcw_avg_window_label, 5, 0, 1, 2)
            self.tab4_tab1settings.addWidget(self.tab4_set_tab3_rcw_avg_window,       5, 2, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_tab3_result_limit_plot_xrange, 5, 3, 1, 1)

            self.tab4_tab1settings.addWidget(QLabel("<h4><p>Setup of Fixed Values to Include in Fit (all Tabs, universal)</p></h4>"),
                                                                                      6, 0, 1, 4, alignment=QtCore.Qt.AlignCenter)
            self.tab4_tab1settings_linfit_usefixed_xrange = QCheckBox("Use")
            self.tab4_tab1settings_satfit_usefixed_xrange = QCheckBox("Use")
            self.tab4_tab1settings_sswfit_usefixed_xrange = QCheckBox("Use")
            sx_, sy_ = 60, 20
            self.tab4_tab1settings_linfit_xmin = QDoubleSpinBox(value=0.00, maximumWidth=sx_, maximumHeight=sy_, decimals=2, singleStep=0.01, minimum=-99.9, maximum=99.9)
            self.tab4_tab1settings_linfit_xmax = QDoubleSpinBox(value=0.00, maximumWidth=sx_, maximumHeight=sy_, decimals=2, singleStep=0.01, minimum=-99.9, maximum=99.9)
            self.tab4_tab1settings_satfit_xmin = QDoubleSpinBox(value=0.00, maximumWidth=sx_, maximumHeight=sy_, decimals=2, singleStep=0.01, minimum=-99.9, maximum=99.9)
            self.tab4_tab1settings_satfit_xmax = QDoubleSpinBox(value=0.00, maximumWidth=sx_, maximumHeight=sy_, decimals=2, singleStep=0.01, minimum=-99.9, maximum=99.9)
            self.tab4_tab1settings_sswfit_xmin = QDoubleSpinBox(value=0.00, maximumWidth=sx_, maximumHeight=sy_, decimals=2, singleStep=0.01, minimum=-99.9, maximum=99.9)
            self.tab4_tab1settings_sswfit_xmax = QDoubleSpinBox(value=0.00, maximumWidth=sx_, maximumHeight=sy_, decimals=2, singleStep=0.01, minimum=-99.9, maximum=99.9)
            self.tab4_tab1settings.addWidget(QLabel('Linear Fit: x range (V)'),       7, 0, 1, 1,
                                             alignment=QtCore.Qt.AlignRight)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_linfit_xmin,      7, 1, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_linfit_xmax,      7, 2, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_linfit_usefixed_xrange, 7, 3, 1, 1)
            self.tab4_tab1settings.addWidget(QLabel('Saturation Fit: x range (V)'),   8, 0, 1, 1,
                                             alignment=QtCore.Qt.AlignRight)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_satfit_xmin,      8, 1, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_satfit_xmax,      8, 2, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_satfit_usefixed_xrange, 8, 3, 1, 1)
            self.tab4_tab1settings.addWidget(QLabel('Subthr.Sw. Fit: x range (V)'),   9, 0, 1, 1,
                                             alignment=QtCore.Qt.AlignRight)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_sswfit_xmin,      9, 1, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_sswfit_xmax,      9, 2, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_tab1settings_sswfit_usefixed_xrange, 9, 3, 1, 1)

            # add possibility to give custom column names that don't need to comply with one of the presets
            self.tab4_set_custom_column_names = QLineEdit(
                toolTip="Give the column header line here in the format 'col1;col2;col3'",
                placeholderText="No custom columns given")
            self.tab4_set_custom_skiprows = QSpinBox(
                toolTip="Give the number of rows to skip at the beginning of the file (e.g.: SweepMe! has 3)")
            self.tab4_tab1settings.addWidget(QLabel("Custom column names",toolTip="Give the column header line here in the format 'col1;col2;col3'"),
                                                                                      10, 0, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_set_custom_column_names,       10, 1, 1, 3)
            self.tab4_tab1settings.addWidget(QLabel("Custom skiprows",toolTip="Give the number of rows to skip at the beginning of the file (e.g.: SweepMe! has 3)"),
                                                                                      11, 0, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_set_custom_skiprows,           11, 1, 1, 1)
            self.tab4_set_TLM_xmin_automatic =  QCheckBox("TLM-Fit x_min auto?",checked=True, toolTip="""<p>If this is chosen, the x<sub>min</sub> value chosen for TLM fit-line plotting
            will be set according to the extracted value of L<sub>1/2</sub>. Otherwise, x<sub>min</sub> will be hard-coded to 1µm.</p>""")
            self.tab4_execute_mTLM = QCheckBox('mTLM?',checked=False,toolTip="Execute m-TLM?")
            # self.tab4_tab1settings.addWidget(QLabel("TLM-Fit x<sub>min</sub> auto?", toolTip="Test"),
            #                                                                          11, 2, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_execute_mTLM,                  11, 2, 1, 1)
            self.tab4_tab1settings.addWidget(self.tab4_set_TLM_xmin_automatic,        11, 3, 1, 1)

            #self.tab4_show_L_correct_db_path = QLineEdit(readOnly=True, toolTip=f"{self.default_L_correct_db}",
            #                                             placeholderText=f"{self.default_L_correct_db}")
            self.tab4_show_L_correct_db_path = QLineEdit(readOnly=True, toolTip=f"---",
                                                         placeholderText=f"---")
            self.tab4_automatic_Lcorrect = QCheckBox("Active",toolTip="<p>All analysis that uses the channel length will attempt to use the channel length measured via SEM that is "
                                                                      "given in the database.</p>")

            self.tab4_change_L_correct_db_path = QPushButton("Corrected L database")
            self.tab4_change_L_correct_db_path.setToolTip=("<p>Click to change.<br/><br>If the sample is listed in the database, the program will attempt to use the real, measured channel length instead of the nominal one given in the filename</p>"),
            self.tab4_change_L_correct_db_path.clicked.connect(self.change_L_correct_db_path)

            self.tab4_tab1settings.addWidget(self.tab4_change_L_correct_db_path,      12, 0, 1, 1)

            self.tab4_tab1settings.addWidget(self.tab4_show_L_correct_db_path,        12, 1, 1, 2)
            self.tab4_tab1settings.addWidget(self.tab4_automatic_Lcorrect,            12, 3, 1, 1)
            #print(self.default_L_correct_db)





            # gridlayout containing the settings geared towards the Transistor Analysis tab
            self.settings = f"{os.getcwd()}/settings.ini"
            self.tab4_show_settings_filecontent = QListWidget()
            self.tab4_settings_overview.addWidget(QLabel("<h4>Settings File Content</h4>"))
            self.tab4_settings_overview.addWidget(self.tab4_show_settings_filecontent)

            # adding the setting for different tabs in the main settings gridlayout
            # defining the settings export
            self.tab4_mainlayout.addLayout(self.tab4_tab1settings,                      0, 0, 1, 2)
            self.tab4_mainlayout.addWidget(self.vline(),                                0, 2, 1, 1)
            self.tab4_mainlayout.addLayout(self.tab4_settings_overview,                 0, 3, 1, 1)
            self.tab4_mainlayout.addWidget(self.hline(),                                1, 0, 1, 4)

            self.tab4_change_tab1_default_directory_button = QPushButton("Change Transfer Analysis Default Directory")
            self.tab4_change_tab1_default_directory_button.clicked.connect(
                self.change_analyze_transfer_default_directory)
            self.tab4_show_tab1_default_directory = QLineEdit(readOnly=True, toolTip=f"{self.default_directory_tab1}",
                                                              placeholderText=f"{self.default_directory_tab1}")
            self.tab4_mainlayout.addWidget(QLabel("Transfer Analysis Default Directory"),   2, 0, 1, 1)
            self.tab4_mainlayout.addWidget(self.tab4_show_tab1_default_directory,           2, 1, 1, 2)
            self.tab4_mainlayout.addWidget(self.tab4_change_tab1_default_directory_button,  2, 3, 1, 1)

            self.tab4_change_tab3_default_directory_button = QPushButton("Change TLM Default Directory")
            self.tab4_change_tab3_default_directory_button.clicked.connect(self.change_TLM_default_directory)
            self.tab4_show_tab3_default_directory = QLineEdit(readOnly=True, toolTip=f"{self.default_directory_tab3}",
                                                              placeholderText=f"{self.default_directory_tab3}")
            self.tab4_mainlayout.addWidget(QLabel("TLM Default Directory"),                 3, 0, 1, 1)
            self.tab4_mainlayout.addWidget(self.tab4_show_tab3_default_directory,           3, 1, 1, 2)
            self.tab4_mainlayout.addWidget(self.tab4_change_tab3_default_directory_button,  3, 3, 1, 1)

            self.tab4_change_tab5_default_directory_button = QPushButton("Change S-Parameter Default Directory")
            self.tab4_change_tab5_default_directory_button.clicked.connect(self.change_sparam_default_directory)
            self.tab4_show_tab5_default_directory = QLineEdit(readOnly=True, toolTip=f"{self.default_directory_tab5}",
                                                              placeholderText=f"{self.default_directory_tab5}")
            self.tab4_mainlayout.addWidget(QLabel("S-Parameter Default Directory"),         4, 0, 1, 1)
            self.tab4_mainlayout.addWidget(self.tab4_show_tab5_default_directory,           4, 1, 1, 2)
            self.tab4_mainlayout.addWidget(self.tab4_change_tab5_default_directory_button,  4, 3, 1, 1)

            self.tab4_change_tab6_default_directory_button = QPushButton("Change Arrhenius Default Directory")
            self.tab4_change_tab6_default_directory_button.clicked.connect(self.change_arrhenius_default_directory)
            self.tab4_show_tab6_default_directory = QLineEdit(readOnly=True, toolTip=f"{self.default_directory_tab6}",
                                                              placeholderText=f"{self.default_directory_tab6}")
            self.tab4_mainlayout.addWidget(QLabel("Arrhenius Default Directory"),           5, 0, 1, 1)
            self.tab4_mainlayout.addWidget(self.tab4_show_tab6_default_directory,           5, 1, 1, 2)
            self.tab4_mainlayout.addWidget(self.tab4_change_tab6_default_directory_button,  5, 3, 1, 1)

            self.tab4_change_tab7_default_directory_button = QPushButton("Change Inverter Default Directory")
            self.tab4_change_tab7_default_directory_button.clicked.connect(self.change_inverter_default_directory)
            self.tab4_show_tab7_default_directory = QLineEdit(readOnly=True, toolTip=f"{self.default_directory_tab7}",
                                                              placeholderText=f"{self.default_directory_tab7}")
            self.tab4_mainlayout.addWidget(QLabel("Inverter Default Directory"), 6, 0, 1, 1)
            self.tab4_mainlayout.addWidget(self.tab4_show_tab7_default_directory, 6, 1, 1, 2)
            self.tab4_mainlayout.addWidget(self.tab4_change_tab7_default_directory_button, 6, 3, 1, 1)

            self.tab4_change_savefig_default_directory_button = QPushButton("Change Savefig Default Directory")
            self.tab4_change_savefig_default_directory_button.clicked.connect(self.change_savefig_default_directory)
            self.tab4_show_savefig_default_directory = QLineEdit(readOnly=True, toolTip=f"{self.default_directory_savefig}",
                                                              placeholderText=f"{self.default_directory_savefig}")
            self.tab4_mainlayout.addWidget(QLabel("Savefig Default Directory"),               7, 0, 1, 1)
            self.tab4_mainlayout.addWidget(self.tab4_show_savefig_default_directory,          7, 1, 1, 2)
            self.tab4_mainlayout.addWidget(self.tab4_change_savefig_default_directory_button, 7, 3, 1, 1)

            self.tab4_save_settings_button = QPushButton("Save Settings")
            self.tab4_save_settings_button.clicked.connect(self.save_settings)
            self.tab4_load_settings_button = QPushButton("Load Settings")
            self.tab4_load_settings_button.clicked.connect(self.load_settings)
            self.tab4_mainlayout.addWidget(self.tab4_load_settings_button,                  8, 0, 1, 2)
            self.tab4_mainlayout.addWidget(self.tab4_save_settings_button,                  8, 3, 1, 1)

            self.tab4_outputline = QLabel(toolTip="""<p>This window is used to display messages to the user without
                the need to look at the Python console output.</p>""",
                maximumHeight=30)
            self.tab4_outputline.setFrameShape(QFrame.Panel)
            self.tab4_outputline.setFrameShadow(QFrame.Sunken)
            self.tab4_outputline.setLineWidth(3)
            self.tab4_mainlayout.addWidget(self.tab4_outputline,                            9, 0, 1, 4)

            self.tab4.layout.addLayout(self.tab4_mainlayout)
            self.load_settings()

        # tab5 contains analysis of dynamic measurements (S-parameters)
        # for documentation, see the context menu in the "Help" section of the GUI
        def initialize_tab5():
            # set the default directory for choosing files in tab5
            self.default_directory_tab5 = 'C:/Users/wollandt_admin/MPICloud/shared_data/Micha/2021-04_Sparameter_for_GUI'

            self.tab5_complete_layout = QHBoxLayout()

            #########################################################
            # tab5 is divided into the left, interactive side where data can be chosen, fit parameters set and the
            # results can be displayed. right side will be only plot canvases
            self.tab5_leftside_interactive_layout = QVBoxLayout()

            # setup of the upper left part (file selection for the TLM analysis)
            self.tab5_file_button = QPushButton('Choose Files')
            self.tab5_file_button.clicked.connect(self.choose_filesSparam)
            self.tab5_file_remove_button = QPushButton('Remove Selected')
            self.tab5_file_remove_button.clicked.connect(self.remove_sparam_file)
            self.tab5_file_empty_button = QPushButton('Empty List')
            self.tab5_file_empty_button.clicked.connect(self.empty_sparam_file_list)
            # the program is not displaying whole paths but solely filenames. for reading the data, the whole
            # path is needed, so they have to be stored in combination -> this dictionary holds the references and
            # the QListWidget shows many files in a clean fashion, however only the active one is analyzed!

            #self.tab5_file_paths = {"H7.xlsx":"C:/Users/wollandt_admin/MPI_Cloud/shared_data/Micha/2021-04_Sparameter_for_GUI/H7.xlsx",
            #                        "DataFile#9.s2p":"C:/Users/wollandt_admin/MPI_Cloud/shared_data/Micha/2021-04_Sparameter_for_GUI/DataFile#9.s2p"}  # filename:path
            #self.tab5_filelist = QListWidget(minimumHeight=25, maximumHeight=80, minimumWidth=50)
            #self.tab5_filelist.addItem("H7.xlsx")
            #self.tab5_filelist.setCurrentRow(0)
            #self.tab5_filelist.addItem("DataFile#9.s2p")
            ##### when the Sparameters analysis works, the testing purpose files can be removed again
            self.tab5_file_paths = {}  # filename:path
            self.tab5_filelist = QListWidget(minimumHeight=120, maximumHeight=80, minimumWidth=50)
            self.tab5_file_selection_layout = QVBoxLayout()
            self.tab5_file_selection_buttons = QHBoxLayout()
            self.tab5_file_selection_buttons.addWidget(self.tab5_file_button)
            self.tab5_file_selection_buttons.addWidget(self.tab5_file_empty_button)
            self.tab5_file_selection_buttons.addWidget(self.tab5_file_remove_button)
            self.tab5_file_selection_layout.addLayout(self.tab5_file_selection_buttons)
            self.tab5_file_selection_layout.addWidget(self.tab5_filelist)

            # setup the estimation/calculation area according to Muellers assumption (?) for fT
            self.tab5_estimate_fT_layout = QVBoxLayout()
            self.tab5_estimate_fT_input_layout_row1 = QHBoxLayout()
            self.tab5_estimate_fT_input_layout_row2 = QHBoxLayout()
            self.tab5_estimate_fT_output_layout = QHBoxLayout()
            self.tab5_estimate_fT_RcW = QLineEdit(placeholderText='---',maximumWidth=50)
            self.tab5_estimate_fT_L = QLineEdit(placeholderText='---',maximumWidth=50)
            self.tab5_estimate_fT_Lov = QLineEdit(placeholderText='---',maximumWidth=50)
            self.tab5_estimate_fT_mu0 = QLineEdit(placeholderText='---',maximumWidth=50)
            self.tab5_estimate_fT_Cdiel = QLineEdit(placeholderText='---',maximumWidth=50)
            self.tab5_estimate_fT_Vov = QLineEdit(placeholderText='---',maximumWidth=50)
            self.tab5_estimate_fT_formula_choice = QComboBox()
            self.tab5_estimate_fT_formula_choice.addItem("w/ RcW");self.tab5_estimate_fT_formula_choice.addItem("w/o RcW")

            self.tab5_estimate_fT_button = QPushButton("Estimate")
            self.tab5_estimate_fT_button.clicked.connect(self.estimate_fT)
            self.tab5_estimate_fT_result = QLineEdit(readOnly=True,placeholderText='---',maximumWidth=60)


            self.tab5_estimate_fT_input_layout_row1.addWidget(QLabel('R<sub>c</sub>W', maximumWidth=50,
                                                                     toolTip="Width-normalized contact resistance"),alignment=QtCore.Qt.AlignRight)
            self.tab5_estimate_fT_input_layout_row1.addWidget(self.tab5_estimate_fT_RcW)
            self.tab5_estimate_fT_input_layout_row1.addWidget(QLabel('Ωcm',maximumWidth=20),alignment=QtCore.Qt.AlignLeft)

            self.tab5_estimate_fT_input_layout_row1.addWidget(QLabel('L', maximumWidth=20,
                                                                     toolTip="Channel length"),alignment=QtCore.Qt.AlignRight)
            self.tab5_estimate_fT_input_layout_row1.addWidget(self.tab5_estimate_fT_L)
            self.tab5_estimate_fT_input_layout_row1.addWidget(QLabel('µm', maximumWidth=15),alignment=QtCore.Qt.AlignLeft)

            self.tab5_estimate_fT_input_layout_row1.addWidget(QLabel('L<sub>ov</sub>', maximumWidth=20,
                                                                     toolTip="Overlap between contact and gate electrodes"),alignment=QtCore.Qt.AlignRight)
            self.tab5_estimate_fT_input_layout_row1.addWidget(self.tab5_estimate_fT_Lov)
            self.tab5_estimate_fT_input_layout_row1.addWidget(QLabel('µm', maximumWidth=15),alignment=QtCore.Qt.AlignLeft)

            self.tab5_estimate_fT_input_layout_row2.addWidget(QLabel('µ<sub>0</sub>',maximumWidth=50,
                                                                     toolTip="Intrinsic mobility"),alignment=QtCore.Qt.AlignRight)
            self.tab5_estimate_fT_input_layout_row2.addWidget(self.tab5_estimate_fT_mu0)
            self.tab5_estimate_fT_input_layout_row2.addWidget(QLabel('cm²/Vs',maximumWidth=40),alignment=QtCore.Qt.AlignLeft)

            self.tab5_estimate_fT_input_layout_row2.addWidget(QLabel('C<sub>diel</sub>',maximumWidth=50,
                                                                     toolTip="Unit-area capacitance of the gate dielectric"),alignment=QtCore.Qt.AlignRight)
            self.tab5_estimate_fT_input_layout_row2.addWidget(self.tab5_estimate_fT_Cdiel)
            self.tab5_estimate_fT_input_layout_row2.addWidget(QLabel('µF/cm²',maximumWidth=40),alignment=QtCore.Qt.AlignLeft)

            self.tab5_estimate_fT_input_layout_row2.addWidget(QLabel('|V<sub>GS</sub>-V<sub>th</sub>|',maximumWidth=50,
                                                                     toolTip="Overdrive voltage"),alignment=QtCore.Qt.AlignRight)
            self.tab5_estimate_fT_input_layout_row2.addWidget(self.tab5_estimate_fT_Vov)
            self.tab5_estimate_fT_input_layout_row2.addWidget(QLabel('V',maximumWidth=20),alignment=QtCore.Qt.AlignLeft)

            self.tab5_estimate_fT_output_layout.addWidget(QLabel("Formula:"))
            self.tab5_estimate_fT_output_layout.addWidget(self.tab5_estimate_fT_formula_choice)
            self.tab5_estimate_fT_output_layout.addWidget(self.tab5_estimate_fT_button)
            self.tab5_estimate_fT_output_layout.addWidget(QLabel('f<sub>T, estimation</sub>', maximumWidth=50,
                                                                 toolTip="Transit frequency according to Meyer capacitance model"),
                                                          alignment=QtCore.Qt.AlignRight)
            self.tab5_estimate_fT_output_layout.addWidget(self.tab5_estimate_fT_result)
            self.tab5_estimate_fT_output_layout.addWidget(QLabel('Hz', maximumWidth=20), alignment=QtCore.Qt.AlignLeft)

            self.tab5_estimate_fT_layout.addLayout(self.tab5_estimate_fT_input_layout_row1)
            self.tab5_estimate_fT_layout.addLayout(self.tab5_estimate_fT_input_layout_row2)
            self.tab5_estimate_fT_layout.addLayout(self.tab5_estimate_fT_output_layout)


            # setup the fit interaction
            self.tab5_fitsetup_layout = QVBoxLayout()
            self.tab5_fitsetup_fTbounds_layout = QHBoxLayout()
            self.tab5_fitsetup_fTbounds_min = QSpinBox(value=1, singleStep=1, minimum=1,
                                                       maximum=999)
            self.tab5_fitsetup_fTbounds_min_magnitude = QComboBox()
            self.tab5_fitsetup_fTbounds_min_magnitude.addItem("Hz")
            self.tab5_fitsetup_fTbounds_min_magnitude.addItem("kHz")
            self.tab5_fitsetup_fTbounds_min_magnitude.addItem("MHz")

            self.tab5_fitsetup_fTbounds_max = QSpinBox(value=10, singleStep=1, minimum=1,
                                                       maximum=999)
            self.tab5_fitsetup_fTbounds_max_magnitude = QComboBox()
            self.tab5_fitsetup_fTbounds_max_magnitude.addItem("Hz")
            self.tab5_fitsetup_fTbounds_max_magnitude.addItem("kHz")
            self.tab5_fitsetup_fTbounds_max_magnitude.addItem("MHz")

            self.tab5_fitsetup_fTbounds_layout.addWidget(QLabel("f<sub>min</sub>"),alignment=QtCore.Qt.AlignRight)
            self.tab5_fitsetup_fTbounds_layout.addWidget(self.tab5_fitsetup_fTbounds_min)
            self.tab5_fitsetup_fTbounds_layout.addWidget(self.tab5_fitsetup_fTbounds_min_magnitude)
            self.tab5_fitsetup_fTbounds_layout.addWidget(QLabel("f<sub>max</sub>"),alignment=QtCore.Qt.AlignRight)
            self.tab5_fitsetup_fTbounds_layout.addWidget(self.tab5_fitsetup_fTbounds_max)
            self.tab5_fitsetup_fTbounds_layout.addWidget(self.tab5_fitsetup_fTbounds_max_magnitude)

            self.tab5_fitsetup_chooseFit_checkbox = QCheckBox("Fit transit frequency? (choose fit range for calculation)")
            self.tab5_fitsetup_chooseFit_checkbox.setChecked(True)

            self.tab5_fitsetup_layout.addWidget(self.tab5_fitsetup_chooseFit_checkbox)
            self.tab5_fitsetup_layout.addLayout(self.tab5_fitsetup_fTbounds_layout)


            # setup the results section
            self.tab5_result_layout = QGridLayout()
            self.tab5_result_empty_button = QPushButton('Empty')
            self.tab5_result_empty_button.clicked.connect(self.empty_sparam_results)
            self.tab5_result_fT = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")
            self.tab5_result_decay_slope = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")

            self.tab5_result_layout.addWidget(self.tab5_result_empty_button,0,1)
            self.tab5_result_layout.addWidget(QLabel("Transit Frequency f<sub>T</sub>"),1,0,alignment=QtCore.Qt.AlignRight)
            self.tab5_result_layout.addWidget(self.tab5_result_fT,1,1)
            self.tab5_result_layout.addWidget(QLabel("Hz"),1,2)
            self.tab5_result_layout.addWidget(QLabel("Current Gain Decay Rate (??) S"),2,0,alignment=QtCore.Qt.AlignRight)
            self.tab5_result_layout.addWidget(self.tab5_result_decay_slope,2,1)
            self.tab5_result_layout.addWidget(QLabel("dB/dec"),2,2)

            self.tab5_sparam_analyze_button = QPushButton('Execute S-Parameter Analysis')
            self.tab5_sparam_analyze_button.clicked.connect(self.analyze_sparam)

            self.tab5_leftside_interactive_layout.addLayout(self.tab5_file_selection_layout)
            self.tab5_leftside_interactive_layout.addLayout(self.tab5_estimate_fT_layout)
            self.tab5_leftside_interactive_layout.addWidget(self.hline())
            self.tab5_leftside_interactive_layout.addLayout(self.tab5_fitsetup_layout)
            self.tab5_leftside_interactive_layout.addLayout(self.tab5_result_layout)
            self.tab5_leftside_interactive_layout.addWidget(self.tab5_sparam_analyze_button)

            ##########################################################################
            # setup the graphing tabwidget where all the fit results are plotted (right side of the window)
            self.tab5_sparam_plot_tabs = QTabWidget()
            self.tab5_sparam_plot_tab_allSxx = QWidget()
            self.tab5_sparam_plot_tab_h21 = QWidget()

            self.tab5_sparam_plot_tabs.addTab(self.tab5_sparam_plot_tab_h21, 'h21')
            self.tab5_sparam_plot_tabs.addTab(self.tab5_sparam_plot_tab_allSxx, 'Sxx')


            self.tab5_sparam_plot_tab_h21.layout = QVBoxLayout(self.tab5_sparam_plot_tab_h21)
            self.tab5_sparam_plot_tab_allSxx.layout = QVBoxLayout(self.tab5_sparam_plot_tab_allSxx)

            canvas_width, canvas_height, canvas_dpi, canvas_min_height, canvas_min_width = 4, 3, 100, 300, 300

            self.tab5_plot_canvas_h21 = PlottingEnvironment_Canvas(self.tab5, width=canvas_width,
                                                                      height=canvas_height, dpi=canvas_dpi)
            self.tab5_plot_canvas_h21.setMinimumHeight(canvas_min_height)
            self.tab5_plot_canvas_h21.setMinimumWidth(canvas_min_width)
            self.tab5_toolbar_h21 = NavigationToolbar(self.tab5_plot_canvas_h21, self)
            self.tab5_sparam_plot_tab_h21.layout.addWidget(self.tab5_toolbar_h21, alignment=QtCore.Qt.AlignLeft)
            self.tab5_sparam_plot_tab_h21.layout.addWidget(self.tab5_plot_canvas_h21,
                                                              alignment=QtCore.Qt.AlignLeft)

            self.tab5_plot_canvas_allSxx = PlottingEnvironment_Canvas(self.tab5, width=canvas_width,
                                                                      height=canvas_height, dpi=canvas_dpi)
            self.tab5_plot_canvas_allSxx.setMinimumHeight(canvas_min_height)
            self.tab5_plot_canvas_allSxx.setMinimumWidth(canvas_min_width)
            self.tab5_toolbar_allSxx = NavigationToolbar(self.tab5_plot_canvas_allSxx, self)
            self.tab5_sparam_plot_tab_allSxx.layout.addWidget(self.tab5_toolbar_allSxx, alignment=QtCore.Qt.AlignLeft)
            self.tab5_sparam_plot_tab_allSxx.layout.addWidget(self.tab5_plot_canvas_allSxx,
                                                              alignment=QtCore.Qt.AlignLeft)

            self.tab5_complete_layout.addLayout(self.tab5_leftside_interactive_layout)
            self.tab5_complete_layout.addWidget(self.vline())
            self.tab5_complete_layout.addWidget(self.tab5_sparam_plot_tabs)
            self.tab5.layout.addLayout(self.tab5_complete_layout)

            self.tab5.layout.addWidget(self.hline())

            self.tab5_useroutput = QLabel("this tab is work in progress",toolTip="""<p>This window is used to display messages to the user without
                   the need to look at the Python console output.</p>""")
            self.tab5_useroutput.setFrameShape(QFrame.Panel)
            self.tab5_useroutput.setFrameShadow(QFrame.Sunken)
            self.tab5_useroutput.setLineWidth(3)

            self.tab5.layout.addWidget(self.tab5_useroutput)


        # tab6 contains analysis of transit curves with respect to temperature (Arrhenius plots etc)
        # for documentation, see the context menu in the "Help" section of the GUI
        def initialize_tab6():
            # set the default directory for choosing files in tab5
            self.default_directory_tab6 = 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM'

            self.tab6_complete_layout = QHBoxLayout()

            #########################################################
            # tab5 is divided into the left, interactive side where data can be chosen, fit parameters set and the
            # results can be displayed. right side will be only plot canvases
            self.tab6_leftside_interactive_layout = QVBoxLayout()

            # setup of the upper left part (file selection for the TLM analysis)
            self.tab6_file_button = QPushButton('Choose Files')
            self.tab6_file_button.clicked.connect(self.choose_filesArrhenius)
            self.tab6_file_remove_button = QPushButton('Remove Selected')
            self.tab6_file_remove_button.clicked.connect(self.remove_arrhenius_file)
            self.tab6_file_empty_button = QPushButton('Empty List')
            self.tab6_file_empty_button.clicked.connect(self.empty_arrhenius_file_list)
            # the program is not displaying whole paths but solely filenames. for reading the data, the whole
            # path is needed, so they have to be stored in combination -> this dictionary holds the references and
            # the QListWidget shows many files in a clean fashion, however only the active one is analyzed!

            self.tab6_file_paths = {}  # filename:path
            self.tab6_filelist = QListWidget(minimumHeight=120, maximumHeight=80, minimumWidth=50)
            self.tab6_file_selection_layout = QVBoxLayout()
            self.tab6_file_selection_buttons = QHBoxLayout()
            self.tab6_file_selection_buttons.addWidget(self.tab6_file_button)
            self.tab6_file_selection_buttons.addWidget(self.tab6_file_empty_button)
            self.tab6_file_selection_buttons.addWidget(self.tab6_file_remove_button)
            self.tab6_file_selection_layout.addLayout(self.tab6_file_selection_buttons)
            self.tab6_file_selection_layout.addWidget(self.tab6_filelist)


            # setup the fit interaction
            #self.tab6_fitsetup_layout = QVBoxLayout()
            # setup fit parameters C_ox, fd and sd
            self.tab6_fitsetup = QGridLayout()
            self.tab6_carrier_type_button = QPushButton('p', maximumWidth=30, checkable=True)
            self.tab6_carrier_type_button.clicked.connect(self.update_carrier_type_button_text)
            self.tab6_analysis_capacitance_input = QDoubleSpinBox(value=0.65, singleStep=0.01, minimum=0.00,
                                                                  maximum=5.00)
            self.tab6_analysis_first_derivative_threshold_input = QDoubleSpinBox(value=0.00, singleStep=0.01,
                                                                                 minimum=0.00, maximum=1.00)
            self.tab6_analysis_second_derivative_threshold_input = QDoubleSpinBox(value=0.00, singleStep=0.01,
                                                                                  minimum=0.00, maximum=1.00)
            self.tab6_analysis_smoothing_factor = QDoubleSpinBox(value=0.25, singleStep=0.01, minimum=0.00,
                                                                 maximum=1.00)
            fi_x, fi_y = 50, 20  # fixed size for spinboxes
            self.tab6_analysis_capacitance_input.setFixedSize(fi_x, fi_y)
            self.tab6_analysis_first_derivative_threshold_input.setFixedSize(fi_x, fi_y)
            self.tab6_analysis_second_derivative_threshold_input.setFixedSize(fi_x, fi_y)
            self.tab6_analysis_smoothing_factor.setFixedSize(fi_x, fi_y)
            self.tab6_fitsetup.addWidget(QLabel('Carrier Type'), 0, 0, alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(self.tab6_carrier_type_button, 0, 1, alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(QLabel('Oxide Capacitance [µF/cm²]:'), 1, 0, alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(self.hline(), 3, 0, 1, 2)
            self.tab6_fitsetup.addWidget(QLabel('Linearity Identification - dI/dV (norm.) >',
                                                toolTip="""<p>This value sets the lower limit to the normalized (1st) derivative,
                                                            above which datapoints are considered in the linear regime.</p>"""),
                                         4, 0,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(QLabel('Linearity Identification - d²I/dV² (norm.) <',
                                                toolTip="""<p>This value sets the upper limit to the normalized (2nd) derivative,
                                                            below which datapoints are considered in the linear regime.</p>"""),
                                         5, 0,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(QLabel('Smoothing Factor - (Gaussian σ):',
                                                toolTip="""<p>Data is smoothed to reduce artifacts during derivation.</br>
                                                            This value does NOT change fitting results, it only influences the automatic
                                                                         determination of points to include in the fit (visible in the plots)!<br>
                                                            This values is used as standard deviation in the gaussian broadening kernel.</p>"""),
                                         6, 0,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(self.tab6_analysis_capacitance_input, 1, 1, alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(self.tab6_analysis_first_derivative_threshold_input, 4, 1,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(self.tab6_analysis_second_derivative_threshold_input, 5, 1,
                                         alignment=QtCore.Qt.AlignRight)
            self.tab6_fitsetup.addWidget(self.tab6_analysis_smoothing_factor, 6, 1,
                                         alignment=QtCore.Qt.AlignRight)


            # setup the results section
            self.tab6_result_layout = QGridLayout()
            self.tab6_result_empty_button = QPushButton('Empty')
            self.tab6_result_empty_button.clicked.connect(self.print_shit)
            #self.tab6_result_fT = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")
            #self.tab6_result_decay_slope = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")

            self.tab6_arrhenius_select_direction_layout = QHBoxLayout()
            self.tab6_arrhenius_select_direction_fwd = QRadioButton("Forward")  # using only forward data
            self.tab6_arrhenius_select_direction_back = QRadioButton("Backward")  # using only backward data
            self.tab6_arrhenius_select_direction_mean = QRadioButton("Mean", checked=True)  # using complete data; Vth determination is 1/2*(Vth_fwd+Vth_back)
            self.tab6_arrhenius_select_direction_layout.addWidget(QLabel("Select direction: "), alignment=QtCore.Qt.AlignLeft)
            self.tab6_arrhenius_select_direction_layout.addWidget(self.tab6_arrhenius_select_direction_fwd,alignment=QtCore.Qt.AlignLeft)
            self.tab6_arrhenius_select_direction_layout.addWidget(self.tab6_arrhenius_select_direction_back,alignment=QtCore.Qt.AlignLeft)
            self.tab6_arrhenius_select_direction_layout.addWidget(self.tab6_arrhenius_select_direction_mean,alignment=QtCore.Qt.AlignLeft)

            self.tab6_arrhenius_analyze_button = QPushButton('Execute Arrhenius Analysis')
            self.tab6_arrhenius_analyze_button.clicked.connect(self.analyze_arrhenius)

            self.tab6_leftside_interactive_layout.addLayout(self.tab6_file_selection_layout)
            self.tab6_leftside_interactive_layout.addLayout(self.tab6_fitsetup)
            self.tab6_leftside_interactive_layout.addLayout(self.tab6_arrhenius_select_direction_layout)
            self.tab6_leftside_interactive_layout.addWidget(self.tab6_arrhenius_analyze_button)


            ##########################################################################
            # setup the graphing tabwidget where all the fit results are plotted (right side of the window)
            self.tab6_arrhenius_plot_tabs = QTabWidget()
            self.tab6_arrhenius_plot_mu0 = QWidget()
            self.tab6_arrhenius_plot_rcw = QWidget()

            self.tab6_arrhenius_plot_tabs.addTab(self.tab6_arrhenius_plot_mu0, 'µ0 (T)')
            self.tab6_arrhenius_plot_tabs.addTab(self.tab6_arrhenius_plot_rcw, 'RcW (T)')

            self.tab6_arrhenius_plot_mu0.layout = QVBoxLayout(self.tab6_arrhenius_plot_mu0)
            self.tab6_arrhenius_plot_rcw.layout = QVBoxLayout(self.tab6_arrhenius_plot_rcw)

            canvas_width, canvas_height, canvas_dpi, canvas_min_height, canvas_min_width = 4, 3, 100, 300, 300

            self.tab6_plot_canvas_arrhenius_mu0 = PlottingEnvironment_Canvas(self.tab6, width=canvas_width,
                                                                      height=canvas_height, dpi=canvas_dpi)
            self.tab6_plot_canvas_arrhenius_mu0.setMinimumHeight(canvas_min_height)
            self.tab6_plot_canvas_arrhenius_mu0.setMinimumWidth(canvas_min_width)
            self.tab6_toolbar_arrhenius_mu0 = NavigationToolbar(self.tab6_plot_canvas_arrhenius_mu0, self)
            self.tab6_arrhenius_plot_mu0.layout.addWidget(self.tab6_toolbar_arrhenius_mu0, alignment=QtCore.Qt.AlignLeft)
            self.tab6_arrhenius_plot_mu0.layout.addWidget(self.tab6_plot_canvas_arrhenius_mu0,
                                                              alignment=QtCore.Qt.AlignLeft)

            self.tab6_plot_canvas_arrhenius_rcw = PlottingEnvironment_Canvas(self.tab6, width=canvas_width,
                                                                             height=canvas_height, dpi=canvas_dpi)
            self.tab6_plot_canvas_arrhenius_rcw.setMinimumHeight(canvas_min_height)
            self.tab6_plot_canvas_arrhenius_rcw.setMinimumWidth(canvas_min_width)
            self.tab6_toolbar_arrhenius_rcw = NavigationToolbar(self.tab6_plot_canvas_arrhenius_rcw, self)
            self.tab6_arrhenius_plot_rcw.layout.addWidget(self.tab6_toolbar_arrhenius_rcw,
                                                           alignment=QtCore.Qt.AlignLeft)
            self.tab6_arrhenius_plot_rcw.layout.addWidget(self.tab6_plot_canvas_arrhenius_rcw,
                                                           alignment=QtCore.Qt.AlignLeft)

            self.tab6_complete_layout.addLayout(self.tab6_leftside_interactive_layout)
            self.tab6_complete_layout.addWidget(self.tab6_arrhenius_plot_tabs)
            self.tab6.layout.addLayout(self.tab6_complete_layout)

            self.tab6.layout.addWidget(self.hline())

            self.tab6_useroutput = QLabel("this tab is work in progress",toolTip="""<p>This window is used to display messages to the user without
                   the need to look at the Python console output.</p>""")
            self.tab6_useroutput.setFrameShape(QFrame.Panel)
            self.tab6_useroutput.setFrameShadow(QFrame.Sunken)
            self.tab6_useroutput.setLineWidth(3)

            self.tab6.layout.addWidget(self.tab6_useroutput)

            """
            # below is just so i dont have to click every time while testing
            a = {
                'TWJB01b_W200_L8_G10_T350_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L8_G10_T350_lin_GOETT.txt',
                'TWJB01b_W200_L20_G10_T350_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L20_G10_T350_lin_GOETT.txt',
                'TWJB01b_W200_L40_G10_T350_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L40_G10_T350_lin_GOETT.txt',
                'TWJB01b_W200_L60_G10_T350_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L60_G10_T350_lin_GOETT.txt',
                'TWJB01b_W200_L80_G10_T350_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L80_G10_T350_lin_GOETT.txt',
                'TWJB01b_W200_L8_G10_T100_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L8_G10_T100_lin_GOETT.txt',
                'TWJB01b_W200_L20_G10_T100_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L20_G10_T100_lin_GOETT.txt',
                'TWJB01b_W200_L40_G10_T100_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L40_G10_T100_lin_GOETT.txt',
                'TWJB01b_W200_L60_G10_T100_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L60_G10_T100_lin_GOETT.txt',
                'TWJB01b_W200_L80_G10_T100_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L80_G10_T100_lin_GOETT.txt',
                'TWJB01b_W200_L8_G10_T250_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L8_G10_T250_lin_GOETT.txt',
                'TWJB01b_W200_L20_G10_T250_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L20_G10_T250_lin_GOETT.txt',
                'TWJB01b_W200_L40_G10_T250_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L40_G10_T250_lin_GOETT.txt',
                'TWJB01b_W200_L60_G10_T250_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L60_G10_T250_lin_GOETT.txt',
                'TWJB01b_W200_L80_G10_T250_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L80_G10_T250_lin_GOETT.txt',
                'TWJB01b_W200_L8_G10_T300_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L8_G10_T300_lin_GOETT.txt',
                'TWJB01b_W200_L20_G10_T300_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L20_G10_T300_lin_GOETT.txt',
                'TWJB01b_W200_L40_G10_T300_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L40_G10_T300_lin_GOETT.txt',
                'TWJB01b_W200_L60_G10_T300_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L60_G10_T300_lin_GOETT.txt',
                'TWJB01b_W200_L80_G10_T300_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L80_G10_T300_lin_GOETT.txt',
                'TWJB01b_W200_L8_G10_T200_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L8_G10_T200_lin_GOETT.txt',
                'TWJB01b_W200_L20_G10_T200_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L20_G10_T200_lin_GOETT.txt',
                'TWJB01b_W200_L40_G10_T200_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L40_G10_T200_lin_GOETT.txt',
                'TWJB01b_W200_L60_G10_T200_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L60_G10_T200_lin_GOETT.txt',
                'TWJB01b_W200_L80_G10_T200_lin_GOETT.txt': 'C:/Users/wollandt_admin/MPI_Cloud/data/other_samples/TWJB/TWJB01/temperature_dependence/all_extracted_data/TLM/TWJB01b_W200_L80_G10_T200_lin_GOETT.txt'
            }

            for f in a:
                self.tab6_file_paths[f] = a[f]
                self.tab6_filelist.addItem(f)
            """

        # tab7 contains analysis of inverter transfer curves
        # for documentation, see the context menu in the "Help" section of the GUI
        def initialize_tab7():
            # set the default directory for choosing files in tab5
            self.default_directory_tab7 = 'C:/Users/wollandt_admin/MPI_Cloud/shared_data/Micha/2022-03_inverter_for_GUI/data'

            self.tab7_complete_layout = QHBoxLayout()

            #########################################################
            # tab5 is divided into the left, interactive side where data can be chosen, fit parameters set and the
            # results can be displayed. right side will be only plot canvases
            self.tab7_leftside_interactive_layout = QVBoxLayout()

            # setup of the upper left part (file selection for the inverter analysis)
            self.tab7_file_button = QPushButton('Choose Files')
            self.tab7_file_button.clicked.connect(self.choose_filesInverter)
            self.tab7_file_remove_button = QPushButton('Remove Selected')
            self.tab7_file_remove_button.clicked.connect(self.remove_inverter_file)
            self.tab7_file_empty_button = QPushButton('Empty List')
            self.tab7_file_empty_button.clicked.connect(self.empty_inverter_file_list)
            # the program is not displaying whole paths but solely filenames. for reading the data, the whole
            # path is needed, so they have to be stored in combination -> this dictionary holds the references and
            # the QListWidget shows many files in a clean fashion, however only the active one is analyzed!

            self.tab7_file_paths = {}  # filename:path
            self.tab7_filelist = QListWidget(minimumHeight=120, maximumHeight=80, minimumWidth=50)
            self.tab7_file_selection_layout = QVBoxLayout()
            self.tab7_file_selection_buttons = QHBoxLayout()
            self.tab7_file_selection_buttons.addWidget(self.tab7_file_button)
            self.tab7_file_selection_buttons.addWidget(self.tab7_file_empty_button)
            self.tab7_file_selection_buttons.addWidget(self.tab7_file_remove_button)
            self.tab7_file_selection_layout.addLayout(self.tab7_file_selection_buttons)
            self.tab7_file_selection_layout.addWidget(self.tab7_filelist)

            # setup the fit interaction
            # self.tab6_fitsetup_layout = QVBoxLayout()
            # setup fit parameters C_ox, fd and sd
            self.tab7_fitsetup = QGridLayout()
            fi_x, fi_y = 50, 20  # fixed size for spinboxes
            self.tab7_analysis_smoothing_factor = QDoubleSpinBox(value=0.25,singleStep=0.01,maximum=1,minimum=0.01)
            self.tab7_analysis_smoothing_factor.setFixedSize(fi_x, fi_y)
            self.tab7_analysis_smoothing_factor.valueChanged.connect(self.analyze_inverter)
            self.tab7_analysis_smooth_bool = QCheckBox("Use Smoothing?",checked=False,toolTip="""<p>Smoothing might result in
            slightly incorrect values for the gain. Therefore smoothing might not be in best interest always.</p>""")


            self.tab7_analysis_supply_voltage = QLineEdit(placeholderText="---", maximumWidth=50)

            self.tab7_fitsetup.addWidget(self.hline(), 1, 0, 1, 4)
            self.tab7_fitsetup.addWidget(self.tab7_analysis_smooth_bool, 2, 0, 1, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab7_fitsetup.addWidget(QLabel('Smoothing Factor - (Gaussian σ):',
                                                toolTip="""<p>Data is smoothed to reduce artifacts during derivation.</br>
                                                                        </p>"""), 2, 1, 1, 2, alignment=QtCore.Qt.AlignRight)
            self.tab7_fitsetup.addWidget(self.tab7_analysis_smoothing_factor, 2, 3, 1, 1, alignment=QtCore.Qt.AlignLeft)
            self.tab7_fitsetup.addWidget(QLabel('Supply Voltage V<sub>DD</sub> [V]',
                                                toolTip="""<p>Value will be read from file if possible. Otherwise set a value here.</br>
                                                                        </p>"""), 3, 0, 1, 3, alignment=QtCore.Qt.AlignRight)
            self.tab7_fitsetup.addWidget(self.tab7_analysis_supply_voltage, 3, 3, 1, 1, alignment=QtCore.Qt.AlignLeft)

            # setup the results section
            self.tab7_result_layout = QGridLayout()
            self.tab7_results_choose_linestyle = QComboBox()
            self.tab7_results_choose_linestyle.addItems(['.','o','x','.-','o-','x-','-','--'])
            self.tab7_result_empty_button = QPushButton('Empty Results')
            self.tab7_result_empty_button.clicked.connect(self.empty_inverter_results)
            self.tab7_result_trip_fwd = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")
            self.tab7_result_trip_bwd = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")
            self.tab7_result_gain_fwd = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")
            self.tab7_result_gain_bwd = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")
            self.tab7_result_noiseMargin_fwd = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")
            self.tab7_result_noiseMargin_bwd = QLineEdit(readOnly=True,placeholderText="---",maximumWidth=100,toolTip="---")

            self.tab7_result_layout.addWidget(QLabel("Linestyle"),                                  0,1,1,1)
            self.tab7_result_layout.addWidget(self.tab7_results_choose_linestyle,                   0,2,1,1)
            self.tab7_result_layout.addWidget(self.tab7_result_empty_button,                        0,3,1,2)
            self.tab7_result_layout.addWidget(QLabel("Trip Point (V): "),                           1,1,1,1)
            self.tab7_result_layout.addWidget(QLabel("Forward"),                                    1,2,1,1)
            self.tab7_result_layout.addWidget(self.tab7_result_trip_fwd,                            1,3,1,1)
            self.tab7_result_layout.addWidget(QLabel("Backward"),                                   1,4,1,1)
            self.tab7_result_layout.addWidget(self.tab7_result_trip_bwd,                            1,5,1,1)
            self.tab7_result_layout.addWidget(QLabel("Gain: "),                                     2,1,1,1)
            self.tab7_result_layout.addWidget(QLabel("Forward"),                                    2,2,1,1)
            self.tab7_result_layout.addWidget(self.tab7_result_gain_fwd,                            2,3,1,1)
            self.tab7_result_layout.addWidget(QLabel("Backward"),                                   2,4,1,1)
            self.tab7_result_layout.addWidget(self.tab7_result_gain_bwd,                            2,5,1,1)
            self.tab7_result_layout.addWidget(QLabel("Noise Margin: "),                             3,1,1,1)
            self.tab7_result_layout.addWidget(QLabel("Forward"),                                    3,2,1,1)
            self.tab7_result_layout.addWidget(self.tab7_result_noiseMargin_fwd,                     3,3,1,1)
            self.tab7_result_layout.addWidget(QLabel("Backward"),                                   3,4,1,1)
            self.tab7_result_layout.addWidget(self.tab7_result_noiseMargin_bwd,                     3,5,1,1)


            self.tab7_inverter_analyze_button = QPushButton('Execute Inverter Analysis')
            self.tab7_inverter_analyze_button.clicked.connect(self.analyze_inverter)

            self.tab7_leftside_interactive_layout.addLayout(self.tab7_file_selection_layout)
            self.tab7_leftside_interactive_layout.addLayout(self.tab7_fitsetup)
            self.tab7_leftside_interactive_layout.addLayout(self.tab7_result_layout)
            self.tab7_leftside_interactive_layout.addWidget(self.tab7_inverter_analyze_button)

            ##########################################################################
            # setup the graphing tabwidget where all the fit results are plotted (right side of the window)
            self.tab7_inverter_plot_tabs = QTabWidget()
            self.tab7_inverter_plot_Vinout = QWidget()
            self.tab7_inverter_plot_deriv = QWidget()

            self.tab7_inverter_plot_tabs.addTab(self.tab7_inverter_plot_Vinout, 'V_out(V_in)')
            self.tab7_inverter_plot_tabs.addTab(self.tab7_inverter_plot_deriv, 'Derivative')

            self.tab7_inverter_plot_Vinout.layout = QVBoxLayout(self.tab7_inverter_plot_Vinout)
            self.tab7_inverter_plot_deriv.layout = QVBoxLayout(self.tab7_inverter_plot_deriv)

            canvas_width, canvas_height, canvas_dpi, canvas_min_height, canvas_min_width = 4, 3, 100, 300, 300

            self.tab7_plot_canvas_inverter_Vinout = PlottingEnvironment_Canvas(self.tab7, width=canvas_width,
                                                                               height=canvas_height, dpi=canvas_dpi)
            self.tab7_plot_canvas_inverter_Vinout.setMinimumHeight(canvas_min_height)
            self.tab7_plot_canvas_inverter_Vinout.setMinimumWidth(canvas_min_width)
            self.tab7_toolbar_inverter_Vinout = NavigationToolbar(self.tab7_plot_canvas_inverter_Vinout, self)
            self.tab7_inverter_plot_Vinout.layout.addWidget(self.tab7_toolbar_inverter_Vinout,
                                                            alignment=QtCore.Qt.AlignLeft)
            self.tab7_inverter_plot_Vinout.layout.addWidget(self.tab7_plot_canvas_inverter_Vinout,
                                                            alignment=QtCore.Qt.AlignLeft)

            self.tab7_plot_canvas_inverter_deriv = PlottingEnvironment_Canvas(self.tab7, width=canvas_width,
                                                                              height=canvas_height, dpi=canvas_dpi)
            self.tab7_plot_canvas_inverter_deriv.setMinimumHeight(canvas_min_height)
            self.tab7_plot_canvas_inverter_deriv.setMinimumWidth(canvas_min_width)
            self.tab7_toolbar_inverter_deriv = NavigationToolbar(self.tab7_plot_canvas_inverter_deriv, self)
            self.tab7_inverter_plot_deriv.layout.addWidget(self.tab7_toolbar_inverter_deriv,
                                                           alignment=QtCore.Qt.AlignLeft)
            self.tab7_inverter_plot_deriv.layout.addWidget(self.tab7_plot_canvas_inverter_deriv,
                                                           alignment=QtCore.Qt.AlignLeft)

            self.tab7_complete_layout.addLayout(self.tab7_leftside_interactive_layout)
            self.tab7_complete_layout.addWidget(self.tab7_inverter_plot_tabs)
            self.tab7.layout.addLayout(self.tab7_complete_layout)

            self.tab7.layout.addWidget(self.hline())

            self.tab7_useroutput = QLabel("this tab is work in progress", toolTip="""<p>This window is used to display messages to the user without
                       the need to look at the Python console output.</p>""")
            self.tab7_useroutput.setFrameShape(QFrame.Panel)
            self.tab7_useroutput.setFrameShadow(QFrame.Sunken)
            self.tab7_useroutput.setLineWidth(3)

            self.tab7.layout.addWidget(self.tab7_useroutput)

        initialize_tab1()
        initialize_tab2()
        initialize_tab3()
        initialize_tab5()
        initialize_tab6()
        initialize_tab7()
        # settings tab should be initialized last. reason: it changes variables that have to be introduced before
        initialize_tab4()

        self.root_layout.addWidget(self.tabs)
        self.setLayout(self.root_layout)
        #self.analyze_arrhenius() # this line was used during the coding of the arrhenius plot. if still here in october, can be removed

    ##############
    # functions handling settings
    ##############

    def save_settings(self):
        settings_dict = {"settings_timestamp": time.strftime("%a, %Y-%m-%d %H:%M:%S"),
                         "manual_xrange":{"linfit":(self.tab4_tab1settings_linfit_xmin.value(), self.tab4_tab1settings_linfit_xmax.value()),
                                        "satfit":(self.tab4_tab1settings_satfit_xmin.value(), self.tab4_tab1settings_satfit_xmax.value()),
                                        "sswfit":(self.tab4_tab1settings_sswfit_xmin.value(), self.tab4_tab1settings_sswfit_xmax.value())},
                         "use_manual_xrange":{"linfit": self.tab4_tab1settings_linfit_usefixed_xrange.isChecked(),
                                              "satfit": self.tab4_tab1settings_satfit_usefixed_xrange.isChecked(),
                                              "sswfit": self.tab4_tab1settings_sswfit_usefixed_xrange.isChecked()},
                         "datafile_preset": self.tab4_set_datapreset.currentItem().text(),
                         "L_correction":{"active":self.tab4_automatic_Lcorrect.isChecked(),"database":self.default_L_correct_db},
                         "custom_columns":{"names":self.tab4_set_custom_column_names.text(),
                                           "skiprows":self.tab4_set_custom_skiprows.value()},
                         "execute_mTLM":self.tab4_execute_mTLM.isChecked(),
                         "plotdata_absolute": self.tab4_set_tab1_plotdata_absolute.isChecked(),
                         "default_directory_tab1": self.default_directory_tab1,
                         "default_directory_tab3": self.default_directory_tab3,
                         "default_directory_tab5": self.default_directory_tab5,
                         "default_directory_tab6": self.default_directory_tab6,
                         "default_directory_tab7": self.default_directory_tab7,
                         "default_directory_savefig": self.default_directory_savefig,
                         "tab1_plot_chosen_data_overwrite_checkbox": self.tab1_plot_chosen_data_overwrite_checkbox.isChecked(),
                         "tab1_plot_scale_menu": (self.tab1_plot_scale_menu.currentText(), self.tab1_plot_scale_menu.currentIndex()),
                         "tab3_result_plot_all_transfercurves_checkbox": self.tab3_result_plot_all_transfercurves_checkbox.isChecked(),
                         "tab3_result_checkboxes":
                             {"save_all_plots":self.tab3_result_save_all_plots_checkbox.isChecked(), "limit_xrange":self.tab4_tab3_result_limit_plot_xrange.isChecked()},
                         "capacitance":{"tab1": np.round(self.tab1_analysis_capacitance_input.value(),2),
                                        "tab3": np.round(self.tab3_analysis_capacitance_input.value(),2),
                                        "tab6": np.round(self.tab6_analysis_capacitance_input.value(),2)},
                         "carrier_typeP": {"tab1": self.tab1_carrier_type_button.isChecked(),
                                           "tab3": self.tab3_carrier_type_button.isChecked(),
                                           "tab6": self.tab6_carrier_type_button.isChecked()},
                         "tab1_result":{"showfwd" : self.tab1_resultshowfwd.isChecked(),
                                        "showback": self.tab1_resultshowback.isChecked(),
                                        "showmean": self.tab1_resultshowmean.isChecked()},
                         "tab3_TLM_direction": {"fwd" : self.tab3_TLM_select_direction_fwd.isChecked(),
                                                "back": self.tab3_TLM_select_direction_back.isChecked(),
                                                "mean": self.tab3_TLM_select_direction_mean.isChecked()},
                         "tab6_arrhenius_direction": {"fwd": self.tab6_arrhenius_select_direction_fwd.isChecked(),
                                                     "back": self.tab6_arrhenius_select_direction_back.isChecked(),
                                                     "mean": self.tab6_arrhenius_select_direction_mean.isChecked()},
                         "tab1_results":{"oor_lin": self.tab1_results_choose_oor_regime.isChecked(),
                                         "ssw_sat": self.tab1_results_choose_ssw_regime.isChecked(),
                                         "vth_sat": self.tab1_results_choose_vth_regime.isChecked()},
                         "smoothing_factors":{"tab1":self.tab1_analysis_smoothing_factor.value(),
                                              "tab3":self.tab3_analysis_smoothing_factor.value(),
                                              #"tab5":self.tab1_analysis_smoothing_factor.value(),
                                              "tab6":self.tab6_analysis_smoothing_factor.value(),
                                              "tab7":self.tab7_analysis_smoothing_factor.value()},
                         "linestyles":{'tab1':self.tab1_choose_linestyle.currentIndex(),
                                       'tab7':self.tab7_results_choose_linestyle.currentIndex()},
                         "tab1_onOffRatio_avgWindow": self.tab4_set_tab1_oor_avg_window.value(),
                         "tab3_rcw_avgWindow": self.tab4_set_tab3_rcw_avg_window.value(),
                         "tab3_TLM_xmin_auto": self.tab4_set_TLM_xmin_automatic.isChecked(),
                         "default_tab": self.tab4_default_tab.currentText(),
                         "tab5_fitsetup":{"fT_fit_min": self.tab5_fitsetup_fTbounds_min.value(),
                                          "fT_fit_min_magnitude": self.tab5_fitsetup_fTbounds_min_magnitude.currentIndex(),
                                          "fT_fit_max": self.tab5_fitsetup_fTbounds_max.value(),
                                          "fT_fit_max_magnitude": self.tab5_fitsetup_fTbounds_max_magnitude.currentIndex(),
                                          "fT_fit_bool": self.tab5_fitsetup_chooseFit_checkbox.isChecked()
                                          },
                         "tab5_estimate_settings":{
                                            "formula":self.tab5_estimate_fT_formula_choice.currentIndex(),
                                            "RcW":self.tab5_estimate_fT_RcW.text(),
                                            "mu0":self.tab5_estimate_fT_mu0.text(),
                                            "C":self.tab5_estimate_fT_Cdiel.text(),
                                            "Vov":self.tab5_estimate_fT_Vov.text(),
                                            "L":self.tab5_estimate_fT_L.text(),
                                            "Lov":self.tab5_estimate_fT_Lov.text(),},
                         }

        with open(self.settings, "w") as f:
            self.tab4_show_settings_filecontent.clear()
            for key, val in settings_dict.items():
                self.tab4_show_settings_filecontent.addItem(f"{key}:{val}")

            f.write(json.dumps(settings_dict))

        self.print_useroutput('Settings saved successfully.', self.tab4_outputline)
        print(f"[{time.strftime('%H:%M:%S')}] Settings file updated successfully.")

        return True

    def load_settings(self):
        try:
            with open(self.settings, "r") as f:
                settings_dict = json.loads(f.read())

            self.tab4_show_settings_filecontent.clear()
            for key, val in settings_dict.items():
                self.tab4_show_settings_filecontent.addItem(f"{key}:{val}")
        except:
            print_exc()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Settings not found!')
            msg.setText(
                "The file 'settings.ini' seems to be missing in the currently working directory (CWD).")
            msg.setInformativeText(
                """Please make sure the 'settings.ini' file can be found by placing it in the CWD.""")
            msg.exec_()
        try:
            # suppress command line output because changing the settings on some checkbuttons may result in a print
            # command...eg setting the plotting scale will try to plot the data which is not possible
            sys.stdout = open(os.devnull, "w")
            self.tab1_results_choose_oor_regime.setChecked(settings_dict["tab1_results"]["oor_lin"])
            self.tab1_results_choose_vth_regime.setChecked(settings_dict["tab1_results"]["vth_sat"])
            self.tab1_results_choose_ssw_regime.setChecked(settings_dict["tab1_results"]["ssw_sat"])
            self.tab4_set_tab1_plotdata_absolute.setChecked(settings_dict["plotdata_absolute"])
            self.tab1_plot_chosen_data_overwrite_checkbox.setChecked(
                settings_dict['tab1_plot_chosen_data_overwrite_checkbox'])
            self.tab1_plot_scale_menu.setCurrentIndex(settings_dict["tab1_plot_scale_menu"][1])
            self.tab3_result_plot_all_transfercurves_checkbox.setChecked(
                settings_dict["tab3_result_plot_all_transfercurves_checkbox"])
            self.tab3_result_save_all_plots_checkbox.setChecked(
                settings_dict["tab3_result_checkboxes"]["save_all_plots"])
            self.tab4_tab3_result_limit_plot_xrange.setChecked(
                settings_dict["tab3_result_checkboxes"]["limit_xrange"])
            self.tab4_tab1settings_linfit_usefixed_xrange.setChecked(settings_dict["use_manual_xrange"]["linfit"])
            self.tab4_tab1settings_satfit_usefixed_xrange.setChecked(settings_dict["use_manual_xrange"]["satfit"])
            self.tab4_tab1settings_sswfit_usefixed_xrange.setChecked(settings_dict["use_manual_xrange"]["sswfit"])
            self.tab4_tab1settings_linfit_xmin.setValue(settings_dict["manual_xrange"]["linfit"][0])
            self.tab4_tab1settings_linfit_xmax.setValue(settings_dict["manual_xrange"]["linfit"][1])
            self.tab4_tab1settings_satfit_xmin.setValue(settings_dict["manual_xrange"]["satfit"][0])
            self.tab4_tab1settings_satfit_xmax.setValue(settings_dict["manual_xrange"]["satfit"][1])
            self.tab4_tab1settings_sswfit_xmin.setValue(settings_dict["manual_xrange"]["sswfit"][0])
            self.tab4_tab1settings_sswfit_xmax.setValue(settings_dict["manual_xrange"]["sswfit"][1])
            self.tab1_analysis_capacitance_input.setValue(settings_dict["capacitance"]["tab1"])
            self.tab3_analysis_capacitance_input.setValue(settings_dict["capacitance"]["tab3"])
            self.tab6_analysis_capacitance_input.setValue(settings_dict["capacitance"]["tab6"])
            for item in self.tab4_set_datapreset.findItems(settings_dict["datafile_preset"],QtCore.Qt.MatchFixedString):
                self.tab4_set_datapreset.setCurrentRow(self.tab4_set_datapreset.row(item))

            self.tab4_set_custom_column_names.setText(settings_dict["custom_columns"]["names"])
            self.tab4_set_custom_skiprows.setValue(settings_dict["custom_columns"]["skiprows"])
            self.tab4_execute_mTLM.setChecked(settings_dict["execute_mTLM"])
            self.default_directory_tab1 = settings_dict["default_directory_tab1"]
            self.tab4_show_tab1_default_directory.setPlaceholderText(self.default_directory_tab1)
            self.tab4_show_tab1_default_directory.setToolTip(self.default_directory_tab1)
            self.default_directory_tab3 = settings_dict["default_directory_tab3"]
            self.tab4_show_tab3_default_directory.setPlaceholderText(self.default_directory_tab3)
            self.tab4_show_tab3_default_directory.setToolTip(self.default_directory_tab3)
            self.default_directory_tab5 = settings_dict["default_directory_tab5"]
            self.tab4_show_tab5_default_directory.setPlaceholderText(self.default_directory_tab5)
            self.tab4_show_tab5_default_directory.setToolTip(self.default_directory_tab5)
            self.default_directory_tab6 = settings_dict["default_directory_tab6"]
            self.tab4_show_tab6_default_directory.setPlaceholderText(self.default_directory_tab6)
            self.tab4_show_tab6_default_directory.setToolTip(self.default_directory_tab6)
            self.default_directory_savefig = settings_dict["default_directory_savefig"]
            self.tab4_show_savefig_default_directory.setPlaceholderText(self.default_directory_savefig)
            self.tab4_show_savefig_default_directory.setToolTip(self.default_directory_savefig)

            self.tab1_resultshowfwd.setChecked(settings_dict["tab1_result"]["showfwd"])
            self.tab1_resultshowback.setChecked(settings_dict["tab1_result"]["showback"])
            self.tab1_resultshowmean.setChecked(settings_dict["tab1_result"]["showmean"])
            self.tab3_TLM_select_direction_fwd.setChecked(settings_dict["tab3_TLM_direction"]["fwd"])
            self.tab3_TLM_select_direction_back.setChecked(settings_dict["tab3_TLM_direction"]["back"])
            self.tab3_TLM_select_direction_mean.setChecked(settings_dict["tab3_TLM_direction"]["mean"])
            self.tab6_arrhenius_select_direction_fwd.setChecked(settings_dict["tab6_arrhenius_direction"]["fwd"])
            self.tab6_arrhenius_select_direction_back.setChecked(settings_dict["tab6_arrhenius_direction"]["back"])
            self.tab6_arrhenius_select_direction_mean.setChecked(settings_dict["tab6_arrhenius_direction"]["mean"])
            self.tab1_carrier_type_button.setChecked(settings_dict["carrier_typeP"]["tab1"])
            self.tab3_carrier_type_button.setChecked(settings_dict["carrier_typeP"]["tab3"])
            self.tab6_carrier_type_button.setChecked(settings_dict["carrier_typeP"]["tab6"])
            self.tab4_set_tab1_oor_avg_window.setValue(settings_dict["tab1_onOffRatio_avgWindow"])
            self.tab4_set_tab3_rcw_avg_window.setValue(settings_dict["tab3_rcw_avgWindow"])
            self.tab4_set_TLM_xmin_automatic.setChecked(settings_dict["tab3_TLM_xmin_auto"])


            if settings_dict["default_tab"] == "Transfer Analysis":
                self.tabs.setCurrentIndex(0)
                self.tab4_default_tab.setCurrentIndex(0)
            elif settings_dict["default_tab"] == "TLM":
                self.tabs.setCurrentIndex(1)
                self.tab4_default_tab.setCurrentIndex(1)
            elif settings_dict["default_tab"] == "S-Parameters":
                self.tabs.setCurrentIndex(2)
                self.tab4_default_tab.setCurrentIndex(2)
            elif settings_dict["default_tab"] == "Arrhenius":
                self.tabs.setCurrentIndex(3)
                self.tab4_default_tab.setCurrentIndex(3)
            elif settings_dict["default_tab"] == "Inverter Analysis":
                self.tabs.setCurrentIndex(4)
                self.tab4_default_tab.setCurrentIndex(4)

            self.default_L_correct_db = settings_dict["L_correction"]["database"]
            self.tab4_show_L_correct_db_path.setPlaceholderText(self.default_L_correct_db)
            self.tab4_show_L_correct_db_path.setToolTip(self.default_L_correct_db)
            self.tab3_automatic_Lcorrect.setChecked(settings_dict["L_correction"]["active"])
            self.tab4_automatic_Lcorrect.setChecked(settings_dict["L_correction"]["active"])
            try:
                # note: reading the database from excel takes > 30 sec, making the GUI less usable. reading it from .csv is incredibly much faster
                # therefore, the database needs to be exported as csv for real usage
                cols = ["fullName","W_nom","L_nom","W_real","L_real"]
                dtypes = {"fullName":"str","W_nom":"float","L_nom":"float","W_real":"float","L_real":"float"}
                self.L_correct = pd.read_csv(self.default_L_correct_db,usecols=cols,dtype=dtypes,encoding="latin")
                self.L_correct = self.L_correct.rename(columns={"fullName":"Sample"})
            except Exception as e:
                print(f'Corrected L database could not be read...please check.')
                print(e)

            self.tab1_analysis_smoothing_factor.setValue(settings_dict["smoothing_factors"]["tab1"])
            self.tab3_analysis_smoothing_factor.setValue(settings_dict["smoothing_factors"]["tab3"])
            self.tab6_analysis_smoothing_factor.setValue(settings_dict["smoothing_factors"]["tab6"])
            self.tab7_analysis_smoothing_factor.valueChanged.disconnect()
            self.tab7_analysis_smoothing_factor.setValue(settings_dict["smoothing_factors"]["tab7"])
            self.tab7_analysis_smoothing_factor.valueChanged.connect(self.analyze_inverter)

            self.tab1_choose_linestyle.setCurrentIndex(settings_dict["linestyles"]["tab1"])
            self.tab7_results_choose_linestyle.setCurrentIndex(settings_dict["linestyles"]["tab7"])

            self.tab5_fitsetup_fTbounds_min.setValue(settings_dict["tab5_fitsetup"]["fT_fit_min"])
            self.tab5_fitsetup_fTbounds_min_magnitude.setCurrentIndex(
                settings_dict["tab5_fitsetup"]["fT_fit_min_magnitude"])
            self.tab5_fitsetup_fTbounds_max.setValue(settings_dict["tab5_fitsetup"]["fT_fit_max"])
            self.tab5_fitsetup_fTbounds_max_magnitude.setCurrentIndex(
                settings_dict["tab5_fitsetup"]["fT_fit_max_magnitude"])
            self.tab5_fitsetup_chooseFit_checkbox.setChecked(settings_dict["tab5_fitsetup"]["fT_fit_bool"])

            self.tab5_estimate_fT_formula_choice.setCurrentIndex(settings_dict["tab5_estimate_settings"]["formula"])
            self.tab5_estimate_fT_RcW.setText(settings_dict["tab5_estimate_settings"]["RcW"])
            self.tab5_estimate_fT_mu0.setText(settings_dict["tab5_estimate_settings"]["mu0"])
            self.tab5_estimate_fT_Cdiel.setText(settings_dict["tab5_estimate_settings"]["C"])
            self.tab5_estimate_fT_Vov.setText(settings_dict["tab5_estimate_settings"]["Vov"])
            self.tab5_estimate_fT_L.setText(settings_dict["tab5_estimate_settings"]["L"])
            self.tab5_estimate_fT_Lov.setText(settings_dict["tab5_estimate_settings"]["Lov"])

            self.update_carrier_type_button_text()
            self.update_choose_regime_buttons_text()
            settings_timestamp = settings_dict["settings_timestamp"]

            # restore command line output
            sys.stdout = sys.__stdout__

            self.print_useroutput(f'Settings loaded successfully (settings last changed {settings_timestamp})',
                                  self.tab4_outputline)
            print(f"[{time.strftime('%H:%M:%S')}] Settings file loaded successfully.")

        except:
            print_exc()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle('Settings cannot be loaded!')
            msg.setText(
                "The file 'settings.ini' seems to be corrupted.")
            msg.setInformativeText(
                """Please make sure the 'settings.ini' file is structured according to the format it is saved in.""")
            msg.exec_()

        # for statement in settings_dict.values():
        #    exec(str(statement))

        return True


    ######################
    # CORE FUNCTIONALITY OF THIS PROGRAM - the following blocks of code define the analyses in the respective tabs
    ######################

    # tab1-method that contains all transfer curve analysis steps. it reads the parameters for fit setup and yields
    # them to the analysis defined in the analysis_script.py
    # results given by the script are read; summary graphs are plotted and numeric values are updated
    def analyze_transfer_data(self):
        t0 = time.time()  # at the end the total analysis runtime will be reported to the user

        # read filenames and give report to user if something's wrong with the choices
        l_ = self.tab1_analysis_choose_lin_data_combobox.currentText()
        s_ = self.tab1_analysis_choose_sat_data_combobox.currentText()
        if l_ == 'None' and s_ == 'None': self.print_useroutput(
            'Analysis button pressed with no chosen dataset. Thats not how fitting works ;-)',
            self.tab1_outputline); return False

        filenames_ = {
            'lin': self.tab1_file_paths_dictionary[l_] if not l_ == 'None' else self.print_useroutput(
                'Choose data for the linear fit, otherwise only the saturation regime can be analyzed.',
                self.tab1_outputline),
            'sat': self.tab1_file_paths_dictionary[s_] if not s_ == 'None' else self.print_useroutput(
                'Choose data for the saturation fit, otherwise only the linear regime can be analyzed.',
                self.tab1_outputline)
        }

        # extract the filename from the path
        if len(j := filenames_['lin'])>0: print(j[0]); n = j[0].split('_')[0]
        elif len(j := filenames_['sat'])>0: n = j[0].split('_')[0]

        # read fit settings from the values that either were detected automatically or given by the user
        try:
            W = float(self.tab1_channel_width.text())
            L = float(self.tab1_channel_length.text())
            VDS = float(self.tab1_linear_VDS_input.text())# if l_ != "None" else -np.inf
            carrier_type = self.tab1_carrier_type_button.text()
            factor = 1 if carrier_type == "p" else -1  # introduced to correctly display SSw sign. may be used for other things later on
        except:
            self.print_useroutput(
                'The given channel dimensions or the given V_DS are not of type FLOAT. Analysis aborted.',
                self.tab1_outputline)
            return False
        c_ = self.tab1_analysis_capacitance_input.value()
        sm_ = self.tab1_analysis_smoothing_factor.value()
        fd_ = self.tab1_analysis_first_derivative_threshold_input.value()
        sd_ = self.tab1_analysis_second_derivative_threshold_input.value()
        ft_ = self.datafile_preset

        mfr = self.get_manual_fit_regions()

        if self.tab1_results_choose_ssw_regime.isChecked():
            ss_region = 'sat'
        else:
            ss_region = 'lin'
        if self.tab1_results_choose_oor_regime.isChecked():
            oor_region = 'lin'
        else:
            oor_region = 'sat'
        oor_avg_window = int(self.tab4_set_tab1_oor_avg_window.text())
        if self.tab1_results_choose_vth_regime.isChecked():
            vth_region = 'sat'
        else:
            vth_region = 'lin'

        scale_input = self.tab1_plot_scale_menu.currentText()
        scale_dict = {'Linear (x&y)': ['linear', 'linear'], 'SemiLog (y)': ['linear', 'log'],
                      'LogLog (x&y)': ['log', 'log']}
        scale_ = scale_dict[scale_input]

        col_sett_ = {"names":self.tab4_set_custom_column_names.text(),
                           "skiprows":self.tab4_set_custom_skiprows.value()} if ft_=="Custom" else {"names":None,"skiprows":None}

        # check for automated L-correction (using measured channel lengths instead of nominal ones) - needs a excel database from the GUI
        if self.tab4_automatic_Lcorrect.isChecked() is not None:
            try:
                if n in self.L_correct.Sample.unique():
                    a_ = self.L_correct[(self.L_correct.Sample == n) & (self.L_correct.L_nom == L) & (self.L_correct.W_nom == W)]
                    W = a_.W_real
                    L = a_.L_real
                else:
                    print(f"Sample {n} not in list for corrected L values. Using nominal values instead.")
            except Exception as e:
                print(e)

        # initialize the object that contains all the data and the method to analyze them. they are NOT called within
        # the __init__() method, with exception for the determination of the threshold voltage (for overdrive data)
        t = TransistorAnalysis(W,
                               L,
                               c_,
                               filenames=filenames_,
                               filetype=ft_,
                               carrier_type=carrier_type,
                               fd=fd_,
                               sd=sd_,
                               smoothing=sm_,
                               V_DS=VDS,
                               manualFitRange=mfr,
                               ss_region=ss_region,
                               oor_region=oor_region,
                               oor_avg=oor_avg_window,
                               column_settings=col_sett_
                               )

        # if the value of fd/sd is changed, the analysis will be run from anew. this would be fatal and lead to an
        # infinite loop to prevent this, the button action has to be revoked, the value changed and afterwards
        # the button action can be restored
        self.tab1_analysis_first_derivative_threshold_input.valueChanged.disconnect()
        self.tab1_analysis_second_derivative_threshold_input.valueChanged.disconnect()
        self.tab1_purge_fit_error_tooltips()
        m,l = self.resolve_linestyle(self.tab1_choose_linestyle.currentText())

        # all of the code below is conditional. it runs only the analysis that is possible with the data given and
        # shows the corresponding values (e.g. Vth, if saturation is chosen there).
        try:
            # do all analysis that is possible with data provided for the saturation regime. contains determination
            # of mu (static and Vg-dependent) and Vth in saturation, on-off-ratio and subthreshold swing
            def linear_regression(x, a, b):
                return a * x + b

            sswlin_fwd, sswlin_back, sswlin_mean, sswsat_fwd, sswsat_back, sswsat_mean, \
            oorlin_fwd, oorlin_back, oorlin_mean, oorsat_fwd, oorsat_back, oorsat_mean, \
            vthlin_fwd, vthlin_back, vthlin_mean, vthsat_fwd, vthsat_back, vthsat_mean, \
            mulin_fwd, mulin_back, mulin_mean, musat_fwd, musat_back, musat_mean = [None] * 24

            if s_ != "None":
                self.tab1_saturation_fit_data_for_export = t.transfer_data_saturation
                fit_sat = t.fit_mobility_sat()
                if fit_sat is None: self.print_useroutput(
                    'The saturation regime fit exited with errors. Please try to loosen the 1st/2nd derivative constraints',
                    self.tab1_outputline); raise RuntimeError


                popts_sat, fitresultdata_sat, determination_sat, fitdata_sat, reliability_sat, errors_sat = fit_sat

                # the fitting error read out here is not a phyiscal uncertainty, it's the numerical fit error from the
                # line fit through the datapoints selected prior. only use as a "fit reliability" measure, not as error bar!
                musat_fwd, vthsat_fwd = popts_sat["fwd"]; musat_back, vthsat_back = popts_sat["back"];musat_mean, vthsat_mean = popts_sat["mean"]
                musat_fwd_err, vthsat_fwd_err = errors_sat["fwd"];musat_back_err, vthsat_back_err = errors_sat["back"];musat_mean_err, vthsat_mean_err = errors_sat["mean"]
                fd_sat, sd_sat, ysmoothsat = determination_sat
                xfitfwd_sat, xfitback_sat, yfitfwd_sat, yfitback_sat = fitdata_sat
                musat_reliability_fwd, musat_reliability_back, musat_reliability_mean = reliability_sat["fwd"], reliability_sat["back"], reliability_sat["mean"]

                oorsat_data = t.on_off_ratio()
                try:
                    oorsat_fwd, oorsat_back, oorsat_mean, oor_minmax_mean = oorsat_data
                except:
                    pass

                if self.tab1_resultshowfwd.isChecked():
                    self.tab1_result_musat_selected = musat_fwd
                    self.tab1_result_vthsat_selected = vthsat_fwd
                    self.tab1_result_musat_err_selected = musat_fwd_err
                    self.tab1_result_vthsat_err_selected = vthsat_fwd_err
                    self.tab1_result_oorsat_selected = oorsat_fwd
                    self.tab1_result_reliability_sat_selected = musat_reliability_fwd

                elif self.tab1_resultshowback.isChecked():
                    self.tab1_result_musat_selected = musat_back
                    self.tab1_result_vthsat_selected = vthsat_back
                    self.tab1_result_musat_err_selected = musat_back_err
                    self.tab1_result_vthsat_err_selected = vthsat_back_err
                    self.tab1_result_oorsat_selected = oorsat_back
                    self.tab1_result_reliability_sat_selected = musat_reliability_back

                elif self.tab1_resultshowmean.isChecked():
                    self.tab1_result_musat_selected = musat_mean
                    self.tab1_result_vthsat_selected = vthsat_mean
                    self.tab1_result_musat_err_selected = musat_mean_err
                    self.tab1_result_vthsat_err_selected = vthsat_mean_err
                    self.tab1_result_oorsat_selected = oorsat_mean
                    self.tab1_result_reliability_sat_selected = musat_reliability_mean

                self.tab1_result_musat.setText(f'{self.tab1_result_musat_selected:.2f}')
                self.tab1_result_musat.setToolTip(f'Fitting error: {self.tab1_result_musat_err_selected:.4f}')
                self.tab1_result_reliability.setText(f'---/{self.tab1_result_reliability_sat_selected:.2f}')
                if vth_region == 'sat':
                    self.tab1_result_vth.setText(f'{self.tab1_result_vthsat_selected:.2f}')
                    self.tab1_result_vth.setToolTip(f'Fitting error: {self.tab1_result_vthsat_err_selected:.4f}')

                if oor_region == 'sat': self.tab1_result_onoff.setText(f'{self.tab1_result_oorsat_selected:.2f}')

                self.tab1_plot_canvas_satfit.plot_data(t.saturation_Vg, np.sqrt(np.abs(t.saturation_Id)),
                                                       scale=['linear', 'linear'],
                                                       overwrite=True, label="data", xlabel=r"$V_{g,sat}$ (V)",
                                                       ylabel=r"$I_d^{0.5}$ (A$^{0.5}$)",
                                                       marker=m, linestyle=l)
                self.tab1_plot_canvas_satfit.plot_data(
                    fitresultdata_sat[0], np.sqrt(np.abs(fitresultdata_sat[1])), scale=['linear', 'linear'], overwrite=False,
                    label="fwd-fit")
                self.tab1_plot_canvas_satfit.plot_data(
                    fitresultdata_sat[0], np.sqrt(np.abs(fitresultdata_sat[2])), scale=['linear', 'linear'], overwrite=False,
                    label="back-fit")
                self.tab1_plot_canvas_satfit.plot_data(fitdata_sat[0], np.sqrt(np.abs(fitdata_sat[2])), scale=['linear', 'linear'], overwrite=False,
                    label="fwd-data",
                    marker='.', linestyle='')
                self.tab1_plot_canvas_satfit.plot_data(fitdata_sat[1], np.sqrt(np.abs(fitdata_sat[3])),
                                                       scale=['linear', 'linear'],
                                                       overwrite=False, label="back-data", marker='.', linestyle='',
                                                       lastplot=True)

                x1, x2, y1, y2 = t.mobility_sat_Vgdependent_plot()
                self.tab1_plot_canvas_muvgsat.plot_data(
                    x1, y1, scale=['linear', 'linear'], overwrite=True, label="fwd", xlabel=r"$V_{g,sat}$ (V)",
                    ylabel=r"$\mu_{eff}$")
                self.tab1_plot_canvas_muvgsat.plot_data(x2[1:], y2[1:], scale=['linear', 'linear'], overwrite=False,
                                                        label="back",
                                                        xlabel=r"$V_{g,sat}$ (V)", ylabel=r"$\mu_{eff}$")
                self.tab1_plot_canvas_muvgsat.plot_data(
                    x1, len(x1) * [float(self.tab1_result_musat.text())], scale=['linear', 'linear'],
                    overwrite=False,
                    linestyle='--',
                    color='k', alpha=0.5, lastplot=True)

                try:
                    if ss_region == 'sat':
                        a_ = t.subthreshold_swing()
                        popt_ssw_sat = a_[0]
                        fd_ssw_sat = a_[4]
                        xfitfwd_ssw, xfitback_ssw, yfitfwd_ssw, yfitback_ssw, x_plotlinefit = a_[1]
                        sswsat_fwd, sswsat_back, sswsat_mean = -1000 / popt_ssw_sat['fwd'][0], -1000 / popt_ssw_sat['back'][0], -1000 / \
                                                               popt_ssw_sat['mean'][0]

                        sswsat_err_fwd, sswsat_err_back, sswsat_err_mean = a_[3]

                        if self.tab1_resultshowfwd.isChecked():
                            self.tab1_result_sswsat_selected = sswsat_fwd
                            self.tab1_result_sswsat_err_selected = sswsat_err_fwd
                        elif self.tab1_resultshowback.isChecked():
                            self.tab1_result_sswsat_selected = sswsat_back
                            self.tab1_result_sswsat_err_selected = sswsat_err_back
                        elif self.tab1_resultshowmean.isChecked():
                            self.tab1_result_sswsat_selected = sswsat_mean
                            self.tab1_result_sswsat_err_selected = sswsat_err_mean

                        # np.abs is a workaround because I don't know right now how to extract the correct value but still plot it correctly in the plot
                        # since negative SSW does not make any sense, I leave this in for now. v1.4.2
                        self.tab1_result_ssw.setText(f'{factor * self.tab1_result_sswsat_selected:.2f}')
                        self.tab1_result_ssw.setToolTip(
                            f'Fitting error: {np.abs(self.tab1_result_sswsat_err_selected):.2f}')

                    if ss_region == 'lin':
                        x, y, xlabel_ = t.linear_Vg, t.linear_Id, r"$V_{g,lin}$"
                    else:
                        x, y, xlabel_ = t.saturation_Vg, t.saturation_Id, r"$V_{g,sat}$"

                    self.tab1_plot_canvas_ssw.plot_data(x, y, scale=['linear', 'log'],
                                                        overwrite=True, label="data", xlabel=xlabel_,
                                                        ylabel=r"$I_d$ (A)")
                    self.tab1_plot_canvas_ssw.plot_data(x_plotlinefit,
                                                        10 ** linear_regression(x_plotlinefit, *popt_ssw_sat['fwd']),
                                                        scale=['linear', 'log'], overwrite=False, label="fwd-fit")
                    self.tab1_plot_canvas_ssw.plot_data(x_plotlinefit,
                                                        10 ** linear_regression(x_plotlinefit, *popt_ssw_sat['back']),
                                                        scale=['linear', 'log'], overwrite=False, label="back-fit")
                    self.tab1_plot_canvas_ssw.plot_data(xfitfwd_ssw, yfitfwd_ssw, scale=['linear', 'log'],
                                                        overwrite=False, label="fwd-data", marker='.', linestyle='')
                    self.tab1_plot_canvas_ssw.plot_data(xfitback_ssw, yfitback_ssw, scale=['linear', 'log'],
                                                        overwrite=False, label="back-data", marker='.',
                                                        linestyle='',
                                                        lastplot=True)
                except:
                    self.print_useroutput(
                        "Subthreshold Swing fit unsuccessful. Try lowering the 1st derivative/raising 2nd derivative constraint.",
                        self.tab1_outputline)
                    self.tab1_plot_canvas_ssw.clear()
                    self.tab1_result_ssw.clear()

                self.tab1_analysis_first_derivative_threshold_input.setValue(fd_sat)
                self.tab1_analysis_second_derivative_threshold_input.setValue(sd_sat)

            # do all analysis that is possible with data provided for the linear regime. contains determination
            # of mu (static and Vg-dependent) and Vth in linear
            if l_ != "None":
                self.tab1_linear_fit_data_for_export = t.transfer_data_linear
                fit_lin = t.fit_mobility_lin()
                if fit_lin is None: self.print_useroutput(
                    'The linear regime fit exited with errors. Please try to loosen the 1st/2nd derivative constraints',
                    self.tab1_outputline); raise RuntimeError

                popts_lin, fitresultdata_lin, determination_lin, fitdata_lin, reliability_lin, errors_lin = fit_lin
                mulin_fwd, vthlin_fwd = popts_lin["fwd"]; mulin_back, vthlin_back = popts_lin["back"]; mulin_mean, vthlin_mean = popts_lin["mean"]
                mulin_fwd_err, vthlin_fwd_err = errors_lin["fwd"]; mulin_back_err, vthlin_back_err = errors_lin["back"]; mulin_mean_err, vthlin_mean_err = errors_lin["mean"]
                fd_lin, sd_lin, ysmooth = determination_lin
                xfitfwd_lin, xfitback_lin, yfitfwd_lin, yfitback_lin = fitdata_lin
                mulin_reliability_fwd, mulin_reliability_back, mulin_reliability_mean = reliability_lin["fwd"], reliability_lin["back"], reliability_lin["mean"]

                oor_lin_data = t.on_off_ratio()
                try:
                    oorlin_fwd, oorlin_back, oorlin_mean, oor_minmax_mean = oor_lin_data
                except:
                    pass

                if self.tab1_resultshowfwd.isChecked():
                    self.tab1_result_mulin_selected = mulin_fwd
                    self.tab1_result_vthlin_selected = vthlin_fwd
                    self.tab1_result_mulin_err_selected = mulin_fwd_err
                    self.tab1_result_vthlin_err_selected = vthlin_fwd_err
                    self.tab1_result_oorlin_selected = oorlin_fwd
                    self.tab1_result_reliability_lin_selected = mulin_reliability_fwd

                elif self.tab1_resultshowback.isChecked():
                    self.tab1_result_mulin_selected = mulin_back
                    self.tab1_result_vthlin_selected = vthlin_back
                    self.tab1_result_mulin_err_selected = mulin_back_err
                    self.tab1_result_vthlin_err_selected = vthlin_back_err
                    self.tab1_result_oorlin_selected = oorlin_back
                    self.tab1_result_reliability_lin_selected = mulin_reliability_back

                elif self.tab1_resultshowmean.isChecked():
                    self.tab1_result_mulin_selected = mulin_mean
                    self.tab1_result_vthlin_selected = vthlin_mean
                    self.tab1_result_mulin_err_selected = mulin_mean_err
                    self.tab1_result_vthlin_err_selected = vthlin_mean_err
                    self.tab1_result_oorlin_selected = oorlin_mean
                    self.tab1_result_reliability_lin_selected = mulin_reliability_mean

                self.tab1_result_mulin.setText(f'{self.tab1_result_mulin_selected:.2f}')
                self.tab1_result_mulin.setToolTip(f'Fitting error: {self.tab1_result_mulin_err_selected:.4f}')
                self.tab1_result_reliability.setText(f'{self.tab1_result_reliability_lin_selected:.2f}/---')
                if vth_region == 'lin':
                    self.tab1_result_vth.setText(f'{self.tab1_result_vthlin_selected:.2f}')
                    self.tab1_result_vth.setToolTip(f'Fitting error: {self.tab1_result_vthlin_err_selected:.4f}')

                if oor_region == 'lin' and oor_lin_data is not False: self.tab1_result_onoff.setText(
                    f'{self.tab1_result_oorlin_selected:.2f}')

                self.tab1_plot_canvas_linfit.plot_data(
                    t.linear_Vg, t.linear_Id, scale=['linear', 'linear'], overwrite=True, label="data",
                    xlabel=r"$V_{g,lin}$ (V)",
                    ylabel=r"$I_d$ (A)",marker=m, linestyle=l)
                self.tab1_plot_canvas_linfit.plot_data(
                    fitresultdata_lin[0], fitresultdata_lin[1], scale=['linear', 'linear'], overwrite=False, label="fwd-fit")
                self.tab1_plot_canvas_linfit.plot_data(
                    fitresultdata_lin[0], fitresultdata_lin[2], scale=['linear', 'linear'], overwrite=False, label="back-fit")
                # self.tab1_plot_canvas_dataset.plot_data(
                #    t.linear_Vg, fit_lin[7], scale=scale_, overwrite=False, label="smoothed",alpha=.35)
                self.tab1_plot_canvas_linfit.plot_data(
                    fitdata_lin[0], fitdata_lin[2], scale=['linear', 'linear'], overwrite=False, label="fwd-data",
                    marker='.',
                    linestyle=''
                )
                self.tab1_plot_canvas_linfit.plot_data(
                    fitdata_lin[1], fitdata_lin[3], scale=['linear', 'linear'], overwrite=False, label="back-data",
                    marker='.',
                    linestyle='',
                    lastplot=True
                )

                x1, x2, y1, y2 = t.mobility_lin_Vgdependent_plot()
                self.tab1_plot_canvas_muvglin.plot_data(
                    x1, y1, scale=['linear', 'linear'], overwrite=True, label="fwd", xlabel=r"$V_{g,lin}$ (V)",
                    ylabel=r"$\mu_{eff}$",marker=m, linestyle=l)
                self.tab1_plot_canvas_muvglin.plot_data(
                    x2[1:], y2[1:], scale=['linear', 'linear'], overwrite=False, label="back",
                    xlabel=r"$V_{g,lin}$ (V)",
                    ylabel=r"$\mu_{eff}$",marker=m, linestyle=l)
                self.tab1_plot_canvas_muvglin.plot_data(
                    x1, len(x1) * [self.tab1_result_mulin_selected], scale=['linear', 'linear'], overwrite=False,
                    linestyle='--',
                    color='k', alpha=0.5,
                    lastplot=True
                )

                try:
                    if ss_region == 'lin':
                        a_ = t.subthreshold_swing()

                        popt_ssw_lin = a_[0]
                        fd_ssw_lin = a_[4]
                        xfitfwd_ssw, xfitback_ssw, yfitfwd_ssw, yfitback_ssw, x_plotlinefit = a_[1]
                        sswlin_fwd, sswlin_back, sswlin_mean = -1000 / popt_ssw_lin['fwd'][0], -1000 / popt_ssw_lin['back'][0], -1000 / \
                                                               popt_ssw_lin['mean'][0]
                        sswlin_err_fwd, sswlin_err_back, sswlin_err_mean = a_[3]

                        if not self.tab1_results_choose_ssw_regime.isChecked():
                            if self.tab1_resultshowfwd.isChecked():
                                self.tab1_result_sswlin_selected = sswlin_fwd
                                self.tab1_result_sswlin_err_selected = sswlin_err_fwd
                            elif self.tab1_resultshowback.isChecked():
                                self.tab1_result_sswlin_selected = sswlin_back
                                self.tab1_result_sswlin_err_selected = sswlin_err_back
                            elif self.tab1_resultshowmean.isChecked():
                                self.tab1_result_sswlin_selected = sswlin_mean
                                self.tab1_result_sswlin_err_selected = sswlin_err_mean

                            # np.abs is a workaround because I don't know right now how to extract the correct value but still plot it correctly in the plot
                            # since negative SSW does not make any sense, I leave this in for now. v1.4.2
                            self.tab1_result_ssw.setText(f'{factor * self.tab1_result_sswlin_selected:.2f}')
                            self.tab1_result_ssw.setToolTip(
                                f'Fitting error: {np.abs(self.tab1_result_sswlin_err_selected):.2f}')

                        x, y = t.linear_Vg, t.linear_Id

                        self.tab1_plot_canvas_ssw.plot_data(x, y, scale=['linear', 'log'],
                                                            overwrite=True, label="data", xlabel=r"$V_{g,lin}$ (V)",
                                                            ylabel=r"$I_d$ (A)")
                        self.tab1_plot_canvas_ssw.plot_data(x_plotlinefit,
                                                            10 ** linear_regression(x_plotlinefit, *popt_ssw_lin['fwd']),
                                                            scale=['linear', 'log'], overwrite=False,
                                                            label="fwd-fit")
                        self.tab1_plot_canvas_ssw.plot_data(x_plotlinefit,
                                                            10 ** linear_regression(x_plotlinefit, *popt_ssw_lin['back']),
                                                            scale=['linear', 'log'], overwrite=False,
                                                            label="back-fit")
                        self.tab1_plot_canvas_ssw.plot_data(xfitfwd_ssw, yfitfwd_ssw, scale=['linear', 'log'],
                                                            overwrite=False, label="fwd-data", marker='.',
                                                            linestyle='')
                        self.tab1_plot_canvas_ssw.plot_data(xfitback_ssw, yfitback_ssw, scale=['linear', 'log'],
                                                            overwrite=False, label="back-data", marker='.',
                                                            linestyle='',
                                                            lastplot=True)
                except:
                    self.print_useroutput(
                        "Subthreshold Swing fit unsuccessful. Try lowering the 1st derivative constraint.",
                        self.tab1_outputline)
                    self.tab1_plot_canvas_ssw.clear()
                    self.tab1_result_ssw.clear()

                try:
                    self.tab1_analysis_first_derivative_threshold_input.setValue(min(fd_lin, fd_ssw_lin))
                except:
                    self.tab1_analysis_first_derivative_threshold_input.setValue(fd_lin)
                self.tab1_analysis_second_derivative_threshold_input.setValue(sd_lin)

            if l_ != "None" and s_ != "None":
                if self.tab1_resultshowfwd.isChecked():
                    self.tab1_result_reliability.setText(f'{mulin_reliability_fwd:.2f}/{musat_reliability_fwd:.2f}')
                elif self.tab1_resultshowback.isChecked():
                    self.tab1_result_reliability.setText(
                        f'{mulin_reliability_back:.2f}/{musat_reliability_back:.2f}')
                elif self.tab1_resultshowmean.isChecked():
                    self.tab1_result_reliability.setText(
                        f'{mulin_reliability_mean:.2f}/{musat_reliability_mean:.2f}')
                try:
                    if ('fd_ssw' in locals()) or ('fd_ssw' in globals()):
                        self.tab1_analysis_first_derivative_threshold_input.setValue(
                            min(fd_lin, fd_sat, fd_ssw_lin, fd_ssw_sat))
                except:
                    self.tab1_analysis_first_derivative_threshold_input.setValue(min(fd_lin, fd_sat))
                    self.tab1_analysis_second_derivative_threshold_input.setValue(max(sd_lin, sd_sat))

                    try:
                        self.tab1_analysis_first_derivative_threshold_input.setValue(min(fd_lin, fd_sat))
                        self.tab1_analysis_second_derivative_threshold_input.setValue(max(sd_lin, sd_sat))
                    except:
                        self.tab1_analysis_second_derivative_threshold_input.setValue(max(sd_lin, sd_sat))

            t2 = time.time()
            if "unsuccessful" not in self.tab1_outputline.text():
                self.print_useroutput(f"Analysis complete. Execution took {t2 - t0:.5f}s", self.tab1_outputline)
        except RuntimeError:
            pass
        except:
            print_exc()

        self.tab1_all_results = pd.DataFrame({
            "fwd": {
                "oor_lin": i if (i := oorlin_fwd) else None, "oor_sat": i if (i := oorsat_fwd) else None,
                "ssw_lin": i if (i := sswlin_fwd) else None, "ssw_sat": i if (i := sswsat_fwd) else None,
                "vth_lin": i if (i := vthlin_fwd) else None, "vth_sat": i if (i := vthsat_fwd) else None,
                "mu_lin": i if (i := mulin_fwd) else None, "mu_sat": i if (i := musat_fwd) else None
            },
            "back": {
                "oor_lin": i if (i := oorlin_back) else None, "oor_sat": i if (i := oorsat_back) else None,
                "ssw_lin": i if (i := sswlin_back) else None, "ssw_sat": i if (i := sswsat_back) else None,
                "vth_lin": i if (i := vthlin_back) else None, "vth_sat": i if (i := vthsat_back) else None,
                "mu_lin": i if (i := mulin_back) else None, "mu_sat": i if (i := musat_back) else None
            },
            "mean": {
                "oor_lin": i if (i := oorlin_mean) else None, "oor_sat": i if (i := oorsat_mean) else None,
                "ssw_lin": i if (i := sswlin_mean) else None, "ssw_sat": i if (i := sswsat_mean) else None,
                "vth_lin": i if (i := vthlin_mean) else None, "vth_sat": i if (i := vthsat_mean) else None,
                "mu_lin": i if (i := mulin_mean) else None, "mu_sat": i if (i := musat_mean) else None
            }
        })

        self.tab1_analysis_first_derivative_threshold_input.valueChanged.connect(self.analyze_transfer_data)
        self.tab1_analysis_second_derivative_threshold_input.valueChanged.connect(self.analyze_transfer_data)

        # don't show an empty plot when analysis is run (can happen if the user doesn't deliberately plot the dataset)
        if self.tab1_plot_canvas_dataset.empty and l_ != "None" and self.tab1_plotting_tabs.currentIndex() == 0: self.tab1_plotting_tabs.setCurrentIndex(
            1)
        if self.tab1_plot_canvas_dataset.empty and l_ == "None" and s_ != "None" and self.tab1_plotting_tabs.currentIndex() == 0: self.tab1_plotting_tabs.setCurrentIndex(
            2)

    # tab1-method that allows to export the analyzed transfer data
    def analyze_transfer_export_data(self):
        l_ = self.tab1_analysis_choose_lin_data_combobox.currentText()
        s_ = self.tab1_analysis_choose_sat_data_combobox.currentText()
        if l_ == 'None' and s_ == 'None': self.print_useroutput(
            'Export button pressed with no chosen dataset. No export executed.',
            self.tab1_outputline); return False
        filenames_ = {
            'lin': self.tab1_file_paths_dictionary[l_] if not l_ == 'None' else self.print_useroutput(
                'Choose data for the linear fit, otherwise only the saturation regime will be exported.',
                self.tab1_outputline),
            'sat': self.tab1_file_paths_dictionary[s_] if not s_ == 'None' else self.print_useroutput(
                'Choose data for the saturation fit, otherwise only the linear regime will be exported.',
                self.tab1_outputline)
        }

        # spoof data
        # filenames_ = {}
        # filenames_['lin'] = "C:/Users/wollandt_admin/Desktop/data/TW001/2020-01-20/TW1-Michal1_W100L30O30_transfer_lin2-1.txt"
        # filenames_['sat'] = "C:/Users/wollandt_admin/Desktop/data/TW001/2020-01-20/TW1-Michal1_W100L30O30_transfer_sat3-1.txt"

        lin_data = self.read_datafile(filepath=filenames_['lin'])
        sat_data = self.read_datafile(filepath=filenames_['sat'])

        # add important data to the data dataframe
        d = pd.DataFrame()
        if l_ != "None":
            # print(np.array(lin_data['lin_gate Voltage'].values))
            d['V_Glin'] = np.array([i for i in lin_data['lin_gate Voltage'].values]).flatten()
            d['I_Dlin'] = np.array([i for i in lin_data['lin_drain Current'].values]).flatten()
            d['I_Glin'] = np.array([i for i in lin_data['lin_gate Current'].values]).flatten()
        if s_ != "None":
            d['V_Gsat'] = np.array([i for i in sat_data['sat_gate Voltage'].values]).flatten()
            d['I_Dsat'] = np.array([i for i in sat_data['sat_drain Current'].values]).flatten()
            d['I_Gsat'] = np.array([i for i in sat_data['sat_gate Current'].values]).flatten()

        # add the results dataframe
        r = pd.DataFrame()
        r[f'on/off ({"lin" if self.tab1_results_choose_ssw_regime.isChecked() else "sat"})'] = pd.Series(
            float(i)) if len(i := self.tab1_result_onoff.text()) > 0 else pd.Series(np.nan)
        r['µ_lin'] = pd.Series(float(i)) if len(i := self.tab1_result_mulin.text()) > 0 else pd.Series(np.nan)
        r[f'SSw ({"sat" if self.tab1_results_choose_ssw_regime.isChecked() else "lin"})'] = pd.Series(float(i)) if len(
            i := self.tab1_result_ssw.text()) > 0 else pd.Series(np.nan)
        r['µ_sat'] = pd.Series(float(i)) if len(i := self.tab1_result_musat.text()) > 0 else pd.Series(np.nan)
        r[f'Vth ({"sat" if self.tab1_results_choose_ssw_regime.isChecked() else "lin"})'] = pd.Series(float(i)) if len(
            i := self.tab1_result_vth.text()) > 0 else pd.Series(np.nan)
        r['reliability (lin/sat)'] = pd.Series(i) if len(i := self.tab1_result_reliability.text()) > 0 else pd.Series(
            np.nan)

        r = self.tab1_all_results
        print(r)

        # determine the location to save the file and save it
        export_filename = i if len(i := self.tab1_export_filename.text()) > 0 else False
        if export_filename == False: self.print_useroutput("Please choose name for results file. Results not saved.",
                                                           self.tab1_outputline); return False
        directory_path = QFileDialog.getExistingDirectory(self, 'Select directory', self.default_directory_tab1)
        # if self.tab1_resultshowfwd.isChecked(): line_chosen_for_fit = "fwd"
        # elif self.tab1_resultshowback.isChecked(): line_chosen_for_fit = "back"
        # elif self.tab1_resultshowmean.isChecked(): line_chosen_for_fit = "mean"
        # else: line_chosen_for_fit = "unknown"
        with pd.ExcelWriter(directory_path + '/' + export_filename + '.xlsx', engine='xlsxwriter') as writer:
            r.to_excel(writer, sheet_name=f'Results')
            d.to_excel(writer, sheet_name='Data')

        self.print_useroutput("Results saved successfully.", self.tab1_outputline)
        print(f"[{time.strftime('%H:%M:%S')}] Transfer analysis results saved to {directory_path}")

        return True

    # tab3-method that takes the selected overdrive voltage from the combobox and updates the shown graph so that
    # it shows the linear fit for the width-normalized resistance for the chosen OV voltage
    def update_Rcfit(self):
        if self.tab3_singlerw_choose_ov.count() == 0: return False

        ov = i if (i := self.tab3_singlerw_choose_ov.currentText()) is not None else ''
        if ov == '': return False

        x_data, y_data = [], []
        for l in self.tab3_all_ov_RWs[ov]['data'].keys():
            for i in self.tab3_all_ov_RWs[ov]['data'][l]:
                x_data.append(1e-6 * l)
                y_data.append(i)
        x_data, y_data = np.array(x_data), np.array(y_data)

        popt = np.array(list(self.tab3_all_ov_RWs[ov]['popt']))
        r_sq = self.tab3_all_ov_RWs[ov]['r_sq']
        pcov = np.array(list(self.tab3_all_ov_RWs[ov]['pcov']))
        rc_error = np.sqrt(np.diag(pcov)[1])

        def linear_regression(x, a, b):
            return a * x + b

        # assumption for this block of code: l_1_2 will be bigger than l_0 (absolute values). if something can not be
        # seen because it is too negative, it can be adjusted here.
        # update v1.4.12.1: added a line of code in comment that allows for automatic resolution
        # looks weird if the data is not nice, so it is not mainline code for now
        # update v1.8.3.2: assumption: l_0 and l_1_2 should not be larger than largest L
        i_, j_ = self.tab3_result_l_1_2_value, self.tab4_tab3_result_limit_plot_xrange.isChecked()
        if self.tab4_set_TLM_xmin_automatic.isChecked():
            xmin_ = -1.5*min(i_,x_data.max()) if (i_ not in [None,False,np.nan] or j_) else - 1.5*x_data.max()
        else: xmin_ = - 1e-6
        x_fit = np.linspace(xmin_, x_data.max(), 10)
        y_fit = linear_regression(x_fit, *popt)

        overwrite_ = False if self.tab3_singlerw_showall_checkbox.isChecked() else True
        showlabel_ = r'''$V_o$={:.2f}V, $R^2$={:.3f}
    $R_CW$={:.1f}±{:.1f}$\Omega$cm'''.format(
            float(ov), r_sq, 1e2 * popt[1], 1e2 * rc_error) if self.tab3_singlerw_showlabel.isChecked() else ""

        self.tab3_plot_canvas_single_RW.plot_data(1e6 * x_data, 1e2 * y_data, scale=['linear', 'linear'],
                                                  overwrite=overwrite_, label=showlabel_,
                                                  xlabel="L [µm]", ylabel="RW [Ωcm]", marker="o", linestyle='',sci=False)
        self.tab3_plot_canvas_single_RW.plot_data(1e6 * x_fit, 1e2 * y_fit, scale=['linear', 'linear'],
                                                  overwrite=False,
                                                  lastplot=True, absolute=False,sci=False)

    # tab3-method that takes the selected channel length from the combobox and updates the shown graph so that
    # it shows the linear fit for the according transfer curve, including the points present in the respective fit
    def update_single_linFit(self):
        if self.tab3_single_linFit_choose_L.count() == 0: return False

        # reading the data file chosen in the dropdown menu and identify the instance (if there is more than one curve for that L)
        L_ = i if (i := self.tab3_single_linFit_choose_L.currentText()) is not None else ''
        if L_ == '': return False
        else:
            if '#' in L_:
                _ = L_.split('#')
                L,idx = float(_[0]),int(_[1])
            else:
                L,idx = float(L_), 0

        # read out the according data that was already saved during TLM (not run here again to save computational time)
        fitted_datapoints, fitline_data, xydata = self.tab3_tlm_singleL_linFit_plotData[L][idx]
        x_fitdata_fwd, x_fitdata_back, y_fitdata_fwd, y_fitdata_back = fitted_datapoints
        x_fitplot, y_fitplot_fwd, y_fitplot_back = fitline_data
        x_transfer, y_transfer = xydata

        # plotting the whole bunch
        self.tab3_plot_canvas_single_linear_fit.plot_data(x_transfer, y_transfer, scale=['linear', 'linear'],
                                overwrite=True, label=f"L={L} µm data",
                                xlabel=r"$V_{GS}$ [V]", ylabel=r"$I_D$ [A]", marker="", linestyle='-',sci=False)
        self.tab3_plot_canvas_single_linear_fit.plot_data(x_fitdata_fwd, y_fitdata_fwd, scale=['linear', 'linear'],
                                overwrite=False, label="fitpoints fwd", marker="o", linestyle='',sci=False)
        self.tab3_plot_canvas_single_linear_fit.plot_data(x_fitdata_back, y_fitdata_back, scale=['linear', 'linear'],
                                overwrite=False, label="fitpoints back", marker='o', linestyle='',sci=False, lastplot=False)
        self.tab3_plot_canvas_single_linear_fit.plot_data(x_fitplot, y_fitplot_fwd, scale=['linear', 'linear'],
                                overwrite=False, label="fit fwd", marker='', linestyle='-',sci=False, lastplot=False)
        self.tab3_plot_canvas_single_linear_fit.plot_data(x_fitplot, y_fitplot_back, scale=['linear', 'linear'],
                                overwrite=False, label="fit back", marker='', linestyle='-',sci=False, lastplot=True)


    # tab3-method that contains all analysis steps for TLM. it reads the parameters for fit setup and yields them to
    # the analysis defined in the analysis_skript.py
    # results given by the skript are read; summary graphs are plotted and numeric values are updated
    def analyze_TLM(self):
        t0 = time.time()
        if len(self.tab3_file_paths.keys()) < 2: self.print_useroutput(
            'Insufficient number of measurements selected for TLM analysis.', self.tab3_useroutput); return False
        try:
            ft_ = self.datafile_preset
            c = self.tab3_analysis_capacitance_input.value()
            sm_ = self.tab3_analysis_smoothing_factor.value()
            f = list(d) if len(d := self.tab3_file_paths.values()) > 0 else None
            VDS = float(i) if len(i := self.tab3_result_show_TLM_VDS.text()) > 0 else None
            carrier_type = self.tab3_carrier_type_button.text()
            ssw_factor = 1 if carrier_type == "p" else -1  # introduced to correctly display SSw sign. may be used for other things later on
            mfr = self.get_manual_fit_regions()
            tlm_dir = self.get_TLM_direction()
            col_sett_ = {"names": self.tab4_set_custom_column_names.text(),
                         "skiprows": self.tab4_set_custom_skiprows.value()} if ft_ == "Custom" else {"names": None,
                                                                                                     "skiprows": None}
            L_correction = self.L_correct if self.tab3_automatic_Lcorrect.isChecked() else None

            t = TLM_Analysis(c, filenames=f, filetype=ft_, carrier_type=carrier_type, smoothing=sm_, V_DS=VDS,
                             fd=self.tab3_analysis_first_derivative_threshold_input.value(),
                             sd=self.tab3_analysis_second_derivative_threshold_input.value(),
                             manualFitRange=mfr, fitRestriction=tlm_dir, column_settings=col_sett_,L_correct=L_correction)
            self.tab3_result_show_TLM_VDS.setText(f"{t.VDS:.3f}")
            saveplots = self.tab3_result_save_all_plots_checkbox.isChecked()

            # resetting values used as local variables even though they are global (so to have access from outside the method)
            self.tab3_tlm_data_for_export = {}
            fd_, sd_ = 1, 0
            self.tab3_tlm_singleL_linFit_plotData = {}
            self.tab3_single_linFit_choose_L.clear()

            for l in sorted(t.measurements.keys()):
                for t_ in t.measurements[l]:
                    try:
                        m = t_.fit_mobility_lin()
                        x_singleL,y_singleL = t_.linear_Vg, t_.linear_Id

                        # finding the smallest common derivative thresholds
                        f__, s__, ysmooth__ = m[2]
                        if f__ < fd_: fd_ = f__
                        if s__ > sd_: sd_ = s__

                        # collect data to show single linear fit for mu/vth
                        if not l in self.tab3_tlm_singleL_linFit_plotData.keys():
                            self.tab3_tlm_singleL_linFit_plotData[l] = [ (m[3],m[1],(x_singleL,y_singleL)) ]
                        else:
                            self.tab3_tlm_singleL_linFit_plotData[l].append( (m[3],m[1],(x_singleL,y_singleL)) )

                    except:
                        continue


                    # prepare data for export
                    if not l in self.tab3_tlm_data_for_export.keys():
                        self.tab3_tlm_data_for_export[l] = [t_.transfer_data_linear]
                    else:
                        self.tab3_tlm_data_for_export[l].append(t_.transfer_data_linear)

            self.tab3_analysis_first_derivative_threshold_input.setValue(fd_)
            self.tab3_analysis_second_derivative_threshold_input.setValue(sd_)
            for l_ in self.tab3_tlm_singleL_linFit_plotData.keys():
                if len(self.tab3_tlm_singleL_linFit_plotData[l_]) == 1:
                    self.tab3_single_linFit_choose_L.addItem(f'{l_}')
                else:
                    for i in range(len(self.tab3_tlm_singleL_linFit_plotData[l_])):
                        self.tab3_single_linFit_choose_L.addItem(f'{l_}#{i}')

            try:
                self.update_single_linFit()
            except:
                print_exc()

            o, r, err, bestfitdata, allRWs, l_0, Rc0W, mu0, mu0err, rs_sheet, rs_sheet_err, all_Vths, all_SSws = t.contactresistance()
            transferdata = t.get_transfer_curves()
            self.tab3_tlm_overdrivedata_for_export = pd.DataFrame(
                {"Vg-Vth [V]": o, "RcW [Ωm]": r, "RcW-err [Ωm]": err, "µ0 [cm²/Vs]": mu0})

            self.tab3_result_L0.setText(f'{-1e6 * l_0:.1f}')
            self.tab3_result_L0value = l_0
            self.tab3_result_Rc0W.setText(f'{1e2 * Rc0W:.1f}')
            hl = len(rs_sheet) // 2
            self.tab3_result_Rsheet.setText(f'{np.mean(rs_sheet[hl - 3:hl + 3]) / 1000:.1f}')

            # plotting all RcW values against overdrive voltage
            label_ = t.name if t.name else "data"
            self.tab3_plot_canvas_allRcW.plot_data(o, 1e2 * r, scale=['linear', 'log'], overwrite=True,
                                                   yerror=1e2 * err,
                                                   label=label_, xlabel="overdrive Vov [V]", ylabel="RcW [Ωcm]",
                                                   linestyle='', marker=".", lastplot=True)
            if saveplots: self.tab3_plot_canvas_allRcW.save(path=f"{self.default_directory_savefig}/plot_allRcW.png")

            ignore = 5
            self.tab3_plot_canvas_RcW_vs_overdrive.plot_data(1 / o[ignore:-ignore], 1e2 * r[ignore:-ignore],
                                                             scale=['linear', 'linear'], overwrite=True,
                                                             label="data", xlabel="1/overdrive Vov [1/V]",
                                                             ylabel="RcW [Ωcm]",
                                                             linestyle='', marker=".", lastplot=True)

            self.tab3_plot_canvas_mobility_vs_overdrive.plot_data(o, mu0, scale=['linear', 'linear'],
                                                                  overwrite=True,
                                                                  label="data", xlabel="overdrive Vov [V]",
                                                                  ylabel="µ0 [cm²/Vs]",
                                                                  ylim=np.abs(np.median(mu0)) * np.array(
                                                                      [0.5, 1.5]),
                                                                  linestyle='', marker=".",sci=False, lastplot=True)

            max_ov = (t.factor * o).argmax()
            r_finites, err_finites = r[np.isfinite(r)], err[np.isfinite(err)]
            r_avg = self.tab4_set_tab3_rcw_avg_window.value()
            self.tab3_result_RcW.setText(
                f'{1e2 * np.mean(r_finites[max_ov - r_avg:max_ov + r_avg]):.1f} ± {1e2 * np.mean(err_finites[max_ov - r_avg:max_ov + r_avg]):.1f}')  # give in Ohm*cm instead of SI units (Ohm*m)
            print(f"C-TLM: {self.tab3_result_RcW.text()}")

            if self.tab4_execute_mTLM.isChecked():
                o_m, r_m, err_m, bestfitdata_m, allRWpLs_m, mu0_m, mu0err_m, rs_sheet_m, rs_sheet_err_m = t.contactresistance_mTLM()
                max_ov_m = (t.factor * o_m).argmax()
                r_finites_m, err_finites_m = r_m[np.isfinite(r_m)], err_m[np.isfinite(err_m)]
                print(f'M-TLM: {1e2 * np.mean(r_finites_m[max_ov_m - r_avg:max_ov_m + r_avg]):.1f} ± {1e2 * np.mean(err_finites_m[max_ov_m - r_avg:max_ov_m + r_avg]):.1f}')

            # plot intrinsic mobility fit and show results in QLineEdits
            l12, muintr, lengths_, mobs_, err_l12, err_mu0 = t.intr_mob()
            self.tab3_result_l_1_2_value = l12  # is used in update_Rcfit()
            self.tab3_result_l_1_2.setText(f'{1e6 * l12:.1f} ± {1e6 * err_l12:.1f}')
            self.tab3_result_intr_mob.setText(f'{muintr:.2f} ± {err_mu0:.2f}')

            # for comparison calculate what RcW should be based on mu0 fitting, using sheet resistance from TLM
            rsh = np.mean(rs_sheet[hl - 3:hl + 3]) / 1000
            rsh_err = np.mean(rs_sheet_err[hl-3:hl+3]) / 1000
            rcwcomp = 1e6*l12 * rsh / 10 # factor because l12*rsh will be given in kQ*µm, but is useful in Q*cm

            # setting exact values as tooltips
            self.tab3_result_RcW.setToolTip(f"R<sub>C</sub>W = {1e2 * np.mean(r_finites[max_ov - r_avg:max_ov + r_avg]):.7f} ± {1e2 * np.mean(err_finites[max_ov - r_avg:max_ov + r_avg]):.7f} Ωcm")
            self.tab3_result_Rc0W.setToolTip(f"R<sub>C,0</sub>W = {1e2 * Rc0W:.7f} Ωcm")
            self.tab3_result_intr_mob.setToolTip(f"µ<sub>0</sub> = {muintr:.7f} ± {err_mu0:.7f} cm²/Vs")
            self.tab3_result_l_1_2.setToolTip(f'<p>L<sub>1/2</sub> = L<sub>T</sub> = {1e6 * l12:.7f} ± {1e6 * err_l12:.7f} µm <br/>By comparison of the mu0 fit with the sheet resistance of TLM:\nRcW = {rcwcomp:.1f} Ωcm\nCompare Sawada et al. 2020</p>')
            self.tab3_result_L0.setToolTip(f"L<sub>0</sub> = {-1e6 * l_0:.7f} µm")
            self.tab3_result_Rsheet.setToolTip(f"R<sub>sheet</sub> = {rsh:.4f} ± {rsh_err:.4f} kΩ/□")
            #self.tab3_result_l_1_2.setToolTip(f'By comparison of the mu0 fit with the sheet resistance of TLM:\nRcW = {rcwcomp:.1f} Ωcm\nCompare Sawada et al. 2020')

            # assign all data for future plots (RW vs L in dependence of overdrive voltage)
            self.tab3_all_ov_RWs = allRWs
            self.tab3_singlerw_choose_ov.clear()
            for o_ in allRWs.keys():
                self.tab3_singlerw_choose_ov.addItem(o_)
            self.tab3_singlerw_choose_ov.setCurrentIndex(
                self.tab3_singlerw_choose_ov.findText(str(bestfitdata['ov']), QtCore.Qt.MatchFixedString))
            self.update_Rcfit()
            if saveplots: self.tab3_plot_canvas_single_RW.save(path=f"{self.default_directory_savefig}/TLM_fit.png")

            ##############################################################
            # test out mTLM-plot
            if self.tab4_execute_mTLM.isChecked():
                d,p_,c_=allRWpLs_m[bestfitdata_m["ov"]]["data"],allRWpLs_m[bestfitdata_m["ov"]]["popt"],allRWpLs_m[bestfitdata_m["ov"]]["pcov"]
                x, y = [], []
                for key, value in d.items():
                    if isinstance(value, float): x.append(1 / key); y.append(value)
                    elif isinstance(value, list):
                        for item in value: x.append(1 / key); y.append(item)
                z_RcW=f"RcW = {1e2 * p_[1]:.1f} ± {1e2 * np.sqrt(np.diag(c_))[1]:.1f} $\Omega$cm"
                z_mu0=f"mu0 = {1e6 * c * abs(float(bestfitdata_m['ov'])) / p_[0]:.1f} ± ? cm$^2$/Vs" # for diag(c_)[0] gets larger for better fit somehow??
                label_ = f"Vov = {bestfitdata_m['ov']}\n{z_RcW}\n{z_mu0}"
                self.tab3_plot_canvas_mTLM_vs_InvChannelLength.plot_data(x,y,scale=['linear', 'linear'], overwrite=True,
                                                                         xlabel="1/L [1/µm]", ylabel="RW/L [Ohm*cm/µm]?",
                                                                         label=label_, linestyle='', marker='o', sci=False,
                                                                         lastplot=False, absolute=False)
                x_fit = np.linspace(- 1e-6, 1.25*max(x), 10)
                y_fit = p_[0]+p_[1]*1e6*x_fit
                self.tab3_plot_canvas_mTLM_vs_InvChannelLength.plot_data(x_fit, y_fit, scale=['linear', 'linear'],
                                                          overwrite=False,
                                                          lastplot=True, absolute=False, sci=False)
                if saveplots: self.tab3_plot_canvas_mTLM_vs_InvChannelLength.save(
                    path=f"{self.default_directory_savefig}/RWpL_vs_invL.png")
            #####################################################

            def intr_mu(L, l_1_2, mu0):  # equation taken from ulrikes thesis, page 60
                return mu0 / (1 + (l_1_2 / L))

            x_fit = np.linspace(lengths_.min(), lengths_.max(), 1000)
            y_fit = intr_mu(x_fit, l12, muintr)
            label_ = t.name if t.name else "data"
            self.tab3_plot_canvas_intr_mob.plot_data(1e6 * lengths_, mobs_, scale=['linear', 'linear'],
                                                     overwrite=True,sci=False,
                                                     label=label_, xlabel="L [µm]", ylabel="µ [cm²/Vs]", marker="o",
                                                     linestyle='')
            self.tab3_plot_canvas_intr_mob.plot_data(1e6 * x_fit, y_fit, scale=['linear', 'linear'],
                                                     overwrite=False,sci=False,
                                                     lastplot=True)
            if saveplots: self.tab3_plot_canvas_intr_mob.save(path=f"{self.default_directory_savefig}/mu0_fit.png")

            # plotting all transfer curves for a quick overlook

            if self.tab3_result_plot_all_transfercurves_checkbox.isChecked():
                self.tab3_plot_canvas_all_transfer_curves.clear()

                colors_blue = [(i / 2, i / 2, i, 1) for i in np.linspace(0.6, 1, len(list(transferdata.keys())))]
                colors_red = [(i, i / 2, i / 2, 1) for i in np.linspace(0.6, 1, len(list(transferdata.keys())))]

                # idx is used to determine the plot color, l is the channel length
                for idx, l in enumerate(sorted(transferdata.keys(), reverse=True)):
                    __ = 0
                    # for each channel length there exists a list with data taken there. easiest case would be 1 entry
                    # if more than one dataset exists, it will be plotted with the same color, but without label
                    for i in transferdata[l]:
                        label_ = f"L{l}µm" if __ == 0 else ""
                        self.tab3_plot_canvas_all_transfer_curves.plot_data(i['Vg'], i['Id'],
                                                                            scale=['linear', 'log'],
                                                                            overwrite=False,
                                                                            xlabel=r"$V_{GS}$ [V]",
                                                                            ylabel=r"$I_D$ [A]",
                                                                            label=label_,
                                                                            linestyle='-', marker='',
                                                                            color=colors_blue[idx],
                                                                            lastplot=False)

                        self.tab3_plot_canvas_all_transfer_curves.plot_data(i['Vg'], i['Ig'],
                                                                            scale=['linear', 'log'],
                                                                            overwrite=False,
                                                                            linestyle='-', marker='',
                                                                            color=colors_red[idx], lastplot=False)
                        __ += 1

                self.tab3_plot_canvas_all_transfer_curves.show()
                if saveplots: self.tab3_plot_canvas_all_transfer_curves.save(path=f"{self.default_directory_savefig}/transfercurves.png")

            # plotting the subthreshold swing in dependence of the channel lengths used in TLM
            label_ = t.name if t.name else "data"
            self.tab3_plot_canvas_ssw_vs_channellength.plot_data(all_SSws[0], ssw_factor * all_SSws[1],
                                                                 scale=['linear', 'linear'], overwrite=True,
                                                                 xlabel="L [µm]", ylabel="SSw [V]", label=label_,
                                                                 linestyle='', marker='o',sci=False,
                                                                 lastplot=True, absolute=False)
            if saveplots: self.tab3_plot_canvas_ssw_vs_channellength.save(
                path=f"{self.default_directory_savefig}/SSw_vs_L.png")

            # plotting the threshold voltage in dependence of the channel lengths used in TLM
            self.tab3_plot_canvas_vth_vs_channellength.plot_data(all_Vths[0], all_Vths[1],
                                                                 scale=['linear', 'linear'], overwrite=True,
                                                                 xlabel="L [µm]", ylabel="Vth [V]", label=label_,
                                                                 linestyle='', marker='o',sci=False,
                                                                 lastplot=True, absolute=False)
            if saveplots: self.tab3_plot_canvas_vth_vs_channellength.save(
                path=f"{self.default_directory_savefig}/Vth_vs_L.png")



            # saving some info available outside this analysis method (e.g. for copying to clipboard)
            self.TLM_all_Vths = all_Vths[1]
            self.TLM_all_channel_lengths = all_Vths[0]
            self.TLM_all_SSws = all_SSws[1]
            self.TLM_mobilities = mobs_
            self.TLM_RcW = 1e2 * np.mean(r_finites[max_ov - r_avg:max_ov + r_avg])
            self.TLM_RcWerr = 1e2 * np.mean(err_finites[max_ov - r_avg:max_ov + r_avg])
            self.TLM_mu0 = muintr
            self.TLM_mu0err = err_mu0
            self.TLM_Rsh = np.mean(rs_sheet[hl - 3:hl + 3]) / 1000 #kQ/sq

            self.print_useroutput(f"TLM analysis ended successfully. Runtime: {time.time() - t0:.4f}s",
                                  self.tab3_useroutput)
            print(f"[{time.strftime('%H:%M:%S')}] TLM analysis complete")
        except:
            print_exc()

    # tab3-method that allows to export the analyzed TLM data
    def TLM_analysis_export_data(self):

        results = {
            "RcW [Ωcm]": i if (i := self.tab3_result_RcW.text()) not in [None, ""] else "---",
            "Rc0W [Ωcm]": i if (i := self.tab3_result_Rc0W.text()) not in [None, ""] else "---",
            "µ0 [cm²/Vs]": i if (i := self.tab3_result_intr_mob.text()) not in [None, ""] else "---",
            "L12 [µm]": i if (i := self.tab3_result_l_1_2.text()) not in [None, ""] else "---",
            "-L0 [µm]": i if (i := self.tab3_result_L0.text()) not in [None, ""] else "---",
            "Rsh [kΩ/□]": i if (i := self.tab3_result_Rsheet.text()) not in [None, ""] else "---",
        }
        r = pd.DataFrame(results, index=[0])
        ov_d = self.tab3_tlm_overdrivedata_for_export

        d_dict = {}

        for filepath_ in self.tab3_file_paths.values():
            m = re.match('.*[_#]?W(?P<W>[\d.]+)[_#]*L(?P<L>[\d.]+).*', filepath_)
            l__ = float(m.group('L'))

            try:
                if l__ in d_dict.keys(): continue
                for i in self.tab3_tlm_data_for_export[l__]:
                    d = i[['lin_gate Voltage', 'lin_gate Current', 'lin_drain Current',
                           'overdrive_voltage', 'RW']]
                    d.columns = ["V_g [V]", "I_g [A]", "I_d [A]", "Vg-Vth [V]", "RW [Ωm]"]
                    if l__ not in d_dict.keys():
                        d_dict[l__] = [d]
                    else:
                        d_dict[l__].append(d)
            except:
                print_exc();continue

        export_filename = i if len(i := self.tab3_export_filename.text()) > 0 else False
        if export_filename == False: self.print_useroutput("Please choose name for results file. Results not saved.",
                                                           self.tab3_useroutput); return False
        directory_path = QFileDialog.getExistingDirectory(self, 'Select directory', self.default_directory_tab3)

        with pd.ExcelWriter(directory_path + '/' + export_filename + '.xlsx', engine='xlsxwriter') as writer:
            r.to_excel(writer, sheet_name=f'Results')
            ov_d.to_excel(writer, sheet_name=f'Overdrive Data')
            for l in sorted(d_dict.keys()):
                __ = 0
                for i in d_dict[l]:
                    appd_ = "" if __ == 0 else f"#{__}"
                    i.to_excel(writer, sheet_name=f'Data L={l}µm{appd_}')
                    __ += 1
        self.print_useroutput("Results saved successfully.", self.tab3_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] TLM results saved in {directory_path}")

        return True

    # tab3-method to copy info about the transfer curves used in TLM to clipboard
    def TLM_copy_to_clipboard(self):
        try:
            import csv
            L = self.TLM_all_channel_lengths
            mu = self.TLM_mobilities
            V = self.TLM_all_Vths
            SSw = self.TLM_all_SSws[~np.isnan(self.TLM_all_SSws)] # necessary because not all data sets have functioning SSw fit; since only min/max should be extracted, this extension makes sense
            RcW = self.TLM_RcW
            RcWerr = self.TLM_RcWerr
            mu0 = self.TLM_mu0
            mu0_err = self.TLM_mu0err
            Rsh = self.TLM_Rsh
            ls = os.linesep
            info = f"L = {min(L)} .. {max(L)} µm{ls}µ = {min(mu):.2f} .. {max(mu):.2f} cm²/Vs{ls}Vth = {min(V):.2f} .. {max(V):.2f} V{ls}SSw = {min(SSw):.1f} .. {max(SSw):.1f} mV/dec{ls}{ls}RcW = {RcW:.1f} ± {RcWerr:.1f} Ωcm{ls}µ0 = {mu0:.2f} ± {mu0_err:.2f} cm²/Vs{ls}Rsh = {Rsh:.1f} kΩ/□"

            # workaround, this seems to be the easiest way to copy something to clipboard
            info = pd.DataFrame([info])
            info.to_clipboard(index=False,header=False)
            self.print_useroutput("Copied info about transfer curves included in TLM to clipboard.", self.tab3_useroutput)
            return True
        except:
            self.print_useroutput("Nothing to copy - action aborted.", self.tab3_useroutput)
            print_exc()
            return False

    # tab5-method to start S-parameter analysis with the given datafile
    def analyze_sparam(self):
        t0 = time.time()

        if len(self.tab5_file_paths.keys()) == 0:
            self.print_useroutput("No data given for S-parameter analysis. Please select data file.",self.tab5_useroutput)
            print("No data given for S-parameter analysis. Please select data file.")
            return False
        else:
            file_ = self.tab5_filelist.currentItem().text()

        # read fitting setup
        fit_bool = self.tab5_fitsetup_chooseFit_checkbox.isChecked()
        min_ = self.tab5_fitsetup_fTbounds_min.value()
        min_mag_txt = self.tab5_fitsetup_fTbounds_min_magnitude.currentText()
        min_mag_ = 1 if min_mag_txt=="Hz" else 1e3 if min_mag_txt=="kHz" else 1e6 if min_mag_txt=="MHz" else None

        max_ = self.tab5_fitsetup_fTbounds_max.value()
        max_mag_txt = self.tab5_fitsetup_fTbounds_max_magnitude.currentText()
        max_mag_ = 1 if max_mag_txt=="Hz" else 1e3 if max_mag_txt=="kHz" else 1e6 if max_mag_txt=="MHz" else None

        bounds_ = [min_*min_mag_, max_*max_mag_]
        if bounds_[1] <= bounds_[0]:
            self.print_useroutput("Bounds given for the fit are not valid. Check: is f_max < f_min?",
                                  self.tab5_useroutput)
            print("Bounds given for the fT fit of the S parameters are not valid. Check: is f_max < f_min?")
            return False


        # execute analysis and plot results
        d = SparameterAnalysis(filename=self.tab5_file_paths[file_],#"C:/Users/wollandt_admin/MPI_Cloud/shared_data/Micha/2021-04_Sparameter_for_GUI/H7.xlsx",
                               fTbounds=bounds_, fTfit=fit_bool)
        #d = SparameterAnalysis(filename="C:/Users/wollandt_admin/MPI_Cloud/shared_data/Micha/2021-04_Sparameter_for_GUI/DataFile#9.s2p")
        f = d.data_raw["f"]
        S11 = 20*np.log10(d.data_raw["S11"])
        S12 = 20*np.log10(d.data_raw["S12"])
        S21 = 20*np.log10(d.data_raw["S21"])
        S22 = 20*np.log10(d.data_raw["S22"])
        h21 = 20*np.log10(d.data["h21"])

        # plot h21(f)
        self.tab5_plot_canvas_h21.plot_data(f, h21,
                                               scale=['log', 'linear'], overwrite=True,
                                               label="h21", xlabel=r"Frequency $f$ (Hz)",
                                               ylabel=r"$h_{21}$ (dB)", absolute=False,
                                               linestyle='-', marker=" ", lastplot=False)

        if fit_bool:
            fTresults = d.calculate_fT()

            self.tab5_plot_canvas_h21.plot_data(fTresults["xfitdata"], 20 * np.log10(fTresults["yfitdata"]),
                                            scale=['log', 'linear'], overwrite=False,
                                            label="Fit Data", xlabel=r"Frequency $f$ (Hz)",
                                            ylabel=r"$h_{21}$ (dB)", absolute=False,
                                            linestyle=' ', marker=".", lastplot=False)
            self.tab5_plot_canvas_h21.plot_data(fTresults["xdata"], fTresults["fitplot_ydata"],
                                            scale=['log', 'linear'], overwrite=False,
                                            label="Fit", xlabel=r"Frequency $f$ (Hz)",
                                            ylabel=r"$h_{21}$ (dB)", absolute=False,
                                            linestyle='-', marker=" ", lastplot=False)

            self.tab5_result_fT.setText(f"{fTresults['fT']:.2e}")
            self.tab5_result_fT.setToolTip(f"{fTresults['errors']['fT']:.2e}")
            self.tab5_result_decay_slope.setText(f"{fTresults['fitslope']:.2f}")
            self.tab5_result_decay_slope.setToolTip(f"{fTresults['errors']['slope']:.2f}")

        self.tab5_plot_canvas_h21.plot_data(f, [1]*len(f),
                                            scale=['log', 'linear'], overwrite=False,
                                            label="", xlabel=r"Frequency $f$ (Hz)",
                                            ylabel=r"$h_{21}$ (dB)", absolute=False, color="grey",
                                            linestyle='--', marker=" ", lastplot=True)

        # plot all of the S parameters into one plot
        self.tab5_plot_canvas_allSxx.plot_data(f, S11,
                                               scale=['log', 'linear'], overwrite=True,
                                               label="S11", xlabel=r"Frequency $f$ (Hz)",
                                               ylabel=r"$S_{xx}$ (dB)", absolute=False,
                                               linestyle='-', marker=" ", lastplot=False)
        self.tab5_plot_canvas_allSxx.plot_data(f, S12,
                                               scale=['log', 'linear'], overwrite=False,
                                               label="S12", xlabel=r"Frequency $f$ (Hz)",
                                               ylabel=r"$S_{xx}$ (dB)", absolute=False,
                                               linestyle='-', marker=" ", lastplot=False)
        self.tab5_plot_canvas_allSxx.plot_data(f, S21,
                                               scale=['log', 'linear'], overwrite=False,
                                               label="S21", xlabel=r"Frequency $f$ (Hz)",
                                               ylabel=r"$S_{xx}$ (dB)", absolute=False,
                                               linestyle='-', marker=" ", lastplot=False)
        self.tab5_plot_canvas_allSxx.plot_data(f, S22,
                                               scale=['log', 'linear'], overwrite=False,
                                               label="S22", xlabel=r"Frequency $f$ (Hz)",
                                               ylabel=r"$S_{xx}$ (dB)", absolute=False,
                                               linestyle='-', marker=" ", lastplot=True)


        self.print_useroutput(f"S-parameter analysis ended successfully. Runtime: {1000*(time.time() - t0):.1f}ms",
                              self.tab5_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] S-parameter analysis complete.")
        return True

    # tab5 method to estimate the transit frequency based on the TFT characteristics
    def estimate_fT(self):
        try:
            formula_type = self.tab5_estimate_fT_formula_choice.currentText()
            # read the given values and convert them to SI so that the calulation works later on
            RcW = float(self.tab5_estimate_fT_RcW.text()) * 1e-2
            mu0 = float(self.tab5_estimate_fT_mu0.text()) * 1e-4
            C = float(self.tab5_estimate_fT_Cdiel.text()) * 1e-2
            Vov = np.abs(float(self.tab5_estimate_fT_Vov.text()))
            L = float(self.tab5_estimate_fT_L.text())     * 1e-6
            Lov = float(self.tab5_estimate_fT_Lov.text()) * 1e-6
            if any([i < 0 for i in [RcW,mu0,C,L,Vov]]): raise ValueError

            if formula_type == "w/ RcW":
                fT = (mu0 * Vov) / (2 * np.pi * (L + (1 / 2) * mu0 * C * RcW * Vov) * (2 * Lov + (2 / 3) * L))
            elif formula_type == "w/o RcW":
                fT = (mu0 * Vov) / (2 * np.pi * (L * (2 * Lov + L)))
            else:
                fT = None

            self.tab5_estimate_fT_result.setText(f"{fT:.2e}")
            return True

        except:
            print("Transit frequency could not be estimated. Are there only (positive) numbers given?")
            self.print_useroutput("Transit frequency could not be estimated. Are there only (positive) numbers given?",self.tab5_useroutput)
            return False

    # tab6-method to start arrhenius analysis with the given datafiles
    def analyze_arrhenius(self):
        t0 = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] Arrhenius analysis started. Please wait...")

        try:
            ft_ = self.datafile_preset
            c_ = self.tab6_analysis_capacitance_input.value()
            sm_ = self.tab6_analysis_smoothing_factor.value()
            f = list(d) if len(d := self.tab6_file_paths.values()) > 0 else None
            carrier_type = self.tab3_carrier_type_button.text()
            direction_ = self.get_arrhenius_direction()
            col_sett_ = {"names": self.tab4_set_custom_column_names.text(),
                         "skiprows": self.tab4_set_custom_skiprows.value()} if ft_ == "Custom" else {"names": None,
                                                                                                     "skiprows": None}
            #mfr = self.get_manual_fit_regions()

            a = Arrhenius(c_ox=c_, filenames=f, filetype=ft_, carrier_type=carrier_type, smoothing=sm_,
                          fitRestriction=direction_,column_settings=col_sett_)

            arrhenius_dict, temps, rcws, mu0s,\
                    (xfit, yfit, (const, barrier), (const_err, barrier_err)) = a.analyze_temperatureDependent_TLM()



            self.tab6_plot_canvas_arrhenius_mu0.plot_data(1000/temps[0], mu0s[0], scale = ['linear','log'], overwrite = True,
                                                    yerror=mu0s[1],
                                                    label = "data", xlabel = r"Inv. Temperature 1000/$T$ (1000/K)",
                                                    ylabel = r"Intrinsic Mobility $\mu_0$ (cm²/Vs)",
                                                    linestyle = '', marker = ".", lastplot = False)
            self.tab6_plot_canvas_arrhenius_mu0.plot_data(1000 / xfit, yfit, scale=['linear', 'log'], overwrite=False,
                                                      label=f"Exp. Fit:\nE_a={barrier:.1f}+/-{barrier_err:.1f} meV",
                                                      xlabel=r"Inv. Temperature 1000/$T$ (1000/K)",
                                                      ylabel=r"Intrinsic Mobility $\mu_0$ (cm²/Vs)",
                                                      linestyle='-', marker="", lastplot=True)

            self.tab6_plot_canvas_arrhenius_rcw.plot_data(1000 / temps[0], rcws[0], scale=['linear', 'log'], overwrite=True,
                                                    yerror=rcws[1],
                                                    label="data", xlabel=r"Inv. Temperature 1000/$T$ (1000/K)",
                                                    ylabel=r"Contact Resistance $R_CW$ (Ωcm)",
                                                    linestyle = '', marker = ".", lastplot = True)


        except:
            print_exc()
            return False



        self.print_useroutput(f"Arrhenius analysis ended successfully. Runtime: {1000 * (time.time() - t0):.1f}ms",
            self.tab6_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Arrhenius analysis complete.")
        return True

    # tab7-method to start inverter analysis with the selected datafile
    def analyze_inverter(self):
        t0 = time.time()

        ft_ = self.datafile_preset
        sm_bool = self.tab7_analysis_smooth_bool.isChecked()

        #file_ = "C:/Users/wollandt_admin/MPI_Cloud/shared_data/Micha/2022-03_inverter_for_GUI/data/bad_coarse.txt" #self.tab7_file_paths[file_]

        if len(self.tab7_file_paths.keys()) == 0:
            self.print_useroutput("No data given for Inverter analysis. Please select data file.",self.tab7_useroutput)
            print("No data given for Inverter analysis. Please select data file.")
            return False
        else:
            file_ = self.tab7_file_paths[self.tab7_filelist.currentItem().text()]

        try:
            Vdd_ = float(self.tab7_analysis_supply_voltage.text())
        except:
            Vdd_ = None

        # execute analysis and plot results
        d = InverterAnalysis(filename=file_,
                             filetype=ft_,
                             smooth_factor=self.tab7_analysis_smoothing_factor.value() if sm_bool else None,
                             V_DD=Vdd_,
                                  )
        if Vdd_ is None:
            self.tab7_analysis_supply_voltage.setText(f"{d.supply_voltage:.2f}")

        data = d.get_characteristics()
        Vin  = np.concatenate((d.V_in_fwd,d.V_in_bwd))   if d.bwd_available else d.V_in_fwd
        #Vout = np.concatenate((d.V_out_fwd,d.V_out_bwd)) if d.bwd_available else d.V_out_fwd
        dV   = np.concatenate((d.dV_fwd,d.dV_bwd))       if d.bwd_available else d.dV_fwd
        gain_fwd, gain_bwd = data["max_gain"]["fwd"], data["max_gain"]["bwd"]
        self.tab7_result_gain_fwd.setText(f"{int(gain_fwd)}")
        if d.bwd_available: self.tab7_result_gain_bwd.setText(f"{int(gain_bwd)}")

        self.tab7_result_noiseMargin_fwd.setText(f"{data['nm_eff_fwd'][0]:.2f} V // {100*data['nm_eff_fwd'][1]:.1f} %")
        self.tab7_result_noiseMargin_fwd.setToolTip(f"{data['nm_eff_fwd'][0]:.6f} V // {100*data['nm_eff_fwd'][1]:.4f} %")
        self.tab7_result_noiseMargin_bwd.setText(f"{data['nm_eff_bwd'][0]:.2f} V // {100*data['nm_eff_bwd'][1]:.1f} %")
        self.tab7_result_noiseMargin_bwd.setToolTip(f"{data['nm_eff_bwd'][0]:.6f} V // {100*data['nm_eff_bwd'][1]:.4f} %")
        self.tab7_result_trip_fwd.setText(f"{data['trip_point']['fwd'][0]:.3f} V")
        self.tab7_result_trip_bwd.setText(f"{data['trip_point']['bwd'][0]:.3f} V")

        # preparing to plot the points used for unity gain in order to calculate noise margin, and the trip point
        ugp = data["unity_gain_points"]["fwd"]+data["unity_gain_points"]["bwd"]
        ugp_x = [i[0] for i in ugp]
        ugp_y = [i[1] for i in ugp]
        tp_x = [data["trip_point"]["fwd"][0],data["trip_point"]["bwd"][0]]
        tp_y = [data["trip_point"]["fwd"][1],data["trip_point"]["bwd"][1]]

        ls = self.tab7_results_choose_linestyle.currentText()
        m,l = self.resolve_linestyle(ls)

        self.tab7_plot_canvas_inverter_Vinout.plot_data(d.V_in, d.V_out_raw, scale=['linear', 'linear'], overwrite=True,
                                                        label="data", xlabel=r"V_in (V)",
                                                        ylabel=r"V_out (V)",
                                                        linestyle=l, marker=m, lastplot=False)

        self.tab7_plot_canvas_inverter_Vinout.plot_data(ugp_x, ugp_y, scale=['linear', 'linear'], overwrite=False,
                                                        label="unity gain",
                                                        linestyle='', marker="o", lastplot=False)

        self.tab7_plot_canvas_inverter_Vinout.plot_data(tp_x, tp_y, scale=['linear', 'linear'], overwrite=False,
                                                        label="trip point",
                                                        linestyle='', marker="o", lastplot=True)


        self.tab7_plot_canvas_inverter_deriv.plot_data(Vin, dV, scale=['linear', 'linear'], overwrite=True,
                                                        label="data", xlabel=r"V_in (V)",
                                                        ylabel=r"gain (dV_out / dV_in)",
                                                        linestyle='', marker=".", sci=False, lastplot=True)
                                                        #linestyle = '', marker = ".", lastplot = False if __ else True)
        #__ = self.tab7_results_show_gain_fits.isChecked()
        #if __:
        #    self.tab7_plot_canvas_inverter_deriv.plot_data(gain_dict["fwd"][0], gain_dict["fwd"][1],
        #                                               scale=['linear', 'linear'], overwrite=False,
        #                                               label="fit_fwd",
        #                                               linestyle='-', marker="", lastplot=False if d.bwd_available else True)
        #
        #    if d.bwd_available:
        #        self.tab7_plot_canvas_inverter_deriv.plot_data(gain_dict["bwd"][0], gain_dict["bwd"][1],
        #                                               scale=['linear', 'linear'], overwrite=False,
        #                                               label="fit_bwd",
        #                                               linestyle='-', marker="", lastplot=True)

        self.print_useroutput(f"Inverter analysis ended successfully. Runtime: {1000 * (time.time() - t0):.1f}ms",
                              self.tab7_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Inverter analysis complete.")
        return True

    ##############
    # changing some settings
    ##############

    def change_data_preset(self):
        self.datafile_preset = self.tab4_set_datapreset.currentItem().text()
        return True

    def change_analyze_transfer_default_directory(self):
        choose_default_path = i if os.path.exists((i := self.default_directory_tab1)) else os.getcwd()

        self.default_directory_tab1 = QFileDialog.getExistingDirectory(self,
                                                                       'Select directory to be opened by default for file selection',
                                                                       f"{choose_default_path}")
        self.tab4_show_tab1_default_directory.setText(self.default_directory_tab1)
        return True

    def change_TLM_default_directory(self):
        choose_default_path = i if os.path.exists((i := self.default_directory_tab3)) else os.getcwd()

        self.default_directory_tab3 = QFileDialog.getExistingDirectory(self,
                                                                       'Select directory to be opened by default for file selection',
                                                                       f"{choose_default_path}")
        self.tab4_show_tab3_default_directory.setText(self.default_directory_tab3)
        return True

    def change_sparam_default_directory(self):
        choose_default_path = i if os.path.exists((i := self.default_directory_tab5)) else os.getcwd()

        self.default_directory_tab5 = QFileDialog.getExistingDirectory(self,
                                                                       'Select directory to be opened by default for file selection',
                                                                       f"{choose_default_path}")
        self.tab4_show_tab5_default_directory.setText(self.default_directory_tab5)
        return True

    def change_arrhenius_default_directory(self):
        choose_default_path = i if os.path.exists((i := self.default_directory_tab6)) else os.getcwd()

        self.default_directory_tab6 = QFileDialog.getExistingDirectory(self,
                                                                       'Select directory to be opened by default for file selection',
                                                                       f"{choose_default_path}")
        self.tab4_show_tab6_default_directory.setText(self.default_directory_tab6)
        return True

    def change_inverter_default_directory(self):
        choose_default_path = i if os.path.exists((i := self.default_directory_tab7)) else os.getcwd()

        self.default_directory_tab7 = QFileDialog.getExistingDirectory(self,
                                                                       'Select directory to be opened by default for file selection',
                                                                       f"{choose_default_path}")
        self.tab4_show_tab7_default_directory.setText(self.default_directory_tab7)
        return True

    def change_savefig_default_directory(self):
        choose_default_path = i if os.path.exists((i := self.default_directory_savefig)) else os.getcwd()

        self.default_directory_savefig = QFileDialog.getExistingDirectory(self,
                                                                       'Select directory to be opened by default for file selection',
                                                                       f"{choose_default_path}")
        self.tab4_show_savefig_default_directory.setText(self.default_directory_savefig)
        return True

    # changing the path of the database for automated L-correction with real measured channel lengths
    def change_L_correct_db_path(self):
        choose_default_path = i if os.path.exists((i := self.default_L_correct_db)) else os.getcwd()
        file_suffix_string = "Excel Files (*.xlsx; *xls);;All Files (*)"
        self.default_L_correct_db = QFileDialog.getOpenFileName(self, 'Select Excel database for corrected channel lengths',
                                                                          f"{choose_default_path}",file_suffix_string)[0]
        self.tab4_show_L_correct_db_path.setPlaceholderText(str(self.default_L_correct_db))
        self.tab4_show_L_correct_db_path.setToolTip(str(self.default_L_correct_db))

    ####################
    # handling files and parameters stored in the individual tabs: adding or removing files, clearing results sections etc
    ####################

    # tab1-method for adding files to the filelist from which plot and fit data can be selected
    def choose_files(self, filelist=None):
        if filelist: files = filelist
        else:
            file_suffix_string = "Text Files (*.txt);;Data Files (*.dat);;All Files (*)" if self.datafile_preset in ["SweepMe!","ParameterAnalyzer","Goettingen","Surrey","Marburg","Custom"]\
                else "Data Files (*.dat);;Text Files (*.txt);;All Files (*)"

            files, _ = QFileDialog.getOpenFileNames(self, "Dialog",
                                                self.default_directory_tab1,
                                                file_suffix_string)

        # if there are files selected, update the background path dictionary and the frontend filelist
        # in case the files are denoted linear/saturation according to our standard naming pattern, add the choices
        # to the analysis combobox; automatically choose the first item in the respective list
        if files:
            for f in files:
                f_reduced = f.split('/')[-1]
                if f_reduced in self.tab1_file_paths_dictionary.keys(): continue
                self.tab1_file_paths_dictionary[f_reduced] = f
                self.tab1_file_list.addItem(f_reduced)

                if ("_lin" not in f_reduced) and ("tl." not in f_reduced) and ("_out" not in f_reduced):
                    self.tab1_analysis_choose_sat_data_combobox.addItem(f_reduced)
                    count_sat = int(self.tab1_analysis_choose_sat_data_combobox.count())
                    self.tab1_analysis_choose_sat_data_combobox.setItemData(count_sat - 1, f"{f_reduced}",
                                                                            QtCore.Qt.ToolTipRole)
                if ("_sat" not in f_reduced) and ("ts." not in f_reduced) and ("_out" not in f_reduced):
                    self.tab1_analysis_choose_lin_data_combobox.addItem(f_reduced)
                    count_lin = int(self.tab1_analysis_choose_lin_data_combobox.count())
                    self.tab1_analysis_choose_lin_data_combobox.setItemData(count_lin - 1, f"{f_reduced}",
                                                                            QtCore.Qt.ToolTipRole)

            self.tab1_file_list.setCurrentRow(0)
            if self.tab1_analysis_choose_lin_data_combobox.count() >= 2:
                self.tab1_analysis_choose_lin_data_combobox.setCurrentIndex(1)
            if self.tab1_analysis_choose_sat_data_combobox.count() >= 2:
                self.tab1_analysis_choose_sat_data_combobox.setCurrentIndex(1)

            print(f"[{time.strftime('%H:%M:%S')}] Data files for Transistor analysis loaded successfully.")

    # tab1-method to reset (almost?) everything to default
    # empty the file and path list, all selection boxes where files have been added as selection, and results from those
    def empty_file_list(self):
        self.tab1_file_list.clear()
        self.tab1_file_paths_dictionary = {}
        self.tab1_plot_file_choose_xdata_combobox.clear()
        self.tab1_plot_file_choose_xdata_combobox.addItem('None')
        self.tab1_plot_file_choose_ydata_combobox.clear()
        self.tab1_plot_file_choose_ydata_combobox.addItem('None')
        self.tab1_channel_width.clear()
        self.tab1_channel_length.clear()
        self.tab1_linear_VDS_input.clear()
        self.empty_analysis_results()
        self.tab1_plot_canvas_dataset.clear()

        # disconnection needed, otherwise the algorithm tried to search for a W, L and V_DS during the deletion
        self.tab1_analysis_choose_lin_data_combobox.currentIndexChanged.disconnect()
        self.tab1_analysis_choose_sat_data_combobox.currentIndexChanged.disconnect()
        self.tab1_analysis_choose_lin_data_combobox.clear()
        self.tab1_analysis_choose_lin_data_combobox.addItem('None')
        self.tab1_analysis_choose_sat_data_combobox.clear()
        self.tab1_analysis_choose_sat_data_combobox.addItem('None')
        self.tab1_analysis_choose_lin_data_combobox.currentIndexChanged.connect(
            self.determine_transistor_characteristics)
        self.tab1_analysis_choose_sat_data_combobox.currentIndexChanged.connect(
            self.determine_transistor_characteristics)

        self.print_useroutput("File list, analysis results and graphs emptied successfully.", self.tab1_outputline)
        print(f"[{time.strftime('%H:%M:%S')}] Transistor analysis file list, resulsts and graphs has been cleared.")

    # tab1-method for removing the selected file from the background and frontend lists
    def remove_transistoranalysis_item(self):
        f_ = self.tab1_file_list.currentItem().text()
        r_ = self.tab1_file_list.currentRow()
        if f_ is not None:
            del self.tab1_file_paths_dictionary[f_]
            self.tab1_file_list.takeItem(r_)
            print(f"[{time.strftime('%H:%M:%S')}] Dataset {f_} has been removed from the list")

            # also remove from the list for choosing fitting data
            try:
                l_idx = self.tab1_analysis_choose_lin_data_combobox.findText(
                    f_, QtCore.Qt.MatchFixedString)
                self.tab1_analysis_choose_lin_data_combobox.removeItem(l_idx)
                if l_idx > 0:
                    self.tab1_result_mulin.clear()
                    self.tab1_result_vth.clear()
                    self.tab1_plot_canvas_linfit.clear()
                    self.tab1_plot_canvas_muvglin.clear()

            except:
                pass
            try:
                s_idx = self.tab1_analysis_choose_sat_data_combobox.findText(
                    f_, QtCore.Qt.MatchFixedString)
                self.tab1_analysis_choose_sat_data_combobox.removeItem(s_idx)
                if s_idx > 0:
                    self.tab1_result_onoff.clear()
                    self.tab1_result_ssw.clear()
                    self.tab1_result_musat.clear()
                    self.tab1_plot_canvas_satfit.clear()
                    self.tab1_plot_canvas_ssw.clear()
                    self.tab1_plot_canvas_muvgsat.clear()
            except:
                pass

    # tab1-method to reset all analysis results, both graphs and numeric values
    def empty_analysis_results(self):
        self.tab1_result_onoff.clear()
        self.tab1_result_ssw.clear()
        self.tab1_result_mulin.clear()
        self.tab1_result_musat.clear()
        self.tab1_result_vth.clear()
        self.tab1_result_reliability.clear()

        self.tab1_plot_canvas_linfit.clear()
        self.tab1_plot_canvas_satfit.clear()
        self.tab1_plot_canvas_ssw.clear()
        self.tab1_plot_canvas_muvglin.clear()
        self.tab1_plot_canvas_muvgsat.clear()

        # if the value of fd/sd is changed, the analysis will be run from anew. to prevent this, the button action
        # has to be revoked, the value changed and afterwards the button action can be restored
        self.tab1_analysis_first_derivative_threshold_input.valueChanged.disconnect()
        self.tab1_analysis_second_derivative_threshold_input.valueChanged.disconnect()
        self.tab1_analysis_first_derivative_threshold_input.setValue(0)
        self.tab1_analysis_second_derivative_threshold_input.setValue(0)
        self.tab1_analysis_first_derivative_threshold_input.valueChanged.connect(self.analyze_transfer_data)
        self.tab1_analysis_second_derivative_threshold_input.valueChanged.connect(self.analyze_transfer_data)
        print(f"[{time.strftime('%H:%M:%S')}] Transfer analysis results cache cleared.")

    # tab3-method for adding files to the list for TLM analysis
    def choose_filesTLM(self,filelist=None):
        if filelist: files = filelist
        else:
            file_suffix_string = "Text Files (*.txt);;Data Files (*.dat);;All Files (*)" if self.datafile_preset in ["SweepMe!","ParameterAnalyzer","Goettingen","Marburg","Surrey","Custom"]\
                else "Data Files (*.dat);;Text Files (*.txt);;All Files (*)"
            files, _ = QFileDialog.getOpenFileNames(self, "Dialog",
                                                self.default_directory_tab3,
                                                file_suffix_string)
        if files:
            for f in files:
                f_reduced = f.split('/')[-1]
                if f_reduced in self.tab3_file_paths.keys(): continue
                self.tab3_file_paths[f_reduced] = f
                self.tab3_filelist.addItem(f_reduced)

            self.tab3_filelist.setCurrentRow(0)

        self.print_useroutput("Data files for TLM analysis loaded successfully.",self.tab3_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Data files for TLM analysis loaded successfully.")
        return True

    # tab3-method to reset (almost?) everything to default
    # empty the file and path list and results from the TLM analysis
    def empty_TLM_file_list(self):
        self.tab3_filelist.clear()
        self.tab3_file_paths = {}
        self.empty_TLM_results()
        self.tab3_analysis_first_derivative_threshold_input.setValue(0)
        self.tab3_analysis_second_derivative_threshold_input.setValue(0)
        print(f"[{time.strftime('%H:%M:%S')}] TLM file list has been cleared.")

    # tab3-method for removing the selected file from the background and frontend lists
    def remove_TLM_file(self):
        f_ = self.tab3_filelist.currentItem().text()
        del self.tab3_file_paths[f_]
        self.tab3_filelist.takeItem(self.tab3_filelist.currentRow())
        print(f"[{time.strftime('%H:%M:%S')}] Dataset {f_} has been removed from the TLM list.")

    # tab3-method to reset all analysis results, both graphs and numeric values
    def empty_TLM_results(self):
        self.tab3_result_show_TLM_VDS.clear()
        self.tab3_result_RcW.clear()
        self.tab3_result_intr_mob.clear()
        self.tab3_result_l_1_2.clear()
        self.tab3_result_l_1_2.setToolTip("")
        self.tab3_result_Rc0W.clear()
        self.tab3_result_L0.clear()
        self.tab3_result_Rsheet.clear()

        self.tab3_plot_canvas_allRcW.clear()
        self.tab3_plot_canvas_single_RW.clear()
        self.tab3_plot_canvas_intr_mob.clear()
        self.tab3_plot_canvas_mTLM_vs_InvChannelLength.clear()
        self.tab3_plot_canvas_RcW_vs_overdrive.clear()
        self.tab3_plot_canvas_mobility_vs_overdrive.clear()
        self.tab3_plot_canvas_all_transfer_curves.clear()
        self.tab3_plot_canvas_single_linear_fit.clear()
        self.tab3_plot_canvas_vth_vs_channellength.clear()
        self.tab3_plot_canvas_ssw_vs_channellength.clear()

        self.tab3_analysis_first_derivative_threshold_input.setValue(0)
        self.tab3_analysis_second_derivative_threshold_input.setValue(0)

        self.tab3_tlm_singleL_linFit_plotData = {}
        self.tab3_single_linFit_choose_L.clear()

        self.tab3_result_RcW.setToolTip(None)
        self.tab3_result_Rc0W.setToolTip(None)
        self.tab3_result_intr_mob.setToolTip(None)
        self.tab3_result_l_1_2.setToolTip(None)
        self.tab3_result_L0.setToolTip(None)
        self.tab3_result_Rsheet.setToolTip(None)

        self.print_useroutput("Results cache cleared.", self.tab3_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] TLM result cache cleared.")

    # tab5-method for adding files to the list for S-parameter analysis
    def choose_filesSparam(self, filelist=None):
        if filelist:
            files = filelist
        else:
            file_suffix_string = "VNA Files (*.s2p);;Excel Files (*.xlsx);;All Files (*)"
            files, _ = QFileDialog.getOpenFileNames(self, "Dialog",
                                                    self.default_directory_tab5,
                                                    file_suffix_string)
        if files:
            for f in files:
                f_reduced = f.split('/')[-1]
                if f_reduced in self.tab5_file_paths.keys(): continue
                self.tab5_file_paths[f_reduced] = f
                self.tab5_filelist.addItem(f_reduced)

            self.tab5_filelist.setCurrentRow(0)

        self.print_useroutput("Data files for S-parameter analysis loaded successfully.", self.tab5_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Data files for S-parameter analysis loaded successfully.")
        return True

    # tab5-method to reset (almost?) everything to default, empty the file and path list and results from the TLM analysis
    def empty_sparam_file_list(self):
        self.tab5_filelist.clear()
        self.tab5_file_paths = {}
        self.empty_sparam_results()
        print(f"[{time.strftime('%H:%M:%S')}] S-parameter file list has been cleared.")

    # tab5-method for removing the selected file from the background and frontend lists
    def remove_sparam_file(self):
        f_ = self.tab5_filelist.currentItem().text()
        del self.tab5_file_paths[f_]
        self.tab5_filelist.takeItem(self.tab5_filelist.currentRow())
        print(f"[{time.strftime('%H:%M:%S')}] Dataset {f_} has been removed from the S-paramter list.")

    # tab5-method to reset all analysis results, both graphs and numeric values
    def empty_sparam_results(self):

        self.tab5_plot_canvas_h21.clear()
        self.tab5_plot_canvas_allSxx.clear()

        self.tab5_result_fT.clear()
        self.tab5_result_decay_slope.clear()

        self.print_useroutput("Results cache cleared.", self.tab5_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] S-parameter result cache cleared.")
        return True

    # tab6-method for adding files to the list for S-parameter analysis
    def choose_filesArrhenius(self, filelist=None):
        if filelist:
            files = filelist
        else:
            file_suffix_string = "Text Files (*.txt);;Data Files (*.dat);;All Files (*)"
            files, _ = QFileDialog.getOpenFileNames(self, "Dialog",
                                                    self.default_directory_tab6,
                                                    file_suffix_string)
        if files:
            for f in files:
                f_reduced = f.split('/')[-1]
                if f_reduced in self.tab6_file_paths.keys(): continue
                self.tab6_file_paths[f_reduced] = f
                self.tab6_filelist.addItem(f_reduced)

            self.tab6_filelist.setCurrentRow(0)

        self.print_useroutput("Data files for Arrhenius analysis loaded successfully.", self.tab6_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Data files for Arrhenius analysis loaded successfully.")
        return True

    # tab6-method to reset (almost?) everything to default, empty the file and path list and results from the TLM analysis
    def empty_arrhenius_file_list(self):
        self.tab6_filelist.clear()
        self.tab6_file_paths = {}
        self.empty_arrhenius_results()
        print(f"[{time.strftime('%H:%M:%S')}] Arrhenius file list has been cleared.")

    # tab6-method for removing the selected file from the background and frontend lists
    def remove_arrhenius_file(self):
        f_ = self.tab6_filelist.currentItem().text()
        del self.tab6_file_paths[f_]
        self.tab6_filelist.takeItem(self.tab6_filelist.currentRow())
        print(f"[{time.strftime('%H:%M:%S')}] Dataset {f_} has been removed from the Arrhenius list.")

    # tab6-method to reset all analysis results, both graphs and numeric values
    def empty_arrhenius_results(self):

        self.tab6_plot_canvas_arrhenius_mu0.clear()
        self.tab6_plot_canvas_arrhenius_rcw.clear()

        self.print_useroutput("Results cache cleared.", self.tab6_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Arrhenius result cache cleared.")
        return True

    def choose_filesInverter(self, filelist=None):
        if filelist:
            files = filelist
        else:
            file_suffix_string = "Text Files (*.txt);;Data Files (*.dat);;All Files (*)"
            files, _ = QFileDialog.getOpenFileNames(self, "Dialog",
                                                    self.default_directory_tab7,
                                                    file_suffix_string)
        if files:
            for f in files:
                f_reduced = f.split('/')[-1]
                if f_reduced in self.tab7_file_paths.keys(): continue
                self.tab7_file_paths[f_reduced] = f
                self.tab7_filelist.addItem(f_reduced)

            self.tab7_filelist.setCurrentRow(0)

        self.print_useroutput("Data files for Inverter analysis loaded successfully.", self.tab7_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Data files for Inverter analysis loaded successfully.")
        return True

        # tab7-method to reset (almost?) everything to default, empty the file and path list and results from the this tab

    def empty_inverter_file_list(self):
        self.tab7_filelist.clear()
        self.tab7_file_paths = {}
        self.empty_inverter_results()
        print(f"[{time.strftime('%H:%M:%S')}] Inverter file list has been cleared.")

        # tab7-method for removing the selected file from the background and frontend lists

    def remove_inverter_file(self):
        f_ = self.tab7_filelist.currentItem().text()
        del self.tab7_file_paths[f_]
        self.tab7_filelist.takeItem(self.tab7_filelist.currentRow())
        print(f"[{time.strftime('%H:%M:%S')}] Dataset {f_} has been removed from the Inverter list.")

        # tab7-method to reset all analysis results, both graphs and numeric values

    def empty_inverter_results(self):

        self.tab7_plot_canvas_inverter_Vinout.clear()
        self.tab7_plot_canvas_inverter_deriv.clear()

        self.tab7_analysis_supply_voltage.clear()
        self.tab7_result_trip_fwd.clear()
        self.tab7_result_trip_bwd.clear()
        self.tab7_result_gain_fwd.clear()
        self.tab7_result_gain_bwd.clear()
        self.tab7_result_noiseMargin_fwd.clear()
        self.tab7_result_noiseMargin_bwd.clear()

        self.print_useroutput("Results cache cleared.", self.tab7_useroutput)
        print(f"[{time.strftime('%H:%M:%S')}] Inverter result cache cleared.")
        return True

    #######################
    # some functions needed for plotting random data files
    #######################

    # the filename ususally contains the channel width and length, and in the linear regime V_DS
    # this function tries to extract them and set the values in the GUI accordingly
    def determine_transistor_characteristics(self):
        l_ = self.tab1_analysis_choose_lin_data_combobox.currentText()
        s_ = self.tab1_analysis_choose_sat_data_combobox.currentText()
        # determination of channel width and length
        try:
            m_lin = re.match('.*[_#]?W(?P<W>[\d.]+)[_#]*?L(?P<L>[\d.]+).*', l_)
            length_lin = float(m_lin.group('L'))
            width_lin = float(m_lin.group('W'))
        except:
            length_lin = None;
            width_lin = None
        try:
            m_sat = re.match('.*[_#]?W(?P<W>[\d.]+)[_#]*?L(?P<L>[\d.]+).*', s_)
            length_sat = float(m_sat.group('L'))
            width_sat = float(m_sat.group('W'))
        except:
            length_sat = None;
            width_sat = None

        # determination of V_DS for the linear
        VDS = None
        if l_ != "None":
            try:  # assume labview
                m_vds = re.match('.*Vds(?P<VDS>[+\-\d.]+).*', l_)
                VDS = float(m_vds.group('VDS'))  # if m_vds is not None else None
            except:
                try:  # assume sweepme
                    d = pd.read_table(self.tab1_file_paths_dictionary[l_],
                                      header=[0, 1])
                    d.columns.droplevel(1)
                    VDS = float(d.filter(regex='drain.*Voltage').mean().iloc[0])
                except:
                    try:  # assume goettingen SuperFunAnalyzer v2
                        d = pd.read_table(self.tab1_file_paths_dictionary[l_],
                                          skiprows=2, header=1)
                        VDS = float(d['V_DS'].mean())
                    except:
                        try:
                            d = pd.read_table(self.tab1_file_paths_dictionary[l_],
                                              skiprows=2, header=1)
                            VDS = float(d['V_Drain'].mean())
                        except:
                            try: # assume Marburg
                                d = pd.read_table(self.tab1_file_paths_dictionary[l_],
                                                  header=[0, 1])
                                d.columns.droplevel(1)
                                try:VDS = float(d.filter(regex='drain.*Voltage').mean().iloc[0])
                                except:VDS = float(d.filter(regex='[dD]rain.*[vV]oltage').mean().iloc[0])
                            except:

                                try: # assume Surrey
                                    d = pd.read_table(self.tab1_file_paths_dictionary[l_],
                                                  skiprows=None, header=0, sep=',')
                                    VDS = float(d['Drain Voltage(1)'].mean())
                                except:
                                    pass

            if VDS is not None: self.tab1_linear_VDS_input.setText(f"{VDS:.2f}")

        # check whether the data is consistent between lin and sat
        # if there is inconsistency, the user is notified
        if all([i == "None" for i in [l_, s_]]):
            return True

        if all([i is None for i in [length_lin, length_sat, width_lin, width_sat]]):
            self.print_useroutput(
                "Channel width and length could not be determined automatically. Please enter values manually. Analysis aborted.",
                self.tab1_outputline)

        elif ((length_lin != length_sat) or (width_lin != width_sat)) and all([i not in ["None", None] for i in [l_,
                                                                                                                 s_]]):  # and all([i != None for i in [length_lin,length_sat,width_lin,width_sat]]):
            self.print_useroutput(
                "Channel width or length of selected linear and saturation data are not equal. Please enter values manually. Analysis aborted.",
                self.tab1_outputline)

        else:
            self.tab1_channel_width.setText(f"{width_lin if width_lin is not None else width_sat}")
            self.tab1_channel_length.setText(f"{length_lin if length_lin is not None else length_sat}")
            self.print_useroutput(
                "Channel width and length were successfully updated (automatically). Please still check if they are correct.",
                self.tab1_outputline)
            if VDS is None: self.print_useroutput(
                "Drain-Source Voltage could not be determined automatically. Please enter value manually. Analysis aborted",
                self.tab1_outputline)

    # tab1-method for reading the column names in a certain file. this is used to be able to read and show data from
    # an arbitrary file, not only sweepme. this is not yet fully working! for now it only recognizes sweepme and labview
    # the columns are added to the combobox from which the x and y data for plotting can be chosen
    # if the datafile is a transfer curve with lin or sat voltage/current, the x and y data are preset automatically
    def read_columnnames(self):
        if self.tab1_file_list.currentItem() is None: return False
        path = self.tab1_file_paths_dictionary[i] if (i := self.tab1_file_list.currentItem().text()) not in [None, '',
                                                                                                             'None'] else ''

        # output data is not the target here, so if the user chooses output files nothing should be done
        if "_out" in path: return False

        if self.datafile_preset == "SweepMe!":
            # print("SweepMe! preset selected. Attempt to read data...")
            try:
                d = pd.read_table(path, nrows=5, header=[0, 1])
                c = d.columns.droplevel(1)
            except:
                print("SweepMe! preset was selected, but file does not follow preset. Please check file format")

        if self.datafile_preset == "Custom":
            # print("Custom preset selected. Attempt to read data...")
            try:
                n = self.tab4_set_custom_column_names.text().split(';')
                s = self.tab4_set_custom_skiprows.value()
                d = pd.read_table(path, nrows=5, header=1, names=n, skiprows=s)
                c = d.columns
            except:
                print("Custom preset was selected, but columns could not be read. Please check file format or code?")

        if self.datafile_preset == "Goettingen":
            # print("Goettingen preset selected. Attempt to read data...")
            try:
                d = pd.read_table(path, skiprows=2, nrows=5, header=1)
                c = d.columns
            except:
                print("Goettingen preset was selected, but file does not follow preset. Please check file format")

        if self.datafile_preset == "Marburg":
            # print("Marburg preset selected. Attempt to read data...")
            try:
                d = pd.read_table(path, nrows=5, header=[0, 1])
                c = d.columns.droplevel(1)
            except:
                print("Marburg preset was selected, but file does not follow preset. Please check file format")

        if self.datafile_preset == "Surrey":
            # print("Surrey preset selected. Attempt to read data...")
            try:
                d = pd.read_table(path, skiprows=None, nrows=5, header=0, sep=",")
                c = d.columns
            except:
                print("Surrey preset was selected, but file does not follow preset. Please check file format")

        if self.datafile_preset == "LabVIEW":
            # print("LabVIEW preset selected. Attempt to read data...")
            if "tl." in path:
                c = [
                    'V_G lin', 'time', 'I_D lin', 'I_G lin',
                    '|I_D| lin', '|I_G| lin', 'sqrt I_D lin',
                    '1stderiv I_D lin', '2ndderiv I_D lin'
                ]
            elif "ts." in path:
                c = [
                    'V_G sat', 'time', 'I_D sat', 'I_G satsat',
                    '|I_D| sat', '|I_G| sat', 'sqrt I_D sat',
                    '1stderiv I_D sat', '2ndderiv I_D sat'
                ]
            else:
                print(
                    "LabVIEW preset was selected, but filename does not follow preset. Please check file format");
                return False

        if self.datafile_preset == "ParameterAnalyzer":
            # print("Parameter Analyzer preset selected. Attempt to read data...")
            try:
                d = pd.read_table(path, nrows=5, header=[0, 1])
                c = d.columns.droplevel(1)
            except:
                print(
                    "Parameter Analyzer preset was selected, but file does not follow preset. Please check file format")

        self.tab1_plot_file_choose_xdata_combobox.clear()
        self.tab1_plot_file_choose_ydata_combobox.clear()

        for i in c:
            self.tab1_plot_file_choose_xdata_combobox.addItem(i)
            self.tab1_plot_file_choose_ydata_combobox.addItem(i)

        # if it is readable sweepme data, preselect the usual plot arrays
        index_x = self.tab1_plot_file_choose_xdata_combobox.findText(
            'lin_gate Voltage', QtCore.Qt.MatchFixedString)
        index_y = self.tab1_plot_file_choose_ydata_combobox.findText(
            'lin_drain Current', QtCore.Qt.MatchFixedString)

        if index_x >= 0:
            self.tab1_plot_file_choose_xdata_combobox.setCurrentIndex(index_x)
        else:
            index_x = self.tab1_plot_file_choose_xdata_combobox.findText(
                'sat_gate Voltage', QtCore.Qt.MatchFixedString)
            self.tab1_plot_file_choose_xdata_combobox.setCurrentIndex(index_x)

        if index_y >= 0:
            self.tab1_plot_file_choose_ydata_combobox.setCurrentIndex(index_y)
        else:
            index_y = self.tab1_plot_file_choose_xdata_combobox.findText(
                'sat_drain Current', QtCore.Qt.MatchFixedString)
            self.tab1_plot_file_choose_ydata_combobox.setCurrentIndex(index_y)

        # if data is labview, index_x/y will be "found" to be -1, so retry with different column names
        if index_y == -1 and index_x == -1:
            index_x = self.tab1_plot_file_choose_xdata_combobox.findText(
                'lin_gate Voltage', QtCore.Qt.MatchFixedString)
            index_y = self.tab1_plot_file_choose_ydata_combobox.findText(
                'lin_drain Current', QtCore.Qt.MatchFixedString)
            if index_x >= 0:
                self.tab1_plot_file_choose_xdata_combobox.setCurrentIndex(index_x)
            else:
                index_x = self.tab1_plot_file_choose_xdata_combobox.findText(
                    'sat_gate Voltage', QtCore.Qt.MatchFixedString)
                self.tab1_plot_file_choose_xdata_combobox.setCurrentIndex(index_x)

            if index_y >= 0:
                self.tab1_plot_file_choose_ydata_combobox.setCurrentIndex(index_y)
            else:
                index_y = self.tab1_plot_file_choose_xdata_combobox.findText(
                    'sat_drain Current', QtCore.Qt.MatchFixedString)
                self.tab1_plot_file_choose_ydata_combobox.setCurrentIndex(index_y)

    # tab1-method that reads the datafile needed for plotting or fitting
    def read_datafile(self, filepath=None):
        if filepath is not None:
            path = filepath
        else:
            path = self.tab1_file_paths_dictionary[i] if (i := self.tab1_file_list.currentItem().text()) not in [None,
                                                                                                                 '',
                                                                                                                 'None'] else ''

        # output files are not the main target here, but they should be displayed if the user chooses to
        if "_out" in path:
            c = ['Time', 'TimeStamp', 'Vs', 'Is',
                 'Vg', 'Ig', 'Vd', 'Id']
            d = pd.read_table(path, names=c, skiprows=2, header=None)
            d['Vg'] = d['Vg'].round(2)
            # Vgs = d['Vg'].unique()
            return d

        if self.datafile_preset == "SweepMe!" or self.datafile_preset == "Marburg":
            d = pd.read_table(path,
                              header=[0, 1])


        if self.datafile_preset == "Custom":
            d = pd.read_table(path,
                              names=self.tab4_set_custom_column_names.text().split(';'),
                              skiprows=self.tab4_set_custom_skiprows.value())

        if self.datafile_preset == "Goettingen":
            d = pd.read_table(path, skiprows=2, header=1)

        if self.datafile_preset == "Surrey":
            d = pd.read_table(path, skiprows=None, header=0, sep=",")

        elif self.datafile_preset == "LabVIEW":
            if "tl." in path:
                c = [
                    'V_G lin', 'time', 'I_D lin', 'I_G lin',
                    '|I_D| lin', '|I_G| lin', 'sqrt I_D lin',
                    '1stderiv I_D lin', '2ndderiv I_D lin'
                ]
                # c = [
                #    'lin_gate Voltage', 'time', 'lin_drain Current', 'lin_gate Current',
                #    'abs_lin_drain_current', 'abs_lin_gate_current', 'sqrt_lin_drain_current',
                #    '1stderiv_lin_drain_current', '2ndderiv_lin_drain_current'
                # ]
            elif "ts." in path:
                c = [
                    'V_G sat', 'time', 'I_D sat', 'I_G satsat',
                    '|I_D| sat', '|I_G| sat', 'sqrt I_D sat',
                    '1stderiv I_D sat', '2ndderiv I_D sat'
                ]
                # c = [
                #    'sat_gate Voltage', 'time', 'sat_drain Current', 'sat_gate Current',
                #    'abs_sat_drain_current', 'abs_sat_gate_current', 'sqrt_sat_drain_current',
                #    '1stderiv_sat_drain_current', '2ndderiv_sat_drain_current'
                # ]
            d = pd.read_table(path, skiprows=2, names=c)

        if self.datafile_preset == "ParameterAnalyzer":
            c = ["idx", "VDS", "VGS", "ID", "IG"]
            d = pd.read_table(path, skiprows=5, names=c, header=None)

        return d

    # tab1-method which resets the tooltips for the QLabels which show the fitting results. the tooltip shows the pure
    # fitting error, which is not equivalent to a real physical error since it can be "randomly chosen" by choice of
    # measurement data for the fit; therefore it is not shown in the QLabel but rather its tooltip. for safety reasons,
    # it should be reset at the beginning of each analysis
    def tab1_purge_fit_error_tooltips(self):
        self.tab1_result_musat.setToolTip("---")
        self.tab1_result_mulin.setToolTip("---")
        self.tab1_result_vth.setToolTip("---")
        self.tab1_result_ssw.setToolTip("---")

    # interpretation of the linestyle setting given by user
    def resolve_linestyle(self, ls=None):
        if ls is None:
            m, l = '.', ''
        else:
            if (ls == '--'): m, l = ',','--'
            else:
                l = '-' if '-' in ls else ''
                if '.' in ls: m = '.'
                elif 'o' in ls: m = 'o'
                elif 'x' in ls: m = 'x'
                else: m = ''

        return m,l

    # method that gets used by tab1 and tab3 to determine whether the data included in the fit will be given by user
    # input or determined automatically. added 09.02.2021 to enable setting those values for TLM as well, not only TrAn
    def get_manual_fit_regions(self):
        # checking whether a fixed x-range is given for values to be used in fits
        if self.tab4_tab1settings_linfit_usefixed_xrange.isChecked():
            try:
                manualFitRange_lin = (
                    float(self.tab4_tab1settings_linfit_xmin.value()), float(self.tab4_tab1settings_linfit_xmax.value()))
            except:
                self.print_useroutput("Fixed values to be used in fit could not be converted to FLOAT.",
                                      self.tab4_outputline)
                return False
        else:
            manualFitRange_lin = False

        if self.tab4_tab1settings_satfit_usefixed_xrange.isChecked():
            try:
                manualFitRange_sat = (
                    float(self.tab4_tab1settings_satfit_xmin.value()), float(self.tab4_tab1settings_satfit_xmax.value()))
            except:
                self.print_useroutput("Fixed values to be used in fit could not be converted to FLOAT.",
                                      self.tab4_outputline)
                return False
        else:
            manualFitRange_sat = False

        if self.tab4_tab1settings_sswfit_usefixed_xrange.isChecked():
            try:
                manualFitRange_ssw = (
                    float(self.tab4_tab1settings_sswfit_xmin.value()), float(self.tab4_tab1settings_sswfit_xmax.value()))
            except:
                self.print_useroutput("Fixed values to be used in fit could not be converted to FLOAT.",
                                      self.tab4_outputline)
                return False
        else:
            manualFitRange_ssw = False

        return {'lin': manualFitRange_lin, 'sat': manualFitRange_sat, 'ssw': manualFitRange_ssw}

    def get_TLM_direction(self):
        d = None
        if self.tab3_TLM_select_direction_fwd.isChecked():
            d = "fwd"
        elif self.tab3_TLM_select_direction_back.isChecked():
            d = "back"
        elif self.tab3_TLM_select_direction_mean.isChecked():
            d = "mean"

        return d

    def get_arrhenius_direction(self):
        d = None
        if self.tab6_arrhenius_select_direction_fwd.isChecked():
            d = "fwd"
        elif self.tab6_arrhenius_select_direction_back.isChecked():
            d = "back"
        elif self.tab6_arrhenius_select_direction_mean.isChecked():
            d = "mean"

        return d
    ##########################
    # methods used for the overall interaction with the user, misc functions
    ##########################

    # just a primitive method which can be used to test a button
    def print_shit(self, message=None):
        print('something happened - shit', message)
        return True

    # method that allows feedback to the user without the need for them to hunt errors in the command line output of python
    # it also has a timestamp so the user can follow when the last message has been displayed. there is no history (so far)
    def print_useroutput(self, message, outputwidget):
        outputwidget.setText(f"[{time.strftime('%H:%M:%S')}]  {message}")

    # tab1/3 method for changing carrier type
    def update_carrier_type_button_text(self):
        if self.tab1_carrier_type_button.isChecked():
            self.tab1_carrier_type_button.setText('n')
        else:
            self.tab1_carrier_type_button.setText('p')

        if self.tab3_carrier_type_button.isChecked():
            self.tab3_carrier_type_button.setText('n')
        else:
            self.tab3_carrier_type_button.setText('p')

        if self.tab6_carrier_type_button.isChecked():
            self.tab6_carrier_type_button.setText('n')
        else:
            self.tab6_carrier_type_button.setText('p')

    # tab1-method for changing the button texts in order to mimick a switch
    def update_choose_regime_buttons_text(self):
        l_ = self.tab1_analysis_choose_lin_data_combobox.currentText()
        s_ = self.tab1_analysis_choose_sat_data_combobox.currentText()

        if self.tab1_results_choose_oor_regime.isChecked():
            self.tab1_results_choose_oor_regime.setText('On-Off Ratio (lin.)')
            if l_ == "None": self.tab1_result_onoff.clear()
        else:
            self.tab1_results_choose_oor_regime.setText('On-Off Ratio (sat.)')
            if s_ == "None": self.tab1_result_onoff.clear()

        if self.tab1_results_choose_ssw_regime.isChecked():
            self.tab1_results_choose_ssw_regime.setText('Subthr. Swing (sat.)')
            if s_ == "None": self.tab1_result_ssw.clear()
        else:
            self.tab1_results_choose_ssw_regime.setText('Subthr. Swing (lin.)')
            if l_ == "None": self.tab1_result_ssw.clear()

        if self.tab1_results_choose_vth_regime.isChecked():
            self.tab1_results_choose_vth_regime.setText('Threshold Voltage (sat.)')
            if s_ == "None": self.tab1_result_vth.clear()
        else:
            self.tab1_results_choose_vth_regime.setText('Threshold Voltage (lin.)')
            if l_ == "None": self.tab1_result_vth.clear()

        self.analyze_transfer_data()

    # tab2-method used for function plotter. not commented or overhauled. work in progress
    def get2_parameter_assignments(self):
        raw = self.var_12_value.toPlainText()
        print(f'raw parameter string: {raw}')
        par_dict = {}  # key:value -> variable:assigned_value
        for line in raw.splitlines():
            print(line)
            if '=' not in line:
                print(f"{line} states no value assignment")
                continue
            l_ = line.replace(' ', '').split('=')
            try:
                par_dict[l_[0]] = float(l_[1])
            except ValueError:
                print('One of the entered values is not numeric. Please check.')

        print(f'parameter dictionary = {par_dict}')
        return par_dict

    # tab1-method that plots the currently selected item in the "Data" canvas
    def plot_chosen_data(self):
        if self.tab1_plot_canvas_dataset.empty: self.tab1_plotting_tabs.setCurrentIndex(0)
        l_ = self.tab1_file_list.currentItem()
        if l_ is None: print('cannot plot empty data'); return False
        scale_input = self.tab1_plot_scale_menu.currentText()
        scale_dict = {'Linear (x&y)': ['linear', 'linear'], 'SemiLog (y)': ['linear', 'log'],
                      'LogLog (x&y)': ['log', 'log']}
        scale_ = scale_dict[scale_input]
        overwrite_ = self.tab1_plot_chosen_data_overwrite_checkbox.isChecked()
        label_ = self.tab1_plot_chosen_data_label.text()
        x_col = self.tab1_plot_file_choose_xdata_combobox.currentText()
        y_col = self.tab1_plot_file_choose_ydata_combobox.currentText()
        xlabel = x_col
        ylabel = y_col
        # xlabel = i if len((i:=self.tab1_plotting_data_tab_xlabel.text())) > 0 else x_col
        # ylabel = i if len((i:=self.tab1_plotting_data_tab_ylabel.text())) > 0 else y_col
        if len(l_.text()) > 0:
            try:
                d = self.read_datafile()

                # output curves are not the main focus here, but they should display correctly nevertheless
                if "_out" in l_.text():
                    Vgs = d['Vg'].unique()
                    if overwrite_: self.tab1_plot_canvas_dataset.clear()
                    for v in Vgs[:-1]:
                        self.tab1_plot_canvas_dataset.plot_data(d['Vd'][d['Vg'] == v], d['Id'][d['Vg'] == v],
                                                                scale=scale_, overwrite=False,
                                                                label=f"Vg={v}V")
                    self.tab1_plot_canvas_dataset.plot_data(d['Vd'][d['Vg'] == Vgs[-1]], d['Id'][d['Vg'] == Vgs[-1]],
                                                            scale=scale_,
                                                            overwrite=False, lastplot=True,
                                                            label=f"Vg={Vgs[-1]}V", xlabel='V_d (V)', ylabel='I_d (A)')
                    return True

                self.tab1_plot_canvas_dataset.plot_data(
                    x=d[x_col], y=d[y_col], scale=scale_, overwrite=overwrite_, label=label_, xlabel=xlabel,
                    ylabel=ylabel, lastplot=True)
            except Exception as e:
                print(e)
                return False

        if self.tab1_analysis_choose_lin_data_combobox.currentIndex() >= 1 or self.tab1_analysis_choose_sat_data_combobox.currentIndex() >= 1:
            self.analyze_transfer_data()

    # method used for function plotter. not commented or overhauled. work in progress
    def plot2_new(self):
        x_min = self.plot2_range_x_min.text()
        x_max = self.plot2_range_x_max.text()
        x_steps = self.plot2_range_x_steps.text()
        x_steps_logscale = self.plot2_range_x_steps_logscale.isChecked()
        try:
            x_min, x_max, x_steps = float(x_min), float(x_max), int(x_steps)
            if x_steps_logscale:
                x_data = np.logtab1_space(x_min, x_max, x_steps)
            elif not x_steps_logscale:
                x_data = np.linspace(x_min, x_max, x_steps)
        except Exception as e:
            print(e)
            x_data = None

        func_str = self.plot2_equation.text()
        par_assignment_dict = self.get2_parameter_assignments()
        scale_input = self.plot2_scale_menu.currentText()
        scale_dict = {'Linear (x&y)': ['linear', 'linear'], 'SemiLog (y)': ['linear', 'log'],
                      'LogLog (x&y)': ['log', 'log']}
        scale_ = scale_dict[scale_input]
        # print(f'scale={scale_}')
        # print(f'parameter_assignment_dict = {par_assignment_dict}')
        # print(f'scale_input = {scale_input}')
        if len(func_str) > 0 and type(x_data) != type(None):
            self.sc2.plot_new(
                func=func_str, par=par_assignment_dict, scale=scale_, x=x_data)
        elif len(func_str) > 0 and type(x_data) == type(None):
            print("Problem with definition of x dataset.")
        elif len(func_str) == 0:
            print("No function for plotting defined.")

    # The following three methods set up dragging and dropping of files into the application
    # Mind that this only has an effect for tabs where the data files can be used (transfer analysis, TLM, sparam, Arrhenius)
    # based on the code snippet in https://gist.github.com/benjaminirving/f45de3bbabbcacd3ca29
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()

            fnames = []
            for url in e.mimeData().urls():
                fnames.append(str(url.toLocalFile()))

            # this list has to be curated if the order of tabs is changing
            if len(fnames)>0:
                if self.tabs.currentIndex()==0:                 # transfer analysis
                    self.choose_files(filelist=fnames)
                elif self.tabs.currentIndex()==1:               # TLM analysis
                    self.choose_filesTLM(filelist=fnames)
                elif self.tabs.currentIndex()==2:               # Sparameter analysis
                    self.choose_filesSparam(filelist=fnames)
                elif self.tabs.currentIndex() == 3:  # Arrhenius analysis
                    self.choose_filesArrhenius(filelist=fnames)
                elif self.tabs.currentIndex() == 4:  # Arrhenius analysis
                    self.choose_filesInverter(filelist=fnames)
                else:
                    print("Files were drag&dropped into a tab that does not support this. Only works for Transfer Analysis and TLM.")
        else:
            e.ignore()

    # abstract method that allows drawing a vertical line as QWidget, to help the eye separate GUI regions
    def vline(self):
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    # abstract method that allows drawing a horizontal line as QWidget, to help the eye separate GUI regions
    def hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line


# main loop that executes the whole GUI
if __name__ == '__main__':
    app = QApplication()
    app.setStyle("Fusion")
    ex = App()
    sys.exit(app.exec())

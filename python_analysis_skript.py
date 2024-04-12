import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'; used to suppress SettingWithCopyWarning (df[idx] vs df.loc[:,idx])
from scipy.optimize import curve_fit
try:from analysis_function_definitions import *
except: print("Could not import the functions module (analysis_function_definitions.py). Please place it in the same directory as GUI.py")

import re
from traceback import print_exc



import warnings
warnings.simplefilter('ignore', (UserWarning, RuntimeWarning))


class TLM_Analysis():
    def __init__(self, C_ox, filenames = None, filetype = None, carrier_type = 'p', fd=None,sd=None,smoothing=.25,V_DS=None,
                 manualFitRange={'lin': False,
                                 'sat': False,
                                 'ssw': False},
                 fitRestriction=None, # could be "fwd", "back" or "mean" otherwise
                 column_settings={"names": None, "skiprows": None},
                 L_correct = None
                 ):
        self.filetype = filetype
        self.capacitance_oxide = C_ox
        self.carrier_type = carrier_type
        self.factor = -1 if self.carrier_type == 'p' else 1
        self.manualFitRanges = manualFitRange
        self.fitRestriction = fitRestriction
        self.column_settings = column_settings
        self.L_correct = L_correct
        if (fd is None) or (sd is None): self.first_deriv_limit=1; self.second_deriv_limit=0; self.deriv_lim_manual = False
        else: self.first_deriv_limit = fd; self.second_deriv_limit = sd; self.deriv_lim_manual = True
        if filenames is not None: self.filenames = filenames
        else:
            print("Please select data for TLM analysis")

        self.measurements = {}
        self.VDS = V_DS

        for i in self.filenames:
            try:
                # this try/except is only to read the sample name, to be used as plot label in the RcW(V-Vth) plot.
                # if it does not succeed, everything else can be used but the label will default to "data" (see main script)
                try:
                    m = re.match(r'.*[\\/](?P<N>[A-Za-z\d]+)[_#]?W(?P<W>[\d\.]+)[_#]*L(?P<L>[\d\.]+).*', i)
                    l = float(m.group('L'))
                    w = float(m.group('W'))
                    self.name = m.group('N')
                except:
                    m = re.match('.*[_#]?W(?P<W>[\d.]+)[_#]*L(?P<L>[\d.]+).*', i)
                    l = float(m.group('L'))
                    w = float(m.group('W'))
                    self.name = None

                # VDS should be written in the filename. however, if that is not the case (e.g. with sweepme files)
                # the real VDS will be determined from the file
                if self.VDS is None:
                    try:
                        self.VDS = float(re.match(r".*[_#]?W(?P<W>[\d.]+)[_#]*L(?P<L>[\d.]+).*V[dsDS]+(?P<VDS>[\-+\d.]+)?.*",i).group("VDS"))
                    except:
                        try:
                            if self.filetype == "SweepMe!" or self.filetype == None:
                                d = pd.read_table(i)
                                self.VDS = float(d.filter(regex='V').filter(regex='(drain)|(DS)|(_D)').iloc[3:].astype('float').mean().iloc[0])

                            if self.filetype == "Marburg":
                                d = pd.read_table(i)
                                self.VDS = float(d.filter(regex='V').filter(regex='(drain)|(DS)|(_D)').iloc[3:].astype('float').mean().iloc[0])


                            elif self.filetype == "Goettingen":
                                d = pd.read_table(i,
                                                  skiprows=2,header=1)
                                try:
                                    self.VDS = float(d['V_DS'].mean()) # SuperFunAnalyzer v2 data
                                except:
                                    self.VDS = float(d['V_Drain'].mean()) # SuperFunAnalyzer v3 data

                            elif self.filetype == "ParameterAnalyzer":
                                d = pd.read_table(i,skiprows=5,names=["idx","VDS","VGS","ID","IG"],
                                                  header=None)
                                self.VDS = float(d['VDS'].mean())
                        except:
                            print("V_DS was not set and could not be determined from file name. Please set V_DS.")
                            pass

                # check for automated L-correction (using measured channel lengths instead of nominal ones) - needs a excel database from the GUI
                if self.L_correct is not None:
                    try:
                        if self.name in self.L_correct.Sample.unique():
                            w_, l_ = w,l
                            l = _l if not np.isnan(_l:=np.nanmean(L_correct[(L_correct.Sample==self.name) & (L_correct.L_nom==l_) & (L_correct.W_nom==w_)].L_real)) else l_
                            w = _w if not np.isnan(_w:=np.nanmean(L_correct[(L_correct.Sample==self.name) & (L_correct.W_nom==w_) & (L_correct.L_nom==l_)].W_real)) else w_
                        else:
                            print(f"Sample {self.name} not in list for corrected L values. Using nominal values instead.")
                            continue
                    except Exception as e:
                        print(e)

                t = TransistorAnalysis(w, l, C_ox, filenames={'lin':i,'sat':None},filetype=self.filetype,isTLM=True,
                                       carrier_type=self.carrier_type,fd=self.first_deriv_limit,sd=self.second_deriv_limit,smoothing=smoothing,V_DS=self.VDS,
                                       manualFitRange=self.manualFitRanges,fitRestriction=self.fitRestriction,
                                       column_settings=self.column_settings)
                if l not in self.measurements.keys(): self.measurements[l] = [t]
                else: self.measurements[l].append(t)
            except:
                print_exc()
            # print(self.measurements[l].transfer_data_all)
            # print(self.measurements[l].results)
            # break

        # check for the common derivative thresholds
        if not self.deriv_lim_manual:
            for l in sorted(self.measurements.keys()):
                for t_ in self.measurements[l]:
                    try:
                        m = t_.fit_mobility_lin()
                        x_singleL, y_singleL = t_.linear_Vg, t_.linear_Id

                        # finding the smallest common derivative thresholds
                        f__, s__, ysmooth__ = m[2]
                        if f__ < self.first_deriv_limit: self.first_deriv_limit = f__
                        if s__ > self.second_deriv_limit: self.second_deriv_limit = s__

                    except:
                        continue


            for l in self.measurements.keys():
                for index in range(len(self.measurements[l])):
                    self.measurements[l][index] = TransistorAnalysis(1e6*self.measurements[l][index].channel_width, 1e6*self.measurements[l][index].channel_length,
                                        1e6*self.measurements[l][index].capacitance_oxide,
                                        filenames={'lin':self.measurements[l][index].filenames['lin'],'sat':None},filetype=self.filetype,isTLM=True,
                                        carrier_type=self.carrier_type,fd=self.first_deriv_limit,sd=self.second_deriv_limit,
                                        smoothing=smoothing,V_DS=self.VDS,
                                        manualFitRange=self.manualFitRanges,fitRestriction=self.fitRestriction,
                                        column_settings=self.column_settings)



    def contactresistance(self):
        def linear_regression(x, a, b):
            return a * x + b

        # I'm not satisfied with the fact that the dict Vths is made from scratch for each overdrive voltage
        # for now, I will leave it as is, because it's working nicely
        def single_overdrive(o):
            RWs = {}
            Vths = {}
            SSws = {}
            for l in self.measurements.keys():
                for trans_an_obj in self.measurements[l]:
                    if trans_an_obj.Vth is None: continue

                    # building lists for Vth and SSw as function of L for plotting later on
                    if l not in Vths.keys(): Vths[l] = [trans_an_obj.Vth]
                    else: Vths[l].append(trans_an_obj.Vth)

                    if l not in SSws.keys(): SSws[l] = [trans_an_obj.SSw]
                    else: SSws[l].append(trans_an_obj.SSw)

                    # include all values in the R*W data that are within one step size of the nominal overdrive voltage
                    # this is most important for fitRestriction=="mean", but also for "fwd" and "back" because the overdrive voltage is an exact measurement, not rounded
                    stepsize = trans_an_obj.Vg_stepsize
                    ovdata_tot = trans_an_obj.overdrive_data
                    ovdata_fwd = ovdata_tot.head(int(len(ovdata_tot)/2))
                    ovdata_back = ovdata_tot.tail(int(len(ovdata_tot)/2))
                    if self.fitRestriction == "mean":
                        rw = ovdata_tot[np.abs(ovdata_tot['overdrive_voltage'] - o) < np.abs(stepsize / 2)]['RW'].mean()

                    elif self.fitRestriction == "fwd":
                        rw = ovdata_fwd[np.abs(ovdata_fwd['overdrive_voltage'] - o) < np.abs(stepsize/2)]['RW'].mean()

                    elif self.fitRestriction == "back":
                        rw = ovdata_back[np.abs(ovdata_back['overdrive_voltage'] - o) < np.abs(stepsize/2)]['RW'].mean()


                    if not np.isnan(rw):
                        if l not in RWs.keys(): RWs[l] = [float(rw)]
                        else: RWs[l].append(float(rw))

                #if np.isnan(rw): print(l,o,rw)

                #print(rw)

            # x: channel length, y: width-normalized resistance
            x, y = [], []
            for l in RWs.keys():
                for i in RWs[l]:
                    x.append(1e-6 * l)
                    y.append(i)

            x, y = np.array(x), np.array(y)

            popt, pcov = curve_fit(linear_regression, x, y)

            # calculate R^2 value
            ss_residuals = np.sum((y - linear_regression(x, *popt))**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r_sq = 1 - (ss_residuals/ss_tot)

            r_sheet, r_contact = popt # both are width normalized
            r_sheet_error,r_contact_error = np.sqrt(np.diag(pcov)) # numerical fitting error

            # within the single overdrive voltage, the following data will be returned
            # contact resistance RcW, its error dRcW, sheet resistance R_sh, threshold voltage, fitting covariance and parameters, width-norm. resistance RW, R^2 value of the fit
            return r_contact, r_contact_error, r_sheet, r_sheet_error, Vths, pcov, popt, RWs, r_sq, SSws


        ovs = []
        rs = []
        errs = []
        mu0s = []
        mu0errs = []
        rs_sheet = []
        rs_sheet_errs = []
        best_ov = {'ov': np.nan, 'err': np.inf}
        all_RWs = {}

        # channel length and maximum overdrive voltage where the least overdrive voltage datapoints are found
        # using it as smallest common denominator so the analysis includes all channel lengths for the available V_ov
        least_overdrive_voltages = [np.inf, np.inf, None]
        for l in self.measurements.keys():
            for trans_an_obj in self.measurements[l]:
                try:
                    # do not use np.max!! this is a workaround, but may give wrong results if measurements
                    # are not done within a certain VGS range!! OVERHAUL!
                    # comment 2021-02-09: tbh, i am not sure anymore why this was an issue. maybe for n-channel/ambipolar TFTs?
                    lowest_max_ov = np.max(self.factor * trans_an_obj.overdrive_data['overdrive_voltage'])
                    if lowest_max_ov < least_overdrive_voltages[1]:
                        least_overdrive_voltages = [l, lowest_max_ov, trans_an_obj] # [l, max(ov[l]), analysis_object]
                except:
                    pass

        for i in least_overdrive_voltages[2].overdrive_data['overdrive_voltage']:
            if i in ovs: continue
            try:
                r_c, r_c_err, r_sh, r_sh_err, V_ths, pcov, popt, rws, r_sq, SSws = single_overdrive(i)

                ov_str = f'{i:.2f}'
                if ov_str not in all_RWs.keys(): all_RWs[ov_str] = {'r_sq':r_sq,'data':rws,'popt':popt,'pcov':pcov}
                if best_ov['err'] > r_c_err: best_ov['ov'] = ov_str;best_ov['err'] = r_c_err
                ovs.append(i)
                rs.append(r_c)
                errs.append(r_c_err)
                mu0s.append(1 / ((1e-6 * self.capacitance_oxide) * r_sh * i))
                mu0errs.append( np.abs((1 / ((1e-6 * self.capacitance_oxide) * r_sh**2 * i)))*r_sh_err )
                rs_sheet.append(r_sh)
                rs_sheet_errs.append(r_sh_err)
            except:
                if np.abs(i)>0.03: print(f"There was an error with the TLM fit for an overdrive voltage of {i:.3f}V")
                #print_exc()
                continue


        # recursive function to find the closest point to intersection of several lines with small calculation cost
        def find_l_0(l_range=np.linspace(-80e-6, 5e-6, 10), l_0=np.nan, Rc0W=np.nan, s=np.inf):
            if np.ptp(l_range) < 0.5e-6:
                return l_0, Rc0W
            else:
                for l in l_range:
                    sum_of_squares = 0
                    line_values = []
                    # determination of the mean value of all TLM fit lines for each channel length
                    for ov in all_RWs.keys():
                        # only used the high overdrive voltages (highest 30%) in the "graphical" extraction of L_0
                        # also exclude bad fits (r^2 below 0.98) and "too good fits" (a.k.a. too few points) (r^2 above 0.99999)
                        if (np.abs(float(ov)) / np.max(
                                np.abs(np.array(list(all_RWs.keys())).astype(float))) < 0.7) or (
                                all_RWs[ov]['r_sq'] < 0.98) or (all_RWs[ov]['r_sq'] > 0.99999): continue
                        line_values.append(linear_regression(l, *all_RWs[ov]['popt']))
                    Rc0W_ = np.median(line_values)

                    # determination of L0 and Rc0W by means of least squares deviation from the mean value
                    # where the least squares are, there is the closest overlap/intersection of the lines
                    for ov in all_RWs.keys():
                        # only used the high overdrive voltages (highest 30%) in the "graphical" extraction of L_0
                        if (np.abs(float(ov)) / np.max(
                                np.abs(np.array(list(all_RWs.keys())).astype(float))) < 0.7) or (
                                all_RWs[ov]['r_sq'] < 0.98) or (all_RWs[ov]['r_sq'] > 0.99999): continue
                        sum_of_squares += (linear_regression(l, *all_RWs[ov]['popt']) - Rc0W_) ** 2
                    if sum_of_squares < s: s = sum_of_squares; l_0 = l; Rc0W = Rc0W_

                stepsize = l_range[1] - l_range[0]
                next_min, next_max = l_0 - stepsize, l_0 + stepsize
                return find_l_0(l_range=np.linspace(next_min, next_max, 10), l_0=l_0, Rc0W=Rc0W)

        # for physical explanation of l_0 and Rc0W, refer to Ulrike Kraft's PhD thesis
        l_0, Rc0W = find_l_0()

        # make a readily accessible list of Vths that will be used (only) for plotting Vth(l)
        ls_temp = []
        V_ths_temp = []
        for l in V_ths.keys():
            for val in V_ths[l]:
                ls_temp.append(l)
                V_ths_temp.append(val)
        V_ths = [np.array(ls_temp), np.array(V_ths_temp)]

        # make a readily accessible list of SSws that will be used (only) for plotting SSw(l)
        ls_temp = []
        SSws_temp = []
        for l in SSws.keys():
            for val in SSws[l]:
                ls_temp.append(l)
                SSws_temp.append(val)
        SSws = [np.array(ls_temp), np.array(SSws_temp)]

        return np.array(ovs), np.array(rs), np.array(errs), best_ov, all_RWs, l_0, Rc0W,\
               np.array(mu0s), np.array(mu0errs), np.array(rs_sheet), np.array(rs_sheet_errs), V_ths, SSws


    def contactresistance_mTLM(self):
        def linear_regression(x, a, b):
            return a + b * x

        # I'm not satisfied with the fact that the dict Vths is made from scratch for each overdrive voltage
        # for now, I will leave it as is, because it's working nicely
        def single_overdrive(o):
            RWpLs = {}
            Vths = {}
            for l in self.measurements.keys():
                for trans_an_obj in self.measurements[l]:
                    if trans_an_obj.Vth is None: continue

                    # building lists for Vth and SSw as function of L for plotting later on
                    if l not in Vths.keys(): Vths[l] = [trans_an_obj.Vth]
                    else: Vths[l].append(trans_an_obj.Vth)

                    # include all values in the R*W data that are within one step size of the nominal overdrive voltage
                    # this is most important for fitRestriction=="mean", but also for "fwd" and "back" because the overdrive voltage is an exact measurement, not rounded
                    stepsize = trans_an_obj.Vg_stepsize
                    ovdata_tot = trans_an_obj.overdrive_data
                    ovdata_fwd = ovdata_tot.head(int(len(ovdata_tot)/2))
                    ovdata_back = ovdata_tot.tail(int(len(ovdata_tot)/2))
                    if self.fitRestriction == "mean":
                        rw = ovdata_tot[np.abs(ovdata_tot['overdrive_voltage'] - o) < np.abs(stepsize / 2)]['RW'].mean()

                    elif self.fitRestriction == "fwd":
                        rw = ovdata_fwd[np.abs(ovdata_fwd['overdrive_voltage'] - o) < np.abs(stepsize/2)]['RW'].mean()

                    elif self.fitRestriction == "back":
                        rw = ovdata_back[np.abs(ovdata_back['overdrive_voltage'] - o) < np.abs(stepsize/2)]['RW'].mean()


                    if not np.isnan(rw):
                        if l not in RWpLs.keys(): RWpLs[l] = [float(rw/(1e-6*l))]
                        else: RWpLs[l].append(float(rw/(1e-6*l)))

                #if np.isnan(rw): print(l,o,rw)

                #print(rw)

            # for normal TLM -- x: channel length, y: width-normalized resistance
            x, y = [], []
            for l in RWpLs.keys():
                for i in RWpLs[l]:
                    x.append(1/(1e-6*l))
                    y.append(i)

            x, y = np.array(x), np.array(y)

            popt, pcov = curve_fit(linear_regression, x, y)

            # calculate R^2 value
            ss_residuals = np.sum((y - linear_regression(x, *popt)) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_sq = 1 - (ss_residuals / ss_tot)
            r_sheet, r_contact = popt  # both are width normalized
            r_sheet_error, r_contact_error = np.sqrt(np.diag(pcov))  # numerical fitting error
            #print(popt,pcov)
            #print(f"RcW = {r_contact:.2f} + {r_contact_error:.2f} \t {r_sheet:.2f} + {r_sheet_error:.2f}")
            # within the single overdrive voltage, the following data will be returned
            # contact resistance RcW, its error dRcW, sheet resistance R_sh, threshold voltage, fitting covariance and parameters, width-norm. resistance RW, R^2 value of the fit
            return r_contact, r_contact_error, r_sheet, r_sheet_error, Vths, (pcov,popt), RWpLs, r_sq


        ovs = []
        rs = []
        errs = []
        mu0s = []
        mu0errs = []
        rs_sheet = []
        rs_sheet_errs = []
        best_ov = {'ov': np.nan, 'err': np.inf}
        all_RWpLs = {}

        # channel length and maximum overdrive voltage where the least overdrive voltage datapoints are found
        # using it as smallest common denominator so the analysis includes all channel lengths for the available V_ov
        least_overdrive_voltages = [np.inf, np.inf, None]
        for l in self.measurements.keys():
            for trans_an_obj in self.measurements[l]:
                try:
                    # do not use np.max!! this is a workaround, but may give wrong results if measurements
                    # are not done within a certain VGS range!! OVERHAUL!
                    # comment 2021-02-09: tbh, i am not sure anymore why this was an issue. maybe for n-channel/ambipolar TFTs?
                    lowest_max_ov = np.max(self.factor * trans_an_obj.overdrive_data['overdrive_voltage'])
                    if lowest_max_ov < least_overdrive_voltages[1]:
                        least_overdrive_voltages = [l, lowest_max_ov, trans_an_obj] # [l, max(ov[l]), analysis_object]
                except:
                    pass

        for i in least_overdrive_voltages[2].overdrive_data['overdrive_voltage']:
            if i in ovs: continue
            try:
                r_c, r_c_err, r_sh, r_sh_err, V_ths, (pcov, popt), rwpls, r_sq = single_overdrive(i)
                ov_str = f'{i:.2f}'
                if ov_str not in all_RWpLs.keys(): all_RWpLs[ov_str] = {'r_sq':r_sq,'data':rwpls,'popt':popt,'pcov':pcov}
                if best_ov['err'] > r_c_err: best_ov['ov'] = ov_str;best_ov['err'] = r_c_err
                ovs.append(i)
                rs.append(r_c)
                errs.append(r_c_err)
                mu0s.append(1 / ((1e-6 * self.capacitance_oxide) * r_sh * i))
                mu0errs.append( np.abs((1 / ((1e-6 * self.capacitance_oxide) * r_sh**2 * i)))*r_sh_err )
                rs_sheet.append(r_sh)
                rs_sheet_errs.append(r_sh_err)
            except:
                if np.abs(i)>0.03: print(f"There was an error with the TLM fit for an overdrive voltage of {i:.3f}V")
                #print_exc()
                continue



        return np.array(ovs), np.array(rs), np.array(errs), best_ov, all_RWpLs,\
               np.array(mu0s), np.array(mu0errs), np.array(rs_sheet), np.array(rs_sheet_errs)


    def intr_mob(self):
        def intr_mu(L, l_1_2, mu0):  # equation taken from ulrikes thesis, page 60
            return mu0 / (1 + (l_1_2 / L))

        mu_data = {}
        for l in self.measurements.keys():
            for trans_an_obj in self.measurements[l]:
                if trans_an_obj.Vth is None: continue

                if self.fitRestriction == "mean":
                    mu = trans_an_obj.fit_mobility_lin()[0]['mean'][0]
                elif self.fitRestriction == "fwd":
                    mu = trans_an_obj.fit_mobility_lin()[0]['fwd'][0]
                elif self.fitRestriction == "back":
                    mu = trans_an_obj.fit_mobility_lin()[0]['back'][0]

                if not l in mu_data.keys(): mu_data[l] = [mu]
                else: mu_data[l].append(mu)

        ls, ms = [], []
        for l_ in mu_data.keys():
            for m_ in mu_data[l_]:
                ls.append(1e-6 * l_)
                ms.append(m_)
        ls, ms = np.array(ls), np.array(ms)

        popt, pcov = curve_fit(intr_mu, ls, ms)
        # print(popt)

        l_1_2, mu0 = popt
        l_1_2_err, mu0_err = np.sqrt(np.diag(pcov))

        # returns transfer lengths, intrinsic mobility, l- and mu-data for plotting it, and the respective fitting errors
        return l_1_2, mu0, ls, ms, l_1_2_err, mu0_err


    def get_transfer_curves(self):
        data = {}
        for l in self.measurements.keys():
            for trans_an_obj in self.measurements[l]:
                data_dict = {'Vg':trans_an_obj.linear_Vg,'Id':trans_an_obj.linear_Id,'Ig':trans_an_obj.linear_Ig,
                             'fitpoints':trans_an_obj.linearFitData}

                if not l in data.keys(): data[l] = [data_dict]
                else: data[l].append(data_dict)

        return data


class TransistorAnalysis():
    def __init__(self, W, L, C_ox, carrier_type='p', filenames=None, filetype=None,
                 fd=.75, sd=.4, smoothing=.25, V_DS = -.1, isTLM=False,
                 manualFitRange={'lin':False,
                                'sat':False,
                                'ssw':False},
                 fitRestriction=None,  # could be "fwd", "back" or "mean" otherwise
                 ss_region = 'lin', oor_region = 'sat', oor_avg = 4, column_settings={"names":None,"skiprows":None},
                 sample_name=None
                 ):
        # input of W,L,C_ox in µm and µF/cm², respectively. fd and sd are thresholds for automatic data fit

        self.filenames = filenames
        self.filetype = filetype

        self.carrier_type = carrier_type
        self.channel_width = W * 1e-6
        self.channel_length = L * 1e-6
        self.capacitance_oxide = C_ox * 1e-6
        self.linear_source_drain_voltage = V_DS
        self.first_deriv_limit = fd
        self.second_deriv_limit = sd
        self.smoothing = smoothing
        self.manualFitRanges = manualFitRange
        self.fitRestriction = fitRestriction # this is not used for now. will be used later on to make it possible to use data files with only fwd or back data.
        self.ss_region = ss_region
        self.oor_region = oor_region
        self.oor_avg_window = oor_avg
        self.f = -1 if self.carrier_type == 'p' else 1 if self.carrier_type == 'n' else None
        self.column_names = i.split(";") if ((i:=column_settings["names"]) is not None) else None
        self.skiprows = column_settings["skiprows"]

        try:
            c = pd.read_table(self.filenames['lin'],nrows=5).columns
            file_ext = self.filenames['lin'].split('.')[-1]
        except:
            try:
                c = pd.read_table(self.filenames['sat'],nrows=5).columns
                file_ext = self.filenames['sat'].split('.')[-1]
            except:
                c = []
                try: file_ext = self.filenames['lin'].split('.')[-1]
                except: file_ext = self.filenames['sat'].split('.')[-1]
                pass

        if self.filetype is None: self.filetype = "SweepMe!" if any(['_gate' in i for i in c])\
            else "Goettingen" if any(["GOETT" in i for i in [j for j in self.filenames.values() if j is not None]])\
            else "LabVIEW" if (any(['GS' in i for i in c]) and any([i == file_ext for i in ["dat","DAT"]]))\
            else "ParameterAnalyzer" if file_ext=="TXT"\
            else False

        if self.filetype == "Custom":
            transfer_column_names = {'lin':self.column_names,'sat':[i.replace('lin','sat') for i in self.column_names]}
            skiprows = self.skiprows
            sep = "\t"
            print("Use custom data preset on your own risk. Errors in syntax, column names etc can happen!!")

        elif self.filetype == "SweepMe!":
            transfer_column_names = {
                'lin':['time_elapsed', 'timestamp', 'lin_source Voltage', 'lin_source Current', 'lin_source Resistance',
                       'lin_drain Voltage', 'lin_drain Current', 'lin_drain Resistance',
                       'lin_gate Voltage', 'lin_gate Current', 'lin_gate Resistance'],
                'sat':['time_elapsed', 'timestamp', 'sat_source Voltage', 'sat_source Current', 'sat_source Resistance',
                       'sat_drain Voltage', 'sat_drain Current', 'sat_drain Resistance',
                       'sat_gate Voltage', 'sat_gate Current', 'sat_gate Resistance']} if any(['Resistance' in i for i in c]) else {
                'lin': ['time_elapsed', 'timestamp', 'lin_source Voltage', 'lin_source Current', 'lin_drain Voltage',
                        'lin_drain Current', 'lin_gate Voltage', 'lin_gate Current'],
                'sat': ['time_elapsed', 'timestamp', 'sat_source Voltage', 'sat_source Current', 'sat_drain Voltage',
                        'sat_drain Current', 'sat_gate Voltage', 'sat_gate Current']}
            skiprows = 3
            sep = "\t"

        elif self.filetype == "Marburg":
            transfer_column_names = {
                'lin': ['time_elapsed', 'timestamp', 'lin_drain Voltage', 'lin_drain Current',
                        'lin_drain Resistance', 'lin_gate Voltage', 'lin_gate Current', 'lin_gate Resistance'],
                'sat': ['time_elapsed', 'timestamp', 'sat_drain Voltage','sat_drain Resistance',
                        'sat_drain Current', 'sat_gate Voltage', 'sat_gate Current', 'sat_gate Resistance']} if any(['Resistance' in i for i in c]) else {
                'lin': ['time_elapsed', 'timestamp', 'lin_drain Voltage',
                        'lin_drain Current', 'lin_gate Voltage', 'lin_gate Current'],
                'sat': ['time_elapsed', 'timestamp', 'sat_drain Voltage',
                        'sat_drain Current', 'sat_gate Voltage', 'sat_gate Current']}
            skiprows = 3
            sep = "\t"

        elif self.filetype == "Goettingen":
            transfer_column_names = {
                'lin':['lin_drain Voltage', 'lin_gate Voltage', 'lin_drain Current', 'lin_gate Current', 'time_elapsed','empty'],
                'sat':['sat_drain Voltage', 'sat_gate Voltage', 'sat_drain Current', 'sat_gate Current', 'time_elapsed','empty']
            }  if self.column_names == None else self.column_names
            skiprows = 4
            sep = "\t"

        elif self.filetype == "LabVIEW":
            transfer_column_names = {
                'lin':['lin_gate Voltage', 'time', 'lin_drain Current', 'lin_gate Current', 'abs_lin_drain_current',
                       'abs_lin_gate_current', 'sqrt_lin_drain_current', '1stderiv_lin_drain_current', '2ndderiv_lin_drain_current'],
                'sat':['sat_gate Voltage', 'time', 'sat_drain Current', 'sat_gate Current', 'abs_sat_drain_current',
                       'abs_sat_gate_current', 'sqrt_sat_drain_current','1stderiv_sat_drain_current', '2ndderiv_sat_drain_current']}
            skiprows = 2
            sep = "\t"

        elif self.filetype == "ParameterAnalyzer":
                transfer_column_names = {
                    'lin':['idx', 'lin_drain Voltage', 'lin_gate Voltage', 'lin_drain Current','lin_gate Current'],
                    'sat':['idx', 'sat_drain Voltage', 'sat_gate Voltage', 'sat_drain Current','sat_gate Current']}
                skiprows = 5
                sep="\t"

        elif self.filetype == "Surrey":
            transfer_column_names = {
                'lin': ['rep','point','lin_drain Voltage','lin_drain Current','tdrain','lin_gate Voltage','lin_gate Current','tgate'],
                'sat': ['rep','point','sat_drain Voltage','sat_drain Current','tdrain','sat_gate Voltage','sat_gate Current','tgate']}
            skiprows = 1
            sep = ','


        if self.filenames['lin'] is not None:
            try:
                self.transfer_data_linear = pd.read_table(self.filenames['lin'],
                                                          skiprows=skiprows,
                                                          names=transfer_column_names['lin'],
                                                          header=None, index_col=None, sep=sep)
                self.linear_Vg = self.transfer_data_linear['lin_gate Voltage']
                self.linear_Id = self.f * self.transfer_data_linear['lin_drain Current'] + 1e-15 # needed for log description I think? comment Sept 2021
                self.linear_Ig = self.f * self.transfer_data_linear['lin_gate Current']

            except:
                print("Something went wrong during reading of the datafile for Transistor Analysis (linear).")
                self.Vth = None

        if self.filenames['sat'] is not None:
            try:
                self.transfer_data_saturation = pd.read_table(self.filenames['sat'],
                                                              skiprows=skiprows,
                                                              names=transfer_column_names['sat'],
                                                              header=None, index_col=None)
                self.saturation_Vg = self.transfer_data_saturation['sat_gate Voltage']
                self.saturation_Id = self.f * self.transfer_data_saturation['sat_drain Current'] + 1e-15 # needed for log description I think? comment Sept 2021
                self.saturation_Ig = self.f * self.transfer_data_saturation['sat_gate Current']
            except:
                print("Something went wrong during reading of the datafile for Transistor Analysis (saturation.")



        try:
            ###################### some Analysis included (needed) for overdrive voltage ####################
            if isTLM:

                # check if there is a "lin" in the file name. this will save time searching errors in case
                # some idiot (me) includes saturation/output data in the file list
                if not any([i in self.filenames["lin"] for i in ["_lin","_tl"]]):
                    print("Check loaded data files, there is one without a 'lin' in them - maybe loaded wrong for TLM?")

                fml = self.fit_mobility_lin()
                ssw = self.subthreshold_swing()

                # this is used to plot single channel length fits in a separate tab
                try:
                    self.linearFitData = fml[3]
                except:
                    print(self.channel_length*1e6)

                if fml is None:
                    self.Vth = None
                    print(f'L={self.channel_length:.2e}m cant be fitted for Vth and will be ignored in the TLM analysis.')
                else:
                    popts_fml = fml[0]
                    if self.fitRestriction == "mean":
                        self.Vth = popts_fml['mean'][1]

                    elif self.fitRestriction == "fwd":
                        self.Vth = popts_fml['fwd'][1]

                    elif self.fitRestriction == "back":
                        self.Vth = popts_fml['back'][1]

                if ssw is None:
                    self.SSw = np.nan
                    print(f'L={self.channel_length:.2e}m has problems with SSw fitting.')
                else:
                    popts_ssw = ssw[0]
                    if self.fitRestriction == "mean":
                        self.SSw = -1000 / popts_ssw['mean'][0]

                    elif self.fitRestriction == "fwd":
                        self.SSw = -1000 / popts_ssw['fwd'][0]

                    elif self.fitRestriction == "back":
                        self.SSw = -1000 / popts_ssw['back'][0]


                # determining the average step size (assumes linear spacing!!) since SweepMe! measures the exact voltage,
                # Vg_stepsize is not necessarily equal to the nominal step size.
                self.Vg_stepsize = np.abs(np.mean([self.transfer_data_linear['lin_gate Voltage'][i+1] - self.transfer_data_linear['lin_gate Voltage'][i]
                       for i in range(len(self.transfer_data_linear['lin_gate Voltage'])//2-1)]))

                def find_nearest(array, value):
                    array = np.asarray(array)
                    idx = (np.abs(array - value)).argmin()
                    return array[idx]
                Vth_round = np.round(find_nearest(np.arange(-50, 50, self.Vg_stepsize), self.Vth), 2)

                # RW in Ohm cm
                self.transfer_data_linear['RW'] = self.channel_width * self.linear_source_drain_voltage / self.transfer_data_linear['lin_drain Current']
                self.transfer_data_linear['overdrive_voltage'] = self.transfer_data_linear['lin_gate Voltage'] - Vth_round
                if self.carrier_type == 'p': self.overdrive_data = self.transfer_data_linear[self.transfer_data_linear['overdrive_voltage'] <= 0]
                elif self.carrier_type == 'n': self.overdrive_data = self.transfer_data_linear[self.transfer_data_linear['overdrive_voltage'] >= 0]

        except:
            self.Vth = None
            if isTLM:
                #print_exc()
                print(f'L={self.channel_length:.2e}m cant be fitted and will be ignored in the TLM analysis.')


    def on_off_ratio(self, ignore=2):
        # calculate the on-off-ratio for saturation regime
        # average the maximum and minimum values to account for noisy data, especially in the off state
        # differentiate between fwd and back sweep
        # python can throw RuntimeWarning because the averaging data can be empty ->
        # and the division for the ration could be infinite
        try:
            if self.oor_region == 'lin': I_d = self.linear_Id
            elif self.oor_region == 'sat': I_d = self.saturation_Id
        except AttributeError: return False
        a = ignore
        b = -ignore
        halflength = len(I_d) // 2

        # abs needed, otherwise log10 might return np.nan
        I_fwd = np.abs(I_d[a:halflength])
        I_back = np.abs(I_d[halflength:b])
        avg_window = self.oor_avg_window

        #min_fwd, min_back = np.mean(I_fwd[:avg_window]), np.mean(   # old, faulty way to do it. prerequisite is that off state is at beginning of data
        #    I_back[-avg_window:])
        min_fwd, min_back = I_fwd.sort_values(ascending=True).iloc[0:avg_window].mean(), I_back.sort_values(ascending=True).iloc[0:avg_window].mean()
        min_mean = (min_fwd + min_back) / 2

        #max_fwd, max_back = np.mean(I_fwd[-avg_window:]), np.mean(
        #    I_back[:avg_window])
        max_fwd, max_back = I_fwd.sort_values(ascending=False).iloc[0:avg_window].mean(), I_back.sort_values(ascending=False).iloc[0:avg_window].mean()
        max_mean = (max_fwd + max_back) / 2

        r_fwd = np.log10(max_fwd / min_fwd)
        r_back = np.log10(max_back / min_back)
        r_mean = np.log10(max_mean / min_mean)
        return r_fwd, r_back, r_mean, (
            min_mean, max_mean)  # 3-tuple of log-ratios given in decades

    def subthreshold_swing(self, ignore=10):
        if self.ss_region == 'lin':
            x = self.linear_Vg
            y = self.linear_Id
        elif self.ss_region == 'sat':
            x = self.saturation_Vg
            y = self.saturation_Id
        # ignore the first a steps for fwd and the last 10 steps for back sweep to cut out noisy off state
        a = ignore
        b = -a
        halflength = len(x) // 2
        fd_input = self.first_deriv_limit

        # determine the datapoints around the linear part of the curve by normalizing to the largest 1st derivative
        # and taking only values where the 1st derivative is larger than a set value; differentiate between fwd and back
        fd = first_derivative(np.log10(np.abs(
            y)),gauss_s=self.smoothing)  # np.abs is needed to account for negative noise values
        max_slope = np.amax(fd[a:halflength])
        norm = fd / max_slope
        breakall = False
        for ff_ in np.arange(1, 0, -.1):
            if breakall: break

            #####
            # FOR NOW THIS FEATURE OF SETTING THE THRESHOLD MANUALL IS DISABLED
            # it keeps the TLM from running and more often than not it does not work properly
            # working now for TLM, but it does not work to set it manually for the TransferAnalysis tab
            # I do not know why, but it has to be adressed sooner rather than later (25.02.2021)
            #if fd_input > 0.01:
            #    min_val = fd_input
            #    breakall = True
            #
            #else:
            min_val = ff_

            try:
                if self.manualFitRanges['ssw'] is False:
                    xfit_fwd, yfit_fwd, xfit_back, yfit_back = [], [], [], []
                    for i in range(len(x[a:halflength])):
                        # iloc indexing is needed because pandas doesnt allow negative indexing natively (?)
                        if (norm[a + i] > min_val) and not (
                                (y.iloc[a + i + 2] < y.iloc[a + i]) and
                                (y.iloc[a + i - 2] < y.iloc[a + i])):
                            xfit_fwd.append(x.iloc[a + i])
                            yfit_fwd.append(y.iloc[a + i])
                        if (-norm[b - i] > min_val) and not (
                                (y.iloc[b - i + 2] < y.iloc[b - i]) and
                                (y.iloc[b - i - 2] < y.iloc[b - i])):
                            xfit_back.append(x.iloc[b - i])
                            yfit_back.append(y.iloc[b - i])
                else:
                    xmin, xmax = self.manualFitRanges['ssw']
                    if xmin > xmax: xmin_ = xmin; xmin= xmax; xmax = xmin_; del xmin_

                    xfit_fwd, yfit_fwd, xfit_back, yfit_back = [], [], [], []
                    for i in range(len(x) // 2):
                        if i == 0:
                            continue
                        if xmax > x.iloc[i] > xmin:
                            xfit_fwd.append(x.iloc[i])
                            yfit_fwd.append(y.iloc[i])
                        if xmax > x.iloc[-i] > xmin:
                            xfit_back.append(x.iloc[-i])
                            yfit_back.append(y.iloc[-i])

                xfit_fwd, yfit_fwd, xfit_back, yfit_back = np.array(
                    xfit_fwd), np.array(yfit_fwd), np.array(xfit_back), np.array(
                    yfit_back)
                xfit_tot, yfit_tot = np.concatenate(
                    (xfit_fwd, xfit_back)), np.concatenate((yfit_fwd, yfit_back))

                def linear_regression(x, a, b):
                    return a * x + b

                if len(xfit_fwd)<3 or len(xfit_back)<3: continue
                popt_fwd, pcov_fwd = curve_fit(linear_regression, xfit_fwd,
                                               np.log10(np.abs(yfit_fwd)),check_finite=True)
                popt_back, pcov_back = curve_fit(linear_regression, xfit_back,
                                                 np.log10(np.abs(yfit_back)),check_finite=True)
                popt_tot, pcov_tot = curve_fit(linear_regression, xfit_tot,
                                               np.log10(np.abs(yfit_tot)),check_finite=True)
                popt_mean = 1 / 2 * np.array(
                    [popt_fwd[0] + popt_back[0], popt_fwd[1] + popt_back[1]])

                ssw_fwd_err = np.sqrt(np.diag(pcov_fwd))[0]
                ssw_back_err = np.sqrt(np.diag(pcov_back))[0]
                ssw_mean_err = 0.5 * (np.sqrt(np.diag(pcov_fwd))[0] + np.sqrt(np.diag(pcov_back))[0])


                # determine what values to include in the plot of the fitted line. should be the values included in fit plus some area around
                if self.carrier_type == 'p':
                    start, stop = np.where(x == np.max(xfit_fwd))[0][0], np.where(
                        x == np.min(xfit_fwd))[0][0]
                elif self.carrier_type == 'n':
                    start, stop = np.where(x == np.min(xfit_fwd))[0][0], np.where(
                        x == np.max(xfit_fwd))[0][0]
                start -= 5
                stop += 5
                x_plot_line = x[start:stop]

                # if the code runs until here, fitting was successful and fd/sd dont need to be adjusted anymore
                breakall = True

                errors = [ssw_fwd_err, ssw_back_err, ssw_mean_err]
                popts = {'fwd':popt_fwd,'back':popt_back,'tot':popt_tot,'mean':popt_mean}
                fit_data = [xfit_fwd, xfit_back, yfit_fwd, yfit_back]
                fitresult_data = [xfit_fwd, xfit_back, yfit_fwd, yfit_back, x_plot_line]
                automatic_determination = min_val

                return popts, fitresult_data, fit_data, errors, automatic_determination
                #return popt_fwd, popt_back, popt_tot, popt_mean, xfit_fwd, xfit_back, x_plot_line, yfit_fwd, yfit_back, min_val, errors

            except: continue


    def fit_mobility_lin(self):

        x_data = self.linear_Vg
        y_data = self.linear_Id
        V_d = self.linear_source_drain_voltage
        Z = self.channel_width
        L = self.channel_length
        C_ox = self.capacitance_oxide
        halflength = len(x_data) // 2
        fd_input = self.first_deriv_limit
        sd_input = self.second_deriv_limit

        y_smooth = smoothing(y_data,gauss_s=self.smoothing)
        first_deriv = first_derivative(y_data,gauss_s=self.smoothing)
        second_deriv = second_derivative(y_data,gauss_s=self.smoothing)

        # normalization in order to avoid hardcoding - derivative values w/o normalization are somewhat random
        # 07.01.2021: added limitation for the maximum to be close to operating voltages so that random spikes
        # in the derivative in the off state cannot mess up the fitting; requires hardcoded >1e2 on-off-ratio
        first_deriv /= np.max(np.abs(first_deriv[np.abs(y_data) > 1e2*np.min(np.abs(y_data))]))
        second_deriv /= np.max(np.abs(second_deriv[10:halflength - 10][np.abs(y_data[10:halflength - 10]) > 1e2*np.min(np.abs(y_data[10:halflength - 10]))]))

        # automatically determine which datapoints to include in fit. separately for forward and backward sweep
        # note: this could be done so much more elegent with pandas dataframes, but never change a running system (28.3.2022)
        breakall = False
        for ff_ in np.arange(1, 0, -.1):
            if breakall: break
            for ss_ in np.arange(0, 1, .1):
                if breakall: break
                if (sd_input >= 0.01) and (fd_input >= 0.01):
                    sd_min_val = sd_input; fd_min_val = fd_input#; breakall = True
                else:
                    sd_min_val = ss_; fd_min_val = ff_

                try:
                    if self.manualFitRanges['lin'] is False:
                        xfit_fwd, yfit_fwd, xfit_back, yfit_back = [], [], [], []

                        for i in range(len(x_data) // 2):
                            if i == 0:
                                continue
                            if (np.abs(second_deriv[i]) < sd_min_val) and (np.abs(
                                    first_deriv[i]) > fd_min_val):
                                xfit_fwd.append(x_data.iloc[i])
                                yfit_fwd.append(y_data.iloc[i])
                            if (np.abs(second_deriv[-i]) < sd_min_val) and (np.abs(
                                    first_deriv[-i]) > fd_min_val):
                                xfit_back.append(x_data.iloc[-i])
                                yfit_back.append(y_data.iloc[-i])
                        #print(self.channel_length,xfit_fwd,xfit_back)

                    else:
                        xmin, xmax = self.manualFitRanges['lin']
                        if xmin > xmax: xmin_ = xmin; xmin = xmax; xmax = xmin_; del xmin_

                        xfit_fwd, yfit_fwd, xfit_back, yfit_back = [], [], [], []

                        for i in range(len(x_data) // 2):
                            if i == 0:
                                continue
                            if xmax > x_data.iloc[i] > xmin:
                                xfit_fwd.append(x_data.iloc[i])
                                yfit_fwd.append(y_data.iloc[i])
                            if xmax > x_data.iloc[-i] > xmin:
                                xfit_back.append(x_data.iloc[-i])
                                yfit_back.append(y_data.iloc[-i])

                    # ensure that fitting would run smoothly and results would be somewhat reliable
                    if (len(xfit_fwd) < 3) or (len(xfit_back) < 3): continue

                    # convert python lists to numpy arrays to do easily modify (e.g. multiply by factor)
                    xfit_fwd, yfit_fwd, xfit_back, yfit_back = np.array(xfit_fwd), np.array(yfit_fwd),\
                                                               np.array(xfit_back), np.array(yfit_back)

                    # fit routine for forward and backward sweep as well as all datapoints selected for the fit (to compare fwd/back mean with total fit)
                    popt_fwd, pcov_fwd = curve_fit(
                        lambda V_g, mu_eff, V_th: mobility_lin(
                            V_g, V_d, Z, L, C_ox, mu_eff, V_th), xfit_fwd, yfit_fwd)
                    popt_back, pcov_back = curve_fit(
                        lambda V_g, mu_eff, V_th: mobility_lin(
                            V_g, V_d, Z, L, C_ox, mu_eff, V_th), xfit_back, yfit_back)
                    popt_tot, pcov_tot = curve_fit(
                        lambda V_g, mu_eff, V_th: mobility_lin(V_g, V_d, Z, L, C_ox,
                                                               mu_eff, V_th),
                        np.concatenate((xfit_fwd, xfit_back)),
                        np.concatenate((yfit_fwd, yfit_back)))
                    popt_avg = np.array([
                        0.5 * (popt_fwd[0] + popt_back[0]),
                        0.5 * (popt_fwd[1] + popt_back[1])
                    ])
                    mulin_fwd_err, vthlin_fwd_err = np.sqrt(np.diag(pcov_fwd))
                    mulin_back_err, vthlin_back_err = np.sqrt(np.diag(pcov_back))
                    mulin_mean_err, vthlin_mean_err = 0.5 * (np.sqrt(np.diag(pcov_fwd)) + np.sqrt(np.diag(pcov_back)))

                    breakall = True

                    # caluclate reliability factor (DOI: 10.1038/nmat5035)
                    y = np.array(y_data)
                    reliability_fwd = (  (np.max(np.abs(y[:halflength]))-np.abs(y[0]))/np.max(np.abs(x_data[:halflength]))  ) / (np.abs(V_d)*Z*C_ox*popt_fwd[0]/L)
                    reliability_back = (  (np.max(np.abs(y[halflength:]))-np.abs(y[-1]))/np.max(np.abs(x_data[halflength:]))  ) / (np.abs(V_d)*Z*C_ox*popt_back[0]/L)
                    reliability_mean = 1/2 * (reliability_fwd+reliability_back)

                    # calculate data to be shown in fits
                    if self.carrier_type == 'p':
                        start, stop = np.where(x_data == np.max(xfit_fwd))[0][0], np.where(
                            x_data == np.min(xfit_fwd))[0][0]
                    elif self.carrier_type == 'n':
                        start, stop = np.where(x_data == np.min(xfit_fwd))[0][0], np.where(
                            x_data == np.max(xfit_fwd))[0][0]

                    start -= 5
                    stop += 5
                    x_data_fit = x_data[start:stop]
                    y_data_fit_fwd = mobility_lin(x_data[start:stop], V_d, Z, L, C_ox, *popt_fwd)
                    y_data_fit_back = mobility_lin(x_data[start:stop], V_d, Z, L, C_ox, *popt_back)

                    errors = {"fwd":(mulin_fwd_err,vthlin_fwd_err),
                              "back":(mulin_back_err, vthlin_back_err),
                              "mean":(mulin_mean_err, vthlin_mean_err)}

                    automatic_determination_parameters = (fd_min_val, sd_min_val, y_smooth)
                    popts = {"fwd":popt_fwd, "back":popt_back, "mean":popt_avg}
                    fitresult_data = (x_data_fit, y_data_fit_fwd, y_data_fit_back) # bundling the fitting lines
                    fit_data = (xfit_fwd, xfit_back, yfit_fwd, yfit_back) # bundling together to plot datapoints used in fits
                    reliability = {"fwd":reliability_fwd, "back":reliability_back, "mean":reliability_mean}

                    return popts, fitresult_data, automatic_determination_parameters, fit_data, reliability, errors
                   #return popt_fwd, popt_back, popt_tot, avg, x_data_fit, y_data_fit_fwd, y_data_fit_back, y_smooth, fd_min_val, sd_min_val, xfit_fwd, xfit_back, yfit_fwd, yfit_back, reliability_fwd, reliability_back, reliability_mean, errors
                except:
                    continue


    def fit_mobility_sat(self):
        x_data = self.saturation_Vg
        y_data = self.saturation_Id
        Z = self.channel_width
        L = self.channel_length
        C_ox = self.capacitance_oxide
        fd_input = self.first_deriv_limit
        sd_input = self.second_deriv_limit

        halflength = len(x_data) // 2

        y_smooth = smoothing(y_data,gauss_s=self.smoothing)
        first_deriv = first_derivative(y_data,gauss_s=self.smoothing)
        second_deriv = second_derivative(y_data,gauss_s=self.smoothing)

        # normalization in order to avoid hardcoding - derivative values w/o normalization are somewhat random
        # 07.01.2021: added limitation for the maximum to be close to operating voltages so that random spikes
        # in the derivative cannot mess up the fitting; requires hardcoded >1e2 on-off-ratio

        first_deriv /= np.nanmax(np.abs(first_deriv[np.abs(y_data) > 1e2 * np.min(np.abs(y_data))]))
        second_deriv /= np.nanmax(np.abs(second_deriv[10:halflength - 10][
                                          np.abs(y_data[10:halflength - 10]) > 1e2 * np.min(
                                              np.abs(y_data[10:halflength - 10]))]))

        breakall = False
        for ff_ in np.arange(1,0,-.1):
            if breakall: break
            for ss_ in np.arange(1,0,-.1):
                if breakall: break
                if (sd_input >= 0.01) and (fd_input >= 0.01):
                    sd_min_val = sd_input; fd_min_val = fd_input; breakall = True
                else:
                    sd_min_val = ss_; fd_min_val = ff_
                try:
                    if self.manualFitRanges['sat'] is False:
                        xfit_fwd, yfit_fwd, xfit_back, yfit_back = [], [], [], []

                        for i in range(len(x_data) // 2):
                            if i == 0:
                                continue
                            if (np.abs(second_deriv[i]) > sd_min_val) and (np.abs(
                                    first_deriv[i]) > fd_min_val):
                                xfit_fwd.append(x_data.iloc[i])
                                yfit_fwd.append(y_data.iloc[i])
                            if (np.abs(second_deriv[-i]) > sd_min_val) and (np.abs(
                                    first_deriv[-i]) > fd_min_val):
                                xfit_back.append(x_data.iloc[-i])
                                yfit_back.append(y_data.iloc[-i])

                    else:
                        xmin, xmax = self.manualFitRanges['sat']
                        if xmin > xmax: xmin_ = xmin; xmin = xmax; xmax = xmin_; del xmin_

                        xfit_fwd, yfit_fwd, xfit_back, yfit_back = [], [], [], []
                        for i in range(len(x_data) // 2):
                            if i == 0:
                                continue
                            if xmax > x_data.iloc[i] > xmin:
                                xfit_fwd.append(x_data.iloc[i])
                                yfit_fwd.append(y_data.iloc[i])
                            if xmax > x_data.iloc[-i] > xmin:
                                xfit_back.append(x_data.iloc[-i])
                                yfit_back.append(y_data.iloc[-i])

                    # ensure that fitting would run smoothly and results would be reliable
                    if (len(xfit_fwd) < 3) or (len(xfit_back) < 3): continue

                    xfit_fwd, yfit_fwd, xfit_back, yfit_back = np.array(
                        xfit_fwd), np.array(yfit_fwd), np.array(xfit_back), np.array(
                        yfit_back)
                    popt_fwd, pcov_fwd = curve_fit(
                        lambda V_g, mu_eff, V_th: mobility_sat_simplified(
                            V_g, mu_eff, V_th, Z, L, C_ox), xfit_fwd, yfit_fwd, check_finite=False)
                    popt_back, pcov_back = curve_fit(
                        lambda V_g, mu_eff, V_th: mobility_sat_simplified(
                            V_g, mu_eff, V_th, Z, L, C_ox), xfit_back, yfit_back, check_finite=False)
                    popt_tot, pcov_tot = curve_fit(
                        lambda V_g, mu_eff, V_th: mobility_sat_simplified(
                            V_g, mu_eff, V_th, Z, L, C_ox),
                        np.concatenate((xfit_fwd, xfit_back)),
                        np.concatenate((yfit_fwd, yfit_back)), check_finite=False)
                    popt_avg = np.array([
                        0.5 * (popt_fwd[0] + popt_back[0]),
                        0.5 * (popt_fwd[1] + popt_back[1])
                    ])

                    musat_fwd_err, vthsat_fwd_err = np.sqrt(np.diag(pcov_fwd))
                    musat_back_err, vthsat_back_err = np.sqrt(np.diag(pcov_back))
                    musat_mean_err, vthsat_mean_err = 0.5 * (np.sqrt(np.diag(pcov_fwd)) + np.sqrt(np.diag(pcov_back)))

                    breakall = True

                    # caluclate reliability factor (DOI: 10.1038/nmat5035)
                    y = np.array(y_data)
                    reliability_fwd = ((np.sqrt(np.max(np.abs(y[:halflength]))) - np.sqrt(np.abs(y[0]))) / np.max(
                        np.abs(x_data[:halflength])))**2 / (Z * C_ox * popt_fwd[0] / (2*L))
                    reliability_back = ((np.sqrt(np.max(np.abs(y[halflength:]))) - np.sqrt(np.abs(y[-1]))) / np.max(
                        np.abs(x_data[halflength:])))**2 / (Z * C_ox * popt_back[0] / (2*L))
                    reliability_mean = 1 / 2 * (reliability_fwd + reliability_back)

                    if self.carrier_type == 'p':
                        start, stop = np.where(x_data == np.max(xfit_fwd))[0][0], np.where(
                            x_data == np.min(xfit_fwd))[0][0]
                    elif self.carrier_type == 'n':
                        start, stop = np.where(x_data == np.min(xfit_fwd))[0][0], np.where(
                            x_data == np.max(xfit_fwd))[0][0]
                    start -= 5
                    stop += 5
                    x_data_fit = x_data[start:stop]
                    y_data_fit_fwd = mobility_sat_simplified(x_data[start:stop], *popt_fwd, Z, L, C_ox)
                    y_data_fit_back = mobility_sat_simplified(x_data[start:stop], *popt_back, Z, L, C_ox)

                    errors = {"fwd": (musat_fwd_err, vthsat_fwd_err),
                              "back": (musat_back_err, vthsat_back_err),
                              "mean": (musat_mean_err, vthsat_mean_err)}
                    automatic_determination_parameters = (fd_min_val, sd_min_val, y_smooth)
                    popts = {"fwd": popt_fwd, "back": popt_back, "mean": popt_avg}
                    fitresult_data = (x_data_fit, y_data_fit_fwd, y_data_fit_back)  # bundling the fitting lines
                    fit_data = (xfit_fwd, xfit_back, yfit_fwd, yfit_back)  # bundling together to plot datapoints used in fits
                    reliability = {"fwd": reliability_fwd, "back": reliability_back, "mean": reliability_mean}

                    return popts, fitresult_data, automatic_determination_parameters, fit_data, reliability, errors
                  # return popt_fwd, popt_back, popt_tot, avg, x_data_fit, y_data_fit_fwd, y_data_fit_back, y_smooth, fd_min_val, sd_min_val, xfit_fwd, xfit_back, yfit_fwd, yfit_back, reliability_fwd, reliability_back, reliability_mean, errors

                except: continue


    def mobility_sat_Vgdependent_plot(self):
        x_data = self.saturation_Vg
        y_data = self.saturation_Id
        Z = self.channel_width
        L = self.channel_length
        C_ox = self.capacitance_oxide
        #try:
        mu_eff = np.gradient(np.sqrt(np.abs(y_data)), x_data)**2 * 2 * L / (Z * C_ox)
        #except RuntimeWarning:
        #    print("caught")
        #mu_eff = np.gradient(np.sqrt(np.abs(y_data)), x_data[1]-x_data[0])**2 * 2 * L / (Z * C_ox)

        #mu_eff = first_derivative(np.sqrt(np.abs(y_data)), gauss_s=self.smoothing)**2 * 2*L/(Z*C_ox)
        l_ = len(x_data) // 2
        #print(len(x_data),len(mu_eff),l_)
        x_fwd, x_back = x_data[:l_-1], x_data[l_+1:]
        mu_eff_fwd, mu_eff_back = mu_eff[:l_-1], mu_eff[l_+1:]
        #print(len(x_fwd),len(mu_eff_fwd),len(x_back),len(mu_eff_back))

        return x_fwd, x_back, mu_eff_fwd, mu_eff_back


    def mobility_lin_Vgdependent_plot(self):
        x_data = self.linear_Vg
        y_data = self.linear_Id
        V_d = self.linear_source_drain_voltage
        Z = self.channel_width
        L = self.channel_length
        C_ox = self.capacitance_oxide

        #mu_eff = first_derivative(y_data, gauss_s=self.smoothing) * L/(Z*C_ox*V_d)
        #mu_eff = np.gradient(y_data, x_data[1] - x_data[0]) * L / (Z * C_ox * V_d)
        mu_eff = np.gradient(y_data, x_data) * L / (Z * C_ox * V_d)

        l_ = len(x_data)//2
        x_fwd, x_back = x_data[:l_-1], x_data[l_+1:]
        mu_eff_fwd, mu_eff_back = mu_eff[:l_-1], mu_eff[l_+1:]

        return x_fwd, x_back, mu_eff_fwd, mu_eff_back


class InverterAnalysis():
    def __init__(self, carrier_type='p', filename=None, filetype=None,
                 smooth_factor=None, V_DD=None,
                 manualFitRange=False,
                 fitRestriction=None,  # could be "fwd", "back" or "mean" otherwise
                 column_settings={"names": None, "skiprows": None},
                 ):
        self.filename = filename
        self.filetype = filetype

        self.carrier_type = carrier_type
        self.supply_voltage = V_DD
        self.smoothing = smooth_factor
        self.manualFitRange = manualFitRange
        self.f = -1 if self.carrier_type == 'p' else 1 if self.carrier_type == 'n' else None
        self.column_names = i.split(";") if ((i := column_settings["names"]) is not None) else None
        self.skiprows = column_settings["skiprows"]


        if self.filetype == "Custom":
            transfer_column_names = self.column_names
            skiprows = self.skiprows
            print("Use custom data preset on your own risk. Errors in syntax, column names etc can happen!!")

        elif self.filetype == "SweepMe!": # this needs to be changed to allow for data including resistance calculation
            transfer_column_names = ['time_elapsed', 'timestamp'  ,
                                     'gnd Voltage' , 'gnd Current',
                                     'dd Voltage'  , 'dd Current' ,
                                     'out Voltage' , 'out Current',
                                     'in Voltage'  , 'in Current' ,]
            skiprows = 3

        else:
            print_exc()
            return False


        try:
            # read data from data file. CAREFUL! this part is crucial, and depends on the column names.
            # Changes to column structure might break this!
            self.inv_transfer_data = pd.read_table(self.filename,
                                                      skiprows=skiprows,
                                                      names=transfer_column_names,
                                                      header=None, index_col=None)
            self.V_in = np.array(self.inv_transfer_data['in Voltage'])
            self.V_out_raw = self.inv_transfer_data['out Voltage']
            self.V_out = smoothing(self.V_out_raw,gauss_s=self.smoothing) if (self.smoothing is not None) else np.array(self.V_out_raw)

            # try and read Vdd if not given manually
            if self.supply_voltage is None: self.supply_voltage = np.round(self.inv_transfer_data['dd Voltage'].mean(),2)

            # automatic check if bwd scan is active (if first and last datapoint coincide)
            self.bwd_available = (np.abs(self.V_in[0]-self.V_in[-1])<5e-3)
            if self.bwd_available == False: print("Backwards sweep seemingly not included. Please check data. If nothing is wrong there, maybe the resistance column is expected/given and the code expects it or not...please check that.")

        except:
            print("Something went wrong during reading of the datafile for Inverter Analysis.")


    def get_characteristics(self):
        try:
            if (len(self.V_in) < 3) or (len(self.V_out) < 3):
                self.dV_fwd, self.dV_bwd = None, None
                return False

            halflength_ = len(self.V_in) // 2
            x_fwd = self.V_in [:halflength_] if self.bwd_available else self.V_in
            y_fwd = self.V_out[:halflength_] if self.bwd_available else self.V_out
            x_bwd = self.V_in [halflength_:] if self.bwd_available else None
            y_bwd = self.V_out[halflength_:] if self.bwd_available else None
            self.V_in_fwd, self.V_out_fwd = x_fwd, y_fwd
            if self.bwd_available:
                self.V_in_bwd, self.V_out_bwd = x_bwd, y_bwd


            # 22.04.2022 change: np.gradient uses centered gradient, but one-sided gradient is the correct approach for "perfect" inverters
            # otherwise (for one point with high gain only) the gain would be cut in half (for ideal inverter)
            def one_side_gradient(y, x):
                l = len(x)
                dydx = np.abs( np.array([(y[i] - y[i + 1]) / (x[i] - x[i + 1]) for i in range(l - 1)]) )
                dydx[dydx == np.inf] = np.nan  # np.max() will treat inf as highest value - replace with nan
                return np.append(dydx, np.nan)  # need to add one value to keep shape of arrays

            #self.dV_fwd = np.abs(np.gradient(y_fwd, x_fwd)) # no condition needed because x_fwd is whole range otherwise
            #self.dV_bwd = np.abs(np.gradient(y_bwd, x_bwd)) if self.bwd_available else None
            self.dV_fwd = one_side_gradient(y_fwd,x_fwd)
            self.dV_bwd = one_side_gradient(y_bwd,x_bwd) if self.bwd_available else None

            trip_point_index_fwd = np.nanargmax(self.dV_fwd)
            trip_point_fwd = (x_fwd[trip_point_index_fwd], y_fwd[trip_point_index_fwd])
            gain_fwd = self.dV_fwd[trip_point_index_fwd]
            # use here and in the following unity gain calculation all but the 5 edge points, since it was recognized
            # as unity gain and messed up the noise margin quite often. not sure if this is the right approach, but at least it works better
            # in case there are no 5 data points before unity gain, trip point will not be calculated
            if (len(self.dV_fwd[5:trip_point_index_fwd]) != 0) and (len(self.dV_fwd[trip_point_index_fwd:-5]) != 0):
                u1 = np.abs(self.dV_fwd[5:trip_point_index_fwd] - 1).argmin() + 5

                # addition needed to correctly address the data array after
                # otherwise the array[tp:] has index starting from 0 again, resulting in wrong indexing
                u2 = np.abs(self.dV_fwd[trip_point_index_fwd:-5] - 1).argmin() + trip_point_index_fwd + 5
                unity_gain_point_fwd_before = (x_fwd[u1], y_fwd[u1])
                unity_gain_point_fwd_after  = (x_fwd[u2], y_fwd[u2])
            else: unity_gain_point_fwd_before = (np.nan,np.nan); unity_gain_point_fwd_after = (np.nan,np.nan)

            if self.bwd_available:
                trip_point_index_bwd = np.nanargmax(self.dV_bwd)
                trip_point_bwd = (x_bwd[trip_point_index_bwd], y_bwd[trip_point_index_bwd])
                gain_bwd = self.dV_bwd[trip_point_index_bwd]
                if (len(self.dV_bwd[5:trip_point_index_bwd])!=0) and (len(self.dV_bwd[trip_point_index_bwd:-5])!=0):
                    u3 = np.abs(self.dV_bwd[5:trip_point_index_bwd] - 1).argmin() + 5
                    u4 = np.abs(self.dV_bwd[trip_point_index_bwd:-5] - 1).argmin() + trip_point_index_bwd + 5
                    unity_gain_point_bwd_before = (x_bwd[u3], y_bwd[u3])
                    unity_gain_point_bwd_after  = (x_bwd[u4], y_bwd[u4])
                else:
                    unity_gain_point_bwd_before = (np.nan, np.nan); unity_gain_point_bwd_after = (np.nan,np.nan)

            else:
                trip_point_bwd, unity_gain_point_bwd_before, unity_gain_point_bwd_after, gain_bwd = np.nan, np.nan, np.nan, np.nan

            # before and after refer to the trip point. in each fwd+bwd sweep there are 4 points to get the noise margin from
            # THIS ANALYSIS OF BEFORE/AFTER IS FLAWED UNTIL NOW- WHAT HAPPENS FOR TRIP POINT NOT AT V_DD/2???????
            """noise_margin_fwd_before      = self.supply_voltage - unity_gain_point_fwd_before[0]
            noise_feedthrough_fwd_before = self.supply_voltage - unity_gain_point_fwd_before[1]
            noise_margin_fwd_after       = self.supply_voltage - unity_gain_point_fwd_after[0]
            noise_feedthrough_fwd_after  = self.supply_voltage - unity_gain_point_fwd_after[1]
    
            noise_margin_bwd_before      = self.supply_voltage - unity_gain_point_bwd_before[0]
            noise_feedthrough_bwd_before = self.supply_voltage - unity_gain_point_bwd_before[1]
            noise_margin_bwd_after       = self.supply_voltage - unity_gain_point_bwd_after[0]
            noise_feedthrough_bwd_after  = self.supply_voltage - unity_gain_point_bwd_after[1]
        
            results = {"fwd":{"noise_margin":{"before":noise_margin_fwd_before, "after":noise_margin_fwd_after},
                           "noise_feedthrough":{"before":noise_feedthrough_fwd_before,"after":noise_feedthrough_fwd_after},
                           "plotdata":{"before":None,"after":None}},
                    "bwd":{"noise_margin":{"before":noise_margin_fwd_before, "after":noise_margin_fwd_after},
                           "noise_feedthrough":{"before":noise_feedthrough_fwd_before,"after":noise_feedthrough_fwd_after},
                           "plotdata":{"before":None,"after":None}}
                    }
            """


            nm_low_fwd  = unity_gain_point_fwd_before[0] - unity_gain_point_fwd_after[1]
            nm_high_fwd = unity_gain_point_fwd_before[1] - unity_gain_point_fwd_after[0]
            nm_eff_fwd = min(nm_low_fwd,nm_high_fwd)
            nm_eff_fwd_perc = nm_eff_fwd/(1/2*self.supply_voltage)

            nm_low_bwd = unity_gain_point_bwd_after[0] - unity_gain_point_bwd_before[1]
            nm_high_bwd = unity_gain_point_bwd_after[1] - unity_gain_point_bwd_before[0]
            nm_eff_bwd = min(nm_low_bwd, nm_high_bwd)
            nm_eff_bwd_perc = nm_eff_bwd / (1 / 2 * self.supply_voltage)

            results = {"trip_point":{"fwd":trip_point_fwd,"bwd":trip_point_bwd},
                       "nm_eff_fwd":(nm_eff_fwd,nm_eff_fwd_perc),
                       "nm_eff_bwd":(nm_eff_bwd,nm_eff_bwd_perc),
                       "unity_gain_points":{
                                            "fwd":(unity_gain_point_fwd_before,unity_gain_point_fwd_after),
                                            "bwd":(unity_gain_point_bwd_before,unity_gain_point_bwd_after)},
                       "max_gain":{"fwd":gain_fwd,"bwd":gain_bwd}
                       }
            return results

        except:
            print_exc()


class SparameterAnalysis():
    def __init__(self,
                 W=100,
                 L=100,
                 C_ox=0.65,
                 carrier_type='p',
                 filename=None,
                 smoothing=.25,
                 V_DS=-.1,
                 fTfit=True,
                 fTbounds=[1e6,1e7],
                 column_settings={"names": None, "skiprows": None},
                 ):
        self.filename = filename

        self.carrier_type = carrier_type
        self.f = -1 if self.carrier_type == 'p' else 1 if self.carrier_type == 'n' else None
        self.channel_width = W * 1e-6
        self.channel_length = L * 1e-6
        self.capacitance_oxide = C_ox * 1e-6
        self.linear_source_drain_voltage = V_DS
        self.smoothing = smoothing
        self.fTfit_bool = fTfit
        self.fTbounds = fTbounds
        self.column_names = i.split(";") if ((i := column_settings["names"]) is not None) else None
        self.skiprows = column_settings["skiprows"]

        # read the data and parse it accordingly
        self.datatype = "AnritsuVNA" if self.filename.endswith(".s2p") else "unknown"
        if self.datatype == "AnritsuVNA":
            self.data_raw = pd.read_table(self.filename, skiprows=8, sep="\s+",
                               names=["f", "S11r", "S11i", "S21r", "S21i", "S12r", "S12i", "S22r", "S22i"])
            self.data_raw["f"] = 1e9 * self.data_raw["f"]
            self.data_raw["S11"] = self.data_raw["S11r"] + 1j * self.data_raw["S11i"]
            self.data_raw["S21"] = self.data_raw["S21r"] + 1j * self.data_raw["S21i"]
            self.data_raw["S12"] = self.data_raw["S12r"] + 1j * self.data_raw["S12i"]
            self.data_raw["S22"] = self.data_raw["S22r"] + 1j * self.data_raw["S22i"]
            self.data_raw["S11abs_dB"] = 20 * np.log10(np.abs(self.data_raw["S11"]))
            self.data_raw["S21abs_dB"] = 20 * np.log10(np.abs(self.data_raw["S21"]))
            self.data_raw["S12abs_dB"] = 20 * np.log10(np.abs(self.data_raw["S12"]))
            self.data_raw["S22abs_dB"] = 20 * np.log10(np.abs(self.data_raw["S22"]))
            self.data_raw["S11phase_deg"] = np.angle(self.data_raw["S11"], deg=True)
            self.data_raw["S21phase_deg"] = np.angle(self.data_raw["S21"], deg=True)
            self.data_raw["S12phase_deg"] = np.angle(self.data_raw["S12"], deg=True)
            self.data_raw["S22phase_deg"] = np.angle(self.data_raw["S22"], deg=True)

            self.data = self.data_raw[["f", "S11", "S21", "S12", "S22"]]

        else:
            try:
                self.data_raw = pd.read_excel(self.filename, engine='openpyxl', skiprows=8,
                                   names=["f", "S11db", "S11deg", "S12db", "S12deg", "S21db", "S21deg", "S22db",
                                          "S22deg"], header=None)

                self.data_raw.loc[:,"S11"] = 10 ** ((self.data_raw.loc[:,"S11db"]) / 20) * np.cos(np.deg2rad(self.data_raw.loc[:,"S11deg"])) + 1j * 10 ** (
                            (self.data_raw.loc[:,"S11db"]) / 20) * np.sin(np.deg2rad(self.data_raw.loc[:,"S11deg"]))
                self.data_raw.loc[:,"S12"] = 10 ** ((self.data_raw.loc[:,"S12db"]) / 20) * np.cos(np.deg2rad(self.data_raw.loc[:,"S12deg"])) + 1j * 10 ** (
                            (self.data_raw.loc[:,"S12db"]) / 20) * np.sin(np.deg2rad(self.data_raw.loc[:,"S12deg"]))
                self.data_raw.loc[:,"S21"] = 10 ** ((self.data_raw.loc[:,"S21db"]) / 20) * np.cos(np.deg2rad(self.data_raw.loc[:,"S21deg"])) + 1j * 10 ** (
                            (self.data_raw.loc[:,"S21db"]) / 20) * np.sin(np.deg2rad(self.data_raw.loc[:,"S21deg"]))
                self.data_raw.loc[:,"S22"] = 10 ** ((self.data_raw.loc[:,"S22db"]) / 20) * np.cos(np.deg2rad(self.data_raw.loc[:,"S22deg"])) + 1j * 10 ** (
                            (self.data_raw.loc[:,"S22db"]) / 20) * np.sin(np.deg2rad(self.data_raw.loc[:,"S22deg"]))
                self.data = self.data_raw[["f", "S11", "S12", "S21", "S22"]]

            except:
                print("Couldn't read data file. Please check if the datafile is the correct one and if pandas got fed\
                the correct instructions for the datafile. Note that for reading excel files pandas needs the openpyxl module!")

        h21_ = self.calculate_h21()
        self.data_raw.loc[:,"h21"], self.data.loc[:,"h21"] = h21_, h21_
        self.data_raw.loc[:,"h21_dB"], self.data.loc[:,"h21_dB"] = 20*np.log10(np.abs(h21_)), 20*np.log10(np.abs(h21_))

    def calculate_h21(self):

        S11, S12, S21, S22 = self.data.loc[:,"S11"], self.data.loc[:,"S12"], self.data.loc[:,"S21"], self.data.loc[:,"S22"]
        h21 = np.abs( -2*S21 / (    (1-S11)*(1+S22)  + S21*S12   ) )
        return h21

    # the transit frequency is determined by the intercept of a linear fit of the linear part of h21(f) with y=1 in a semilogx plot
    # to accomplish that the data is converted to logscale and dB, respectively, before doing the fit
    def calculate_fT(self):
        if self.fTfit_bool == False: return None # user can choose not to fit fT

        start, stop = self.fTbounds
        x,y = self.data["f"],self.data["h21"]
        xfit = self.data[(self.data["f"]>start)&(self.data["f"]<stop)]["f"]
        yfit = self.data[(self.data["f"]>start)&(self.data["f"]<stop)]["h21"]
        x_log, y_dB, xfit_log, yfit_dB = np.log10(x), 20*np.log10(y), np.log10(xfit), 20*np.log10(yfit)
        def linear_regression(x, a, b):
            return a * x + b
        try:
            popt, pcov = curve_fit(linear_regression, xfit_log, yfit_dB, check_finite=True)
            a, b = popt
            da, db = np.sqrt(np.diag(pcov))
            intercept = (1-b)/a    # where the fitting curve equals y=1
            fT = 10**intercept     # fT in Hz since fit was done for log10(x)
            dfT = np.abs(-1/a)*db + np.abs( -(1-b)/(a**2) )*da  # error propagation

            results = {"xdata":x,"ydata":y,"xfitdata":xfit,"yfitdata":yfit,"fT":fT,"fitslope":a,
                       "fitplot_ydata":linear_regression(np.log10(x),*popt), # needs to be calculated as line so that it works in the GUI with semilogx
                       "errors":{"fT":dfT,"slope":da}}
            return results

        except:
            print("fT fit was not successful, maybe the range of frequency to fit was awry. Please check.")
            return None



class Arrhenius():
    def __init__(self,
                 c_ox=None,
                 carrier_type='p',
                 filenames=None,
                 filetype=None,
                 fd=.75,
                 sd=.4,
                 smoothing=.25,
                 V_DS=None,
                 manualFitRange={'lin': False,
                                 'sat': False,
                                 'ssw': False},
                 fitRestriction=None,  # could be "fwd" or "back" otherwise
                 column_settings={"names": None, "skiprows": None},
                 L_correct=None
                 ):
        # input of Z,L,C_ox in µm and µF/cm², respectively. fd and sd are thresholds for automatic data fit

        self.filenames = filenames
        self.filetype = filetype

        self.carrier_type = carrier_type
        self.capacitance_oxide = c_ox
        self.first_deriv_limit = fd
        self.second_deriv_limit = sd
        self.smoothing = smoothing
        self.VDS = V_DS
        self.manualFitRanges = manualFitRange
        self.fitRestriction = fitRestriction  # this is not used for now. will be used later on to make it possible to use data files with only fwd or back data.
        self.f = -1 if self.carrier_type == 'p' else 1 if self.carrier_type == 'n' else None
        self.column_names = i.split(";") if ((i := column_settings["names"]) is not None) else None
        self.skiprows = column_settings["skiprows"]
        self.measurements = {}
        self.L_correct = L_correct if (L_correct is not None) else None

        for i in self.filenames:
            try:
                # this try/except is only to read the sample name, to be used as plot label in the RcW(V-Vth) plot.
                # if it does not succeed, everything else can be used but the label will default to "data" (see main script)
                try:
                    # this pattern refers to the goettingen files that have been renamed to TW convention
                    #p_goett = r".*[\/\\](?P<N>[A-Za-z\d]+).*W(?P<W>[\d.]+)[_#]*L(?P<L>[\d.]+)[_#].*G(?P<G>[\d]+)[_\w]*T(?P<T>[\d]+).*"
                    if self.filetype=="Goettingen":
                        p_goett = r".*[\/\\](?P<N>[A-Za-z\d]+)_W(?P<W>[\d.]+)[_#]*L(?P<L>[\d.]+)_[_\w]*G(?P<G>[\d]+)_T(?P<T>[\d]+).*"
                        m = re.match(p_goett, i)
                        n, t, w, l, g = m.group(("N")), int(m.group(("T"))), int(m.group(("W"))), float(m.group(("L"))), int(m.group("G"))

                    elif self.filetype=="Marburg":
                        p_marburg = r".*[\/\\](?P<N>[A-Za-z\d]+)_W(?P<W>[\d.]+)[_#]*L(?P<L>[\d.]+).*_T(?P<T>[\d]+).*"
                        m = re.match(p_marburg, i)
                        n, t, w, l = m.group(("N")), float(m.group(("T"))), float(m.group(("W"))), float(m.group(("L")))
                except:
                    print_exc()
                    print("The required info (SampleName,ChannelWidth,ChannelLength,Temperature) could not be extracted from filename. Please check the regex pattern!")
                    continue



                # assuming sweepme files or goettingen files
                # the real VDS will be determined from the file
                if self.VDS is None:
                    try:
                        c = pd.read_table(i, nrows=5).columns
                        file_ext = i.split('.')[-1]

                        if self.filetype == "Custom":
                            transfer_column_names = self.column_names
                            skiprows = self.skiprows
                            print("Use custom data preset on your own risk. Errors in syntax, column names etc can happen!!")

                        elif self.filetype == "SweepMe!":
                            transfer_column_names = ['time_elapsed', 'timestamp', 'lin_source Voltage', 'lin_source Current',
                                        'lin_drain Voltage', 'lin_drain Current', 'lin_gate Voltage', 'lin_gate Current']
                            skiprows = 3

                        elif self.filetype == "Goettingen":
                            transfer_column_names = ['lin_drain Voltage', 'lin_gate Voltage', 'lin_drain Current',
                                        'lin_gate Current', 'time_elapsed', 'empty']
                            skiprows = 4

                        elif self.filetype == "Marburg":
                            transfer_column_names = {
                                'lin': ['time_elapsed', 'timestamp', 'lin_drain Voltage', 'lin_drain Current', 'lin_drain Resistance', 'lin_gate Voltage', 'lin_gate Current', 'lin_gate Resistance'],
                                'sat': ['time_elapsed', 'timestamp', 'sat_drain Voltage', 'sat_drain Resistance','sat_drain Current', 'sat_gate Voltage', 'sat_gate Current', 'sat_gate Resistance']} if any(['Resistance' in i for i in c]) else {
                                'lin': ['time_elapsed', 'timestamp', 'lin_drain Voltage', 'lin_drain Current', 'lin_gate Voltage', 'lin_gate Current'],
                                'sat': ['time_elapsed', 'timestamp', 'sat_drain Voltage', 'sat_drain Current', 'sat_gate Voltage', 'sat_gate Current']}
                            skiprows = 3
                            sep = "\t"


                        elif self.filetype == "LabVIEW":
                            transfer_column_names = ['lin_gate Voltage', 'time', 'lin_drain Current', 'lin_gate Current',
                            'abs_lin_drain_current', 'abs_lin_gate_current', 'sqrt_lin_drain_current', '1stderiv_lin_drain_current',
                            '2ndderiv_lin_drain_current']
                            skiprows = 2

                        elif self.filetype == "ParameterAnalyzer":
                            transfer_column_names = ['idx', 'lin_drain Voltage', 'lin_gate Voltage', 'lin_drain Current', 'lin_gate Current']
                            skiprows = 5

                        else: raise TypeError



                        if self.filetype == "Marburg":
                            d = pd.read_table(i)
                            self.VDS = float(d.filter(regex='V').filter(regex='(drain)|(DS)|(_D)').iloc[3:].astype(
                                'float').mean().iloc[0])

                        else:
                            d = pd.read_table(i, skiprows=skiprows,
                                              names=transfer_column_names, header=None, index_col=None)
                            self.VDS = np.round(float(d['lin_drain Voltage'].mean()), 3)

                        print(f"VDS for use in Arrhenius analysis was determined to be {self.VDS} V")

                    except:
                        print_exc()
                        print("V_DS was not set and could not be determined from file name. Please set V_DS.")
                        pass

                if t not in self.measurements.keys(): self.measurements[t] = {"files":[]}
                self.measurements[t]["files"].append(i)
            except:
                print_exc()


    def analyze_temperatureDependent_TLM(self):
        # arrays of data that is to be plotted in the GUI
        ts, terrs, rcws, mu0s, rcwerrs, mu0errs, TLMfitdata = [], [], [], [], [], [], {}

        # for each available temperature there should be one TLM
        for t in self.measurements:
            files_for_single_temp_tlm = self.measurements[t]["files"]
            try:
                print(f"Analyzing T={int(t):03d} K ...")
                tlm = TLM_Analysis(
                self.capacitance_oxide,
                filenames=files_for_single_temp_tlm,filetype=self.filetype,carrier_type=self.carrier_type,smoothing=self.smoothing,
                V_DS=self.VDS,fd=self.first_deriv_limit,sd=self.second_deriv_limit,manualFitRange=self.manualFitRanges,
                fitRestriction=self.fitRestriction,L_correct=self.L_correct)
            except:
                print_exc()

            o, r, err, bestfitdata, allRWs, l_0, Rc0W, mu0, mu0err, rs_sheet, rs_sheet_err, all_Vths, all_SSws = tlm.contactresistance()

            #transferdata = tlm.get_transfer_curves()

            self.measurements[t]["RcW"] = 1e2*np.mean(np.array(r)[-4:-1])   # in Ohm*cm
            self.measurements[t]["RcWerr"] = 1e2*np.mean(np.array(err)[-4:-1])   # in Ohm*cm
            self.measurements[t]["mu0"] = np.mean(np.array(self.f * mu0)[-4:-1]) # in cm2/Vs
            self.measurements[t]["mu0err"] = np.mean(np.array(self.f * mu0err)[-4:-1]) # in cm2/Vs


            if t not in ts:
                ts.append(t)
                terrs.append(5) # temperature uncertainty taken as 5K
                rcws.append(self.measurements[t]["RcW"])
                rcwerrs.append(self.measurements[t]["RcWerr"])
                mu0s.append(self.measurements[t]["mu0"])
                mu0errs.append(self.measurements[t]["mu0err"])


        ts, rcws, mu0s = np.array(ts), np.array(rcws), np.array(mu0s)
        terrs, rcwerrs, mu0errs = np.array(terrs), np.array(rcwerrs), np.array(mu0errs)


        # calculate the energy barrier (see Fig. 5.14 in James Borcherts thesis)
        def exp(T,c,E):
            k = 8.6173e-2 # boltzmann constant in meV/K
            return c * np.exp(-E/(k*T))

        popt, pcov = curve_fit(exp, ts, mu0s)

        xfit = np.linspace(ts.min(),ts.max(),1000)
        yfit = exp(xfit,*popt)
        fiterror = np.sqrt(np.diag(pcov))


        return self.measurements, (ts, terrs), (rcws,rcwerrs), (mu0s,mu0errs), (xfit, yfit, popt ,fiterror)

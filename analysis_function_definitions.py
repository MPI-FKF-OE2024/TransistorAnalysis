#### should d be insulator thickness or depletion width?!?!
import numpy as np

def mobility_lin(V_g, V_d, Z, L, C_ox, mu_eff, V_th):
    """
    fit function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.306 (Eq. 24)
    Z,L are channel width,length respectively
    C_ox is the gate oxide capacitance in µF/cm^2
    q is elementary charge in C
    mu_eff is the effective mobility in cm^2/Vs
    V_th is the threshold voltage of the transistor
    """
    return Z / L * mu_eff * C_ox * (V_g - V_th - V_d / 2) * V_d


def mobility_sat_simplified(V_g, mu_eff, V_th, Z, L, C_ox=0.5):
    """
    fit function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.306 (Eq. 27)
    Z,L are channel width,length respectively
    C_ox is the gate oxide capacitance in µF/cm^2
    mu_eff is the effective mobility in cm^2/Vs
    V_th is the threshold voltage of the transistor
    """
    M = 1  # for most cases -> research more about the origin

    return Z / (2 * M * L) * mu_eff * C_ox * (V_g - V_th)**2


def gaussian(x, s=.1, mu=0):
    return 1 / (np.sqrt(2 * np.pi) * s) * np.exp(-(x - mu)**2 / (2 * s**2))


def gaussian_1stderiv(x, s=.1, mu=0):
    return -((x - mu) * np.exp(-(x - mu)**2 /
                               (2 * s**2))) / (np.sqrt(2 * np.pi) * s**3)


def gaussian_2ndderiv(x, s=.1, mu=0):
    return (((x - mu)**2 * np.exp(-(x - mu)**2 / (2 * s**2))) / s**4 -
            np.exp(-(x - mu)**2 /
                   (2 * s**2)) / s**2) / (np.sqrt(2 * np.pi) * s)


def smoothing(array, gauss_s=.25,lim=5,pts=59):
    #pts=len(array)//3
    x = np.linspace(-lim, lim, pts)

    # calculate first order deriv.
    sm = gaussian(x, s=gauss_s)
    y_conv = np.convolve(array, sm/sm.sum(), mode="same") # division by sm.sum() needed to normalize the gaussian. not needed for the derivatives for some reason since the integral over them vanishes?
    return y_conv

def first_derivative(array, gauss_s=.25, lim=5,pts=59):
    #pts=len(array)//3
    """
    due to the convolution theorem, d/dx (f *(conv) g) = (d/dx f) *(conv) g
    the derivative of a smoothed (by convolution) dataset is therefore equivalent to the convolution with
    the derived convolution kernel. the relation of lim and pts defines the numerical "sharpness" (how well the
    gaussian is defined) and thus influences the convoluted data. the initial values were found a good compromise
    between smoothening the data and including too much noise in the application for identification of linear regimes
    """
    x = np.linspace(-lim, lim, pts)

    # calculate first order deriv.
    sm = gaussian_1stderiv(x, s=gauss_s)
    y_conv = np.convolve(array, sm, mode="same")
    return y_conv


def second_derivative(array, gauss_s=.25, lim=5,pts=59):
    #pts=len(array)//3
    """
    due to the convolution theorem, d/dx (f *(conv) g) = (d/dx f) *(conv) g
    the derivative of a smoothed (by convolution) dataset is therefore equivalent to the convolution with
    the derived convolution kernel. the relation of lim and pts defines the numerical "sharpness" (how well the
    gaussian is defined) and thus influences the convoluted data. the initial values were found a good compromise
    between smoothening the data and including too much noise in the application for identification of linear regimes
    """
    x = np.linspace(-lim, lim, pts)

    # calculate second order deriv.
    sm = gaussian_2ndderiv(x, s=gauss_s)
    y_conv = np.convolve(array, sm/sm.sum(), mode="same")
    return y_conv



def mobility_sat(V_g, mu_eff, V_th, C_ox = 0.5, N_A = 1, q = 1.602e-19, eps_s = 3, ptype=True):
    """
    fit function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.306 (Eq. 27)
    C_ox is the gate oxide capacitance in µF/cm^2
    N_A is the acceptor impurity concentration in XXX (which unit?)
    q is elementary charge in C
    eps_s is the semiconductor permitivitty (unitless)
    mu_eff is the effective mobility in cm^2/Vs
    V_th is the threshold voltage of the transistor
    """
    K = np.sqrt(eps_s*q*N_A) / C_ox
    M = 1 + K/(2*psi_b)
    M = 1 # for most cases -> research more about the origin

    if ptype == True: factor = -1
    elif ptype == False: factor = 1

    return factor * Z/(2*M*L) * mu_eff*(V_g-V_th)**2


def current_density_fowler_nordheim_tunneling(V, const, d, m_eff, phi_b, hbar=6.636e-34, q = 1.602e-19):
    """
    function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.227
    const is a constant because in the textbook shows only a proportionality
    m_eff is the effective charge carrier mass in kg
    q is elementary charge in C
    hbar is planck quantum in J*s
    phi_b is the barrier height in eV
    E is electric field in the insulator (V/nm) for voltage V over insulator thickness d
    """
    E = V/d
    return const * E**2 * np.exp( (-4*np.sqrt(2*m_eff)*(q*phi_b)**(3/2)) / (3*q*hbar*E))

def current_density_direct_tunneling(V, const, d, m_eff, phi_b, hbar=6.636e-34, q = 1.602e-19):
    """
    function taken from DOI:10.1002/adfm.201904576
    const is a constant because in the textbook shows only a proportionality
    m_eff is the effective charge carrier mass in kg
    q is elementary charge in C
    hbar is planck quantum in J*s
    phi_b is the barrier height in eV
    d is the insulator thickness in m
    """
    return const * E**2 * np.exp( (-2*d*np.sqrt(2*m_eff*q*phi_b)) / hbar )

def current_density_thermionic_emission(V, m_eff, T, phi_b, eps_i, d, q = 1.602e-19, k = 8.617e-5, h = 4.136e-15):
    """
    function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.227
    m_eff is the charge carrier effective mass in kg
    T is environment temperature in K
    phi_b is the barrier height in eV
    k is the Boltzmann constant in eV/K
    q is the elementary charge in C
    h is the Planck quantum (not reduced) in eV*s
    eps_i is the insulator permitivitty
    E is electric field in the insulator (V/nm) for voltage V over insulator thickness d
    """
    E = V/d
    A = 4*np.pi*q*k**2/h**3 * m_eff
    return A * T**2 * np.exp(- (q*(phi_b - np.sqrt(q*E/(4*np.pi*eps_i))) ) / (k*T) )

def current_density_frenkel_poole(V, const, T, phi_b, eps_i, d, q = 1.602e-19, k = 8.617e-5):
    """
    function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.227
    const is a constant because in the textbook shows only a proportionality
    T is environment temperature in K
    phi_b is the barrier height in eV
    k is the Boltzmann constant in eV/K
    q is the elementary charge in C
    eps_i is the insulator permitivitty
    E is electric field in the insulator (V/nm) for voltage V over insulator thickness d
    """
    E = V/d
    return E * np.exp(- (q*(phi_b - np.sqrt(q*E/(np.pi*eps_i))) ) / (k*T) )

def current_density_ohmic(V, const, T, dE_ac, k = 8.617e-5):
    """
    function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.227
    const is a constant because in the textbook shows only a proportionality
    T is environment temperature in K
    dE_ac is the activation energy of electrons in eV
    k is the Boltzmann constant in eV/K
    E is electric field in the insulator (V/nm) for voltage V over insulator thickness d
    """
    E = V/d
    return const * E * np.exp(- dE_ac / (k*T) )

def current_density_ionic_conduction(V, const, T, dE_ai, k = 8.617e-5):
    """
    function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.227
    const is a constant because in the textbook shows only a proportionality
    T is environment temperature in K
    dE_ac is the activation energy of ions in eV
    k is the Boltzmann constant in eV/K
    E is electric field in the insulator (V/nm) for voltage V over insulator thickness d
    """
    E = V/d
    return const * E * np.exp(- dE_ai / (k*T) )

def current_density_SCL(V, mu, eps_i, d):
    """
    function taken from Sze, Ng: Physics of Semiconductor Devices 3rd Edition p.227
    mu is the charge carrier mobility in cm^2/Vs
    d is the insulator thickness in m
    eps_i is the insulator permitivitty
    E is electric field in the insulator (V/nm) for voltage V over insulator thickness d
    """
    return (9 * eps_i * mu * V**2) / (8 * d**3)
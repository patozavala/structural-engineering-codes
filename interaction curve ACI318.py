"""
author : Patricio Zavala Fuenzalida
year   : 2019
"""


import numpy as np
import matplotlib.pylab as plt


class StructuralElement:

    def __init__(self, parameters):
        self.b = parameters['width']
        self.h = parameters['high']
        self.E = parameters['elastic_module']
        self.f_sy = parameters['yield_strength']
        self.eps_cu = parameters['ultimate_deformation_concrete']
        self.fc = parameters['concrete_compressive_stress']
        self.alpha = parameters['alpha']
        self.beta = parameters['beta']
        self.rec = parameters['covering']
        self.d = self.h - self.rec
        self.bars_position = None
        self.steel_area = None
        self.interaction_curve = None
        self.design_curve = None

    def steel_constitutive_relation(self, eps):
        """
        this routine determine the stress for a bar using an elasto-plastic constitutive relation
        :param eps: deformation for an steel bar
        :return:
        """
        eps_sy = self.f_sy / self.E
        if abs(eps) <= eps_sy:
            fs = self.E * eps
        else:
            if eps < 0:
                fs = -self.f_sy
            else:
                fs = self.f_sy
        return fs

    def phi_aci(self, eps):
        """
        this routine gives the value for reduction of resistance factor defined in ACI318-14 code
        :param eps: deformation for an steel bar
        :return:
        """
        eps = abs(eps)
        eps_sy = self.f_sy / self.E
        phi = 0
        if eps <= eps_sy:
            phi = 0.65
        elif eps >= eps_sy and eps <= 0.005:
            phi = 0.65 + 0.25 * (eps - eps_sy) / (0.005 - eps_sy)
        elif eps >= 0.005:
            phi = 0.9
        return phi

    def incorporate_bars(self, bars_per_line, bars_diameter):
        """
        this routine determine the position of each steel bars line in the section assuming uniforming distribution
        :param bars_per_line: (list) number of bars in each line
        :param bars_diameter: (list) diameters for bars in each line
        :return: None
        """
        self.bars_position = np.linspace(- (self.h - 2. * self.rec) / 2, (self.h - 2. * self.rec) / 2,
                                         len(bars_per_line))
        self.steel_area = []
        for i in range(len(bars_per_line)):
            self.steel_area.append(bars_per_line[i] * float(1 / 4) * np.pi * bars_diameter[i] ** 2)

    def get_interaction_curve(self):
        """
        this routine calculate the interaction curve and design curve using the ACI318-14 considerations for the element
        :return: None
        """

        c = np.linspace(1E-8, self.h, 40)
        fs = np.zeros([len(self.bars_position)])
        pn = []
        mn = []
        phi_mn = []
        phi_pn = []
        # pure traction considering non compressive resistance for steel
        Cc = 0
        ycc = 0
        for j in range(len(self.bars_position)):
            eps_s = -0.005
            force_steel = self.steel_constitutive_relation(eps_s)  # stress in lines
            fs[j] = force_steel * self.steel_area[j]  # force in bars line
            phi_design = self.phi_aci(eps_s)
        pn.append((Cc + np.sum(fs)))
        mn.append((Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        phi_pn.append(phi_design * (Cc + np.sum(fs)))
        phi_mn.append(phi_design * (Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        # positive part of the curve
        for i in range(len(c)):
            ycc = (self.h - self.beta * c[i]) / 2  # position of the steel level w/r to neutral axis
            phi = self.eps_cu / c[i]
            # concrete force using the rectangular block
            Cc = self.alpha * self.beta * self.fc * self.b * c[i]
            for j in range(len(self.bars_position)):
                ys_p = self.h / 2 + self.bars_position[j] - (self.d - c[i]) - self.rec
                eps_s = phi * ys_p  # deformation of each bar in line i
                force_steel = self.steel_constitutive_relation(eps_s)  # stress in line i
                fs[j] = force_steel * self.steel_area[j]  # force in line i
                phi_design = self.phi_aci(eps_s)
            pn.append((Cc + np.sum(fs)))
            mn.append((Cc * ycc + np.sum(self.bars_position * fs)) / 100)
            phi_pn.append(phi_design * (Cc + np.sum(fs)))
            phi_mn.append(phi_design * (Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        # pure compression
        Cc = self.alpha * self.fc * self.b * self.h
        ycc = 0
        for j in range(len(self.bars_position)):
            eps_s = self.eps_cu  # deformation of each bar in line i
            force_steel = self.steel_constitutive_relation(eps_s)  # stress in lines
            fs[j] = force_steel * self.steel_area[j]  # force in line i
            phi_design = self.phi_aci(eps_s)
        pn.append((Cc + np.sum(fs)))
        mn.append((Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        phi_pn.append(phi_design * (Cc + np.sum(fs)))
        phi_mn.append(phi_design * (Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        # negative part of the curve
        self.steel_area.reverse()
        c = np.linspace(self.h, 1E-8, 40)
        for i in range(len(c)):
            # concrete force using the rectangular block
            Cc = self.alpha * self.beta * self.fc * self.b * c[i]
            ycc = (self.h - self.beta * c[i]) / 2  # position of the steel level w/r to neutral axis
            phi = self.eps_cu / c[i]
            for j in range(len(self.bars_position)):
                ys_p = self.h / 2 + self.bars_position[j] - (self.d - c[i]) - self.rec
                eps_s = phi * ys_p  # deformation of each bar in line i
                force_steel = self.steel_constitutive_relation(eps_s)  # stress in line i
                fs[j] = force_steel * self.steel_area[j]  # force in line i
                phi_design = self.phi_aci(eps_s)
            pn.append((Cc + np.sum(fs)))
            mn.append(-(Cc * ycc + np.sum(self.bars_position * fs)) / 100)
            phi_pn.append(phi_design * (Cc + np.sum(fs)))
            phi_mn.append(-phi_design * (Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        # pure tension
        Cc = 0
        for j in range(len(self.bars_position)):
            eps_s = -0.005  # deformation of each bar in line i
            force_steel = self.steel_constitutive_relation(eps_s)  # stress in lines
            fs[j] = force_steel * self.steel_area[j]  # force in line i
            phi_design = self.phi_aci(eps_s)
        pn.append((Cc + np.sum(fs)))
        mn.append(-(Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        phi_pn.append(phi_design * (Cc + np.sum(fs)))
        phi_mn.append(-phi_design * (Cc * ycc + np.sum(self.bars_position * fs)) / 100)
        # maximum compressive resistance criteria
        p_max = 0.80 * np.max(pn)
        phip_max = 0.65 * p_max
        for i in range(len(pn)):
            if pn[i] >= p_max:
                pn[i] = p_max
            if phi_pn[i] >= phip_max:
                phi_pn[i] = phip_max
        self.interaction_curve = (mn, pn)
        self.design_curve = (phi_mn, phi_pn)


"""
Execution
"""

parameters = {'width': 80.0,
              'high': 80.0,
              'elastic_module': 2100.0,
              'yield_strength': 4.2,
              'ultimate_deformation_concrete': 0.003,
              'concrete_compressive_stress': 0.250,
              'alpha': 0.85,
              'beta': 0.85,
              'covering': 5.0}

number_of_steel_lines = 4

bars = {'bars_per_line': [4] * number_of_steel_lines,
        'bars_diameter': [2.5] * number_of_steel_lines}
column1 = StructuralElement(parameters=parameters)
column1.incorporate_bars(bars_per_line=bars['bars_per_line'], bars_diameter=bars['bars_diameter'])
column1.get_interaction_curve()

plt.figure()
plt.title('Interaction curve')
plt.xlabel('$M_{n}[tonf - m ]$')
plt.ylabel('$P_{n} [tonf]$')
plt.plot(column1.interaction_curve[0], column1.interaction_curve[1], 'k', label='interaction curve ACI318-14')
plt.plot(column1.design_curve[0], column1.design_curve[1], 'r', label='design curve ACI318-14')
plt.grid()
plt.legend(loc=1)
plt.show()

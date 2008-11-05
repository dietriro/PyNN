# ==============================================================================
# Synapse Dynamics classes for pcsim
# $Id$
# ==============================================================================

from pyNN import common
import pypcsim

synapse_models = [s for s in dir(pypcsim) if 'Synapse' in s]

class SynapseDynamics(common.SynapseDynamics):
    """
    For specifying synapse short-term (faciliation, depression) and long-term
    (STDP) plasticity. To be passed as the `synapse_dynamics` argument to
    `Projection.__init__()` or `connect()`.
    """
    
    def __init__(self, fast=None, slow=None):
        common.SynapseDynamics.__init__(self, fast, slow)

        
class STDPMechanism(common.STDPMechanism):
    """Specification of STDP models."""
    
    def __init__(self, timing_dependence=None, weight_dependence=None,
                 voltage_dependence=None, dendritic_delay_fraction=1.0, model=None):
        # not sure what the situation is with dendritic_delay_fraction in PCSIM
        common.STDPMechanism.__init__(self, timing_dependence, weight_dependence,
                                      voltage_dependence, dendritic_delay_fraction,model)


class TsodyksMarkramMechanism(common.TsodyksMarkramMechanism):
    
    translations = common.build_translations(
        ('U', 'U'),
        ('tau_rec', 'D', 1e-3),
        ('tau_facil', 'F', 1e-3),
        ('u0', 'u0'),  
        ('x0', 'r0' ), # I'm not at all sure this 
        ('y0', 'f0')   # translation is correct
                       # need to look at the source code
    )
    #possible_models = set([s for s in synapse_models if "Dynamic" in s])
    possible_models = set([pypcsim.DynamicStdpSynapse,
                           pypcsim.DynamicStdpCondExpSynapse])
    #native_name = pypcsim.DynamicStdpSynapse
    
    def __init__(self, U=0.5, tau_rec=100.0, tau_facil=0.0, u0=0.0, x0=1.0, y0=0.0):
        common.TsodyksMarkramMechanism.__init__(self, U, tau_rec, tau_facil, u0, x0, y0)
        parameters = dict(locals()) # need the dict to get a copy of locals. When running
        parameters.pop('self')      # through coverage.py, for some reason, the pop() doesn't have any effect
        self.parameters = self.translate(parameters)
        

class AdditiveWeightDependence(common.AdditiveWeightDependence):
    """
    The amplitude of the weight change is fixed for depression (`A_minus`)
    and for potentiation (`A_plus`).
    If the new weight would be less than `w_min` it is set to `w_min`. If it would
    be greater than `w_max` it is set to `w_max`.
    """
    
    translations = common.build_translations(
        ('w_max',     'Wex',  1e-9), # unit conversion
        ('w_min',     'w_min_always_zero_in_PCSIM'),
        ('A_plus',    'Apos', '1e-9*A_plus*w_max', '1e9*Apos/w_max'),  # note that here Apos and Aneg
        ('A_minus',   'Aneg', '-1e-9*A_minus*w_max', '-1e9*Aneg/w_max'), # have the same units as the weight
    )
    possible_models = set([pypcsim.DynamicStdpSynapse,
                           pypcsim.DynamicStdpCondExpSynapse])
    
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01): # units?
        if w_min != 0:
            raise Exception("Non-zero minimum weight is not supported by PCSIM.")
        common.AdditiveWeightDependence.__init__(self, w_min, w_max, A_plus, A_minus)
        parameters = dict(locals())
        parameters.pop('self')
        self.parameters = self.translate(parameters)
        self.parameters['useFroemkeDanSTDP'] = False
        self.parameters['mupos'] = 0.0
        self.parameters['muneg'] = 0.0
        self.parameters.pop('w_min_always_zero_in_PCSIM')
    
    
class MultiplicativeWeightDependence(common.MultiplicativeWeightDependence):
    """
    The amplitude of the weight change depends on the current weight.
    For depression, Dw propto w-w_min
    For potentiation, Dw propto w_max-w
    """
    translations = common.build_translations(
        ('w_max',     'Wex',  1e-9), # unit conversion
        ('w_min',     'w_min_always_zero_in_PCSIM'),
        ('A_plus',    'Apos'),     # here Apos and Aneg
        ('A_minus',   'Aneg', -1), # are dimensionless
    )
    possible_models = set([pypcsim.DynamicStdpSynapse,
                           pypcsim.DynamicStdpCondExpSynapse])
    
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01): # units?
        if w_min != 0:
            raise Exception("Non-zero minimum weight is not supported by PCSIM.")
        common.MultiplicativeWeightDependence.__init__(self, w_min, w_max, A_plus, A_minus)
        parameters = dict(locals())
        parameters.pop('self')
        self.parameters = self.translate(parameters)
        self.parameters['useFroemkeDanSTDP'] = False
        self.parameters['mupos'] = 1.0
        self.parameters['muneg'] = 1.0


class AdditivePotentiationMultiplicativeDepression(common.AdditivePotentiationMultiplicativeDepression):
    """
    The amplitude of the weight change depends on the current weight for
    depression (Dw propto w-w_min) and is fixed for potentiation.
    """
    translations = common.build_translations(
        ('w_max',     'Wex',  1e-9), # unit conversion
        ('w_min',     'w_min_always_zero_in_PCSIM'),
        ('A_plus',    'Apos', 1e-9), # Apos has the same units as the weight
        ('A_minus',   'Aneg', -1),   # Aneg is dimensionless
    )
    possible_models = set([pypcsim.DynamicStdpSynapse,
                           pypcsim.DynamicStdpCondExpSynapse])
    
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01): # units?
        if w_min != 0:
            raise Exception("Non-zero minimum weight is not supported by PCSIM.")
        common.AdditivePotentiationMultiplicativeDepression.__init__(self, w_min, w_max, A_plus, A_minus)
        parameters = dict(locals())
        parameters.pop('self')
        self.parameters = self.translate(parameters)
        self.parameters['useFroemkeDanSTDP'] = False
        self.parameters['mupos'] = 0.0
        self.parameters['muneg'] = 1.0


class GutigWeightDependence(common.GutigWeightDependence):
    """
    The amplitude of the weight change depends on the current weight.
    For depression, Dw propto w-w_min
    For potentiation, Dw propto w_max-w
    """
    translations = common.build_translations(
        ('w_max',     'Wex',  1e-9), # unit conversion
        ('w_min',     'w_min_always_zero_in_PCSIM'),
        ('A_plus',    'Apos'),
        ('A_minus',   'Aneg', -1),
        ('mu_plus',   'mupos'),
        ('mu_minus',  'muneg')
    )
    possible_models = set([pypcsim.DynamicStdpSynapse,
                           pypcsim.DynamicStdpCondExpSynapse])
    
    def __init__(self, w_min=0.0, w_max=1.0, A_plus=0.01, A_minus=0.01, mu_plus=0.5, mu_minus=0.5): # units?
        if w_min != 0:
            raise Exception("Non-zero minimum weight is not supported by PCSIM.")
        common.AdditivePotentiationMultiplicativeDepression.__init__(self, w_min, w_max, A_plus, A_minus)
        parameters = dict(locals())
        parameters.pop('self')
        self.parameters = self.translate(parameters)
        self.parameters['useFroemkeDanSTDP'] = False
        

class SpikePairRule(common.SpikePairRule):
    
    translations = common.build_translations(
        ('tau_plus',  'taupos', 1e-3),
        ('tau_minus', 'tauneg', 1e-3), 
    )
    #possible_models = set([s for s in synapse_models if 'EachPairStdp' in s]) #'stdp_synapse_hom'
    possible_models = set([pypcsim.DynamicStdpSynapse,
                           pypcsim.DynamicStdpCondExpSynapse])
    
    def __init__(self, tau_plus=20.0, tau_minus=20.0):
        common.SpikePairRule.__init__(self, tau_plus, tau_minus)
        parameters = dict(locals())
        parameters.pop('self')
        self.parameters = self.translate(parameters)

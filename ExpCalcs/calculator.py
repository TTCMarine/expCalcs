from .models import MathChannelConfig, RollingMathChannelConfig
from typing import Dict, Optional, Union
from Expedition import Var, ExpeditionDLL
import numpy as np
from abc import ABC, abstractmethod


class Calculator(ABC):
    def __init__(self,
                 expedition: ExpeditionDLL,
                 expression: str,
                 output_var: Var,
                 output_var_user_name: Optional[str] = None,):
        self.expedition = expedition
        self.expression = expression
        self.output_var = output_var
        self.output_var_user_name = output_var_user_name

        self.variables = {}
        self.functions = {'__builtins__': None}

        self.add_default_functions()
        self.add_default_variables()

        if self.output_var_user_name and Var.User0 <= self.output_var <= Var.UserMax:
            self.expedition.set_exp_user_var_name(self.output_var, self.output_var_user_name)

    def add_default_functions(self):
        """
        Add the following Python functions to be used in a mathematical expression:
        """
        self.functions['sin'] = np.sin
        self.functions['cos'] = np.cos
        self.functions['tan'] = np.tan

        self.functions['arcsin'] = np.arcsin
        self.functions['arccos'] = np.arccos
        self.functions['arctan'] = np.arctan

        self.functions['sinh'] = np.sinh
        self.functions['cosh'] = np.cosh
        self.functions['tanh'] = np.tanh

        self.functions['arcsinh'] = np.arcsinh
        self.functions['arccosh'] = np.arccosh
        self.functions['arctanh'] = np.arctanh

        self.functions['hypot'] = np.hypot
        self.functions['arctan2'] = np.arctan2

        self.functions['degrees'] = np.degrees
        self.functions['radians'] = np.radians
        self.functions['unwrap'] = np.unwrap

        self.functions['abs'] = np.abs
        self.functions['sqrt'] = np.sqrt
        self.functions['clip'] = np.clip
        self.functions['exp'] = np.exp
        self.functions['log'] = np.log
        self.functions['log2'] = np.log2
        self.functions['log10'] = np.log10

        self.functions['ceil'] = np.ceil
        self.functions['floor'] = np.floor
        self.functions['trunc'] = np.trunc
        self.functions['round'] = np.round
        self.functions['rint'] = np.rint
        self.functions['fix'] = np.fix

        self.functions['mean'] = np.mean
        self.functions['median'] = np.median
        self.functions['average'] = np.average
        self.functions['std'] = np.std
        self.functions['var'] = np.var
        self.functions['sum'] = np.sum
        self.functions['prod'] = np.prod
        self.functions['cumsum'] = np.cumsum
        self.functions['cumprod'] = np.cumprod
        self.functions['diff'] = np.diff
        self.functions['gradient'] = np.gradient
        self.functions['cross'] = np.cross
        self.functions['trapz'] = np.trapz
        self.functions['expm1'] = np.expm1
        self.functions['log1p'] = np.log1p
        self.functions['sign'] = np.sign
        self.functions['heaviside'] = np.heaviside

    def add_default_variables(self):
        """
        Add the following Python variables to be used in a mathematical expression:
        """
        self.variables['pi'] = np.pi
        self.variables['e'] = np.e

    @abstractmethod
    def calculate(self) -> float:
        raise NotImplementedError("calculate method must be implemented in a subclass")

    def evaluate(self, variables: Union[Dict[str, float], Dict[str, np.ndarray]]) -> float:
        """
        Evaluate a mathematical expression using the given variables
        :param variables: a dictionary of variable names and their values
        :return: the result of the expression
        """
        try:
            result = eval(self.expression, variables, self.functions)
            if isinstance(result, float):
                self.expedition.set_exp_var_value(self.output_var, result)
                return result
        except Exception as e:
            print(f"Error evaluating expression: {e}")
        return np.nan


class MathChannelCalculator(Calculator):
    def __init__(self, config: MathChannelConfig, expedition: ExpeditionDLL):
        super().__init__(expedition,
                         config.expression,
                         config.output_expedition_var,
                         config.output_expedition_user_name)
        self.config = config
        self.inputs = config.inputs

    def calculate(self) -> float:
        values = self.expedition.get_exp_vars([input_var.expedition_var for input_var in self.config.inputs])
        variables = dict(zip([input_var.local_var_name for input_var in self.config.inputs], values))
        variables.update(self.variables)
        return self.evaluate(variables)


class RollingMathChannelCalculator(MathChannelCalculator):
    def __init__(self, config: RollingMathChannelConfig, expedition: ExpeditionDLL, time_step: float = 0.1):
        super().__init__(config, expedition)
        self.time_step = time_step
        self.buffer_length = int(np.ceil(config.window_length_time_delta.total_seconds() / time_step))

        self.buffers = {
            i.local_var_name: np.zeros(self.buffer_length) * np.nan
            for i in self.config.inputs
        }

    def calculate(self) -> float:
        # get the latest input values
        for i in self.inputs:
            latest_value = self.expedition.get_exp_var_value(i.expedition_var)
            self.buffers[i.local_var_name] = np.roll(self.buffers[i.local_var_name], 1)
            self.buffers[i.local_var_name][0] = latest_value

        variables = {**self.buffers}
        variables.update(self.variables)
        return self.evaluate(variables)

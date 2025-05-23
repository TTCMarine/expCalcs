from .models import MathChannelConfig
from typing import Dict, Optional, Union
from Expedition import Var, ExpeditionDLL
import numpy as np
from abc import ABC, abstractmethod
import logging
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class Calculator(QObject):
    evaluated = Signal(float)  # Emitted when an expression is successfully evaluated
    error = Signal(str)  # Emitted when an error occurs during evaluation

    def __init__(self,
                 expedition: ExpeditionDLL,
                 expression: str,
                 output_var: Var,
                 output_var_user_name: Optional[str] = None,
                 name: Optional[str] = None):
        QObject.__init__(self)

        self.expedition = expedition
        self.expression = expression
        self.output_var = output_var
        self.output_var_user_name = output_var_user_name
        self.name = name if name else expression

        self.variables = {}
        self.functions = {'__builtins__': None}
        self._evaluation_variables = {}

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
        self.functions['power'] = np.power
        self.functions['square'] = np.square
        self.functions['cbrt'] = np.cbrt
        self.functions['reciprocal'] = np.reciprocal
        self.functions['negative'] = np.negative
        self.functions['positive'] = np.positive
        self.functions['signbit'] = np.signbit
        self.functions['copysign'] = np.copysign

    def add_default_variables(self):
        """
        Add the following Python variables to be used in a mathematical expression:
        """
        self.variables['pi'] = np.pi
        self.variables['e'] = np.e

    @staticmethod
    def from_config(config: MathChannelConfig,
                    expedition: ExpeditionDLL,
                    time_step: float = 0.1,
                    ) -> 'Calculator':
        """
        Create a calculator from a MathChannelConfig
        :param config: MathChannelConfig
        :param expedition: ExpeditionDLL
        :param time_step: time step for rolling calculations
        :return: Calculator
        """
        if config.window_length:
            return RollingMathChannelCalculator(config, expedition, time_step)
        else:
            return MathChannelCalculator(config, expedition)

    @abstractmethod
    def calculate(self) -> float:
        raise NotImplementedError("calculate method must be implemented in a subclass")

    def evaluate(self, variables: Union[Dict[str, float], Dict[str, np.ndarray]]) -> float:
        """
        Evaluate a mathematical expression using the given variables
        :param variables: a dictionary of variable names and their values
        :return: the result of the expression
        """
        self._evaluation_variables = variables
        try:
            result = eval(self.expression, self._evaluation_variables, self.functions)
            if isinstance(result, float):
                self.expedition.set_exp_var_value(self.output_var, result)
                self.evaluated.emit(result)
                return result
            elif isinstance(result, np.ndarray):
                if result.size == 1:
                    result = result.item()
                    self.expedition.set_exp_var_value(self.output_var, result)
                    self.evaluated.emit(result)
                    return result
                else:
                    logger.warning(f"Expression returned an array of size {result.size}, expected a single value.")
                    self.error.emit("Expression returned an array, expected a single value.")
        except Exception as e:
            logger.warning(f"Error evaluating expression: {e}")
            self.error.emit(str(e))
            # set the output variable to NaN

        self.expedition.set_exp_var_value(self.output_var, np.nan)
        self.evaluated.emit(float('nan'))
        return np.nan

    @property
    def evaluation_variables(self) -> Dict[str, Union[float, np.ndarray]]:
        """
        Get the evaluation variables used in the last evaluation
        :return: a dictionary of variable names and their values
        """
        # return self._evaluation_variables without the builtins
        return {k: v for k, v in self._evaluation_variables.items() if not k.startswith('__')}


class MathChannelCalculator(Calculator):
    def __init__(self, config: MathChannelConfig, expedition: ExpeditionDLL):
        super().__init__(expedition,
                         config.expression,
                         config.output_expedition_var,
                         config.output_expedition_user_name,
                         config.name)
        self.config = config
        self.inputs = config.inputs

    def calculate(self) -> float:
        values = self.expedition.get_exp_vars([input_var.expedition_var for input_var in self.config.inputs])
        variables = dict(zip([input_var.local_var_name for input_var in self.config.inputs], values))
        variables.update(self.variables)
        return self.evaluate(variables)


class RollingMathChannelCalculator(MathChannelCalculator):
    def __init__(self, config: MathChannelConfig, expedition: ExpeditionDLL, time_step: float = 0.1):
        super().__init__(config, expedition)
        self.time_step = time_step
        self.buffer_length = max(int(np.ceil(config.window_length_time_delta.total_seconds() / time_step)), 1)

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

from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, field_validator
from Expedition import Var
import pandas as pd
from datetime import timedelta

__all = ["ExpeditionConfig", "GcpConfig", "ChannelConfig", "GroupConfig", "Config"]


class InputVar(BaseModel):
    expedition_var_enum_string: str
    local_var_name: str

    @field_validator('expedition_var_enum_string')
    @classmethod
    def enum_var_string_is_in_enum(cls, v: Any) -> Any:
        if v not in Var.__members__:
            raise ValueError(f"{v} is not a valid Var")
        return v

    @property
    def expedition_var(self) -> Var:
        # convert the string to the enum
        return Var[self.expedition_var_enum_string]


class ExpeditionConfig(BaseModel):
    install_path: str


class MathChannelConfig(BaseModel):
    name: str
    output_expedition_var_enum_string: str
    output_expedition_user_name: Optional[str] = None
    expression: str
    inputs: List[InputVar]
    output_is_heading: Optional[bool] = False
    window_length: Optional[str] = None # e.g. "1s", "5m", "1h"

    @field_validator('output_expedition_var_enum_string')
    @classmethod
    def enum_var_string_is_in_enum(cls, v: Any) -> Any:
        if v not in Var.__members__:
            raise ValueError(f"{v} is not a valid Var")
        return v

    @property
    def output_expedition_var(self) -> Var:
        # convert the string to the enum
        return Var[self.output_expedition_var_enum_string]

    @staticmethod
    def channel_type() -> str:
        return "Math Channel"

    @property
    def window_length_time_delta(self) -> Optional[timedelta]:
        if self.window_length is None:
            return None
        else:
            return pd.to_timedelta(self.window_length)

class Config(BaseModel):
    expedition: ExpeditionConfig
    boat: Optional[int] = 0
    math_channels: List[MathChannelConfig]


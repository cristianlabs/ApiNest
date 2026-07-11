import enum

from sqlalchemy import Enum as SAEnum


def str_enum_column(enum_cls: type[enum.Enum], length: int = 20) -> SAEnum:
    return SAEnum(enum_cls, native_enum=False, length=length, values_callable=lambda e: [m.value for m in e])

"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    PIN_HOLIDAYS = "pin_holidays"
    PUBLIC_HOLIDAYS = "public_holidays"
    CALENDAR = "calendar"


class Task(Enum):
    FIND_DEADLINE = "find-deadline"


class Country(Enum):
    US = "US"
    CA = "CA"
    GB = "GB"
    DE = "DE"
    FR = "FR"
    CH = "CH"
    AU = "AU"
    NZ = "NZ"


COUNTRY = "The country, by its ISO 3166-1 alpha-2 code"
REGION = 'The region inside the country, as Nager.Date codes it (e.g. "DE-BY", "GB-SCT", "AU-NSW"), or "" for none'
DATE = "A date written YYYY-MM-DD"


@dataclass
class Holiday(Output):
    date: Annotated[str, DATE]
    name: Annotated[str, "Its English name"]
    nationwide: Annotated[bool, "Whether it is a holiday in the whole country (Nager.Date's global)"]
    regions: Annotated[list[str], "The regions it is a holiday in when it is not nationwide (Nager.Date's counties)"]
    types: Annotated[list[str], "Its kinds: Public, Bank, School, Authorities, Optional or Observance"]


@dataclass
class DeadlineInput(Output):
    country: Annotated[Country, COUNTRY]
    region: Annotated[str, REGION]
    start: Annotated[str, "The date counting starts after, YYYY-MM-DD (the start itself never counts)"]
    business_days: Annotated[int, "How many business days to count, 1 to 30"]


@dataclass
class YearHolidays(Output):
    year: Annotated[int, "The year"]
    holidays: Annotated[list[Holiday], "Every holiday Nager.Date lists for the country that year"]


@dataclass
class PinOutput(Output):
    country: Annotated[Country, COUNTRY]
    region: Annotated[str, REGION]
    start: Annotated[str, DATE]
    business_days: Annotated[int, "How many business days are counted"]
    years: Annotated[list[YearHolidays], "The holidays of the start's year and the next, as Nager.Date gave them"]
    table_sha256: Annotated[
        str, "The sha256 of the question and each year's holidays, as rules.table_sha256 computes it"
    ]


@dataclass
class HolidaysInput(Output):
    country: Annotated[Country, COUNTRY]
    year: Annotated[int, "The year, 1990 to 2040"]


@dataclass
class HolidaysOutput(Output):
    country: Annotated[Country, COUNTRY]
    year: Annotated[int, "The year"]
    holidays: Annotated[list[Holiday], "Every holiday Nager.Date lists for the country that year, by date"]


@dataclass
class MonthInput(Output):
    year: Annotated[int, "The year, 1990 to 2040"]
    month: Annotated[int, "The month, 1 to 12"]


@dataclass
class Day(Output):
    date: Annotated[str, DATE]
    weekday: Annotated[str, "Monday to Sunday"]


@dataclass
class MonthOutput(Output):
    year: Annotated[int, "The year"]
    month: Annotated[int, "The month"]
    days: Annotated[list[Day], "Every day of the month with its weekday"]


@dataclass
class DeadlineOutput(Output):
    deadline: Annotated[str, "The date of the Nth business day, YYYY-MM-DD"]
    skipped_holidays: Annotated[
        list[str], "The dates of the applying holidays that fell on a weekday between the start and the deadline"
    ]


TOOLS = {
    Tool.PIN_HOLIDAYS: (DeadlineInput, PinOutput),
    Tool.PUBLIC_HOLIDAYS: (HolidaysInput, HolidaysOutput),
    Tool.CALENDAR: (MonthInput, MonthOutput),
}

TASKS = {Task.FIND_DEADLINE: (DeadlineInput, DeadlineOutput)}

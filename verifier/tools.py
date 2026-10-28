"""Each tool's input and output checks."""

from .days import WEEKDAYS, month_length, to_days, weekday
from .rules import FIRST_YEAR, LAST_YEAR, list_sha256, question_problem, table_sha256
from .task import result


def year_problem(year):
    return None if FIRST_YEAR <= year <= LAST_YEAR else f"the year must be {FIRST_YEAR} to {LAST_YEAR}"


def holidays_problem(holidays, year):
    for holiday in holidays:
        if not holiday.date.startswith(f"{year:04d}-"):
            return f"{holiday.name} on {holiday.date} is not in {year}"
        if not holiday.types:
            return f"{holiday.name} has no type"
        if not holiday.nationwide and not holiday.regions:
            return f"{holiday.name} is neither nationwide nor regional"
    return None


class Pin:
    @staticmethod
    def verify_input(value):
        problem = question_problem(value.country.value, value.region, value.start, value.business_days)
        return result(problem is None, problem or "input is valid")

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        asked = (input_value.country, input_value.region, input_value.start, input_value.business_days)
        if (output_value.country, output_value.region, output_value.start, output_value.business_days) != asked:
            return result(False, "the key is for another question")
        for entry in output_value.years:
            problem = holidays_problem(entry.holidays, entry.year)
            if problem:
                return result(False, problem)
        years = [(entry.year, entry.holidays) for entry in output_value.years]
        digest = table_sha256(
            output_value.country.value, output_value.region, output_value.start, output_value.business_days, years
        )
        if output_value.table_sha256 != digest:
            return result(False, "table_sha256 does not match the key")
        return result(True, "the key is consistent", years=[entry.year for entry in output_value.years])


class Holidays:
    @staticmethod
    def verify_input(value):
        problem = year_problem(value.year)
        return result(problem is None, problem or "input is valid")

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        if (output_value.country, output_value.year) != (input_value.country, input_value.year):
            return result(False, "the holidays are for another country or year")
        problem = holidays_problem(output_value.holidays, output_value.year)
        if problem:
            return result(False, problem)
        return result(True, "the holidays are well formed", digest=list_sha256(output_value.holidays))


class Month:
    @staticmethod
    def verify_input(value):
        problem = year_problem(value.year) or (None if 1 <= value.month <= 12 else "the month must be 1 to 12")
        return result(problem is None, problem or "input is valid")

    @staticmethod
    def verify_output(input_value, output_value, workspace):
        expected = [
            f"{input_value.year:04d}-{input_value.month:02d}-{d:02d}"
            for d in range(1, month_length(input_value.year, input_value.month) + 1)
        ]
        if [day.date for day in output_value.days] != expected:
            return result(False, "the days are not the month's, in order")
        if any(day.weekday != WEEKDAYS[weekday(to_days(day.date))] for day in output_value.days):
            return result(False, "a weekday is wrong")
        return result(True, "the month is right", days=len(expected))

import re

from datetime import datetime
from dateutil import relativedelta

def clean_text(text: str) -> str:
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s\n.,;:!?"\'\[\]{}=+()\-@]', '', text)
    
    return cleaned_text

def remove_non_readable_chars(input_string: str) -> str:
    # Regular expression for non-readable characters
    # \x00-\x1F: Control characters
    # \x7F: Delete character
    # Additional characters can be added as needed
    non_readable_regex = r'[\x00-\x1F\x7F]'

    # Replace non-readable characters with an empty string
    cleaned_string = re.sub(non_readable_regex, '', input_string)

    return cleaned_string


def get_total_experience(experience: list[str]) -> int:
    """
    Wrapper function to extract total months of experience from a resumes

    :param experience: list of experience text extracted
    :return: total months of experience
    """

    exp = []

    for line in experience:
        experience = re.search(
            r'(?P<fmonth>\w+.\d+)\s*(\D|to)\s*(?P<smonth>\w+.\d+|present)',
            line,
            re.I
        )
        if experience:
            exp.append(experience.groups())
    total_exp = sum(
        [get_number_of_months_from_dates(i[0], i[2]) for i in exp]
    )
    
    return total_exp


def get_number_of_months_from_dates(date1, date2):
    """
    Helper function to extract total months of experience from a resumes

    :param date1: Starting date
    :param date2: Ending date
    :return: months of experience from date1 to date2
    """

    if date2.lower() == 'present':
        date2 = datetime.now().strftime('%b %Y')

    try:
        if len(date1.split()[0]) > 3:
            date1 = date1.split()
            date1 = date1[0][:3] + ' ' + date1[1]
        if len(date2.split()[0]) > 3:
            date2 = date2.split()
            date2 = date2[0][:3] + ' ' + date2[1]
    except IndexError:
        return 0
    
    try:
        date1 = datetime.strptime(str(date1), '%b %Y')
        date2 = datetime.strptime(str(date2), '%b %Y')
        months_of_experience = relativedelta.relativedelta(date2, date1)
        months_of_experience = (months_of_experience.years
                                * 12 + months_of_experience.months)
    except ValueError:
        return 0
    
    return months_of_experience
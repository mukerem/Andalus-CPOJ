from django.core.exceptions  import ValidationError
import os
from django.core.validators import validate_email

def validate_problem_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')
    
def validate_testcase_in_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.in']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')

def validate_testcase_out_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.out', '.ans']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')


def email_validate(email_address):
    try:
        validate_email(email_address)
    except ValidationError as e:
        return 0
    else:
        return 1
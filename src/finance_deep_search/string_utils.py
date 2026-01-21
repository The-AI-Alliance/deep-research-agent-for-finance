# Common string utilities

def replace_variables(string: str, **variables) -> str:
    """
    Replace variables in a string with their values.
    """
    for key, value in variables.items():
        string = string.replace('{{{{'+key+'}}}}', str(value))
    
    return string

def logged_decode(data_bytes, label, errorlog=None, encoding='ascii', errors='replace'):
    try:
        return data_bytes.decode(encoding)
    except UnicodeDecodeError as e:
        safename = data_bytes.decode(encoding, errors=errors)
        if errorlog is not None:
            errorlog.log_warning_message(f"{label} has an undecodable name '{safename}'")
        else:
            raise e
        return safename

def logged_encode(data, label, errorlog=None, encoding='ascii', errors='replace'):
    try:
        return data.encode(encoding)
    except UnicodeEncodeError as e:
        safename = data.encode(encoding, errors=errors)
        if errorlog is not None:
            errorlog.log_warning_message(f"{label} has a non-{encoding} name '{safename}'")
        else:
            raise e
        return safename

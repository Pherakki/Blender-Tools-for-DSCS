import os


def get_root_path():
    current_path = os.path.realpath(__file__)
    path = os.path.join(current_path, 
                             os.path.pardir,
                             os.path.pardir,
                             os.path.pardir)
    return os.path.realpath(path)


def get_package_name():
    return os.path.basename(get_root_path())

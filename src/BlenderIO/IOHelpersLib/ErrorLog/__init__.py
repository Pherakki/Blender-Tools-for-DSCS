"""
The errorlog submodule was inspired by and initially based on the Google-forms 
reporter at https://github.com/TheDuckCow/user-report-wrapper
"""
from .Logger import ErrorLogBase
from .Warning import ReportableError
from .Warning import DisplayableVerticesError
from .Warning import DisplayablePolygonsError
from .Warning import DisplayableMeshesError

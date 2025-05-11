import functools

import bpy

from ...utils.Sentinels import NoOpSentinel


####################################
# ACTIVE OBJECT SWAPPING UTILITIES #
####################################

def set_active_obj(obj):
    bpy.context.view_layer.objects.active = obj


def get_active_obj():
    return bpy.context.view_layer.objects.active


class TempSwapActiveObject:
    """
    A Context Manager that, on exit, restores the current view layer's active 
    object back to whatever it was immediately before the wrapped function was 
    called.
    """
    def __init__(self, swap_to=NoOpSentinel):
        self.swap_to  = swap_to
        self.prev_obj = get_active_obj()
    
    def __enter__(self):
        if self.swap_to is not NoOpSentinel:
            set_active_obj(self.swap_to)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_active_obj(self.prev_obj)
        

def preserve_initial_active_object(func):
    """
    A function descriptor that, after the wrapped function returns, restores 
    the current view layer's active object back to whatever it was immediately 
    before the wrapped function was called.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        with TempSwapActiveObject():
            return func(*args, **kwargs)
    return wrapped


###########################
# MODE SWAPPING UTILITIES #
###########################

def get_mode():
    return bpy.context.object.mode

def set_mode(mode):
    bpy.ops.object.mode_set(mode=mode)


class TempSwapActiveObjectMode:
    def __init__(self, mode):
        self.prev_mode = get_mode()
        self.mode      = mode
    
    def __enter__(self):
        set_mode(self.mode)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_mode(self.prev_mode)


def preserve_initial_object_mode(func):
    """
    A function descriptor that, after the wrapped function returns, restores 
    the current view layer's active object's mode back to whatever it was 
    immediately before the wrapped function was called.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        with TempSwapActiveObjectMode(get_mode()), TempSwapActiveObject():
            out = func(*args, **kwargs)
            active_obj = get_active_obj()
        set_active_obj(active_obj)
        
        return out
    return wrapped


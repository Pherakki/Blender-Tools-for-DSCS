import typing

import bpy


class ArgGroup:
    """
    A class to hold property type annotations. The role of this class is to
    contain a list of arguments for operators which can also be packaged
    into a PropertyGroup.
    To meet this goal, there are two methods on ArgGroup:
    1) PropGroup()
       This defines a PropertyGroup with the type annotations of ArgGroup and
       its superclasses. This PropertyGroup can have its values initialized
       from another PropertyGroup containing those annotations, or an operator
       containing them. This group must be independently registered with
       Blender.
    2) AnnotationGroup()
       This defines a class containing *only* the type annotations of ArgGroup
       and its superclasses. This is a class that Operators should inherit from
       in order to implement the properties of the ArgGroup. Inheriting from
       this class avoid polluting the Operator with the methods of the 
       ArgGroup.
    """
    @classmethod
    def PropGroup(cls):
        """
        Creates a class inheriting from PropertyGroup that can be initialized 
        from objects inheriting from the classes of this ArgGroup.
        This class must be registered with Blender in order to be used.
        """
        class ArgPropertyGroup(cls.AnnotationGroup(), bpy.types.PropertyGroup):
            def copy_from(self, other):
                self.copy_between(other, self)
                
            def copy_to(self, other):
                self.copy_between(self, other)
            
            @classmethod
            def copy_between(cls, from_, to_):
                for name, prop in typing.get_type_hints(cls).items():
                    # Ignore any non-property types
                    if not isinstance(prop, bpy.props._PropertyDeferred):
                        continue
                    
                    setattr(to_, name, getattr(from_, name))
            
        return ArgPropertyGroup

    @classmethod
    def AnnotationGroup(cls):
        """
        Creates a class containing only annotations and no functions,
        to avoid polluting operators with ArgGroup methods.
        """
        class ArgAnnotationGroup:
            pass
        
        for name, annotation in typing.get_type_hints(cls).items():
            ArgAnnotationGroup.__annotations__[name] = annotation
        
        return ArgAnnotationGroup


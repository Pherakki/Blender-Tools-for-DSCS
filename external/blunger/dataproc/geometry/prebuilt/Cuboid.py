def make_cuboid(width, height, depth, scale=1):
    x_span  = scale[0] * width  / 2
    y_span  = scale[1] * height / 2
    z_span  = scale[2] * depth  / 2
    
    vertices = [
        (-x_span, -y_span, -z_span),
        (-x_span, -y_span, +z_span),
        (-x_span, +y_span, -z_span),
        (-x_span, +y_span, +z_span),
        (+x_span, -y_span, -z_span),
        (+x_span, -y_span, +z_span),
        (+x_span, +y_span, -z_span),
        (+x_span, +y_span, +z_span),
    ]
        
    faces = [
        (0, 1, 3, 2),
        (4, 6, 7, 5),
        (2, 3, 7, 6),
        (0, 4, 5, 1),
        (0, 2, 6, 4),
        (1, 5, 7, 3)
    ]
    
    return vertices, [], faces


import math


def make_capsule(n, radius, height, scale=1):
    scale = sum(scale)/len(scale)
    radius *= scale
    height *= scale
    
    # n is the number of verts per quarter
    
    vertices = []
    polys = []
    
    # Hemisphere 1
    v_offset = len(vertices)
    for j in range(n):
        theta = j * 2*math.pi/ (4*n)
        z = radius*math.sin(theta) + height
        for i in range(n*4):
            phi = i * 2*math.pi/ (4*n)
            
            x = radius * math.cos(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.cos(theta)
            
            vertices.append((x, y, z))
    vertices.append((0., 0., radius + height))

    for j in range(n-1):
        for i in range(n*4 - 1):
            s1 = v_offset + 4*n*j + i
            s2 = v_offset + 4*n*(j+1) + i
            polys.append((s1, s1+1, s2+1, s2))
        
        s1 = v_offset + 4*n*j     + (4*n - 1)
        s2 = v_offset + 4*n*(j+1) + (4*n - 1)
        polys.append((s1, 4*n*j, 4*n*(j+1), s2))
        
    final_idx = len(vertices) - 1
    j_row = v_offset + 4*n*(n-1)
    for i in range(n*4 - 1):
        polys.append((j_row + i, j_row + i + 1, final_idx))
    polys.append((final_idx-1, j_row, final_idx))

    # Hemisphere 2
    v_offset = len(vertices)
    for j in range(n):
        theta = j * 2*math.pi/ (4*n)
        z = - radius*math.sin(theta) - height
        for i in range(n*4):
            phi = i * 2*math.pi/ (4*n)
            
            x = radius * math.cos(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.cos(theta)
            
            vertices.append((x, y, z))
    vertices.append((0., 0., - radius - height))

    for j in range(n-1):
        for i in range(n*4 - 1):
            s1 = v_offset + 4*n*j + i
            s2 = v_offset + 4*n*(j+1) + i
            polys.append((s1+1, s1, s2, s2+1))
        
        s1 = v_offset + 4*n*j     
        s2 = v_offset + 4*n*(j+1)
        polys.append((s1, s1 + (4*n - 1), s2 + (4*n - 1), s2))
        
    final_idx = len(vertices) - 1
    j_row = v_offset + 4*n*(n-1)
    for i in range(n*4 - 1):
        polys.append((j_row + i + 1, j_row + i, final_idx))
    polys.append((j_row, final_idx-1, final_idx))
    
    # Cylinder body
    for i in range(n*4 - 1):
        s1 = i
        s2 = v_offset + i
        polys.append([s1+1, s1, s2, s2+1])
    s1 = n*4-1
    s2 = v_offset + n*4 - 1
    polys.append([0, s1, s2, v_offset])
    
    return vertices, [], polys


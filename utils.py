import math

def rotate_point(x, y, center_x, center_y, angle_deg):
    """Rotate a point around a center by an angle in degrees."""
    # Convert angle to radians
    angle_rad = math.radians(angle_deg)
    
    # Translate point to origin
    translated_x = x - center_x
    translated_y = y - center_y
    
    # Rotate point
    rotated_x = translated_x * math.cos(angle_rad) - translated_y * math.sin(angle_rad)
    rotated_y = translated_x * math.sin(angle_rad) + translated_y * math.cos(angle_rad)
    
    # Translate back
    return rotated_x + center_x, rotated_y + center_y

def distance(point1, point2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def angle_between_points(point1, point2):
    """Calculate angle between two points in degrees."""
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    return math.degrees(math.atan2(dy, dx))

def point_in_rect(point, rect):
    """Check if a point is inside a rectangle."""
    return (rect.left <= point[0] <= rect.right and 
            rect.top <= point[1] <= rect.bottom)

def line_intersects_rect(line_start, line_end, rect):
    """Check if a line segment intersects with a rectangle."""
    # Check if either endpoint is inside the rectangle
    if point_in_rect(line_start, rect) or point_in_rect(line_end, rect):
        return True
    
    # Check intersection with each edge of the rectangle
    rect_edges = [
        ((rect.left, rect.top), (rect.right, rect.top)),
        ((rect.right, rect.top), (rect.right, rect.bottom)),
        ((rect.right, rect.bottom), (rect.left, rect.bottom)),
        ((rect.left, rect.bottom), (rect.left, rect.top))
    ]
    
    for edge_start, edge_end in rect_edges:
        if lines_intersect(line_start, line_end, edge_start, edge_end):
            return True
    
    return False

def lines_intersect(line1_start, line1_end, line2_start, line2_end):
    """Check if two line segments intersect."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    
    return (ccw(line1_start, line2_start, line2_end) != ccw(line1_end, line2_start, line2_end) and
            ccw(line1_start, line1_end, line2_start) != ccw(line1_start, line1_end, line2_end))

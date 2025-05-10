import pygame
import math
import numpy as np
from utils import rotate_point, distance, angle_between_points

class Vehicle:
    def __init__(self, x, y, angle=0):
        """Initialize the vehicle."""
        # Position and physics
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.angle = angle  # in degrees
        self.start_angle = angle
        self.velocity = 0
        self.max_velocity = 4
        self.acceleration = 0.1
        self.deceleration = 0.2
        self.turning_speed = 2  # degrees per frame when turning
        
        # Vehicle dimensions (rectangle)
        self.width = 40
        self.length = 80
        self.color = (0, 0, 255)  # Blue car
        
        # Navigation
        self.target_x = None
        self.target_y = None
        self.target_angle = None
        self.path = []
        self.current_path_index = 0
        self.path_colors = [(0, 255, 0), (255, 165, 0), (128, 0, 128)]  # Green, Orange, Purple for different attempts
        
        # State machine
        self.state = "idle"  # idle, moving, rotating, parking, returning
        self.parking_phase = 0  # Different phases of the parking maneuver
    
    def reset(self):
        """Reset the vehicle to its initial state."""
        self.x = self.start_x
        self.y = self.start_y
        self.angle = self.start_angle
        self.velocity = 0
        self.target_x = None
        self.target_y = None
        self.target_angle = None
        self.path = []
        self.current_path_index = 0
        self.state = "idle"
        self.parking_phase = 0
    
    def set_path(self, path, attempt_number):
        """Set a new path for the vehicle to follow."""
        self.path = path
        self.current_path_index = 0
        self.path_color = self.path_colors[min(attempt_number - 1, len(self.path_colors) - 1)]
    
    def move_to(self, target_x, target_y, target_angle=None):
        """Set a target position and angle for the vehicle."""
        self.target_x = target_x
        self.target_y = target_y
        self.target_angle = target_angle
        self.state = "moving"
    
    def get_corners(self):
        """Get the four corners of the vehicle based on position and rotation."""
        half_length = self.length / 2
        half_width = self.width / 2
        
        # Define the four corners relative to center (before rotation)
        corners = [
            (-half_length, -half_width),  # top-left
            (half_length, -half_width),   # top-right
            (half_length, half_width),    # bottom-right
            (-half_length, half_width)    # bottom-left
        ]
        
        # Rotate and translate the corners
        rotated_corners = []
        for corner_x, corner_y in corners:
            rx, ry = rotate_point(corner_x, corner_y, 0, 0, self.angle)
            rotated_corners.append((self.x + rx, self.y + ry))
        
        return rotated_corners
    
    def is_colliding(self, obstacles):
        """Check if the vehicle is colliding with any obstacles."""
        vehicle_corners = self.get_corners()
        vehicle_rect = pygame.Rect(0, 0, 0, 0)
        vehicle_rect.points = vehicle_corners
        
        for obstacle in obstacles:
            # Simple rectangle collision
            if self._check_rectangle_collision(vehicle_corners, obstacle):
                return True
        
        return False
    
    def _check_rectangle_collision(self, vehicle_corners, obstacle_rect):
        """Check collision between the vehicle and a rectangle obstacle."""
        # Convert pygame Rect to corners
        obstacle_corners = [
            (obstacle_rect.left, obstacle_rect.top),
            (obstacle_rect.right, obstacle_rect.top),
            (obstacle_rect.right, obstacle_rect.bottom),
            (obstacle_rect.left, obstacle_rect.bottom)
        ]
        
        # Check each edge of the vehicle against each edge of the obstacle
        for i in range(4):
            # Vehicle edge
            v_edge_start = vehicle_corners[i]
            v_edge_end = vehicle_corners[(i + 1) % 4]
            
            for j in range(4):
                # Obstacle edge
                o_edge_start = obstacle_corners[j]
                o_edge_end = obstacle_corners[(j + 1) % 4]
                
                # Check if the two edges intersect
                if self._do_lines_intersect(v_edge_start, v_edge_end, o_edge_start, o_edge_end):
                    return True
        
        # Also check if one rectangle is completely inside the other
        return self._is_point_in_polygon(vehicle_corners[0], obstacle_corners) or \
               self._is_point_in_polygon(obstacle_corners[0], vehicle_corners)
    
    def _do_lines_intersect(self, p1, p2, p3, p4):
        """Check if two line segments intersect."""
        def ccw(a, b, c):
            return (c[1]-a[1]) * (b[0]-a[0]) > (b[1]-a[1]) * (c[0]-a[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    def _is_point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting algorithm."""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def update(self, obstacles=[]):
        """Update the vehicle's position and state."""
        if self.state == "idle":
            return
        
        if self.state == "moving":
            self._update_moving()
        elif self.state == "rotating":
            self._update_rotating()
        elif self.state == "parking":
            self._update_parking(obstacles)
        elif self.state == "returning":
            self._update_returning()
    
    def _update_moving(self):
        """Update the vehicle when it's moving towards a target."""
        if self.target_x is None or self.target_y is None:
            self.state = "idle"
            return
        
        # Calculate distance to target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        target_distance = math.sqrt(dx*dx + dy*dy)
        
        # Calculate desired angle to target
        target_angle_rad = math.atan2(dy, dx)
        desired_angle = math.degrees(target_angle_rad)
        
        # Adjust angle
        angle_diff = (desired_angle - self.angle) % 360
        if angle_diff > 180:
            angle_diff -= 360
        
        # Rotate towards target
        if abs(angle_diff) > 2:
            if angle_diff > 0:
                self.angle += min(self.turning_speed, angle_diff)
            else:
                self.angle -= min(self.turning_speed, -angle_diff)
            # Normalize angle
            self.angle %= 360
            # Reduce speed when turning sharply
            self.velocity = max(0, self.velocity - 0.05)
        else:
            # We're facing the right direction, accelerate
            self.velocity = min(self.max_velocity, self.velocity + self.acceleration)
        
        # Move the vehicle
        rad_angle = math.radians(self.angle)
        self.x += self.velocity * math.cos(rad_angle)
        self.y += self.velocity * math.sin(rad_angle)
        
        # Check if we've reached the target
        if target_distance < 5:
            self.velocity = 0
            if self.target_angle is not None:
                self.state = "rotating"
            else:
                self.state = "idle"
                self.target_x = None
                self.target_y = None
    
    def _update_rotating(self):
        """Update the vehicle when it's rotating to a target angle."""
        if self.target_angle is None:
            self.state = "idle"
            return
        
        # Calculate angle difference
        angle_diff = (self.target_angle - self.angle) % 360
        if angle_diff > 180:
            angle_diff -= 360
        
        # Rotate towards target angle
        if abs(angle_diff) > 1:
            if angle_diff > 0:
                self.angle += min(self.turning_speed, angle_diff)
            else:
                self.angle -= min(self.turning_speed, -angle_diff)
            # Normalize angle
            self.angle %= 360
        else:
            # We've reached the target angle
            self.angle = self.target_angle
            self.state = "idle"
            self.target_angle = None
    
    def _update_parking(self, obstacles):
        """Update the vehicle during parking maneuvers."""
        # This would implement the specific parking maneuver steps
        # based on the parking_phase
        
        # For simplicity, just using general movement for now
        # In a full implementation, this would have specific movement patterns
        # for parallel and perpendicular parking
        
        # Check for collisions
        if self.is_colliding(obstacles):
            self.state = "returning"
            return
        
        if self.path and self.current_path_index < len(self.path):
            # Follow the path
            target = self.path[self.current_path_index]
            
            # Calculate distance to target
            dx = target[0] - self.x
            dy = target[1] - self.y
            target_distance = math.sqrt(dx*dx + dy*dy)
            
            # Calculate desired angle to target
            target_angle_rad = math.atan2(dy, dx)
            desired_angle = math.degrees(target_angle_rad)
            
            # Adjust angle
            angle_diff = (desired_angle - self.angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            
            # Rotate towards target
            if abs(angle_diff) > 2:
                if angle_diff > 0:
                    self.angle += min(self.turning_speed, angle_diff)
                else:
                    self.angle -= min(self.turning_speed, -angle_diff)
                # Normalize angle
                self.angle %= 360
                # Reduce speed when turning sharply
                self.velocity = max(0, self.velocity - 0.05)
            else:
                # We're facing the right direction, accelerate
                self.velocity = min(self.max_velocity / 2, self.velocity + self.acceleration / 2)
            
            # Move the vehicle
            rad_angle = math.radians(self.angle)
            self.x += self.velocity * math.cos(rad_angle)
            self.y += self.velocity * math.sin(rad_angle)
            
            # Check if we've reached the target
            if target_distance < 5:
                self.current_path_index += 1
                if self.current_path_index >= len(self.path):
                    self.state = "idle"
                    self.velocity = 0
        else:
            self.state = "idle"
            self.velocity = 0
    
    def _update_returning(self):
        """Update the vehicle when it's returning to the start position."""
        # Move back to starting position
        dx = self.start_x - self.x
        dy = self.start_y - self.y
        distance_to_start = math.sqrt(dx*dx + dy*dy)
        
        if distance_to_start < 10:
            # We're close enough to the start
            self.x = self.start_x
            self.y = self.start_y
            
            # Now adjust angle
            angle_diff = (self.start_angle - self.angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
                
            if abs(angle_diff) < 2:
                # We've returned to start
                self.angle = self.start_angle
                self.velocity = 0
                self.state = "idle"
                return
                
            # Rotate towards starting angle
            if angle_diff > 0:
                self.angle += min(self.turning_speed, angle_diff)
            else:
                self.angle -= min(self.turning_speed, -angle_diff)
            # Normalize angle
            self.angle %= 360
        else:
            # Calculate desired angle to start
            target_angle_rad = math.atan2(dy, dx)
            desired_angle = math.degrees(target_angle_rad)
            
            # Adjust angle
            angle_diff = (desired_angle - self.angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            
            # Rotate towards target
            if abs(angle_diff) > 2:
                if angle_diff > 0:
                    self.angle += min(self.turning_speed, angle_diff)
                else:
                    self.angle -= min(self.turning_speed, -angle_diff)
                # Normalize angle
                self.angle %= 360
                # Reduce speed when turning sharply
                self.velocity = max(0, self.velocity - 0.05)
            else:
                # We're facing the right direction, accelerate
                self.velocity = min(self.max_velocity, self.velocity + self.acceleration)
            
            # Move the vehicle
            rad_angle = math.radians(self.angle)
            self.x += self.velocity * math.cos(rad_angle)
            self.y += self.velocity * math.sin(rad_angle)
    
    def draw(self, screen):
        """Draw the vehicle on the screen."""
        # Draw the vehicle as a rotated rectangle
        corners = self.get_corners()
        pygame.draw.polygon(screen, self.color, corners)
        
        # Draw a small triangle to indicate the front of the vehicle
        front_x = self.x + (self.length / 2) * math.cos(math.radians(self.angle))
        front_y = self.y + (self.length / 2) * math.sin(math.radians(self.angle))
        
        # Draw front indicator
        indicator_size = 8
        indicator_points = [
            (front_x, front_y),
            (front_x - indicator_size * math.cos(math.radians(self.angle - 30)), 
             front_y - indicator_size * math.sin(math.radians(self.angle - 30))),
            (front_x - indicator_size * math.cos(math.radians(self.angle + 30)), 
             front_y - indicator_size * math.sin(math.radians(self.angle + 30)))
        ]
        pygame.draw.polygon(screen, (255, 255, 0), indicator_points)  # Yellow triangle
        
        # Draw the path with appropriate color
        if len(self.path) > 1:
            for i in range(len(self.path) - 1):
                pygame.draw.line(screen, self.path_color, 
                                self.path[i], self.path[i + 1], 2)
            
            # Draw current target point with a different color
            if self.current_path_index < len(self.path):
                pygame.draw.circle(screen, (255, 0, 0), 
                                  self.path[self.current_path_index], 5)

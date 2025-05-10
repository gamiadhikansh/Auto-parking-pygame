import pygame
import random
import numpy as np
from vehicle import Vehicle
from pathfinding import PathFinder
from utils import distance

class ParkingSimulation:
    def __init__(self, width, height):
        """Initialize the parking simulation."""
        self.width = width
        self.height = height
        
        # Create a vehicle
        start_x = 100
        start_y = height // 2
        self.vehicle = Vehicle(start_x, start_y, 0)
        
        # Setup environment
        self.obstacles = []  # Red cars
        self.parking_spots = []  # Green rectangles
        self.create_environment()
        
        # Pathfinding
        self.pathfinder = PathFinder(width, height)
        
        # Simulation state
        self.current_attempt = 0
        self.max_attempts = 3
        self.status = "Ready to start"
        self.active_spot = None
        
        # Create initial path
        self.find_parking_spot()
    
    def create_environment(self):
        """Create parking spots and obstacles."""
        self.obstacles = []
        self.parking_spots = []
        
        # Create some parallel parking spots (horizontal)
        parallel_count = 6
        spot_width = 100
        spot_height = 50
        start_x = 300
        y_positions = [150, self.height - 200]
        
        for y_pos in y_positions:
            for i in range(parallel_count):
                x = start_x + i * (spot_width + 20)
                
                # 70% chance to have an obstacle in the spot
                if random.random() < 0.7:
                    # Create a red car (obstacle)
                    obstacle_rect = pygame.Rect(x, y_pos, spot_width - 10, spot_height - 10)
                    self.obstacles.append(obstacle_rect)
                else:
                    # Create an empty parking spot
                    spot_rect = pygame.Rect(x, y_pos, spot_width, spot_height)
                    self.parking_spots.append({
                        "rect": spot_rect,
                        "type": "parallel",
                        "orientation": "horizontal" 
                    })
        
        # Create some perpendicular parking spots (vertical)
        perp_count = 4
        spot_width = 60
        spot_height = 90
        start_y = 250
        x_positions = [300, self.width - 200]
        
        for x_pos in x_positions:
            for i in range(perp_count):
                y = start_y + i * (spot_height + 20)
                
                # 70% chance to have an obstacle in the spot
                if random.random() < 0.7:
                    # Create a red car (obstacle)
                    obstacle_rect = pygame.Rect(x_pos, y, spot_width - 10, spot_height - 10)
                    self.obstacles.append(obstacle_rect)
                else:
                    # Create an empty parking spot
                    spot_rect = pygame.Rect(x_pos, y, spot_width, spot_height)
                    self.parking_spots.append({
                        "rect": spot_rect,
                        "type": "perpendicular",
                        "orientation": "vertical"
                    })
    
    def reset(self):
        """Reset the simulation."""
        self.vehicle.reset()
        self.create_environment()
        self.current_attempt = 0
        self.status = "Reset"
        self.active_spot = None
        self.find_parking_spot()
    
    def find_parking_spot(self):
        """Find the nearest available parking spot."""
        if self.current_attempt >= self.max_attempts:
            self.status = "No parking available after 3 attempts"
            return False
        
        # Get vehicle current position
        vehicle_pos = (self.vehicle.x, self.vehicle.y)
        
        # Find the nearest parking spot
        nearest_spot = None
        min_distance = float('inf')
        
        for spot in self.parking_spots:
            # Calculate distance to the spot
            spot_center = (
                spot["rect"].centerx,
                spot["rect"].centery
            )
            dist = distance(vehicle_pos, spot_center)
            
            if dist < min_distance:
                min_distance = dist
                nearest_spot = spot
        
        if nearest_spot:
            self.active_spot = nearest_spot
            self.current_attempt += 1
            
            # Calculate entry point based on spot type
            entry_point = self.calculate_entry_point(nearest_spot)
            
            # Generate a path to the entry point
            obstacles = self.obstacles.copy()
            
            # Add all other parking spots as obstacles for pathfinding
            for spot in self.parking_spots:
                if spot != nearest_spot:
                    obstacles.append(spot["rect"])
            
            # Find path to entry point
            path = self.pathfinder.find_path(
                (self.vehicle.x, self.vehicle.y),
                entry_point,
                obstacles
            )
            
            if path:
                # Add parking maneuver to the path
                full_path = self.add_parking_maneuver(path[-1], nearest_spot)
                self.vehicle.set_path(full_path, self.current_attempt)
                self.vehicle.state = "parking"
                self.status = f"Attempting parking in spot {self.current_attempt}/{self.max_attempts}"
                return True
        
        self.status = "No valid parking spots found"
        return False
    
    def calculate_entry_point(self, spot):
        """Calculate the entry point for a parking maneuver."""
        rect = spot["rect"]
        spot_type = spot["type"]
        orientation = spot["orientation"]
        
        if spot_type == "parallel":
            if orientation == "horizontal":
                # Entry point is in front of the spot
                return (rect.left - 50, rect.centery)
            else:  # vertical
                # Entry point is to the side of the spot
                return (rect.centerx, rect.top - 50)
        
        elif spot_type == "perpendicular":
            if orientation == "horizontal":
                # Entry point is in front of the spot
                return (rect.centerx, rect.top - 70)
            else:  # vertical
                # Entry point is to the side of the spot
                return (rect.left - 70, rect.centery)
        
        return (rect.centerx, rect.centery)
    
    def add_parking_maneuver(self, entry_point, spot):
        """Add parking maneuver waypoints to the path."""
        rect = spot["rect"]
        spot_type = spot["type"]
        orientation = spot["orientation"]
        
        # Start with the entry point
        path = [entry_point]
        
        # Add specific waypoints based on parking type
        if spot_type == "parallel":
            if orientation == "horizontal":
                # Parallel parking horizontally
                path.append((rect.left + 30, rect.centery))
                path.append((rect.centerx, rect.centery))
            else:  # vertical
                # Parallel parking vertically
                path.append((rect.centerx, rect.top + 30))
                path.append((rect.centerx, rect.centery))
        
        elif spot_type == "perpendicular":
            if orientation == "horizontal":
                # Perpendicular parking horizontally
                path.append((rect.centerx, rect.top + 30))
                path.append((rect.centerx, rect.centery))
            else:  # vertical
                # Perpendicular parking vertically
                path.append((rect.left + 30, rect.centery))
                path.append((rect.centerx, rect.centery))
        
        return path
    
    def update(self):
        """Update the simulation state."""
        # Update vehicle
        previous_state = self.vehicle.state
        self.vehicle.update(self.obstacles)
        
        # Check if vehicle state changed
        if previous_state != self.vehicle.state:
            if self.vehicle.state == "idle" and previous_state == "parking":
                # We successfully parked
                self.status = "Successfully parked!"
            elif self.vehicle.state == "idle" and previous_state == "returning":
                # We returned to start position after failed attempt
                self.status = f"Parking attempt {self.current_attempt} failed, trying new spot"
                self.find_parking_spot()
        
        # Check if we need to find a new parking spot
        if self.vehicle.state == "idle" and self.current_attempt < self.max_attempts and not self.status.startswith("Successfully"):
            self.find_parking_spot()
    
    def get_status(self):
        """Get the current status of the simulation."""
        return self.status
    
    def draw(self, screen):
        """Draw the simulation on the screen."""
        # Draw parking spots
        for spot in self.parking_spots:
            pygame.draw.rect(screen, (0, 200, 0), spot["rect"], 2)  # Green rectangles
        
        # Draw obstacles (red cars)
        for obstacle in self.obstacles:
            pygame.draw.rect(screen, (200, 0, 0), obstacle)  # Red rectangles
        
        # Draw active spot with a different color if exists
        if self.active_spot:
            pygame.draw.rect(screen, (0, 255, 0), self.active_spot["rect"], 3)  # Brighter green
        
        # Draw vehicle
        self.vehicle.draw(screen)

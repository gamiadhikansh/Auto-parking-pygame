import pygame
import numpy as np
import heapq
from utils import distance

class PathFinder:
    def __init__(self, width, height, grid_size=20):
        """Initialize the path finder with grid dimensions."""
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.grid_width = width // grid_size
        self.grid_height = height // grid_size
    
    def find_path(self, start, end, obstacles):
        """Find a path from start to end avoiding obstacles using A* algorithm."""
        # Convert start and end to grid coordinates
        start_grid = (int(start[0] / self.grid_size), int(start[1] / self.grid_size))
        end_grid = (int(end[0] / self.grid_size), int(end[1] / self.grid_size))
        
        # Check if start or end are out of bounds
        if not self._is_valid_position(start_grid) or not self._is_valid_position(end_grid):
            return []
        
        # Create an obstacle grid
        obstacle_grid = self._create_obstacle_grid(obstacles)
        
        # Check if start or end points are in obstacles
        if obstacle_grid[start_grid[1]][start_grid[0]] or obstacle_grid[end_grid[1]][end_grid[0]]:
            return []
        
        # A* algorithm
        open_set = []  # Priority queue
        heapq.heappush(open_set, (0, start_grid))  # (priority, position)
        
        came_from = {}  # To reconstruct the path
        g_score = {start_grid: 0}  # Cost from start
        f_score = {start_grid: self._heuristic(start_grid, end_grid)}  # Estimated total cost
        
        open_set_hash = {start_grid}  # For quick membership check
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)
            
            if current == end_grid:
                # Reconstruct path
                path = self._reconstruct_path(came_from, current)
                # Convert back to world coordinates
                return [(x * self.grid_size + self.grid_size // 2, 
                         y * self.grid_size + self.grid_size // 2) for x, y in path]
            
            # Check neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Skip if outside grid or in obstacle
                if not self._is_valid_position(neighbor) or obstacle_grid[neighbor[1]][neighbor[0]]:
                    continue
                
                # Calculate cost (diagonal movement costs more)
                if dx != 0 and dy != 0:
                    tentative_g_score = g_score[current] + 1.414  # sqrt(2)
                else:
                    tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    # This path to neighbor is better than any previous one
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, end_grid)
                    
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        
        # No path found
        return []
    
    def _is_valid_position(self, pos):
        """Check if a grid position is valid."""
        x, y = pos
        return 0 <= x < self.grid_width and 0 <= y < self.grid_height
    
    def _create_obstacle_grid(self, obstacles):
        """Create a grid marking obstacle locations."""
        grid = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        for obstacle in obstacles:
            # Convert obstacle rect to grid coordinates
            left = max(0, obstacle.left // self.grid_size)
            right = min(self.grid_width - 1, obstacle.right // self.grid_size)
            top = max(0, obstacle.top // self.grid_size)
            bottom = min(self.grid_height - 1, obstacle.bottom // self.grid_size)
            
            # Mark cells as obstacles with a safety margin
            margin = 1  # Safety margin in grid cells
            
            for y in range(max(0, top - margin), min(self.grid_height, bottom + margin + 1)):
                for x in range(max(0, left - margin), min(self.grid_width, right + margin + 1)):
                    grid[y][x] = True
        
        return grid
    
    def _heuristic(self, a, b):
        """Calculate heuristic (estimated distance) between two grid positions."""
        # Diagonal distance
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + 0.414 * min(dx, dy)  # Diagonal shortcut
    
    def _reconstruct_path(self, came_from, current):
        """Reconstruct the path from start to end."""
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        
        return list(reversed(total_path))

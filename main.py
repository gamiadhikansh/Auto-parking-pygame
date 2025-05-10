import pygame
import math
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
CAR_LENGTH = 40
CAR_WIDTH = 20

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)

class ParkingType(Enum):
    PARALLEL = 1
    PERPENDICULAR = 2

class CarState(Enum):
    SEARCHING = 1
    PARKING = 2
    PARKED = 3
    FAILED = 4

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.is_hovered = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color if not self.is_hovered else (*self.color[:3], 200), self.rect)
        font = pygame.font.Font(None, 36)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class AutonomousCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.steering_angle = 0
        self.state = CarState.SEARCHING
        self.attempt_count = 0
        self.path_points = []
        self.target_spot = None
        self.failed_spots = []  # Keep track of failed parking spots
        self.approach_side = 'right'  # Track which side to approach from
        self.last_route = None  # Store the last attempted route

    def reset_position(self):
        self.x = 100
        self.y = WINDOW_HEIGHT//2
        self.angle = 0
        self.path_points = []
        # Alternate approach side after each failure
        self.approach_side = 'left' if self.approach_side == 'right' else 'right'
        
    def move(self):
        if self.state == CarState.SEARCHING or self.state == CarState.PARKING:
            self.x += math.cos(math.radians(self.angle)) * self.speed
            self.y -= math.sin(math.radians(self.angle)) * self.speed
            self.angle += self.steering_angle
            self.path_points.append((self.x, self.y))

    def draw(self, screen):
        # Draw path
        if len(self.path_points) > 1:
            pygame.draw.lines(screen, BLUE, False, self.path_points, 2)

        # Draw car body
        car_surface = pygame.Surface((CAR_LENGTH, CAR_WIDTH), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, GREEN if self.state == CarState.PARKED else YELLOW, 
                        (0, 0, CAR_LENGTH, CAR_WIDTH))
        
        # Rotate and position the car
        rotated_surface = pygame.transform.rotate(car_surface, self.angle)
        screen.blit(rotated_surface, (self.x - rotated_surface.get_width()/2,
                                    self.y - rotated_surface.get_height()/2))

class ParkingSimulation:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Autonomous Parking Simulation")
        
        self.car = AutonomousCar(100, WINDOW_HEIGHT//2)
        self.parking_spots = self.generate_parking_spots()
        self.parked_cars = self.generate_parked_cars()
        
        # Create buttons
        self.start_button = Button(50, 50, 100, 40, "Start", GREEN)
        self.pause_button = Button(170, 50, 100, 40, "Pause", YELLOW)
        self.reset_button = Button(290, 50, 100, 40, "Reset", RED)
        
        self.running = True
        self.paused = True
        self.clock = pygame.time.Clock()

    def generate_parking_spots(self):
        spots = []
        
        # Generate parallel parking spots on the right side
        for i in range(5):  # Increased from 3 to 5
            spots.append({
                'rect': pygame.Rect(800, 100 + i * 120, CAR_LENGTH + 20, CAR_WIDTH + 20),
                'type': ParkingType.PARALLEL
            })
            
        # Generate parallel parking spots on the left side
        for i in range(5):  # Added left side parallel spots
            spots.append({
                'rect': pygame.Rect(200, 100 + i * 120, CAR_LENGTH + 20, CAR_WIDTH + 20),
                'type': ParkingType.PARALLEL
            })
        
        # Generate perpendicular parking spots at the bottom
        for i in range(8):  # Increased from 4 to 8
            spots.append({
                'rect': pygame.Rect(300 + i * 80, 600, CAR_WIDTH + 20, CAR_LENGTH + 20),
                'type': ParkingType.PERPENDICULAR
            })
            
        # Generate perpendicular parking spots at the top
        for i in range(8):  # Added top perpendicular spots
            spots.append({
                'rect': pygame.Rect(300 + i * 80, 100, CAR_WIDTH + 20, CAR_LENGTH + 20),
                'type': ParkingType.PERPENDICULAR
            })
            
        return spots

    def generate_parked_cars(self):
        parked_cars = []
        available_spots = self.parking_spots.copy()
        
        # Randomly occupy 60-80% of parking spots
        num_spots_to_occupy = random.randint(
            int(len(self.parking_spots) * 0.6),
            int(len(self.parking_spots) * 0.8)
        )
        
        # Randomly select spots to occupy
        occupied_spots = random.sample(available_spots, num_spots_to_occupy)
        
        for spot in occupied_spots:
            parked_cars.append({
                'rect': spot['rect'],
                'type': spot['type']
            })
            
        return parked_cars

    def find_nearest_parking_spot(self):
        available_spots = []
        
        for spot in self.parking_spots:
            # Skip if spot is occupied or was previously failed
            if any(car['rect'] == spot['rect'] for car in self.parked_cars) or \
               spot in self.car.failed_spots:
                continue
            
            distance = math.sqrt((self.car.x - spot['rect'].centerx)**2 + 
                               (self.car.y - spot['rect'].centery)**2)
            available_spots.append((spot, distance))
        
        if not available_spots:
            return None
            
        # Sort spots by distance
        available_spots.sort(key=lambda x: x[1])
        
        # Choose a different spot based on attempt count
        spot_index = min(self.car.attempt_count, len(available_spots) - 1)
        return available_spots[spot_index][0]

    def check_collision(self):
        car_rect = pygame.Rect(self.car.x - CAR_WIDTH/2, self.car.y - CAR_LENGTH/2,
                              CAR_WIDTH, CAR_LENGTH)
        
        # Check collision with parked cars
        for parked_car in self.parked_cars:
            if car_rect.colliderect(parked_car['rect']):
                return True
        
        # Check collision with boundaries
        if (self.car.x < 0 or self.car.x > WINDOW_WIDTH or 
            self.car.y < 0 or self.car.y > WINDOW_HEIGHT):
            return True
            
        return False

    def reset_simulation(self):
        self.car = AutonomousCar(100, WINDOW_HEIGHT//2)
        self.paused = True
        self.parking_spots = self.generate_parking_spots()
        self.parked_cars = self.generate_parked_cars()

    def generate_approach_path(self, target_spot):
        """Generate different approach paths based on parking type and previous failures"""
        if target_spot['type'] == ParkingType.PARALLEL:
            # For parallel parking, generate different approach angles
            if self.car.approach_side == 'right':
                return {'approach_x': target_spot['rect'].x - 100,
                       'approach_y': target_spot['rect'].y - 50,
                       'final_angle': 0}
            else:
                return {'approach_x': target_spot['rect'].x - 100,
                       'approach_y': target_spot['rect'].y + 50,
                       'final_angle': 0}
        else:
            # For perpendicular parking, try different approach distances
            offset = 150 if self.car.attempt_count % 2 == 0 else 200
            return {'approach_x': target_spot['rect'].x - offset,
                   'approach_y': target_spot['rect'].y,
                   'final_angle': 90}

    def parallel_parking_movement(self):
        target = self.car.target_spot['rect']
        approach_path = self.generate_approach_path(self.car.target_spot)
        
        # Phase 1: Approach the parking spot
        if not hasattr(self, 'parking_phase'):
            self.parking_phase = 1
            
        if self.parking_phase == 1:
            dx = approach_path['approach_x'] - self.car.x
            dy = approach_path['approach_y'] - self.car.y
            
            if abs(dx) > 5 or abs(dy) > 5:
                angle_to_target = math.degrees(math.atan2(-dy, dx))
                angle_diff = (angle_to_target - self.car.angle) % 360
                
                self.car.speed = 2
                self.car.steering_angle = min(max(angle_diff * 0.1, -3), 3)
            else:
                self.parking_phase = 2
                
        # Phase 2: Execute parking maneuver
        elif self.parking_phase == 2:
            dx = target.centerx - self.car.x
            dy = target.centery - self.car.y
            
            if abs(dx) > 5 or abs(dy) > 5:
                # Add more complex parking logic here
                angle_to_target = math.degrees(math.atan2(-dy, dx))
                angle_diff = (angle_to_target - self.car.angle) % 360
                
                self.car.speed = 1  # Slower speed during actual parking
                self.car.steering_angle = min(max(angle_diff * 0.15, -5), 5)
            else:
                self.car.state = CarState.PARKED
                self.car.speed = 0
                self.car.steering_angle = 0
                self.parking_phase = 1  # Reset for next attempt

    def perpendicular_parking_movement(self):
        target = self.car.target_spot['rect']
        approach_path = self.generate_approach_path(self.car.target_spot)
        
        if not hasattr(self, 'parking_phase'):
            self.parking_phase = 1
            
        if self.parking_phase == 1:
            # Approach phase
            dx = approach_path['approach_x'] - self.car.x
            dy = approach_path['approach_y'] - self.car.y
            
            if abs(dx) > 5 or abs(dy) > 5:
                angle_to_target = math.degrees(math.atan2(-dy, dx))
                angle_diff = (angle_to_target - self.car.angle) % 360
                
                self.car.speed = 2
                self.car.steering_angle = min(max(angle_diff * 0.1, -3), 3)
            else:
                self.parking_phase = 2
                
        elif self.parking_phase == 2:
            # Final parking phase
            dx = target.centerx - self.car.x
            dy = target.centery - self.car.y
            
            if abs(dx) > 5 or abs(dy) > 5:
                angle_to_target = math.degrees(math.atan2(-dy, dx))
                angle_diff = (angle_to_target - self.car.angle) % 360
                
                self.car.speed = 1
                self.car.steering_angle = min(max(angle_diff * 0.15, -5), 5)
            else:
                self.car.state = CarState.PARKED
                self.car.speed = 0
                self.car.steering_angle = 0
                self.parking_phase = 1  # Reset for next attempt

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Handle button events
                if self.start_button.handle_event(event):
                    self.paused = False
                elif self.pause_button.handle_event(event):
                    self.paused = True
                elif self.reset_button.handle_event(event):
                    self.reset_simulation()

            if not self.paused:
                if self.car.state == CarState.SEARCHING:
                    # Find nearest parking spot
                    target_spot = self.find_nearest_parking_spot()
                    if target_spot:
                        self.car.target_spot = target_spot
                        self.car.state = CarState.PARKING
                    elif self.car.attempt_count >= 3:
                        self.car.state = CarState.FAILED
                    else:
                        self.car.attempt_count += 1
                        if self.car.target_spot:
                            self.car.failed_spots.append(self.car.target_spot)
                        self.car.reset_position()

                elif self.car.state == CarState.PARKING:
                    if self.car.target_spot['type'] == ParkingType.PARALLEL:
                        self.parallel_parking_movement()
                    else:
                        self.perpendicular_parking_movement()

                # Update car position
                self.car.move()
                
                # Check for collisions
                if self.check_collision():
                    if self.car.target_spot:
                        self.car.failed_spots.append(self.car.target_spot)
                    self.car.state = CarState.SEARCHING
                    self.car.attempt_count += 1
                    self.car.reset_position()
                    if hasattr(self, 'parking_phase'):
                        self.parking_phase = 1

            # Draw everything
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(60)

    def draw(self):
        # Clear screen
        self.screen.fill(WHITE)
        
        # Draw parking spots
        for spot in self.parking_spots:
            pygame.draw.rect(self.screen, GREEN, spot['rect'], 2)
        
        # Draw parked cars (obstacles)
        for car in self.parked_cars:
            pygame.draw.rect(self.screen, RED, car['rect'])
        
        # Draw autonomous car
        self.car.draw(self.screen)
        
        # Draw buttons
        self.start_button.draw(self.screen)
        self.pause_button.draw(self.screen)
        self.reset_button.draw(self.screen)
        
        # Draw status
        font = pygame.font.Font(None, 36)
        status_text = f"Status: {self.car.state.name}"
        attempts_text = f"Attempts: {self.car.attempt_count}/3"
        
        status_surface = font.render(status_text, True, BLACK)
        attempts_surface = font.render(attempts_text, True, BLACK)
        
        self.screen.blit(status_surface, (50, 100))
        self.screen.blit(attempts_surface, (50, 140))
        
        # Update display
        pygame.display.flip()

if __name__ == "__main__":
    simulation = ParkingSimulation()
    simulation.run()
    pygame.quit()

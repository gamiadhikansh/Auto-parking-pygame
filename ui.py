import pygame

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        """Initialize a button with position, size, text, and colors."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.SysFont('Arial', 20)
        self.text_surface = self.font.render(text, True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
    
    def draw(self, screen):
        """Draw the button on the screen."""
        # Check if mouse is hovering over button
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color
        
        # Draw button
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=5)  # Border
        screen.blit(self.text_surface, self.text_rect)
    
    def is_clicked(self, mouse_pos):
        """Check if the button is clicked."""
        return self.rect.collidepoint(mouse_pos)

def draw_text(screen, text, position, size=24, color=(0, 0, 0)):
    """Draw text on the screen."""
    font = pygame.font.SysFont('Arial', size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.topleft = position
    screen.blit(text_surface, text_rect)

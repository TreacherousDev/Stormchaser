import pygame

# Base Button Class
class Button:
    def __init__(self, text, x, y, width, height, font, color, text_color):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.color = color
        self.text_color = text_color

    def draw(self, screen):
        """Draw the button on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        screen.blit(text_surface, (self.rect.centerx - text_surface.get_width() // 2, 
                                   self.rect.centery - text_surface.get_height() // 2))

    def is_clicked(self, mouse_pos):
        """Check if the button is clicked."""
        return self.rect.collidepoint(mouse_pos)

# Toggleable Button Class that inherits from Button
class ToggleableButton(Button):
    def __init__(self, text, x, y, width, height, font, color, text_color, is_playing=False):
        # Initialize the base class with common attributes
        super().__init__(text, x, y, width, height, font, color, text_color)
        self.is_playing = is_playing  # State to track if playing or paused

    def toggle(self):
        """Toggle the button between Play and Pause."""
        self.is_playing = not self.is_playing
        self.text = "PAUSE" if self.is_playing else "PLAY"

    def draw(self, screen):
        """Override draw method to include play/pause logic."""
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        screen.blit(text_surface, (self.rect.centerx - text_surface.get_width() // 2, 
                                   self.rect.centery - text_surface.get_height() // 2))
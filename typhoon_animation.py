import pygame
import math
import typhoon_scraper as ty
from datetime import datetime, timedelta
import western_pacific_map_maker as mapmaker
from map_image_processor import MapImageProcessor


def initialize_dataset():
    min_month = 10
    min_day = 13
    year=2024
    global typhoons, earliest_time
    typhoons = ty.scrape_typhoon_data(year=year, min_date=datetime(year,min_month,min_day))
    # Parse the `time` strings into datetime objects and calculate start times
    earliest_time = min(
        datetime.strptime(point['time'], '%Y-%m-%d %H:%M')
        for typhoon in typhoons
        for point in typhoon['path'])

    for typhoon in typhoons:
        first_time = datetime.strptime(typhoon['path'][0]['time'], '%Y-%m-%d %H:%M')
        # Set `start_time` as the offset in milliseconds from the current time
        typhoon['start_time'] = int(((first_time - earliest_time).total_seconds() * time_scale_factor) * 1000)
        print(typhoon['name'], typhoon['start_time'])
   

# Map latitude and longitude to screen coordinates
def latlon_to_screen(lat, lon):
    screen_x = int((lon - 100) * (width / 70))  # Longitude scaling
    screen_y = int((40 - lat) * (height / 50))  # Latitude scaling
    return screen_x, screen_y



class Typhoon:
    def __init__(self, name, path, start_time, category_colors, fade_in_duration=1, fade_out_duration=0.5):
        self.name = name
        self.path = path
        self.start_time = start_time
        self.category_colors = category_colors
        self.fade_in_duration = fade_in_duration
        self.fade_out_duration = fade_out_duration

        self.current_step = 0
        self.current_position = {'lat': path[0]['lat'], 'long': path[0]['long']}
        self.alpha = 0
        self.active = True
        self.blade_angle = 0
        self.current_color = (0, 0, 0, 0)  # Start fully transparent
        self.is_in_water = True
        self.landfall_crosses = []  # To store landfall crosses with a timer

        # Font for rendering the typhoon name, wind speed, and pressure
        self.font = pygame.font.Font(None, 24)  # Default font with size 24

    def check_for_landfall(self, img):
        if img:
            screen_position = latlon_to_screen(self.current_position['lat'], self.current_position['long'])
            coordinate_color = MapImageProcessor.is_color_at_coordinate(
                img, screen_position[0], screen_position[1], (0, 0, 70)
            )
            if self.is_in_water != coordinate_color and self.is_in_water:
                # Add a cross at the landfall position with initial animation properties
                self.landfall_crosses.append({
                    "position": screen_position,
                    "scale": 10.0,  # Start with a large scale for zoom-in animation
                    "fade_alpha": 255  # Fully opaque initially
                })
            self.is_in_water = coordinate_color
            
    def update_landfall_crosses(self, dt):
        """Update the animation properties of landfall crosses."""
        for cross in self.landfall_crosses:
            # Zoom-in effect: reduce the scale over time
            if cross["scale"] > 1.0:
                cross["scale"] = max(cross["scale"] - 20.0 * dt, 1.0)  # Shrink to normal size

            # Start fading only when the typhoon begins to fade
            cross["fade_alpha"] = self.alpha

        # Remove crosses that are fully transparent
        self.landfall_crosses = [cross for cross in self.landfall_crosses if cross["fade_alpha"] > 0]
        
    def draw_landfall_crosses(self, screen):
        """Draw all landfall crosses with transparency as diagonal X marks."""
        for cross in self.landfall_crosses:
            # Create a transparent surface
            cross_surface_size = int(50 * cross["scale"])  # Size depends on the scale
            cross_surface = pygame.Surface((cross_surface_size, cross_surface_size), pygame.SRCALPHA)

            # Set up the cross's color with transparency
            color = (255, 0, 0, int(cross["fade_alpha"]))  # Red with transparency

            # Draw the diagonal cross (X) on the transparent surface
            center = cross_surface_size // 2
            line_length = int(6 * cross["scale"])  # Scale the line length
            pygame.draw.line(cross_surface, color, 
                            (center - line_length, center - line_length), 
                            (center + line_length, center + line_length), 3)  # Top-left to bottom-right
            pygame.draw.line(cross_surface, color, 
                            (center - line_length, center + line_length), 
                            (center + line_length, center - line_length), 3)  # Bottom-left to top-right

            # Blit the cross surface onto the main screen at the correct position
            cross_x, cross_y = cross["position"]
            screen.blit(cross_surface, (cross_x - center, cross_y - center))

    def distance(self, point1, point2):
        """Calculate the distance between two points."""
        return math.sqrt((point2['lat'] - point1['lat'])**2 + (point2['long'] - point1['long'])**2)

    def move_constant_speed(self, point1, point2, duration, dt):
        """Move at a constant speed between two points."""
        total_distance = self.distance(point1, point2)
        if total_distance == 0:  # Avoid division by zero
            return point2

        # Calculate the required speed to cover the total distance in the given duration
        speed = total_distance / duration

        # Calculate the direction vector (unit vector)
        direction_lat = (point2['lat'] - point1['lat']) / total_distance
        direction_long = (point2['long'] - point1['long']) / total_distance

        # Calculate the distance to move this frame
        move_distance = speed * dt
        new_lat = self.current_position['lat'] + direction_lat * move_distance
        new_long = self.current_position['long'] + direction_long * move_distance

        # Check if the new position exceeds the target
        if self.distance(point1, {'lat': new_lat, 'long': new_long}) >= total_distance:
            return point2  # Snap to the target point
        return {'lat': new_lat, 'long': new_long}

    def create_blade_surface(self, color_with_alpha, num_blades=6, base_radius=11, spiral_factor=11, blade_length=35):
        surface_size = 2 * (base_radius + spiral_factor * math.log1p(blade_length))
        blade_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        x, y = surface_size // 2, surface_size // 2  # Center of the surface
        angle_step = math.pi * 2 / num_blades

        for i in range(num_blades):
            blade_angle = angle_step * i
            points = []
            for t in range(1, blade_length + 1):
                radius = base_radius + spiral_factor * math.log1p(t)
                x_end = x + math.cos(blade_angle + t / spiral_factor) * radius
                y_end = y + math.sin(blade_angle + t / spiral_factor) * radius
                points.append((x_end, y_end))
            if len(points) > 1:
                pygame.draw.lines(blade_surface, color_with_alpha, False, points, 5)
        return blade_surface.convert_alpha()

    def create_center_dot_surface(self, color_with_alpha):
        dot_radius = 6
        dot_surface = pygame.Surface((dot_radius * 2, dot_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot_surface, color_with_alpha, (dot_radius, dot_radius), dot_radius)
        return dot_surface.convert_alpha()

    def update(self, elapsed_time, dt):
        """Update typhoon and storm animation."""
        self.update_landfall_crosses(dt)
        if elapsed_time < self.start_time:
            return
        if self.current_step >= len(self.path) - 1:
            if self.alpha > 0:
                self.alpha = max(self.alpha - (255 / self.fade_out_duration) * dt, 0)
                self.current_color = (*self.current_color[:3], int(self.alpha))
            else:
                self.active = False
            return

        # Update position
        point1 = self.path[self.current_step]
        point2 = self.path[self.current_step + 1]
        time_diff = (datetime.strptime(point2['time'], '%Y-%m-%d %H:%M') - 
                     datetime.strptime(point1['time'], '%Y-%m-%d %H:%M')).total_seconds() / 3600
        animation_duration = time_diff * time_scale_factor * 3600
        self.current_position = self.move_constant_speed(point1, point2, animation_duration, dt)

        # Fade in
        if self.alpha < 255:
            self.alpha = min(self.alpha + (255 / self.fade_in_duration) * dt, 255)

        # Update color blending
        target_color = self.category_colors.get(point2['class'], (0, 0, 0))
        blend_speed = 4
        self.current_color = tuple(
            int(self.current_color[i] + (target_color[i] - self.current_color[i]) * blend_speed * dt)
            for i in range(3)
        ) + (int(self.alpha),)

        # Update to the next step if at the target
        if self.current_position == point2:
            self.current_step += 1
        
        self.check_for_landfall(img)
        

    def draw(self, screen):
        if self.alpha > 0:
            screen_x, screen_y = latlon_to_screen(self.current_position['lat'], self.current_position['long'])
            # Dynamically regenerate surfaces with current color and alpha
            blade_surface = self.create_blade_surface(self.current_color)
            center_dot = self.create_center_dot_surface(self.current_color)
            rotated_blade = pygame.transform.rotate(blade_surface, self.blade_angle)

            # Compute the blit position to center the rotated image
            blade_rect = rotated_blade.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated_blade, blade_rect.topleft)

            # Blit the center dot
            dot_rect = center_dot.get_rect(center=(screen_x, screen_y))
            screen.blit(center_dot, dot_rect.topleft)

            # Get wind speed and pressure at the current point in the path
            wind_speed = self.path[self.current_step].get('speed', 'N/A')
            pressure = self.path[self.current_step].get('pressure', 'N/A')

            # Render and blit the typhoon's name below the typhoon center
            name_surface = self.font.render(self.name, True, (255, 255, 255))  # White text
            name_rect = name_surface.get_rect(center=(screen_x, screen_y + 60))  # 20 pixels below the typhoon center
            screen.blit(name_surface, name_rect.topleft)

            # Render and blit wind speed below the name
            wind_speed_surface = self.font.render(f"{wind_speed} km/h", True, (255, 255, 255))
            wind_speed_rect = wind_speed_surface.get_rect(center=(screen_x, screen_y + 80))  # 20 pixels below the name
            screen.blit(wind_speed_surface, wind_speed_rect.topleft)

            # Render and blit pressure below the wind speed
            pressure_surface = self.font.render(f"{pressure} hPa", True, (255, 255, 255))
            pressure_rect = pressure_surface.get_rect(center=(screen_x, screen_y + 100))  # 20 pixels below the wind speed
            screen.blit(pressure_surface, pressure_rect.topleft)

            self.blade_angle += 2

        # Draw landfall crosses
        self.draw_landfall_crosses(screen)


# Play Button Class
class Button:
    def __init__(self, text, x, y, width, height, font, color, text_color):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.color = color
        self.text_color = text_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        screen.blit(text_surface, (self.rect.centerx - text_surface.get_width() // 2, 
                                   self.rect.centery - text_surface.get_height() // 2))

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
    

# Main Animation Function
def animate_typhoons():
    clock = pygame.time.Clock()

    # Create Typhoon objects
    typhoon_objects = [
        Typhoon(typhoon['name'], typhoon['path'], typhoon['start_time'], category_colors)
        for typhoon in typhoons
    ]

    running = True
    game_started = False
    start_ticks = pygame.time.get_ticks()
    elapsed_time = 0
    # Create play button
    font = pygame.font.SysFont(None, 30)
    # Define button dimensions and position for bottom-left corner
    button_width, button_height = 100, 50
    screen_width, screen_height = screen.get_size()

    # Position the button in the bottom-left corner with 10px margin
    button_x = 10  # 10px margin from the left edge
    button_y = screen_height - button_height - 10  # 10px margin from the bottom edge

    # Create the play button with the new position
    play_button = Button("Play", button_x, button_y, button_width, button_height, font, (70, 130, 180), (255, 255, 255))

    
    while running:
        screen.fill((255, 255, 255))
        screen.blit(map_image, (0, 0))  # Draw the map once
        play_button.draw(screen)
        fps = clock.get_fps()
        fps_text = font.render(f"FPS: {fps:.2f}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if play button is clicked
                if play_button.is_clicked(event.pos):
                    game_started = True
                    start_ticks = pygame.time.get_ticks()
        
         # Update and draw typhoons
        
        dt = clock.tick(120) / 1000.0  # Time delta in seconds
        if game_started:
            # Calculate the current time being played
            elapsed_time = pygame.time.get_ticks() - start_ticks
            current_play_time = earliest_time + timedelta(seconds=(elapsed_time/1000) * 43200)

            # Format the time in a readable format (e.g., YYYY-MM-DD HH:MM)
            formatted_time = current_play_time.strftime('%Y-%m-%d %H:%M')

            # Render the current time at the bottom-right of the screen
            current_time_text = font.render(f"Current Time: {formatted_time}", True, (255, 255, 255))
            screen.blit(current_time_text, (screen_width - current_time_text.get_width() - 10, screen_height - current_time_text.get_height() - 10))

            elapsed_time = pygame.time.get_ticks() - start_ticks

            for typhoon in typhoon_objects:
                typhoon.update(elapsed_time, dt)
                typhoon.draw(screen)

        # Refresh display
        pygame.display.flip()

    pygame.quit()




typhoons = None
earliest_time = None
time_scale_factor = 1 / (12 * 60 * 60)  # 1 second per 12 hours in real-time 

screen_width, screen_height = 1400, 1000
image_path = "simple_western_pacific_map.png"  # Path to your image
img = MapImageProcessor.load_image(image_path)

# Initialize Pygame
pygame.init()
width, height = 1400, 1000
screen = pygame.display.set_mode((width, height), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("PROJECT STORMCHASER")
# Load map background
map_image = pygame.image.load(mapmaker.create_western_pacific_map()).convert()
# Scale the map to fit the window size while maintaining the aspect ratio
map_width, map_height = map_image.get_size()
aspect_ratio = map_width / map_height
new_width = width
new_height = int(new_width / aspect_ratio)

if new_height > height:
    new_height = height
    new_width = int(new_height * aspect_ratio)
map_image = pygame.transform.scale(map_image, (new_width, new_height))


category_colors = {
    0: (135, 206, 235),
    1: (100, 238, 100),  # Light Green (Calm Green)
    2: (225, 225, 0),    # Bright Yellow
    3: (255, 130, 0),    # Orange
    4: (255, 0, 0),     # Red
    5: (180, 0, 180)   
}


if __name__ == "__main__":
    # Start the animation
    initialize_dataset()
    animate_typhoons()

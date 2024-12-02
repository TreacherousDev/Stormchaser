import pygame
import math
from math import radians, tan, log, pi
from datetime import datetime
from map_image_processor import MapImageProcessor

class Typhoon:
    def __init__(self, name, path, start_time, category_colors, screen_width, screen_height, time_scale_factor, reference_map, basin, fade_in_duration=1, fade_out_duration=0.5, ):
        self.name = name
        self.path = path
        self.start_time = start_time
        self.category_colors = category_colors
        self.fade_in_duration = fade_in_duration
        self.fade_out_duration = fade_out_duration
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.time_scale_factor = time_scale_factor
        self.reference_map = reference_map
        self.basin = basin
        self.basin_boundaries = {
            "western_pacific": [100, 180, 0, 60],
            "northern_atlantic": [-100, -20, 0, 60],
            "eastern_pacific": [-175, -95, 0, 60],
            "northern_indian": [40, 100, -10, 35],
            "southern_indian": [20, 120, -75, 0]
        }

        self.current_step = 0
        self.current_position = {'lat': path[0]['lat'], 'long': path[0]['long']}
        self.alpha = 0
        self.active = True
        self.blade_angle = 0
        self.current_color = (0, 0, 0, 0)  # Start fully transparent
        self.is_in_water = True
        self.landfall_crosses = []  # To store landfall crosses with a timer

        # Font for rendering the typhoon name, wind speed, and pressure
        self.font = pygame.font.Font(None, 20)  # Default font with size 24


    def latlon_to_screen(self, lat, lon):
        """
        Convert latitude and longitude to screen coordinates using the Plate Carrée projection.
        Maps directly to the linear grid of the Plate Carrée background map.
        """
        if self.basin not in self.basin_boundaries:
            raise ValueError(f"Unknown basin: {self.basin}")

        # Get basin boundaries
        min_lon, max_lon, min_lat, max_lat = self.basin_boundaries[self.basin]

        # Longitude (x-axis) - linear mapping
        lon_range = max_lon - min_lon
        screen_x = int((lon - min_lon) * (self.screen_width / lon_range))

        # Latitude (y-axis) - linear mapping
        lat_range = max_lat - min_lat
        screen_y = int((max_lat - lat) * (self.screen_height / lat_range))

        return screen_x, screen_y


        
    def check_for_landfall(self, img):
        if img:
            screen_position = self.latlon_to_screen(self.current_position['lat'], self.current_position['long'])
            coordinate_color = MapImageProcessor.is_color_at_coordinate(
                img, screen_position[0], screen_position[1], (0, 0, 70)
            )
            if self.is_in_water != coordinate_color and self.is_in_water:
                # Add a cross at the landfall position with initial animation properties
                self.landfall_crosses.append({
                    "position": screen_position,
                    "scale": 30.0,  # Start with a large scale for zoom-in animation
                    "fade_alpha": 255  # Fully opaque initially
                })
            self.is_in_water = coordinate_color
            
    def update_landfall_crosses(self, dt):
        """Update the animation properties of landfall crosses."""
        for cross in self.landfall_crosses:
            # Zoom-in effect: reduce the scale over time
            if cross["scale"] > 1.0:
                cross["scale"] = max(cross["scale"] - 80.0 * dt, 1.0)  # Shrink to normal size

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
            line_length = int(4.5 * cross["scale"])  # Scale the line length
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

    def create_blade_surface(self, color_with_alpha, num_blades=6, base_radius=8, spiral_factor=10, blade_length=32):
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
        dot_radius = 5
        dot_surface = pygame.Surface((dot_radius * 2, dot_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot_surface, color_with_alpha, (dot_radius, dot_radius), dot_radius)
        return dot_surface.convert_alpha()

    def update(self, elapsed_time, dt):
        """Update typhoon and storm animation."""
        self.update_landfall_crosses(dt)
        # Does not arrive yet, skip
        if elapsed_time < self.start_time:
            return
        
        # Fade out
        if self.current_step >= len(self.path) - 1:
            if self.alpha > 0:
                self.alpha = max(self.alpha - (255 / self.fade_out_duration) * dt, 0)
                self.current_color = (*self.current_color[:3], int(self.alpha))
            else:
                self.active = False
            return

        self.check_for_landfall(self.reference_map)
        # Update position
        point1 = self.path[self.current_step]
        point2 = self.path[self.current_step + 1]
        time_diff = (datetime.strptime(point2['time'], '%Y-%m-%d %H:%M') - 
                     datetime.strptime(point1['time'], '%Y-%m-%d %H:%M')).total_seconds() / 3600
        animation_duration = time_diff * self.time_scale_factor * 3600
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
        
    def draw(self, screen, dt):
        # Early return for inactive typhoons
        if self.alpha <= 0:
            return
        
        # Draw landfall crosses
        self.draw_landfall_crosses(screen) 
        
        screen_x, screen_y = self.latlon_to_screen(self.current_position['lat'], self.current_position['long'])
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
        name_rect = name_surface.get_rect(center=(screen_x, screen_y + 53))  # 20 pixels below the typhoon center
        screen.blit(name_surface, name_rect.topleft)

        # Render and blit wind speed below the name
        wind_speed_surface = self.font.render(f"{wind_speed} kt", True, (255, 255, 255))
        wind_speed_rect = wind_speed_surface.get_rect(center=(screen_x, screen_y + 64))  # 20 pixels below the name
        screen.blit(wind_speed_surface, wind_speed_rect.topleft)

        # Render and blit pressure below the wind speed
        pressure_surface = self.font.render(f"{pressure} hPa", True, (255, 255, 255))
        pressure_rect = pressure_surface.get_rect(center=(screen_x, screen_y + 75))  # 20 pixels below the wind speed
        screen.blit(pressure_surface, pressure_rect.topleft)

        # Some random normalizing formula that changes the typhooon's rotation speed based on its strength
        typhoon_class = self.path[self.current_step].get('class', '0')
        self.blade_angle += (1.5 + (pow(1 + typhoon_class, 1.7)/8)) * dt * 100
import pygame
import typhoon_scraper as ty
from datetime import datetime, timedelta
import map_maker as mapmaker
from map_image_processor import MapImageProcessor
from typhoon_icon import Typhoon
from buttons import Button, ToggleableButton
import threading
import os
import sys
import time

# Function to get the absolute path to a resource
def get_resource_path(relative_path):
    """ Get the absolute path to a resource, works for both normal and bundled versions. """
    if getattr(sys, 'frozen', False):
        # If the app is frozen (i.e., running as a PyInstaller bundle)
        base_path = sys._MEIPASS  # PyInstaller sets this attribute
    else:
        # If the app is not frozen, just use the script's location
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

# Global variables and constants
typhoons = None
earliest_time = None
loading = False  # Flag to control the loading screen
TIME_SCALE_FACTOR = 1 / (12 * 60 * 60)  # 1 second per 12 hours in real-time 
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 900
# Using get_resource_path to load the image from the resources folder
reference_map = None
BASIN_ABBREVIATIONS = {
    "Northern Atlantic": "na",
    "Eastern Pacific" : "ep",
    "Western Pacific": "wp",
    "Northern Indian": "ni",
    "Southern Indian": "si"
    # "Southern Pacific": "sp"
}
selected_basin = "Western Pacific"

category_colors = {
    0: (135, 206, 235),  # Light Blue
    1: (100, 238, 100),  # Light Green
    2: (225, 225, 0),    # Yellow
    3: (255, 130, 0),    # Orange
    4: (255, 0, 0),      # Red
    5: (255, 0, 255)     # Purple
}

# Function to initialize the dataset based on the start date
def initialize_dataset(screen, screen_width, screen_height, start_date, selected_basin):
    global typhoons, earliest_time, loading
    basin_name = selected_basin.replace("_", " ").title()
    loading = True
    typhoons = []

    # Start scraping typhoon data in a background thread
    def scrape_data():
        global typhoons
        typhoons = ty.scrape_typhoon_data(start_date.year, basin_name)
        
        # Filter typhoons by start date after scraping is done
        if start_date:
            typhoons = filter_typhoons_by_start_date(typhoons, start_date)

        if not typhoons:
            print(f"No typhoons found starting after {start_date}.")
            return

        # Calculate the earliest time across all typhoons
        global earliest_time
        earliest_time = get_earliest_time(typhoons)

        # Set start times for each typhoon relative to the earliest time
        set_typhoon_start_times(typhoons, earliest_time)
        
        # Mark loading as complete
        global loading
        loading = False

    # Create and start the scraping thread
    scrape_thread = threading.Thread(target=scrape_data)
    scrape_thread.start()

    # While the scraping is running, show a loading screen
    while loading:
        screen.fill((0, 0, 0))  # Clear screen with black
        font = pygame.font.SysFont("Arial", 24)
        loading_text = font.render("Loading typhoon data...", True, (255, 255, 255))
        screen.blit(loading_text, (screen_width // 2 - loading_text.get_width() // 2, screen_height // 2 - loading_text.get_height() // 2))
        pygame.display.update()  # Update the screen
        time.sleep(0.1)  # Delay for a short time to prevent 100% CPU usage

    # After scraping is done, proceed with the next steps
    print("Data scraping complete!")
    return typhoons

# Function to filter typhoons based on the start date
def filter_typhoons_by_start_date(typhoons, start_date):
    return [
        typhoon for typhoon in typhoons
        if datetime.strptime(typhoon['path'][0]['time'], '%Y-%m-%d %H:%M') >= start_date
    ]

# Function to get the earliest time from all typhoons
def get_earliest_time(typhoons):
    return min(
        datetime.strptime(point['time'], '%Y-%m-%d %H:%M')
        for typhoon in typhoons
        for point in typhoon['path']
    )

# Function to set start times for each typhoon relative to the earliest time
def set_typhoon_start_times(typhoons, earliest_time):
    for typhoon in typhoons:
        first_time = datetime.strptime(typhoon['path'][0]['time'], '%Y-%m-%d %H:%M')
        typhoon['start_time'] = int(((first_time - earliest_time).total_seconds() * TIME_SCALE_FACTOR) * 1000)
        print(typhoon['name'], typhoon['start_time'])



##########################
# INPUT WINDOW FUNCTIONS #
##########################

def render_input_box(screen, label, x, y, width, height, active, text, font, color_active, color_inactive, label_font):
    color = color_active if active else color_inactive

    # Create a transparent surface for the input box
    input_box_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Draw the input box with rounded corners on the transparent surface
    pygame.draw.rect(input_box_surface, (color[0], color[1], color[2], 150), (0, 0, width, height), 0, border_radius=12)
    screen.blit(input_box_surface, (x, y))  # Blit the transparent input box to the main screen

    # Render the text inside the input box
    text_surface = font.render(text, True, (255, 255, 255))
    text_surface.set_alpha(170)  # Set 50% transparency for the text
    screen.blit(text_surface, (x + 10, y + (height - text_surface.get_height()) // 2))
    
    # Render the label below the textbox
    label_surface = label_font.render(label, True, (255, 255, 255))
    label_surface.set_alpha(200)  # Set 50% transparency for the label
    screen.blit(label_surface, (x + (width - label_surface.get_width()) // 2, y + height + 2))

def render_basin_button(screen, button, x, y, width, height, button_font, button_active_color, button_inactive_color):
    # Choose color based on whether the button is active or not
    color = button_active_color if button["active"] else button_inactive_color
    
    # Create a transparent surface for the button
    button_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Draw the button with rounded corners on the transparent surface
    pygame.draw.rect(button_surface, (color[0], color[1], color[2], 128), (0, 0, width, height), border_radius=5)
    screen.blit(button_surface, (x, y))  # Blit the transparent button to the main screen

    # Render the text inside the button
    button_text = button_font.render(button["label"], True, (51,52,109))
    text_rect = button_text.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(button_text, text_rect)

# Main UI function with updated button rendering
def initialize_input_ui(screen, screen_width, screen_height):
    font = pygame.font.SysFont("Impact", 36)  # Modern font for text input
    label_font = pygame.font.SysFont("Arial", 15, bold=True)  # Smaller font for labels
    title_font = pygame.font.SysFont("Impact", 58)  # Larger font for title
    button_font = pygame.font.SysFont("Impact", 15)  # Font for buttons
    clock = pygame.time.Clock()
    current_map = None
    map_image = pygame.image.load(mapmaker.get_detailed_map_image()).convert()

    def get_map_image(next_map):
        nonlocal map_image, current_map
        # Load map background
        if current_map == next_map:
            return map_image
        
        map_image = pygame.image.load(mapmaker.get_detailed_map_image(next_map)).convert()
        map_width, map_height = map_image.get_size()
        aspect_ratio = map_width / map_height
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)

        if new_height > screen_height:
            new_height = screen_height
            new_width = int(new_height * aspect_ratio)
        map_image = pygame.transform.scale(map_image, (new_width, new_height))
        current_map = next_map
        return map_image

    # Define the width and height of each input box
    input_box_width = 100
    input_box_height = 50
    spacing = 30  # Space between the input boxes

    total_width = (input_box_width * 3) + (spacing * 2)
    start_x = (600 - total_width) // 2

    input_boxes = [
        {"label": "Year", "x": start_x, "y": 200, "width": input_box_width, "height": input_box_height, "active": False, "text": ""},
        {"label": "Month (optional)", "x": start_x + input_box_width + spacing, "y": 200, "width": input_box_width, "height": input_box_height, "active": False, "text": ""},
        {"label": "Day (optional)", "x": start_x + 2 * (input_box_width + spacing), "y": 200, "width": input_box_width, "height": input_box_height, "active": False, "text": ""}
    ]
    
    buttons = [
        {"label": "North Atlantic", "code": "northern_atlantic", "active": False},
        {"label": "East Pacific", "code": "eastern_pacific", "active": False},
        {"label": "West Pacific", "code": "western_pacific", "active": True},  # Set WP to active by default
        {"label": "North Indian", "code": "northern_indian", "active": False},
        {"label": "South Indian", "code": "southern_indian", "active": False}
    ]

    button_width = 105
    button_height = 30
    button_spacing = 10
    button_start_x = (screen_width - (button_width * len(buttons) + button_spacing * (len(buttons) - 1))) // 2
    button_y = 280
    for i, button in enumerate(buttons):
        button["x"] = button_start_x + i * (button_width + button_spacing)
        button["y"] = button_y
        # button["active"] = False

    color_active = pygame.Color("dodgerblue2")
    color_inactive = pygame.Color("lightskyblue3")
    button_active_color = pygame.Color("lawngreen")
    button_inactive_color = pygame.Color("lightgreen")
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None, None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for box in input_boxes:
                    box["active"] = box["x"] < event.pos[0] < box["x"] + box["width"] and box["y"] < event.pos[1] < box["y"] + box["height"]
                for button in buttons:
                    if button["x"] < event.pos[0] < button["x"] + button_width and button["y"] < event.pos[1] < button["y"] + button_height:
                        for b in buttons:
                            b["active"] = False
                        button["active"] = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    done = True
                for box in input_boxes:
                    if box["active"]:
                        if event.key == pygame.K_BACKSPACE:
                            box["text"] = box["text"][:-1]
                        else:
                            box["text"] += event.unicode
                            
        selected_basin = next((button["code"] for button in buttons if button["active"]), None)
        next_map = selected_basin.replace("_", " ").title()
        screen.blit(get_map_image(next_map), (0, 0))

        for box in input_boxes:
            render_input_box(screen, box["label"], box["x"], box["y"], box["width"], box["height"], box["active"], box["text"], font, color_active, color_inactive, label_font)
        
        # Render buttons using the new function
        for button in buttons:
            render_basin_button(screen, button, button["x"], button["y"], button_width, button_height, button_font, button_active_color, button_inactive_color)

        title_text = "PROJECT STORMCHASER"
        main_color = (82,150,63)
        outline_color = (51,52,109)
        title_position = (300 - title_font.size(title_text)[0] // 2, 30)
        render_text_with_outline(title_text, title_font, main_color, outline_color, title_position, screen, 4)
        
        submit_text = font.render("Press Enter to Submit", True, (255, 255, 255))
        submit_text_surface = pygame.Surface(submit_text.get_size(), pygame.SRCALPHA)
        submit_text_surface.blit(submit_text, (0, 0))
        submit_text_surface.set_alpha(200)
        screen.blit(submit_text_surface, (300 - submit_text.get_width() // 2, 400))

        pygame.display.flip()
        clock.tick(30)

    selected_basin = next((button["code"] for button in buttons if button["active"]), None)
    return parse_start_date(input_boxes), selected_basin

# Function to render text with outline
def render_text_with_outline(text, font, color, outline_color, position, screen, outline_offset=2):
    # Render the outline (slightly offset)
    outline_text = font.render(text, True, outline_color)

    # Render the main text
    main_text = font.render(text, True, color)

    # Get the position of the text
    x, y = position

    # Blit the outline text at offset positions
    screen.blit(outline_text, (x - outline_offset, y - outline_offset))  # Top-left offset
    screen.blit(outline_text, (x + outline_offset, y - outline_offset))  # Top-right offset
    screen.blit(outline_text, (x - outline_offset, y + outline_offset))  # Bottom-left offset
    screen.blit(outline_text, (x + outline_offset, y + outline_offset))  # Bottom-right offset

    # Finally, blit the main text on top
    screen.blit(main_text, (x, y))


def parse_start_date(input_boxes):
    year = input_boxes[0]["text"]
    month = input_boxes[1]["text"] if input_boxes[1]["text"] else "1"
    day = input_boxes[2]["text"] if input_boxes[2]["text"] else "1"

    try:
        start_date = datetime(int(year), int(month), int(day))
        
        # Get the current year
        current_year = datetime.now().year
        
        # Check if the entered year is before 1951
        if start_date.year < 1951:
            print("Date must be after 1951. Please enter a valid date.")
            return None
        
        # Check if the entered year is greater than the current year
        if start_date.year > current_year:
            print(f"Date cannot be in the future. Please enter a valid date before {current_year}.")
            return None
        
        return start_date
    except ValueError:
        print("Invalid date input. Please restart and enter a valid date.")
        return None


###########################
# Main Animation Function #
###########################
def animate_typhoons(year, basin):
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("PROJECT STORMCHASER")

    # Generate file paths for the maps dynamically based on the basin parameter
    detailed_map_filename = f"../resources/{basin}_detailed_map.png"
    simple_map_filename = f"../resources/{basin}_simple_map.png"

    # Load reference map and detailed map
    reference_map = MapImageProcessor.load_image(get_resource_path(simple_map_filename))
    map_image = pygame.image.load(get_resource_path(detailed_map_filename)).convert()

    # Scale the map to fit the window size while maintaining the aspect ratio
    map_width, map_height = map_image.get_size()
    aspect_ratio = map_width / map_height
    new_width = SCREEN_WIDTH
    new_height = int(new_width / aspect_ratio)

    if new_height > SCREEN_HEIGHT:
        new_height = SCREEN_HEIGHT
        new_width = int(new_height * aspect_ratio)
    map_image = pygame.transform.scale(map_image, (new_width, new_height))

    clock = pygame.time.Clock()
    
    # Create Typhoon objects
    typhoon_objects = [
        Typhoon(typhoon['name'], typhoon['path'], typhoon['start_time'], category_colors, SCREEN_WIDTH, SCREEN_HEIGHT, TIME_SCALE_FACTOR, reference_map, basin)
        for typhoon in typhoons
    ]

    running = True
    start_ticks = pygame.time.get_ticks()
    elapsed_time = 0
    skip_time = 0

    # Create buttons
    font = pygame.font.SysFont(None, 30)
    button_height = 50
    screen_width, screen_height = screen.get_size()
    
    # Play button positioning
    play_button_width = 100
    play_button_x = 10
    play_button_y = button_height - 40
    
    # Skip button positioning
    skip_button_width = 140
    skip_button_x = play_button_x + play_button_width + 10
    skip_button_y = play_button_y
    
    # Back to Menu button positioning
    back_button_width = 200
    back_button_x = skip_button_x + skip_button_width + 10
    back_button_y = play_button_y

    # Initialize buttons
    play_button = ToggleableButton("PLAY", play_button_x, play_button_y, play_button_width, button_height, font, (70, 130, 180), (255, 255, 255), is_playing=False)
    skip_button = Button(">> 1 WEEK", skip_button_x, skip_button_y, skip_button_width, button_height, font, (70, 130, 180), (255, 255, 255))
    back_button = Button("BACK TO MENU", back_button_x, back_button_y, back_button_width, button_height, font, (200, 50, 50), (255, 255, 255))

    formatted_time = earliest_time.strftime('%Y-%m-%d %H:%M')
    
    while running:
        screen.fill((255, 255, 255))
        screen.blit(map_image, (0, 0))  # Draw the map once
        play_button.draw(screen)
        skip_button.draw(screen)
        back_button.draw(screen)
        
        fps = clock.get_fps()
        fps_text = font.render(f"FPS: {fps:.2f}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 70))
        
        # Extract the current year from current_play_time
        if play_button.is_playing:
            current_play_time = earliest_time + timedelta(seconds=(elapsed_time / 1000) / TIME_SCALE_FACTOR)
            current_year = current_play_time.year
            
            # Stop the clock if the current year exceeds the year passed to animate_typhoons
            if current_year > year:
                play_button.is_playing = False  # Pause the simulation

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if play/pause button is clicked
                if play_button.is_clicked(event.pos):
                    play_button.toggle()
                    if play_button.is_playing:
                        start_ticks = pygame.time.get_ticks() - elapsed_time
                # Check if skip button is clicked
                elif skip_button.is_clicked(event.pos):
                    start_ticks -= 7 * 24 * 60 * 60 * 1000 * TIME_SCALE_FACTOR  # Convert days to milliseconds
                # Check if back button is clicked
                elif back_button.is_clicked(event.pos):
                    running = False  # Exit the loop and return to main

        # Update and draw typhoons only if not paused
        if play_button.is_playing:
            elapsed_time = pygame.time.get_ticks() + skip_time - start_ticks
            current_play_time = earliest_time + timedelta(seconds=(elapsed_time / 1000) / TIME_SCALE_FACTOR)
            
            for typhoon in typhoon_objects:
                typhoon.update(elapsed_time, clock.get_time() / 1000.0)

        if play_button.is_playing:
            formatted_time = current_play_time.strftime('%Y-%m-%d %H:%M')

        # Render the current time at the bottom-right of the screen
        current_time_text = font.render(f"Current Time: {formatted_time}", True, (255, 255, 255))
        screen.blit(current_time_text, (screen_width - current_time_text.get_width() - 10, screen_height - current_time_text.get_height() - 10))

        for typhoon in typhoon_objects:
            typhoon.draw(screen, clock.get_time() / 1000.0)

        # Refresh display
        pygame.display.flip()
        clock.tick(60)

    # Return to the main menu after exiting the loop
    main()

# Main function to run the program
def main():
    pygame.init()
    pygame.font.init()
    screen_height = 900
    screen_width = 1200
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("PROJECT STORMCHASER MAIN MENU")
    
    while True:
        # Get the start date from the input UI
        start_date, selected_basin = initialize_input_ui(screen, screen_width, screen_height)
        if not start_date:
            print("Invalid date entered. Please try again.")
            
            # Hacky bugfix for stopping the program when pygame quits from the function above
            try:
                # Trying to use Pygame after quitting should raise an error
                font = pygame.font.SysFont("Arial", 24)
            except pygame.error as e:
                return
                
            continue  # Prompt the user again if the date is invalid or too old

        print(f"Start Date: {start_date}")
        break  # Exit the loop if a valid date is entered

    # Initialize the typhoon dataset based on the selected start date
    initialize_dataset(screen, screen_width, screen_height, start_date, selected_basin)
    
    # After scraping is done, proceed with the next steps
    print("Data scraping complete!")
    pygame.quit()
    animate_typhoons(start_date.year, selected_basin)

# Run the main function
if __name__ == "__main__":
    main()
    
# pyinstaller --add-data "resources/*;resources" --add-data "data/*;data" --noconsole --icon=resources\_stormchaser.ico scripts/stormchaser.py
import os
import sys
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def get_resource_path(relative_path):
    """Get the absolute path to the resource file, works both in development and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # If running in a bundled PyInstaller app
        base_path = sys._MEIPASS
    else:
        # If running in development mode
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def ensure_resources_folder():
    """Ensure that the resources folder exists."""
    resources_path = get_resource_path('../resources')
    
    if not os.path.exists(resources_path):
        os.makedirs(resources_path)

def create_western_pacific_map(output_path=None):
    """Creates and saves a map of the Western Pacific with enhanced features."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_path)  # Project root (parent folder of 'scripts')
    resources_path = os.path.join(project_root, 'resources')  # 'resources' next to 'scripts'
    
    print(f"Resources path: {resources_path}")  # Debug statement to check path
    
    if output_path is None:
        output_path = os.path.join(resources_path, 'western_pacific_map.png')

    ensure_resources_folder()

    if os.path.exists(output_path):
        print(f"Map already exists at {output_path}. Using the cached version.")
        return output_path

    # Set up the figure and axis with the PlateCarree projection
    fig = plt.figure(figsize=(8, 6), dpi=300)
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree())

    # Western Pacific Map Region
    ax.set_extent([100, 180, 0, 60], crs=ccrs.PlateCarree())  

    # Add Land and Ocean Features
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '10m', facecolor='darkgreen'))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', '10m', facecolor=rgb_to_normalized(0, 0, 70)))
    ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', linewidth=1)
    ax.add_feature(cfeature.RIVERS, edgecolor=rgb_to_normalized(0, 0, 70), linewidth=0.5)
    ax.add_feature(cfeature.LAKES, facecolor=rgb_to_normalized(0, 0, 70))
    ax.stock_img(zorder=3).set_alpha(0.35)

    # Adjust layout and save the map image
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"Map saved to {output_path}")
    return output_path


def create_simple_western_pacific_map(output_path=None):
    """Creates and saves a map of the Western Pacific with simplified features."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_path)  # Project root (parent folder of 'scripts')
    resources_path = os.path.join(project_root, 'resources')  # 'resources' next to 'scripts'
    
    print(f"Resources path: {resources_path}")  # Debug statement to check path
    
    if output_path is None:
        output_path = os.path.join(resources_path, 'simple_western_pacific_map.png')

    ensure_resources_folder()

    if os.path.exists(output_path):
        print(f"Map already exists at {output_path}. Using the cached version.")
        return output_path

    width_pixels = 1200
    height_pixels = 900
    dpi = 300
    figsize = (width_pixels / dpi, height_pixels / dpi)

    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree())

    ax.set_extent([100, 180, 0, 60], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '10m', facecolor='darkgreen'))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', '10m', facecolor=rgb_to_normalized(0, 0, 70)))

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"Map saved to {output_path} with resolution {width_pixels}x{height_pixels} pixels.")
    return output_path


def rgb_to_normalized(r, g, b):
    """Converts RGB values to normalized values between 0 and 1."""
    rgb = (r, g, b)
    return tuple([x / 255.0 for x in rgb])


def get_detailed_map_image():
    """Returns the paths of the Western Pacific map images, generating them if necessary."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_path)  # Project root (parent folder of 'scripts')
    resources_path = os.path.join(project_root, 'resources')  # 'resources' next to 'scripts'

    # Paths for the image
    detailed_map_path = os.path.join(resources_path, 'western_pacific_map.png')

    # # Create the map if it does not exist
    # if not os.path.exists(detailed_map_path):
    #     create_western_pacific_map(detailed_map_path)

    # Return the paths
    return detailed_map_path


if __name__ == "__main__":
    create_simple_western_pacific_map()
    create_western_pacific_map()

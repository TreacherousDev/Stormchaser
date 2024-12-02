import os
import sys
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from PIL import Image  # For resizing simple maps

BASINS = {
    "Western Pacific": [100, 180, 0, 60],
    "Northern Atlantic": [-100, -20, 0, 60],
    "Eastern Pacific": [-175, -95, 0, 60],
    "Northern Indian": [40, 100, -10, 35],
    "Southern Indian": [20, 120, -75, 0],
    "Southern Pacific": [135, 215, -60, 0]
}
def get_resource_path(relative_path):
    """Get the absolute path to the resource file, works both in development and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def ensure_resources_folder():
    """Ensure that the resources folder exists."""
    resources_path = get_resource_path('../resources')
    if not os.path.exists(resources_path):
        os.makedirs(resources_path)


def rgb_to_normalized(r, g, b):
    """Converts RGB values to normalized values between 0 and 1."""
    return tuple(x / 255.0 for x in (r, g, b))


def adjust_to_aspect_ratio(extent, target_aspect_ratio=4 / 3):
    """
    Adjusts the map extent to fit the target aspect ratio while preserving the basin's coverage.

    extent: [min_longitude, max_longitude, min_latitude, max_latitude]
    target_aspect_ratio: Desired aspect ratio (width/height).
    """
    min_long, max_long, min_lat, max_lat = extent

    width = max_long - min_long
    height = max_lat - min_lat
    current_aspect_ratio = width / height

    if current_aspect_ratio < target_aspect_ratio:
        # Expand width
        required_width = height * target_aspect_ratio
        delta = (required_width - width) / 2
        min_long -= delta
        max_long += delta
    elif current_aspect_ratio > target_aspect_ratio:
        # Expand height
        required_height = width / target_aspect_ratio
        delta = (required_height - height) / 2
        min_lat -= delta
        max_lat += delta

    return [min_long, max_long, min_lat, max_lat]

def create_basin_map(basin_name, extent, output_path=None, detailed=True):
    """Creates and saves a map of the specified typhoon basin, or returns the cached version."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_path)
    resources_path = os.path.join(project_root, 'resources')

    # Generate the output path if not specified
    if output_path is None:
        suffix = "detailed" if detailed else "simple"
        output_path = os.path.join(resources_path, f'{basin_name.lower().replace(" ", "_")}_{suffix}_map.png')

    ensure_resources_folder()

    # Check if the file already exists
    if os.path.exists(output_path):
        print(f"Map for {basin_name} ({'detailed' if detailed else 'simple'}) already exists at {output_path}. Using the cached version.")
        return output_path

    # Adjust the extent to fit the 4:3 aspect ratio
    # midpoint = (extent[0] + extent[1]) / 2
    adjusted_extent = adjust_to_aspect_ratio(extent)

    fig = plt.figure(figsize=(8, 6), dpi=300)  # 4:3 aspect ratio
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree(central_longitude=180 if basin_name == 'Southern Pacific' else 0))

    ax.set_extent(adjusted_extent, crs=ccrs.PlateCarree())

    # Add features
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '10m', facecolor='darkgreen'))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', '10m', facecolor=rgb_to_normalized(0, 0, 70)))
    if detailed:
        # Add more detailed features
        ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', linewidth=1)
        ax.add_feature(cfeature.RIVERS, edgecolor=rgb_to_normalized(0, 0, 70), linewidth=0.5)
        ax.add_feature(cfeature.LAKES, facecolor=rgb_to_normalized(0, 0, 70))
        ax.stock_img(zorder=3).set_alpha(0.35)  # Semi-transparent stock image overlay

    # Adjust layout
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # Save the image
    if detailed:
        plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
    else:
        # Disable antialiasing by using lower DPI and rasterizing features
        plt.savefig(output_path, dpi=150, bbox_inches='tight', pad_inches=0, transparent=True)
    
    plt.close()

    print(f"Map for {basin_name} ({'detailed' if detailed else 'simple'}) saved to {output_path}")

    if not detailed:
        # Resize simple maps to 1200x900
        resize_image(output_path, 1200, 900)

    return output_path




def resize_image(image_path, width, height):
    """Resizes the image to the specified dimensions."""
    with Image.open(image_path) as img:
        img_resized = img.resize((width, height))
        img_resized.save(image_path)
        print(f"Resized image saved at {image_path} to {width}x{height} dimensions.")


def generate_basin_maps(basin_name, extent, output_directory=None):
    """
    Generate both detailed and non-detailed maps for a specified basin.
    Returns the paths to the created maps or the cached versions.
    """
    detailed_map_path = create_basin_map(basin_name, extent, output_path=output_directory, detailed=True)
    simple_map_path = create_basin_map(basin_name, extent, output_path=output_directory, detailed=False)
    return detailed_map_path, simple_map_path


def get_detailed_map_image(basin_name="Western Pacific"):
    """
    Returns the path to a high-quality (detailed) map of the specified basin.
    If the map does not exist, it generates and caches the map.
    """

    if basin_name not in BASINS:
        raise ValueError(f"Invalid basin name: {basin_name}. Available options are: {', '.join(BASINS.keys())}")

    extent = BASINS[basin_name]
    return create_basin_map(basin_name, extent, detailed=True)


def get_simple_map_image(basin_name="Western Pacific"):
    """
    Returns the path to a low-quality (simple) map of the specified basin.
    If the map does not exist, it generates and caches the map.
    """

    if basin_name not in BASINS:
        raise ValueError(f"Invalid basin name: {basin_name}. Available options are: {', '.join(BASINS.keys())}")

    extent = BASINS[basin_name]
    return create_basin_map(basin_name, extent, detailed=False)


def main():

    print("Available Basins:")
    for basin in BASINS:
        extent = BASINS[basin]
        detailed_map, simple_map = generate_basin_maps(basin, extent)

        print(f"Detailed map saved at: {detailed_map}")
        print(f"Simple map saved at: {simple_map}")

    print("done")

if __name__ == "__main__":
    main()

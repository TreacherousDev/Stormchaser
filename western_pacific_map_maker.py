import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def create_western_pacific_map(output_path="western_pacific_map.png"):
    """
    Creates and saves a map of the Western Pacific with enhanced features using Cartopy.
    If the map file already exists, it will load and return the existing file.

    Parameters:
    - output_path (str): Path where the generated map image will be saved.

    Returns:
    - str: Path to the saved map image.
    """
    # Check if the map already exists
    if os.path.exists(output_path):
        print(f"Map already exists at {output_path}. Using the cached version.")
        return output_path

    # Set up the figure and axis with the PlateCarree projection
    fig = plt.figure(figsize=(10, 7), dpi=300)
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree())

    # Western Pacific Map Region
    ax.set_extent([100, 170, -10, 40], crs=ccrs.PlateCarree())  

    # Add Land and Ocean Features
    ax.add_feature(cfeature.LAND, facecolor='darkgreen')
    ax.add_feature(cfeature.OCEAN, facecolor=rgb_to_normalized(0, 0, 70))
    # Add country boundaries
    ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', linewidth=1)

    # Add rivers and lakes
    ax.add_feature(cfeature.RIVERS, edgecolor=rgb_to_normalized(0, 0, 70), linewidth=0.5)
    ax.add_feature(cfeature.LAKES, facecolor=rgb_to_normalized(0, 0, 70))

    # Add a stock image for basic elevation data
    ax.stock_img(zorder=3).set_alpha(0.35)

    # Adjust layout and save the map image
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"Map saved to {output_path}")
    return output_path

def create_simple_western_pacific_map(output_path="simple_western_pacific_map.png"):
    # Check if the map already exists
    if os.path.exists(output_path):
        print(f"Map already exists at {output_path}. Using the cached version.")
        return output_path

    # Desired resolution in pixels
    width_pixels = 1400
    height_pixels = 1000
    dpi = 300  # Dots per inch for high-quality output

    # Calculate figsize (in inches) based on desired resolution
    figsize = (width_pixels / dpi, height_pixels / dpi)

    # Set up the figure and axis with the PlateCarree projection
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree())

    # Western Pacific Map Region
    ax.set_extent([100, 170, -10, 40], crs=ccrs.PlateCarree())  

    # Add Land and Ocean Features with no anti-aliasing for the edges
    ax.add_feature(cfeature.LAND, facecolor='darkgreen')
    ax.add_feature(cfeature.OCEAN, facecolor=rgb_to_normalized(0, 0, 70))

    # Adjust layout to avoid anti-aliasing and smooth transitions
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # Save the map with the desired resolution
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"Map saved to {output_path} with resolution {width_pixels}x{height_pixels} pixels.")
    return output_path


def rgb_to_normalized(r, g, b):
    """Converts RGB values to normalized values between 0 and 1."""
    rgb = (r, g, b)
    return tuple([x / 255.0 for x in rgb])

if __name__ == "__main__":
    create_western_pacific_map()
    create_simple_western_pacific_map()
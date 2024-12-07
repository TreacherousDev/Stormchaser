import cartopy.feature as cfeature
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

def rgb_to_normalized(r, g, b):
    """Converts RGB values to normalized values between 0 and 1."""
    return tuple(x / 255.0 for x in (r, g, b))

# Create figure and axis
fig = plt.figure(figsize=(12, 6))  # Adjust the size as needed
ax = fig.add_subplot(111, projection=ccrs.PlateCarree(central_longitude=180))

# Set the extent of the map
ax.set_extent([120, 260, 15, 80], crs=ccrs.PlateCarree())

# Add features to the map
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
ax.coastlines('50m')
ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '10m', facecolor='darkgreen'))
ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', '10m', facecolor=rgb_to_normalized(0, 0, 70)))
# Add more detailed features
ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', linewidth=1)
ax.add_feature(cfeature.RIVERS, edgecolor=rgb_to_normalized(0, 0, 70), linewidth=0.5)
ax.add_feature(cfeature.LAKES, facecolor=rgb_to_normalized(0, 0, 70))
ax.stock_img(zorder=3).set_alpha(0.35)  # Semi-transparent stock image overlay

# Remove extra whitespace and make the map fill the window
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

plt.show()

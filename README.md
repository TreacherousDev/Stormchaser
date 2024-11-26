# Project Stormchaser 🌀

A real-time typhoon visualization system that scrapes and animates Western Pacific typhoon data. This project creates an interactive visualization of typhoon paths, including wind speeds, pressure data, and landfall detection.

## 🌟 Features

- **Real-time Typhoon Tracking**: Visualizes typhoon paths with smooth animations
- **Dynamic Color Coding**: Changes typhoon colors based on intensity categories
- **Landfall Detection**: Automatically detects and marks typhoon landfall points
- **Detailed Information Display**: Shows typhoon names, wind speeds, and pressure data
- **Interactive Timeline**: Includes a play button and time display
- **FPS Counter**: Monitors visualization performance
- **Data Caching**: Implements efficient data storage and retrieval

## 🛠 Technical Components

### Map Generation (`western_pacific_map_maker.py`)
- Creates high-resolution maps of the Western Pacific region
- Utilizes Cartopy for accurate geographical projections
- Supports both detailed and simplified map versions
- Features include land masses, ocean, country borders, and basic elevation data

### Typhoon Data Scraper (`typhoon_scraper.py`)
- Scrapes typhoon data from Digital Typhoon database
- Extracts detailed track information including:
  - Position (latitude/longitude)
  - Wind speeds
  - Pressure data
  - Timestamps
- Implements caching mechanism to store scraped data

### Visualization Engine (`typhoon_animation.py`)
- Built with Pygame for smooth real-time animations
- Features include:
  - Rotating typhoon symbols
  - Color-coded intensity levels
  - Dynamic fade in/out effects
  - Landfall detection and marking
  - Time scaling for visualization
  - Interactive controls

### Map Image Processor
- Handles map image loading and processing
- Provides coordinate transformation utilities
- Supports landfall detection through color sampling

## 🎨 Visualization Features
![1126-ezgif com-video-to-gif-converter](https://github.com/user-attachments/assets/a9ae5de8-44f1-4b6e-b3fe-61e6ce39eb88)

### Typhoon Representation
- **Symbol**: Animated rotating spiral with center dot
- **Color Coding**:
  ```python
  category_colors = {
      0: (135, 206, 235),  # Light Blue
      1: (100, 238, 100),  # Light Green
      2: (225, 225, 0),    # Yellow
      3: (255, 130, 0),    # Orange
      4: (255, 0, 0),      # Red
      5: (180, 0, 180)     # Purple
  }
  ```
- **Information Display**: Shows name, wind speed (km/h), and pressure (hPa)

### Animation Effects
- Smooth fade-in/fade-out transitions
- Constant speed movement between track points
- Rotating blade animation
- Dynamic landfall markers with zoom effects

## 🚀 Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

Required packages:
- pygame
- requests
- beautifulsoup4
- cartopy
- matplotlib
- numpy

### Running the Application
   ```python
   python typhoon_animation.py
   ```

### Controls
- Click the "Play" button to start the animation
- Close window to exit

## 📊 Data Structure

### Typhoon Object Format
```python
{
    "name": str,            # Typhoon name
    "path": [{
        "time": str,        # Format: "YYYY-MM-DD HH:MM"
        "lat": float,       # Latitude
        "long": float,      # Longitude
        "class": int,       # Intensity category (0-5)
        "speed": str,       # Wind speed in km/h
        "pressure": int     # Pressure in hPa
    }],
    "start_time": int       # Animation start time offset
}
```

## ⚙️ Configuration

Key parameters that can be adjusted:

```python
# Time scaling
time_scale_factor = 1 / (12 * 60 * 60)  # 1 second = 12 hours

# Screen dimensions
screen_width, screen_height = 1400, 1000

# Animation parameters
fade_in_duration = 1
fade_out_duration = 0.5
fps_target = 120
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

<add license section>.

## 🙏 Acknowledgments

- Data source: Digital Typhoon (http://agora.ex.nii.ac.jp/digital-typhoon/)
- Map data: Natural Earth via Cartopy
- Inspiration: Real-time weather visualization systems

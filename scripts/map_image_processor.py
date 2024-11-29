from PIL import Image

class MapImageProcessor:
    @staticmethod
    def load_image(image_path):
        """
        Load an image from a given path and return it in a pixel-accessible format.
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Image.Image: The loaded image in RGB format.
        """
        try:
            img = Image.open(image_path).convert('RGB')  # Convert to RGB for consistent pixel access
            print(f"Image loaded successfully: {image_path}")
            return img
        except FileNotFoundError:
            print(f"Error: Image file not found at {image_path}")
            return None
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

    @staticmethod
    def is_color_at_coordinate(img, x, y, target_color):
        """
        Check if a pixel at (x, y) matches the target color.

        Args:
            img (Image.Image): The pixel-accessible image object.
            x (int): X-coordinate of the pixel.
            y (int): Y-coordinate of the pixel.
            target_color (tuple): Target color in (R, G, B) format.

        Returns:
            bool: True if the color matches, False otherwise.
        """
        try:
            if x < 0 or y < 0 or x >= img.width or y >= img.height:
                raise ValueError(f"Coordinates ({x}, {y}) are out of bounds for image size {img.size}.")
            
            pixel_color = img.getpixel((x, y))
            return pixel_color == target_color
        except Exception as e:
            # print(f"Error checking pixel color: {e}")
            return False

    @staticmethod
    def get_color_at_coordinate(img, x, y):
        """
        Get the color at a specific pixel coordinate.

        Args:
            img (Image.Image): The pixel-accessible image object.
            x (int): X-coordinate of the pixel.
            y (int): Y-coordinate of the pixel.

        Returns:
            tuple: RGB color tuple of the pixel (R, G, B).
        """
        try:
            if x < 0 or y < 0 or x >= img.width or y >= img.height:
                raise ValueError(f"Coordinates ({x}, {y}) are out of bounds for image size {img.size}.")
            
            return img.getpixel((x, y))
        except Exception as e:
            # print(f"Error getting pixel color: {e}")
            return None

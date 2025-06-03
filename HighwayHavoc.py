class GameObjects:
    """Base class for all game objects with drawing and positioning functionality."""
    
    def __init__(self, x, y, width, height):
        """Initialize game object with position and dimensions."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def draw(self, screen):
        """Draw the game object on the screen."""
        pass
    
    def get_position(self):
        """Return the current position of the game object."""
        return (self.x, self.y)


class FallingObjects:
    """Mixin class for objects that fall down the screen."""
    
    def __init__(self, fall_speed=5):
        """Initialize falling object with fall speed."""
        self.fall_speed = fall_speed
    
    def update_fall_speed(self, new_speed):
        """Update the falling speed of the object."""
        self.fall_speed = new_speed

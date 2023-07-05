import pygame
import pygame_gui

# Initialize Pygame
pygame.init()

# Define screen dimensions
screen_width = 800
screen_height = 600

# Define colors
black = (0, 0, 0)
white = (255, 255, 255)

# Create screen
screen = pygame.display.set_mode((screen_width, screen_height))

# Define slider properties
slider_width = 400
slider_height = 20

# Create UI manager
manager = pygame_gui.UIManager((screen_width, screen_height))

# Create a UI container for the slider at the bottom of the screen
container = pygame_gui.core.UIContainer(
    relative_rect=pygame.Rect((screen_width // 2 - slider_width // 2, screen_height - 50), (slider_width, slider_height)),
    manager=manager
)

# Create slider
slider = pygame_gui.elements.UIHorizontalSlider(
    relative_rect=pygame.Rect((0, 0), (slider_width, slider_height)),
    start_value=30,
    value_range=(1, 60),
    manager=manager,
    container=container
)

# Initialize color and frequency
color = black
frequency = slider.get_current_value()

# Create a custom event for color switching
SWITCH_COLOR = pygame.USEREVENT + 1
pygame.time.set_timer(SWITCH_COLOR, int(1000 / frequency))

# Main loop
run = True
while run:
    time_delta = pygame.time.Clock().tick(60) / 1000.0

    # Event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == slider:
                    frequency = event.value
                    pygame.time.set_timer(SWITCH_COLOR, int(1000 / frequency))
            manager.process_events(event)
        if event.type == SWITCH_COLOR:
            color = white if color == black else black

    # Update UI
    manager.update(time_delta)

    # Switch colors and update screen
    screen.fill(color)
    manager.draw_ui(screen)
    pygame.display.update()

# Quit pygame
pygame.quit()

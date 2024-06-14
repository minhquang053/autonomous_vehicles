import pygame
import sys
import math

# Constants
WIDTH, HEIGHT = 800, 600
CAR_RADIUS = 8
CAR_SPEED = 3
OBSTACLE_SIZE = 40
SENSOR_LENGTH = 200
SPARSENESS_PROBABILITY = 2
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)

# Wall properties
WALL_THICKNESS = 1
WALL_COLOR = BLACK

# Fixed obstacle positions
OBSTACLE_POSITIONS = [
    (100, 100),
    (200, 300),
    (400, 200),
    (600, 400),
    (300, 500),
    (500, 100),
    (700, 300),
    (100, 500),
]

# Wall positions (left, top, width, height)
WALLS = [
    pygame.Rect(0, 0, WIDTH, WALL_THICKNESS),  # Top wall
    pygame.Rect(0, 0, WALL_THICKNESS, HEIGHT),  # Left wall
    pygame.Rect(WIDTH - WALL_THICKNESS, 0, WALL_THICKNESS, HEIGHT),  # Right wall
    pygame.Rect(0, HEIGHT - WALL_THICKNESS, WIDTH, WALL_THICKNESS),  # Bottom wall
]

# Car class
class Car(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((2 * CAR_RADIUS, 2 * CAR_RADIUS), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (CAR_RADIUS, CAR_RADIUS), CAR_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = CAR_SPEED
        self.angle = 0

        # Sensor directions (relative angles)
        # represent left, front, right sensor
        self.sensor_angles = [45, 0, -45]
        self.sensors = [Sensor(self.rect.center, angle) for angle in self.sensor_angles]

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.angle += 5
        if keys[pygame.K_RIGHT]:
            self.angle -= 5
        if keys[pygame.K_SPACE]:
            input()

        self.rect.x += self.speed * math.cos(math.radians(self.angle))
        self.rect.y -= self.speed * math.sin(math.radians(self.angle))

        # Check for collisions with the walls
        for wall in WALLS:
            if pygame.Rect(wall).colliderect(self.rect):
                # If collision with a wall, respawn the car at the center
                self.rect.center = (WIDTH // 2, HEIGHT // 2)

        # Check for collisions with obstacles
        collisions = pygame.sprite.spritecollide(self, obstacles, False)

        if collisions:
            # If collision with an obstacle, respawn the car at the center
            self.rect.center = (WIDTH // 2, HEIGHT // 2)

        # Update sensor positions and distances
        for sensor in self.sensors:
            sensor.update(self.rect.center, self.angle)

    def get_sensor_distances(self):
        return [sensor.distance for sensor in self.sensors]

# Sensor class
class Sensor(pygame.sprite.Sprite):
    def __init__(self, start_pos, angle_offset):
        super().__init__()
        self.image = pygame.Surface((0, 0), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.start_pos = start_pos
        self.angle_offset = angle_offset
        self.end_pos = start_pos
        self.distance = SENSOR_LENGTH

    def update(self, car_center, car_angle):
        self.start_pos = car_center
        # Calculate sensor position based on car's center and angle
        angle = math.radians(car_angle + self.angle_offset)
        self.end_pos = (
            int(car_center[0] + SENSOR_LENGTH * math.cos(angle)),
            int(car_center[1] - SENSOR_LENGTH * math.sin(angle))
        )
        self.rect.topleft = car_center

        # Calculate the distance to the closest obstacle
        closest_obstacle = None
        closest_distance = SENSOR_LENGTH

        for obstacle in obstacles:
            # Calculate the intersection point of the line segment and the obstacle's rect
            intersection_point = self.get_line_rect_intersection(self.start_pos, self.end_pos, obstacle.rect)
            if intersection_point:
                distance = math.sqrt((car_center[0] - intersection_point[0]) ** 2 +
                                     (car_center[1] - intersection_point[1]) ** 2)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_obstacle = obstacle

        for wall in WALLS:
            # Calculate the intersection point of the line segment and the wall
            intersection_point = self.get_line_rect_intersection(self.start_pos, self.end_pos, pygame.Rect(wall))
            if intersection_point:
                distance = math.sqrt((car_center[0] - intersection_point[0]) ** 2 +
                                     (car_center[1] - intersection_point[1]) ** 2)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_obstacle = None  # Walls override other obstacles

        if closest_obstacle:
            self.distance = abs(int(closest_distance - CAR_RADIUS))
        else:
            self.distance = SENSOR_LENGTH

    @staticmethod
    def get_line_rect_intersection(start_pos, end_pos, rect):
        # Get the four corners of the rectangle
        rect_corners = [(rect.left, rect.top), (rect.right, rect.top), (rect.right, rect.bottom), (rect.left, rect.bottom)]

        for i in range(4):
            # Check for intersection with each line segment of the rectangle
            line_start = rect_corners[i]
            line_end = rect_corners[(i + 1) % 4]

            intersection = line_intersection(start_pos, end_pos, line_start, line_end)
            if intersection:
                return intersection

        return None

# Function to find the intersection point of two lines
def line_intersection(start1, end1, start2, end2):
    x1, y1 = start1
    x2, y2 = end1
    x3, y3 = start2
    x4, y4 = end2

    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if denominator == 0:
        return None

    x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
    y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator

    # Check if the intersection point is within the line segments
    if min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2) and \
       min(x3, x4) <= x <= max(x3, x4) and min(y3, y4) <= y <= max(y3, y4):
        return int(x), int(y)
    else:
        return None

# Obstacle class
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((OBSTACLE_SIZE, OBSTACLE_SIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

# Initialize Pygame
pygame.init()

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autonomous Car Simulation")

# Create sprites
all_sprites = pygame.sprite.Group()
car = Car(WIDTH // 2, HEIGHT // 2)
obstacles = pygame.sprite.Group()

all_sprites.add(car)

# Spawn fixed obstacles and walls outside the game loop
for position in OBSTACLE_POSITIONS:
    obstacle = Obstacle(position[0], position[1], WHITE)
    obstacles.add(obstacle)
    all_sprites.add(obstacle)

for wall in WALLS:
    wall_obstacle = Obstacle(wall[0], wall[1], WALL_COLOR)
    wall_obstacle.rect.size = (wall[2], wall[3])
    obstacles.add(wall_obstacle)
    all_sprites.add(wall_obstacle)

# Game loop
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update
    all_sprites.update()

    # Draw
    screen.fill(BLACK)
    
    # Draw sensors and car
    for sensor in car.sensors:
        pygame.draw.line(screen, YELLOW, sensor.start_pos, sensor.end_pos, 2)

    distances = car.get_sensor_distances()
    print(distances)

    # Draw obstacles
    all_sprites.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
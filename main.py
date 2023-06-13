import math

import pygame
import random
import sys

# Размеры окна в пикселях
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 480

# Viewport1
CELL_SIZE = 4       # Размер ячейки
BORDER_SIZE = 3     # Размер рамки
# Размеры сетки в ячейках
WIDTH = (WINDOW_WIDTH // 2) // CELL_SIZE
HEIGHT = WINDOW_HEIGHT // CELL_SIZE

# Viewport2
WINDOW_WIDTH_VP2 = 120  # Ширина в пикселях
WINDOW_HEIGHT_VP2 = 100

# Viewport 3
CELL_SIZE_VP3 = 20
WINDOW_WIDTH_VP3 = 180
WINDOW_HEIGHT_VP3 = 180
WIDTH_VP3 = WINDOW_WIDTH_VP3 // CELL_SIZE_VP3
HEIGHT_VP3 = WINDOW_HEIGHT_VP3 // CELL_SIZE_VP3

# Цвета
BG_COLOR = (0, 0, 0)
GRID_COLOR = (40, 40, 40)
APPLE_COLOR = (255, 0, 0)
APPLE_OUTER_COLOR = (155, 0, 0)
SNAKE_COLOR = (0, 255, 0)
SNAKE_OUTER_COLOR = (0, 155, 0)
HEAD_COLOR = (173, 255, 47)
HEAD_OUTER_COLOR = (154, 205, 50)
TEXT_COLOR = (255, 100, 0)

FPS = 15

EDGELESS = True  # Мир закольцован

LIMIT_OF_APPLES = 1000
MAX_SPEED = FPS
MIN_SPEED = 1
MIN_LEN_SNAKE = 3
a1 = 4/100
a2 = math.log(MAX_SPEED - MIN_SPEED) + a1 * MIN_LEN_SNAKE


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y

    def __lt__(self, other):
        return self.x < other.x or self.y < other.y

    def __le__(self, other):
        return self.x <= other.x or self.y <= other.y

    def __gt__(self, other):
        return self.x > other.x or self.y > other.y

    def __ge__(self, other):
        return self.x >= other.x or self.y >= other.y

    def __neg__(self):
        return Cell(self.x * (-1), self.y * (-1))

    def __add__(self, other):
        return Cell(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Cell(self.x - other.x, self.y - other.y)

    def __imod__(self, other):
        self.x %= other.x
        self.y %= other.y
        return self

    def __iadd__(self, other):
        return Cell(self.x + other.x, self.y + other.y)

    def draw(self, surface, outer_color, inner_color, cell_size):
        #  Ячейка состоит из двух квадратов разных цветов:
        #  * большой квадрат закрашивается цветом outer_color,
        x = self.x * cell_size
        y = self.y * cell_size
        r = pygame.Rect(x, y, cell_size, cell_size)
        pygame.draw.rect(surface, outer_color, r, 0)
        #  * меньший - inner_color.
        x += BORDER_SIZE
        y += BORDER_SIZE
        size = cell_size - BORDER_SIZE * 2
        r = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, inner_color, r, 0)


class Snake:
    def __init__(self):
        self.cells = [Cell(WIDTH//2, i) for i in range(HEIGHT//2+1, HEIGHT//2-2, -1)]
        for cell in self.cells:
            map_world[cell.y][cell.x] = 2
        self.speed = MAX_SPEED
        self.direction_of_head = self.cells[-1] - self.cells[-2]
        self.vision = [[0] * WIDTH_VP3 for _ in range(HEIGHT_VP3)]
        self.brain()

    def brain(self):
        for y in range(HEIGHT_VP3):
            for x in range(WIDTH_VP3):
                oriented_cell = orient(x, y, HEIGHT_VP3, WIDTH_VP3, self.direction_of_head)
                cell = self.cells[-1] + oriented_cell - Cell(WIDTH_VP3//2, HEIGHT_VP3//2)
                cell %= Cell(WIDTH, HEIGHT)
                self.vision[y][x] = map_world[cell.y][cell.x]

    def draw_brain(self):
        for y in range(HEIGHT_VP3):
            for x in range(WIDTH_VP3):
                if self.vision[y][x] == 1:
                    Cell(x, y).draw(viewport3, APPLE_OUTER_COLOR, APPLE_COLOR, CELL_SIZE_VP3)
                if self.vision[y][x] == 2:
                    Cell(x, y).draw(viewport3, SNAKE_OUTER_COLOR, SNAKE_COLOR, CELL_SIZE_VP3)
                if self.vision[y][x] == 3:
                    Cell(x, y).draw(viewport3, HEAD_OUTER_COLOR, HEAD_COLOR, CELL_SIZE_VP3)

    def get_new_head(self, side):
        f = get_sensor(side)
        f = orient(f.x, f.y, HEIGHT_VP3, WIDTH_VP3, self.direction_of_head)
        head = Cell(HEIGHT_VP3 // 2, WIDTH_VP3 // 2)
        return f - head

    def make_decision(self):
        ways = ['forward', 'left', 'right']
        for side in ways:
            sensor = get_sensor(side)
            if self.see_apple(sensor):
                return side
        if self.see_self(get_sensor('forward')) or random.randrange(10) == 0:
            if self.see_self(get_sensor('left')):
                return 'right'
            elif self.see_self(get_sensor('right')):
                return 'left'
            else:
                return random.sample(['left', 'right'], 1)[0]
        else:
            return 'forward'

    def move_to(self, side):
        global count_apple
        """Функция перемещения змейки на одну ячейку в заданном направлении."""
        end_of_tail = self.cells.pop(0)
        map_world[end_of_tail.y][end_of_tail.x] = 0
        old_head = self.cells[-1]
        new_head = old_head + self.get_new_head(side)
        if -1 <= new_head.x - old_head.x <= 1 and -1 <= new_head.y - old_head.y <= 1:
            self.direction_of_head = new_head - old_head
        # Если мир без границ, то закольцовываем координаты
        if EDGELESS:
            new_head %= Cell(WIDTH, HEIGHT)
        self.cells.append(new_head)
        # Если змейка задела свой хвост:
        #   * оторвать хвост в месте касания
        #   * превратить хвост в яблоки
        bite_self, index = self.bite_self()
        if bite_self:
            tail = self.cells[0:index]
            for cell in tail:
                map_world[cell.y][cell.x] = 1
            self.cells = self.cells[index:]
        # Обработка ситуации столкновения змейки с яблоком.
        #  При столкновении:
        #   * увеличить размер змейки, если кол-во съеденных яблок равняется длине змейки
        #   * добавить новое яблоко
        if self.hit_apple():
            count_apple += 1
            # Условие роста змейки.
            if count_apple >= len(self.cells):
                count_apple = 0
                self.grow()
            if sum(row.count(1) for row in map_world) <= LIMIT_OF_APPLES:
                new_apple = add_apple()
                # Если яблоко на змее, то располагаем яблоко позади хвоста
                if map_world[new_apple.y][new_apple.x] == 2 or map_world[new_apple.y][new_apple.x] == 3:
                    new_apple = self.cells[0] + (self.cells[0] - self.cells[1])
                    new_apple %= Cell(WIDTH, HEIGHT)
                map_world[new_apple.y][new_apple.x] = 1
        map_world[old_head.y][old_head.x] = 2
        map_world[new_head.y][new_head.x] = 3
        self.brain()

    def hit_edge(self):
        """Функция возвращает True,
        если змейка пересекла одну из границ окна."""
        if self.cells[-1] < Cell(0, 0) or self.cells[-1] > Cell(WIDTH, HEIGHT):
            return True

    def hit_apple(self):
        """Функция возвращает True, если голова
        змейки находится в той же ячейке, что и яблоко."""
        for cell in self.cells[-1::-1]:
            if map_world[cell.y][cell.x] == 1:
                map_world[cell.y][cell.x] = 2
                return True

    def grow(self):
        """Функция увеличения длины змейки."""
        self.cells.insert(0, self.cells[0])

    def bite_self(self):
        """Функция возвращает True и индекс пересечения головы с хвостом, если голова змеи
        пересеклась с блоком хвоста."""
        for cell in self.cells[:-2]:
            if self.cells[-1] == cell:
                return True, self.cells.index(cell)
        return False, -1

    def see_apple(self, sensor):
        """Если змея увидела яблоко, то функция возвращает True"""
        return self.vision[sensor.y][sensor.x] == 1

    def see_self(self, sensor):
        """Если змея увидела себя, то функция возвращает True"""
        return self.vision[sensor.y][sensor.x] == 2


def add_apple():
    """Функция возвращает ячейку со случайными координатами Cell(x, y)."""
    return Cell(random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))


# Создаем пустой мир из 0
map_world = [[0] * WIDTH for _ in range(HEIGHT)]    # 1 - яблоко, 2 - хвост, 3 - голова, 0 - пусто
# Добавляем яблоки
for _ in range(LIMIT_OF_APPLES):
    apple = add_apple()
    map_world[apple.y][apple.x] = 1
count_apple = 0


def main():
    global FPS_CLOCK
    global DISPLAY
    global viewport1, viewport2, viewport3
    global font

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Wormy')
    viewport1 = create_viewport(WINDOW_WIDTH // 2, WINDOW_HEIGHT)  # область мира змейки
    viewport2 = create_viewport(WINDOW_WIDTH_VP2, WINDOW_HEIGHT_VP2)  # боковая область, отображение длины змейки
    viewport3 = create_viewport(WINDOW_WIDTH_VP3, WINDOW_HEIGHT_VP3)
    font = pygame.font.SysFont('couriernew', 12)
    while True:
        # Game... Game never changes.
        run_game()


def run_game():
    snake = Snake()
    max_len = len(snake.cells)
    count_delay = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        # При не закольцованном режиме, если змейка достигла границы окна, начать новую игру.
        if not EDGELESS and snake.hit_edge():
            break
        if count_delay <= 0:
            # Решить, куда идти
            side = snake.make_decision()
            # Сдвинуть змейку в заданном направлении
            snake.move_to(side)
            snake.speed = get_speed(len(snake.cells))
            count_delay = MAX_SPEED - snake.speed
        else:
            count_delay -= 1
        # Фиксирование максимальной длины, за сессию
        if max_len < len(snake.cells):
            max_len = len(snake.cells)
        text = f'Len:{len(snake.cells)} ({max_len})\n'
        text += f'speed: {snake.speed}'
        draw_frame(snake, text)
        FPS_CLOCK.tick(FPS)


def draw_frame(snake, text):
    DISPLAY.fill(GRID_COLOR)
    viewport1.fill(BG_COLOR)
    viewport2.fill(BG_COLOR)
    viewport3.fill(BG_COLOR)
    draw_text(text)
    draw_grid(viewport1, WIDTH, HEIGHT, CELL_SIZE)
    draw_grid(viewport3, WIDTH_VP3, HEIGHT_VP3, CELL_SIZE_VP3)
    snake.draw_brain()
    draw_map_world()

    DISPLAY.blit(viewport1, (0, 0))
    DISPLAY.blit(viewport2, (WINDOW_WIDTH - WINDOW_WIDTH_VP2, 0))
    DISPLAY.blit(viewport3, (WINDOW_WIDTH // 2 + CELL_SIZE_VP3, 0))
    pygame.display.update()


def draw_grid(surface, width, height, cell_size):
    """Функция заполняет всю поверхность surface сеткой width X height квадратов"""
    for i in range(width):
        pygame.draw.line(surface, GRID_COLOR, (i * cell_size, 0), (i * cell_size, surface.get_size()[1]))
    for i in range(height):
        pygame.draw.line(surface, GRID_COLOR, (0, i * cell_size), (surface.get_size()[0], i * cell_size))


def draw_map_world():
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if map_world[y][x] != 0:
                if map_world[y][x] == 3:
                    Cell(x, y).draw(viewport1, HEAD_OUTER_COLOR, HEAD_COLOR, CELL_SIZE)
                if map_world[y][x] == 2:
                    Cell(x, y).draw(viewport1, SNAKE_OUTER_COLOR, SNAKE_COLOR, CELL_SIZE)
                elif map_world[y][x] == 1:
                    Cell(x, y).draw(viewport1, APPLE_OUTER_COLOR, APPLE_COLOR, CELL_SIZE)


def draw_text(text):
    y = 5
    for string in text.split('\n'):
        viewport2.blit(font.render(string, True, TEXT_COLOR), (3, y))
        y += 20


def orient(x, y, height, width, direction_of_head):
    if direction_of_head == Cell(-1, 0):
        return rotate_270(x, y, height)
    elif direction_of_head == Cell(0, 1):
        return rotate_180(x, y, height, width)
    elif direction_of_head == Cell(1, 0):
        return rotate_90(x, y, width)
    else:
        return Cell(x, y)


def rotate_90(x, y, length):
    return Cell(abs(y - length + 1), x)


def rotate_180(x, y, length_x, length_y):
    return Cell(abs(x - length_x + 1), abs(y - length_y + 1))


def rotate_270(x, y, length):
    return Cell(y, abs(x - length + 1))


def get_sensor(side: str):
    """Функция возвращает координату сенсора змеи(слева, справа, спереди)"""
    head = Cell(HEIGHT_VP3 // 2, WIDTH_VP3 // 2)
    match side:
        case 'left':
            return head + Cell(-1, 0)
        case 'forward':
            return head + Cell(0, -1)
        case 'right':
            return head + Cell(1, 0)
        case _:
            return head


def get_speed(length):
    """Функция возвращает скорость змеи(чем больше змея, тем скорость меньше)"""
    if length >= 3:
        return round(math.exp(-a1 * length + a2) + 1)
    return 0


def create_viewport(width, height):
    """Функция создает поверхность(Surface) с заданными размерами (width, height)"""
    surface = pygame.Surface((width, height))
    return surface


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()

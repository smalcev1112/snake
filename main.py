import pygame
import random
import sys

# Размеры окна в пикселях
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

# Размер сетки и ее рамки
CELL_SIZE = 20
BORDER_SIZE = 3

LIMIT_OF_APPLES = 50

# Ширина viewport2
WIDTH_VP2 = 80

# Размеры сетки в ячейках(viewport1)
WIDTH = (WINDOW_WIDTH - WIDTH_VP2) // CELL_SIZE
HEIGHT = WINDOW_HEIGHT // CELL_SIZE

# Цвета
BG_COLOR = (0, 0, 0)
GRID_COLOR = (40, 40, 40)
APPLE_COLOR = (255, 0, 0)
APPLE_OUTER_COLOR = (155, 0, 0)
SNAKE_COLOR = (0, 255, 0)
SNAKE_OUTER_COLOR = (0, 155, 0)
VISION_COLOR = (255, 170, 200)
VISION_OUTER_COLOR = (230, 150, 180)
HEAD_COLOR = (173, 255, 47)
HEAD_OUTER_COLOR = (154, 205, 50)
TEXT_COLOR = (255, 100, 0)

FPS = 3

EDGELESS = True  # Мир закольцован


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

    def draw(self, outer_color, inner_color):
        #  Ячейка состоит из двух квадратов разных цветов:
        #  * большой квадрат закрашивается цветом outer_color,
        x = self.x * CELL_SIZE
        y = self.y * CELL_SIZE
        r = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(viewport1, outer_color, r, 0)
        #  * меньший - inner_color.
        x += BORDER_SIZE
        y += BORDER_SIZE
        size = CELL_SIZE - BORDER_SIZE * 2
        r = pygame.Rect(x, y, size, size)
        pygame.draw.rect(viewport1, inner_color, r, 0)


class Snake:
    def __init__(self):
        self.cells = [Cell(10, i) for i in range(3, 6)]
        self.direction_of_head = self.cells[-1] - self.cells[-2]
        self.vision = self.get_vision()

    def get_vision(self):
        cells = [Cell(-1, 0), Cell(0, -1), Cell(1, 0), Cell(0, 1)]
        if -self.direction_of_head in cells:
            cells.remove(-self.direction_of_head)
        for cell in cells:
            cell.x += self.cells[-1].x
            cell.y += self.cells[-1].y
            cell %= Cell(WIDTH, HEIGHT)
        return cells

    def get_sensor(self, side: str):
        """Функция возвращает координату сенсора змеи(слева, справа, спереди)"""
        tongue = self.direction_of_head + self.cells[-1]  # Сенсор впереди змеи
        tongue %= Cell(WIDTH, HEIGHT)
        if side == 'forward':
            return tongue
        s = self.vision                         # В s хранятся координаты 3-х сенсоров [l_eye, tongue, r_eye]
        i = s.index(tongue)                     # относительно языка, глаза находятся слева и справа,
        if side == 'left':
            return s[(i - 1) % len(s)]
        elif side == 'right':
            return s[(i + 1) % len(s)]
        else:       # 'break'
            return self.cells[-1]

    def make_decision(self, apples):
        ways = ['left', 'forward', 'right']
        for side in ways:
            sensor = self.get_sensor(side)
            if see_apple(sensor, apples):
                return side
        if see_self(self.get_sensor('forward'), self.cells[-3::-1]) or random.randrange(10) == 0:
            if see_self(self.get_sensor('left'), self.cells[-3::-1]):
                return 'right'
            elif see_self(self.get_sensor('right'), self.cells[-3::-1]):
                return 'left'
            else:
                return random.sample(['left', 'right'], 1)[0]
        else:
            return 'forward'

    def move_to(self, side):
        """Функция перемещения змейки на одну ячейку в заданном направлении."""
        direction = self.get_sensor(side) - self.cells[-1]
        direction %= Cell(WIDTH, HEIGHT)
        if side is not None:
            self.cells.pop(0)
            new_head = self.cells[-1] + direction
            self.direction_of_head = direction
            # Если мир без границ, то закольцовываем координаты
            if EDGELESS:
                new_head %= Cell(WIDTH, HEIGHT)
            self.cells.append(new_head)
            self.vision = self.get_vision()

    def draw_snake(self):
        """Функция рисования змеи"""
        # голова змеи
        self.cells[-1].draw(SNAKE_OUTER_COLOR, HEAD_COLOR)
        # область зрения
        # for sensor in self.vision:
        #     sensor.draw(VISION_OUTER_COLOR, VISION_COLOR)
        # хвост змеи
        for item in self.cells[-2::-1]:
            item.draw(SNAKE_OUTER_COLOR, SNAKE_COLOR)

    def hit_edge(self):
        """Функция возвращает True,
        если змейка пересекла одну из границ окна."""
        if self.cells[-1] < Cell(0, 0) or self.cells[-1] > Cell(WIDTH, HEIGHT):
            return True

    def hit_apple(self, apples):
        """Функция возвращает True, если голова
        змейки находится в той же ячейке, что и яблоко."""
        for apple in apples:
            for cell in self.cells[-1::-1]:
                if cell == apple:
                    apples.remove(apple)
                    return True

    def grow(self):
        """Функция увеличения длины змейки."""
        self.cells.insert(0, self.cells[0])

    def bite_self(self):
        """Функция возвращает True, если голова змеи
        пересеклась хотя бы с одним блоком хвоста."""
        for cell in self.cells[:-1]:
            if self.cells[-1] == cell:
                return True, self.cells.index(cell)
        return False, -1


class Apple:
    def __init__(self):
        self.cells = [add_apple() for _ in range(LIMIT_OF_APPLES)]

    def draw_apple(self):
        for apple in self.cells:
            apple.draw(APPLE_OUTER_COLOR, APPLE_COLOR)


def main():
    global FPS_CLOCK
    global DISPLAY
    global viewport1, viewport2
    global font

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Wormy')
    viewport1 = create_viewport(WINDOW_WIDTH - WIDTH_VP2, WINDOW_HEIGHT)    # область мира змейки
    viewport2 = create_viewport(WIDTH_VP2, WINDOW_HEIGHT)   # боковая область, отображение длины змейки
    font = pygame.font.SysFont('couriernew', 12)
    while True:
        # Game... Game never changes.
        run_game()


def run_game():
    apples = Apple()
    snake = Snake()
    speed = 5   # Нужно переписать логику смены скорости, не завязываясь на FPS
    count_apple = 0
    max_len = len(snake.cells)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                # смена скорости змейки
                tmp = get_speed(event)
                if type(tmp) is int:
                    speed = tmp
        # При не закольцованном режиме, если змейка достигла границы окна, начать новую игру.
        if not EDGELESS and snake.hit_edge():
            break
        # Если змейка задела свой хвост:
        #   * оторвать хвост в месте касания
        #   * превратить хвост в яблоки
        bite_self, index = snake.bite_self()
        if bite_self:
            apples.cells.extend(snake.cells[0:index])
            snake.cells = snake.cells[index:]
        # Обработка ситуации столкновения змейки с яблоком.
        #  При столкновении:
        #   * увеличить размер змейки, если кол-во съеденных яблок равняется длине змейки
        #   * добавить новое яблоко
        if snake.hit_apple(apples.cells):
            count_apple += 1
            # Условие роста змейки.
            if count_apple >= len(snake.cells):
                count_apple = 0
                snake.grow()
            if len(apples.cells) <= LIMIT_OF_APPLES:
                apples.cells.append(add_apple())
                # Если яблоко на змее, то располагаем яблоко позади хвоста
                for cell in snake.cells:
                    if cell == apples.cells[-1]:
                        apples.cells[-1] = snake.cells[0] + (snake.cells[0] - snake.cells[1])
        # сдвинуть змейку в заданном направлении
        side = snake.make_decision(apples)
        snake.move_to(side)
        # Фиксирование максимальной длины, за сессию
        if max_len < len(snake.cells):
            max_len = len(snake.cells)
        s = f'Len:{len(snake.cells)} ({max_len})'
        text = font.render(s, True, TEXT_COLOR)
        draw_frame(snake, apples, text)

        FPS_CLOCK.tick(FPS * speed)


def draw_frame(snake, apples, text):
    viewport1.fill(BG_COLOR)
    viewport2.fill(GRID_COLOR)
    viewport2.blit(text, (3, 5))
    draw_grid()
    snake.draw_snake()
    apples.draw_apple()
    DISPLAY.blit(viewport1, (0, 0))
    DISPLAY.blit(viewport2, (WINDOW_WIDTH - WIDTH_VP2, 0))
    pygame.display.update()


def draw_grid():
    """Функция заполняет всю поверхность viewport, вертикальными и горизонтальными линиями с шагом CELL_SIZE пикселей"""
    for i in range(WIDTH + 1):
        pygame.draw.line(viewport1, GRID_COLOR, (i * CELL_SIZE, 0), (i * CELL_SIZE, viewport1.get_size()[1]))
    for i in range(HEIGHT):
        pygame.draw.line(viewport1, GRID_COLOR, (0, i * CELL_SIZE), (viewport1.get_size()[0], i * CELL_SIZE))


def add_apple():
    """Функция возвращает ячейку со случайными координатами Cell(x, y)."""
    return Cell(random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))


def see_apple(sensor, apples):
    """Если змея увидела яблоко, то функция возвращает True"""
    for apple in apples.cells:
        if sensor == apple:
            return True


def see_self(sensor, cells):
    """Если змея увидела себя, то функция возвращает True"""
    for cell in cells[0:-4]:
        if sensor == cell:
            return True


# def get_direction(event, direction):
#     """Функция возвращает направление движения.
#     Если нажата клавиша противоположного направления движения,
#     то не менять направление."""
#     if event.key == pygame.K_LEFT and direction.x != 1:
#         return Cell(-1, 0)
#     elif event.key == pygame.K_RIGHT and direction.x != -1:
#         return Cell(1, 0)
#     elif event.key == pygame.K_UP and direction.y != 1:
#         return Cell(0, -1)
#     elif event.key == pygame.K_DOWN and direction.y != -1:
#         return Cell(0, 1)
#     elif event.key == pygame.K_SPACE:  # остановка движения
#         return Cell(0, 0)
#     else:
#         return direction


def create_viewport(width, height):
    """Функция создает поверхность(Surface) с заданными размерами (width, height)"""
    surface = pygame.Surface((width, height))
    return surface


def get_speed(event):
    """Функция возвращает число от 1 до 5, в зависимости от нажатия клавиш 1-5"""
    if event.key == pygame.K_1:
        return 1
    elif event.key == pygame.K_2:
        return 2
    elif event.key == pygame.K_3:
        return 3
    elif event.key == pygame.K_4:
        return 4
    elif event.key == pygame.K_5:
        return 5


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()

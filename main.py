from copy import deepcopy

import pygame
import random
import sys

# Размеры окна в пикселях
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

# Размер сетки и ее рамки
CELL_SIZE = 20
BORDER_SIZE = 3

# Размеры сетки в ячейках
WIDTH = (WINDOW_WIDTH - 4 * CELL_SIZE) // CELL_SIZE
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

    def get_direction_of_head(self):
        d_last = self.direction_of_head
        d = self.cells[-1] - self.cells[-2]
        if -1 <= d.x <= 1 and -1 <= d.y <= 1:
            return d
        else:
            return d_last

    def get_vision(self):
        cells = [Cell(-1, 0), Cell(0, -1), Cell(1, 0), Cell(0, 1)]
        if -self.direction_of_head in cells:
            cells.remove(-self.direction_of_head)
        for cell in cells:
            cell.x += self.cells[-1].x
            cell.x %= WIDTH
            cell.y += self.cells[-1].y
            cell.y %= HEIGHT
        return cells

    def make_decision(self, apples):
        possible_way = deepcopy(self.vision)
        for eye in self.vision:
            if see_apple(eye, apples):
                return eye - self.cells[-1]
            if see_self(eye, self.cells):
                possible_way.remove(eye)
        if len(possible_way) == 3 or len(possible_way) == 0:
            if random.randrange(10) > 0:
                return self.direction_of_head
            else:
                return random.sample(possible_way, 1)[0] - self.cells[-1]
        if len(possible_way) < 3:
            return random.sample(possible_way, 1)[0] - self.cells[-1]

    def move(self, direction):
        """Функция перемещения змейки на одну ячейку в заданном направлении."""
        if direction != Cell(0, 0):
            self.cells.pop(0)
            new_head = self.cells[-1] + direction
            # Если мир без границ, то закольцовываем координаты
            if EDGELESS:
                new_head %= Cell(WIDTH, HEIGHT)
            self.cells.append(new_head)
            self.direction_of_head = self.get_direction_of_head()

    def draw_snake(self):
        """Функция рисования змеи"""
        # голова змеи
        self.cells[-1].draw(SNAKE_OUTER_COLOR, HEAD_COLOR)
        # область зрения
        for item in self.vision:
            item.draw(VISION_OUTER_COLOR, VISION_COLOR)
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
            if self.cells[-1] == apple:
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
        self.cells = [add_apple() for _ in range(10)]

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
    viewport1 = create_viewport(WINDOW_WIDTH-4*CELL_SIZE, WINDOW_HEIGHT)
    viewport2 = create_viewport(4*CELL_SIZE, WINDOW_HEIGHT)
    font = pygame.font.SysFont('couriernew', 12)
    while True:
        # Game... Game never changes.
        run_game()


def run_game():
    apples = Apple()
    snake = Snake()
    # исходное направление движения змейки.
    direction = snake.direction_of_head
    speed = 3
    count_apple = 0
    max_len = len(snake.cells)
    manual_control, count = False, 50
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                manual_control = True
                direction = get_direction(event, direction)
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
            if count_apple >= len(snake.cells):
                count_apple = 0
                snake.grow()
            if len(apples.cells) <= 10:
                apples.cells.append(add_apple())
                # Если яблоко на змее, то располагаем яблоко позади хвоста
                for cell in snake.cells:
                    if cell == apples.cells[-1]:
                        apples.cells[-1] = snake.cells[0] + (snake.cells[0] - snake.cells[1])
                        break
        if not manual_control:
            count = 20
            direction = snake.make_decision(apples)
        else:
            count -= 1
            if count <= 0:
                manual_control = False
        # сдвинуть змейку в заданном направлении
        snake.move(direction)
        snake.vision = snake.get_vision()
        if max_len < len(snake.cells):
            max_len = len(snake.cells)
        s = f'Len:{len(snake.cells)} ({max_len})'
        text = font.render(s, True, TEXT_COLOR)
        draw_frame(snake, apples, text)

        FPS_CLOCK.tick(FPS * speed)


def draw_frame(snake, apples, text):
    viewport1.fill(BG_COLOR)     # область мира змейки
    viewport2.fill(GRID_COLOR)
    viewport2.blit(text, (3, 5))
    draw_grid()
    snake.draw_snake()
    apples.draw_apple()
    DISPLAY.blit(viewport1, (0, 0))
    DISPLAY.blit(viewport2, (WINDOW_WIDTH - 4 * CELL_SIZE, 0))
    pygame.display.update()


def draw_grid():
    """Функция заполняет всю поверхность viewport, вертикальными и горизонтальными линиями с шагом CELL_SIZE пикселей"""
    for i in range(WIDTH+1):
        pygame.draw.line(viewport1, GRID_COLOR, (i * CELL_SIZE, 0), (i * CELL_SIZE, viewport1.get_size()[1]))
    for i in range(HEIGHT):
        pygame.draw.line(viewport1, GRID_COLOR, (0, i * CELL_SIZE), (viewport1.get_size()[0], i * CELL_SIZE))


def add_apple():
    """Функция возвращает ячейку со случайными координатами Cell(x, y)."""
    return Cell(random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))


def see_apple(eye, apples):
    """Если змея увидела яблоко, то функция возвращает True"""
    for apple in apples.cells:
        if eye == apple:
            return True


def see_self(eye, cells):
    """Если змея увидела себя, то функция возвращает True"""
    for cell in cells[0:-4]:
        if eye == cell:
            return True


def get_direction(event, direction):
    """Функция возвращает направление движения.
    Если нажата клавиша противоположного направления движения,
    то не менять направление."""
    if event.key == pygame.K_LEFT and direction.x != 1:
        return Cell(-1, 0)
    elif event.key == pygame.K_RIGHT and direction.x != -1:
        return Cell(1, 0)
    elif event.key == pygame.K_UP and direction.y != 1:
        return Cell(0, -1)
    elif event.key == pygame.K_DOWN and direction.y != -1:
        return Cell(0, 1)
    elif event.key == pygame.K_SPACE:  # остановка движения
        return Cell(0, 0)
    else:
        return direction


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

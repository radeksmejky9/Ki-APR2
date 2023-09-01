# Imports
import pygame as pg
import random
import os


# Classes


class Player:
    def __init__(self, name: str, color: pg.color, direction: bool):
        self.name = name
        self.color = color
        tile_y = GameBoard.screen_height if direction else 0
        self.home_tile = HomeTile(GameBoard.screen_width, tile_y, 30, "White")
        self.bar_tile = BarTile(GameBoard.screen_width / 14 * 7, tile_y, 30, "White")

    def paint(self, screen: pg.surface):
        self.home_tile.paint(screen)
        self.bar_tile.paint(screen)


class ClickManager:
    def __init__(self):
        self.current_tile = None

    def click(self, tiles: list, dices: list, turn_manager, position):
        # Highlighted bar stone clicked
        if len(turn_manager.player_on_turn.bar_tile.stones) > 0:
            for stone in turn_manager.player_on_turn.bar_tile.stones:
                if stone.highlighted and stone.circle_collider.collidepoint(position):
                    turn_manager.find_available_bar_moves(tiles, dices, True)
                    any_highlighted = False
                    for stone in turn_manager.player_on_turn.bar_tile.stones:
                        if stone.highlighted:
                            any_highlighted = True
                        if not any_highlighted:
                            turn_manager.player_on_turn = (
                                player1 if turn_manager.player_on_turn == player2 else player2
                            )
                    return
        # Highlighted tile clicked (bar)
        if len(turn_manager.player_on_turn.bar_tile.stones) > 0:
            for tile in tiles:
                if tile.highlighted and tile.tile_collider.collidepoint(position):
                    if len(tile.stones) == 0:
                        GameBoard.move_stone(turn_manager.player_on_turn.bar_tile, tile)
                        turn_manager.dice_value_used(
                            24 - tiles.index(tile),
                            tiles.index(tile) + 1,
                            dices,
                        )
                    elif len(tile.stones) > 0:
                        if tile.stones[0].player is turn_manager.player_on_turn:
                            GameBoard.move_stone(turn_manager.player_on_turn.bar_tile, tile)
                            turn_manager.dice_value_used(
                                24 - tiles.index(tile),
                                tiles.index(tile) + 1,
                                dices,
                            )
                        else:
                            GameBoard.move_stone(
                                tile,
                                player1.bar_tile if turn_manager.player_on_turn is not player1 else player2.bar_tile,
                            )
                            GameBoard.move_stone(turn_manager.player_on_turn.bar_tile, tile)
                            turn_manager.dice_value_used(
                                24 - tiles.index(tile),
                                tiles.index(tile) + 1,
                                dices,
                            )
                    return

        # Highlighted stone clicked
        for tile in tiles:
            for stone in tile.stones:
                if stone.highlighted and stone.circle_collider.collidepoint(position):
                    self.current_tile = tile
                    HighlightManager.unhighlight_all(tiles)
                    tile.highlight_stone()
                    turn_manager.find_available_turns(dices, tiles, tile, True)
                    return

        # Highlighted tile clicked
        for tile in tiles:
            if tile.highlighted and tile.tile_collider.collidepoint(position):
                HighlightManager.unhighlight_tiles(tiles)
                if len(tile.stones) < 1:
                    GameBoard.move_stone(self.current_tile, tile)
                elif len(tile.stones) == 1:
                    if self.current_tile.stones[0].player is tile.stones[0].player:
                        GameBoard.move_stone(self.current_tile, tile)
                    else:
                        GameBoard.move_stone(tile, tile.stones[0].player.bar_tile)
                        GameBoard.move_stone(self.current_tile, tile)
                elif len(tile.stones) > 1:
                    GameBoard.move_stone(self.current_tile, tile)
                turn_manager.dice_value_used(
                    tiles.index(self.current_tile) - tiles.index(tile),
                    tiles.index(tile) - tiles.index(self.current_tile),
                    dices,
                )
                return

        # No tile or stone clicked
        self.current_tile = None
        turn_manager.find_all_stones(tiles, dices, True)


class Stone:
    white_color = (255, 255, 255)
    black_color = (0, 0, 0)
    highlight_color = (255, 0, 0)
    highlight_thickness = 5
    base_radius = 25

    def __init__(self, player: Player):
        self.circle_collider = None
        self.highlighted = False
        self.player = player

    def paint(
        self,
        screen: pg.surface,
        x: float,
        y: float,
        num: int,
        x_shift: float,
        direction: bool,
        count: int,
    ):
        count_shift = count / 5 if count / 5 >= 1 else 1
        y_shift = (
            (y + (2 * self.base_radius) * (num / count_shift) + self.base_radius)
            if direction
            else (y + (2 * self.base_radius) * -(num / count_shift) - self.base_radius)
        )
        color = self.white_color if self.player.color == "White" else self.black_color
        self.circle_collider = pg.draw.circle(screen, color, (x + x_shift, y_shift), self.base_radius)
        if self.highlighted:
            pg.draw.circle(
                screen,
                self.highlight_color,
                (x + x_shift, y_shift),
                self.base_radius,
                self.highlight_thickness,
            )


class Tile:
    white_color = (133, 78, 35)
    black_color = (107, 74, 53)
    highlight_color = (255, 0, 0)
    highlight_thickness = 5
    height_multiplier = 3

    def __init__(self, pos_x: float, pos_y: float, size: float, color: pg.Color):
        self.tile_collider = None
        self.highlighted = False
        self.stones = []
        self.size = size
        self.color = color
        self.pos_x = pos_x
        self.pos_y = pos_y

    def add_stone(self, stone: Stone):
        self.stones.append(stone)

    def remove_stone(self):
        self.stones.pop()

    def paint(self, screen: pg.surface):
        tile_direction = self.size * self.height_multiplier if self.pos_y == 0 else -self.size * self.height_multiplier
        points = [
            [self.pos_x, self.pos_y],
            [self.pos_x + self.size / 2, self.pos_y + tile_direction],
            [self.pos_x + self.size, self.pos_y],
        ]

        self.tile_collider = pg.draw.polygon(
            screen,
            self.white_color if self.color == "White" else self.black_color,
            points,
        )

        if self.highlighted:
            pg.draw.polygon(screen, self.highlight_color, points, self.highlight_thickness)

        for i, stone in enumerate(self.stones):
            stone.paint(
                screen,
                self.pos_x,
                self.pos_y,
                i,
                self.size / 2,
                self.pos_y == 0,
                len(self.stones),
            )

    def highlight_stone(self):
        if len(self.stones) > 0:
            self.stones[-1].highlighted = True

    def unhighlight_stones(self):
        for stone in self.stones:
            stone.highlighted = False


class HomeTile(Tile):
    def __init__(self, pos_x: float, pos_y: float, size: float, color: pg.Color):
        super().__init__(pos_x, pos_y, size, color)

    def paint(self, screen: pg.surface):
        for i, stone in enumerate(self.stones):
            stone.paint(
                screen,
                self.pos_x - 2.22 * self.size,
                self.pos_y,
                i,
                self.size / 2,
                self.pos_y == 0,
                len(self.stones),
            )

    def add_stone(self, stone: Stone):
        return super().add_stone(stone)

    def remove_stone(self):
        return super().remove_stone()


class BarTile(Tile):
    def __init__(self, pos_x: float, pos_y: float, size: float, color: pg.Color):
        super().__init__(pos_x, pos_y, size, color)

    def paint(self, screen: pg.surface):
        for i, stone in enumerate(self.stones):
            stone.paint(
                screen,
                self.pos_x - 2.22 * self.size,
                self.pos_y,
                i,
                self.size / 2,
                self.pos_y == 0,
                len(self.stones),
            )

    def add_stone(self, stone: Stone):
        return super().add_stone(stone)

    def remove_stone(self):
        return super().remove_stone()

    def highlight_stone(self):
        if len(self.stones) > 0:
            self.stones[-1].highlighted = True

    def unhighlight_stones(self):
        for stone in self.stones:
            stone.highlighted = False


class GameBoard:
    screen_width = 1400
    screen_height = 800
    base_margin = 30
    box_color = (171, 117, 46)
    surface_color = (247, 236, 200)

    def __init__(self, player_one: Player, player_two: Player):
        self.tiles = []
        self.players = [player_one, player_two]
        self.turn_manager = TurnManager()
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))
        self.screen.fill(self.box_color)
        self.game_over = False

    def paint(self):
        for tile in self.tiles:
            tile.paint(self.screen)

    @staticmethod
    def move_stone(tile_from: Tile, tile_to: Tile):
        if len(tile_from.stones) != 0:
            tile_to.add_stone(tile_from.stones[-1])
            tile_from.remove_stone()
        else:
            return


class Dice:
    base_size = 100
    dot_base_size = 10
    border_radius = 15
    color_available = (240, 240, 240)
    color_disabled = (125, 125, 125)

    def __init__(self, pos_x: float, pos_y: float):
        self.roll_used = False
        self.value = 1
        self.pos_x = pos_x - self.base_size / 2
        self.pos_y = pos_y - self.base_size / 2

    def throw(self, rand_from: int, rand_to: int):
        self.roll_used = False
        self.value = random.randint(rand_from, rand_to)

    def paint(self, screen: pg.surface):
        base_rect = [self.pos_x, self.pos_y, self.base_size, self.base_size]
        if self.roll_used:
            pg.draw.rect(screen, self.color_disabled, base_rect, 0, self.border_radius)
        else:
            pg.draw.rect(screen, self.color_available, base_rect, 0, self.border_radius)

        match self.value:
            case 1:
                self.paint_one(screen)
            case 2:
                self.paint_two(screen)
            case 3:
                self.paint_one(screen)
                self.paint_two(screen)
            case 4:
                self.paint_two(screen)
                self.paint_four(screen)
            case 5:
                self.paint_one(screen)
                self.paint_two(screen)
                self.paint_four(screen)
            case 6:
                self.paint_four(screen)
                self.paint_two(screen)
                self.paint_six(screen)

    def paint_one(self, screen: pg.Surface):
        pg.draw.circle(
            screen,
            "Black",
            [
                self.pos_x + self.base_size // 2,
                self.pos_y + self.base_size // 2,
            ],
            self.dot_base_size,
        )

    def paint_two(self, screen: pg.Surface):
        pg.draw.circle(
            screen,
            "Black",
            [
                self.pos_x + self.base_size // 5,
                self.pos_y + self.base_size // 5,
            ],
            self.dot_base_size,
        )
        pg.draw.circle(
            screen,
            "Black",
            [
                self.pos_x + self.base_size // 5 * 4,
                self.pos_y + self.base_size // 5 * 4,
            ],
            self.dot_base_size,
        )

    def paint_four(self, screen: pg.Surface):
        pg.draw.circle(
            screen,
            "Black",
            [
                self.pos_x + self.base_size // 5,
                self.pos_y + self.base_size // 5 * 4,
            ],
            self.dot_base_size,
        )
        pg.draw.circle(
            screen,
            "Black",
            [
                self.pos_x + self.base_size // 5 * 4,
                self.pos_y + self.base_size // 5,
            ],
            self.dot_base_size,
        )

    def paint_six(self, screen: pg.Surface):
        pg.draw.circle(
            screen,
            "Black",
            [
                self.pos_x + self.base_size // 5,
                self.pos_y + self.base_size // 2,
            ],
            self.dot_base_size,
        )
        pg.draw.circle(
            screen,
            "Black",
            [
                self.pos_x + self.base_size // 5 * 4,
                self.pos_y + self.base_size // 2,
            ],
            self.dot_base_size,
        )


class TurnManager:
    available_turns = []
    player_changed = True

    def __init__(self):
        self._turn_history = []
        self.player_on_turn = None

    @property
    def player_on_turn(self):
        return self._player_on_turn

    @player_on_turn.setter
    def player_on_turn(self, value: Player):
        self._player_on_turn = value
        self.player_changed = True

    def find_all_stones(self, tiles: list, dices: list, highlight: bool):
        HighlightManager.unhighlight_all(tiles)
        available_tile_indexes = []
        if len(turn_manager.player_on_turn.bar_tile.stones) > 0:
            for result in self.find_available_bar_moves(tiles, dices, False):
                if result is True:
                    if highlight is True:
                        turn_manager.player_on_turn.bar_tile.highlight_stone()
                    else:
                        available_tile_indexes.append(True)
                else:
                    if not highlight:
                        available_tile_indexes.append(False)

        else:
            for tile in tiles:
                if len(tile.stones) > 0:
                    if tile.stones[0].player == self.player_on_turn:
                        for result in self.find_available_turns(dices, tiles, tile, False):
                            if result is True:
                                if highlight is True:
                                    tile.highlight_stone()
                                else:
                                    available_tile_indexes.append(True)
                            else:
                                if not highlight:
                                    available_tile_indexes.append(False)
        return available_tile_indexes

    def find_available_bar_moves(self, tiles: list, dices: list, highlight: bool):
        results = []
        if turn_manager.player_on_turn == player1:
            for dice in dices:
                results.append(self.find_available_bar_move(tiles, tiles[dice.value - 1], dices, highlight))
        else:
            for dice in dices:
                results.append(self.find_available_bar_move(tiles, tiles[24 - dice.value], dices, highlight))
        return results

    def find_available_bar_move(self, tiles: list, tile: Tile, dices: list, highlight: bool):
        if len(tile.stones) <= 1:
            if highlight:
                tile.highlighted = True
            else:
                return True
        if len(tile.stones) > 1:
            if turn_manager.player_on_turn == tile.stones[0].player:
                if highlight:
                    tile.highlighted = True
                else:
                    return True
        elif not highlight:
            return False
        return False

    def find_available_turns(self, dices: list, tiles: list, tile: Tile, highlight: bool):
        tile_index = tiles.index(tile)
        results = []
        for dice in dices:
            if dice.roll_used is False:
                if tile_index - dice.value > 0 and self.player_on_turn == player2:
                    results.append(self.find_available_turn(tiles, tile_index - dice.value, highlight))
                elif tile_index + dice.value < 24 and self.player_on_turn == player1:
                    results.append(self.find_available_turn(tiles, tile_index + dice.value, highlight))
        return results

    def find_available_turn(self, tiles: list, tile_index: int, highlight: bool):
        if len(tiles[tile_index].stones) <= 1:
            if highlight:
                tiles[tile_index].highlighted = True
            else:
                return True
        elif len(tiles[tile_index].stones) > 0:
            if tiles[tile_index].stones[0].player == self._player_on_turn:
                if highlight:
                    tiles[tile_index].highlighted = True
                else:
                    return True
        else:
            if not highlight:
                return False

    def dice_value_used(self, value1: int, value2: int, dices: list):
        dice_value = value1 if self.player_on_turn == player2 else value2
        rolls_used = 0
        value_changed = False
        for dice in dices:
            if dice.value == dice_value and value_changed is False and dice.roll_used is False:
                dice.roll_used = True
                value_changed = True
            if dice.roll_used is False:
                self.find_all_stones(tiles, dices, True)
            else:
                rolls_used += 1
            if rolls_used == 2:
                self.player_on_turn = player1 if self.player_on_turn == player2 else player2
                self.find_all_stones(tiles, dices, True)


class HighlightManager:
    @staticmethod
    def unhighlight_all(tiles: list):
        for tile in tiles:
            tile.highlighted = False
            tile.unhighlight_stones()
            turn_manager.player_on_turn.bar_tile.unhighlight_stones()

    @staticmethod
    def unhighlight_tiles(tiles: list):
        for tile in tiles:
            tile.highlighted = False

    @staticmethod
    def unhighlight_stones(tiles: list):
        for tile in tiles:
            tile.unhighlight_stones()


# Game initialization

player1 = Player("Player1", "White", True)
player2 = Player("Player2", "Black", False)

click_manager = ClickManager()
game_board = GameBoard(player1, player2)
turn_manager = TurnManager()
turn_manager.player_on_turn = player1

# Dices
dices = [
    Dice(game_board.screen_width / 12 * 10, game_board.screen_height / 2),
    Dice(game_board.screen_width / 12 * 11, game_board.screen_height / 2),
]


# Tiles
tiles = game_board.tiles
for y in range(2):
    for x in range(13):
        if x == 6:
            continue
        tile_x = (
            x * game_board.screen_width / 14
            if y == 1
            else game_board.screen_width - (x + 2) * game_board.screen_width / 14
        )
        tile_y = game_board.screen_height if y == 1 else 0
        color = (
            (player1.color if x % 2 == 0 else player2.color)
            if y == 1
            else (player1.color if x % 2 == 1 else player2.color)
        )
        game_board.tiles.append(Tile(tile_x, tile_y, game_board.screen_width / 14, color))


positions = [
    (11, player1, 5),
    (12, player2, 5),
    (18, player1, 5),
    (5, player2, 5),
    (16, player1, 3),
    (7, player2, 3),
    (0, player1, 2),
    (23, player2, 2),
]

for pos, player, count in positions:
    for i in range(count):
        tiles[pos].add_stone(Stone(player))


# General PyGame setup
pg.init()

# Set up the game
running = True


def stop_game():
    global running
    running = False


clock = pg.time.Clock()

# Game loop
while running:
    # Event handling
    for event in pg.event.get():
        if event.type == pg.QUIT:
            os._exit(1)
        elif event.type == pg.MOUSEBUTTONUP:
            click_manager.click(tiles, dices, turn_manager, pg.mouse.get_pos())

    # Game over check
    if game_board.game_over:
        # TODO: handle UI for win/loss
        pass

    # Draw elements
    for dice in dices:
        dice.paint(game_board.screen)
    game_board.paint()
    player1.paint(game_board.screen)
    player2.paint(game_board.screen)

    # Handle turn change
    if turn_manager.player_changed:
        turn_manager.player_changed = False
        for dice in dices:
            dice.throw(1, 6)
            turn_manager.find_all_stones(game_board.tiles, dices, True)

    # PyGame Code
    pg.display.flip()
    clock.tick(60)
    game_board.screen.fill(game_board.box_color)

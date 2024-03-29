import pygame
import sys
import time

# Initialize Pygame
pygame.init()

# Constants for the game window and board
WINDOW_SIZE = 820
BOARD_SIZE = 600
GRID_SIZE = 9
LINE_SPACING = BOARD_SIZE // (GRID_SIZE - 1)
RADIUS = LINE_SPACING // 2 - 5

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Set up the window
window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Go Game")

# Load and scale the background image
background_image = pygame.image.load('background.jpg')
background_image = pygame.transform.scale(background_image, (WINDOW_SIZE, WINDOW_SIZE))

# Board state, current player, and timers
board_state = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
current_player = 1 # 1 -> black, -1 -> white
last_time_switch = time.time()
black_time = 0.0
white_time = 0.0
komi = 5.5
pass_count = 0  # To track consecutive passes

# Define resign button properties
resign_button_color = (100, 100, 100)  # Grey color
resign_button_position = (610, 750)  # Bottom right
resign_button_size = (100, 30)
resign_button_text = 'Resign'

# Define pass button properties
pass_button_color = (100, 100, 100)  # Grey color
pass_button_position = (490, 750)  # Bottom right
pass_button_size = (100, 30)
pass_button_text = 'Pass'


game_over = False

# Track the board history
board_history = []

# Create a log message system
log_messages = []

# Font for displaying counts and timers
font = pygame.font.Font(None, 36)
fontlog = pygame.font.Font(None, 25)


def update_time():
    global black_time, white_time, last_time_switch
    current_time = time.time()
    if current_player == 1:
        black_time += current_time - last_time_switch
    else:
        white_time += current_time - last_time_switch
    last_time_switch = current_time

def draw_board():
    global black_time, white_time, log_messages, current_player

    # Draw the background image
    window.blit(background_image, (0, 0))

    top_left_x = (WINDOW_SIZE - BOARD_SIZE) // 2
    top_left_y = (WINDOW_SIZE - BOARD_SIZE) // 2

    # Draw the grid
    for i in range(GRID_SIZE):
        pygame.draw.line(window, BLACK, (top_left_x + i * LINE_SPACING, top_left_y),
                         (top_left_x + i * LINE_SPACING, top_left_y + BOARD_SIZE - 1))
        pygame.draw.line(window, BLACK, (top_left_x, top_left_y + i * LINE_SPACING),
                         (top_left_x + BOARD_SIZE - 1, top_left_y + i * LINE_SPACING))

    # Draw the stones and count them
    black_stones = white_stones = 0
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board_state[row][col]:
                color = BLACK if board_state[row][col] == 1 else WHITE
                pygame.draw.circle(window, color, (top_left_x + col * LINE_SPACING, top_left_y + row * LINE_SPACING), RADIUS)
                if board_state[row][col] == 1:
                    black_stones += 1
                else:
                    white_stones += 1

    # Display the stone counts
    black_count_text = font.render(f'Black Stones: {black_stones}', True, BLACK)
    white_count_text = font.render(f'White Stones: {white_stones}', True, WHITE)
    window.blit(black_count_text, (10, 10))
    window.blit(white_count_text, (WINDOW_SIZE - white_count_text.get_width() - 10, 10))

    # Update and display the timers
    update_time()
    black_timer_text = font.render(f'Black Time: {black_time:.1f}', True, BLACK)
    white_timer_text = font.render(f'White Time: {white_time:.1f}', True, WHITE)
    window.blit(black_timer_text, (10, 40))
    window.blit(white_timer_text, (WINDOW_SIZE - white_timer_text.get_width() - 10, 40))

    # Display the current player's turn
    player_name = "Player 1" if current_player == 1 else "Player 2"
    text_color_move = BLACK if current_player == 1 else WHITE
    current_player_text = font.render(f"{player_name}'s Turn", True, text_color_move)
    text_rect = current_player_text.get_rect(center=(WINDOW_SIZE // 2, 50))
    window.blit(current_player_text, text_rect)

    # Display log messages
    log_x = 110  # Starting x position for log messages
    log_y = 720  # Starting y position for log messages
    for message, player in log_messages[-5:]:  # Display the last 10 messages
        text_color = BLACK if player == 1 else WHITE
        log_text = fontlog.render(message, True, text_color)
        window.blit(log_text, (log_x, log_y))
        log_y += 15  # Increment y position for next message

    # Draw the resign button
    draw_resign_button()

    # Draw the pass button
    draw_pass_button()

    pygame.display.flip()  # Update the display

def is_valid_move(board, row, col, player):
    if row < 0 or row >= GRID_SIZE or col < 0 or col >= GRID_SIZE:
        return False  # Move is outside the board
    if board[row][col] is not None:
        return False  # Cell is already occupied

    # Temporarily place the stone to check for liberties or capture
    board[row][col] = player
    group, liberties = check_liberties(row, col, board)
    opponent = -player
    capture = any(check_liberties(r, c, board)[1] == 0 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)] for r, c in [(row + dr, col + dc)] if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and board[r][c] == opponent)
    
    # Undo the temporary move
    board[row][col] = None

    return liberties > 0 or capture

def remove_captured_stones(group, board):
    for (r, c) in group:
        board[r][c] = None

def check_liberties(row, col, board, checked=None):
    if checked is None:
        checked = set()
    if (row, col) in checked or board[row][col] is None:
        return set(), 0
    checked.add((row, col))
    player = board[row][col]
    liberties = 0
    group = {(row, col)}
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r, c = row + dr, col + dc
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            if board[r][c] is None:
                liberties += 1
            elif board[r][c] == player and (r, c) not in checked:
                additional_group, additional_liberties = check_liberties(r, c, board, checked)
                liberties += additional_liberties
                group.update(additional_group)
    return group, liberties

def board_copy(board):
    return [row[:] for row in board]

def is_ko(board):
    return board in board_history

def capture_stones(row, col, board_state, opponent):
    captured_stones = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Check all four directions
        r, c = row + dr, col + dc
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and board_state[r][c] == opponent:
            group, liberties = check_liberties(r, c, board_state)
            if liberties == 0:
                captured_stones.extend(group)  # Add captured group positions
                remove_captured_stones(group, board_state)
    return captured_stones  # Return a list of positions


def calculate_territory(board, player):
    visited = set()
    territory_count = 0

    def is_enclosed(row, col, player):
        if (row, col) in visited or row < 0 or row >= GRID_SIZE or col < 0 or col >= GRID_SIZE:
            return True
        if board[row][col] is None:
            visited.add((row, col))
            return all(is_enclosed(row + dr, col + dc, player) for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)])
        return board[row][col] == player

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] is None and (row, col) not in visited:
                if is_enclosed(row, col, player):
                    territory_count += 1

    return territory_count

def calculate_points(board_state, komi=5.5):
    black_points = 0
    white_points = komi  # White gets an initial komi score
    captured_territories = {'Black': 0, 'White': 0}

    # Count stones on the board
    for row in board_state:
        for cell in row:
            if cell == 1:  # 1 represents black stones
                black_points += 1
            elif cell == -1:  # -1 represents white stones
                white_points += 1

    # Calculate captured territories (this requires a proper implementation)
    captured_territories['Black'] = calculate_territory(board_state, 1)
    captured_territories['White'] = calculate_territory(board_state, -1)

    # Add captured territories to the score
    black_points += captured_territories['Black']
    white_points += captured_territories['White']

    # Handle start points
    black_points -= 1
    white_points -= 1

    return black_points, white_points


def handle_mouse_click(pos):
    global current_player, last_time_switch, board_history, board_state, log_messages, pass_count

    x, y = pos
    row, col = get_closest_intersection(x, y)

    if row is not None and col is not None:
        if is_valid_move(board_state, row, col, current_player):
            board_state[row][col] = current_player
            update_time()

            # Add log message for stone placement
            player_name = "1" if current_player == 1 else "2"
            log_messages.append((f"Player {player_name} placed stone at ({row}, {col})", current_player))

            captured_stones = capture_stones(row, col, board_state, -current_player)
            if captured_stones:
                # Add log message for captures
                captured_positions = ', '.join(f"({r}, {c})" for r, c in captured_stones)
                log_messages.append((f"Stones captured at: {captured_positions}", current_player))

            # Check for Ko
            if is_ko(board_state):
                # Undo the move if it's a Ko
                board_state[row][col] = None
            else:
                board_history.append(board_copy(board_state))
                current_player = -current_player

            # Reset pass count on a regular move
            pass_count = 0
            
            draw_board()

def get_closest_intersection(x, y):
    top_left_x = (WINDOW_SIZE - BOARD_SIZE) // 2
    top_left_y = (WINDOW_SIZE - BOARD_SIZE) // 2

    row = round((y - top_left_y) / LINE_SPACING)
    col = round((x - top_left_x) / LINE_SPACING)

    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return row, col
    return None, None


def draw_pass_button():
    pygame.draw.rect(window, pass_button_color, (*pass_button_position, *pass_button_size))
    button_font = pygame.font.Font(None, 32)
    text_surf = button_font.render(pass_button_text, True, WHITE)
    text_rect = text_surf.get_rect(center=(pass_button_position[0] + pass_button_size[0] // 2, pass_button_position[1] + pass_button_size[1] // 2))
    window.blit(text_surf, text_rect)

def is_pass_button_clicked(pos):
    x, y = pos
    return (pass_button_position[0] <= x <= pass_button_position[0] + pass_button_size[0] and 
            pass_button_position[1] <= y <= pass_button_position[1] + pass_button_size[1])

def handle_pass():
    global current_player, pass_count, log_messages, game_over

    pass_count += 1  # Increment pass count

    # Add log message for pass
    player_name = "1" if current_player == 1 else "2"
    log_messages.append((f"Player {player_name} passed", current_player))

    # Switch player
    current_player = -current_player

    # Check if both players passed consecutively
    if pass_count == 2:
        handle_game_end()
        game_over = True
    else:
        draw_board()

def handle_game_end():
    global game_over
    window.blit(background_image, (0, 0))  # Clear screen with background

    black_score, white_score = calculate_points(board_state)

    if black_score > white_score:
        win_message = f"Player 1 won!"
        win_color = BLACK
    else:
        win_message = f"Player 2 won!"
        win_color = WHITE
    
    win_font = pygame.font.Font(None, 68)
    win_text = win_font.render(win_message, True, win_color)
    win_rect = win_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 150))
    window.blit(win_text, win_rect)

    black_score_font = pygame.font.Font(None, 55)
    black_score_text = black_score_font.render(f"Player 1: {black_score} points", True, BLACK)
    black_score_rect = black_score_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    window.blit(black_score_text, black_score_rect)

    white_score_font = pygame.font.Font(None, 55)
    white_score_text = white_score_font.render(f"Player 2: {white_score} points", True, WHITE)
    white_score_rect = white_score_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 80))
    window.blit(white_score_text, white_score_rect)
    
    
    pygame.display.flip()
    game_over = True



def draw_resign_button():
    pygame.draw.rect(window, resign_button_color, (*resign_button_position, *resign_button_size))
    button_font = pygame.font.Font(None, 32)
    text_surf = button_font.render(resign_button_text, True, WHITE)
    text_rect = text_surf.get_rect(center=(resign_button_position[0] + resign_button_size[0] // 2, resign_button_position[1] + resign_button_size[1] // 2))
    window.blit(text_surf, text_rect)

def is_resign_button_clicked(pos):
    x, y = pos
    return (resign_button_position[0] <= x <= resign_button_position[0] + resign_button_size[0] and 
            resign_button_position[1] <= y <= resign_button_position[1] + resign_button_size[1])

def handle_resign():
    global current_player, game_over
    window.blit(background_image, (0, 0))  # Clear screen with background

    winner = "1" if current_player == -1 else "2"
    win_color = WHITE if current_player == 1 else BLACK
    win_message = f"Player {winner} won the game by resign"
    
    win_font = pygame.font.Font(None, 48)
    win_text = win_font.render(win_message, True, win_color)
    win_rect = win_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    window.blit(win_text, win_rect)

    game_over = True 
    
    pygame.display.flip()

    # Optionally, add a delay or wait for a key press before closing the game


# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if not game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if is_resign_button_clicked(event.pos):
                    handle_resign()
                elif is_pass_button_clicked(event.pos):
                    handle_pass()
                else:
                    pass_count = 0  # Reset pass count on any move
                    handle_mouse_click(event.pos)

    if not game_over:
        draw_board()

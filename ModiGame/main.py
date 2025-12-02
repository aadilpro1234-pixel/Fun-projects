import pygame
import sys
import random

pygame.init()

# -------------------------------------------------
# WINDOW SETUP
# -------------------------------------------------
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Modi Game")
clock = pygame.time.Clock()

# FONTS
BASE_FONT_SIZE = 50
font = pygame.font.SysFont(None, BASE_FONT_SIZE)
small_font = pygame.font.SysFont(None, 20)

# -------------------------------------------------
# BACKGROUND
# -------------------------------------------------
bg = pygame.image.load("assets/background.png").convert()
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
bg_x = 0

# -------------------------------------------------
# PLAYER
# -------------------------------------------------
modi_img = pygame.image.load("assets/modi.png").convert_alpha()
modi_img = pygame.transform.scale(modi_img, (40, 40))
modi_rect = modi_img.get_rect(center=(100, 300))

# -------------------------------------------------
# PIPES
# -------------------------------------------------
pipe_img = pygame.image.load("assets/pipe.png").convert_alpha()
pipe_img = pygame.transform.scale(pipe_img, (40, 450))

PIPE_GAP = 140
PIPE_SPEED = 3
pipe_list = []

# -------------------------------------------------
# PHYSICS
# -------------------------------------------------
gravity = 0.0            # vertical velocity
jump_strength = -8

# -------------------------------------------------
# SCORE
# -------------------------------------------------
score = 0
passed_pipes = set()

# -------------------------------------------------
# GAME STATE
# -------------------------------------------------
GAME_ACTIVE = True

# -------------------------------------------------
# PIPE TIMER
# -------------------------------------------------
SPAWN_PIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWN_PIPE, 1400)

# -------------------------------------------------
# SOUNDS
# -------------------------------------------------
pygame.mixer.music.load("assets/modi.song.ogg")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)

death_sound = pygame.mixer.Sound("assets/Death.sound.ogg")
death_sound.set_volume(0.5)

# -------------------------------------------------
# ADMIN FLAGS
# -------------------------------------------------
console_active = False
console_text = ""

noclip = False
godmode = False

# Small helper to log to terminal so you can see commands
def log(msg):
    print("[GAME]", msg)

# -------------------------------------------------
# ADMIN CONSOLE COMMANDS
# -------------------------------------------------
def run_console_command(cmd):
    global noclip, godmode, score, PIPE_SPEED, gravity, jump_strength, GAME_ACTIVE

    parts = cmd.strip().split()
    if len(parts) == 0:
        return

    # lowercase for robust parsing
    parts = [p.lower() for p in parts]

    # Noclip
    if parts[0] == "noclip":
        if len(parts) == 2 and parts[1] in ("on", "off", "true", "false", "1", "0", "yes", "no"):
            noclip = parts[1] in ("on", "true", "1", "yes")
            log(f"noclip -> {noclip}")
        else:
            log("usage: noclip on/off")
        return

    # Godmode
    if parts[0] in ("god", "godmode"):
        if len(parts) == 2 and parts[1] in ("on", "off", "true", "false", "1", "0", "yes", "no"):
            godmode = parts[1] in ("on", "true", "1", "yes")
            log(f"godmode -> {godmode}")
        else:
            log("usage: godmode on/off")
        return

    # Score
    if parts[0] == "score":
        if len(parts) == 2 and parts[1].lstrip("-").isdigit():
            score = int(parts[1])
            log(f"score -> {score}")
        else:
            log("usage: score <number>")
        return

    # Pipe speed
    if parts[0] == "speed":
        if len(parts) == 2:
            try:
                PIPE_SPEED = float(parts[1])
                log(f"pipe speed -> {PIPE_SPEED}")
            except ValueError:
                log("speed argument must be a number")
        return

    # Gravity (sets the current vertical velocity baseline; use with care)
    if parts[0] == "gravity":
        if len(parts) == 2:
            try:
                gravity = float(parts[1])
                log(f"gravity -> {gravity}")
            except ValueError:
                log("gravity argument must be a number")
        return

    # Jump strength
    if parts[0] == "jump":
        if len(parts) == 2:
            try:
                jump_strength = -abs(float(parts[1]))
                log(f"jump_strength -> {jump_strength}")
            except ValueError:
                log("jump argument must be a number")
        return

    # Kill command (instantly ends the run, freezes gravity)
    if parts[0] == "kill":
        GAME_ACTIVE = False
        gravity = 0.0
        log("kill executed -> GAME_ACTIVE = False")
        return

    log("unknown command")

# -------------------------------------------------
# PIPE FUNCTIONS
# -------------------------------------------------
def create_pipe():
    height = random.randint(150, 400)
    pair_id = random.random()
    bottom_rect = pipe_img.get_rect(midtop=(450, height + PIPE_GAP))
    top_rect = pipe_img.get_rect(midbottom=(450, height))
    return (bottom_rect, pair_id), (top_rect, pair_id)

def move_pipes(pipes):
    new_list = []
    for rect, pid in pipes:
        rect.centerx -= PIPE_SPEED
        if rect.right > 0:
            new_list.append((rect, pid))
    return new_list

def draw_pipes(pipes):
    for rect, pid in pipes:
        if rect.bottom >= HEIGHT:
            screen.blit(pipe_img, rect)
        else:
            flipped = pygame.transform.flip(pipe_img, False, True)
            screen.blit(flipped, rect)

def check_collision(rect, pipes):
    """
    Returns True if a collision should cause death, taking into account noclip.
    If noclip is True -> never collide.
    """
    global noclip
    if noclip:
        return False

    # Pipe collisions
    for p_rect, pid in pipes:
        if rect.colliderect(p_rect):
            return True

    # Ceiling/floor
    if rect.top <= 0 or rect.bottom >= HEIGHT:
        return True

    return False

def reset_game():
    global gravity, pipe_list, modi_rect, score, passed_pipes, GAME_ACTIVE
    gravity = 0.0
    pipe_list = []
    score = 0
    passed_pipes = set()
    modi_rect = modi_img.get_rect(center=(100, 300))
    GAME_ACTIVE = True

# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Toggle console: CTRL+SHIFT+C
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL and mods & pygame.KMOD_SHIFT:
                console_active = not console_active
                console_text = ""
                log(f"console_active -> {console_active}")

        # Quick keyboard toggles for testing (bypass console)
        if event.type == pygame.KEYDOWN and not console_active:
            if event.key == pygame.K_n:  # toggle noclip
                noclip = not noclip
                log(f"[hotkey] noclip -> {noclip}")
            if event.key == pygame.K_g:  # toggle godmode
                godmode = not godmode
                log(f"[hotkey] godmode -> {godmode}")

        # Console input (when open)
        if console_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    run_console_command(console_text)
                    console_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    console_text = console_text[:-1]
                else:
                    if len(event.unicode) > 0:
                        console_text += event.unicode
            # continue prevents gameplay while console is open
            continue

        # Gameplay input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if GAME_ACTIVE:
                    gravity = jump_strength
                else:
                    reset_game()

        # Pipe spawn
        if event.type == SPAWN_PIPE and GAME_ACTIVE:
            pipe_list.extend(create_pipe())

    # -------------------------------------------------
    # GAME LOGIC
    # -------------------------------------------------
    if GAME_ACTIVE:

        # Background
        bg_x -= 1
        if bg_x <= -WIDTH:
            bg_x = 0

        screen.blit(bg, (bg_x, 0))
        screen.blit(bg, (bg_x + WIDTH, 0))

        # Gravity: only apply if NOT godmode
        if not godmode:
            gravity += 0.5
            modi_rect.y += gravity
        else:
            # freeze vertical velocity while in godmode so you float
            gravity = 0.0

        # Pipes
        pipe_list = move_pipes(pipe_list)
        draw_pipes(pipe_list)

        # Score
        for rect, pid in pipe_list:
            if rect.centerx < modi_rect.centerx and pid not in passed_pipes:
                score += 1
                passed_pipes.add(pid)

        # Player draw
        screen.blit(modi_img, modi_rect)

        # Score text
        score_text = font.render(str(score), True, (255, 255, 255))
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 20))

        # Collision check (check_collision already respects noclip)
        collided = check_collision(modi_rect, pipe_list)
        if collided and not godmode:
            death_sound.play()
            GAME_ACTIVE = False

    else:
        screen.fill((0, 0, 0))
        font_big = pygame.font.SysFont(None, 70)

        game_over_text = font_big.render("GAME OVER", True, (255, 0, 0))
        final_score_text = font.render(f"Score: {score}", True, (255, 255, 0))
        restart_text = font.render("Press SPACE to Restart", True, (255, 255, 255))

        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 100))
        screen.blit(final_score_text, (WIDTH//2 - final_score_text.get_width()//2, HEIGHT//2 - 20))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))

    # -------------------------------------------------
    # ADMIN PANEL UI
    # -------------------------------------------------
    if console_active:
        panel_height = 140
        panel_y = HEIGHT - panel_height - 10

        panel = pygame.Surface((WIDTH, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 190))
        screen.blit(panel, (0, panel_y))

        pygame.draw.rect(screen, (0, 255, 0), (0, panel_y, WIDTH, panel_height), 3)

        title = pygame.font.SysFont(None, 32).render("[ ADMIN CONSOLE ]", True, (0, 255, 0))
        screen.blit(title, (10, panel_y + 10))

        entered = font.render("> " + console_text, True, (0, 255, 0))
        screen.blit(entered, (10, panel_y + 70))

    pygame.display.update()

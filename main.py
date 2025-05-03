import tkinter as tk
from tkinter import messagebox
import random
import threading
import time
import pygame  # Sound support

# Initialize Pygame mixer
pygame.init()
pygame.mixer.init()

# Load sounds
dice_sound = pygame.mixer.Sound("dice_roll.wav")
tick_sound = pygame.mixer.Sound("tick.wav")
tick_channel = pygame.mixer.Channel(1)

# Constants
DICE_SIZE = 60
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 400
MIN_DICE = 3
MAX_DICE = 6
REWARD = 4
PENALTY = 1
TURN_TIME = 20
turn_timer_id = None
game_over = False

PIP_OFFSETS = {
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.5), (0.75, 0.5), (0.25, 0.75), (0.75, 0.75)],
}

# Game state
correctAnswer = 0
incorrectAnswer = 0
score = 0
currentTotal = 0
timeLeft = TURN_TIME

# Tkinter UI
root = tk.Tk()
root.title("Dice Math Game")

canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
canvas.pack()

timer_label = tk.Label(root, text=f"Time Left: {timeLeft}s", font=("Arial", 14))
timer_label.pack()

score_label = tk.Label(root, text=f"Correct: 0 | Incorrect: 0 | Score: 0", font=("Arial", 14))
score_label.pack(pady=5)
answer_frame = tk.Frame(root)
answer_frame.pack(pady=5)

answer_label = tk.Label(answer_frame, text="")
answer_label.pack(side=tk.LEFT)

answer_entry = tk.Entry(answer_frame, width=10, font=("Arial", 14))
answer_entry.pack(side=tk.LEFT)
answer_entry.bind("<Return>", lambda event: check_answer())

submit_button = tk.Button(answer_frame, text="Submit", command=lambda: check_answer())
submit_button.pack(side=tk.LEFT)


def overlaps(x, y, positions):
    for px, py in positions:
        if (abs(px - x) < DICE_SIZE) and (abs(py - y) < DICE_SIZE):
            return True
    return False

def draw_die(x, y, value):
    canvas.create_rectangle(x, y, x + DICE_SIZE, y + DICE_SIZE, fill="white", outline="black", width=2)
    for dx, dy in PIP_OFFSETS[value]:
        cx = x + dx * DICE_SIZE
        cy = y + dy * DICE_SIZE
        r = 5
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="black")

def update_score_labels():
    score_label.config(text=f"Correct: {correctAnswer} | Incorrect: {incorrectAnswer} | Score: {score}")

def play_dice_sound():
    dice_sound.play()

def countdown_timer():
    global timeLeft, game_over, turn_timer_id

    while timeLeft > 0 and not game_over:
        time.sleep(1)
        timeLeft -= 1
        if timer_label.winfo_exists():
            timer_label.after(0, lambda: timer_label.config(text=f"Time Left: {timeLeft}s"))

        if timeLeft == 0:
            root.after(0, end_game)
            break

def start_ticking():
    if not tick_channel.get_busy():
        tick_channel.play(tick_sound, loops=-1)
        adjust_ticking_volume()

def adjust_ticking_volume():
    # Adjust tick sound volume based on time left (10s → 1.0 volume, 0s → 2.0 volume)
    if timeLeft <= 10:
        volume = min(0.2 + (10 - timeLeft) * 0.08, 1.0)
    else:
        volume = 0.2
    tick_channel.set_volume(volume)
    if tick_channel.get_busy():
        root.after(1000, adjust_ticking_volume)

def stop_ticking():
    tick_channel.stop()

def next_turn():
    global currentTotal, timeLeft

    canvas.delete("all")
    dice_positions = []
    dice_count = random.randint(MIN_DICE, MAX_DICE)
    currentTotal = 0

    while len(dice_positions) < dice_count:
        x = random.randint(0, CANVAS_WIDTH - DICE_SIZE)
        y = random.randint(0, CANVAS_HEIGHT - DICE_SIZE)
        if not overlaps(x, y, dice_positions):
            value = random.randint(1, 6)
            draw_die(x, y, value)
            dice_positions.append((x, y))
            currentTotal += value
                
    play_dice_sound()
    start_ticking()
    answer_prompt()
    threading.Thread(target=countdown_timer, daemon=True).start()


def answer_prompt():
    global turn_timer_id
    answer_entry.config(state="normal")
    answer_entry.delete(0, tk.END)
    submit_button.config(state="normal")
    
    # Start 20s timer for this turn
    turn_timer_id = root.after(20000, lambda: check_answer(timeout=True))

def check_answer(timeout=False):
    global correctAnswer, incorrectAnswer, score, timeLeft, turn_timer_id

    # Cancel the timeout if not already done
    if turn_timer_id:
        root.after_cancel(turn_timer_id)

    answer = answer_entry.get().strip()
    answer_entry.config(state="disabled")
    submit_button.config(state="disabled")

    if timeout or not answer or not answer.isdigit():
        end_game()
    elif int(answer) == currentTotal:
        correctAnswer += 1
        score += REWARD
        timeLeft += 1
    else:
        incorrectAnswer += 1
        score -= PENALTY
        timeLeft -= 1

    if timeLeft <= 0:
        end_game()
    else:
        if timer_label.winfo_exists():
            timer_label.config(text=f"Time Left: {timeLeft}s")
        update_score_labels()
        root.after(500, next_turn)


def end_game():
    global game_over
    game_over = True
    stop_ticking()
    canvas.delete("all")
    messagebox.showinfo("Game Over", f"Final Score: {score}\nCorrect: {correctAnswer}\nIncorrect: {incorrectAnswer}")
    root.destroy()

# Start game
next_turn()
root.mainloop()

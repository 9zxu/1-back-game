import tkinter as tk
import random
import string
import time
import csv
import os

class NBackGame:
    def __init__(self, root):
        self.root = root
        self.root.title("N-Back Game")
        self.root.configure(bg="white")
        self.root.attributes('-fullscreen', True)

        self.n = 2
        self.match_count = 10
        self.total_rounds = 30
        self.letter_interval = 500  # milliseconds
        self.flash_duration = 100   # milliseconds flash between letters

        self.sequence = []
        self.responses = []
        self.response_times = []
        self.current_index = -1
        self.running = False
        self.last_shown_time = 0
        self.user_id = ""

        self.feedback_timer = None

        # GUI elements
        self.label = tk.Label(root, text="", font=("Helvetica", 150), bg="white", fg="black")
        self.label.place(relx=0.5, rely=0.4, anchor="center")

        self.ui_frame = tk.Frame(root, bg="white")
        self.ui_frame.pack()

        self.uid_label = tk.Label(self.ui_frame, text="User ID (for log name):", font=("Helvetica", 16), bg="white", fg="black")
        self.uid_label.grid(row=0, column=0, sticky="e")
        self.uid_entry = tk.Entry(self.ui_frame, font=("Helvetica", 16), width=20)
        self.uid_entry.grid(row=0, column=1)

        self.n_label = tk.Label(self.ui_frame, text="N-Back Level (e.g., 2):", font=("Helvetica", 16), bg="white", fg="black")
        self.n_label.grid(row=1, column=0, sticky="e")
        self.n_entry = tk.Entry(self.ui_frame, font=("Helvetica", 16), width=5)
        self.n_entry.grid(row=1, column=1, sticky="w")

        self.start_button = tk.Button(self.ui_frame, text="Start Game", command=self.start_game, font=("Helvetica", 16))
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.result_label = tk.Label(root, text="", font=("Helvetica", 16), bg="white", fg="black")
        self.result_label.pack(pady=10)

        root.bind("<space>", self.handle_space)
        root.bind("<Escape>", lambda e: root.destroy())

    def start_game(self):
        try:
            self.n = int(self.n_entry.get())
            if self.n < 1 or self.n >= self.total_rounds:
                raise ValueError
        except ValueError:
            self.result_label.config(text="Please enter a valid N (1 <= N < total rounds)")
            return

        self.user_id = self.uid_entry.get().strip()
        if not self.user_id:
            self.result_label.config(text="Please enter a user ID.")
            return

        self.sequence.clear()
        self.responses.clear()
        self.response_times.clear()
        self.current_index = -1
        self.running = False
        self.result_label.config(text="")
        self.start_button.config(state="disabled")

        self.generate_sequence()
        self.countdown(3)

    def countdown(self, seconds_left):
        if seconds_left == 0:
            self.running = True
            self.show_next_letter()
        else:
            self.label.config(text=str(seconds_left), fg="black", bg="white")
            self.root.after(1000, self.countdown, seconds_left - 1)

    def generate_sequence(self):
        self.sequence = [''] * self.total_rounds
        available_indices = list(range(self.n, self.total_rounds))
        match_indices = random.sample(available_indices, self.match_count)

        for i in range(self.total_rounds):
            if i in match_indices:
                self.sequence[i] = self.sequence[i - self.n]
            else:
                while True:
                    letter = random.choice(string.ascii_letters)
                    if i < self.n or letter != self.sequence[i - self.n]:
                        self.sequence[i] = letter
                        break

    def show_next_letter(self):
        if not self.running:
            return

        if self.feedback_timer:
            self.root.after_cancel(self.feedback_timer)
            self.feedback_timer = None

        self.current_index += 1
        if self.current_index >= self.total_rounds:
            self.end_game()
            return

        # Flash black screen first
        self.label.config(text="", bg="black")
        self.root.configure(bg="black")
        self.root.after(self.flash_duration, self.display_letter)

    def display_letter(self):
        letter = self.sequence[self.current_index]
        self.label.config(text=letter, fg="black", bg="white")
        self.root.configure(bg="white")
        self.last_shown_time = time.time()

        self.root.after(self.letter_interval, self.show_next_letter)

    def handle_space(self, event):
        if not self.running or self.current_index < 0:
            return

        response_time = time.time() - self.last_shown_time
        match_expected = (
            self.current_index >= self.n and
            self.sequence[self.current_index] == self.sequence[self.current_index - self.n]
        )

        self.responses.append((self.current_index, match_expected, True))
        self.response_times.append(response_time)

        if match_expected:
            # Correct Hit
            self.label.config(fg="green")
        else:
            # False Alarm
            self.label.config(fg="red")

        if self.feedback_timer:
            self.root.after_cancel(self.feedback_timer)
        self.feedback_timer = self.root.after(self.letter_interval, self.show_next_letter)

    def end_game(self):
        self.running = False
        self.start_button.config(state="normal")
        self.label.config(text="Done", fg="black", bg="white")

        correct_hits = 0
        total_matches = 0

        for i in range(self.n, self.total_rounds):
            if self.sequence[i] == self.sequence[i - self.n]:
                total_matches += 1

        for idx, match_expected, responded in self.responses:
            if match_expected and responded:
                correct_hits += 1

        accuracy = (correct_hits / total_matches) * 100 if total_matches else 100
        avg_response_time = (
            sum(self.response_times) / len(self.response_times) if self.response_times else 0
        )

        self.result_label.config(
            text=f"Accuracy: {accuracy:.2f}%\nAvg RT: {avg_response_time:.3f}s"
        )
        self.save_log_csv(accuracy, avg_response_time)

    def save_log_csv(self, accuracy, avg_rt):
        log_exists = os.path.exists("nback_log.csv")
        with open("nback_log.csv", "a", newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not log_exists:
                writer.writerow(["user_id", "accuracy", "average_response_time"])
            writer.writerow([self.user_id, f"{accuracy:.2f}", f"{avg_rt:.3f}"])


if __name__ == "__main__":
    root = tk.Tk()
    game = NBackGame(root)
    root.mainloop()

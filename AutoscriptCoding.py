import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import threading

class Teleprompter:
    def __init__(self, root):
        # ตั้งค่าหน้าต่างหลัก
        self.root = root
        self.root.title("Teleprompter")

        # ช่องใส่ข้อความสำหรับสคริปต์ที่ต้องการอ่าน
        self.input_text = tk.Text(root, wrap=tk.WORD, font=("Helvetica", 16), width=50, height=5)
        self.input_text.pack(pady=10, padx=10, fill='x')

        # กำหนดให้ปุ่ม Ctrl+C และ Ctrl+V ใช้คัดลอกและวางข้อความในช่อง input_text
        self.input_text.bind("<Control-c>", self.copy_text)
        self.input_text.bind("<Control-v>", self.paste_text)

        # ปุ่มแสดงข้อความที่ผู้ใช้ป้อน
        self.show_button = ttk.Button(root, text="แสดงข้อความ", command=self.show_text, style="RoundedButton.TButton")
        self.show_button.pack(pady=5)

        # ตั้งค่าปุ่มและสไตล์
        style = ttk.Style()
        style.configure("RoundedButton.TButton", font=("Helvetica", 16), foreground="black", background="red", borderwidth=2)
        style.map("RoundedButton.TButton", background=[("active", "red")])

        # กำหนดค่าเริ่มต้นของความเร็วในการเลื่อน ขนาดฟอนต์ และตัวแปรอื่นๆ
        self.scroll_speed = 1  # ความเร็วในการเลื่อน
        self.font_size = 24  # ขนาดตัวอักษร
        self.current_line = 0  # บรรทัดปัจจุบันที่กำลังอ่าน
        self.script_lines = []  # เก็บข้อความแต่ละบรรทัดของสคริปต์
        self.highlighted_tag = "highlighted"  # ชื่อแท็กใช้สำหรับไฮไลท์ข้อความ
        self.is_voice_detection_active = False  # สถานะการทำงานของการตรวจจับเสียง
        self.is_scrolling = False  # สถานะการเลื่อนข้อความ

    # -------------
    # ฟังก์ชันสำหรับคัดลอกข้อความที่เลือก
    def copy_text(self, event=None):
        try:
            self.root.clipboard_clear()
            selected_text = self.input_text.selection_get()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass

    # -------------
    # ฟังก์ชันสำหรับวางข้อความจากคลิปบอร์ด
    def paste_text(self, event=None):
        try:
            clipboard_text = self.root.clipboard_get()
            self.input_text.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass

    # -------------
    # ฟังก์ชันสำหรับแสดงข้อความที่ผู้ใช้ป้อนในหน้าต่างใหม่
    def show_text(self):
        script_text = self.input_text.get("1.0", tk.END).strip()
        self.script_lines = script_text.splitlines()

        # สร้างหน้าต่างใหม่สำหรับการแสดงผล teleprompter
        self.new_window = tk.Toplevel(self.root)
        self.new_window.title("Teleprompter Display")
        self.new_window.geometry("800x600")

        # สร้างกรอบควบคุมต่างๆ ด้านซ้ายมือ
        control_frame = tk.Frame(self.new_window)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # ป้ายข้อมูลแสดงขนาดตัวอักษรและความเร็ว
        self.info_label = tk.Label(control_frame, text=f"ขนาดตัวอักษร: {self.font_size} | ความเร็ว: {self.scroll_speed}", font=("Helvetica", 14), fg="white", bg="black")
        self.info_label.pack(pady=5)

        # ปุ่มสำหรับเริ่มและหยุดการเลื่อน
        self.toggle_scroll_button = ttk.Button(control_frame, text="เริ่มเลื่อน", command=self.toggle_scroll)
        self.toggle_scroll_button.pack(pady=5)

        # ปุ่มสำหรับเริ่มและหยุดการตรวจจับเสียง
        self.voice_toggle_button = ttk.Button(control_frame, text="เริ่มตรวจจับการอ่าน", command=self.toggle_voice_detection)
        self.voice_toggle_button.pack(pady=5)

        # ปุ่มสำหรับรีเซ็ตการทำงาน
        self.reset_button = ttk.Button(control_frame, text="เริ่มต้นใหม่", command=self.reset_all)
        self.reset_button.pack(pady=5)

        # ปุ่มสำหรับปรับขนาดตัวอักษรใหญ่ขึ้นและเล็กลง
        self.enlarge_button = ttk.Button(control_frame, text="ขยายตัวอักษร", command=self.enlarge_text)
        self.enlarge_button.pack(pady=5)

        self.reduce_button = ttk.Button(control_frame, text="ลดตัวอักษร", command=self.reduce_text)
        self.reduce_button.pack(pady=5)

        # ปุ่มสำหรับเพิ่มและลดความเร็วการเลื่อน
        self.increase_speed_button = ttk.Button(control_frame, text="เพิ่มความเร็ว", command=self.increase_scroll_speed)
        self.increase_speed_button.pack(pady=5)

        self.decrease_speed_button = ttk.Button(control_frame, text="ลดความเร็ว", command=self.decrease_scroll_speed)
        self.decrease_speed_button.pack(pady=5)

        # สร้างพื้นที่สำหรับแสดงข้อความที่ผู้ใช้ป้อน
        self.text_display = tk.Text(self.new_window, font=("Helvetica", self.font_size), bg="black", fg="white", wrap=tk.WORD, padx=10, pady=10)
        self.text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # สร้าง Scrollbar สำหรับเลื่อนข้อความ
        scrollbar = tk.Scrollbar(self.new_window, command=self.text_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_display.config(yscrollcommand=scrollbar.set)

        # เพิ่มข้อความสคริปต์ลงในหน้าต่างแสดงผล
        for line in self.script_lines:
            self.text_display.insert(tk.END, line + "\n")

        self.text_display.config(state=tk.DISABLED)
        self.text_display.tag_configure(self.highlighted_tag, foreground="green")

        self.text_display.update_idletasks()
        self.text_display.config(scrollregion=self.text_display.bbox(tk.END))

        # กำหนดให้ใช้ MouseWheel เลื่อนข้อความได้
        self.new_window.bind("<MouseWheel>", self.scroll_with_mouse)

    # -------------
    # ฟังก์ชันเริ่มและหยุดการเลื่อนข้อความอัตโนมัติ
    def toggle_scroll(self):
        if self.is_scrolling:
            self.stop_scroll()
        else:
            self.start_scroll()

    # ฟังก์ชันเริ่มเลื่อนข้อความ
    def start_scroll(self):
        self.is_scrolling = True
        self.toggle_scroll_button.config(text="หยุดเลื่อน")
        self.scroll_text()

    # ฟังก์ชันหยุดการเลื่อนข้อความ
    def stop_scroll(self):
        self.is_scrolling = False
        self.toggle_scroll_button.config(text="เริ่มเลื่อน")

    # ฟังก์ชันเลื่อนข้อความทีละนิดอย่างนุ่มนวล
    def scroll_text(self):
        if self.is_scrolling:
            self.text_display.yview_scroll(1, "units")
            if self.text_display.yview()[1] == 1.0:
                self.stop_scroll()
        self.new_window.after(1000, self.scroll_text)

    # -------------
    # ฟังก์ชันเลื่อนข้อความด้วย MouseWheel
    def scroll_with_mouse(self, event):
        if event.delta > 0:
            self.text_display.yview_scroll(-1, "units")
        else:
            self.text_display.yview_scroll(1, "units")

    # -------------
    # ฟังก์ชันขยายขนาดตัวอักษร
    def enlarge_text(self):
        self.font_size += 2
        self.text_display.config(font=('Helvetica', self.font_size))
        self.update_info_label()

    # -------------
    # ฟังก์ชันลดขนาดตัวอักษร
    def reduce_text(self):
        if self.font_size > 10:
            self.font_size -= 2
            self.text_display.config(font=('Helvetica', self.font_size))
            self.update_info_label()

    # -------------
    # ฟังก์ชันอัปเดตข้อมูลแสดงขนาดตัวอักษรและความเร็ว
    def update_info_label(self):
        self.info_label.config(text=f"ขนาดตัวอักษร: {self.font_size} | ความเร็ว: {self.scroll_speed}")

    # -------------
    # ฟังก์ชันเพิ่มความเร็วการเลื่อน
    def increase_scroll_speed(self):
        self.scroll_speed = min(self.scroll_speed + 1, 5)
        self.update_info_label()
    # ฟังก์ชันลดความเร็วการเลื่อน
    def decrease_scroll_speed(self):
        self.scroll_speed = max(self.scroll_speed - 1, 1)
        self.update_info_label()

    # -------------
    # ฟังก์ชันเริ่มและหยุดการตรวจจับเสียง
    def toggle_voice_detection(self):
        if self.is_voice_detection_active:
            self.stop_voice_detection()
        else:
            self.start_voice_detection()

    # -------------
    # ฟังก์ชันเริ่มการตรวจจับเสียง
    def start_voice_detection(self):
        self.is_voice_detection_active = True
        self.voice_toggle_button.config(text="หยุดตรวจจับการอ่าน")
        self.voice_thread = threading.Thread(target=self.detect_voice)
        self.voice_thread.start()

    # -------------
    # ฟังก์ชันหยุดการตรวจจับเสียง
    def stop_voice_detection(self):
        self.is_voice_detection_active = False
        self.voice_toggle_button.config(text="เริ่มตรวจจับการอ่าน")

    # -------------
    # ฟังก์ชันตรวจจับเสียงและเลื่อนข้อความเมื่อพบการอ่าน
    def detect_voice(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        while self.is_voice_detection_active:
            try:
                with microphone as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source)
                    recognized_text = recognizer.recognize_google(audio, language="th")

                    # เปรียบเทียบข้อความที่ได้จากเสียงกับข้อความในบรรทัดปัจจุบัน
                    current_line_text = self.script_lines[self.current_line]
                    similarity = self.calculate_similarity(recognized_text, current_line_text)

                    if similarity >= 0.5:
                        self.current_line += 1
                        self.highlight_current_line()

            except sr.UnknownValueError:
                pass

    # -------------
    # ฟังก์ชันคำนวณความคล้ายคลึงระหว่างข้อความที่อ่านและข้อความปัจจุบัน
    def calculate_similarity(self, recognized_text, current_line_text):
        return len(set(recognized_text.split()) & set(current_line_text.split())) / max(len(current_line_text.split()), 1)

    # -------------
    # ฟังก์ชันไฮไลต์บรรทัดปัจจุบัน
    def highlight_current_line(self):
        self.text_display.config(state=tk.NORMAL)
        self.text_display.tag_remove(self.highlighted_tag, "1.0", tk.END)

        line_start = f"{self.current_line + 1}.0"
        line_end = f"{self.current_line + 1}.end"
        self.text_display.tag_add(self.highlighted_tag, line_start, line_end)

        self.text_display.config(state=tk.DISABLED)
        self.text_display.see(line_start)

    # -------------
    # ฟังก์ชันรีเซ็ตทุกค่ากลับไปเริ่มต้น
    def reset_all(self):
        self.font_size = 24
        self.scroll_speed = 1
        self.current_line = 0
        self.is_voice_detection_active = False
        self.is_scrolling = False

        self.update_info_label()
        self.text_display.config(state=tk.NORMAL)
        self.text_display.tag_remove(self.highlighted_tag, "1.0", tk.END)
        self.text_display.config(state=tk.DISABLED)

        self.toggle_scroll_button.config(text="เริ่มเลื่อน")
        self.voice_toggle_button.config(text="เริ่มตรวจจับการอ่าน")

# เรียกใช้งานโปรแกรม
if __name__ == "__main__":
    root = tk.Tk()
    app = Teleprompter(root)
    root.mainloop()

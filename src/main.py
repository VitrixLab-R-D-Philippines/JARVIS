# main.py
import os
os.environ["VISPY_APP_BACKEND"] = "osxmetal"

import sys
import threading
import time
import random
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt
from vispy import scene, app

import pyttsx3
import speech_recognition as sr
import sounddevice as sd

# -------------------------------
# Sphere Class
class Sphere:
    def __init__(self, view, N_u=40, N_v=40, radius=1.2, wave_amplitude=0.2, wave_speed=1.0, mass=5.0):
        self.view = view
        self.N_u = N_u
        self.N_v = N_v
        self.sphere_radius_base = radius
        self.wave_amplitude = wave_amplitude
        self.wave_speed = wave_speed
        self.mass = mass

        u = np.linspace(0, 2*np.pi, N_u)
        v = np.linspace(0, np.pi, N_v)
        self.x_unit = np.outer(np.cos(u), np.sin(v))
        self.y_unit = np.outer(np.sin(u), np.sin(v))
        self.z_unit = np.outer(np.ones(N_u), np.cos(v))

        faces = []
        for i in range(N_u - 1):
            for j in range(N_v - 1):
                idx = i * N_v + j
                faces.append([idx, idx + 1, idx + N_v])
                faces.append([idx + 1, idx + N_v + 1, idx + N_v])
        self.faces = np.array(faces)

        self.vertices = np.column_stack([
            self.x_unit.flatten() * self.sphere_radius_base,
            self.y_unit.flatten() * self.sphere_radius_base,
            self.z_unit.flatten() * self.sphere_radius_base
        ])

        self.sphere = scene.visuals.Mesh(
            vertices=self.vertices, faces=self.faces,
            color=(0, 0.75, 1, 1), shading='smooth', parent=view.scene
        )

    def update(self, vol=0.0, frame_count=0):
        try:
            breath = 1 + self.wave_amplitude * np.sin(frame_count * np.pi / 180 * self.wave_speed) + 1.5*vol
            vertices_new = np.column_stack([
                self.x_unit.flatten() * self.sphere_radius_base * breath,
                self.y_unit.flatten() * self.sphere_radius_base * breath,
                self.z_unit.flatten() * self.sphere_radius_base * breath
            ])
            vertices_new = np.nan_to_num(vertices_new)
            self.sphere.set_data(vertices=vertices_new, faces=self.faces)
        except Exception as e:
            print(f"[Sphere update ERROR]: {e}")

# -------------------------------
# Stars Class
class Stars:
    def __init__(self, view, speed=1.0):
        self.view = view
        self.speed = speed
        self.n_stars = 300
        self.r_base = 2.1

        np.random.seed(42)
        self.theta = np.random.uniform(0, 2*np.pi, self.n_stars)
        self.phi = np.random.uniform(0, np.pi, self.n_stars)
        self.brightness = np.random.uniform(0.3, 1.0, self.n_stars)
        self.size = np.random.uniform(2, 5, self.n_stars)
        self.stardome_variation = np.random.uniform(0.0001, 0.001, self.n_stars)
        self.twinkle_phase = np.random.uniform(0, 2*np.pi, self.n_stars)

        base_colors = np.array([
            [0.0, 0.75, 1.0, 1.0],
            [0.0, 0.85, 0.95, 1.0],
            [0.2, 0.6, 1.0, 1.0],
            [1.0, 0.3, 0.8, 1.0],
            [1.0, 0.6, 0.2, 1.0],
            [0.95, 0.95, 0.9, 1.0]
        ])
        self.colors = base_colors[np.random.randint(0, len(base_colors), self.n_stars)]

        self.sin_phi = np.sin(self.phi)
        self.cos_phi = np.cos(self.phi)

        x = self.r_base * self.sin_phi * np.cos(self.theta)
        y = self.r_base * self.sin_phi * np.sin(self.theta)
        z = self.r_base * self.cos_phi
        self.x = x
        self.y = y
        self.z = z

        colors_with_alpha = self.colors.copy()
        colors_with_alpha[:, 3] *= self.brightness
        self.markers = scene.visuals.Markers(parent=self.view.scene)
        self.markers.set_data(
            np.column_stack([x, y, z]),
            face_color=colors_with_alpha,
            size=self.size,
            edge_color=None
        )

    def update(self, vol=0.0):
        self.theta += self.stardome_variation * 50 * self.speed
        radius = self.r_base * (1 + 0.2 * vol)

        x = radius * self.sin_phi * np.cos(self.theta)
        y = radius * self.sin_phi * np.sin(self.theta)
        z = radius * self.cos_phi

        twinkle = 0.2 * np.sin(self.twinkle_phase + self.theta)
        alphas = np.clip(self.colors[:, 3] * self.brightness + twinkle + 0.2 * vol, 0.2, 1.0)
        colors_with_alpha = self.colors.copy()
        colors_with_alpha[:, 3] = alphas

        self.x = x
        self.y = y
        self.z = z

        self.markers.set_data(
            np.column_stack([x, y, z]),
            face_color=colors_with_alpha,
            size=self.size,
            edge_color=None
        )

# -------------------------------
# Bursts Class
class Bursts:
    def __init__(self, view, star_colors=None, n_bursts=150, radius=2.0):
        self.view = view
        self.enabled = True
        self.scale = 0.2
        self.n_bursts = n_bursts
        self.radius = radius

        self.base_colors = np.array([
            [0.0, 0.75, 1.0, 1.0],
            [0.0, 0.85, 0.95, 1.0],
            [0.2, 0.6, 1.0, 1.0],
            [1.0, 0.3, 0.8, 1.0],
            [1.0, 0.6, 0.2, 1.0],
            [0.95, 0.95, 0.9, 1.0]
        ])
        if isinstance(star_colors, np.ndarray) and star_colors.shape[1]==4:
            self.colors = star_colors[np.random.randint(0, len(star_colors), n_bursts)]
        else:
            self.colors = self.base_colors[np.random.randint(0, len(self.base_colors), n_bursts)]

        self._generate_spherical_positions()
        self.velocities = np.random.uniform(-0.03, 0.03, (n_bursts, 3)) * self.scale
        self.sizes = np.random.uniform(1, 5, n_bursts)
        self.markers = scene.visuals.Markers(parent=view.scene)
        self._update_markers()

    def _generate_spherical_positions(self):
        phi = np.arccos(1 - 2 * np.random.rand(self.n_bursts))
        theta = 2 * np.pi * np.random.rand(self.n_bursts)
        r = self.radius

        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)

        self.positions = np.column_stack([x, y, z])

    def _update_markers(self):
        n = min(len(self.positions), len(self.colors))
        if self.enabled:
            self.markers.set_data(
                self.positions[:n],
                face_color=self.colors[:n],
                edge_color=None,
                size=self.sizes[:n]
            )
        else:
            twinkle_colors = self.colors[:n].copy()
            twinkle_colors[:, 3] = np.random.uniform(0.1, 0.5, n)
            self.markers.set_data(
                self.positions[:n],
                face_color=twinkle_colors,
                edge_color=None,
                size=self.sizes[:n]
            )

    def update(self, vol=0.0):
        self.positions += self.velocities
        self.positions *= (1 + 0.01 * vol)
        self._update_markers()

    def toggle(self, state: bool):
        self.enabled = state
        self._update_markers()

    def set_n_bursts(self, n):
        self.n_bursts = n
        self._generate_spherical_positions()
        self.velocities = np.random.uniform(-0.03, 0.03, (n, 3)) * self.scale
        self.sizes = np.random.uniform(1, 5, n)
        self.colors = self.base_colors[np.random.randint(0, len(self.base_colors), n)]
        self._update_markers()

# -------------------------------
# AudioStream Class
class AudioStream:
    def __init__(self):
        self.enabled = True
        self.audio_level = 0.0
        self.lock = threading.Lock()

        try:
            self.stream = sd.InputStream(
                channels=1,
                samplerate=44100,
                blocksize=1024,
                callback=self.callback
            )
            self.stream.start()
        except Exception as e:
            print("Audio unavailable:", e)
            self.enabled = False

    def callback(self, indata, frames, time_, status):
        if not self.enabled:
            return
        rms = np.sqrt(np.mean(indata.astype(np.float32)**2))
        with self.lock:
            self.audio_level = 0.2 * rms + 0.8 * self.audio_level

    def get_level(self):
        with self.lock:
            return self.audio_level if self.enabled else 0.0

# -------------------------------
# VoiceControl Class
class VoiceControl:
    def __init__(self, gui=None):
        self.gui = gui
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.enabled = True
        self.listening = True

        voices = self.engine.getProperty('voices')
        for v in voices:
            if "male" in v.name.lower() or "english" in v.name.lower():
                self.engine.setProperty('voice', v.id)
                break
        self.engine.setProperty('rate', 160)

        if self.gui:
            threading.Thread(target=self.listen_voice_commands, daemon=True).start()

    def speak(self, text):
        if self.enabled:
            threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()

    def _speak_sync(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                print("JARVIS is listening...")
                audio = self.recognizer.listen(source, timeout=5)
            return self.recognizer.recognize_google(audio)
        except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
            return None

    def listen_voice_commands(self):
        while self.listening:
            if not (self.gui and getattr(self.gui, 'voice_control_enabled', True)):
                time.sleep(0.1)
                continue

            command = self.listen()
            if not command:
                continue

            command = command.lower()

            if self.gui:
                if "pause" in command:
                    self.gui.toggle_pause()
                    self.speak("Pausing animations")
                elif "resume" in command:
                    self.gui.toggle_pause()
                    self.speak("Resuming animations")
                elif "audio on" in command:
                    self.gui.audio.enabled = True
                    self.speak("Audio reactive mode activated")
                elif "audio off" in command:
                    self.gui.audio.enabled = False
                    self.speak("Audio reactive mode deactivated")
                elif "bursts on" in command:
                    self.gui.bursts.enabled = True
                    self.speak("Bursts mode activated")
                elif "bursts off" in command:
                    self.gui.bursts.enabled = False
                    self.speak("Bursts mode deactivated")
                elif "reset sliders" in command:
                    for slider, default in self.gui.default_sliders.items():
                        slider.setValue(default)
                    self.speak("All sliders reset to default values")
                elif "set amplitude" in command:
                    nums = [int(s) for s in command.split() if s.isdigit()]
                    if nums:
                        val = max(0, min(nums[0], 50))
                        self.gui.sphere.wave_am
                        self.gui.sphere.wave_amplitude = val / 100
                        self.speak(f"Setting breath amplitude to {val}")
                elif "jarvis talk" in command:
                    words_list = [
                        "Initializing", "Processing", "Calculating", "Analyzing", "Quantum",
                        "Neural", "Sphere", "Orbit", "Velocity", "Energy", "Data", "Matrix",
                        "Activating", "Scanning", "Synchronizing", "Hyperdrive", "Engaged"
                    ]
                    sentence = ' '.join(random.choices(words_list, k=random.randint(3, 6)))
                    self.speak(sentence)

            time.sleep(0.1)

# -------------------------------
# SphereGUI Class
class SphereGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Sphere AI OS")
        self.setGeometry(100, 100, 1000, 900)
        self.paused = False
        self.frame_count = 0

        # Canvas
        self.canvas = scene.SceneCanvas(keys='interactive', size=(900, 900), bgcolor='black', show=True)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(fov=45, distance=6)

        # Objects
        self.sphere = Sphere(self.view)
        self.stars = Stars(self.view, speed=1.0)
        self.bursts = Bursts(self.view, self.stars.colors)
        self.audio = AudioStream()
        self.voice = VoiceControl(self)

        # Voice control toggle
        self.voice_control_enabled = True
        voice_cb = QCheckBox("Voice Control (JARVIS)")
        voice_cb.setChecked(True)
        voice_cb.stateChanged.connect(lambda state: setattr(self, 'voice_control_enabled', state==Qt.Checked))

        # GUI Panel
        central_widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.canvas.native)
        control_layout = QVBoxLayout()

        # Sliders GroupBox
        slider_group = QGroupBox("Adjust Settings")
        slider_layout = QVBoxLayout()
        self.default_sliders = {}

        def add_slider(label_text, min_val, max_val, default_val, setter_func, voice_msg=None):
            container = QHBoxLayout()
            label = QLabel(label_text)
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(min_val)
            slider.setMaximum(max_val)
            slider.setValue(default_val)

            def on_change(val):
                setter_func(val)
                if self.voice_control_enabled and voice_msg:
                    self.voice.speak(f"{voice_msg} set to {val}")

            slider.valueChanged.connect(on_change)

            reset_btn = QPushButton("Reset")
            reset_btn.setFixedWidth(60)
            reset_btn.setToolTip(f"Reset {label_text} to default {default_val}")
            reset_btn.clicked.connect(lambda: slider.setValue(default_val))

            container.addWidget(label)
            container.addWidget(reset_btn)
            slider_layout.addLayout(container)
            slider_layout.addWidget(slider)
            self.default_sliders[slider] = default_val
            return slider

        add_slider("Breath Amplitude", 0, 50, int(self.sphere.wave_amplitude*100),
                   lambda val: setattr(self.sphere, "wave_amplitude", val/100),
                   voice_msg="Breath amplitude")
        add_slider("Wave Speed", 1, 10, int(self.sphere.wave_speed),
                   lambda val: setattr(self.sphere, "wave_speed", val),
                   voice_msg="Wave speed")
        add_slider("Stardome Speed", 1, 20, int(self.stars.speed*10),
                   lambda val: setattr(self.stars, "speed", val/10),
                   voice_msg="Stardome speed")
        add_slider("Burst Volume", 10, 300, self.bursts.n_bursts,
                   lambda val: self.bursts.set_n_bursts(val),
                   voice_msg="Burst volume")

        # Reset All
        reset_all_btn = QPushButton("Reset All Defaults")
        reset_all_btn.setStyleSheet("font-weight: bold;")
        def reset_all():
            for s, v in self.default_sliders.items():
                s.setValue(v)
            if self.voice_control_enabled:
                self.voice.speak("All sliders reset to default values")
        reset_all_btn.clicked.connect(reset_all)
        slider_layout.addWidget(reset_all_btn)

        slider_group.setLayout(slider_layout)
        control_layout.addWidget(slider_group)

        # Features GroupBox
        toggle_group = QGroupBox("Features")
        toggle_layout = QVBoxLayout()
        def add_checkbox(label, obj, attr, default=True, voice_on=None, voice_off=None):
            cb = QCheckBox(label)
            cb.setChecked(default)
            def on_toggle(state):
                setattr(obj, attr, state==Qt.Checked)
                if self.voice_control_enabled:
                    if state==Qt.Checked and voice_on: self.voice.speak(voice_on)
                    if state!=Qt.Checked and voice_off: self.voice.speak(voice_off)
            cb.stateChanged.connect(on_toggle)
            toggle_layout.addWidget(cb)
            return cb

        add_checkbox("Bursts ON/OFF", self.bursts, "enabled", True,
                     voice_on="Bursts mode activated", voice_off="Bursts mode deactivated")
        add_checkbox("Audio Reactive", self.audio, "enabled", True,
                     voice_on="Audio reactive mode activated", voice_off="Audio reactive mode deactivated")
        toggle_layout.addWidget(voice_cb)
        toggle_group.setLayout(toggle_layout)
        control_layout.addWidget(toggle_group)

        # Pause Button
        self.pause_resume_btn = QPushButton("Pause")
        self.pause_resume_btn.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_resume_btn)

        # Gravity Label
        self.gravity_label = QLabel("Gravitational Status: 0.00")
        control_layout.addWidget(self.gravity_label)

        layout.addLayout(control_layout)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Timer
        self.timer = app.Timer(interval=0.016, connect=self.update_scene, start=True)

        # Voice Threads
        threading.Thread(target=lambda: self.voice.speak(
            "Hello, I am JARVIS... the Sphere AI OS is now online."
        ), daemon=True).start()
        threading.Thread(target=self.voice.listen_voice_commands, daemon=True).start()
        threading.Thread(target=self.random_jarvis_speech, daemon=True).start()

        self.show()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_resume_btn.setText("Resume" if self.paused else "Pause")
        if self.voice_control_enabled:
            self.voice.speak("Animations paused" if self.paused else "Animations resumed")

    def random_jarvis_speech(self):
        words_list = [
            "Initializing", "Processing", "Calculating", "Analyzing", "Quantum",
            "Neural", "Sphere", "Orbit", "Velocity", "Energy", "Data", "Matrix",
            "Activating", "Scanning", "Synchronizing", "Hyperdrive", "Engaged"
        ]
        while True:
            if getattr(self, 'voice_control_enabled', True):
                sentence = ' '.join(random.choices(words_list, k=random.randint(2, 5)))
                self.voice.speak(sentence)
            time.sleep(random.uniform(5, 15))

    def update_scene(self, ev):
        if self.paused:
            return
        self.frame_count += 1
        vol = self.audio.get_level()

        self.sphere.update(vol, self.frame_count)
        self.stars.update(vol)
        self.bursts.update(vol)

        G = 1.0
        sphere_mass = getattr(self.sphere, "mass", 5.0)
        star_masses = np.ones(self.stars.n_stars) * 0.1
        try:
            star_positions = np.column_stack([self.stars.x, self.stars.y, self.stars.z])
        except AttributeError:
            r = self.stars.r_base * (1 + 0.2*vol)
            x = r * np.sin(self.stars.phi) * np.cos(self.stars.theta)
            y = r * np.sin(self.stars.phi) * np.sin(self.stars.theta)
            z = r * np.cos(self.stars.phi)
            star_positions = np.column_stack([x, y, z])

        distances = np.linalg.norm(star_positions, axis=1)
        grav_effect = np.sum(G * sphere_mass * star_masses / (distances**2 + 1e-6))
        self.gravity_label.setText(f"Gravitational Status: {grav_effect:.3f}")

# -------------------------------
# Entry Point
if __name__ == "__main__":
    appQt = QApplication(sys.argv)
    window = SphereGUI()
    sys.exit(appQt.exec_())

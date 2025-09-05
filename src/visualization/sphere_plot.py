# File: src/visualization/sphere_plot.py

import numpy as np
from vispy import app, scene
import pyttsx3
import sounddevice as sd
import threading
import time
import speech_recognition as sr

def draw_scene():
    # -------------------------------
    # Global audio variable
    audio_level = 0.0
    lock = threading.Lock()

    # -------------------------------
    # VisPy canvas
    canvas = scene.SceneCanvas(keys='interactive', size=(900, 900), bgcolor='black', show=True)
    view = canvas.central_widget.add_view()
    view.camera = scene.TurntableCamera(fov=45, distance=6)

    # -------------------------------
    # Sphere setup
    N_u, N_v = 40, 40
    u = np.linspace(0, 2*np.pi, N_u)
    v = np.linspace(0, np.pi, N_v)
    x_unit = np.outer(np.cos(u), np.sin(v))
    y_unit = np.outer(np.sin(u), np.sin(v))
    z_unit = np.outer(np.ones(N_u), np.cos(v))

    sphere_radius_base = 1.2
    sphere_breath_amplitude = 0.2

    vertices = np.column_stack([x_unit.flatten()*sphere_radius_base,
                                y_unit.flatten()*sphere_radius_base,
                                z_unit.flatten()*sphere_radius_base])
    faces = []
    for i in range(N_u - 1):
        for j in range(N_v - 1):
            idx = i*N_v + j
            faces.append([idx, idx + 1, idx + N_v])
            faces.append([idx + 1, idx + N_v + 1, idx + N_v])
    faces = np.array(faces)

    sphere = scene.visuals.Mesh(vertices=vertices, faces=faces, color=(0,0.75,1,1),
                                shading='smooth', parent=view.scene)

    # -------------------------------
    # Stars setup with color palette
    np.random.seed(42)
    n_stars = 300
    theta = np.random.uniform(0, 2*np.pi, n_stars)
    phi = np.random.uniform(0, np.pi, n_stars)
    r_stars = 2.1

    stars_x = r_stars * np.sin(phi) * np.cos(theta)
    stars_y = r_stars * np.sin(phi) * np.sin(theta)
    stars_z = r_stars * np.cos(phi)
    stars_brightness = np.random.uniform(0.3, 1.0, n_stars)
    stars_size = np.random.uniform(2, 5, n_stars)
    stardome_variation = np.random.uniform(0.0001, 0.001, n_stars)

    base_colors = np.array([
        [0.0, 0.75, 1.0],  # core cyan
        [0.0, 0.85, 0.95],
        [0.2, 0.6, 1.0],
        [1.0, 0.3, 0.8],   # complementary spark
        [1.0, 0.6, 0.2]    # complementary spark
    ])
    stars_colors = base_colors[np.random.randint(0, len(base_colors), n_stars)]

    stars = scene.visuals.Markers(parent=view.scene)
    stars.set_data(
        np.column_stack([stars_x, stars_y, stars_z]),
        face_color=np.column_stack([stars_colors, stars_brightness]),
        size=stars_size,
        edge_color=None
    )

    # -------------------------------
    # Stardust burst layer
    n_burst = 50
    burst_positions = np.zeros((n_burst, 3))
    burst_colors = stars_colors[np.random.randint(0, len(stars_colors), n_burst)]
    burst_sizes = np.random.uniform(3, 6, n_burst)
    burst_alphas = np.zeros(n_burst)
    burst_active = np.zeros(n_burst, dtype=bool)

    burst_layer = scene.visuals.Markers(parent=view.scene)
    burst_layer.set_data(burst_positions,
                         face_color=np.column_stack([burst_colors, burst_alphas]),
                         size=burst_sizes,
                         edge_color=None)

    def update_bursts():
        nonlocal burst_positions, burst_alphas, burst_active

        # Randomly activate bursts
        for i in range(n_burst):
            if not burst_active[i] and np.random.rand() < 0.01:  # 1% chance to trigger
                phi_rand = np.random.uniform(0, np.pi)
                theta_rand = np.random.uniform(0, 2*np.pi)
                r_rand = 1.8
                burst_positions[i] = [r_rand*np.sin(phi_rand)*np.cos(theta_rand),
                                      r_rand*np.sin(phi_rand)*np.sin(theta_rand),
                                      r_rand*np.cos(phi_rand)]
                burst_alphas[i] = 1.0
                burst_active[i] = True

        # Update active bursts
        burst_alphas[burst_active] -= 0.02  # fade out
        burst_active[burst_alphas <= 0] = False
        burst_alphas = np.clip(burst_alphas, 0, 1)

        burst_layer.set_data(burst_positions,
                             face_color=np.column_stack([burst_colors, burst_alphas]),
                             size=burst_sizes,
                             edge_color=None)

    frame_count = 0

    # -------------------------------
    # Audio callback
    def audio_callback(indata, frames, time_, status):
        nonlocal audio_level
        rms = np.sqrt(np.mean(indata**2))
        with lock:
            audio_level += (rms - audio_level) * 0.2

    stream = sd.InputStream(channels=1, callback=audio_callback, samplerate=44100, blocksize=1024)
    stream.start()

    # -------------------------------
    # JARVIS TTS
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'male' in voice.name.lower() or 'Alex' in voice.name:
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 150)

    def speak_text(text):
        print(f"JARVIS: {text}")
        engine.say(text)
        engine.runAndWait()

    # -------------------------------
    # Speech recognition
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    def play_beep(frequency=1000, duration=0.15, samplerate=44100):
        t = np.linspace(0, duration, int(samplerate*duration), endpoint=False)
        wave = 0.3 * np.sin(2*np.pi*frequency*t)
        sd.play(wave, samplerate)
        sd.wait()

    def listen_and_respond():
        while True:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                play_beep()
                audio = recognizer.listen(source)
            try:
                recognized_text = recognizer.recognize_google(audio)
                speak_text(f"You said: {recognized_text}")
            except sr.UnknownValueError:
                speak_text("Sorry, I did not catch that.")
            except sr.RequestError:
                speak_text("Speech recognition service is unavailable.")
            time.sleep(2)

    def idle_speech():
        while True:
            speak_text("Waiting for your command...")
            time.sleep(10)

    def jarvis_intro():
        phrases = [
            "Hi, I am JARVIS.",
            "What is our agenda for today?"
        ]
        time.sleep(1)
        for phrase in phrases:
            speak_text(phrase)
            time.sleep(3)
        threading.Thread(target=idle_speech, daemon=True).start()
        threading.Thread(target=listen_and_respond, daemon=True).start()

    threading.Thread(target=jarvis_intro, daemon=True).start()

    # -------------------------------
    # Animation update
    def update(ev):
        nonlocal frame_count, audio_level
        frame_count += 1
        with lock:
            vol = audio_level

        # Sphere breathing
        breath = 1 + sphere_breath_amplitude * np.sin(frame_count*np.pi/180) + 1.5*vol
        vertices_new = np.column_stack([x_unit.flatten()*sphere_radius_base*breath,
                                        y_unit.flatten()*sphere_radius_base*breath,
                                        z_unit.flatten()*sphere_radius_base*breath])
        sphere.set_data(vertices_new, faces)

        # Camera rotation
        view.camera.azimuth = 20*np.sin(frame_count*np.pi/360)

        # Stars rotation & twinkle
        new_theta = theta + frame_count * stardome_variation
        new_x = (r_stars * (1 + 0.2*vol)) * np.sin(phi) * np.cos(new_theta)
        new_y = (r_stars * (1 + 0.2*vol)) * np.sin(phi) * np.sin(new_theta)
        new_z = (r_stars * (1 + 0.2*vol)) * np.cos(phi)
        twinkle = 0.2 * np.sin(frame_count/30 + np.random.uniform(0, 2*np.pi, n_stars))
        alphas = np.clip(stars_brightness + twinkle + 0.2*vol, 0.2, 1.0)

        stars.set_data(
            np.column_stack([new_x, new_y, new_z]),
            face_color=np.column_stack([stars_colors, alphas]),
            size=stars_size,
            edge_color=None
        )

        # Update stardust bursts
        update_bursts()

    # -------------------------------
    # Timer
    timer = app.Timer()
    timer.connect(update)
    timer.start(0.016)

    # -------------------------------
    # Run app
    app.run()


if __name__ == "__main__":
    draw_scene()

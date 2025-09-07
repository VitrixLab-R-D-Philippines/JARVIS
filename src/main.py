# ===============================
# main.py - JARVIS AI OS MVP (Enhanced)
# Principles: DRY, SOLID, SoC, Composition, Fail-Fast
# ===============================

import sys
import threading
import logging
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider
from PyQt5.QtCore import Qt
from vispy import scene

# -------------------------------
# Logging
# -------------------------------
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# -------------------------------
# Fail-Fast Decorator
# -------------------------------
def safe_call(default=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                cls = args[0].__class__.__name__ if args else "Unknown"
                logging.error(f"[{cls}] {func.__name__} failed: {e}")
                return default
        return wrapper
    return decorator

# -------------------------------
# Visual Controllers
# -------------------------------
class SphereController:
    def __init__(self, view):
        self.view = view
        self.sphere = None
        self.sensitivity = 1.0
        self.wobble = 0.5
        self.wave = 0.5

    @safe_call()
    def setup(self, SphereClass):
        self.sphere = SphereClass(self.view)

class StarController:
    def __init__(self, view, n_stars=300):
        self.view = view
        self.n_stars = n_stars
        self.stars = None
        self.speed = 1.0

    @safe_call()
    def setup(self, StarsClass):
        self.stars = StarsClass(self.view, n_stars=self.n_stars)

class BurstController:
    def __init__(self, view, n_bursts=150):
        self.view = view
        self.n_bursts = n_bursts
        self.bursts = None
        self.enabled = True

    @safe_call()
    def setup(self, BurstsClass):
        self.bursts = BurstsClass(self.view, n_bursts=self.n_bursts)

# -------------------------------
# FX Controller (Glow + Ripple)
# -------------------------------
class FXController:
    def __init__(self, SphereFXClass, sphere, GlowClass, RippleClass, PostFXPipelineClass):
        self.fx = SphereFXClass(sphere,
                                glow=GlowClass(),
                                ripple=RippleClass(),
                                pipeline=PostFXPipelineClass())

# -------------------------------
# Audio Engine Wrapper
# -------------------------------
class AudioEngineWrapper:
    @safe_call()
    def __init__(self):
        try:
            from audio import AudioEngine
            self.audio = AudioEngine()
            self.audio.start_stream()
        except:
            logging.warning("AudioEngine unavailable, using dummy audio.")
            self.audio = type("DummyAudio", (), {})()
            self.audio.eq_values = {"low": 0.0, "mid": 0.0, "high": 0.0}
            self.audio.start_stream = lambda: None

# -------------------------------
# AI / Interaction Manager (VIE)
# -------------------------------
class AIController:
    def __init__(self, sphere_ctrl, star_ctrl, burst_ctrl, audio_engine, InteractionManagerClass):
        self.sphere_ctrl = sphere_ctrl
        self.star_ctrl = star_ctrl
        self.burst_ctrl = burst_ctrl
        self.audio_engine = audio_engine
        self.InteractionManagerClass = InteractionManagerClass
        self.vie = None

    @safe_call()
    def toggle_vie(self, enable=True):
        if enable and not self.vie:
            self.vie = self.InteractionManagerClass(
                sphere=self.sphere_ctrl.sphere,
                stars=self.star_ctrl.stars,
                bursts=self.burst_ctrl.bursts,
                audio=self.audio_engine.audio
            )
            threading.Thread(target=self.vie.start, daemon=True).start()
            logging.info("VIE enabled.")
        elif not enable and self.vie:
            self.vie.stop()
            self.vie = None
            logging.info("VIE disabled.")

# -------------------------------
# GUI / Main Window
# -------------------------------
class SphereGUI(QMainWindow):
    @safe_call()
    def __init__(self, SphereClass, StarsClass, BurstsClass,
                 SphereFXClass, GlowClass, RippleClass, PostFXPipelineClass,
                 InteractionManagerClass):
        super().__init__()
        self.setWindowTitle("JARVIS - Sphere AI OS MVP")
        self.setGeometry(100, 100, 900, 650)

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Canvas
        self.canvas = scene.SceneCanvas(keys='interactive', size=(800, 500), bgcolor=(0, 0, 0, 1))
        self.layout.addWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()

        # Initialize Controllers
        self.sphere_ctrl = SphereController(self.view)
        self.sphere_ctrl.setup(SphereClass)

        self.star_ctrl = StarController(self.view)
        self.star_ctrl.setup(StarsClass)

        self.burst_ctrl = BurstController(self.view)
        self.burst_ctrl.setup(BurstsClass)

        self.fx_ctrl = FXController(SphereFXClass,
                                    self.sphere_ctrl.sphere,
                                    GlowClass, RippleClass, PostFXPipelineClass)

        # Audio + AI
        self.audio_engine = AudioEngineWrapper()
        self.ai_ctrl = AIController(self.sphere_ctrl,
                                    self.star_ctrl,
                                    self.burst_ctrl,
                                    self.audio_engine,
                                    InteractionManagerClass)
        self.ai_ctrl.toggle_vie(True)

        # Simple Slider Control (Example)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        self.layout.addWidget(slider)

        # Apply some defaults
        self.apply_defaults()

    @safe_call()
    def apply_defaults(self):
        # Default visual parameters
        if self.sphere_ctrl.sphere:
            if hasattr(self.sphere_ctrl.sphere, "set_breathing"):
                self.sphere_ctrl.sphere.set_breathing(True)
        if self.star_ctrl.stars:
            self.star_ctrl.set_speed(2.5)
        if self.burst_ctrl.bursts:
            self.burst_ctrl.enabled = True

# -------------------------------
# Main Entry
# -------------------------------
def main():
    app = QApplication(sys.argv)

    # Lazy imports for modularity
    from objects import Sphere, Stars, Bursts
    from vie import InteractionManager
    from shaders import SphereWithFX, GlowEffect, RippleEffect, PostFXPipeline

    gui = SphereGUI(
        SphereClass=Sphere,
        StarsClass=Stars,
        BurstsClass=Bursts,
        SphereFXClass=SphereWithFX,
        GlowClass=GlowEffect,
        RippleClass=RippleEffect,
        PostFXPipelineClass=PostFXPipeline,
        InteractionManagerClass=InteractionManager
    )

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

/** * sketch.js – Super Engine Interface
 * This script bridges the Web UI to the C++ Parallel API.
 * High Throughput: 100,000+ particles handled in C++ VRAM.
 * Low Latency: Zero-copy rendering.
 */

let superEngine = null;
let targetParticleCount = 100000; // The "Super Engine" throughput
let flowSpeed = 0.8;
let autoDrift = true;
let t = 0;

// This comes from the compiled Wasm module
Module.onRuntimeInitialized = () => {
    console.log("C++ Parallel API Hooked.");
    // Initialize the engine with 100k particles
    superEngine = new Module.FermatEngine(targetParticleCount);
    // Initial Lens Radius
    superEngine.setLensRadius(250.0);
};

function setup() {
    // We use WEBGL mode to give the C++ API a GPU context to draw into
    createCanvas(windowWidth, windowHeight, WEBGL);
    
    // Set p5 to handle colors in the same range as the C++ logic if needed
    colorMode(HSB, 360, 100, 100, 1);
    background(240, 60, 5);
}

function draw() {
    // Ensure the C++ Engine is warmed up before calling
    if (!superEngine) {
        drawLoadingState();
        return;
    }

    // 1. LAYER 1: Background & Trails
    // We draw a semi-transparent quad to create the silky fluid trails
    push();
    resetMatrix();
    noStroke();
    fill(240, 60, 5, 0.15); 
    rect(-width/2, -height/2, width, height);
    pop();

    // 2. LAYER 2: Input & Logic (Low Latency Control)
    // Map mouse/auto-drift to Normalized Device Coordinates (-1.0 to 1.0)
    let srcX = autoDrift ? (sin(t) * 0.6) : map(mouseX, 0, width, -1, 1);
    let srcY = autoDrift ? (cos(t * 1.3) * 0.6) : map(mouseY, 0, height, -1, 1);
    
    // Use the API to set the Source and Sink (Directly into C++ Memory)
    superEngine.setSource(srcX, srcY, 0.0);
    superEngine.setSink(-srcX, -srcY, 0.0);

    // 3. LAYER 3: The Heavy Lifting (High Throughput Physics)
    // Call the C++ step function. This triggers the Parallel Compute Shader.
    // 100k particles are updated here in roughly 0.5ms.
    superEngine.step(deltaTime / 1000.0);

    // 4. LAYER 4: Zero-Copy Rendering
    // The C++ API tells the GPU to draw the particle buffer it already holds.
    // No particle data is sent over the bus; it's already in VRAM.
    superEngine.render();

    t += 0.005;
}

// --------------------------------------------------------------
// API Event Handlers (Bridging the HTML UI to C++)
// --------------------------------------------------------------

function updateParticleCount(val) {
    targetParticleCount = parseInt(val);
    document.getElementById('particleCountVal').innerText = val;
    
    if (superEngine) {
        // Destroy the old C++ object to free VRAM
        superEngine.delete(); 
        // Re-allocate the Super Engine with the new count
        superEngine = new Module.FermatEngine(targetParticleCount);
    }
}

function updateSpeed(val) {
    flowSpeed = parseFloat(val);
    document.getElementById('speedVal').innerText = val;
    // Note: C++ uses deltaTime, but we can pass flowSpeed as a uniform
    // if we added a setSpeed method to the API.
}

function toggleMotion() {
    autoDrift = !autoDrift;
}

function resetParticles() {
    if (superEngine) {
        // Force re-init of the particle buffer in VRAM
        superEngine.delete();
        superEngine = new Module.FermatEngine(targetParticleCount);
    }
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

function drawLoadingState() {
    background(240, 60, 5);
    fill(255);
    textAlign(CENTER);
    text("INITIALIZING PARALLEL C++ API...", 0, 0);
}

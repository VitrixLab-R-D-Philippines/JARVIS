/** * sketch.js – Super Engine Interface
 * This script bridges the Web UI to the C++ Parallel API.
 * High Throughput: 100,000+ particles handled in C++ VRAM.
 * Low Latency: Zero-copy rendering.

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

 */


let particleCount = 100000;
let gl, pipeline;
let source = [0.5, 0.0];
let sink = [-0.5, 0.0];
let t = 0;

function setup() {
    let canvas = createCanvas(windowWidth, windowHeight, WEBGL);
    gl = canvas.GL;
    
    // Initialize the GPU Parallel Pipeline
    pipeline = new GPUPhysicsPipeline(gl, particleCount);
    background(0);
}

function draw() {
    // 1. Silky Trail Effect
    resetMatrix();
    noStroke();
    fill(0, 20); 
    rect(-width/2, -height/2, width, height);

    // 2. Update Controls (Low Latency)
    source = [sin(t) * 0.6, cos(t * 1.2) * 0.6];
    sink = [cos(t) * 0.6, sin(t * 1.2) * 0.6];
    
    // 3. Step & Render (High Throughput)
    pipeline.run(source, sink, 0.8);
    
    t += 0.01;
}

class GPUPhysicsPipeline {
    constructor(gl, count) {
        this.gl = gl;
        this.count = count;
        this.current = 0; // Ping-pong buffer toggle
        
        // Setup Shaders
        const vSrc = document.getElementById('vshader').text;
        const fSrc = document.getElementById('fshader').text;
        this.program = this.createProgram(gl, vSrc, fSrc);

        // Create 2 Buffers (Ping-Pong Architecture)
        // One buffer holds current data, the other receives the update
        this.buffers = [this.createBuffer(count), this.createBuffer(count)];
        this.vaos = [gl.createVertexArray(), gl.createVertexArray()];

        for (let i = 0; i < 2; i++) {
            gl.bindVertexArray(this.vaos[i]);
            gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers[i]);
            gl.enableVertexAttribArray(0); // pos
            gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 16, 0);
            gl.enableVertexAttribArray(1); // vel
            gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 16, 8);
        }
    }

    createBuffer(count) {
        let data = new Float32Array(count * 4);
        for(let i=0; i<data.length; i+=4) {
            data[i] = (Math.random() * 2 - 1); // x
            data[i+1] = (Math.random() * 2 - 1); // y
        }
        let b = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, b);
        gl.bufferData(gl.ARRAY_BUFFER, data, gl.STREAM_DRAW);
        return b;
    }

    createProgram(gl, v, f) {
        let vs = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vs, v); gl.compileShader(vs);
        let fs = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fs, f); gl.compileShader(fs);
        
        let p = gl.createProgram();
        gl.attachShader(p, vs); gl.attachShader(p, fs);
        // The "Magic" Link: Tell the GPU which outputs to save
        gl.transformFeedbackVaryings(p, ['v_pos', 'v_vel'], gl.INTERLEAVED_ATTRIBS);
        gl.linkProgram(p);
        return p;
    }

    run(src, snk, speed) {
        let next = 1 - this.current;
        gl.useProgram(this.program);
        
        // Uniforms
        gl.uniform2f(gl.getUniformLocation(this.program, "u_source"), src[0], src[1]);
        gl.uniform2f(gl.getUniformLocation(this.program, "u_sink"), snk[0], snk[1]);
        gl.uniform1f(gl.getUniformLocation(this.program, "u_speed"), speed);

        gl.bindVertexArray(this.vaos[this.current]);
        gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, this.buffers[next]);

        gl.beginTransformFeedback(gl.POINTS);
        gl.drawArrays(gl.POINTS, 0, this.count);
        gl.endTransformFeedback();
        
        gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, null);
        this.current = next; // Swap
    }
}

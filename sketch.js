// sketch.js – Optimized Fermat Flow
// Key Upgrades: Field Caching, Vectorized Flow, and High-Speed Integration

let poles = [];
let particles = [];
let field = []; // Pre-calculated Refractive Field (The "Inference Layer")
let resolution = 20; // Grid size for the field
let cols, rows;
let t = 0;
let flowSpeed = 0.8;
let targetParticleCount = 3000; // Bumped up for "throughput"

function setup() {
  createCanvas(windowWidth, windowHeight);
  colorMode(HSB, 360, 100, 100, 1);
  cols = floor(width / resolution) + 1;
  rows = floor(height / resolution) + 1;
  
  poles.push(new TemporalPole(width * 0.7, height * 0.5, 1, "SOURCE"));
  poles.push(new TemporalPole(width * 0.3, height * 0.5, -1, "SINK"));
  
  for (let i = 0; i < targetParticleCount; i++) particles.push(new Particle());
  background(240, 60, 5);
}

function draw() {
  // Use a softer "tail" effect by drawing a semi-transparent rect
  blendMode(BLEND);
  noStroke();
  fill(240, 60, 5, 0.15); 
  rect(0, 0, width, height);

  // Update Field Physics (The "Training" phase - heavy but cached)
  updateField();

  // Particle Physics (The "Inference" phase - low latency)
  blendMode(ADD);
  for (let p of particles) {
    p.follow(field);
    p.update();
    p.display();
  }

  for (let p of poles) {
    p.drift();
    p.display();
  }
  t += 0.005;
}

// 1. THE CACHED FIELD (Optimizing the "Physics Law")
function updateField() {
  for (let i = 0; i < cols; i++) {
    field[i] = [];
    for (let j = 0; j < rows; j++) {
      let x = i * resolution;
      let y = j * resolution;
      
      // Calculate Fermat Gradient + Pole Force
      let force = calculateForce(x, y);
      let fermat = calculateFermatGradient(x, y);
      
      // Combine and store (The "Pre-computed" intelligence)
      force.add(fermat.mult(25));
      force.limit(1); 
      field[i][j] = force;
    }
  }
}

// 2. VECTORIZED GRADIENT (Fermat's Principle: Light seeks the path of least time)
function calculateFermatGradient(x, y) {
  let eps = 5;
  let nL = getRefractiveIndex(x - eps, y);
  let nR = getRefractiveIndex(x + eps, y);
  let nU = getRefractiveIndex(x, y - eps);
  let nD = getRefractiveIndex(x, y + eps);
  
  // The gradient of the refractive index 'n'
  return createVector(nR - nL, nD - nU);
}

function getRefractiveIndex(x, y) {
  let d = dist(x, y, width/2, height/2);
  let lensRadius = 250;
  if (d < lensRadius) {
    // High index in center = slower speed = bending light
    return 1.0 + 2.5 * (0.5 + 0.5 * cos(PI * d / lensRadius));
  }
  return 1.0;
}

function calculateForce(x, y) {
  let v = createVector(0, 0);
  for (let p of poles) {
    let d = dist(x, y, p.pos.x, p.pos.y);
    let mag = (p.q * 500) / (constrain(d, 20, 1000));
    let angle = atan2(y - p.pos.y, x - p.pos.x);
    v.add(p5.Vector.fromAngle(angle).mult(mag));
  }
  return v;
}

class Particle {
  constructor() { this.spawn(); }
  
  spawn() {
    this.pos = createVector(random(width), random(height));
    this.vel = createVector(0, 0);
    this.acc = createVector(0, 0);
    this.prev = this.pos.copy();
    this.h = random(180, 220);
  }

  follow(vectors) {
    let x = floor(this.pos.x / resolution);
    let y = floor(this.pos.y / resolution);
    if (vectors[x] && vectors[x][y]) {
      this.acc.add(vectors[x][y]);
    }
  }

  update() {
    let n = getRefractiveIndex(this.pos.x, this.pos.y);
    this.vel.add(this.acc);
    // Snell's Law Approximation: velocity is inversely proportional to refractive index
    this.vel.limit(4 / n); 
    this.prev = this.pos.copy();
    this.pos.add(this.vel.copy().mult(flowSpeed));
    this.acc.mult(0);
    
    if (this.pos.x < 0 || this.pos.x > width || this.pos.y < 0 || this.pos.y > height) this.spawn();
  }

  display() {
    let speed = this.vel.mag();
    stroke(this.h + speed * 20, 80, 100, 0.5);
    strokeWeight(1.5);
    line(this.prev.x, this.prev.y, this.pos.x, this.pos.y);
  }
}

class TemporalPole {
  constructor(x, y, q, label) {
    this.pos = createVector(x, y);
    this.q = q;
    this.label = label;
    this.seed = random(100);
  }
  drift() {
    this.pos.x = noise(this.seed + t) * width;
    this.pos.y = noise(this.seed + 50 + t) * height;
  }
  display() {
    fill(this.q > 0 ? 20 : 190, 80, 100, 0.2);
    circle(this.pos.x, this.pos.y, 20);
  }
}

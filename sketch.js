// sketch.js – Liquid Particle System (Fermat's Edition)

let poles = [];
let particles = [];
let t = 0;
let autoDrift = true;
let flowSpeed = 0.5;
let targetParticleCount = 2000;

// Fermat Lens Constants
let lensRadius = 220;
let maxRefractiveIndex = 3.0;

function setup() {
  createCanvas(windowWidth, windowHeight);
  colorMode(HSB, 360, 100, 100, 1);
  
  // Initial poles setup
  poles.push(new TemporalPole(width * 0.7, height / 2, 1, "SOURCE"));
  poles.push(new TemporalPole(width * 0.3, height / 2, -1, "SINK"));
  
  initParticles(targetParticleCount);
  background(240, 50, 5, 1); 
}

function initParticles(count) {
  particles = [];
  for (let i = 0; i < count; i++) {
    particles.push(new Particle());
  }
}

function draw() {
  // LAYER 1: Feedback Loop for silky trails
  blendMode(BLEND);
  fill(240, 60, 4, 0.12); // Deep space blue
  rect(0, 0, width, height);
  
  // LAYER 2: The Refractive Field Visualization
  drawRefractiveLens();
  
  // Update poles position
  if (autoDrift) {
    for (let p of poles) p.drift();
  }

  // LAYER 3: Particle Dynamics (Fermat's Principle)
  blendMode(ADD); 
  for (let p of particles) {
    p.update();
    p.display();
  }
  
  // LAYER 4: Interface & Poles
  blendMode(BLEND);
  for (let p of poles) p.display();
  
  t += 0.008;
}

function drawRefractiveLens() {
  push();
  noFill();
  for(let i = 0; i < 3; i++) {
    let pulse = sin(t + i*0.5) * 8;
    stroke(190, 80, 100, 0.08); 
    circle(width/2, height/2, (lensRadius * 2) + pulse);
  }
  pop();
}

// --------------------------------------------------------------
// Particle Logic
// --------------------------------------------------------------

class Particle {
  constructor() {
    this.spawn();
  }

  spawn() {
    this.pos = createVector(random(width), random(height));
    this.prevPos = this.pos.copy();
    this.vel = createVector(0, 0);
    this.hue = 200;
    this.brightness = 0;
  }

  update() {
    this.prevPos = this.pos.copy();
    
    // 1. Calculate Forces
    let baseForce = calculateForce(this.pos.x, this.pos.y);
    let fermatForce = calculateFermatForce(this.pos.x, this.pos.y);
    let n = getRefractiveIndex(this.pos.x, this.pos.y);

    // 2. Physics Integration
    // Light bends toward higher refractive index regions (Fermat's Principle)
    this.vel.x += (baseForce.x + fermatForce.x * 20) * flowSpeed;
    this.vel.y += (baseForce.y + fermatForce.y * 20) * flowSpeed;
    this.vel.limit(4);
    
    // 3. Fermat velocity adjustment: Speed is slower in denser medium (v = c/n)
    this.pos.x += this.vel.x / n;
    this.pos.y += this.vel.y / n;

    // 4. Color Dynamics: Shift hue based on local refraction and velocity
    let speed = this.vel.mag();
    let nEffect = map(n, 1, maxRefractiveIndex, 0, 100);
    this.hue = (200 + nEffect + (this.vel.x * 5)) % 360;
    this.brightness = map(speed, 0, 4, 40, 100);

    this.edges();
  }

  display() {
    let speed = this.vel.mag();
    strokeWeight(map(speed, 0, 4, 0.5, 2.8));
    stroke(this.hue, 80, this.brightness, 0.6);
    line(this.prevPos.x, this.prevPos.y, this.pos.x, this.pos.y);
  }

  edges() {
    if (this.pos.x < 0 || this.pos.x > width || this.pos.y < 0 || this.pos.y > height) {
      this.spawn();
    }
  }
}

// --------------------------------------------------------------
// Field Logic Functions
// --------------------------------------------------------------

function getRefractiveIndex(x, y) {
  let d = dist(x, y, width/2, height/2);
  if (d < lensRadius) {
    // Smooth cosine falloff from center of lens
    return 1.0 + (maxRefractiveIndex - 1.0) * (1 + cos(PI * d / lensRadius)) / 2;
  }
  return 1.0;
}

function calculateFermatForce(x, y) {
  let eps = 2.0; // Gradient step
  let nL = getRefractiveIndex(x - eps, y);
  let nR = getRefractiveIndex(x + eps, y);
  let nU = getRefractiveIndex(x, y - eps);
  let nD = getRefractiveIndex(x, y + eps);
  // Returns the gradient vector (steer toward the "slowest" time)
  return createVector((nR - nL), (nD - nU));
}

function calculateForce(x, y) {
  let v = createVector(0, 0);
  for (let p of poles) {
    let d = dist(x, y, p.pos.x, p.pos.y);
    d = constrain(d, 50, 800);
    let mag = (p.q * 4000) / (d * d);
    let angle = atan2(y - p.pos.y, x - p.pos.x);
    v.x += cos(angle) * mag;
    v.y += sin(angle) * mag;
  }
  return v;
}

class TemporalPole {
  constructor(x, y, q, label) {
    this.pos = createVector(x, y);
    this.q = q; // Charge: positive (future), negative (past)
    this.label = label;
    this.seed = random(1000);
  }
  drift() {
    this.pos.x = noise(this.seed + t) * width;
    this.pos.y = noise(this.seed + 100 + t) * height;
  }
  display() {
    push();
    let c = this.q > 0 ? color(20, 90, 100) : color(190, 90, 100);
    translate(this.pos.x, this.pos.y);
    for(let i = 3; i > 0; i--) {
      fill(hue(c), saturation(c), brightness(c), 0.1 / i);
      noStroke();
      circle(0, 0, i * 35);
    }
    fill(255);
    textAlign(CENTER);
    textSize(11);
    text(this.label, 0, -30);
    pop();
  }
}

// --------------------------------------------------------------
// UI Event Handlers (Linked to HTML)
// --------------------------------------------------------------

function toggleMotion() {
  autoDrift = !autoDrift;
}

function resetParticles() {
  for (let p of particles) p.spawn();
}

function resetField() {
  poles = [];
}

function updateParticleCount(val) {
  targetParticleCount = parseInt(val);
  document.getElementById('particleCountVal').innerText = val;
  initParticles(targetParticleCount);
}

function updateSpeed(val) {
  flowSpeed = parseFloat(val);
  document.getElementById('speedVal').innerText = val;
}

function keyPressed() {
  if (key === '+') {
    poles.push(new TemporalPole(mouseX, mouseY, 1, "SOURCE"));
  } else if (key === '-') {
    poles.push(new TemporalPole(mouseX, mouseY, -1, "SINK"));
  }
  return false; // Prevent browser scrolling
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
}

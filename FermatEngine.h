#pragma once
#include <vector>
#include <memory>

// High-Performance Engine API
class FermatEngine {
public:
    FermatEngine(int particleCount);
    ~FermatEngine();

    // High Throughput: Update 100k+ particles in parallel
    void step(float deltaTime);

    // Low Latency: Data stays in VRAM for rendering
    void render();

    // API Controls
    void setSource(float x, float y, float z);
    void setSink(float x, float y, float z);
    void setLensRadius(float r);

private:
    struct Impl; 
    std::unique_ptr<Impl> pImpl; // Hidden GPU logic
};

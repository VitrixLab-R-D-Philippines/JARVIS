#include "FermatEngine.h"
#include <glad/glad.h> // Modern OpenGL API

struct FermatEngine::Impl {
    GLuint ssbo, computeShader, renderShader;
    int count;

    void init() {
        // 1. Allocate VRAM for 100,000 particles
        glGenBuffers(1, &ssbo);
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo);
        glBufferData(GL_SHADER_STORAGE_BUFFER, count * sizeof(Particle), NULL, GL_DYNAMIC_DRAW);
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, ssbo);
    }
    
    void dispatch(float dt) {
        glUseProgram(computeShader);
        glUniform1f(0, dt); // Pass time to GPU
        // Parallel API: Run 100k threads in chunks of 256
        glDispatchCompute(count / 256, 1, 1);
        
        // Memory Barrier: Ensure physics finish before rendering starts
        glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT);
    }
};

void FermatEngine::step(float dt) { pImpl->dispatch(dt); }
void FermatEngine::render() {
    // Zero-Copy Rendering: Draw directly from the SSBO we just updated
    glBindBuffer(GL_ARRAY_BUFFER, pImpl->ssbo);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Particle), (void*)0);
    glDrawArrays(GL_POINTS, 0, pImpl->count);
}

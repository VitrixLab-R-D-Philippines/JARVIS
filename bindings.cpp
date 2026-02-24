#include <emscripten/bind.h>
#include "FermatEngine.h"

using namespace emscripten;

// This blocks exposes the C++ API to your JavaScript environment
EMSCRIPTEN_BINDINGS(fermat_engine) {
    class_<FermatEngine>("FermatEngine")
        .constructor<int>()
        .function("step", &FermatEngine::step)
        .function("render", &FermatEngine::render)
        .function("setSource", &FermatEngine::setSource)
        .function("setSink", &FermatEngine::setSink)
        .function("setLensRadius", &FermatEngine::setLensRadius);
}

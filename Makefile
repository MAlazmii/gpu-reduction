CXX = c++
NVCC = nvcc
PYTHON = python3
CXXFLAGS = -O3 -std=c++17 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror
CUDA_ARCH = sm_70
NVCCFLAGS = -O3 -std=c++17 -lineinfo

.PHONY: all cpu cuda test test-cuda sanitize gpu-sanitize clean
all: cpu
# Always regenerate the executable and its manifest together. This small project
# favors reliable flag/source tracking over incremental-build complexity.
cpu: | build
	$(PYTHON) scripts/build.py build/reduce_cpu $(CXX) $(CXXFLAGS) src/main.cpp src/cpu.cpp -o build/reduce_cpu
cuda: | build
	$(PYTHON) scripts/build.py build/reduce_cuda $(NVCC) $(NVCCFLAGS) -arch=$(CUDA_ARCH) -DREDUCE_CUDA src/main.cpp src/cuda.cu -o build/reduce_cuda
build:
	mkdir -p build
test: cpu
	TEST_CXX="$(CXX)" REDUCTION_BACKEND=cpu $(PYTHON) -m unittest discover -s tests -v
test-cuda: cuda
	REDUCTION_BACKEND=cuda $(PYTHON) -m unittest discover -s tests -p test_reduction.py -v
sanitize: | build
	$(CXX) -O1 -g -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer src/main.cpp src/cpu.cpp -o build/reduce_sanitize
	REDUCTION_BACKEND=cpu REDUCTION_BINARY=$(CURDIR)/build/reduce_sanitize $(PYTHON) -m unittest discover -s tests -p test_reduction.py -v
gpu-sanitize: cuda
	$(PYTHON) scripts/gpu_sanitize.py
clean:
	rm -rf build

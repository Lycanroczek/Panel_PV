# RP2350 (ARM) platform variant
# Nie używamy RISC-V core - tylko Arm

# Explicit platform selection (to ensure ARM core, not RISC-V)
set(PICO_PLATFORM rp2350-arm-s)

# Minimal debug info
set(PICO_COMPILE_OPTIONS -Os)

# Standard for C/C++
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# ==================== Enviroment Setting ====================

$env:WORK_DIR = get-location
$env:CARLA_ROOT = "$env:WORK_DIR\carla"
$env:CARLA_SERVER = "$env:CARLA_ROOT\CarlaUE4.exe"

# Headless Mode
$env:SDL_VIDEODRIVER = "offscreen"
$env:SDL_HINT_CUDA_DEVICE = "0"

# Run Carla Server
& $env:CARLA_SERVER -log -carla-server -world-port=2000 -RenderOffScreen -nosound -quality-level=Low

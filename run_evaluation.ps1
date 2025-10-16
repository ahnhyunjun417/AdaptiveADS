# ==================== Usage 안내 ====================
if ($args.Count -lt 4) {
    Write-Host "Usage: .\run_evaluation.ps1 <AGENT> <PORT> <ROUTE_NAME> <SCENARIO_NAME>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  .\run_evaluation.ps1 basic 2000 42routes 42routes" -ForegroundColor Green
    exit 1
}

# ==================== Enviroment Setting ====================

$env:WORK_DIR = get-location
$env:CARLA_ROOT = "$env:WORK_DIR\carla"
$env:CARLA_SERVER = "$env:CARLA_ROOT\CarlaUE4.exe"

# PYTHONPATH Setting
$env:PYTHONPATH = "$env:PYTHONPATH;$env:CARLA_ROOT\PythonAPI"
$env:PYTHONPATH = "$env:PYTHONPATH;$env:CARLA_ROOT\PythonAPI\carla"
$env:PYTHONPATH = "$env:PYTHONPATH;$env:CARLA_ROOT\PythonAPI\carla\dist\carla-0.9.10-py3.7-win-amd64.egg"
$env:PYTHONPATH = "$env:PYTHONPATH;$env:WORK_DIR\scenario_runner"
$env:PYTHONPATH = "$env:PYTHONPATH;$env:WORK_DIR\leaderboard"
$env:PYTHONPATH = "$env:PYTHONPATH;$env:WORK_DIR\transfuser"

$env:CHALLENGE_TRACK_CODENAME = "SENSORS"
$env:RESUME = "1"
$env:TEAM_CONFIG = "$env:WORK_DIR\model_ckpt"

# ==================== Script Arguments ====================
$AGENT = $args[0]
$PORT = $args[1]
$ROUTE_NAME = $args[2]
$SCENARIO_NAME = $args[3]

$env:AGENT = $AGENT
$env:PORT = $PORT
$env:ROUTE_NAME = $ROUTE_NAME
$env:SCENARIO_NAME = $SCENARIO_NAME

$env:TEAM_AGENT = "$env:WORK_DIR\transfuser\${AGENT}_agent.py"
$env:ROUTES = "$env:WORK_DIR\leaderboard\data\routes\${ROUTE_NAME}.xml"
$env:SCENARIOS = "$env:WORK_DIR\leaderboard\data\scenarios\${SCENARIO_NAME}.json"
$env:CHECKPOINT_ENDPOINT = "$env:WORK_DIR\results\${AGENT}_${ROUTE_NAME}.json"

# ==================== Execute Python Script ====================
python leaderboard\leaderboard\leaderboard_evaluator.py `
    --port=$PORT `
    --trafficManagerPort="1$PORT" `
    --routes=$env:ROUTES `
    --scenarios=$env:SCENARIOS `
    --agent=$env:TEAM_AGENT `
    --agent-config=$env:TEAM_CONFIG `
    --track=$env:CHALLENGE_TRACK_CODENAME `
    --resume=$env:RESUME `
    --checkpoint=$env:CHECKPOINT_ENDPOINT `
    --gui_support

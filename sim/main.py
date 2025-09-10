import os, asyncio, json
from fastapi import FastAPI, WebSocket, Body
from fastapi.staticfiles import StaticFiles
from sim import BioReactorSim
from mqtt_bridge import MqttBridge

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TICK_MS = int(os.getenv("TICK_MS", "200"))
UI_PORT = int(os.getenv("UI_PORT", "8000"))
UI_ENABLED = os.getenv("UI_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")
SEED = int(os.getenv("SEED", "42"))
TIME_SCALE = float(os.getenv("TIME_SCALE", "1.0"))

sim = BioReactorSim(seed=SEED)
app = FastAPI()
if UI_ENABLED:
    # Serve static UI under /ui and redirect root to /ui/
    app.mount("/ui", StaticFiles(directory="ui/static", html=True), name="ui")
    from fastapi.responses import RedirectResponse

    @app.get("/")
    def _root():
        return RedirectResponse(url="/ui/")

def _to_bool01(v: str) -> int:
    v = v.strip().lower()
    return 1 if v in ("1", "on", "true", "yes") else 0


def _to_float01(v: str) -> float:
    v = v.strip().lower()
    if v in ("on", "true", "yes"):
        return 1.0
    if v in ("off", "false", "no"):
        return 0.0
    try:
        f = float(v)
    except Exception:
        f = 0.0
    return max(0.0, min(1.0, f))


def on_cmd(topic, payload):
    raw = payload.decode("utf-8") if isinstance(payload, (bytes, bytearray)) else str(payload)
    val = raw.strip().lower()
    # Simulation control commands under bioreactor/simCmd/* (and legacy /cmd/reset)
    if topic.endswith("/simCmd/reset") or topic.endswith("/cmd/reset"):
        # If a seed is provided in payload, use it; else reuse current SEED
        try:
            seed_val = int(raw.strip())
        except Exception:
            seed_val = SEED
        sim.__init__(seed=seed_val)
        return
    if topic.endswith("/simCmd/time_scale"):
        global TIME_SCALE
        try:
            ts = float(raw.strip())
        except Exception:
            ts = TIME_SCALE
        # clamp to sane range [0, 50]
        TIME_SCALE = max(0.0, min(50.0, ts))
        return
    if topic.endswith("/valve_in"):
        sim.u.valve_in = _to_bool01(val)
    if topic.endswith("/valve_out"):
        sim.u.valve_out = _to_bool01(val)
    if topic.endswith("/heater"):
        sim.u.heater = _to_float01(val)
    if topic.endswith("/aeration"):
        sim.u.aeration = _to_float01(val)
    if topic.endswith("/agitation"):
        sim.u.agitation = _to_float01(val)
    if topic.endswith("/vent"):
        # comando de exaustão (0..1)
        sim.u.vent = _to_float01(val)

mb = MqttBridge(MQTT_HOST, MQTT_PORT, on_cmd)
mb.loop_start()

@app.get("/health")
def health(): return {"ok": True}

# Simple HTTP control endpoints for UI buttons
@app.post("/api/sim/reset")
async def api_reset(seed: int | None = None):
    try:
        seed_val = int(seed) if seed is not None else SEED
    except Exception:
        seed_val = SEED
    sim.__init__(seed=seed_val)
    return {"ok": True, "seed": seed_val}

@app.post("/api/sim/time_scale")
async def api_time_scale(value: float | None = Body(None, embed=True)):
    global TIME_SCALE
    try:
        ts = float(value) if value is not None else TIME_SCALE
    except Exception:
        ts = TIME_SCALE
    TIME_SCALE = max(0.0, min(50.0, ts))
    return {"ok": True, "time_scale": TIME_SCALE}

if UI_ENABLED:
    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                await asyncio.sleep(TICK_MS / 1000)
                data = sim.readout(include_actuators=True)
                # Adiciona parâmetros de simulação e variáveis ambientais
                data["time_scale"] = TIME_SCALE
                # Variáveis ambientais (ambiente externo)
                data["pressure_ext_kpa"] = getattr(sim, "Patm", 101.3)
                data["temperature_ext_c"] = getattr(sim, "Tamb", 25.0)
                await ws.send_text(json.dumps(data))
        except Exception:
            # Client closed or server shutdown; silently exit WS loop
            pass

async def loop():
    while True:
        dt = (TICK_MS/1000) * TIME_SCALE
        sim.step(dt)
        # Publish sensors and actuators to MQTT
        mb.publish_state(sim.readout(), actuators=sim.actuators())
        await asyncio.sleep(TICK_MS/1000)

@app.on_event("startup")
async def _startup():
    asyncio.create_task(loop())

FROM python:3.11-slim

WORKDIR /app
COPY sim/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (paths are relative to the build context root)
# When `docker build` is run with context `.` and this Dockerfile located at sim/Dockerfile,
# the source files live under `sim/` in the build context.
# Copy application python sources
COPY sim/main.py sim/mqtt_bridge.py sim/sim.py ./
# Copy UI into /app/ui so the static files are available at runtime
COPY ui ./ui
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host","0.0.0.0","--port","8000"]
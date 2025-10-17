Publishing the Docker image to Docker Hub
=====================================

This project includes an automated GitHub Actions workflow that builds and pushes the Docker image for the `./sim` folder to Docker Hub on pushes to `main`.

Workflow file
-------------

- `.github/workflows/docker-publish.yml` — builds `./sim/Dockerfile` and pushes two tags:
  - `${{ secrets.DOCKERHUB_USERNAME }}/bioreactor-sim:latest`
  - `${{ secrets.DOCKERHUB_USERNAME }}/bioreactor-sim:<commit-sha>`

Required setup
--------------

1. Create a Docker Hub repository (for example `profilgusto/bioreactor-sim`).
2. Add the following GitHub Actions secrets in your repository settings:
   - `DOCKERHUB_USERNAME` — your Docker Hub username.
   - `DOCKERHUB_TOKEN` — a Docker Hub access token (or password). A token is recommended.

How it works
------------

- When you push to `main` the workflow will:
  1. Checkout the repo
  2. Set up docker buildx and qemu (multi-arch builds)
  3. Login to Docker Hub using the provided secrets
  4. Build the image from `./sim` and push `latest` and a commit-SHA tag

Using the published image
-------------------------

Pull the published image:

```bash
docker pull profilgusto/bioreactor-sim:latest
```

Run the container locally (example):

```bash
docker run --rm -p 8000:8000 --name bioreactor-sim \
  -e MQTT_HOST=host.docker.internal \
  -e MQTT_PORT=1883 \
  profilgusto/bioreactor-sim:latest
```

Notes
-----

- `docker-compose.yml` in the repository is configured with `image: profilgusto/bioreactor-sim:latest` and still contains `build: ./sim`. `docker compose up --build` will still build locally and use that image name.
- If you want to publish from a different branch or tag, you can trigger the workflow manually from the Actions tab (workflow_dispatch) or adjust the triggers in the workflow file.

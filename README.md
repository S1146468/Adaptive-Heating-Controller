# Adaptive Heating Controller

Version **0.1.0** is an experimental, read-only Home Assistant App installation
foundation for **aarch64 / ARM64**, including Raspberry Pi 5 with 64-bit Home
Assistant OS. Physical Pi verification is tracked separately in [issue #2](https://github.com/S1146468/Adaptive-Heating-Controller/issues/2).
It is not yet the complete v0.1.0 roadmap milestone.

The process logs its mode and waits for shutdown. It does not connect to Home
Assistant, ingest sensors, store history, expose diagnostics entities, calculate
MPC, or control heating. No credentials, entity mappings or sensors are required.
Existing ESPHome controllers and heating automations remain authoritative.
There are no control-mode options, API clients, service/action calls, exposed
ports, device mappings, host-network access or Supervisor/API permissions.

## Install in Home Assistant

After this implementation is merged to the default branch:

1. On 64-bit Home Assistant OS, open **Settings → Apps** (called **Add-ons** in
   older versions), then the app store's menu → **Repositories**.
2. Add `https://github.com/S1146468/Adaptive-Heating-Controller`.
3. Refresh the store, select **Adaptive Heating Controller**, and **Install**.
   Supervisor builds the image locally; allow time for the initial image pull.
4. Leave protection mode enabled. There is no configuration to enter.
5. Select **Start** and open **Logs**. Confirm the startup line below.
6. Select **Stop** and confirm the graceful-shutdown line. The stop timeout is
   10 seconds; normal shutdown should take substantially less than that.
7. Select **Start** again, or **Restart** while running, and confirm a fresh
   read-only startup line. Start on boot is off by default (`boot: manual`).

Expected log lines (Home Assistant may add timestamps or its own container logs):

```text
Adaptive Heating Controller 0.1.0 started (mode=read-only)
Adaptive Heating Controller 0.1.0 stopped gracefully (mode=read-only)
```

No heartbeat is printed. Silence after startup is expected. No physical command
is issued on startup, stop or restart. Record the native installation results,
Home Assistant OS, Core and Supervisor versions in issue #2. Hosted ARM64 CI
cannot establish Supervisor installation or Raspberry Pi compatibility.

## Files and build toolchain

- `repository.yaml`: Home Assistant repository metadata.
- `adaptive_heating_controller/config.yaml`: manifest, stable slug, ARM64 only.
- `adaptive_heating_controller/Dockerfile`: Docker Official Python base
  `python:3.12.12-alpine3.22` (CPython 3.12.12 / Alpine 3.22); no runtime packages
  are installed. The tag fixes the Python/Alpine versions but upstream can
  rebuild it; CI records the resolved base digest in the build log.
- `adaptive_heating_controller/run.sh`: uses `exec` to forward container signals
  to `app/__main__.py`, without leaving a shell parent. Manifest `init: true`
  uses Docker's init; this image does not use S6.
- `scripts/validate_metadata.py`: strict release-specific metadata allowlist,
  rejecting missing/invalid fields, additional privileges and mode options.
- `scripts/smoke_container.py`: real offline container lifecycle and negative control.
- `.github/workflows/validate.yaml`: metadata, Ruff, Python tests, native ARM64
  image build and lifecycle checks. No QEMU/emulation is used.
- [Product roadmap, version 0.4](docs/Adaptive-Heating-Controller-Project-Description.txt):
  faithful supplied source, including later learning/control milestones.

Packaging references: [Home Assistant manifest](https://contributors.home-assistant.io/apps/reference/configuration/)
and [container guide](https://contributors.home-assistant.io/apps/guides/dockerfile/).
Any architecture-compatible base is supported; the Python base needs no Home
Assistant-specific utilities for this offline foundation.

## Reproduce checks and container lifecycle

Use Python 3.12, Docker Engine with Buildx, and a native Linux ARM64 host.
The CI runner is `ubuntu-24.04-arm`. On another architecture you must configure
ARM64 emulation yourself and explicitly report that environment as emulated.
Only ARM64 is advertised; checks running on x86 do not imply x86 app support.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python --version
python -m pip freeze
python scripts/validate_metadata.py
ruff check .
python -m unittest discover -s tests -v

git rev-parse HEAD
uname -m
docker version
docker buildx version
docker buildx build --platform linux/arm64 --load --progress plain -t ahc:test adaptive_heating_controller
docker image inspect ahc:test
docker run --rm --network none --entrypoint python ahc:test --version
python scripts/smoke_container.py ahc:test --expect-immediate-exit
python scripts/smoke_container.py ahc:test
```

The smoke test starts with `--init --network none`, requires exact startup logs
and continuous survival for **30 seconds**, stops with `docker stop --time 10`,
checks shutdown logs, elapsed time and exit code 0, then starts the same stopped
container and repeats the 30-second observation and stop. Forced termination or
unexpected/repetitive logs fail the test. Cleanup removes only its own uniquely
named test container. The negative control overrides the entrypoint with an
immediately exiting Python process and verifies the same observation check
rejects it. Unit tests corrupt temporary manifest copies (architecture, version,
API permission and active options) and require the CLI validator to fail.

For manual inspection:

```sh
docker run -d --init --network none --name ahc-manual ahc:test
docker logs ahc-manual
docker inspect --format '{{.State.Running}}' ahc-manual
docker stop --time 10 ahc-manual
docker logs ahc-manual
docker inspect --format '{{.State.ExitCode}}' ahc-manual
docker start ahc-manual
docker logs ahc-manual
docker restart --time 10 ahc-manual
docker logs ahc-manual
docker stop --time 10 ahc-manual
docker rm ahc-manual
```

## Troubleshooting and verification limits

- **App missing:** refresh the repository/store and check 64-bit `aarch64`
  architecture. There is no image for 32-bit ARM or x86. Before merge, test a
  local app checkout under Supervisor's `/addons/local/` instead of expecting
  the default-branch store entry to exist.
- **Image pull/build fails:** save the Supervisor build log; check registry
  access and disk space. Installation requires registry access even though the
  running application is entirely offline.
- **No logs:** confirm the app is started and inspect the full container log.
  Expect one startup line and no periodic activity.
- **Restart loop, traceback or stop timeout:** this is a failure, not normal
  operation. Disable Start on boot, save logs and report the exact step,
  architecture and OS/Supervisor versions. No actuator recovery is needed from
  this foundation because it has no command path.
- **Missing sensors/tokens:** intentionally irrelevant at this stage. Do not
  add credentials to work around a startup failure.

CI proves metadata validation, Python process handling and an actual native
ARM64 Docker build/offline lifecycle when its jobs pass. It does not prove
physical Pi installation, live Home Assistant connectivity or heating control.
All later active-control work requires separate design and commissioning.

"""Exercise the actual container offline, including restart and normal SIGTERM stop."""

import argparse
import json
import subprocess
import time
import uuid

START = "Adaptive Heating Controller 0.1.0 started (mode=read-only)"
STOP = "Adaptive Heating Controller 0.1.0 stopped gracefully (mode=read-only)"


def docker(*args: str) -> str:
    return subprocess.check_output(["docker", *args], text=True, stderr=subprocess.STDOUT).strip()


def inspect(name: str) -> dict:
    return json.loads(docker("inspect", name))[0]


def observe(name: str, seconds: float, starts: int) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not inspect(name)["State"]["Running"]:
            raise AssertionError("Container exited during observation")
        time.sleep(0.5)
    lines = docker("logs", name).splitlines()
    expected = [START, STOP] * (starts - 1) + [START]
    if lines != expected:
        raise AssertionError(f"Unexpected lifecycle logs: {lines!r}")


def stop(name: str) -> None:
    before = time.monotonic()
    docker("stop", "--time", "10", name)
    elapsed = time.monotonic() - before
    state = inspect(name)["State"]
    logs = docker("logs", name).splitlines()
    if state["Running"] or state["ExitCode"] != 0 or state["OOMKilled"]:
        raise AssertionError(f"Unclean exit: {state}")
    if elapsed >= 10 or logs[-1] != STOP:
        raise AssertionError(f"Shutdown exceeded timeout or missing message: {logs}")
    print(f"SIGTERM stop: {elapsed:.3f}s, exit={state['ExitCode']}, no forced termination")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--expect-immediate-exit", action="store_true")
    args = parser.parse_args()
    name = "ahc-smoke-" + uuid.uuid4().hex[:12]
    extra = ["--entrypoint", "python"] if args.expect_immediate_exit else []
    command = ["-c", "pass"] if args.expect_immediate_exit else []
    try:
        docker("run", "--detach", "--init", "--network", "none", "--name", name,
               *extra, args.image, *command)
        if inspect(name)["HostConfig"]["NetworkMode"] != "none":
            raise AssertionError("Container must run without networking")
        if args.expect_immediate_exit:
            try:
                observe(name, 3, 1)
            except AssertionError as error:
                if "exited during observation" not in str(error):
                    raise
                print("Negative control passed: immediately exiting process detected")
                return
            raise AssertionError("Smoke test accepted an immediately exiting process")
        observe(name, 30, 1)
        stop(name)
        docker("start", name)
        observe(name, 30, 2)
        stop(name)
        print(docker("logs", name))
        print("Offline lifecycle passed: start, 30s alive, stop, restart, 30s alive, stop")
    finally:
        subprocess.run(["docker", "rm", "--force", name], check=False)


if __name__ == "__main__":
    main()

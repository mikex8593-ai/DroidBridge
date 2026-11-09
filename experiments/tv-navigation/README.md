# Guarded TV Navigation Lab

An experimental Python/ADB navigation layer for AI-assisted Android TV operation. It moves short, verified button sequences close to the device to reduce repeated cloud screenshot/decision/input cycles.

**Not a new DroidBridge APK, not an upstream release, and not a universal autonomous TV controller.** The implementation is a separately authored experiment intended to inform future DroidBridge integration. DroidBridge's upstream project is https://github.com/zephyr7030/DroidBridge.

## What is included

- A bounded mapping runner with app/activity/version checks, cancellation, focus freshness checks, and final verification.
- A supervised ADB adapter and an example Crunchyroll settings mapping.
- A direct launcher for ten example streaming-app packages with exact version checks. Foreground verification is not playback verification.
- A screen-recognition cache that refuses unfamiliar, changed or stale state.
- 56 offline tests using synthetic state and mocked transport. Tests do not access a TV.

## Run tests

Python 3.10+ and a Unix-like system are expected (the adapters use `fcntl`). From this directory:

```sh
python3 -m unittest discover -v
```

## Supervised device use

Only use a device you own or have permission to operate. First establish ADB access yourself; this project does not grant access or change network/security settings. Install Android platform tools from their official source. Verify nobody is using the TV, coordinate other operators, and mute during testing.

Set `TV_ADB_SERIAL` to an already authorized ADB device identifier and `TV_EXPECTED_DEVICE` to that device's verified `ro.product.device` value. There is deliberately no default device address. Keep local values out of Git.

```sh
python3 launch_app.py hulu             # preview only
python3 launch_app.py hulu --execute   # explicit live action
python3 adb_adapter.py crunchyroll-settings  # preview only
```

Do not execute the example player mapping until its exact app version, foreground, layout and focus have been verified on your own device. The shipped catalog is an example, not a portable claim of validation. A local reviewer may mark a screen `live_verified` only after testing it. Unknown or changed screens require a fresh observation, not guessed click replay.

Create `STOP` in this directory to cancel. The lock coordinates this runner's processes only; it is not a system-wide lease or detection of human input. Do not run multiple independent controllers together.

## Observed results and limits

During one supervised investigation, a guarded settings sequence reached the target menu in roughly 4.6–4.9 seconds and completed final verification in 7.2–7.5 seconds. These are a small sample, not a universal benchmark. Direct-launch successes covered ten app targets; initial timeouts occurred for two and the cause was not established. App versions and platform behavior change.

Some apps expose useful accessibility nodes; others expose little or no text. A stock hierarchy dump was slower than a screenshot in the initial sample. The primary win was avoiding repeated cloud roundtrips, not eliminating all screenshots. DRM-protected screens, profiles, purchases, transient overlays and changed layouts require care. No purchase, subscription, profile or audio-language automation is included.

## Integration direction

A future native adapter should implement `state`, `observe`, `keys`, and `cancelled` through DroidBridge's supported runtime, input lease, permission checks and cancellation controls. This repository does not ship that integration or expose a network service.

See [AGENT_GUIDE.md](AGENT_GUIDE.md) for operator instructions and [PROVENANCE.md](PROVENANCE.md) for attribution.

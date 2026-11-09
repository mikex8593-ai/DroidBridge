# Instructions for AI operators

1. Confirm the device is available and the requested task is authorized. Use the user's chosen viewing profile; do not infer it from personal names in screenshots.
2. Preview the operation. Check the exact app version and current foreground before a navigation sequence.
3. Prefer direct launch for opening a supported app. Treat foreground, home-ready, title-selected and playing as separate milestones.
4. Reuse a mapping only from its verified starting state. Fresh observations are mandatory after version changes, unknown screens, focus changes, errors or expired transient controls.
5. Batch only short bounded navigation steps. Never batch purchases, sign-in, permission prompts or uncertain selections.
6. Stop on cancellation, ambiguous state, another controller, or human use. Do not blindly retry an action that might already have taken effect.
7. Use screenshots where accessibility nodes are absent. A remembered layout does not prove the current screen matches it.
8. Report actual results and timings, including setup/observation time. A tool call returning success does not by itself prove a show is playing.
9. Stop playback after testing and restore the agreed neutral screen. Do not change account settings or clear watch history without permission.
10. Keep screenshots, private addresses, profile names, tokens and device inventories out of public commits.

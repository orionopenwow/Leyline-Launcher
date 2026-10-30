slug: troubleshooting
title: Troubleshooting
kicker: Chapter 17 · Help
summary: The common messages and fixes, for the launcher, the browser, the game and hosting, and where the logs are.

## Find your logs {#logs}

Launcher: **Settings → Folders → Open logs**. The files that matter are `launcher.log`, `update.log` and `web-backend.log`. Attach them to a bug report (they don't contain your password).

## Launcher messages {#launcher}

| Message | Fix |
| --- | --- |
| **CHOOSE YOUR GAME'S DATA FOLDER** | Press PLAY and pick your game's `Data` folder (or the folder with the game's `.exe`), or play in your browser |
| **Missing X.MPQ** / **X is damaged** | That client is incomplete: pick another folder |
| **This is build N; Leyline needs the 1.12.1 game client (build 5875)** | Wrong version: Leyline needs Vanilla Client v1.3 (English, build 5875) |
| **The game's .exe wasn't found there** | Pick the folder that contains the game's `.exe`, not its parent |
| **SERVER OFFLINE** | The realm is down; check #server-status on Discord, or [Play Solo](solo.html) |
| **This realm doesn't let the desktop game in yet** | The realm takes the browser client only for now: switch to **Browser** |
| **Your sign-in for this realm has ended** | Sign in again (top right), then PLAY |
| **The game is a Windows program: install Wine** | On Linux or macOS the stock client runs through Wine (`sudo apt install wine`, or set `WINE` to your runner), or switch to **Browser** |
| **This realm has no website set** | Pick another realm, or add its portal URL on the Realms page |
| **Leyline is offline** | The central services can't be reached; you can still play Solo and join friends directly |
| **That isn't a Leyline invite link** | Copy the whole link again, or use **Join by address** |
| **Host key changed** | Ask your friend for a new invite link; don't join until they confirm |
| **The update couldn't be applied** | It retries next start; details in `Logs\update.log` |
| Windows says **Unknown publisher** | The launcher isn't code-signed yet: **More info → Run anyway**, or check the checksum first |

## Browser messages {#browser}

See [Playing in the browser](browser.html#trouble). Refreshing once, or trying another browser, fixes most problems.

## In the game {#in-game}

| Problem | Fix |
| --- | --- |
| A Vanilla Remastered window is lost off-screen | `/wnl reset` |
| The interface feels wrong after a change | `/setup` and pick a preset, or `/vanilla` for pure Vanilla |
| An addon errors | Turn it off in `/addons`; for your own addons ask an AI agent with the **Fix an addon error** prompt ([AI](ai.html#prompts)) |
| Stuck, dead in a bad spot, talents broken | **Help → Talk to a GM** ([Tickets](community.html#tickets)) |
| Quest pins or threat missing | Those need the realm; on some realms they're not available |

## Hosting {#hosting}

Hosting now uses Leyline's one-click hosting ([Host your own realm](hosting.html)). If your realm doesn't come online, run the starter file again and ask in the Discord **help** forum with what it printed.

## Still stuck? {#still-stuck}

Ask in the Discord **help** forum with what you did, what you expected, what happened, and your logs. Security problems: report them privately ([security.html](../security.html)).

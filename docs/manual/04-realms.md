slug: realms
title: Realms and friends
kicker: Chapter 4 · Play
summary: The classic launcher's realm browser: add a server by address, join friends with invite links, and how relays, direct connections and nodes work.

> **Note:** This chapter is about the classic launcher. The Leyline realm list is at [play.openvanilla.app/wrath/leyline-preview/realms](https://play.openvanilla.app/wrath/leyline-preview/realms), and hosting your own is one click: see [Host your own realm](hosting.html).

## The realm browser {#browser}

In the launcher, **Realms → Realm browser** shows the live directory, filterable by type, template and free room, plus your favourites and recent realms. Realms come in groups:

| Group | Meaning |
| --- | --- |
| **Verified realms · Official** | Run by Leyline |
| **Verified realms · Vetted** | Checked by the maintainers |
| **Community P2P realms** | Hosted by players; not vetted, play at your own risk |

The [Leyline realm list](https://play.openvanilla.app/wrath/leyline-preview/realms) shows the realms on the Leyline network.

## Add a server by address {#add-server}

**Realms → My servers → Add a server**: name, host or IP, port (default `3724`), the realm's website (optional) and which client to use. Each row shows its ping, with **Select**, **Website** and **Remove**. The **Community list** has hand-picked servers with a **Play here** button.

Using a stock client without the launcher? Put `set realmlist <address>` in the client's `realmlist.wtf`.

## Invite links {#invites}

A friend hosting a realm can send you an invite link. Paste it in the **Invite link** box and press **Join invite**, or just click it: Windows hands it to the launcher. Before you join, the launcher shows what kind of connection it is.

**Join by address** takes an address (`host:port`) and optionally a guest code, account and password.

> **Note:** Peer-to-peer invites, the relay and the community directory are built and tested but switch on later. Until then, add friends' servers by address.

## Relay or direct? {#relay-direct}

| Connection | Your IP | Notes |
| --- | --- | --- |
| **Through the relay** (recommended) | Hidden | Traffic passes through Leyline's relay, end-to-end encrypted |
| **Direct** | The host sees it | Sign-in details between friends travel unencrypted; only join hosts you trust |
| **LAN** | Same network | Leyline isn't involved at all |

The launcher remembers a host's key the first time you join. If it changes, it warns you ("Host key changed … ask them for a new invite link"): someone may be pretending to be them.

## The node network {#nodes}

The classic launcher's volunteer node network never left its test round and is retired. Leyline's network carries players to hosts for you.

## How the player network works {#p2p}

Leyline's network is built so anyone can host a realm and anyone can find and join it safely. It has five parts:

| Part | Runs on | What it does |
| --- | --- | --- |
| **The host** | The host's PC (or Leyline's servers for official realms) | Runs the whole world: every player, creature, bot and spell |
| **The directory** | Leyline's server | Lists realms by tier, checks they're reachable, tells your launcher how to reach them |
| **Relays** | Leyline's servers | Carry traffic for hosts behind home routers, hiding both sides' IP addresses |
| **Nodes** | Volunteers' PCs | Extra relays: more connections, attack absorption, shorter routes |
| **One sign-in** | Leyline's server | Short-lived, realm-bound tokens: you never make a password per realm, and hosts never see yours |

Your connection is sealed end to end between your launcher and the host: a relay or node only copies bytes it can't read, and it can't pretend to be the host.

> **Note:** Relays, nodes and the directory are built and tested, and switch on in stages. Until then, join friends by address (above).

## Why there isn't one giant world {#scaling}

A realm's whole world runs in one server program on one machine; on the server Leyline uses, each continent is updated by a single processor core. Relays and nodes add **connections**, not world power: they can't run part of someone's world, and letting volunteers do that would let them hand out items or read everyone's chat.

So Leyline grows in two ways at once:

- **The official realm gets faster:** measured tuning, then splitting each continent into regions that run in parallel (the approach Nostalrius used), and copies ("layers") only for launches and big events.
- **The network gets wider:** more realms, official and player-hosted, all behind one sign-in, one realm list and one set of rules. Busy community realms can grow up: **Community** → **Verified** → hosted on a datacenter server while staying run by their community.

Characters stay on their realm. Things without in-game power (your Discord roles, website achievements, cosmetics) follow you everywhere.

## Hosting for friends {#host-for-friends}

Want to be the one with the realm? See [Host your own realm](hosting.html).

Read in [Español](README.md)

<div align="center">
  <img src="docs/assets/banner.png" alt="Cerberus Gate Banner" width="400"/>
  <h1>🛡️ CERBERUS GATE SYSTEM</h1>
  <h3>Cognitive Defense Architecture and Isolated Routing</h3>
  <p><i>The "Cerberus Gate" Framework</i></p>
</div>

---

## 👁️ Overview

**Cerberus Gate** is a hyper-modular, tactical-grade Artificial Intelligence framework. Unlike a conventional LLM assistant, Cerberus is an ecosystem that separates cognitive capabilities (the AI) from hardware control (your PC), injecting an unbreakable layer of physical and human protection (**Human-in-The-Loop**).

The base repository contains the architecture of the **6 Operational Pillars**.

## 🏗️ The 6 Architectural Pillars

### Pillar I: The Floating Orb (Minimalist UI)

A *Spotify Mini/Discord PIP* style widget written in PyQt6. Fully *headless*, it responds to voice commands (using local `faster-whisper`) and direct touch interactions without hogging the desktop. It blinks in different colors depending on its state (listening, warning, execution).

### Pillar II: Nubular Brain (Dynamic Prompt Engineering)

The "CEO" of Cerberus. It intercepts your requests and injects the "Total Workspace Context" toward `gemini-2.5-flash`. This process internally generates **Expert Agents** on the fly, giving the AI a hyper-focused personality (UI Engineer, Database Specialist) before tackling the subtask.

### Pillar III: The Fishbowl (Captive Linux Sandbox)

All code generated or downloaded by the Brain is first executed in isolation within a captive environment (WSL Ubuntu). The AI has the freedom to fail, explore, and assemble its own prototype there, without touching the Windows Host. Only when the code passes the Syntax Test does it acquire the `SAFE_CERTIFIED` flag.

### Pillar IV: The Armored Wall (Zero-Trust Host Router)

Only packaged and secure code crosses over to the Host network (Windows). Even so, a strict scanner checks for lethal disk or network intentions (`os.remove`, `rmtree`, `requests`). If it detects a sensitive vector, it halts execution, the Orb flashes amber, and Cerberus requests approval from the human Commander.

### Pillar V: Autonomous Immune System

If a piece of code manages to inject instability or turns out to be obfuscated/malicious, Cerberus intercepts the crash, requests a forensic autopsy from the cloud, extracts the error as a 'vector', stores it in its Vault, and self-applies a Blacklisting filter so it never happens again.

### Pillar VI: The Gauntlet (Persistent DNA Memory)

Artificial intelligences are born amnesic in every execution. Cerberus Gate includes a `user_dna.json` ledger at its core. It detects reprimands, repetitive instructions, or implicit preferences, silently condenses them, and "tattoos" them into its DNA to use them on every boot, for life.

## 🚀 Installation and Deployment

```bash
# 1. Clone the Cerberus Gate core
git clone https://github.com/Cancercervero/Cerberus-Gate.git

# 2. Enter the base router
cd "Cerberus-Gate" # Or your cloned directory

# 3. Initialize environment and launch the Orb
./lanzar_naranja.bat
```

> [!NOTE]
> You must have **WSL2** installed on your Windows machine for the quarantine module (The Fishbowl), and set the `GEMINI_API_KEY` in your `.env` file.

---
<div align="center">
  <p>Built by <b>CC IA Consultores</b></p>
  <p><i>The Future is Autonomous, The Execution is Human.</i></p>
</div>

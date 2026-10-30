# AI Voice Calling Agent — LiveKit WebRTC & Python Edition

A production-grade, ultra-low-latency real-time conversational voice agent platform built with **LiveKit WebRTC, Python, Silero VAD, Sarvam AI, and ElevenLabs Turbo v2.5**.

---

## 🌟 Why LiveKit WebRTC Instead of WebSockets?

1. **True Real-Time WebRTC Media Streaming (UDP / Opus):**
   * No TCP packet loss audio stutter or buffering delay.
   * End-to-end transport latency is **sub-50ms**.
2. **Native Deep Learning Voice Activity Detection (Silero VAD):**
   * Zero noise false-triggers (filters breathing, typing, and background static).
3. **Instant Sub-20ms Barge-In Interruption:**
   * When human speaks, LiveKit automatically cuts the audio output track instantly.
4. **Tool / Function Calling Built-in:**
   * The agent autonomously invokes `book_demo` and `schedule_callback` tools.
5. **Telephony SIP Trunking (LiveKit SIP + Exotel):**
   * Connects to phone networks through LiveKit SIP without modifying any AI agent logic.

---

## 🚀 Quick Start (Windows)

### Step 1: Run Local LiveKit WebRTC Server
In a terminal or Docker:
```powershell
docker run --rm -it -p 7880:7880 -p 7881:7881 -p 7882:7882/udp livekit/livekit-server --dev
```

### Step 2: Start the Python Platform
```powershell
cd voice-agent-python
.\start.ps1
```
Choose **[3]** to launch both the **FastAPI Token Server (Port 8000)** and the **LiveKit WebRTC Voice Agent Worker**.

---

## 🎙️ Testing the Voice Agent

1. Open the [LiveKit Agents Web Playground](https://agents-playground.livekit.io/) in your browser.
2. Enter your credentials:
   * **LiveKit URL:** `ws://localhost:7880`
   * **API Key:** `devkey`
   * **API Secret:** `secret`
3. Click **Connect** and talk directly with your AI Sales Executive!

import sys
import os
import subprocess
import time
import signal

def main():
    python_exe = sys.executable
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    print("=" * 60)
    print(" 🚀 Starting Full Voice Agent Platform (FastAPI + LiveKit Agent)")
    print("=" * 60)
    print(f"📁 Project Root : {project_root}")
    print(f"🐍 Python Exec  : {python_exe}")
    print("=" * 60)

    # 1. Start FastAPI in a background subprocess
    print("📡 [1/2] Starting FastAPI Server on http://localhost:8000 ...")
    fastapi_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=project_root
    )

    time.sleep(1.5)
    print("📖 Swagger API Docs available at: http://localhost:8000/docs")
    print("🎙️ [2/2] Starting LiveKit Agent Worker...")

    agent_proc = None
    try:
        # 2. Start LiveKit Agent Worker
        agent_proc = subprocess.Popen(
            [python_exe, "app/livekit_agent/agent.py", "dev"],
            cwd=project_root
        )

        print("\n✨ Both servers running! Press Ctrl+C to stop both.\n")
        while True:
            if fastapi_proc.poll() is not None:
                print("⚠️ FastAPI server stopped unexpectedly.")
                break
            if agent_proc.poll() is not None:
                print("⚠️ LiveKit Agent worker stopped unexpectedly.")
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers gracefully (waiting for worker cleanup)...")
    finally:
        processes = [("LiveKit Agent", agent_proc), ("FastAPI", fastapi_proc)]
        for name, proc in processes:
            if proc and proc.poll() is None:
                try:
                    # Give process time to handle the console Ctrl+C event cleanly
                    proc.wait(timeout=3)
                except (subprocess.TimeoutExpired, Exception):
                    try:
                        proc.terminate()
                        proc.wait(timeout=2)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass

        print("✅ All processes stopped cleanly.")

if __name__ == "__main__":
    main()

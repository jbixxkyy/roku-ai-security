import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import STORAGE_STATE, CAMERAS_URL, LEAVES_API


def get_camera_list():
    if not STORAGE_STATE.exists():
        raise FileNotFoundError(f"No storage_state.json - run login.py in {STORAGE_STATE.parent}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=str(STORAGE_STATE))
        page = ctx.new_page()
        leaves = {}
        def on_response(resp):
            if LEAVES_API in resp.url and "/streams" not in resp.url:
                try:
                    leaves["data"] = resp.json()
                except Exception:
                    pass
        page.on("response", on_response)
        page.goto(CAMERAS_URL, wait_until="domcontentloaded")
        for _ in range(30):
            if leaves.get("data"):
                break
            time.sleep(2)
        browser.close()
    if not leaves.get("data"):
        raise RuntimeError("Could not fetch camera list - session may be expired")
    cameras = []
    for leaf in leaves["data"]:
        if leaf.get("type") == "device":
            cameras.append({
                "id": leaf["id"],
                "name": leaf["name"],
                "online": leaf.get("state", {}).get("online", {}).get("online", False),
                "local_ip": leaf.get("device", {}).get("localIp"),
                "model": leaf.get("device", {}).get("model"),
            })
    return cameras


def capture_frame():
    if not STORAGE_STATE.exists():
        raise FileNotFoundError(f"No storage_state.json - run login.py in {STORAGE_STATE.parent}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            storage_state=str(STORAGE_STATE),
            viewport={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()
        page.goto(CAMERAS_URL, wait_until="domcontentloaded")
        video = None
        deadline = time.time() + 60
        while time.time() < deadline and not video:
            vids = page.locator("video")
            for i in range(vids.count()):
                v = vids.nth(i)
                try:
                    if v.evaluate("el => el.videoWidth") > 0:
                        video = v
                        break
                except Exception:
                    pass
            if not video:
                time.sleep(2)
        if not video:
            browser.close()
            return None
        tmp_path = Path(__file__).parent / "_tmp_frame.png"
        video.screenshot(path=str(tmp_path))
        browser.close()
        return tmp_path.read_bytes()

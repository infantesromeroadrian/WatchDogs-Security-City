"""Video pipeline end-to-end (offline): upload -> serve -> frame capture -> batch analysis -> PDF."""

import base64
import shutil
import subprocess

import cv2
import pytest
from PIL import Image, ImageDraw
from stub_llm import StubLLM

from src.backend import config

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@pytest.fixture(scope="module")
def video_path(tmp_path_factory):
    """Synthetic 6 s video made of three generated stills (no third-party imagery)."""
    d = tmp_path_factory.mktemp("video")
    for i, color in enumerate([(200, 60, 60), (60, 200, 60), (60, 60, 200)]):
        img = Image.new("RGB", (320, 240), color)
        ImageDraw.Draw(img).text((20, 100), f"FRAME {i + 1}", fill=(255, 255, 255))
        img.save(d / f"s{i}.png")
    out = d / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1/2", "-i", str(d / "s%d.png"),
         "-vf", "fps=10,format=yuv420p", "-c:v", "libx264", str(out)],
        check=True,
    )
    return out


@pytest.fixture
def client(monkeypatch):
    from src.backend.app import app

    app.config["TESTING"] = True
    with StubLLM(content='{"summary": "stub", "has_text": false}') as stub:
        monkeypatch.setattr(config, "LLM_PROVIDER", "custom")
        monkeypatch.setattr(config, "OPENAI_BASE_URL", stub.url)
        monkeypatch.setattr(config, "OPENAI_API_KEY", "test")
        monkeypatch.setattr(config, "OPENAI_MODEL", "stub")
        # analysis_routes builds its coordinator at import time; rebuild it on the stub
        from src.backend.agents.coordinator import CoordinatorAgent
        from src.backend.api import analysis_routes

        monkeypatch.setattr(analysis_routes, "coordinator", CoordinatorAgent())
        with app.test_client() as c:
            from conftest import login

            login(c)
            yield c


def _capture_frames(path, n=3):
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((i + 0.5) * total / n))
        ok, frame = cap.read()
        assert ok
        _, buf = cv2.imencode(".jpg", frame)
        frames.append("data:image/jpeg;base64," + base64.b64encode(buf).decode())
    cap.release()
    return frames


def test_upload_serve_capture_batch_pdf(client, video_path):
    with open(video_path, "rb") as fh:
        r = client.post("/api/upload-video", data={"video": (fh, "clip.mp4")},
                        content_type="multipart/form-data")
    assert r.status_code == 200, r.get_json()
    filename = r.get_json()["filename"]

    served = client.get(f"/api/video/{filename}")
    assert served.status_code == 200
    assert served.mimetype.startswith("video/")

    frames = _capture_frames(video_path)
    payload = {"frames": [{"frame": f, "description": f"Frame {i + 1}"} for i, f in enumerate(frames)]}
    for accumulate in (False, True):  # parallel graph and sequential-with-context paths
        r = client.post("/api/analyze-batch", json={**payload, "enable_context_accumulation": accumulate})
        assert r.status_code == 200, r.get_json()
        results = r.get_json()["results"]
        assert results["frames_analyzed"] == 3
        assert len(results["json"]["individual_results"]) == 3
        assert results["text"]

    single = client.post("/api/analyze-frame", json={"frame": frames[0]})
    assert single.status_code == 200
    analysis = single.get_json()["results"]["json"]
    pdf = client.post("/api/generate-pdf-report", json={"analysis_results": analysis["agents"]})
    assert pdf.status_code == 200, pdf.get_json()
    assert pdf.data.startswith(b"%PDF")

    meta = client.post("/api/extract-metadata", json={"frame": frames[0]})
    assert meta.status_code == 200
    ev = client.post("/api/generate-evidence-package",
                     json={"frame": frames[0], "analysis_results": analysis})
    assert ev.status_code == 200

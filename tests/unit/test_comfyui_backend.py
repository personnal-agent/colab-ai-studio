"""Tests unitaires pour ComfyUIBackend (Step 4 Issue #2).

Vérifie :
1. Injection des paramètres utilisateur dans le template de workflow selon les bindings.
2. Soumission de prompt POST /prompt et récupération de prompt_id.
3. Vérification d'état via GET /history/{prompt_id}.
4. Interruption de l'exécution en cours POST /interrupt.
"""

from __future__ import annotations

import httpx

from app.local_worker.backends.comfyui import ComfyUIBackend


def test_inject_parameters_into_workflow_template():
    backend = ComfyUIBackend(base_url="http://mock-comfyui")
    template = {
        "3": {"inputs": {"seed": 100, "steps": 20}, "class_type": "KSampler"},
        "6": {"inputs": {"text": "default prompt"}, "class_type": "CLIPTextEncode"},
    }
    bindings = {
        "prompt": ["6", "inputs", "text"],
        "seed": ["3", "inputs", "seed"],
    }
    params = {
        "prompt": "Cinematic misty forest at sunrise",
        "seed": 99999,
    }

    modified = backend.inject_parameters(template, bindings, params)
    assert modified["6"]["inputs"]["text"] == "Cinematic misty forest at sunrise"
    assert modified["3"]["inputs"]["seed"] == 99999
    # Le template original reste intact
    assert template["6"]["inputs"]["text"] == "default prompt"


async def test_queue_prompt_and_history():
    def mock_handler(request: httpx.Request):
        if request.url.path == "/prompt" and request.method == "POST":
            return httpx.Response(200, json={"prompt_id": "prompt_abc123"})
        if request.url.path == "/history/prompt_abc123" and request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "prompt_abc123": {
                        "outputs": {
                            "9": {
                                "images": [
                                    {"filename": "out_01.png", "subfolder": "", "type": "output"}
                                ]
                            }
                        },
                        "status": {"completed": True},
                    }
                },
            )
        if request.url.path == "/interrupt" and request.method == "POST":
            return httpx.Response(200, json={"status": "interrupted"})
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    backend = ComfyUIBackend(base_url="http://mock-comfyui", client=client)

    prompt_id = await backend.queue_prompt({"1": {}})
    assert prompt_id == "prompt_abc123"

    history = await backend.get_history("prompt_abc123")
    assert history is not None
    assert "outputs" in history

    interrupted = await backend.interrupt()
    assert interrupted is True

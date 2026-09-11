"""Explicit role routing and local model availability; never auto-pull or substitute."""
import httpx


def canonical(name):
    return name if ":" in name.rsplit("/", 1)[-1] else name + ":latest"


def install_command(model):
    # Model names are validated by Config; this string is advice, never executed.
    return "ollama pull " + model


async def inventory(config, transport=None):
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False, timeout=5, transport=transport) as client:
        async with client.stream("GET", config.endpoint + "/api/tags") as response:
            response.raise_for_status()
            raw = b""
            async for chunk in response.aiter_bytes():
                raw += chunk
                if len(raw) > 1_000_000:
                    raise ValueError("Ollama model inventory exceeded limit")
    import json
    data = json.loads(raw)
    return {canonical(m["name"]): m for m in data["models"]}


async def model_status(config, transport=None):
    installed = await inventory(config, transport)
    models = config.roles or {"general": config.model}
    return [{"role": role, "model": model, "installed": canonical(model) in installed,
             "install_command": None if canonical(model) in installed else install_command(model)}
            for role, model in models.items()]

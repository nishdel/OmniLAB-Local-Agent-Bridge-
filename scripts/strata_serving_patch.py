"""Reproduce the qualification-only patch; never edit an existing source tree.

Upstream: Niko1221/Strata, MIT; see docs/qualification/STRATA-LICENSE.txt.
No downloads, engine changes, configuration changes, or model loading.
"""

import argparse
import difflib
import hashlib
import json
import shutil
from pathlib import Path

BASE_COMMIT = "7695859aa13afb248bdb4d36f9b2e95707db079d"
BASE_SHA256 = "55ee9d1160f0da457cabe6f9dfea9884296b6d70fd3d14abd4ed42e6f79dd72b"


def patch_server(original: bytes) -> bytes:
    if hashlib.sha256(original).hexdigest() != BASE_SHA256:
        raise ValueError("Serving source differs from the reviewed upstream base")
    text = original.decode("utf-8")
    text = text.replace(
        "class EngineNonFinite(ValueError):",
        'class GenerationCancelled(ValueError):\n'
        '    """An incomplete response must not be encoded as a successful stop."""\n\n\n'
        "class EngineNonFinite(ValueError):",
        1,
    )
    text = text.replace(
        "    silence_s = ENGINE_SILENCE_S",
        "    # LAB qualification: a process owns one initial native-engine start only.\n"
        "    _lab_start_lock = threading.Lock()\n"
        "    _lab_start_claimed = False\n\n"
        "    silence_s = ENGINE_SILENCE_S",
        1,
    )
    text = text.replace(
        "        self.spawn = (exe, list(args), cwd, log, env, False, cpus)",
        "        if lazy:\n"
        "            raise EngineDied(\"LAB qualification forbids lazy engine starts\")\n"
        "        with StrataEngine._lab_start_lock:\n"
        "            if StrataEngine._lab_start_claimed:\n"
        "                raise EngineDied(\"LAB qualification engine start already consumed; automatic restart disabled\")\n"
        "            StrataEngine._lab_start_claimed = True\n"
        "        self.spawn = (exe, list(args), cwd, log, env, False, cpus)",
        1,
    )
    start = text.index("    def restart(self, tries: int = 3):")
    end = text.index("    def _parse_done(self, line):", start)
    text = text[:start] + (
        "    def restart(self, tries: int = 3):\n"
        "        raise EngineDied(\"LAB qualification: automatic restart disabled; supervisor decision required\")\n\n"
    ) + text[end:]
    start = text.index("    def ensure_loaded(self):")
    end = text.index("    vram_wait_s =", start)
    text = text[:start] + (
        "    def ensure_loaded(self):\n"
        "        # A failed/unloaded engine cannot be resurrected by requests or controls.\n"
        "        if self.loaded() and not self._vision_down():\n"
        "            return\n"
        "        raise EngineDied(\"LAB qualification engine unavailable; automatic restart disabled\")\n\n"
    ) + text[end:]
    text = "".join(
        line for line in text.splitlines(keepends=True)
        if not any(key in line for key in (
            "nf_retried = False", "segments_before = len(segments)", "nonfinite = False",
        ))
    )
    text = text.replace(
        "                        except EngineNonFinite:\n                            nonfinite = True",
        "                        except EngineNonFinite:\n"
        "                            finish = \"error\"\n"
        "                            raise  # Including partial output: no replay or successful completion.",
        1,
    )
    # DONE may arrive while STOP drains after an EOS token or client cancellation.
    text = text.replace(
        '                    if line is None or line.startswith("ERR"):\n                        break\n'
        '                    if line.startswith("DONE"):\n                        self._parse_done(line)\n                        break',
        '                    if line is None:\n'
        '                        raise EngineDied("the engine died while draining the response")\n'
        '                    if line.startswith("ERR"):\n'
        '                        raise ValueError(line[4:].strip())\n'
        '                    if line.startswith("DONE"):\n'
        '                        self._parse_done(line)\n'
        '                        if self.last.get("finish") == "nonfinite":\n'
        '                            raise EngineNonFinite("the engine logits became non-finite during STOP/drain")\n'
        '                        break',
        1,
    )
    text = text.replace(
        '                            except EngineSilent as e:   # #481: the STOP',
        '                            except ValueError:\n'
        '                                finish = "error"\n'
        '                                raise\n'
        '                            except EngineSilent as e:   # #481: the STOP',
        1,
    )
    text = text.replace(
        '                            segment_done = getattr(self.engine, "last", None)',
        '                            except EngineDied:\n'
        '                                finish = "error"\n'
        '                                raise\n'
        '                            segment_done = getattr(self.engine, "last", None)',
        1,
    )
    start = text.index("                        if nonfinite and not cancel.is_set():")
    end = text.index("                        if recover_prompt is not None", start)
    text = text[:start] + text[end:]
    text = text.replace('hasattr(self.engine, "restart")', "False")
    text = text.replace('hasattr(svc.engine, "restart")', "False")
    text = text.replace("the next request restarts it", "automatic restart disabled")
    text = text.replace("The next request starts the engine again.", "Automatic restart disabled.")
    text = text.replace("the next request loads it again", "automatic reload disabled")
    text = text.replace(
        'str(e) + "; the next request starts "\n                                                     "the engine again"',
        'str(e) + "; automatic restart disabled"',
    )
    text = text.replace(
        'request reads the prompt from token 0.  Service.run sends a request that had produced nothing yet once more, and\n'
        '    ends one that had started (as "length").',
        'request reads the prompt from token 0.  LAB qualification rejects the first failure, including partial output.',
    )
    text = text.replace(
        '                    yield "done", {"finish": "cancel", "completion_tokens": 0, "reused": 0, "timings": None,\n'
        '                                   "reasoning_tokens": 0, "reasoning_recoveries": 0}\n'
        '                    return',
        '                    raise GenerationCancelled("generation cancelled while queued; no response completed")',
        1,
    )
    text = text.replace(
        '        for ev in cut(parser.finish(finish)):',
        '        if finish == "cancel" or cancel.is_set():\n'
        '            raise GenerationCancelled("generation cancelled; incomplete response discarded")\n'
        '        for ev in cut(parser.finish(finish)):',
        1,
    )
    # Non-streamed handlers report cancellation as a service error, not bad input.
    # Streaming handlers already turn ValueError into protocol-specific errors.
    text = text.replace(
        "except EngineNonFinite as e:", "except (EngineNonFinite, GenerationCancelled) as e:",
    )
    return text.encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    destination = args.destination.resolve()
    if destination.exists() or destination.is_relative_to(source):
        parser.error("Destination must be absent and outside the upstream source")
    original = (source / "serve/server.py").read_bytes()
    patched = patch_server(original)
    # Copy ordinary files, never share mutable inodes with the original source.
    if any(p.is_symlink() for p in source.rglob("*")):
        parser.error("Source tree contains symbolic links")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
    (destination / "serve/server.py").write_bytes(patched)
    delta = "".join(difflib.unified_diff(
        original.decode().splitlines(keepends=True), patched.decode().splitlines(keepends=True),
        fromfile="a/serve/server.py", tofile="b/serve/server.py",
    )).encode()
    args.evidence.mkdir(parents=True, exist_ok=True)
    (args.evidence / "strata-serving.patch").write_bytes(delta)
    record = {
        "runtime_label": "Strata 0.1.43 engine with LAB-specific serving patch",
        "upstream_base_commit": BASE_COMMIT,
        "upstream_server_sha256": BASE_SHA256,
        "patch_sha256": hashlib.sha256(delta).hexdigest(),
        "patched_server_sha256": hashlib.sha256(patched).hexdigest(),
        "changed_files": ["serve/server.py"],
    }
    (args.evidence / "strata-serving-provenance.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n",
    )
    print(json.dumps(record))


if __name__ == "__main__":
    main()

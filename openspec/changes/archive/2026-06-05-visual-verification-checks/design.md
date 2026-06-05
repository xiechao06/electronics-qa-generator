## Context

The pipeline renders schematic PNGs but has no check that images are correct.
Ollama running `deepseek-vl2-tiny` locally provides free, offline vision reasoning
sufficient for "does this schematic match the topology" and "are labels readable".

## Goals / Non-Goals

**Goals:**
- Add `complete_vision()` to the existing provider with base64 image encoding.
- Add 2 visual checks using the same CheckResult/Verdict interface.
- Opt-in via `--visual` flag; requires `--render` to have produced the PNG.

**Non-Goals:**
- Cloud VLM providers (saved in backlog for future: Volcengine `doubao-seed-1-6-vision`).
- Bounding-box analysis or pixel-level checks — VLM reasoning only.

## Decisions

### Decision: Base64 inline images (not multipart)
Send the PNG as a `data:image/png;base64,...` URL in the `image_url` content part
of the chat completions request. This is the standard OpenAI vision format, which
Ollama's `/v1/chat/completions` endpoint supports.
- **Why:** Simple, no multipart encoding, works with existing urllib JSON POST.
- **Alternative considered:** Ollama's native `/api/generate` with `images` field.
  Rejected — non-standard; the OpenAI-compatible endpoint is more portable.

### Decision: VLM unavailability → PASS
If Ollama is not running or the model is not pulled, visual checks return PASS.
They are advisory and should never block the pipeline.
- **Why:** Same pattern as LLM checks and humanization — opt-in, best-effort.

### Decision: Separate `VISION_CHECKS` registry in `visual_checks.py`
Same structure as `ITEM_CHECKS` and `LLM_CHECKS`. Integrated into
`ValidationReport.from_items()` via a `vision_provider` keyword argument.

## Risks / Trade-offs

- **VLM hallucination** → Returns WARN, never FAIL. False warnings are noise, not
  blockers.
- **VLM doesn't understand circuit schematics** → Prompt engineering: include
  component symbol descriptions in the system prompt so the VLM knows what a
  zigzag resistor or parallel-plate capacitor looks like.
- **Latency** → Local Ollama model should return in ~1-3s per image on modest
  hardware.

## Migration Plan

1. Add `complete_vision()` to `llm/provider.py`.
2. Add `validation/visual_checks.py` with 2 checks + `VISUAL_CHECKS`.
3. Wire into `ValidationReport.from_items()` and CLI handlers.
4. Add tests with fake vision provider.
- **Rollback:** Remove `--visual` flag.

## Open Questions

- `deepseek-vl2-tiny` model name in Ollama — verify exact name (`ollama list`).
  May be `deepseek-vl2-tiny` or `deepseek-vl2-tiny:latest`.

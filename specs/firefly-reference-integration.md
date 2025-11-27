# Plan: Integrate Best Features from python-firefly Reference

## Task Description

Analyze the `reference/python-firefly-main` codebase and integrate its best MCP and CLI capabilities into the existing `apps/firefly_mcp` and `apps/firefly_sdk` implementations. The reference implementation has several excellent features that would enhance our current implementation without losing the advanced features we already have (6 MCP tools vs their 1).

## Objective

Enhance the Firefly MCP server and SDK with features from the reference implementation including:
- Additional API parameters (`aspect_ratio`, `seed`, `style`, `structure`, `prompt_biasing_locale_code`)
- CLI improvements (mock testing, image download, terminal display, verbose logging)
- Better packaging and installation patterns
- Test infrastructure with mock support

## Problem Statement

Our current implementation has more API coverage (6 tools) but lacks several developer-friendly features from the reference:
1. No mock testing support - can't test without API credentials
2. No image download or terminal display capabilities
3. Missing API parameters: `aspect_ratio`, `seed`, `structure`, `style` objects, `prompt_biasing_locale_code`
4. No verbose logging for debugging
5. CLI uses Click instead of more modern Typer

## Solution Approach

Take a "best of both" approach:
- **Keep**: Our 6-tool MCP coverage, async httpx client, Pydantic models, retry logic
- **Add**: Reference's CLI features, missing API parameters, mock testing, better packaging

## Relevant Files

### Files to Modify

- `apps/firefly_mcp/server.py` - Add missing API parameters to `generate_image` tool
- `apps/firefly_mcp/pyproject.toml` - Add optional dependencies, uvx entry points
- `apps/firefly_sdk/src/firefly_sdk/client.py` - Add missing API parameters
- `apps/firefly_sdk/src/firefly_sdk/models.py` - Add new model fields
- `apps/firefly_sdk/src/firefly_sdk/cli.py` - Replace Click with Typer, add features
- `apps/firefly_sdk/pyproject.toml` - Add Typer, optional deps, update entry points

### New Files

- `apps/firefly_sdk/src/firefly_sdk/mocks.py` - Mock infrastructure for testing
- `apps/firefly_sdk/tests/test_cli.py` - CLI tests with mock support
- `apps/firefly_mcp/tests/test_server.py` - MCP server tests

### Reference Files (Read-only)

- `reference/python-firefly-main/firefly/cli.py` - CLI patterns to adopt
- `reference/python-firefly-main/firefly/mcp/server.py` - MCP patterns
- `reference/python-firefly-main/tests/test_cli.py` - Test patterns

## Implementation Phases

### Phase 1: Foundation - Add Missing API Parameters

Add parameters that exist in the Firefly API but are missing from our implementation:
- `aspect_ratio` (alternative to width/height)
- `seed` (deterministic generation)
- `style` (complex style objects with presets, strength, imageReference)
- `structure` (structure reference objects)
- `prompt_biasing_locale_code` (locale-aware prompts)
- `output_format` (jpeg/png)

### Phase 2: CLI Enhancement

Modernize CLI with Typer and add developer-friendly features:
- Switch from Click to Typer for better UX
- Add `--use-mocks` flag for testing without credentials
- Add `--download` to save generated images
- Add `--show-images` for terminal display (imgcat)
- Add `--verbose` for request debugging
- Add `--format json` for machine-readable output

### Phase 3: Testing Infrastructure

Add mock testing support for both CLI and MCP:
- Create mock responses module
- Add CLI tests using Typer's CliRunner
- Add MCP server tests

## Step by Step Tasks

### 1. Add Missing API Parameters to Models

Update `apps/firefly_sdk/src/firefly_sdk/models.py`:

- Add `seed: Optional[int]` to `GenerateImageRequest`
- Add `aspect_ratio: Optional[str]` (e.g., "1:1", "16:9", "4:3")
- Add `output_format: Optional[Literal["jpeg", "png"]]`
- Add `prompt_biasing_locale_code: Optional[str]`
- Add `style: Optional[dict]` for complex style objects
- Add `structure: Optional[dict]` for structure reference

### 2. Update Firefly SDK Client

Update `apps/firefly_sdk/src/firefly_sdk/client.py`:

- Update `generate_image()` to handle new parameters
- Add `seed` to request body when provided
- Add `aspectRatio` parameter (alternative to size)
- Add `outputFormat` parameter
- Add `promptBiasingLocaleCode` parameter
- Handle `style` dict directly (for presets, imageReference, strength)
- Handle `structure` dict directly

### 3. Update MCP Server generate_image Tool

Update `apps/firefly_mcp/server.py`:

- Add `seed` parameter to `generate_image` tool
- Add `aspect_ratio` parameter
- Add `output_format` parameter
- Add `prompt_biasing_locale_code` parameter
- Add `style` parameter (JSON dict)
- Add `structure` parameter (JSON dict)
- Update docstrings with new parameters

### 4. Replace Click with Typer in CLI

Update `apps/firefly_sdk/src/firefly_sdk/cli.py`:

- Replace Click imports with Typer
- Convert `@click.group()` to `typer.Typer()`
- Convert `@click.command()` to `@app.command()`
- Convert `@click.option()` to `typer.Option()`
- Convert `@click.argument()` to `typer.Argument()`
- Add `envvar` support for credentials
- Keep Rich console output

### 5. Add Mock Testing Infrastructure

Create `apps/firefly_sdk/src/firefly_sdk/mocks.py`:

```python
import responses
from contextlib import contextmanager

MOCK_IMAGE_URL = "https://example.com/mock-image.png"

@contextmanager
def use_firefly_mocks():
    """Context manager for mocking Firefly API responses."""
    rsps = responses.RequestsMock()
    rsps.start()

    # Mock IMS token endpoint
    rsps.add(
        responses.POST,
        "https://ims-na1.adobelogin.com/ims/token/v3",
        json={"access_token": "mock_token", "expires_in": 3600},
        status=200,
    )

    # Mock generate image endpoint
    rsps.add(
        responses.POST,
        "https://firefly-api.adobe.io/v3/images/generate",
        json={
            "size": {"width": 1024, "height": 1024},
            "outputs": [{"seed": 123456, "image": {"url": MOCK_IMAGE_URL}}],
            "contentClass": "art",
        },
        status=200,
    )

    # Add more mocks for other endpoints...

    try:
        yield rsps
    finally:
        rsps.stop()
        rsps.reset()
```

### 6. Add CLI Feature Flags

Update CLI with new options:

- `--use-mocks` - Enable mock mode for testing
- `--download` - Download image to local file
- `--show-images` - Display in terminal using imgcat
- `--verbose` - Print request/response details
- `--format text|json` - Output format
- `--seed` - Seed for deterministic output
- `--aspect-ratio` - Aspect ratio (e.g., "16:9")
- `--style` - Style JSON string
- `--structure` - Structure JSON string

### 7. Implement Image Download

Add to CLI:

```python
def download_image(url: str, filename: Optional[str] = None) -> str:
    """Download image from URL to local file."""
    import httpx
    from urllib.parse import urlparse

    response = httpx.get(url)
    response.raise_for_status()

    if not filename:
        filename = os.path.basename(urlparse(url).path)

    with open(filename, "wb") as f:
        f.write(response.content)

    return filename
```

### 8. Implement Terminal Image Display

Add to CLI:

```python
def show_image_in_terminal(url_or_path: str):
    """Display image in terminal using imgcat."""
    import subprocess
    try:
        if url_or_path.startswith("http"):
            subprocess.run(["imgcat", "--url", url_or_path], check=True)
        else:
            subprocess.run(["imgcat", url_or_path], check=True)
    except FileNotFoundError:
        typer.secho("[warn] imgcat not found. Install with: brew install imgcat", fg="yellow", err=True)
    except subprocess.CalledProcessError as e:
        typer.secho(f"[warn] Could not display image: {e}", fg="yellow", err=True)
```

### 9. Update pyproject.toml Files

Update `apps/firefly_sdk/pyproject.toml`:

```toml
dependencies = [
    "httpx>=0.27.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
    "rich>=13.7.0",
    "typer>=0.12.3",  # Replace click
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "responses>=0.25.7",  # For mocking
    "ruff>=0.3.0",
]

[project.scripts]
firefly = "firefly_sdk.cli:app"
```

Update `apps/firefly_mcp/pyproject.toml`:

```toml
[project.scripts]
mcp-server = "server:mcp.run"
```

### 10. Write CLI Tests

Create `apps/firefly_sdk/tests/test_cli.py`:

- Test generate command with mocks
- Test download functionality
- Test JSON output format
- Test verbose mode
- Test missing credentials error
- Test invalid parameters

### 11. Validate Implementation

Run validation commands to ensure everything works:

- `cd apps/firefly_sdk && uv sync`
- `uv run firefly --help`
- `uv run firefly generate "test" --use-mocks`
- `uv run pytest tests/`
- `cd apps/firefly_mcp && uv sync`
- `uv run mcp dev server.py`

## Testing Strategy

### Unit Tests
- Mock all external API calls using `responses` library
- Test each CLI command with mock mode
- Test parameter validation
- Test error handling for auth failures, API errors

### Integration Tests
- Test MCP server tool execution with mocks
- Test CLI end-to-end with `--use-mocks`

### Edge Cases
- Missing credentials
- Invalid JSON for style/structure
- Invalid aspect ratios
- Network errors
- Rate limiting responses

## Acceptance Criteria

1. `generate_image` MCP tool supports: `seed`, `aspect_ratio`, `style`, `structure`, `output_format`, `prompt_biasing_locale_code`
2. CLI uses Typer instead of Click
3. CLI supports `--use-mocks` for testing without credentials
4. CLI supports `--download` to save images locally
5. CLI supports `--show-images` for terminal display
6. CLI supports `--verbose` for debugging
7. All existing tests pass
8. New CLI tests pass with mock mode
9. Documentation updated in README files

## Validation Commands

Execute these commands to validate the task is complete:

```bash
# Verify SDK installs and CLI works
cd apps/firefly_sdk && uv sync
uv run firefly --help
uv run firefly generate "test prompt" --use-mocks --verbose

# Verify MCP server
cd apps/firefly_mcp && uv sync
uv run python -c "from server import mcp; print('MCP server OK')"

# Run tests
cd apps/firefly_sdk && uv run pytest tests/ -v

# Verify new parameters in MCP
uv run python -c "from server import generate_image; help(generate_image)"
```

## Notes

### Dependencies to Add

```bash
# In firefly_sdk
uv add typer
uv add --dev responses

# Remove click if not used elsewhere
uv remove click
```

### Breaking Changes

- CLI syntax will change from Click to Typer (slightly different option handling)
- Users may need to update scripts using the old CLI

### Future Enhancements

- Add `fill` and `expand` to MCP server from reference
- Add upload image support (base64 → uploadId)
- Add batch processing CLI command
- Support for structure/style image references via upload

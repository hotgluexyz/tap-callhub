# tap-callhub

`tap-callhub` is a Singer tap for [CallHub](https://callhub.io/), a calling and texting platform for campaigns and outreach.

Built with the [Hotglue Singer SDK](https://github.com/hotgluexyz/HotglueSingerSDK) for Singer Taps.

## Installation

```bash
pip install tap-callhub
```

Or install directly from the repository:

```bash
pip install git+https://github.com/hotgluexyz/tap-callhub.git
```

## Configuration

### Accepted Config Options

| Setting         | Required | Description                                                                 |
|-----------------|----------|-----------------------------------------------------------------------------|
| `api_token`     | Yes      | CallHub API token from the account settings UI                              |
| `api_base_url`  | Yes      | CallHub API base URL shown alongside the API token in the UI                |

Example `config.json`:

```json
{
  "api_token": "your_api_token",
  "api_base_url": "https://api-na1.callhub.io"
}
```

A full list of supported settings and capabilities for this tap is available by running:

```bash
tap-callhub --about
```

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Source Authentication and Authorization

This tap uses API token authentication. Generate an API token and note the API base URL from the CallHub account settings UI. Requests send the token in the `Authorization` header as `Token <api_token>`.

## Supported Streams

| Stream     | Replication Key | Primary Key | Description                                                                 |
|------------|-----------------|-------------|-----------------------------------------------------------------------------|
| `contacts` | —               | `id`        | CallHub contacts, including dynamically discovered custom field properties |

Custom field definitions are fetched from `/v1/custom_fields/` at discover time. During sync, values from the API's `custom_fields` payload are flattened onto the contact record using the readable custom field names. Custom fields whose names match a standard contact property are skipped, since CallHub treats them as equivalent to the built-in field.

## Usage

You can easily run `tap-callhub` by itself or in a pipeline.

### Executing the Tap Directly

```bash
tap-callhub --version
tap-callhub --help
tap-callhub --config CONFIG --discover > ./catalog.json
tap-callhub --config CONFIG --catalog CATALOG > ./data.singer
```

## Developer Resources

### Initialize your Development Environment

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install ruff pytest
```

### Create and Run Tests

Create tests within the `tap_callhub/tests` subfolder and then run:

```bash
.venv/bin/pytest
```

You can also test the `tap-callhub` CLI interface directly:

```bash
.venv/bin/tap-callhub --help
```

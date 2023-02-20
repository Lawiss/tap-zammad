# tap-zammad

`tap-zammad` is a Singer tap for Zammad.
This tap allows to extract data from Zammad API.
Currently, this tap supports extraction of Tickets (with associated tags), Groups, Organizations and Users data.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.



## Installation

Install from PyPi:

```bash
pipx install tap-zammad
```


Install from GitHub:

```bash
pipx install git+https://github.com/entropeak/tap-zammad.git@main
```


## Configuration

### Accepted Config Options

<!--
Developer TODO: Provide a list of config options accepted by the tap.

This section can be created by copy-pasting the CLI output from:

```
tap-zammad --about --format=markdown
```
-->
| Setting             | Required | Default | Description |
|:--------------------|:--------:|:-------:|:------------|
| auth_token          | True     | None    | The token to authenticate against the Zammad API |
| start_date          | False    | None    | The earliest record date to sync |
| api_base_url        | True     | None    | The base url of the Zammad API e.g. `https://example.zammad.com/api/v1/` |
| stream_maps         | False    | None    | Config object for stream maps capability. For more information check out [Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html). |
| stream_map_config   | False    | None    | User-defined config values to be used within map expressions. |
| flattening_enabled  | False    | None    | 'True' to enable schema flattening and automatically expand nested properties. |
| flattening_max_depth| False    | None    | The max depth to flatten schemas. |

A full list of supported settings and capabilities for this
tap is available by running:


```bash
tap-zammad --about
```

To use the incremental mode, you should add the proper plugin capabilities to your `meltano.yml` file.
Example of configuration of `meltano.yml`.

```yaml
    - name: tap-zammad
      namespace: tap_zammad
      pip_url: tap-zammad #You can use here a github link
      executable: tap-zammad
      capabilities:
        - state
        - catalog
        - discover
        - about
        - stream-maps
      config:
        auth_token:
        api_base_url:
        start_date: "2022-12-01"
      select:
        - "*.*"
      metadata:
        tickets:
          replication-method: INCREMENTAL
          replication-key: updated_at
        users:
          replication-method: INCREMENTAL
          replication-key: updated_at
        groups:
          replication-method: FULL_TABLE
```

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Source Authentication and Authorization

Zammad API requires to authenticate using an API token. To create an API access token allowing access to your Zammad instance, go to your [Zammad Profile page](https://user-docs.zammad.org/en/latest/extras/profile-and-settings.html#profile-settings) by clicking on your profile photo in the bottom left corner of the Zammad UI. Then click on "access token" and [generate a new access token](https://user-docs.zammad.org/en/latest/extras/profile-and-settings.html#user-profile-settings) dedicated to this tap. 

## Usage

You can easily run `tap-zammad` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-zammad --version
tap-zammad --help
tap-zammad --config CONFIG --discover > ./catalog.json
```

## Developer Resources

Follow these instructions to contribute to this project.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_zammad/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-zammad` CLI interface directly using `poetry run`:

```bash
poetry run tap-zammad --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

<!--
Developer TODO:
Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any "TODO" items listed in
the file.
-->

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-zammad
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-zammad --version
# OR run a test `elt` pipeline:
meltano elt tap-zammad target-jsonl
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to
develop your own taps and targets.

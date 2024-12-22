A simple script that counts SR findings.

## Requirements

[PyGithub](https://pypi.org/project/PyGithub/)

```bash
pip install --user pygithub
```

## Configuration

You will need to generate a personal access token that can access private repositories. [GitHub docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).

Check the "repo" option: full control of private repositories.

Also the SR github username will need to be provided.

Add these in [`config.py`](./config.py).

## Running

CLI version:

```bash
python3 count.py
```

GUI version:

```bash
python3 count_GUI.py
```

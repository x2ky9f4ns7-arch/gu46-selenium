# Gu-46 Selenium Automation

Automates the Gu-46 list page workflow after **manual** login.

## Prerequisites

- Python 3.10+
- Google Chrome + compatible ChromeDriver
- `pip install selenium`

## Usage

1. Put Gu-46 numbers in `numbers.txt` (one per line).
2. Run:

```bash
python main.py
```

3. Log in manually in the opened browser.
4. Press Enter in the terminal to continue.

## Configuration

You can override defaults with environment variables:

- `GU46_DATE_FROM` (default: `2024-01-01`)
- `GU46_DATE_TO` (default: `2024-01-31`)
- `GU46_PAUSE` (default: `2.5` seconds)

Downloads are saved to `./downloads`.

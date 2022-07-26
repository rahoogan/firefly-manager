# Budgets

Setus up a personal financial transaction proccessing pipeline.

```bash
ansible-playbook -i <hostname>, ansible/ansible-install.yml
```

This will:

- Setup an instance of [Firefly](https://github.com/firefly-iii/firefly-iii)
- Setup an instance of [transcat](https://github.com/Hapyr/trans-cat)
- Setup cron jobs to:
    - Parse pdf statements to CSVs and notify on error to discord channel
    - Notify discord channel when parsed pdf's are available to categorise daily
    - Upload categorised CSVs to firefly using FIDI (Firefly data import tool) and notify on error to discord channel

The manual step is to use transcat to categorised parsed transactions. See - https://github.com/Hapyr/trans-cat

## Setup

1. Configure .env file for processing pipeline. This configures the discord API to send notifications to.

```bash
cat .env
DISCORD_REST_API="https://discord.com/api/v10"
DISCORD_BOT_INFO="https://discord.com/developers/applications/<application id>/bot, <bot version>"
DISCORD_TOKEN=
DISCORD_CHANNEL_ID=
```

2. Configure .env file for firefly

```bash
FIREFLY_NGINX_CONF_DIR=./conf.d/
FIREFLY_MYSQL_PASSWORD=
```

3. Configure .fidi.env file for firefly.

```bash
cat deploy/firefly/.fidi.env
<see https://raw.githubusercontent.com/firefly-iii/firefly-iii/main/.env.example>
```

4. Write configs + code for your bank

To setup processing for a bank statement, you need to create:
- A parsing config (see examples in `/configs/parse`), which defines how to extract transactions from a pdf statement
- An import config for the Firefly Data Import Tool (see examples in `/configs/import/`)
- Code up an optional module for additional pre or post processing work when parsing a pdf bank statement. See `modules/`

## Processing tools

### Scripts

These are the scripts run by the cron job for parsing and uploading

```bash
usage: parse.py [-h] -i INPUT [INPUT ...] -o OUTPUT -c CONFIG [-d]

Parse pdf bank statements to a CSV file containing transactions

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        Input directories or files
  -o OUTPUT, --output OUTPUT
                        Output file
  -c CONFIG, --config CONFIG
                        Config file
  -d, --debug           Debug with breakpoint
```

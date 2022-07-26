# 1. Check dir 1 for files
# 2. Run extract on all files in dir 1 and save them to dir2
# 3. Manually categorise files in dir2 and save to dir3
# 4. Upload all categorised files in dir3

from pathlib import Path
from parse import get_input_files, Config as ParseConfig
import subprocess
import requests
import os


DISCORD_REST_API = os.environ.get("DISCORD_REST_API")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")
DISCORD_BOT_INFO = os.environ.get("DISCORD_BOT_INFO")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")


def notify(message: str, channel_id: str, bot_info: str, token: str):
    return requests.post(
        f"{DISCORD_REST_API}/channels/{channel_id}/messages",
        headers={
            "Authorization": f"Bot {token}",
            "UserAgent": f"DiscordBot ({bot_info})",
        },
        json={"content": message, "tts": False},
    )


def upload_files(upload_path: str, parse_config: ParseConfig, import_config_path: Path):
    """Upload categorised files from dir to firefly"""
    input_files = get_input_files(upload_path, parse_config)
    for input_file in input_files:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-it",
                "php",
                "artisan" "importer:import",
                str(import_config_path),
                str(input_file),
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            error_message = f"UPLOAD ERROR: {input_file}"
            error_message += f"\n{result.stdout.decode('utf-8')}"
            error_message += f"\n{result.stderr.decode('utf-8')}"
            result = notify(
                error_message, DISCORD_CHANNEL_ID, DISCORD_BOT_INFO, DISCORD_TOKEN
            )
            if result and not result.status_code != 200:
                print(f"Could not notify upload error: {result.content}")
                print(f"UPLOAD ERROR: {error_message}")
            if not result:
                print(f"UPLOAD ERROR: {error_message}")

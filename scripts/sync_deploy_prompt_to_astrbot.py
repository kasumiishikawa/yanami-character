from __future__ import annotations

import json
from pathlib import Path


CONFIG_PATH = Path(r"C:\Users\31697\data\cmd_config.json")
PROMPT_PATH = Path(r"D:\character\deploy\system_prompt.md")


def main() -> None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

    default_personality = config.get("provider_settings", {}).get("default_personality")
    personas = config.get("persona", [])
    if not personas:
        raise RuntimeError("No persona found in AstrBot config.")

    target = None
    if default_personality:
        for persona in personas:
            if persona.get("name") == default_personality:
                target = persona
                break

    if target is None:
        target = personas[0]

    old_len = len(target.get("system_prompt", ""))
    target["system_prompt"] = prompt
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8-sig",
        newline="\n",
    )

    print(f"Updated persona: {target.get('name')}")
    print(f"System prompt length: {old_len} -> {len(prompt)}")
    print("Restart AstrBot or reload persona config before testing.")


if __name__ == "__main__":
    main()

from pathlib import Path
from typing import Dict, Any


class SafeFileWriter:
    """
    Controlled file writer.
    Prevents arbitrary filesystem access.
    """

    def __init__(self, base_dir: str = "backend/app/generated_apps"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_file(self, relative_path: str, content: str) -> Dict[str, Any]:
        target_path = (self.base_dir / relative_path).resolve()

        # 🚨 Prevent path traversal
        if not str(target_path).startswith(str(self.base_dir)):
            return {
                "success": False,
                "error": "Invalid file path"
            }

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "path": str(target_path)
        }

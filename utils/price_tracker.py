from pathlib import Path
import json

class PriceTracker:
    def __init__(self, file_path='utils/price_history.json'):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def _save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def get_last_price(self, commodity: str):
        return self.data.get(commodity, {}).get('price')

    def update_price(self, commodity: str, new_price: float):
        self.data[commodity] = {'price': new_price}
        self._save() 
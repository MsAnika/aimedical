from app.services.ml.registry import get_registry
from app.core.config import get_settings

settings = get_settings()
print(f'force_demo: {settings.force_demo}')

registry = get_registry()
print(f'Status pneumonia: {registry.status("pneumonia")}')
print(f'Status skin: {registry.status("skin")}')

# Try to load models
registry.load_models()
print(f'After load - Status pneumonia: {registry.status("pneumonia")}')
print(f'After load - Status skin: {registry.status("skin")}')
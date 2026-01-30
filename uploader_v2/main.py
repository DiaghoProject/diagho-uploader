from .runner import run_forever
from ..config import load_config

def main():
    config = load_config()
    run_forever(config)

if __name__ == "__main__":
    main()

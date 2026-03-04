#!/usr/bin/env python3
"""
anami-stream — Video Streaming Service

Streams footage from a USB capture card (HDMI capture device) as MJPEG
over HTTP. Mirrors the architecture of anami-controller/main.py.

Usage:
    python3 main.py
    python3 main.py --config config.yaml
    python3 main.py --device 1 --quality high
    python3 main.py --port 8090

Verification:
    curl http://localhost:8090/api/health
    Open http://localhost:8090/stream in a browser
    curl http://localhost:8090/snapshot > frame.jpg
"""

import argparse
import signal
import sys
import time

import yaml

from capture.capture_manager import CaptureManager
from utils.logger import get_logger, setup_logging

logger = get_logger('Main')


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='anami-stream — MJPEG video streaming service',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py                          # Default config.yaml, device 0
  python3 main.py --device 1              # Use /dev/video1
  python3 main.py --quality high          # Start at high quality
  python3 main.py --port 8091             # Different port
  python3 main.py --config config.yaml    # Explicit config file
        """,
    )
    parser.add_argument('--config', '-c', default='config.yaml',
                        help='Configuration file (default: config.yaml)')
    parser.add_argument('--device', type=int,
                        help='Override capture device index (default: from config)')
    parser.add_argument('--quality', choices=['low', 'medium', 'high'],
                        help='Override default quality (default: from config)')
    parser.add_argument('--port', type=int,
                        help='Override API port (default: from config)')
    parser.add_argument('--host',
                        help='Override API host (default: from config)')
    return parser.parse_args()


def load_config(config_file: str) -> dict:
    try:
        with open(config_file, 'r') as f:
            cfg = yaml.safe_load(f) or {}
        logger.info(f"Configuration loaded from: {config_file}")
        return cfg
    except FileNotFoundError:
        logger.warning(f"Config file '{config_file}' not found, using defaults")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse config file: {e}")
        return {}


def main():
    args = parse_arguments()

    # Load configuration
    config = load_config(args.config)

    # Set up logging from config
    log_cfg = config.get('logging', {})
    setup_logging(
        log_level=log_cfg.get('level', 'INFO'),
        console=log_cfg.get('console', True),
        file=log_cfg.get('file', True),
        log_directory=log_cfg.get('log_directory', 'logs'),
    )

    # Resolve capture settings (CLI overrides config)
    capture_cfg = config.get('capture', {})
    device_index = args.device if args.device is not None else capture_cfg.get('device_index', 0)
    quality = args.quality or capture_cfg.get('default_quality', 'medium')

    # Resolve API settings
    api_cfg = config.get('api', {})
    host = args.host or api_cfg.get('host', '0.0.0.0')
    port = args.port or api_cfg.get('port', 8090)

    logger.info("Starting anami-stream")
    logger.info(f"  Capture device: {device_index}")
    logger.info(f"  Default quality: {quality}")
    logger.info(f"  API endpoint: http://{host}:{port}")

    # Initialise capture manager
    capture_manager = CaptureManager(device_index=device_index, quality=quality)
    opened = capture_manager.start()
    if not opened:
        logger.warning(
            "Capture device not available at startup. "
            "Service will run; stream will show unavailable until device connects."
        )

    # Start API server in main thread (blocks until killed)
    def _signal_handler(sig, frame):
        logger.info("Shutdown signal received — stopping capture...")
        capture_manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        from api.server import start_api_server
        start_api_server(capture_manager, config, host=host, port=port)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        capture_manager.stop()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

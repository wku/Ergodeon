#!/bin/bash

python3 project_scanner_v4.py ../ \
  --output-dir data/Ergodeon \
  --prefix Ergodeon \
  --exclude-dirs \
    .venv data demo .git .idea memory tests research migrations todo mail local_db extentions tmp \
  --exclude-ext \
    .png .jpg .jpeg .gif .ico .svg .webp \
    .lock .log .iml .bin .jar \
  --exclude-patterns \
    .ru.md \
  --include-files \
    pubspec.yaml analysis_options.yaml



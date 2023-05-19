#!/bin/bash
python3 parser.py
git diff --quiet && git diff --staged --quiet || git commit -am "$(date)" && git push

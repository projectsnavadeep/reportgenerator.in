#!/usr/bin/env bash
set -e
exec gunicorn app3:app --bind 0.0.0.0:${PORT}

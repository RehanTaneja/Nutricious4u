#!/bin/bash
uvicorn server:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 75 --timeout-graceful-shutdown 30 --limit-concurrency 1000 --limit-max-requests 10000 
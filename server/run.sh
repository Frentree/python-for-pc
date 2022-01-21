#!/bin/bash


function kill_by_name() {
    ps auxww | awk '/gunicorn/ {print $2}' | xargs kill -9
    ps auxww | awk '/celery_app worker/ {print $2}' | xargs kill -9
}

kill_by_name "gunicorn"
gunicorn Server:app --bind 0.0.0.0:11119 --reload


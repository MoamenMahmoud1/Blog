import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

cpu_count = os.process_cpu_count() or 1
workers = int(os.getenv("WEB_CONCURRENCY", min(cpu_count + 1, 4)))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "2"))

timeout = 30
graceful_timeout = 30
keepalive = 5

max_requests = 1000
max_requests_jitter = 100

preload_app = True
worker_tmp_dir = "/dev/shm"

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
capture_output = True

forwarded_allow_ips = "*"
secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
}

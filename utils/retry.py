from tenacity import retry, wait_exponential, stop_after_attempt

def resilient(**kwargs):
    """
    Decorator that retries a function up to five times, using
    exponential back-off. Apply it with @resilient() above any
    network-fetch function.
    """
    defaults = dict(
        wait=wait_exponential(multiplier=1, min=1, max=32),
        stop=stop_after_attempt(5),
        reraise=True
    )
    defaults.update(kwargs)
    return retry(**defaults)

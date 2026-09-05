"""The limiter's clock is injectable, so the window is driven, never slept on."""
from app.services.rate_limit import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_allows_up_to_the_limit_then_refuses():
    clock = FakeClock()
    limiter = RateLimiter(attempts=3, window_seconds=60, now=clock)

    assert [limiter.retry_after("ip:1.2.3.4") for _ in range(3)] == [None] * 3
    assert limiter.retry_after("ip:1.2.3.4") is not None


def test_the_window_slides_rather_than_resetting():
    clock = FakeClock()
    limiter = RateLimiter(attempts=2, window_seconds=60, now=clock)

    limiter.retry_after("k")
    clock.advance(30)
    limiter.retry_after("k")
    clock.advance(31)

    # The first hit has aged out, the second has not: room for exactly one more.
    assert limiter.retry_after("k") is None
    assert limiter.retry_after("k") is not None


def test_keys_are_budgeted_independently():
    clock = FakeClock()
    limiter = RateLimiter(attempts=1, window_seconds=60, now=clock)

    assert limiter.retry_after("ip:1.2.3.4") is None
    assert limiter.retry_after("ip:5.6.7.8") is None
    assert limiter.retry_after("ip:1.2.3.4") is not None


def test_retry_after_counts_down_as_the_window_passes():
    clock = FakeClock()
    limiter = RateLimiter(attempts=1, window_seconds=60, now=clock)

    limiter.retry_after("k")
    clock.advance(20)

    assert limiter.retry_after("k") == 40


def test_quiet_keys_are_swept_so_the_dict_cannot_grow_forever():
    """Otherwise an attacker rotating addresses turns the rate limiter into its
    own memory exhaustion vector."""
    clock = FakeClock()
    limiter = RateLimiter(attempts=5, window_seconds=60, now=clock)

    for address in range(500):
        limiter.retry_after(f"ip:{address}")

    clock.advance(61)
    limiter.retry_after("ip:still-here")

    assert len(limiter._hits) == 1

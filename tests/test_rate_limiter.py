import unittest
import time
from arxivdigest_recommenders.util import AsyncRateLimiter


class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limit(self):
        stamps = []
        limiter = AsyncRateLimiter(1000, 2)
        while len(stamps) < 10000:
            async with limiter:
                stamps.append(time.monotonic())
        for stamp in stamps[1:1000]:
            self.assertAlmostEqual(stamps[0], stamp, delta=0.1)
        self.assertLess(stamps[0] + 2, stamps[1000])
        for stamp in stamps[9001:]:
            self.assertAlmostEqual(stamps[9000], stamp, delta=0.1)


if __name__ == "__main__":
    unittest.main()

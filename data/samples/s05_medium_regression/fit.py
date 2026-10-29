import random


def fit(xs, ys, lr=0.01, steps=2000):
    """Fit y = w*x + b with gradient descent."""
    w, b = 0.0, 0.0
    n = len(xs)
    for _ in range(steps):
        dw = sum((w * x + b - y) * x for x, y in zip(xs, ys)) * 2 / n
        db = sum((w * x + b - y) for x, y in zip(xs, ys)) * 2 / n
        w -= lr * dw
        b -= lr * db
    return w, b


def mse(xs, ys, w, b):
    return sum((w * x + b - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


if __name__ == "__main__":
    random.seed(1)
    xs = [i / 10 for i in range(50)]
    ys = [3 * x + 2 + random.uniform(-0.3, 0.3) for x in xs]
    w, b = fit(xs, ys)
    print("w", round(w, 2), "b", round(b, 2), "mse", round(mse(xs, ys, w, b), 4))

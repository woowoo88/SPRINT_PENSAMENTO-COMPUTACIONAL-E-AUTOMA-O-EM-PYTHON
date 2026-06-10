import math
import random


class DemandPredictor:
    """Small linear-regression model trained with gradient descent."""

    def __init__(self) -> None:
        self.weights = [0.0] * 6
        self.means = [0.0] * 5
        self.scales = [1.0] * 5
        self._train()

    @staticmethod
    def _features(hour: int, weekday: int, temperature_c: float, event: bool) -> list[float]:
        angle = 2 * math.pi * hour / 24
        return [
            math.sin(angle),
            math.cos(angle),
            1.0 if weekday < 5 else 0.0,
            temperature_c,
            1.0 if event else 0.0,
        ]

    def _training_data(self) -> list[tuple[list[float], float]]:
        rng = random.Random(42)
        rows = []
        for day in range(56):
            weekday = day % 7
            temperature = 19 + 7 * math.sin(day / 8) + rng.uniform(-2, 2)
            for hour in range(24):
                morning_peak = 36 * math.exp(-((hour - 9) ** 2) / 7)
                evening_peak = 25 * math.exp(-((hour - 18) ** 2) / 9)
                business = 18 if weekday < 5 and 8 <= hour <= 19 else 4
                event = weekday in (4, 5) and 18 <= hour <= 22 and rng.random() < 0.2
                demand = 14 + morning_peak + evening_peak + business
                demand += (temperature - 22) * 0.7 + (30 if event else 0) + rng.uniform(-5, 5)
                rows.append((self._features(hour, weekday, temperature, event), max(5, demand)))
        return rows

    def _train(self) -> None:
        rows = self._training_data()
        columns = list(zip(*(features for features, _ in rows)))
        self.means = [sum(column) / len(column) for column in columns]
        self.scales = [
            max(1.0, (sum((value - mean) ** 2 for value in column) / len(column)) ** 0.5)
            for column, mean in zip(columns, self.means)
        ]
        normalized = [
            ([1.0] + [(value - mean) / scale for value, mean, scale in zip(features, self.means, self.scales)], target)
            for features, target in rows
        ]

        learning_rate = 0.015
        for _ in range(900):
            gradients = [0.0] * len(self.weights)
            for features, target in normalized:
                error = sum(weight * value for weight, value in zip(self.weights, features)) - target
                for index, value in enumerate(features):
                    gradients[index] += error * value
            for index in range(len(self.weights)):
                self.weights[index] -= learning_rate * gradients[index] / len(normalized)

    def predict(self, hour: int, weekday: int, temperature_c: float, event: bool = False) -> float:
        raw = self._features(hour, weekday, temperature_c, event)
        features = [1.0] + [
            (value - mean) / scale
            for value, mean, scale in zip(raw, self.means, self.scales)
        ]
        return max(0.0, sum(weight * value for weight, value in zip(self.weights, features)))

    def day_forecast(self, weekday: int, temperature_c: float, event: bool = False) -> list[dict]:
        return [
            {
                "hour": hour,
                "predicted_kw": round(
                    self.predict(hour, weekday, temperature_c, event and 18 <= hour <= 22),
                    1,
                ),
            }
            for hour in range(24)
        ]

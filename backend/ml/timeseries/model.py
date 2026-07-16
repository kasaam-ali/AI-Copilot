"""Time-series LSTM for remaining-useful-life (RUL) regression."""

from __future__ import annotations

import torch
import torch.nn as nn


class RULLSTM(nn.Module):
    """Stacked LSTM over a sensor window, producing a single RUL estimate.

    Dropout modules in the head stay active during MC-Dropout sampling to yield an
    uncertainty estimate, mirroring the image and tabular models.
    """

    def __init__(
        self,
        n_sensors: int,
        hidden: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_sensors,
            hidden_size=hidden,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, window, n_sensors)
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        return self.head(last).squeeze(-1)

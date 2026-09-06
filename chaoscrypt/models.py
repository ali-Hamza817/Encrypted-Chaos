"""Attack models: a deep same-resolution CNN and a small U-Net.

Both map a ciphertext image (N,C,H,W in [0,1]) to a predicted plaintext image in
[0,1] via a final sigmoid. Keep them small -- the contribution is the
cryptanalysis study, not the architecture.
"""
from __future__ import annotations

import torch
import torch.nn as nn


class SimpleCNN(nn.Module):
    def __init__(self, in_ch: int = 1, out_ch: int = 1, width: int = 64, depth: int = 8):
        super().__init__()
        layers = [nn.Conv2d(in_ch, width, 3, padding=1), nn.ReLU(inplace=True)]
        for _ in range(max(0, depth - 2)):
            layers += [nn.Conv2d(width, width, 3, padding=1),
                       nn.BatchNorm2d(width), nn.ReLU(inplace=True)]
        layers += [nn.Conv2d(width, out_ch, 3, padding=1), nn.Sigmoid()]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class _DoubleConv(nn.Module):
    def __init__(self, i, o):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
            nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNet(nn.Module):
    """3-level U-Net. Input H, W must be divisible by 8."""

    def __init__(self, in_ch: int = 1, out_ch: int = 1, base: int = 32):
        super().__init__()
        self.d1 = _DoubleConv(in_ch, base)
        self.d2 = _DoubleConv(base, base * 2)
        self.d3 = _DoubleConv(base * 2, base * 4)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = _DoubleConv(base * 4, base * 8)
        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.u3 = _DoubleConv(base * 8, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.u2 = _DoubleConv(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.u1 = _DoubleConv(base * 2, base)
        self.out = nn.Conv2d(base, out_ch, 1)

    def forward(self, x):
        c1 = self.d1(x)
        c2 = self.d2(self.pool(c1))
        c3 = self.d3(self.pool(c2))
        b = self.bottleneck(self.pool(c3))
        x = self.u3(torch.cat([self.up3(b), c3], dim=1))
        x = self.u2(torch.cat([self.up2(x), c2], dim=1))
        x = self.u1(torch.cat([self.up1(x), c1], dim=1))
        return torch.sigmoid(self.out(x))


def build_model(spec: dict) -> nn.Module:
    spec = dict(spec)
    name = spec.pop("name", "unet").lower()
    if name in ("cnn", "simplecnn"):
        return SimpleCNN(**spec)
    if name == "unet":
        return UNet(**spec)
    raise ValueError(f"unknown model {name!r}; expected 'cnn' or 'unet'")

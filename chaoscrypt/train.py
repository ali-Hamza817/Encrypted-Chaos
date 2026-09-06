"""Training loop for the attack model."""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.utils.data import DataLoader


def _psnr_from_mse(m: float, data_range: float = 1.0) -> float:
    if m <= 1e-12:
        return 99.0
    return 10.0 * torch.log10(torch.tensor(data_range ** 2 / m)).item()


def train_model(model, train_ds, val_ds, *, epochs: int = 20, batch_size: int = 64,
                lr: float = 1e-3, device: str | None = None, l1_weight: float = 1.0,
                mse_weight: float = 0.5, log=print):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, epochs))
    l1, l2 = nn.L1Loss(), nn.MSELoss()

    tl = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    vl = DataLoader(val_ds, batch_size=batch_size)

    history = {"train_loss": [], "val_loss": [], "val_psnr": []}
    best_state, best_psnr = None, -1.0

    for ep in range(1, epochs + 1):
        model.train()
        run = 0.0
        for x, y in tl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            pred = model(x)
            loss = l1_weight * l1(pred, y) + mse_weight * l2(pred, y)
            loss.backward()
            opt.step()
            run += loss.item() * x.size(0)
        sched.step()
        train_loss = run / len(train_ds)

        model.eval()
        vrun, vmse = 0.0, 0.0
        with torch.no_grad():
            for x, y in vl:
                x, y = x.to(device), y.to(device)
                pred = model(x)
                vrun += (l1_weight * l1(pred, y) + mse_weight * l2(pred, y)).item() * x.size(0)
                vmse += l2(pred, y).item() * x.size(0)
        val_loss = vrun / len(val_ds)
        val_psnr = _psnr_from_mse(vmse / len(val_ds))

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_psnr"].append(val_psnr)
        log(f"epoch {ep:3d}/{epochs}  train {train_loss:.4f}  val {val_loss:.4f}  "
            f"val_psnr {val_psnr:.2f} dB")

        if val_psnr > best_psnr:
            best_psnr = val_psnr
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, history

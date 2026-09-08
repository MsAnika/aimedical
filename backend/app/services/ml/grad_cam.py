import numpy as np
import torch
import torch.nn.functional as F


class GradCAM:
    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module):
        self.model = model
        self.model.eval()
        self.gradients = None
        self.activations = None
        hook = target_layer.register_forward_hook(self._forward_hook)
        target_layer.register_full_backward_hook(self._backward_hook)
        self._remove_handles = lambda: hook.remove()

    def _forward_hook(self, module, input, output):
        self.activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def close(self):
        self._remove_handles()

    def generate(self, input_tensor: torch.Tensor, target_class: int | None = None) -> np.ndarray:
        self.model.zero_grad()
        output = self.model(input_tensor)
        if target_class is None:
            target_class = int(output.argmax(dim=1).item())
        one_hot = torch.zeros_like(output)
        one_hot[0, target_class] = 1
        self.model.zero_grad()
        output.backward(gradient=one_hot)

        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.activations).sum(dim=1, keepdim=True))
        cam = F.interpolate(
            cam,
            size=input_tensor.shape[2:],
            mode="bilinear",
            align_corners=False,
        )
        cam = cam[0, 0].cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        return cam


def find_target_layer(model: torch.nn.Module, arch: str) -> torch.nn.Module:
    if arch == "resnet":
        return model.layer4[-1]
    if arch == "efficientnet":
        return model.features[-1]
    for name, module in reversed(list(model.named_modules())):
        if isinstance(module, torch.nn.Conv2d):
            return module
    raise ValueError("No conv layer found for Grad-CAM")

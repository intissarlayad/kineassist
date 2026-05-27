import numpy as np
import os

os.makedirs("data/references", exist_ok=True)
frames = 60
t = np.linspace(0, np.pi, frames)

# Flexion genou
knee = np.column_stack([
    170 - 80 * np.sin(t),
    170 - 80 * np.sin(t),
    180 - 20 * np.sin(t),
    180 - 20 * np.sin(t),
])
np.save("data/references/knee_flexion_ref.npy", knee)

# Elevation bras
arm = np.column_stack([
    10 + 150 * np.sin(t),
    10 + 150 * np.sin(t),
    170 * np.ones(frames),
    170 * np.ones(frames),
])
np.save("data/references/arm_raise_ref.npy", arm)

# Rotation tronc
trunk = np.column_stack([
    90 * np.ones(frames),
    90 * np.ones(frames),
    90 - 45 * np.sin(t),
    90 + 45 * np.sin(t),
])
np.save("data/references/trunk_rotation_ref.npy", trunk)

print("References generees dans data/references/")
for f in os.listdir("data/references"):
    arr = np.load(f"data/references/{f}")
    print(f"  {f} : shape {arr.shape}")
import numpy as np

try:
    from fastdtw import fastdtw
    from scipy.spatial.distance import euclidean
    HAS_DTW = True
except ImportError:
    HAS_DTW = False


def score_rep(angles_series, reference_npy):

    if not angles_series or reference_npy is None:
        return 0.0

    # garder seulement les frames valides
    valid_frames = []

    for frame in angles_series:

        if not isinstance(frame, dict):
            continue

        values = list(frame.values())

        # ignorer frames vides
        if len(values) == 0:
            continue

        # ignorer NaN / None
        clean_values = []

        for v in values:
            if v is None:
                continue

            try:
                clean_values.append(float(v))
            except:
                continue

        if len(clean_values) > 0:
            valid_frames.append(clean_values)

    if len(valid_frames) < 2:
        return 0.0

    # prendre taille minimale commune
    min_len = min(len(f) for f in valid_frames)

    current = np.array(
        [f[:min_len] for f in valid_frames],
        dtype=float
    )

    n_joints = min(current.shape[1], reference_npy.shape[1])

    current = current[:, :n_joints]
    ref = reference_npy[:, :n_joints].astype(float)

    if HAS_DTW:
        dist, _ = fastdtw(current, ref, dist=euclidean)
        normalized = dist / (max(len(current), len(ref)) * n_joints + 1e-6)
        score = max(0.0, 100.0 - normalized * 1.8)
    else:
        ref_mean = np.mean(ref, axis=0)
        errors = [
            abs(v - ref_mean[i])
            for frame in current
            for i, v in enumerate(frame[:n_joints])
        ]
        score = max(0.0, 100.0 - np.mean(errors) * 1.5)

    return round(float(score), 1)


def classify_error(angles, targets, tolerance=15):
    """
    Retourne la liste des erreurs detectees avec severite et direction.
    """
    errors = []
    for joint, current in angles.items():
        target = targets.get(joint)
        if target is None:
            continue
        diff = current - target
        if abs(diff) > tolerance:
            errors.append({
                "joint":     joint,
                "current":   round(current, 1),
                "target":    target,
                "diff":      round(diff, 1),
                "direction": "insuffisante" if diff < 0 else "excessive",
                "severity":  "critique" if abs(diff) > tolerance * 2 else "modere",
            })
    return errors


def progression_summary(scores_history):
    """
    Retourne un dict de stats sur la progression de la session.
    """
    if not scores_history:
        return {}
    arr = np.array(scores_history)
    trend = "amelioration" if len(arr) > 2 and arr[-1] > arr[0] else "stable"
    return {
        "mean":    round(float(np.mean(arr)), 1),
        "best":    round(float(np.max(arr)), 1),
        "worst":   round(float(np.min(arr)), 1),
        "last":    round(float(arr[-1]), 1),
        "trend":   trend,
        "n_reps":  len(arr),
    }
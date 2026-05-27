import numpy as np


def calculate_angle(a, b, c):
    a = np.array(a[:2])
    b = np.array(b[:2])
    c = np.array(c[:2])
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    cosine = np.clip(cosine, -1.0, 1.0)
    return round(float(np.degrees(np.arccos(cosine))), 1)


def get_joint_angles(landmarks):
    if landmarks is None:
        return {}

    def lm(idx):
        l = landmarks[idx]
        return (l.x, l.y)

    return {
        "genou_gauche":   calculate_angle(lm(23), lm(25), lm(27)),
        "genou_droit":    calculate_angle(lm(24), lm(26), lm(28)),
        "hanche_gauche":  calculate_angle(lm(11), lm(23), lm(25)),
        "hanche_droite":  calculate_angle(lm(12), lm(24), lm(26)),
        "epaule_gauche":  calculate_angle(lm(13), lm(11), lm(23)),
        "epaule_droite":  calculate_angle(lm(14), lm(12), lm(24)),
        "coude_gauche":   calculate_angle(lm(11), lm(13), lm(15)),
        "coude_droit":    calculate_angle(lm(12), lm(14), lm(16)),
    }


EXERCISE_JOINTS = {
    # ── Exercices existants ──
    "knee_flexion":    ["genou_gauche", "genou_droit", "hanche_gauche", "hanche_droite"],
    "arm_raise":       ["epaule_gauche", "epaule_droite", "coude_gauche", "coude_droit"],
    "trunk_rotation":  ["hanche_gauche", "hanche_droite", "epaule_gauche", "epaule_droite"],
    # ── Membres inférieurs ──
    "squat":           ["genou_gauche", "genou_droit", "hanche_gauche", "hanche_droite"],
    "hip_extension":   ["hanche_gauche", "hanche_droite"],
    "lunge":           ["genou_gauche", "genou_droit", "hanche_gauche", "hanche_droite"],
    # ── Membres supérieurs ──
    "lateral_raise":   ["epaule_gauche", "epaule_droite"],
    "bicep_curl":      ["coude_gauche", "coude_droit"],
    # ── Rachis ──
    "good_morning":    ["hanche_gauche", "hanche_droite", "epaule_gauche", "epaule_droite"],
}


def get_exercise_angles(landmarks, exercise_id):
    all_angles = get_joint_angles(landmarks)
    joints = EXERCISE_JOINTS.get(exercise_id, list(all_angles.keys()))
    return {k: all_angles[k] for k in joints if k in all_angles}


def angle_to_color(current, target, tolerance=15):
    diff = abs(current - target)
    if diff <= tolerance:
        return (0, 220, 120)
    elif diff <= tolerance * 2:
        return (255, 165, 0)
    return (220, 50, 50)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Pipeline: Label Studio Export -> Target JSON + MediaPipe Joint Angles
=======================================================================
Steps:
    1. Read Label Studio export JSON
    2. Convert to target format (name, shot_type, segment_range, impact_frame, phase_boundaries)
    3. Extract 12 joint angles via MediaPipe
    4. Output complete JSON

Dependencies:
    pip install opencv-python mediapipe numpy

Usage:
    python full_pipeline.py -i export.json -v video.mp4 -o final.json
    python full_pipeline.py -i export.json --preview
    python full_pipeline.py -i export.json -o result.json --no-angles
"""

import json, argparse, os, re, sys
from pathlib import Path


# ===== Part 1: Format Conversion =====

def convert_format(export_data):
    """Convert Label Studio export to target JSON format"""
    items = export_data if isinstance(export_data, list) else [export_data]
    results = []

    for item in items:
        ann = item.get("annotations", [{}])[0]
        result_list = ann.get("result", [])
        if not result_list:
            continue

        fields = {}
        for r in result_list:
            fn = r.get("from_name", "")
            val = r.get("value", {})
            if r.get("type") == "choices":
                fields[fn] = val.get("choices", [None])[0]
            elif r.get("type") == "number":
                fields[fn] = val.get("number")

        file_upload = item.get("file_upload", "unknown.mp4")
        clean_name = re.sub(r'^[a-f0-9]+-', '', Path(file_upload).stem)

        annotation = {
            "name": f"{clean_name}_{fields.get('shot_type','unknown')}",
            "shot_type": fields.get("shot_type", "unknown"),
            "segment_range": [fields.get("start_frame", 0), fields.get("end_frame", 0)],
            "impact_frame": fields.get("impact_frame", 0),
            "phase_boundaries": {
                "start": fields.get("start_frame", 0),
                "backswing_peak": fields.get("backswing_peak", 0),
                "forward_start": fields.get("forward_start", 0),
                "impact": fields.get("impact_frame", 0),
                "end": fields.get("end_frame", 0)
            },
            "fps": 30.0,
            "total_frames": 0,
            "angles": [],
            "key_angles": {}
        }
        results.append(annotation)

    return results


# ===== Part 2: MediaPipe Joint Angle Extraction =====

def extract_joint_angles(video_path, annotation, verbose=True):
    """Extract joint angles from video frames and merge into annotation"""
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
    except ImportError:
        print("Missing dependencies. Run: pip install opencv-python mediapipe numpy")
        return

    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return

    def calc_angle(a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        ba, bc = a - b, c - b
        n1 = np.linalg.norm(ba) + 1e-6
        n2 = np.linalg.norm(bc) + 1e-6
        cos = np.clip(np.dot(ba, bc) / (n1 * n2), -1.0, 1.0)
        return round(np.degrees(np.arccos(cos)), 2)

    phase = annotation["phase_boundaries"]
    needed = set(phase.values())
    sr = annotation["segment_range"]
    if sr and len(sr) == 2 and sr[0] < sr[1]:
        needed.update(range(sr[0], sr[1] + 1))
    needed = sorted(f for f in needed if f >= 0)

    if verbose:
        print(f"Processing {annotation['name']}: {len(needed)} frames")

    cap = cv2.VideoCapture(video_path)
    annotation["fps"] = round(cap.get(cv2.CAP_PROP_FPS), 2)
    annotation["total_frames"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    pose = mp.solutions.pose.Pose(
        model_complexity=1, min_detection_confidence=0.5
    )

    frame_angles = {}
    detected = 0
    missed = 0

    for idx, fid in enumerate(needed):
        if fid >= annotation["total_frames"]:
            continue

        cap.set(cv2.CAP_PROP_POS_FRAMES, fid)
        ret, frame = cap.read()
        if not ret:
            missed += 1
            continue

        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)

        if not result.pose_landmarks:
            missed += 1
            continue

        lm = result.pose_landmarks.landmark
        pt = lambda i: np.array([lm[i].x * w, lm[i].y * h])

        angles = {
            # Arm angles
            "right_elbow":    calc_angle(pt(12), pt(14), pt(16)),
            "left_elbow":     calc_angle(pt(11), pt(13), pt(15)),
            "right_shoulder": calc_angle(pt(14), pt(12), pt(24)),
            "left_shoulder":  calc_angle(pt(13), pt(11), pt(23)),
            "right_wrist":    calc_angle(pt(14), pt(16), pt(20)),
            "left_wrist":     calc_angle(pt(13), pt(15), pt(19)),
            # Torso
            "torso_rotation": round(np.degrees(np.arctan2(
                abs(pt(12)[1]-pt(11)[1]), abs(pt(12)[0]-pt(11)[0])+1e-6)), 2),
            # Leg angles
            "right_knee": calc_angle(pt(24), pt(26), pt(28)),
            "left_knee":  calc_angle(pt(23), pt(25), pt(27)),
            "right_hip":  calc_angle(pt(12), pt(24), pt(26)),
            "left_hip":   calc_angle(pt(11), pt(23), pt(25)),
        }
        # Trunk lean (angle from vertical)
        ms = (pt(11) + pt(12)) / 2
        mh = (pt(23) + pt(24)) / 2
        angles["trunk_lean"] = calc_angle(
            mh, ms, np.array([ms[0], ms[1] - 100])
        )

        frame_angles[fid] = angles
        detected += 1

        if verbose and (idx + 1) % 20 == 0:
            print(f"  Progress: {idx+1}/{len(needed)}")

    cap.release()
    pose.close()

    if verbose:
        print(f"  Detected: {detected} frames | Missed: {missed} frames")

    # Build per-frame angle sequence
    annotation["angles"] = []
    if sr and len(sr) == 2 and sr[0] < sr[1]:
        for f in range(sr[0], sr[1] + 1):
            if f in frame_angles:
                annotation["angles"].append({
                    "frame": f,
                    "angles": frame_angles[f]
                })

    # Build named key-frame angles
    annotation["key_angles"] = {}
    for name, fid in phase.items():
        if fid in frame_angles:
            annotation["key_angles"][name] = {
                "frame": fid,
                "angles": frame_angles[fid]
            }


# ===== Part 3: Main Entry =====

def main():
    parser = argparse.ArgumentParser(
        description="Label Studio Export -> Target JSON + MediaPipe Joint Angles",
        epilog="""Examples:
  python full_pipeline.py -i export.json -v video.mp4 -o serve1.json
  python full_pipeline.py -i export.json --preview
  python full_pipeline.py -i export.json -o result.json --no-angles
        """
    )
    parser.add_argument("-i", "--input", required=True, help="Label Studio export JSON")
    parser.add_argument("-v", "--video", help="Video file path")
    parser.add_argument("-o", "--output", default="final_result.json", help="Output JSON")
    parser.add_argument("--preview", action="store_true", help="Preview only, no file output")
    parser.add_argument("--no-angles", action="store_true", help="Skip angle extraction")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"File not found: {args.input}")
        return

    with open(args.input, encoding="utf-8") as f:
        export_data = json.load(f)

    annotations = convert_format(export_data)
    if not annotations:
        print("No valid annotations found")
        return

    print(f"Format conversion done: {len(annotations)} annotations")

    if not args.no_angles and args.video:
        for ann in annotations:
            extract_joint_angles(args.video, ann)
    elif not args.no_angles and not args.video:
        print("Warning: No video specified, skipping angle extraction")

    if args.preview:
        for a in annotations:
            print(f"\n{'='*50}")
            print(f"Name: {a['name']}")
            print(f"  Shot type:     {a['shot_type']}")
            print(f"  Segment range: {a['segment_range']}")
            print(f"  Impact frame:  {a['impact_frame']}")
            print(f"  Angle frames:  {len(a['angles'])}")
            print(f"  Key angles:    {len(a['key_angles'])}")
            if a['key_angles']:
                imp = a['key_angles'].get('impact', {})
                if imp:
                    print(f"  Impact angles: {json.dumps(imp['angles'], ensure_ascii=False)}")
        return

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)

    print(f"\nOutput saved: {args.output} ({os.path.getsize(args.output)/1024:.1f} KB)")

    if annotations:
        a = annotations[0]
        print(f"\nPreview:")
        print(f"  Name:          {a['name']}")
        print(f"  Shot type:     {a['shot_type']}")
        print(f"  Segment range: {a['segment_range']}")
        print(f"  Impact frame:  {a['impact_frame']}")
        print(f"  Angle frames:  {len(a['angles'])}")
        if a['key_angles']:
            print(f"  Impact angles: {json.dumps(a['key_angles']['impact']['angles'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
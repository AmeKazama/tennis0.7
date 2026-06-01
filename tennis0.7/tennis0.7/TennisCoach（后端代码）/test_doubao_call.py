import asyncio

from services.tennis_final import DoubaoService, format_enhanced_analysis_report


async def main():
    service = DoubaoService()
    phase_dtw = {
        "sequence_distance": 30.97,
        "keyframe_distance": 33.28,
        "phase_distances": [
            {
                "phase": "forward_to_impact",
                "distance": 39.83,
                "user_frames": 2,
                "standard_frames": 6,
                "path_length": 6,
            },
            {
                "phase": "backswing_to_forward",
                "distance": 34.02,
                "user_frames": 3,
                "standard_frames": 5,
                "path_length": 5,
            },
            {
                "phase": "impact_to_finish",
                "distance": 22.73,
                "user_frames": 13,
                "standard_frames": 10,
                "path_length": 13,
            },
        ],
        "keyframe_distances": [
            {"phase": "impact", "distance": 47.61},
            {"phase": "forward_start", "distance": 38.11},
            {"phase": "backswing_peak", "distance": 24.16},
        ],
    }
    prompt = format_enhanced_analysis_report(
        shot_id=1,
        shot_type="serve",
        dtw_distance=31.43,
        issues=[],
        best_match_name="serve002_serve",
        phase_dtw=phase_dtw,
        user_annotation={},
    )
    result = await service.get_coach_advice(prompt)
    print("DOUBAO_RESULT_START")
    print(result)
    print("DOUBAO_RESULT_END")
    await service.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())

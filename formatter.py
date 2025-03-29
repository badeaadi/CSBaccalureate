import json
import os
import re

PREFIX = "data/"


def split_exercises(file_name="data/sample.in"):
    with open(PREFIX + file_name + ".txt", "r", encoding="utf-8") as file:
        content = file.read()

    # Print the content for debugging
    print("Content to match:", content[:200])  # Print first 200 chars

    # Updated pattern with more flexible matching
    subject_pattern = (
        r"SUBIECTUL\s+(?:al\s+)?([IVX]+)(?:-lea)?\s*\((\d+)(?:\s+de)?\s+puncte\)"
    )

    # First find all matches and print them for debugging
    matches = list(re.finditer(subject_pattern, content, re.DOTALL))
    print(f"Found {len(matches)} matches:")
    for m in matches:
        print(f"Match: {m.group(0)}")

    # Now split the content using the matches
    split_positions = [0] + [m.end() for m in matches] + [len(content)]
    subjects_content = []
    for i in range(len(split_positions) - 1):
        start = split_positions[i]
        end = split_positions[i + 1]
        subjects_content.append(content[start:end])

    all_exercises = {}

    for i, subject_match in enumerate(matches):
        roman_numeral = subject_match.group(1)
        points = subject_match.group(2)
        subject_content = subjects_content[
            i + 1
        ].strip()  # +1 because first split might be empty

        # Split subject content into exercises (1., 2., 3., etc.)
        exercise_pattern = r"(?:^|\n)(\d+\.)(.*?)(?=(?:\n\d+\.)|$)"
        exercises = re.finditer(exercise_pattern, subject_content, re.DOTALL)

        subject_key = {
            "I": "subiectul_1",
            "II": "subiectul_2",
            "III": "subiectul_3",
        }.get(roman_numeral, f"subiectul_{roman_numeral}")

        subject_data = {
            "subject_number": roman_numeral,
            "total_points": points,
            "subject_title": {
                "I": "SUBIECTUL I",
                "II": "SUBIECTUL al II-lea",
                "III": "SUBIECTUL al III-lea",
            }.get(roman_numeral, f"SUBIECTUL {roman_numeral}"),
            "exercises": {},
        }

        for exercise_match in exercises:
            exercise_num = exercise_match.group(1).strip(".")
            exercise_content = exercise_match.group(2).strip()

            exercise_data = {
                "content": exercise_content,
                "exercise_number": exercise_num,
            }

            subject_data["exercises"][exercise_num] = exercise_data

        all_exercises[subject_key] = subject_data

    # Save the structured data
    os.makedirs(PREFIX + file_name, exist_ok=True)
    with open(
        PREFIX + file_name + "/" + "toate_subiectele.json", "w", encoding="utf-8"
    ) as f:
        json.dump(all_exercises, f, indent=4, ensure_ascii=False)

    # # Also save individual subject files
    # for subject_key, subject_data in all_exercises.items():
    #     filename = f"{PREFIX}{file_name}/{subject_key}.json"
    #     with open(filename, "w", encoding="utf-8") as f:
    #         json.dump(subject_data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    split_exercises("E_d_Informatica_2020_sp_MI_C_var_06_LRO")
    split_exercises("E_d_Informatica_2021_sp_MI_C_var_01_LRO")
    split_exercises("E_d_informatica_2022_sp_MI_C_var_05_LRO")
    split_exercises("E_d_Informatica_2023_sp_MI_C_var_05_LRO")
    split_exercises("E_d_Informatica_2024_sp_MI_C_var_model")
    split_exercises("E_d_informatica_2025_sp_MI_C_var_model")

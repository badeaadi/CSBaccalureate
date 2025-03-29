import json
from chat import send_chat_request


def process_all_exercises(data, model, temp=0.0):
    # if exercise_by_exercise:
    #     # Iterate through each subject (subiectul_1, subiectul_2, subiectul_3)
    #     for subject_key, subject in data.items():
    #         exercises = subject.get("exercises", {})

    #         # Iterate through each exercise in the subject
    #         for exercise_number, exercise in exercises.items():
    #             # Get the exercise content
    #             content = exercise.get("content", "")

    #             # Create a formatted exercise with subject info
    #             formatted_exercise = {
    #                 "subject": subject["subject_number"],
    #                 "exercise_number": exercise_number,
    #                 "content": content,
    #             }
    #             # Send the exercise to the chat request function
    #             solution = send_chat_request(formatted_exercise, model, temp)
    #             data[subject_key]["exercises"][exercise_number]["solution"] = solution

    # Combine all exercises into one request
    all_exercises = []

    # Iterate through each subject
    for subject_key, subject in data.items():
        if "full_solutions" in subject_key:
            continue
        exercises = subject.get("exercises", {})

        # Add each exercise with its subject info
        for exercise_number, exercise in exercises.items():
            content = exercise.get("content", "")
            formatted_exercise = {
                "subject": subject["subject_number"],
                "exercise_number": exercise_number,
                "content": content,
            }
            all_exercises.append(formatted_exercise)

    # Send all exercises in one request
    response = send_chat_request(all_exercises, model)

    if response and "choices" in response and len(response["choices"]) > 0:
        # Get the content from the response
        content = response["choices"][0]["message"]["content"]

    return content


# Function to process a single model
def process_model(model_info):
    model_name, model_id = model_info
    print(f"Started {model_name}")
    result = process_all_exercises(data, model_id, temp)
    print(f"Finished {model_name}")
    return model_name, result


# Example usage
if __name__ == "__main__":
    list_of_models = [
        # "E_d_informatica_2025_sp_MI_C_var_model",
        # "E_d_Informatica_2024_sp_MI_C_var_model",
        # "E_d_Informatica_2023_sp_MI_C_var_05_LRO",
        # "E_d_informatica_2022_sp_MI_C_var_05_LRO",
        # "E_d_Informatica_2021_sp_MI_C_var_01_LRO",
        ("E_d_Informatica_2020_sp_MI_C_var_06_LRO",
        "https://info-hobby.ro/wp-content/uploads/2020/06/E_d_Informatica_2020_sp_MI_bar_06.pdf",)
    ]

    for model, barem_url in list_of_models:
        print(f"Processing {model}")
        with open(f"data/{model}/toate_subiectele.json", "r", encoding="utf-8") as f:
            data = json.load(f)

            # for temp in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            for temp in [0.0]:
                print(f"Processing {model} with temp {temp}")

                import concurrent.futures

                # Define models and their identifiers
                models = [
                    ("gpt4o", "gpt-4o-2024-11-20"),
                    # ("anthropicclaude37sonnet","anthropic.claude-3-7-sonnet-20250219-v1:0"),
                    # ("gemini20pro", "gemini-2.0-pro-exp-02-05"),
                    # ("gpt-4.5-preview", "gpt-4.5-preview-2025-02-27"),
                    # ("o3mini", "o3-mini-2025-01-31"),
                ]

                # Use ThreadPoolExecutor to run requests in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit all tasks and create a map of futures to model names
                    future_to_model = {
                        executor.submit(process_model, model_info): model_info
                        for model_info in models
                    }

                    # Process results as they complete
                    for future in concurrent.futures.as_completed(future_to_model):
                        model_name, result = future.result()
                        filename = (
                            f"data/{model}/solutions_{model}_{model_name}_temp_{temp}.json"
                        )
                        with open(filename, "w", encoding="utf-8") as f:
                            # Parse the result text into structured JSON by subject and exercise
                            structured_result = {}
                            current_subject = None
                            current_exercise = None
                            current_content = ""

                            # Split the text by lines
                            lines = result.split("\n")
                            for line in lines:
                                # Check for subject and exercise headers
                                if line.startswith("## Subiect"):
                                    # Save previous exercise if exists
                                    if current_subject and current_exercise:
                                        if current_subject not in structured_result:
                                            structured_result[current_subject] = {}
                                        structured_result[current_subject][
                                            current_exercise
                                        ] = current_content.strip()

                                    # Parse new subject and exercise
                                    parts = line.replace("## Subiect ", "").split(
                                        " - Exercițiul "
                                    )
                                    if len(parts) == 2:
                                        current_subject = parts[0].strip()
                                        current_exercise = parts[1].strip()
                                        current_content = ""
                                elif line.startswith("---"):
                                    # Separator between exercises - save current exercise
                                    if current_subject and current_exercise:
                                        if current_subject not in structured_result:
                                            structured_result[current_subject] = {}
                                        structured_result[current_subject][
                                            current_exercise
                                        ] = current_content.strip()
                                else:
                                    # Add line to current content
                                    current_content += line + " "

                            # Save the last exercise
                            if current_subject and current_exercise:
                                if current_subject not in structured_result:
                                    structured_result[current_subject] = {}
                                structured_result[current_subject][current_exercise] = (
                                    current_content.strip()
                                )

                            solutions = {
                                "gpt_model": model,
                                "temp": temp,
                                "results": structured_result,
                                "barem_url": barem_url,
                                "exam": {
                                    "title": model_name,
                                    "subject": "Informatica",
                                    "categories": [
                                        "Filiera teoretică - Profilul real",
                                    ],
                                },
                            }
                            # Write the structured result to file
                            json.dump(solutions, f, indent=4, ensure_ascii=False)

import json
import time

import requests

from token_manager import TokenManager

# Create a global token manager instance
token_manager = TokenManager()


def send_chat_request(exercise_data, model):
    """Create a structured prompt for exam problems"""

    # Different system prompts based on whether we're processing multiple exercises
    if isinstance(exercise_data, list):
        system_prompt = """You are an expert computer science teacher and problem solver.
        You will receive multiple exercises from a computer science exam. For each exercise:
        1. Start with a clear header indicating the Subject and Exercise number
        2. Provide a thorough analysis and solution
        3. Include code solutions in C++ where applicable
        
        Format your response for each exercise as follows:
        
        ## Subject [X] - Exercise [Y]
        ### Problem Analysis
        [Concise analysis of the problem requirements]
        
        ### Solution Approach
        [Step-by-step solution strategy]
        
        ### Answer
        [Clear, justified final answer]
        
        ### Code Solution (if needed)
        ```cpp
        [Well-commented C++ code]
        ```
        
        ---
        [Next exercise follows the same format]"""

        # Create a combined prompt for all exercises
        exercises_text = ""
        for ex in exercise_data:
            exercises_text += f"\nSubject {ex['subject']} - Exercise {ex['exercise_number']}:\n{ex['content']}\n"

        user_prompt = f"""Please solve the following set of exercises from a computer science exam:

    {exercises_text}

    Provide complete solutions following the structured format for each exercise."""

    else:
        system_prompt = """You are an expert computer science teacher and problem solver. 
        Analyze the given exercise and provide:
        1. A clear explanation of the problem
        2. A step-by-step solution approach
        3. The final answer with justification
        4. If code is required, provide it in a clear, well-commented format, in C++
        
        Format your response in a structured way:
        ### Problem Analysis
        [Your analysis here]
        
        ### Solution Approach
        [Your step-by-step approach]
        
        ### Answer
        [Your final answer with explanation]
        
        ### Code (if applicable)
        ```cpp
        [Your code here]
        ```"""

        user_prompt = f"""Please solve the following exercise:

        Exercise Number: {exercise_data.get("exercise_number", "N/A")}
        Content: {exercise_data.get("content", "")}

        Please provide a complete solution following the structured format."""

    try:
        # Get valid token
        token = token_manager.get_valid_token()
        if not token:
            raise Exception("Failed to obtain valid token")

        # Headers
        headers = {
            "X-UiPath-LlmGateway-RequestingProduct": "testproduct",
            "X-UiPath-LlmGateway-RequestingFeature": "test",
            "X-UiPath-LlmGateway-TimeoutSeconds": "280",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "X-UiPath-LlmGateway-NormalizedApi-ModelName": model,
        }

        # Request body
        payload = {
            "model": model,
            "max_tokens": 8000,
            "n": 1,
            "temperature": temp,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        # Send POST request
        max_retries = 7
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = requests.post(
                    "https://alpha.uipath.com/84be1505-5e68-476a-8e34-250744ee09dc/9921e1d4-1b10-464c-900c-f6cc435494fb/llmgateway_/api/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=250,
                )

                # If successful or error other than 400, break out of retry loop
                if response.status_code != 400:
                    break

                print(
                    f"Received 400 error, retrying request... (Attempt {retry_count + 1}/{max_retries})"
                )
                retry_count += 1
                time.sleep(100)

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    raise

        # Check if request was successful
        response.raise_for_status()

        # Only try to parse JSON if we have content
        if response.text.strip():
            return response.json()
        else:
            print("Received empty response from server")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request error occurred: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        print(f"Response content: {response.text}")
        return None
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None


def process_exercises(data, model, temp=0.0):
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
        # print(content)
        data[f"full_solutions_{model}"] = content

        # Split the content by exercise sections
        exercise_solutions = content.split("---")

        # Create a mapping of solutions
        solutions_map = {}
        for solution in exercise_solutions:
            if not solution.strip():
                continue

            # Extract subject and exercise numbers from the solution header
            header_lines = solution.strip().split("\n")[0]  # Get the first line
            if "## Subject" in header_lines:
                # Extract subject and exercise numbers
                parts = header_lines.replace("## Subject ", "").split(" - Exercise ")
                if len(parts) == 2:
                    subject_num = parts[0].strip()  # I, II, or III
                    exercise_num = parts[1].strip()

                    # Convert Roman numerals to numbers if needed
                    roman_to_arabic = {"I": "1", "II": "2", "III": "3"}
                    subject_num = roman_to_arabic.get(subject_num, subject_num)

                    # Create the key and store the solution
                    subject_key = f"subiectul_{subject_num}"
                    if subject_key in data:
                        if exercise_num in data[subject_key]["exercises"]:
                            data[subject_key]["exercises"][exercise_num][
                                f"solution_{model}"
                            ] = solution.strip()

    return content


# Example usage
if __name__ == "__main__":
    list_of_models = [
        #"E_d_informatica_2025_sp_MI_C_var_model",
        "E_d_Informatica_2024_sp_MI_C_var_model",
        "E_d_Informatica_2023_sp_MI_C_var_05_LRO",
        "E_d_informatica_2022_sp_MI_C_var_05_LRO",
        "E_d_Informatica_2021_sp_MI_C_var_01_LRO",
        "E_d_Informatica_2020_sp_MI_C_var_06_LRO",
    ]

    for model in list_of_models:
        print(f"Processing {model}")
        with open(f"data/{model}/toate_subiectele.json", "r", encoding="utf-8") as f:
            data = json.load(f)

            for temp in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
                solutions = {}
                print(f"Processing {model} with temp {temp}")

                import concurrent.futures

                # Define models and their identifiers
                models = [
                    ("gpt4o", "gpt-4o-2024-08-06"),
                    ("anthropicclaude37sonnet","anthropic.claude-3-7-sonnet-20250219-v1:0"),
                    ("gemini20pro", "gemini-2.0-pro-exp-02-05"),
                    #("o3mini", "o3-mini-2025-01-31"),
                ]

                # Function to process a single model
                def process_model(model_info):
                    model_name, model_id = model_info
                    print(f"Started {model_name}")
                    result = process_exercises(data, model_id, temp)
                    print(f"Finished {model_name}")
                    return model_name, result

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
                        solutions[f"solutions_{model_name}_{temp}"] = result

                filename = f"data/{model}/solutions_temp_{temp}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(solutions, f, indent=4, ensure_ascii=False)

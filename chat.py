
from token_manager import TokenManager
import time
import requests
import json

token_manager = TokenManager()


def send_chat_request(exercise_data, model, temp=0.0):
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
        
        [Next exercise follows the same format]
        
        IMPORTANT: Please provide ALL your responses in Romanian language."""

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
        ### Analiza Problemei
        [Your analysis here]
        
        ### Abordarea Soluției
        [Your step-by-step approach]
        
        ### Răspuns
        [Your final answer with explanation]
        
        ### Cod (dacă este cazul)
        ```cpp
        [Your code here]
        ```
        
        IMPORTANT: Please provide ALL your responses in Romanian language."""

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

import os
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if not content.strip():
            print(f"Skipping empty file: {file_path}")
            return None
        return content
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

# Function to count tokens
def count_tokens(model, content):
    try:
        return model.count_tokens(content).total_tokens
    except ValueError:
        print(f"Error counting tokens: Empty content")
        return 0

def save_response(response_text, file_name, analyzed_files):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = 'ai_responses2'
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{timestamp}_{file_name}.txt")
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write("Analyzed files:\n")
        for analyzed_file in analyzed_files:
            file.write(f"- {analyzed_file}\n")
        file.write("\nAnalysis:\n")
        file.write(response_text)
    print(f"Response saved to {file_path}")

def main():
    genai.configure(api_key='API')

    # Set up the safety settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }

    # Set up the model with safety settings
    model = genai.GenerativeModel('gemini-1.5-flsah', safety_settings=safety_settings)

    # System instruction
    system_instruction = """
    You are a cybersecurity agent tasked with testing and analyzing code for vulnerabilities. 
    Examine the provided code line by line, identifying potential security issues. 
    For each vulnerability found:
    1. Specify the exact line(s) of code affected
    2. Describe the type of vulnerability
    3. Explain potential attack vectors
    4. Rate the severity as Low, Medium, or High
    
    Focus on issues that impact user data confidentiality or integrity, including but not limited to:

    1. Cross-site scripting (XSS)
    2. Cross-site request forgery (CSRF)
    3. SQL injection
    4. Remote code execution
    5. Command injection
    6. Server-side request forgery (SSRF)
    7. Insecure deserialization
    8. XML external entity (XXE) injection
    9. Open redirect vulnerabilities
    10. Clickjacking
    11. Insufficient input validation
    12. Improper error handling and information disclosure
    13. Insecure direct object references (IDOR)
    14. Broken authentication and session management
    15. Security misconfiguration
    16. Sensitive data exposure
    17. Missing or improper access controls
    18. Unvalidated redirects and forwards
    19. Use of components with known vulnerabilities
    20. Insufficient logging and monitoring
    21. Race conditions
    22. Buffer overflow vulnerabilities
    23. Format string vulnerabilities
    24. Integer overflow/underflow
    25. Cryptographic failures (weak algorithms, improper implementation)

    Pay special attention to:
    - Inadequate input sanitization or validation
    - Improper handling of user-supplied data
    - Unsafe use of external libraries or APIs
    - Hardcoded credentials or sensitive information
    - Insecure storage or transmission of sensitive data
    - Lack of proper authentication or authorization checks
    - Potential for privilege escalation
    - Unsafe deserialization of user-controlled data
    - Improper handling of file uploads
    - Inadequate protection against brute-force attacks

    Provide a detailed analysis for each file, and maintain context across multiple files if necessary.
    Consider how vulnerabilities in one file might interact with or compound vulnerabilities in another.
    """

    chat = model.start_chat(history=[])

    # Add system instruction to chat
    chat.send_message(system_instruction)

    # Directory containing the downloaded content
    content_dir = 'downloaded_content'

    total_tokens = 0
    current_prompt = ""
    file_count = 0
    batch_number = 1
    analyzed_files = []

    # Iterate through files in the directory
    for root, dirs, files in os.walk(content_dir):
        for file in files:
            # Skip CSS files
            if file.lower().endswith('.css'):
                print(f"Skipping CSS file: {file}")
                continue

            file_path = os.path.join(root, file)
            file_content = read_file(file_path)
            
            if file_content is None:
                continue  # Skip to the next file if this one is empty or unreadable
            
            file_tokens = count_tokens(model, file_content)

            if total_tokens + file_tokens > 530000:
                # Send the current prompt to the AI
                if current_prompt:
                    print(f"Analyzing batch {batch_number} of {file_count} files...")
                    print("Files in this batch:")
                    for analyzed_file in analyzed_files:
                        print(f"- {analyzed_file}")
                    try:
                        response = chat.send_message(current_prompt)
                        print(response.text)
                        save_response(response.text, f"batch_{batch_number}_analysis", analyzed_files)
                        time.sleep(60)  # 1-minute delay between requests
                    except Exception as e:
                        print(f"Error during AI analysis: {e}")
                        save_response(f"Error during analysis: {e}", f"batch_{batch_number}_error", analyzed_files)

                # Reset for the next batch
                current_prompt = ""
                total_tokens = 0
                file_count = 0
                batch_number += 1
                analyzed_files = []

            # Add the file content to the current prompt
            current_prompt += f"\nFile: {file_path}\n\n{file_content}\n"
            total_tokens += file_tokens
            file_count += 1
            analyzed_files.append(file_path)

    # Send any remaining content
    if current_prompt:
        print(f"Analyzing final batch {batch_number} of {file_count} files...")
        print("Files in this batch:")
        for analyzed_file in analyzed_files:
            print(f"- {analyzed_file}")
        try:
            response = chat.send_message(current_prompt)
            print(response.text)
            save_response(response.text, f"batch_{batch_number}_analysis", analyzed_files)
            time.sleep(60)  # 1-minute delay before final report
        except Exception as e:
            print(f"Error during final batch analysis: {e}")
            save_response(f"Error during final batch analysis: {e}", f"batch_{batch_number}_error", analyzed_files)

    # Request final report
    print("Generating final report...")
    final_prompt = """
    Based on all the code you've analyzed, provide a comprehensive and detailed report of all vulnerabilities found. 
    Include the following for each vulnerability:
    1. File name and specific line numbers
    2. Type of vulnerability
    3. Detailed description of the issue
    4. Potential attack scenarios
    5. Severity rating (Low, Medium, High)
    6. Recommended fixes or mitigation strategies
    
    Organize the report by severity, with the most critical vulnerabilities first. 
    Conclude with an overall assessment of the codebase's security posture.
    """
    try:
        final_response = chat.send_message(final_prompt)
        print(final_response.text)
        save_response(final_response.text, "final_security_report", [])
    except Exception as e:
        print(f"Error generating final report: {e}")
        save_response(f"Error generating final report: {e}", "final_report_error", [])

if __name__ == "__main__":
    main()
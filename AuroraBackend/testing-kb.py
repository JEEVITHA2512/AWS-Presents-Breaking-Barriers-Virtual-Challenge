import boto3
from botocore.exceptions import ClientError
import re

# Create an Amazon Bedrock Runtime client.
brt = boto3.client("bedrock-runtime")

# Set the model ID.
model_id = "meta.llama3-8b-instruct-v1:0"

# Define the document to be used in the Bedrock request.
document_path = "content.txt"  # Update with your actual document path

def sanitize_file_name(file_name):
    # Replace invalid characters with an underscore and collapse multiple whitespaces.
    sanitized_name = re.sub(r'[^\w\s\-\(\)\[\]]', '_', file_name)
    sanitized_name = re.sub(r'\s+', ' ', sanitized_name)
    return sanitized_name

def send_request_to_bedrock(user_message):
    # Prepare the basic conversation message.
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]
    
    # Add the predefined document to the conversation.
    with open(document_path, 'rb') as doc_file:
        document_content = doc_file.read()
    
    # Sanitize the file name
    sanitized_file_name = sanitize_file_name(document_path.split('/')[-1])

    conversation[0]["content"].append({
        "document": {
            "format": "txt",  # Adjust based on your document format
            "name": sanitized_file_name,
            "source": {
                "bytes": document_content
            }
        }
    })

    try:
        # Send the message to the model, using a basic inference configuration.
        response = brt.converse(
            modelId=model_id,
            messages=conversation,
            inferenceConfig={"maxTokens": 500, "temperature": 0.5, "topP": 0.9},
        )

        # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        print("Response from Bedrock:")
        print(response_text)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)

if __name__ == "__main__":
    user_text = input("Enter your text: ")
    send_request_to_bedrock(user_text)

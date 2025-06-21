import boto3
import json
from botocore.exceptions import ClientError

# Create an Amazon Bedrock Runtime client
brt = boto3.client("bedrock-runtime", region_name="us-east-1")  # Ensure correct region

# Set the model ID
model_id = "amazon.nova-micro-v1:0"

def send_request_to_nova(user_message):
    # Prepare the request body
    request_body = {
        "inferenceConfig": {
            "maxTokens": 1000  # Note: Nova uses "maxTokens", not "max_new_tokens"
        },
        "system": [
            {
                "text": "You are an event management robot named Nephele, you will interact with the participants"
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": user_message
                    }
                ]
            }
        ]
    }

    try:
        # Invoke the model with structured payload
        response = brt.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        # Parse and print the response
        response_body = json.loads(response['body'].read())
        response_text = response_body['output']['message']['content'][0]['text']
        print("Response from Amazon Nova Micro:")
        print(response_text)

    except (ClientError, Exception) as e:
        print(f"ERROR: Failed to invoke '{model_id}'. Reason: {e}")
        exit(1)

if __name__ == "__main__":
    user_input = input("Enter your message to Nephele: ")
    send_request_to_nova(user_input)

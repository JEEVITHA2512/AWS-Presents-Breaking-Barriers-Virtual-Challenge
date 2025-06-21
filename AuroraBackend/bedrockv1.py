import boto3
from botocore.exceptions import ClientError

# Create an Amazon Bedrock Runtime client.
# service instance 
brt = boto3.client("bedrock-runtime")

# Set the model ID, e.g., Amazon Titan Text G1 - Express.
model_id = "meta.llama3-8b-instruct-v1:0"

def send_request_to_bedrock(user_message):
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]

    try:
        # Send the message to the model, using a basic inference configuration.
        response = brt.converse(
            modelId=model_id,
            messages=conversation,
            system = [
                {
                    'text':'You are an event management robot named as Nephele, you will interact with the participants'
                },
            ],
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

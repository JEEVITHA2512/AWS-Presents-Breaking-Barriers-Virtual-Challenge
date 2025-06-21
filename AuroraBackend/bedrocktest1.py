import boto3
import json

# Initialize the Amazon Bedrock Runtime client
brt = boto3.client(service_name='bedrock-runtime')

# Prompt the user to enter text
user_input = input("Enter your text: ")

# Prepare the request body
body = json.dumps({
    'prompt': user_input,
    'max_tokens_to_sample': 512,  # Adjust this value according to your needs
    'temperature': 0.7,
    'top_p': 0.9
})

try:
    # Invoke the model with response stream
    response = brt.invoke_model_with_response_stream(
        modelId='meta.llama3-8b-instruct-v1:0',  # LLaMA model ID
        body=body
    )

    # Stream and print the response as it arrives
    stream = response['body']
    if stream:
        for event in stream:
            chunk = event.get('chunk')
            if chunk:
                # Extract and print the text from each chunk
                print(json.loads(chunk['bytes'].decode())['text'], end='')

except Exception as e:
    print(f"ERROR: Unable to invoke model. Reason: {e}")

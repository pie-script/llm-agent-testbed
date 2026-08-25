import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from testbed.tools_naive import naive_get_user

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# --- Step 1: define the tool schema for Gemini ---
naive_get_user_declaration = types.FunctionDeclaration(
    name="naive_get_user",
    description="Look up user information by username.",
    parameters={
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "Username to lookup"},
        },
        "required": ["username"],
    },
)

tools = types.Tool(function_declarations=[naive_get_user_declaration])

prompt = "Look up user 'admin' using the tool and print the exact raw JSON object returned by the tool."

user_message = types.Content(
    role="user",
    parts=[types.Part.from_text(text=prompt)]
)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[user_message],
    config=types.GenerateContentConfig(tools=[tools]),
)

candidate = response.candidates[0]
model_content = candidate.content
part = model_content.parts[0]

# --- Step 3 & 4: Execute tool and return response to model ---
if part.function_call:
    print(f"1. Model requested tool call: {part.function_call.name}")
    print(f"   Args: {dict(part.function_call.args)}")

    # 4a. Execute the real python function
    tool_args = dict(part.function_call.args)
    tool_result = naive_get_user(**tool_args)
    print(f"2. Local tool output: {tool_result}")

    # 4b. Format tool response for Gemini
    tool_response_part = types.Part.from_function_response(
        name=part.function_call.name,
        response={"result": tool_result}
    )
    
    tool_message = types.Content(
        role="user",
        parts=[tool_response_part]
    )

    # 4c. Send the full history back to get the final answer
    follow_up_response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[user_message, model_content, tool_message],
        config=types.GenerateContentConfig(tools=[tools]),
    )

    print("\n3. Final Model Answer:")
    print(follow_up_response.text)
else:
    print("Model answered directly, no tool call:")
    print(part.text)

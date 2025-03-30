import google.generativeai as genai

# Set up API key
genai.configure(api_key="AIzaSyAndTfzBMxowQ7eiiVaP6Mf4re0S6xhBKA")

# Use free model
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# Generate a response
response = model.generate_content("Tell me a joke about robots")

# Print the response
print(response.text)

from openai import OpenAI
client = OpenAI(api_key='sk-proj-mNO5LBCS9VqaQOaSw9qJyjMYGupWRcfTCdi-bxMEsPvavjJA7aPp1UmrHcUTFRRR' \
                        'P5Km5px5lrT3BlbkFJYPOngKue73mnhTZ0eq-oRpQ3LVTHTkNwIA4YIE8FFs366ID2YicQH' \
                        '7BMOMo25NIb0AuA2WAK4A')

question = input("Ask the black soldier fly a question: ")

response = client.responses.create(
    model = 'gpt-4.1-mini',
    instructions = 'You are a black soldier fly in a compost bin in Singapore. Answer the question as if you were the fly,' \
    ' and make the answer informative and engaging, yet concise (Try to keep it under 50 words)',
    input = question
)

print("Black Soldier Fly:", response.output_text)
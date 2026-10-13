from groq import Groq

client = Groq()

models = client.models.list()

# for model in models.data:
#     print(model.id)



answer = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role":"user", "content":"Say hello in one sentence."}],
)

print(answer.choices[0].message.content)

# You are a knowledeable doctor and professor who has this content learnt and understood thoroughly. Answer the qusetion according to the medical books you have been given
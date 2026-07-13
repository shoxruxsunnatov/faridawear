import json

from openai import OpenAI

from main.models import (
    Topic,
    Test,
    TestOption
)

from main.variables import INT_TO_LEVEL


def generate(topic: Topic, level: str, model: str):


    client = OpenAI()
    tests = []

    for _ in range(3):

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"Generate 10 grammar questions {topic.prompt} in real {INT_TO_LEVEL[level]} level. No options, just questions. Respond in simple JSON list. No additional text or markdown."
                },
            ],
            model=model,
            temperature=1,
            top_p=1
        )

        data = json.loads(chat_completion.choices[0].message.content)

        for question in data:

            test = Test.objects.create(
                text=question.strip(),
                topic=topic,
                level=level
            )

            tests.append(test)

    return tests
        

def validate_test(test: Test):
    options = list(test.options.all().values_list("text", flat=True))

    prompt = f"Question: {test.text}\nOptions: {options}\n\n" \
        "Give me only grammatically correct options for this question in JSON list. You're allowed to accept multipe correct options. No additional words or markdown."


    client = OpenAI()

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": prompt
            },
        ],
        model="gpt-4o-mini",
        temperature=1,
        top_p=1
    )

    data = json.loads(chat_completion.choices[0].message.content)
    return data


def generate_options(test: Test):
    options = []

    if test.level >= '5':
        prompt = f"Question body: {test.text}\nThis is a question about English grammar. Provide four options and only one " \
            "answer for this question. Add more words to the incorrect options to make them have similar length to the correct" \
            " answer. Make sure there is not more than one correct answer. Respond in JSON list. Put the answer first in the list." \
            " Make other options incorrect. No additional text or markdown."
    
    else:
        prompt = f"Question body: {test.text}\nThis is a question about English grammar. Provide four options and only one answer for" \
            " this question. Make sure there is not more than one correct answer. Respond in JSON list. Put the answer first in the" \
            " list. Make other options incorrect. No additional text or markdown."

    client = OpenAI()

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": prompt
            },
        ],
        model="gpt-4o-mini",
        temperature=0,
        top_p=1
    )

    data = json.loads(chat_completion.choices[0].message.content)
    
    for option in data:
        test_option = TestOption.objects.create(test=test, text=option.strip())
        options.append(test_option)
    
    test.answer = options[0]
    test.save()

    return options


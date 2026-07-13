import json

from openai import OpenAI

from dictionary.models import (
    Vocabulary,
    VocabularyMeta
)

from main.variables import INT_TO_LEVEL


def generate_examples(vocabulary: Vocabulary) -> bool:

    prompt = f'Write the definition of the word "{vocabulary.text}" and generate 3 simple example sentences using this word. Respond ' \
        'in only JSON format: {"definition", "", "text": "", "sentences": []}. No extra words and markdown needed.'

    client = OpenAI()

    try:
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
        
        vm = VocabularyMeta(vocabulary=vocabulary, sentences=data["sentences"])
        vm.save()

        vocabulary.description = data["definition"]
        vocabulary.save()

        return True
    
    except:
        return False
    

def generate_passage(vocabulary: Vocabulary) -> bool:

    prompt = f'Write an approximately 200 words-long interesting reading passage using the word "{vocabulary.text}" several times. Choose a title for the passage. ' \
        'Write all words and idioms of the passage with Uzbek translation. Do not add pronouns, determiners, prepositions, conjunctions in this list. Respond in only JSON ' \
        'format: {"title": "", "passage": "", "words": [["english", "uzbek"],]}'


    client = OpenAI()

    try:
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
        
        vm = vocabulary.metas.first()

        vm.passage = data["passage"]
        vm.passage_title = data["title"]
        vm.passage_vocabularies = [list(t) for t in set(tuple(lst) for lst in data["words"])]
        vm.save()

        return True
    
    except Exception as e:
        return False


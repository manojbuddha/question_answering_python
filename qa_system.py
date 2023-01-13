import wikipedia
from collections import OrderedDict
import re
from string import punctuation
import sys
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize

import warnings
warnings.catch_warnings()
warnings.simplefilter("ignore")

# Query - Where is the Louvre Museum located?
# Query - when and where is the Louvre Museum located?

# Remove the stop words from the text.
def remove_stopwords(text):
    text = text.split()
    stop_words = set(stopwords.words('english'))
    text = [word for word in text if word.lower() not in stop_words]
    return " ".join(text)

def reformulate_question(query):
    question = re.findall('(who|what|when|where)', query.lower())
    # print(question)
    if len(question) > 1:
        return ["ERROR", "Please ask one question at a time."]
    question = re.match(f'{question[0]}', query.lower())
    question = query[question.span()[0]:question.span()[-1]]
    if question.lower() == 'where':
        if "located" in query:
            match = re.match(rf"(where )(is|are)?([\w ]*) (located)([\w ]*)?", query)
            context = match.groups()[2].strip()
            context = remove_stopwords(context)

            if match.groups()[1] is None:
                match.groups()[1] = "is"
            search_queries = [context+" is located", context+" "+match.groups()[1]+" in",
                              context+" is near", context+" "+match.groups()[1], context]
        else:
            match = re.match(rf"(where )(is|are)?([\w ]*)", query)
            context = match.groups()[2].strip()
            context = remove_stopwords(context)
            search_queries = [context+" is located", context+" "+match.groups()[1]+" in",
                              match.groups()[2]+" is near", context+" "+match.groups()[1], context]


    if question.lower() == 'who':
        search_queries = []
        match = re.match(rf"(who )(is|are|was|were)?([\w ]*)", query)
        if match is not None:
            if match.groups()[1] is None:
                verb = match.groups()[2].split()[0]
                context = " ".join(match.groups()[2].split()[1:]).strip()
                context = remove_stopwords(context)

                search_queries.append(context + " is "+verb)
                search_queries.append(context + " are " + verb)
            else:
                verb = match.groups()[1]
                context = match.groups()[2].strip()
                context = remove_stopwords(context)

                search_queries.append(context + " " + verb)
                search_queries.append(context + " is")
                search_queries.append(context + " are")
            # search_queries = list(set(search_queries))


        print(search_queries)

    return [question]+[context]+search_queries

def get_wikipedia_summaries(search_query):

    pages = wikipedia.search(search_query, results=10)
    # print('pages', len(pages), pages[:20])

    documents = OrderedDict()
    for i, p in enumerate(pages):
        try:
            text = wikipedia.summary(p, sentences=2)
            documents[p] = text
        except Exception as e:
            # print('Could not load:', p)
            pass
    return documents

def get_answer(query):

    search_queries = reformulate_question(query)
    if search_queries[0] == "ERROR":
        return search_queries[1]
    else:
        question = search_queries[0]
        context = search_queries[1].lower().strip()
        search_queries = search_queries[2:]

        for search_query in search_queries:
            search_query = search_query.strip()
            print(f"SearchQuery: {search_query}")
            summaries = get_wikipedia_summaries(search_query)
            for key, value in summaries.items():
                print(f"key: {key}")
                print(f"{value}")
                print()
                for sentence in value.split('.'):
                    sentence_cleaned = re.sub('[^ \w,]', '', sentence)

                    if question.lower() == "where":
                        match = re.match(rf"([\w, ]*)?({context})([\w, ]*)?(in )([\w, ]*)", sentence_cleaned.lower())
                        if match != None:
                            print(match.groups())
                            answer = match.groups()[-1].strip().title()
                            answer = context.capitalize()+" is located in "+answer
                            return answer

                    if question.lower() == "who":
                        print(context,sentence_cleaned)
                        match = re.match(rf"([\w, ]*)?({context})([\w, ]*)?(is )([\w, ]*)", sentence_cleaned.lower())
                        if match != None:
                            print(match.groups())
                            answer = match.groups()[-1].strip().title()
                            answer = context.capitalize()+" is "+answer
                            return answer
    return "I am sorry, I dont know the answer."

query = str(input("*** This is a QA system by YourName. It will try to answer "
                  "questions that start with Who, "
                  "What, When or Where. Enter \"exit\" "
                  "to leave the program."+"\n"+"=?>"))

# Remove punctuation from the query
query = re.sub(rf'[{punctuation}]','', query)
print(query)


while query.lower() != "exit":
    if query != None and query != "":
        answer = get_answer(query)
        print(f"=>{answer}")
    else:
        print(f"=!> Please enter some text.")
    query = str(input("=?>")).strip()

sys.exit("Thank you! Goodbye.")

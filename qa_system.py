# importing required packages

import wikipedia
from collections import OrderedDict
import re
from string import punctuation
import sys
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from string import punctuation
import re

# To ignore warnings produced by wikipedia
import warnings
warnings.catch_warnings()
warnings.simplefilter("ignore")


# Remove the stop words from the text.
def remove_stopwords(text):
    
    text = text.split()
    stop_words = set(stopwords.words('english'))
    # Remove stopwords from the text
    text = [word for word in text if word.lower() not in stop_words]
    return " ".join(text)


# Remove the stop words from the text.
def remove_punctuation(text):

    clean_text = re.sub(rf'[{punctuation}]', '', text)
    return clean_text

# to log queries, wikipedia summaries and debug
def log_data(log_writer, data):
    log_writer.write(data)
    log_writer.write('\n')
    

# Function to reformulate the users query to search queries for wikipedia
def reformulate_question(query):
    
    query = query.lower()
    query = remove_punctuation(query)
    
    # Regex to find if there is who, what, when and where in the user query
    question = re.findall('(who|what|when|where)', query)
    
    # To check if there are more than one question
    if len(question) > 1:
        return ["ERROR", "Please ask one question at a time."]
    
    # To check if the query has more than 2 words
    if len(query.split()) < 2:
        return ["ERROR", "Question is not formatted properly"]    

    if query.split()[0] not in ['who', 'what', 'when', 'where']:
        return ["ERROR", "I cannot answer this kind of questions at the moment."]    
    
    
    question = query.split()[0].strip()
    
    # Performing regex and other operation to formate search queries for 'Who' kind of question.
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


    # Performing regex and other operation to formate search queries for 'what' kind of question.
    if question.lower() == 'what':

        match = re.match(rf"(what )(is|are)?([\w ]*)", query)
        context = match.groups()[2].strip()
        context = remove_stopwords(context)

        if match.groups()[1] is None:
            match.groups()[1] = "is"
        search_queries = [context, context+" is ", context+" "+match.groups()[1] ]

    # Performing regex and other operation to formate search queries for 'when' kind of question.
    if question.lower() == 'when':

        if 'born' in query:

            match = re.match(rf"(when )(is|are|was|were)?([\w ]*) (born)([\w ]*)?", query)
            context = match.groups()[2].strip()
            context = remove_stopwords(context)
            if match.groups()[1] is None:
                match.groups()[1] = "was"
            search_queries = [context+" born on ", context]

        else:
            match = re.match(rf"(when )(is|are|was|were)?([\w ]*)", query)
            context = match.groups()[2].strip()
            context = remove_stopwords(context)
            if match.groups()[1] is None:
                match.groups()[1] = "is"
            search_queries = [context+" on ", context]
            
    # Performing regex and other operation to formate search queries for 'where' kind of question.  
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

    return [question]+[context]+search_queries



# Function to get wikipedia summaries
def get_wikipedia_summaries(search_query):
    log_data(log_writer, "Getting summaries for Formulated search query:")
    log_data(log_writer, search_query)
    # Get search results using Wikipedia API
    pages = wikipedia.search(search_query, results=10)

    documents = OrderedDict()
    log_data(log_writer, "Summaries:")
    for i, p in enumerate(pages):
        try:
            # Get summaries for each page
            text = wikipedia.summary(p, sentences=2)
            documents[p] = text
            
            log_data(log_writer, p)
            log_data(log_writer, text)
        except Exception as e:
            # print('Could not load:', p)
            log_data(log_writer, 'Could not load page')
            pass
    return documents



# Function to extract answer from wikipedia summaries
def get_answer(query):
    # Get search queries based on users input
    search_queries = reformulate_question(query)
    if search_queries[0] == "ERROR":
        return search_queries[1]
    else:
        question = search_queries[0]
        context = search_queries[1].lower().strip()
        search_queries = search_queries[2:]
        # Iterate over each search query
        for search_query in search_queries:
            search_query = search_query.strip()
            # Get wikipedia search engine pages, and summaries for each search query
            summaries = get_wikipedia_summaries(search_query)
            # Iterate over each search result/ summary
            for key, value in summaries.items():             
                # Iterate over each sentence in the summary
                for sentence in sent_tokenize(value):
                    # remove unwanted spaces from the summary.
                    sentence_cleaned = re.sub('[^ \w,]', '', sentence)
                    # Regex and filters to extract answer for question type 'Where'
                    if question.lower() == "where":
                        
                        match = re.match(rf"([\w, ]*)?({context})([\w, ]*)?( in )([\w, ]*)", sentence_cleaned.lower())
                        if match != None:
                            i = sentence_cleaned.lower().split().index('in')+1
                            answer1 = ' '.join(sentence_cleaned.lower().split()[i:i+3]).strip().title()
                            answer = match.groups()[-1].strip().title()
                            if answer.split()[0] != answer1.split()[0]:
                                answer = answer1
                            answer = context.capitalize()+" is located in "+answer
                            return answer+"."
                    # Regex and filters to extract answer for question type 'Who'
                    if question.lower() == "who":

                        if key.split()[-1].replace('(','').replace(')','').strip().lower() in ['film', 'book', 'theater', 'setu']:
                            continue
                            

                        match = re.match(rf"([\w, ]*)?({context})([\w, ]*)?( is|was )([\w, ]*)", sentence_cleaned.lower())
                        if match != None:                           

                            split_term = match.groups()[3].strip()
                            try:
                                i = sentence_cleaned.lower().split().index(split_term)+1
                            except ValueError:
                                continue
                            answer = ' '.join(sentence_cleaned.lower().split()[i:]).strip()
                            # answer = match.groups()[-1].strip()
                            answer = context.capitalize()+" "+split_term+" "+answer
                            return answer+"."
                        
                    # Regex and filters to extract answer for question type 'What'
                    if question.lower() == "what":

                        match = re.match(rf"(a )?({context})( is )([\w, ]*)", sentence_cleaned.lower())
                        if match != None:

                            answer = match.groups()[-1].strip()
                            answer = context.title()+" is "+answer
                            return answer+"."
                    # Regex and filters to extract answer for question type 'When'                        
                    if question.lower() == "when":
                        # print(sentence_cleaned.lower())
                        
                        if 'born' in query:
                            if 'born' in sentence_cleaned.lower():
                                match = re.match(rf"({context})([\w, ]*)( born )([\w, ]*)", sentence_cleaned.lower())
                                if match != None:
                                    # Extract date
                                    bday = match.groups()[3]
                                    bday = remove_punctuation(bday)
                                    bday = bday.split()[:7]
                                    bday = [word.title() for word in bday if word.isnumeric() or word in months] 
                                    bday = ' '.join(bday)
                                    if len(bday) < 2:
                                        continue
                                    answer = context.title()+" was born on "+bday
                                    return answer+"."
                        else:
                            match = re.match(rf"({context})([\w, ]*)( on )([\w, ]*)", sentence_cleaned.lower())
                            if match != None:
                                # Extract date
                                date = match.groups()[3].split()[:5]
                                date = [word.title() for word in date if word.isnumeric() or word in months] 
                                date = ' '.join(date)
                                if len(date) < 2:
                                    continue
                                # answer = match.groups()[-1].strip()
                                answer = context.title()+" is on "+date
                                return answer+"."                        
                        
    return "I am sorry, I dont know the answer."



months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']

query = str(input(f"*** This is a QA system developed by Manoj Buddha. It will try to answer "
                  "questions that start with Who, "
                  "What, When or Where. Enter \"exit\" "
                  "to leave the program."+"\n"+"=?>"))

# Remove punctuation from the query

query = remove_punctuation(query)

# Remove multiple spaces from user query
query = re.sub(r'[ ]+',' ',query)

#  Open 'log.txt' in write mode to save user queries, search engine summaries and answer provided by the system
log_writer = open('log.txt', 'w', encoding='utf-8')
log_data(log_writer, "Query:")
log_data(log_writer, query)


# Loop to get input from user until the user inputs 'exit'
while query.lower() != "exit":
    try:
        if query != None and query != "":
            # Function to retrieve answer to user query using wikipedia search engine
            answer = get_answer(query)
            print(f"=>{answer}")
            log_data(log_writer, "Answer:")
            log_data(log_writer, answer)
        else:
            log_data(log_writer, "Answer:")
            print(f"=!> Please enter some text.")
            log_data(log_writer, "=!> Please enter some text.")
        log_data(log_writer, "**********"*5)
        query = str(input("=?>")).strip()
        query = remove_punctuation(query)
        query = re.sub(r'[ ]+',' ',query)
        log_data(log_writer, "Query:")
        log_data(log_writer, query)
    except:
        log_data(log_writer, "Unexpected exception while running the code")
        print("I am sorry i am not able to process this request!!")
        query = str(input("=?>")).strip()
        query = remove_punctuation(query)
        query = re.sub(r'[ ]+',' ',query)
        log_data(log_writer, "Query:")
        log_data(log_writer, query)        

# Close the writer object        
log_writer.close()
print("Thank you! Goodbye.")



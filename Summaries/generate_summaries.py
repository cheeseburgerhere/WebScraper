from enum import Enum
import pandas as pd

from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage


load_dotenv()

class ComplexityLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class ReadingTime(Enum):
    ONE_MINUTE = "1 minute"
    TWO_MINUTES = "2 minutes"
    FIVE_MINUTES = "5 minutes"

#promts
templateStory="""If the given information is not enough, say "I don't know".
You are an editor for the news articles and you give summaries accordingly to the given template. With an academic tone and language. 
Here is the construction of your summary:

Title

Abstract: Here you describe the article with one sentence.
Key Words: Some keywords about the context of the article.
Main Summary: Deep dive into the article make a complete summary here.
Results: In this section explain what might be the consequences of this event.
Conclusion: Make a summary of the main points of the article.
Extra: Evaluate the relevance of the news to the audience or community.

Here is the input to give output from:
Article: {article}
Summary:
"""
templateBulletPoint="""If the given information is not enough, say "I don't know".
You are an editor for the news articles and you give summaries based on the template given below.

These are some bullet points you should use in the summary:

-Identify the primary facts - who, what, when, why, and how.
-Look for background information that provides a broader understanding of the topic or event.
-Explore the potential implications or consequences of the event or topic discussed.
"""
extraBulletPoints="""-Analyze the tone of the article and consider any potential biases in the reporting.
-Evaluate the relevance of the news to the audience or community.
-Assess the credibility and diversity of sources used in the article"""
bulletPointArticlePart="""

Here is the input to give output from:
Article: {article}
Summary:"""


def generate_summaries(news_dataframe: pd.DataFrame, complexity_level: ComplexityLevel, reading_time: ReadingTime) -> pd.DataFrame:
    if news_dataframe.empty:
        raise ValueError
    if (news_dataframe.columns.size<4):
        raise ValueError
    
    #decides the output style
    temperature : float=0
    if(complexity_level==ComplexityLevel.HARD):
        temperature=0.3
        template=templateStory
    else:
        if(ReadingTime.ONE_MINUTE==reading_time):
            template=templateBulletPoint+bulletPointArticlePart
        else:
            template=templateBulletPoint+extraBulletPoints+bulletPointArticlePart
            if(reading_time==ReadingTime.TWO_MINUTES):
                temperature=0.3

    prompt_template = PromptTemplate(input_variables=["article"], template=template)

    llm : ChatOpenAI=ChatOpenAI(temperature=temperature , model="gpt-3.5-turbo-1106")

    #MEMO openai api does not allow more than 3 requests in one minute on free accounts
    output=[]

    #there is a token limit in llm so this loop ensures input stays between the limit by just sending one at a time
    for i in range(0,len(news_dataframe)):
        #when working on csv file it gets longer by one column so change this index
        doc = news_dataframe.iloc[i,3]
        messages=[HumanMessage(content=prompt_template.format(article=doc))]
        outputMessage=llm.invoke(messages).content
        
        #if content is empty llm will answer "I don't know." this ensures its warning
        if(outputMessage=="I don't know."):
            raise ValueError("Content of the article is not compatible for summary")
        
        output.append(outputMessage)
    
    temp:pd.DataFrame=news_dataframe.iloc[:,0:-1]
    outputToSeries=pd.Series(output)
    outputToSeries.name="Summaries"
    df=pd.merge(temp,outputToSeries,right_index=True,left_index=True)


    #print(df)
    return df

# df : pd.DataFrame = scrape_news("10 days ago","world",3)
# print(df)
# generate_summaries(df ,ComplexityLevel.HARD , ReadingTime.TWO_MINUTES)

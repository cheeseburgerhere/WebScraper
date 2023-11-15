from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_transformers import BeautifulSoupTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_extraction_chain
import pandas as pd
import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from googleapiclient.discovery import build

#google keys
my_api_key : str = 'YOUR API KEY'
my_cse_id : str = "YOUR SEARCH ENGİNE ID"

#openai key
load_dotenv()
llm=ChatOpenAI(temperature=0)

#region helpfunctions

def __google_search(search_term:str, api_key:str, cse_id:str, **kwargs): #gets the links
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    
    links=[]
    for i in res["items"]:
        links.append(i["link"])

    return links


def __webPull(link:list): #pulls data fram website
    
    loader=AsyncChromiumLoader(link)
    docs=loader.load()

    bs_transformer=BeautifulSoupTransformer()
    docs_transformed=bs_transformer.transform_documents(
        docs,tags_to_extract=[ "h2","h3","div","span","time" ] 
    )
    splitter=RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)
    splits = splitter.split_documents(docs_transformed)
    
    return splits

#gives data to llm
def __extract(content:str,schema:dict,llm:ChatOpenAI):
    return create_extraction_chain(schema=schema,llm=llm).run(content)

def __parseDate(date_string:str): #pareses the dates to the correct form
    try:
        current_datetime = datetime.datetime.now()

        if 'ago' in date_string:

            time_difference = int(date_string.split()[0])
            parsed_date = current_datetime - relativedelta(days=time_difference)         
        else:
            parsed_date = parser.parse(date_string, default=current_datetime)

        return parsed_date
    except:
        return None


def __list_to_df(input:list,site:str,reqDate:datetime.datetime,num): #creates the dataframe
    names=[]
    dates=[]
    siteN=[]
    for obj in input:
        if (obj["article_date"]!=None):

            date=__parseDate(obj["article_date"])
            if date is not None:  

                date = date.replace(tzinfo=None)
                reqDate = reqDate.replace(tzinfo=None)

                if (date >= reqDate): 

                    if (len(names)>=num):
                        break

                    names.append(obj["article_title"])
                    dates.append(obj["article_date"])  
                    siteN.append(site)

    df=pd.DataFrame({
        "Names":names,
        "Dates":dates,
        "Site":siteN
    })
    return df
#endregion helpfunctions 

def scrape_news(time_range : str, selected_topics : str, num_articles : int):
    res=__google_search(selected_topics, my_api_key, my_cse_id)
    
    medium= "https://medium.com/tag/"+selected_topics+"/recommended"
    reuters= "https://www.reuters.com/site-search/?query="+selected_topics+"&sort=newest&offset=0" #tags:h3,time
    bbc= "https://www.bbc.com/news/technology"

    links = [res[0]]
    linkSplit=res[0].split(".")
    linkName=linkSplit[1]
    
    splits = __webPull(link=links)
    lastDate = __parseDate(time_range)

    schema={
        "properties":{
            "article_title":{"type":"string"},
            "article_date":{"type":"string"},
        },
        "required":["article_title","article_date"]
    }

    endDf = pd.DataFrame()
    for split in splits:
        extraction=__extract(split, schema=schema, llm=llm) #type list
        
        df = __list_to_df(extraction, linkName, reqDate=lastDate, num=num_articles)
        endDf = pd.concat([endDf,df])

        if len(endDf) >= num_articles:
            break

    if len(endDf) < num_articles:
        print("Not enough articles in the timespan!")
    
    print(endDf)
    return endDf

scrape_news(time_range="10 days ago",selected_topics="technology news",num_articles=2)

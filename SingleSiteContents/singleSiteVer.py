from dotenv import load_dotenv
import pandas as pd

from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_transformers import BeautifulSoupTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_extraction_chain

from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from langchain.schema.document import Document

#openai key
load_dotenv()
llm=ChatOpenAI(temperature=0)

#region helpfunctions
def __webPull(link:list,tags:list, split:bool=True, unwanted:list=[]): #pulls data fram website
    loader=AsyncChromiumLoader(link)
    docs=loader.load()

    bs_transformer=BeautifulSoupTransformer()
    docs_transformed=bs_transformer.transform_documents(
        docs,tags_to_extract=tags,unwanted_tags=unwanted
    )
    if split:
        splitter=RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)
        splits= splitter.split_documents(docs_transformed)
        return splits
    else:
        return docs_transformed
    
#gives data to llm
def __extract(content:str,schema:dict,llm:ChatOpenAI):
    return create_extraction_chain(schema=schema,llm=llm).run(content)

def __parseDate(date_string:str): #pareses the dates to the correct form
    try:
        current_datetime = datetime.now()
        tempList=date_string.split(" ")
        if(tempList[0]=="Published"):
            sum=""
            for i in range(1,len(tempList)):
                sum+=tempList[i]+" "
            
            date_string=sum[:-1]

        if 'ago' in date_string:

            time_difference = int(date_string.split()[0])
            parsed_date = current_datetime - relativedelta(days=time_difference)         
        else:
            parsed_date = parser.parse(date_string, default=current_datetime)

        return parsed_date
    except:
        return None


def __list_to_df(input:dict, sites : dict, reqDate:datetime, num): #creates the dataframe
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
                    if (obj["article_title"] in sites):
                        names.append(obj["article_title"])
                        dates.append(obj["article_date"])  
                        siteN.append(sites[obj["article_title"]])
    df=pd.DataFrame({
        "Names":names,
        "Dates":dates,
        "Site":siteN
    })
    return df


def inputSplitter(input:str): #sometimes scraped data comes without spaces and this function adds spaces accordingly
    if(input == None):
        return None
    i:int=0
    prevPointer : int=0
    titlesString=""
    while(i<len(input)-1):
        c:chr=input[i]
        afc: chr=input[i+1]
        if((c>='A' and c<='Z' and afc>='a' and afc <='z')):
            temp=input[prevPointer:i]
            spaceString=" "

            if(len(temp)<1):
                i+=1
                continue

            if(temp[-1]==" "):
                spaceString=""
            if(temp[:9]=="Published"):
                titlesString+=temp[:9] +" "+ temp[9:]+spaceString
            else:
                titlesString+=temp + spaceString
            
            prevPointer=i
        i+=1
    return titlesString

def linkSplitter(links:str):
    linksDic={}
    links = links.split(")")

    for linkAdress in links:
        #print(links)
        temp=linkAdress
        linkAdress=temp[1:]
        temp=linkAdress.split("(")
        if(len(temp[0])>2 and len(temp)>1):
            linksDic[temp[0][:-1]]=temp[1]
                
    return linksDic

def contentsPuller(df:pd.DataFrame): #gets the article content
    siteLinks:list=df.iloc[:,2].to_list()

    pull=__webPull(link=siteLinks,tags=["div","p"], split=False, unwanted=["h3","span","a","img","li","ul"])
    content = []
    for c in pull:
        content.append(inputSplitter(c.page_content))
        #sometimes script can't acces the website so if that happens we need to try again
        #when that error happens BeautifulSoup will give an error but there should be no problem in the output
        if(len(c.page_content)<2):
            return contentsPuller(df)

    df:pd.Series=pd.Series(content)
    df.name="Contents"
    return df

#endregion helpfunctions 

def scrape_news(time_range : str, selected_topics : str, num_articles : int):
    
    lastDate = __parseDate(time_range)
    
    if type(selected_topics) != str:
        raise TypeError
    if num_articles<=0:
        raise IndexError
    if selected_topics == None or len(selected_topics) == 0:
        raise TypeError
    if(lastDate== None):
        raise TypeError
    
    endDf:pd.DataFrame=pd.DataFrame()
    i: int = 1
    schema={
        "properties":{
            "article_title":{"type":"string"},
            "article_date":{"type":"string"},
        },
        "required":["article_title","article_date"]
    }
    while(len(endDf)<num_articles and i<11):
        bbc="https://www.bbc.co.uk/search?q="+selected_topics+"&d=NEWS_GNL&seqId=6dacb860-94ed-11ee-bf63-d95cb16fc5af&page="+str(i)

        links = [bbc]
        splits = __webPull(link=links,tags=["h3","div","span"],split=True)
        linksPuller : Document=__webPull(link=links,tags=["a"],split=True)

        linksDic: dict = linkSplitter(linksPuller[0].page_content[1091:])
        #print(linksDic)
        content = inputSplitter(splits[0].page_content)
        #print(content)
        extraction=__extract(content, schema=schema, llm=llm) #type list
        #print(extraction)
        df = __list_to_df(input=extraction, sites=linksDic, reqDate=lastDate, num=num_articles)
        endDf = pd.concat([endDf,df])

        i+=1
    
    if len(endDf) < num_articles:
        print("Not enough articles in the timespan!")


    articleContent=contentsPuller(endDf)
    endDf=pd.merge(df,articleContent,right_index=True,left_index=True)
    
    print(endDf)
    return endDf

scrape_news(time_range="40 days ago",selected_topics="war",num_articles=3)
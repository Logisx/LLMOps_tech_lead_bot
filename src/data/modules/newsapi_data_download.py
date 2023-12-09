import os
import requests
from datetime import datetime
from pathlib import Path
from typing import List
from dataclasses import dataclass

from config.paths import DATA_RAW_DIR
from src.utils.logging import logger
from src.utils.file_management import FileManagement
from src.utils.configuration_management import ConfigurationManagement

@dataclass
class NewsapiNews:
    author: str
    title: str
    description: str
    content: str
    url: str
    publishedAt: datetime


class NewsapiDataDownload():
    def __init__(self, api_url: str = "https://newsapi.org/v2/top-headlines"):
        logger.info("Initializing NewsapiDataDownload")
        self.__api_url = api_url
        self.__newsapi_request_params = ConfigurationManagement.get_newsapi_request_params()
        self.__newsapi_download_params = ConfigurationManagement.get_news_download_params()
        try: 
            self.__api_key = ConfigurationManagement.get_newsapi_api_key()
        except Exception as e:
            logger.error(f"Missing Newsapi API key: {e}")
            raise e


    def download_news(self) -> Path:
        logger.info("Downloading news from NewsAPI")
        list_of_news = []
        for request in range(self.__newsapi_download_params.num_requests):
            query = self.__newsapi_download_params.queries_list[request]
            logger.info(f"Request {request+1}: query <<< {query} >>>")
            news_batch = self.__fetch_batch_of_news(query)
            list_of_news.extend(news_batch)
        
        logger.info("Saving news to json")
        news_filepath = Path(DATA_RAW_DIR, f"newsapi_news_{self.__newsapi_download_params.from_date}_to_{self.__newsapi_download_params.to_date}.json")
        self.__save_news_to_json(list_of_news, news_filepath)
        logger.info(f"News from NewsAPI downloaded and saved to {news_filepath}")
        return news_filepath
    

    def __fetch_batch_of_news(self, query: str) -> List[NewsapiNews]:
        params = {
            "q": query,
            "language": self.__newsapi_request_params.language,
            "sortBy": self.__newsapi_request_params.sort_by,
            "pageSize": self.__newsapi_request_params.page_size,
            "page": self.__newsapi_request_params.page,
            "apiKey": self.__api_key
        }
        response = requests.get(self.__api_url, params=params)
        if response.status_code == 200:
            logger.info("News batch fetched successfully")
            news_list = []
            for article in response.json()["articles"]:
                news_list.append(
                    NewsapiNews(
                        author=article["author"],
                        title=article["title"],
                        description=article["description"],
                        content=article["content"],
                        url=article["url"],
                        publishedAt=article["publishedAt"]
                    )
                )
            return news_list
        else:
            logger.error("Failed to fetch news")
            logger.error("Response status code: ", response.status_code())
            raise Exception("Failed to fetch news")


    def __save_news_to_json(self, news_list: List[NewsapiNews], file_path: Path):
        news_data = [
            {
                "author": news.author,
                "title": news.title,
                "description": news.description,
                "content": news.content,
                "url": news.url,
                "publishedAt": news.publishedAt
            }
            for news in news_list
        ]
        FileManagement.save_to_json(news_data, file_path)
        

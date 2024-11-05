# back-edn-axioma

## Enpoints
1. articles
    - hay que devolver una lista de articles
    - Ejemplo:
    ```json
    'articles': [
          {
            'source': {'id': 'cnn', 'name': 'CNN'},
            'author': 'John Doe',
            'title': 'Global Markets React to Economic Uncertainty',
            'description':
                'Stock markets around the world faced turbulence as investors reacted to unexpected economic data.',
            'url': 'https://cnn.com/markets-news',
            'urlToImage':
                'https://credentwealth.com/wp-content/uploads/2024/04/AdobeStock_766381554-scaled.jpeg',
            'publishedAt': '2023-10-10T12:34:00Z',
            'content':
                'In an unexpected turn, markets across Europe, Asia, and the Americas reacted sharply...',
          },
          {
            'source': {'id': 'reuters', 'name': 'Reuters'},
            'author': 'Jane Smith',
            'title': 'Tech Giants Report Record Profits Amid Rising Inflation',
            'description':
                'Major tech firms reported record-breaking quarterly profits despite inflation concerns.',
            'url': 'https://reuters.com/tech-news',
            'urlToImage':
                'https://s4.reutersmedia.net/resources/r/?m=02&d=20231010&t=2&i=1694738728&w=780&fh=&fw=&ll=&pl=&sq=&r=LYNXMPEE9D0A7',
            'publishedAt': '2023-10-10T16:45:00Z',
            'content':
                'With tech stocks leading the charge, major indices in the U.S. have been climbing steadily...',
          },
          {
            'source': {'id': 'bbc', 'name': 'BBC'},
            'author': 'Michael Green',
            'title': 'Climate Change Summit: Key Takeaways',
            'description':
                'Global leaders met to discuss critical climate action at the annual climate change summit.',
            'url': 'https://bbc.com/climate-change',
            'urlToImage':
                'https://ichef.bbci.co.uk/news/1024/branded_news/3E13/production/_122018412_climate_change.jpg',
            'publishedAt': '2023-10-10T14:20:00Z',
            'content':
                'In a historic meeting, representatives from over 100 nations gathered to tackle climate change...',
          },
        ]
    ```
    - ademas de cada artiuculo debo madnar:
        - sentiment_category
        - sentiment_score
    - que se pueda buscar por palabras clave usando el chromadb parapoder manadral lista de articulos que contengan esa palabra clave

2. analysis
    - hay que devolver una lista de analisis
    ```json
    // parametro: source: "CNN", interval: 3, unit: "months"
    {
        "source_id": 1,
        "source_name": "CNN",
        "news_history": [
        {
            "date": "2021-01-01",
            "news_count": 10
        },
        {
            "date": "2021-01-02",
            "news_count": 10
        }
        ],

        "news_perception":[
        {
            "date": "2021-01-01",
            "positive_sentiment_score": 0.5,
            "negative_sentiment_score": 0.5
        },
        {
            "date": "2021-01-02",
            "positive_sentiment_score": 0.2,
            "negative_sentiment_score": 0.8
        }
        ],
        "news_count": 20,
        "sources_count": 5,
        "historic_interval": 3,
        "historic_interval_unit": "months", //days, weeks, months, years
        "general_perception": {
        "positive_sentiment_score": 0.4,
        "negative_sentiment_score": 0.6
        }
    }
```
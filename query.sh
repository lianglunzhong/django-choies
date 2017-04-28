curl -XGET 'http://localhost:9200/choiescom/product/_search?pretty=true' -d '{
    "query":{ 
        "filtered": {
            "query": {
                "match_all": {}
            },
            "filter": {
                "terms": { "category_id": [2,3] }
            }
            }
        }
}'

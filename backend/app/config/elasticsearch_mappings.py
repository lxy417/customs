"""
Elasticsearch 索引映射配置
统一管理所有 Elasticsearch 索引的映射定义
"""

# 海关数据索引映射
CUSTOMS_DATA_MAPPING = {
    "mappings": {
        "properties": {
            "海关编码": {"type": "keyword"},
            "编码产品描述": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "编码产品描述本国语言": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "日期": {"type": "date", "format": "yyyy-MM-dd"},
            "月度": {"type": "date", "format": "yyyyMM"},
            "进口商": {
                "type": "keyword",
                "fields": {
                    "text": {
                        "type": "text",
                        "analyzer": "standard"
                    }
                }
            },
            "进口商所在国家": {"type": "keyword"},
            "进口商本地语言": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "出口商": {
                "type": "keyword",
                "fields": {
                    "text": {
                        "type": "text",
                        "analyzer": "standard"
                    }
                }
            },
            "出口商所在国家": {"type": "keyword"},
            "出口商本地语言": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "数量单位": {"type": "keyword"},
            "数量": {"type": "float"},
            "申报数量": {"type": "float"},
            "重量单位": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "净重": {"type": "float"},
            "毛重": {"type": "float"},
            "公吨": {"type": "float"},
            "金额美元": {"type": "float"},
            "美元数量计单价": {"type": "float"},
            "美元重量计单价": {"type": "float"},
            "币种": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "本国币种金额": {"type": "float"},
            "合同金额": {"type": "float"},
            "详细产品名称": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "详细产品名称本国语言": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "产品规格型号品牌": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "产品规格型号品牌本国语言": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "提单号": {"type": "keyword"},
            "关单号": {"type": "keyword"},
            "贸易方式": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "成交方式": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "运输方式": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "当地港口": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "国外港口": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "中转国": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "数据来源": {"type": "keyword"},
            "数据获取网站": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    }
}

# 需要使用 keyword 子字段进行排序的 text 类型字段
TEXT_FIELDS_WITH_KEYWORD = [
    '编码产品描述', 
    '详细产品名称',
    '编码产品描述本国语言',
    '详细产品名称本国语言',
    '产品规格型号品牌',
    '产品规格型号品牌本国语言',
    '进口商本地语言',
    '出口商本地语言',
    '重量单位',
    '币种',
    '贸易方式',
    '成交方式',
    '运输方式',
    '当地港口',
    '国外港口',
    '中转国'
]

# 默认返回字段
DEFAULT_SOURCE_FIELDS = [
    "海关编码", "编码产品描述", "日期", "进口商", "进口商所在国家", 
    "出口商", "出口商所在国家", "数量单位", "数量", "公吨", 
    "金额美元", "详细产品名称", "提单号", "数据来源", "关单号"
]
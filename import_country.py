# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

import time, datetime

from django.db import connection

from core.models import Country


countrys = [
("GB",  "UNITED KINGDOM" , "英国",  303,),
("US",  "UNITED STATES"  , "美国",  502,),
("CA",  "CANADA" , "加拿大", 501,),
("JP",  "JAPAN"  , "日本",  116,),
("DE",  "GERMANY", "德国",  304,),
("FR",  "FRANCE" , "法国",  305,),
("AD",  "ANDORRA", "安道尔共和国",  314,),
("BE",  "BELGIUM", "比利时", 301,),
("DK",  "DENMARK", "丹麦",  302,),
("FI",  "FINLAND", "芬兰",  318,),
("IS",  "ICELAND", "冰岛",  322,),
("IE",  "IRELAND", "爱尔兰", 306,),
("IT",  "ITALY"  , "意大利", 307,),
("MC",  "MONACO" , "摩纳哥", 325,),
("NO",  "NORWAY" , "挪威",  326,),
("PT",  "PORTUGAL"   , "葡萄牙", 311,),
("ES",  "SPAIN"  , "西班牙", 312,),
("SE",  "SWEDEN" , "瑞典",  330,),
("CH",  "SWITZERLAND", "瑞士",  331,),
("VA",  "VATICAN CITY STATE(HOLY SEE)"   , "梵蒂冈", 356,),
("AU",  "AUSTRALIA"  , "澳大利亚",    601,),
("AT",  "AUSTRIA", "奥地利", 315,),
("MT",  "MALTA"  , "马耳他", 324,),
("GR",  "GREECE" , "希腊",  310,),
("KR",  "SOUTH KOREA", "韩国",  133,),
("TW",  "TAIWAN" , "台湾",  0,),
("SG",  "SINGAPORE"  , "新加坡", 132,),
("NZ",  "NEW ZEALAND", "新西兰", 609,),
("CZ",  "CZECH REPUBLIC" , "捷克",  352,),
("PL",  "POLAND" , "波兰",  327,),
("CY",  "CYPRUS" , "塞浦路斯",    108,),
("AM",  "ARMENIA", "亚美尼亚",    338,),
("LT",  "LITHUANIA"  , "立陶宛", 336,),
("LU",  "LUXEMBOURG" , "卢森堡", 308,),
("MD",  "MOLDOVA", "摩尔多瓦",    343,),
("UA",  "UKRAINE", "乌克兰", 347,),
("RO",  "ROMANIA", "罗马尼亚",    328,),
("RU",  "RUSSIAN FEDERATION" , "俄罗斯联邦",   344,),
("AL",  "ALBANIA", "阿尔巴尼亚",   313,),
("BA",  "BOSNIA AND HERZEGOVINA" , "波斯尼亚和黑塞哥维那",  355,),
("HR",  "CROATIA", "克罗地亚",    351,),
("MK",  "MACEDONIA"  , "马其顿", 354,),
("RS",  "SERBIA" , "塞尔维亚",    358,),
("TR",  "TURKEY" , "土耳其", 137,),
("MN",  "MONGOLIA"   , "蒙古",  124,),
("KH",  "CAMBODIA"   , "柬埔寨", 107,),
("ID",  "INDONESIA"  , "印度尼西亚",   112,),
("MY",  "MALAYSIA"   , "马来西亚",    122,),
("MM",  "MYANMAR", "缅甸",  106,),
("TH",  "THAILAND"   , "泰国",  136,),
("PH",  "PHILIPPINES", "菲律宾", 129,),
("IL",  "ISRAEL" , "以色列", 115,),
("JO",  "JORDAN" , "约旦",  117,),
("OM",  "OMAN"   , "阿曼",  126,),
("QA",  "QATAR"  , "卡塔尔", 130,),
("SA",  "SAUDI ARABIA"   , "沙特阿拉伯",   131,),
("AE",  "UNITED ARAB EMIRATES"   , "阿拉伯联合酋长国",    138,),
("AR",  "ARGENTINA"  , "阿根廷", 402,),
("BR",  "BRAZIL" , "巴西",  410,),
("CL",  "CHILE"  , "智利",  412,),
("CR",  "COSTA RICA" , "哥斯达黎加",   415,),
("PA",  "PANAMA" , "巴拿马", 432,),
("PY",  "PARAGUAY"   , "巴拉圭", 433,),
("PE",  "PERU"   , "秘鲁",  434,),
("UY",  "URUGUAY", "乌拉圭", 444,),
("MX",  "MEXICO" , "墨西哥", 429,),
("HU",  "HUNGARY", "匈牙利", 321,),
("CN",  "CHINA"  , "中国",  0,),
("NL",  "NETHERLANDS", "荷兰",  309,),
("AF",  "AFGHANISTAN", "阿富汗", 101,),
("AG",  "ANTIGUA AND BARBUDA", "安提瓜和巴布达", 401,),
("AI",  "ANGUILLA"   , "安圭拉岛",    303,),
("GS",  "THE SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS"   , "南乔治亚岛和南桑德韦奇岛",    303,),
("AO",  "ANGOLA" , "安哥拉", 202,),
("AQ",  "ANTARCTICA" , "南极洲", 0,),
("AS",  "AMERICAN SAMOA" , "美国萨摩亚",   502,),
("AW",  "ARUBA"  , "阿鲁巴岛",    403,),
("AX",  "ALAND ISLANDS"  , "奥兰群岛",    318,),
("AZ",  "AZERBAIJAN" , "阿塞拜疆",    339,),
("BB",  "BARBADOS"   , "巴巴多斯",    405,),
("BD",  "BANGLADESH" , "孟加拉国",    103,),
("BF",  "BURKINA FASO"   , "布基纳法索",   251,),
("BH",  "BAHRAIN", "巴林",  102,),
("BI",  "BURUNDI", "布隆迪", 205,),
("BJ",  "BENIN"  , "贝宁",  203,),
("BM",  "BERMUDA", "百慕大群岛",   504,),
("BN",  "BRUNEI DARUSSALAM"  , "文莱达鲁萨兰国", 105,),
("BO",  "BOLIVIA", "玻利维亚",    408,),
("BS",  "BAHAMAS", "巴哈马", 404,),
("BT",  "BHUTAN" , "不丹",  104,),
("BV",  "BOUVET ISLAND"  , "布韦岛", 326,),
("BW",  "BOTSWANA"   , "博茨瓦纳",    204,),
("BY",  "BELARUS", "白俄罗斯",    340,),
("BZ",  "BELIZE" , "伯利兹", 406,),
("CC",  "COCOS (KEELING) ISLANDS", "科科斯(基林)群岛",   601,),
("CD",  "CONGO(THE DEMOCRATIC REPUBLIC OF)"  , "刚果民主共和国", 213,),
("CF",  "CENTRAL AFRICAN REPUBLIC"   , "中非共和国",   209,),
("CG",  "CONGO(THE REPUBLIC OF)" , "刚果",  252,),
("CI",  "COTE D'IVOIRE"  , "科特迪瓦",    223,),
("CK",  "COOK ISLANDS"   , "库克群岛",    602,),
("CM",  "CAMEROON"   , "喀麦隆", 206,),
("CO",  "COLOMBIA"   , "哥伦比亚",    413,),
("CU",  "CUBA"   , "古巴",  416,),
("CV",  "CAPE VERDE" , "佛得角", 208,),
("CX",  "CHRISTMAS ISLAND"   , "圣诞岛", 601,),
("DJ",  "DJIBOUTI"   , "吉布提", 214,),
("DM",  "DOMINICA"   , "多米尼加",    414,),
("DO",  "DOMINICAN REPUBLIC" , "多米尼加共和国", 418,),
("DZ",  "ALGERIA", "阿尔及利亚",   201,),
("EC",  "ECUADOR", "厄瓜多尔",    419,),
("EG",  "EGYPT"  , "埃及",  215,),
("EH",  "WESTERN SAHARA" , "西撒哈拉",    245,),
("ER",  "ERITREA", "厄立特里亚",   258,),
("ET",  "ETHIOPIA"   , "埃塞俄比亚",   217,),
("FJ",  "FIJI"   , "斐济",  603,),
("FK",  "FALKLAND ISLANDS (MALVINAS)", "福克兰群岛（马尔维纳斯群岛）",  303,),
("FM",  "MICRONESIA  FEDERATED STATES OF", "密克罗尼西亚联邦",    620,),
("FO",  "FAROE ISLANDS"  , "法罗群岛",    357,),
("GA",  "GABON"  , "加蓬",  218,),
("GD",  "GRENADA", "格林纳达",    421,),
("GE",  "GEORGIA", "格鲁吉亚",    337,),
("GF",  "FRENCH GUIANA"  , "法属圭亚那",   420,),
("GG",  "GUERNSEY"   , "格恩西岛",    303,),
("GH",  "GHANA"  , "加纳",  220,),
("GI",  "GIBRALTAR"  , "直布罗陀",    320,),
("GL",  "GREENLAND"  , "格陵兰岛",    503,),
("GM",  "GAMBIA" , "冈比亚", 219,),
("GN",  "GUINEA" , "几内亚", 221,),
("GP",  "GUADELOUPE" , "瓜德罗普岛",   422,),
("GQ",  "EQUATORIAL GUINEA"  , "赤道几内亚",   216,),
("GT",  "GUATEMALA"  , "危地马拉",    423,),
("GU",  "GUAM"   , "关岛",  502,),
("GW",  "GUINEA-BISSAU"  , "几内亚比绍",   222,),
("GY",  "GUYANA" , "圭亚那", 424,),
("HK",  "HONG KONG"  , "香港",  110,),
("HM",  "HEARD ISLAND AND MCDONALD ISLANDS"  , "赫德和麦克唐纳群岛",   0,),
("HN",  "HONDURAS"   , "洪都拉斯",    426,),
("HT",  "HAITI"  , "海地",  425,),
("IM",  "ISLE OF MAN", "马恩岛", 0,),
("IN",  "INDIA"  , "印度",  111,),
("IO",  "BRITISH INDIAN OCEAN TERRITORY" , "英属印度洋领地", 303,),
("IQ",  "IRAQ"   , "伊拉克", 114,),
("IR",  "IRAN"   , "伊朗",  113,),
("JE",  "JERSEY" , "泽西",  303,),
("JM",  "JAMAICA", "牙买加", 427,),
("KE",  "KENYA"  , "肯尼亚", 224,),
("KG",  "KYRGYZSTAN" , "吉尔吉斯斯坦",  146,),
("KI",  "KIRIBATI"   , "基里巴斯",    618,),
("KM",  "COMOROS", "科摩罗", 212,),
("KN",  "SAINT KITTS AND NEVIS"  , "圣基茨和尼维斯", 447,),
("KP",  "KOREA(DEMOCRATIC PEOPLE'S REPUBLIC OF)" , "朝鲜（朝鲜民主主义人民共和国）", 109,),
("KW",  "KUWAIT" , "科威特", 118,),
("KY",  "CAYMAN ISLANDS" , "开曼群岛",    411,),
("KZ",  "KAZAKHSTAN" , "哈萨克斯坦",   145,),
("LA",  "LAO PEOPLE'S DEMOCRATIC REPUBLIC"   , "老挝人民民主共和国",   119,),
("LB",  "LEBANON", "黎巴嫩", 120,),
("LC",  "SAINT LUCIA", "圣露西亚",    437,),
("LI",  "LIECHTENSTEIN"  , "列支敦士登",   323,),
("LK",  "SRI LANKA"  , "斯里兰卡",    134,),
("LR",  "LIBERIA", "利比里亚",    225,),
("LS",  "LESOTHO", "莱索托", 255,),
("LY",  "LIBYAN ARAB JAMAHIRIYA" , "阿拉伯利比亚民众国",   226,),
("MA",  "MOROCCO", "摩洛哥", 232,),
("MG",  "MADAGASCAR" , "马达加斯加",   227,),
("MH",  "MARSHALL ISLANDS"   , "马绍尔群岛",   621,),
("ML",  "MALI"   , "马里",  229,),
("MO",  "MACAO"  , "澳门",  121,),
("MP",  "NORTHERN MARIANA ISLANDS"   , "北马里亚纳群岛", 502,),
("MQ",  "MARTINIQUE" , "马提尼克",    428,),
("MR",  "MAURITANIA" , "毛里塔尼亚",   230,),
("MS",  "MONTSERRAT" , "蒙特塞拉特岛",  430,),
("MU",  "MAURITIUS"  , "毛里求斯",    231,),
("MV",  "MALDIVES"   , "马尔代夫",    123,),
("MW",  "MALAWI" , "马拉维", 228,),
("MZ",  "MOZAMBIQUE" , "莫桑比克",    233,),
("NA",  "NAMIBIA", "纳米比亚",    234,),
("NC",  "NEW CALEDONIA"  , "新喀里多尼亚",  607,),
("NE",  "NIGER"  , "尼日尔", 235,),
("NF",  "NORFOLK ISLAND" , "诺福克岛",    610,),
("NG",  "NIGERIA", "尼日利亚",    236,),
("NI",  "NICARAGUA"  , "尼加拉瓜",    431,),
("NP",  "NEPAL"  , "尼泊尔", 125,),
("NR",  "NAURU"  , "瑙鲁",  606,),
("NU",  "NIUE"   , "纽埃",  602,),
("PF",  "FRENCH POLYNESIA"   , "法属玻利尼西亚", 623,),
("PG",  "PAPUA NEW GUINEA"   , "巴布亚新几内亚", 611,),
("PK",  "PAKISTAN"   , "巴基斯坦",    127,),
("PM",  "SAINT PIERRE AND MIQUELON"  , "圣彼埃尔和密克隆岛",   448,),
("PN",  "PITCAIRN"   , "皮特凯恩",    303,),
("PR",  "PUERTO RICO", "波多黎各",    435,),
("PS",  "PALESTINIAN TERRITORY OCCUPIED" , "巴勒斯坦领土，占领",   128,),
("PW",  "PALAU"  , "帕劳群岛",    622,),
("RE",  "REUNION", "留尼旺", 237,),
("RW",  "RWANDA" , "卢旺达", 238,),
("SB",  "SOLOMON ISLANDS", "所罗门群岛",   613,),
("SC",  "SEYCHELLES" , "塞舌尔", 241,),
("SD",  "SUDAN"  , "苏丹",  246,),
("SH",  "Saint Helena, Ascension and Tristan da Cunha",   "圣海伦娜, 阿森松岛, 库克岛", 0,),
("SJ",  "SVALBARD AND JAN MAYEN" , "斯瓦尔巴群岛和扬马延岛", 326,),
("SK",  "SLOVAKIA"   , "斯洛伐克",    353,),
("SL",  "SIERRA LEONE"   , "塞拉利昂",    242,),
("SM",  "SAN MARINO" , "圣马力诺",    329,),
("SN",  "SENEGAL", "塞内加尔",    240,),
("SO",  "SOMALIA", "索马里", 243,),
("SR",  "SURINAME"   , "苏里南", 441,),
("ST",  "SAO TOME AND PRINCIPE"  , "圣多美和普林西比",    239,),
("SV",  "EL SALVADOR", "萨尔瓦多",    440,),
("SY",  "SYRIAN ARAB REPUBLIC"   , "阿拉伯叙利亚共和国",   135,),
("SZ",  "SWAZILAND"  , "斯威士兰",    257,),
("TC",  "TURKS AND CAICOS ISLANDS"   , "特克斯和凯科斯群岛",   443,),
("TD",  "CHAD"   , "乍得",  211,),
("TF",  "FRENCH SOUTHERN TERRITORIES", "法属南部领地",  305,),
("TG",  "TOGO"   , "多哥",  248,),
("TJ",  "TAJIKISTAN" , "塔吉克斯坦",   147,),
("TK",  "TOKELAU", "托克劳群岛",   609,),
("TL",  "TIMOR-LESTE", "东帝汶", 144,),
("TM",  "TURKMENISTAN"   , "土库曼斯坦",   148,),
("TN",  "TUNISIA", "突尼斯", 249,),
("TO",  "TONGA"  , "汤加",  614,),
("TT",  "TRINIDAD AND TOBAGO", "特立尼达和多巴哥",    442,),
("TV",  "TUVALU" , "图瓦卢", 619,),
("TZ",  "TANZANIA  UNITED REPUBLIC OF"   , "坦桑尼亚联合共和国",   247,),
("UG",  "UGANDA" , "乌干达", 250,),
("UM",  "UNITED STATES MINOR OUTLYING ISLANDS"   , "美国外围岛屿",  0,),
("UZ",  "UZBEKISTAN" , "乌兹别克斯坦",  149,),
("VC",  "SAINT VINCENT AND THE GRENADINES"   , "圣文森特和格林纳丁斯",  439,),
("VE",  "VENEZUELA"  , "委内瑞拉",    445,),
("VG",  "TORTOLA(VIRGIN ISLANDS  BRITISH)"   , "托托拉岛（英属维尔京群岛）",   446,),
("VI",  "VIRGIN ISLANDS  U.S" , "维尔京群岛（美国）",   502,),
("VN",  "VIETNAM", "越南",  141,),
("VU",  "VANUATU", "瓦努阿图",    608,),
("WF",  "WALLIS AND FUTUNA"  , "瓦利斯和富图纳群岛",   625,),
("WS",  "SAMOA"  , "萨摩亚", 617,),
("YE",  "YEMEN"  , "也门",  139,),
("YT",  "MAYOTTE", "马约特岛",    259,),
("ZA",  "SOUTH AFRICA"   , "南非",  244,),
("ZM",  "ZAMBIA" , "赞比亚", 253,),
("ZW",  "ZIMBABWE"   , "津巴布韦",    254,),
("EE",  "ESTONIA", "爱沙尼亚",    334,),
("BG",  "BULGARIA"   , "保加利亚",    316,),
("ME",  "MONTENEGRO" , "黑山共和国",   359,),
("SI",  "SLOVENIA"   , "斯洛文尼亚",   350,),
("LV",  "LATVIA" , "拉脱维亚",    335,),
("IF",  "IFNI"   , "伊夫尼", 232,),
("JI",  "Johnston Island", "约翰斯敦岛",   502,),
("EI",  "EASTER ISLAND"  , "复活岛", 412,),
("ZR",  "Zaire"  , "扎伊尔", 252,),
("DG",  "Diego Garcia"   , "迭戈加西亚",   303,),
("KO",  "Kosovo" , "科索沃", 0,),
("GK",  "GAZA AND KHAN YUNIS", "加沙和汗尤尼斯", 0,),
("MF",  "Metropolitan France", "法国的大都市",  0,),
("XF",  "CORSICA", "科西嘉岛",    305,),
("XG",  "SPANISH TERRITORIES OF N.AFRICA", "北非西班牙属土", 312,),
("XJ",  "BALEARIC ISLANDS"   , "巴利阿里群岛",  312,),
("XK",  "CAROLINE ISLANDS"   , "加罗林群岛",   620,),
("XM",  "WAKE ISLAND", "威克岛", 502,),
("AN",  "Netherlands Antilles"   , "荷属安的列斯群岛",    449,),
("XC",  "CHANNEL ISLANDS", "海峡群岛(诺曼底群岛)", 303),
("IC",  "CANARY ISLANDS" , "加那利群岛",   312,),
("SS",  "SOUTH SUDAN", "南苏丹共和国",  260,),
("CW",  "Curaçao", "库拉索", 0,),
]

for code, name, cn_name, number in countrys:
    country = Country.objects.filter(code=code).first()
    if not country:
        country = Country()
        country.code = code
        country.name = name
        country.cn_name = cn_name
        country.save()
    country.cn_name = cn_name
    country.number = number
    country.save()
print "import country success"

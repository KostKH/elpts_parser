"""Модуль парсера eltps_parser, в который вынесены настройки парсера"""
API_LINK = 'https://portal.elpts.ru/ncher/api/1/esbkts/'
FOLDER = 'results/'
OUTPUT_XSLX = 'elpts.xlsx'
ERROR_PAGES_FILE = 'failed_pages.json'
LOGFILE = 'elpts.log'

# кол-во строк на странице (API позволяет максимум 25 строк)
SIZE = 25
# кол-во параллельных потоков для парсинга
MAX_TASKS = 100
# кол-во попыток спарсить одну страницу.
TRY_NUMBER = 20

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/109.0.0.0 Safari/537.36'),
    'Accept': ('text/html,application/xhtml+xml,application/xml;'
               'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
               'application/signed-exchange;v=b3;q=0.9'),
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

"""Основной модуль парсера elpts_parser. Запускает парсер"""
import asyncio
import datetime as dt
import json
import logging
import os
import time
from math import ceil

import aiohttp

import datasaving
import settings


async def get_total_number(api_link, headers):
    """Функция вытягивает с сайта общее кол-во строк, которое надо спарсить.
    На вход принимает параметры, необходимые для парсинга."""
    url = f'{api_link}count?head=%D0%A2%D0%A1'
    session = aiohttp.ClientSession()
    response = await session.get(url, headers=headers, ssl=False)
    total = await response.json()
    await session.close()
    return int(total)


async def worker(
    name,
    queue,
    api_link,
    date,
    headers,
    size=25,
    result_list=[],
    error_pages_list=[],
):
    """Данная функция - непосредственно парсер страниц, она образует поток.
    На вход принимает очередь из страниц и необходимые параметры для парсинга.
    Спарсенные строки сохраняются в список result_list. Номера страниц,
    которые не удастся спарсить, будут сохранены в список error_pages_list.
    Функция берет из очереди страницы для парсинга и работает до тех пор,
    пока очередь не станет пустой. (После этого поток будет остановлен
    из функции main)"""
    while True:
        if queue.qsize() <= 0:
            await asyncio.sleep(0.1)
            continue
        session = aiohttp.ClientSession()
        page, try_number = await queue.get()
        print(page, name)
        url = (f'{api_link}search?head=ТС&dateFrom=1990-01-01&'
               f'dateTo={date}&page={page}&size={size}')
        try:
            response = await session.get(
                url,
                headers=headers,
                ssl=False,
                timeout=60
            )
        except Exception as e:
            await session.close()
            queue.task_done()
            if try_number > 0:
                queue.put_nowait((page, try_number - 1))
            else:
                logging.exception(f'Не удалось спарсить страницу {page}: {e}')
                error_pages_list.append(page)
            await asyncio.sleep(0.1)
            continue
        data = await response.json()
        datasaving.prepare_data(data, result_list)
        print(page, name, 'done', len(result_list))
        await session.close()
        queue.task_done()
        await asyncio.sleep(0.1)


async def main():
    """Основная функция, запускающая парсинг. Вначале мы определяем кол-во
    строк. Исходя из этого определяем кол-во страниц для парсинга. Создаем
    очередь из страниц. Запускаем параллельные потоки для парсинга данных.
    После окончания парсинга сохраняем данные в excel-файл и логируем
    результат."""
    time_start = time.monotonic()

    excelfile_path = settings.FOLDER + settings.OUTPUT_XSLX
    errorfile_path = settings.FOLDER + settings.ERROR_PAGES_FILE
    logfile_path = settings.FOLDER + settings.LOGFILE
    if not os.path.exists(settings.FOLDER):
        os.mkdir(settings.FOLDER)

    logging.basicConfig(
        filename=logfile_path,
        filemode='w',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    datasaving.save_titles_to_excel(excelfile_path)
    total = await get_total_number(
        settings.API_LINK,
        settings.HEADERS
    )
    logging.info(f'Всего строк для парсинга: {total}')
    queue = asyncio.Queue()
    last_page = ceil(total / settings.SIZE)
    for page in range(1, last_page + 1):
        queue.put_nowait((page, settings.TRY_NUMBER))
    (queue.qsize())
    date = dt.datetime.now().strftime('%Y-%m-%d')
    result_list = []
    error_pages_list = []
    worker_kwargs = {
        'queue': queue,
        'api_link': settings.API_LINK,
        'date': date,
        'headers': settings.HEADERS,
        'size': settings.SIZE,
        'result_list': result_list,
        'error_pages_list': error_pages_list,
    }
    tasks = []
    for i in range(settings.MAX_TASKS):
        task = asyncio.create_task(worker(f'worker-{i}', **worker_kwargs))
        tasks.append(task)
    await queue.join()
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    with open(errorfile_path, 'w') as file:
        file.write(json.dumps(error_pages_list))
    datasaving.save_data_to_excel(excelfile_path, result_list)
    print('final', len(result_list))
    logging.info(f'Сохранено строк в файл: {len(result_list)}')
    if len(result_list) < total:
        logging.error(
            f'Excel-файл не полный!!! Сохранено только: {len(result_list)}'
            f'строк из {total}'
        )
    time_duration = round((time.monotonic() - time_start) / 60)
    logging.info(f'Парсинг длился: {time_duration} мин.')


if __name__ == '__main__':
    asyncio.run(main())

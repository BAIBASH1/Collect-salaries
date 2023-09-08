import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable
import math
import time


BASE_URL_HH = 'https://api.hh.ru/vacancies'
BASE_URL_SJ = 'https://api.superjob.ru/2.0/vacancies/'
PROGRAMMING_LANGS = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    'C',
    'Go'
]



def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        predicted_salary = (salary_to + salary_from) / 2
        return predicted_salary
    if salary_to:
        predicted_salary = salary_to * 0.8
        return predicted_salary
    if salary_from:
        predicted_salary = salary_from * 1.2
        return predicted_salary
    predicted_salary = None
    return predicted_salary


def predict_rub_salary_hh(vacancy):
    vacancy_salary = vacancy['salary']
    if not vacancy_salary or vacancy_salary['currency'] != 'RUR':
        predicted_salary = None
    else:
        predicted_salary = predict_salary(vacancy_salary['from'], vacancy_salary['to'])
    return predicted_salary


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        predicted_salary = None
    else:
        predicted_salary = predict_salary(vacancy['payment_from'], vacancy['payment_to'])
    return predicted_salary


def process_page_hh(response):
    salaries = []
    vacancies = response.json()['items']
    for vacancy in vacancies:
        predicted_salary = predict_rub_salary_hh(vacancy)
        if predicted_salary:
            salaries.append(int(predicted_salary))
    return salaries


def process_page_sj(response):
    salaries = []
    vacancies = response.json()['objects']
    for vacancy in vacancies:
        predicted_salary = predict_rub_salary_sj(vacancy)
        if predicted_salary:
            salaries.append(int(predicted_salary))
    return salaries


def collect_salaries_hh():
    salaries_of_lang = {}
    moscow_code_hh = 1
    params = {
        'text': 'Программист',
        'area': moscow_code_hh,
        'page': 0
    }
    for lang in PROGRAMMING_LANGS:
        total_salaries = []
        params['text'] = f'Программист {lang}'
        page = 0
        while True:
            params['page'] = page
            response = requests.get(BASE_URL_HH, params=params)
            response.raise_for_status()
            time.sleep(0.5)
            vacancies = response.json()
            salaries = process_page_hh(response)
            total_salaries += salaries
            pages = vacancies['pages']
            max_available_pages = 100
            if page == pages - 1 or page > max_available_pages:
                vacancies_found = vacancies['found']
                break
            page += 1
        salary_sum = sum(total_salaries)
        vacancies_processed = len(total_salaries)
        if salary_sum:
            average_salary = salary_sum / vacancies_processed
        else:
            average_salary = 0
        salaries_of_lang[lang] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": int(average_salary)
        }
    return salaries_of_lang


def collect_salaries_sj():
    SECRET_KEY_SJ = os.environ['SECRET_KEY_SJ']
    headers = {
        'X-Api-App-Id': SECRET_KEY_SJ
    }
    moscow_code_sj = 4
    params = {
        'text': 'Программист',
        'town': moscow_code_sj
    }
    salaries_of_lang = {}
    for lang in PROGRAMMING_LANGS:
        total_salaries = []
        params['keywords'] = f'Программист {lang}'
        page = 0

        while True:
            params['page'] = page
            response = requests.get(BASE_URL_SJ, headers=headers, params=params)
            response.raise_for_status()
            vacancies = response.json()
            salaries_sj = process_page_sj(response)
            total_salaries += salaries_sj
            vacancies_found = vacancies['total']
            vacancies_on_page = 20
            pages = math.ceil(vacancies_found / vacancies_on_page)
            if page == pages:
                break
            page += 1
        salary_sum = sum(total_salaries)
        vacancies_processed = len(total_salaries)
        if salary_sum:
            average_salary = salary_sum / vacancies_processed
        else:
            average_salary = 0
        salaries_of_lang[lang] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": int(average_salary)
        }
    return salaries_of_lang


def get_tables(salaries_of_lang, site_name):

    table = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for lang, salary in salaries_of_lang.items():
        table.append([lang, salary['vacancies_found'], salary['vacancies_processed'], salary['average_salary']])
    return AsciiTable(table, site_name).table


def main():
    load_dotenv()
    salaries_sj = collect_salaries_sj()
    print(get_tables(salaries_sj, 'Superjob Moscow'))
    salaries_hh = collect_salaries_hh()
    print(get_tables(salaries_hh, 'HeadHunter Moscow'))


if __name__ == '__main__':
    main()